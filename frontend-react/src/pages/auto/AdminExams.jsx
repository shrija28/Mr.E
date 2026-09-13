import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';

const AdminExams = () => {
  const [exams, setExams] = useState([]);
  const [subject, setSubject] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [isError, setIsError] = useState(false);

  // Modal for inspecting exam questions
  const [inspectExamId, setInspectExamId] = useState(null);
  const [inspectLoading, setInspectLoading] = useState(false);
  const [inspectData, setInspectData] = useState(null);
  const [activeSetTab, setActiveSetTab] = useState(0);

  const fetchExams = async () => {
    try {
      const res = await fetch('/api/admin/exams', { credentials: 'include' });
      const data = await res.json();
      if (res.ok && data.exams) {
        setExams(data.exams.map(e => ({
          id: e.exam_id,
          name: e.exam_name || `KCET ${e.subject} Exam`,
          subject: e.subject,
          created: e.created_at ? e.created_at.split('T')[0] : '—',
          sets: e.set_count || 4,
          status: e.is_published ? 'Active' : 'Draft'
        })));
      }
    } catch (err) {
      console.error('Failed to load exams', err);
    }
  };

  useEffect(() => {
    fetchExams();
  }, []);

  const handleCreateExam = async () => {
    if (!subject) {
      setMessage('Please select a Subject first.');
      setIsError(true);
      return;
    }
    
    setLoading(true);
    setMessage(`Retrieving generated questions from Question Bank and creating exam for ${subject}...`);
    setIsError(false);

    try {
      const res = await fetch('/api/admin/exams', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          subject: subject,
          is_published: true
        })
      });

      const data = await res.json();
      setLoading(false);

      if (!res.ok) {
        setMessage(data.message || data.error || 'Failed to create exam');
        setIsError(true);
        return;
      }

      setMessage(`✓ Exam "${data.exam_name || 'KCET ' + subject + ' Exam'}" created successfully with 60 questions from Question Bank!`);
      setIsError(false);
      setSubject('');
      fetchExams();

      setTimeout(() => {
        setMessage('');
      }, 6000);
    } catch (err) {
      setLoading(false);
      setMessage('Network error occurred while creating exam.');
      setIsError(true);
    }
  };

  const togglePublish = async (id, currentStatus) => {
    const targetPublish = currentStatus !== 'Active';
    try {
      const res = await fetch(`/api/admin/exams/${id}`, {
        method: 'PATCH',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ is_published: targetPublish })
      });
      if (res.ok) {
        await fetchExams();
      } else {
        const data = await res.json().catch(() => ({}));
        alert(data.message || data.error || 'Failed to update publish state');
      }
    } catch (err) {
      console.error('Failed to toggle publish status', err);
      alert('Error updating exam status. Please check your connection.');
    }
  };

  const handleDeleteExam = async (id, name) => {
    if (!window.confirm(`Are you sure you want to delete "${name}"? This cannot be undone.`)) {
      return;
    }
    try {
      const res = await fetch(`/api/admin/exams/${id}`, {
        method: 'DELETE',
        credentials: 'include'
      });
      if (res.ok) {
        await fetchExams();
      } else {
        const data = await res.json().catch(() => ({}));
        alert(data.message || data.error || 'Failed to delete exam');
      }
    } catch (err) {
      console.error('Failed to delete exam', err);
      alert('Error deleting exam. Please check your connection.');
    }
  };

  const openInspectModal = async (examId) => {
    setInspectExamId(examId);
    setInspectLoading(true);
    setInspectData(null);
    setActiveSetTab(0);

    try {
      const res = await fetch(`/api/admin/exams/${examId}`, { credentials: 'include' });
      const data = await res.json();
      if (res.ok) {
        setInspectData(data);
      } else {
        alert(data.message || 'Failed to load exam details');
        setInspectExamId(null);
      }
    } catch (err) {
      console.error('Failed to load exam questions', err);
      alert('Network error while loading exam questions');
      setInspectExamId(null);
    } finally {
      setInspectLoading(false);
    }
  };

  return (
    <>
      <div className="bg-mesh"></div>
      
      <div className="main-wrap">
        <div className="section-card">
          <div className="section-card-header">
            <div className="section-icon" style={{"background":"linear-gradient(135deg,rgba(124,58,237,0.2),rgba(37,99,235,0.2))"}}>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>
            </div>
            <div>
              <h2>Create Exam</h2>
              <p className="section-sub">
                Select a subject to create an exam with 4 paper sets (Sets A, B, C, D — 60 questions each) retrieved directly from your Question Bank
              </p>
            </div>
          </div>
          <div className="section-body">
            <div style={{ display: "flex", gap: "16px", alignItems: "flex-end", flexWrap: "wrap" }}>
              <div className="input-group" style={{ minWidth: '300px' }}>
                <label className="input-label" htmlFor="subjectSelect">Subject</label>
                <select 
                  id="subjectSelect" 
                  className="text-input" 
                  style={{ minWidth: "300px", padding: "10px 14px" }}
                  value={subject}
                  onChange={(e) => setSubject(e.target.value)}
                  disabled={loading}
                >
                  <option value="" disabled>Select subject…</option>
                  <option value="Biology">Biology</option>
                  <option value="Physics">Physics</option>
                  <option value="Chemistry">Chemistry</option>
                  <option value="Mathematics">Mathematics</option>
                </select>
              </div>

              <button className="btn-primary" onClick={handleCreateExam} disabled={loading} style={{ padding: "11px 24px" }}>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ width: "16px", height: "16px" }}><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
                {loading ? 'Creating Exam...' : '+ Create Exam'}
              </button>
            </div>

            {message && (
              <div style={{ marginTop: "14px", color: isError ? 'var(--red)' : 'var(--green)', fontSize: '0.92rem', fontWeight: 'bold' }}>
                {message}
              </div>
            )}
          </div>
        </div>
        
        <div className="section-card">
          <div className="section-card-header">
            <div className="section-icon" style={{"background":"linear-gradient(135deg,rgba(8,145,178,0.2),rgba(5,150,105,0.2))"}}>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><line x1="3" y1="9" x2="21" y2="9"/><line x1="9" y1="21" x2="9" y2="9"/></svg>
            </div>
            <div>
              <h2>All Created Exams</h2>
              <p className="section-sub">{exams.length} exams available in system</p>
            </div>
          </div>
          <div className="section-body" style={{"padding":"0"}}>
            <div className="table-scroll">
              <table className="results-table">
                <thead>
                  <tr>
                    <th>Exam Name</th>
                    <th>Subject</th>
                    <th>Questions</th>
                    <th>Created</th>
                    <th>Status</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {exams.length > 0 ? (
                    exams.map(exam => (
                      <tr key={exam.id}>
                        <td style={{fontWeight: 600, color: 'var(--blue)'}}>{exam.name}</td>
                        <td>
                          <span style={{
                            padding: '3px 10px',
                            borderRadius: '12px',
                            fontSize: '0.8rem',
                            background: exam.subject === 'Biology' ? 'rgba(16, 185, 129, 0.1)' : exam.subject === 'Physics' ? 'rgba(59, 130, 246, 0.1)' : 'rgba(245, 158, 11, 0.1)',
                            color: exam.subject === 'Biology' ? '#059669' : exam.subject === 'Physics' ? '#2563eb' : '#d97706',
                            fontWeight: 600
                          }}>
                            {exam.subject}
                          </span>
                        </td>
                        <td>{exam.sets === 1 ? '60 Questions (1 Set)' : `${exam.sets * 60} Qs (${exam.sets} Sets)`}</td>
                        <td>{exam.created}</td>
                        <td>
                          <span style={{
                            padding: '4px 8px', 
                            borderRadius: '12px', 
                            fontSize: '0.75rem', 
                            background: exam.status === 'Active' ? 'rgba(16, 185, 129, 0.1)' : 'rgba(245, 158, 11, 0.1)',
                            color: exam.status === 'Active' ? 'var(--green)' : '#d97706',
                            fontWeight: 'bold'
                          }}>
                            {exam.status === 'Active' ? 'Published' : 'Draft'}
                          </span>
                        </td>
                        <td>
                          <div style={{display: 'flex', gap: '8px'}}>
                            <button 
                              className="btn-outline small"
                              onClick={() => openInspectModal(exam.id)}
                              style={{ borderColor: 'var(--blue)', color: 'var(--blue)' }}
                              title="Inspect Questions in this Exam"
                            >
                              View Questions
                            </button>
                            <button 
                              className="btn-outline small"
                              onClick={() => togglePublish(exam.id, exam.status)}
                              style={exam.status === 'Draft' ? {borderColor: 'var(--green)', color: 'var(--green)'} : {borderColor: '#d97706', color: '#d97706'}}
                            >
                              {exam.status === 'Draft' ? 'Publish' : 'Unpublish'}
                            </button>
                            <button 
                              className="btn-outline small"
                              onClick={() => handleDeleteExam(exam.id, exam.name)}
                              style={{borderColor: 'var(--red)', color: 'var(--red)'}}
                              title="Delete Exam"
                            >
                              Delete
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr><td colSpan="6" style={{"textAlign":"center","color":"var(--muted)","padding":"36px"}}>No exams created yet. Select a subject above and click "+ Create Exam".</td></tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Modal: View Questions in Exam */}
        {inspectExamId && (
          <div style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(0,0,0,0.75)',
            backdropFilter: 'blur(6px)',
            zIndex: 1000,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '24px'
          }}>
            <div style={{
              background: 'var(--card-bg, #fff)',
              border: '1px solid var(--border)',
              borderRadius: '12px',
              maxWidth: '900px',
              width: '100%',
              maxHeight: '90vh',
              display: 'flex',
              flexDirection: 'column',
              boxShadow: '0 20px 40px rgba(0,0,0,0.3)',
              overflow: 'hidden'
            }}>
              {/* Modal Header */}
              <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                padding: '18px 24px',
                borderBottom: '1px solid var(--border)',
                background: 'var(--s1, rgba(0,0,0,0.02))'
              }}>
                <div>
                  <h3 style={{ margin: 0, fontSize: '1.2rem', color: 'var(--blue)' }}>
                    📋 {inspectData ? inspectData.exam_name : 'Loading Exam...'}
                  </h3>
                  {inspectData && (
                    <span style={{ fontSize: '0.82rem', color: 'var(--muted)' }}>
                      Subject: {inspectData.subject} · {inspectData.total_questions} Questions Retrieved from Question Bank across 4 Sets
                    </span>
                  )}
                </div>
                <button 
                  onClick={() => setInspectExamId(null)}
                  style={{
                    background: 'none',
                    border: 'none',
                    fontSize: '1.5rem',
                    cursor: 'pointer',
                    color: 'var(--muted)'
                  }}
                >
                  ✕
                </button>
              </div>

              {/* Modal Body */}
              <div style={{ flex: 1, overflowY: 'auto', padding: '20px 24px' }}>
                {inspectLoading || !inspectData ? (
                  <div style={{ textAlign: 'center', padding: '50px', color: 'var(--muted)' }}>
                    ⏳ Loading exam sets and assigned questions...
                  </div>
                ) : (
                  <>
                    {/* Set Tabs */}
                    <div style={{ display: 'flex', gap: '8px', marginBottom: '18px', borderBottom: '1px solid var(--border)', paddingBottom: '10px' }}>
                      {inspectData.sets.map((setObj, sIdx) => (
                        <button
                          key={setObj.set_id || sIdx}
                          onClick={() => setActiveSetTab(sIdx)}
                          style={{
                            padding: '8px 18px',
                            borderRadius: '8px',
                            border: activeSetTab === sIdx ? '1px solid var(--blue)' : '1px solid var(--border)',
                            background: activeSetTab === sIdx ? 'var(--blue)' : 'transparent',
                            color: activeSetTab === sIdx ? '#fff' : 'var(--text)',
                            fontWeight: 600,
                            cursor: 'pointer',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '6px'
                          }}
                        >
                          <span>Set {setObj.set_label}</span>
                          <span style={{
                            fontSize: '0.75rem',
                            background: activeSetTab === sIdx ? 'rgba(255,255,255,0.25)' : 'rgba(0,0,0,0.06)',
                            padding: '2px 6px',
                            borderRadius: '10px'
                          }}>
                            {setObj.questions.length} Qs
                          </span>
                        </button>
                      ))}
                    </div>

                    {/* Questions List for Active Set */}
                    {inspectData.sets[activeSetTab]?.questions.length === 0 ? (
                      <div style={{ textAlign: 'center', padding: '30px', color: 'var(--muted)' }}>
                        No questions in this set.
                      </div>
                    ) : (
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                        {inspectData.sets[activeSetTab]?.questions.map((q, qIdx) => {
                          const opts = Array.isArray(q.options) ? q.options : [];
                          const correctIdx = parseInt(q.correct_option, 10);
                          const optLabels = ['A', 'B', 'C', 'D'];

                          return (
                            <div 
                              key={q.id || qIdx}
                              style={{
                                padding: '14px 18px',
                                borderRadius: '8px',
                                border: '1px solid var(--border)',
                                background: 'var(--card-bg, #fff)'
                              }}
                            >
                              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
                                <p style={{ margin: 0, fontSize: '0.95rem', fontWeight: 600, color: 'var(--text)', lineHeight: 1.4 }}>
                                  <span style={{ color: 'var(--blue)', marginRight: '8px' }}>Q{qIdx + 1}.</span>
                                  {q.question}
                                </p>
                                {q.topic && (
                                  <span style={{
                                    fontSize: '0.75rem',
                                    background: 'rgba(59, 130, 246, 0.1)',
                                    color: 'var(--blue)',
                                    padding: '2px 8px',
                                    borderRadius: '10px',
                                    whiteSpace: 'nowrap',
                                    marginLeft: '10px'
                                  }}>
                                    {q.topic}
                                  </span>
                                )}
                              </div>

                              {/* Options */}
                              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '8px', marginTop: '10px' }}>
                                {opts.map((opt, oIdx) => {
                                  const isCorrect = oIdx === correctIdx;
                                  return (
                                    <div
                                      key={oIdx}
                                      style={{
                                        padding: '8px 12px',
                                        borderRadius: '6px',
                                        fontSize: '0.86rem',
                                        background: isCorrect ? 'rgba(16, 185, 129, 0.08)' : 'rgba(0,0,0,0.02)',
                                        border: isCorrect ? '1px solid #10b981' : '1px solid var(--border)',
                                        color: 'var(--text)'
                                      }}
                                    >
                                      <strong style={{ color: isCorrect ? '#10b981' : 'var(--muted)', marginRight: '6px' }}>
                                        ({optLabels[oIdx]})
                                      </strong>
                                      {opt}
                                      {isCorrect && (
                                        <span style={{ float: 'right', color: '#10b981', fontWeight: 'bold', fontSize: '0.75rem' }}>✓</span>
                                      )}
                                    </div>
                                  );
                                })}
                              </div>

                              {q.explanation && (
                                <div style={{ marginTop: '8px', fontSize: '0.8rem', color: 'var(--muted)', fontStyle: 'italic' }}>
                                  💡 <strong>Explanation:</strong> {q.explanation}
                                </div>
                              )}
                            </div>
                          );
                        })}
                      </div>
                    )}
                  </>
                )}
              </div>

              {/* Modal Footer */}
              <div style={{
                padding: '14px 24px',
                borderTop: '1px solid var(--border)',
                display: 'flex',
                justifyContent: 'flex-end',
                background: 'var(--s1, rgba(0,0,0,0.02))'
              }}>
                <button className="btn-outline" onClick={() => setInspectExamId(null)}>
                  Close
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </>
  );
};

export default AdminExams;
