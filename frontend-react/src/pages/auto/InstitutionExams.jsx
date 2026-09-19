import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';

const InstitutionExams = () => {
  const [exams, setExams] = useState([]);
  const [batches, setBatches] = useState([]);
  const [questionCounts, setQuestionCounts] = useState({});
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState('');
  const [successMsg, setSuccessMsg] = useState('');

  // Form State
  const [examName, setExamName] = useState('');
  const [subject, setSubject] = useState('Mathematics');
  const [batchId, setBatchId] = useState('');
  const [durationMinutes, setDurationMinutes] = useState(60);
  const [totalMarks, setTotalMarks] = useState(60);
  const [questionCount, setQuestionCount] = useState(20);
  const [scheduledStart, setScheduledStart] = useState('');
  const [scheduledEnd, setScheduledEnd] = useState('');
  const [isPublished, setIsPublished] = useState(true);

  // Filter
  const [filterSubject, setFilterSubject] = useState('all');
  const [filterBatch, setFilterBatch] = useState('all');

  const fetchData = async () => {
    setLoading(true);
    setError('');
    try {
      // 1. Fetch Exams
      const examRes = await fetch('/api/institution/content/exams', { credentials: 'include' });
      if (examRes.ok) {
        const data = await examRes.json();
        setExams(data.exams || []);
      }

      // 2. Fetch Batches
      const batchRes = await fetch('/api/institution/batches', { credentials: 'include' });
      if (batchRes.ok) {
        const bData = await batchRes.json();
        setBatches(bData.batches || []);
      }

      // 3. Fetch Question Counts
      const qRes = await fetch('/api/institution/content/questions/counts', { credentials: 'include' });
      if (qRes.ok) {
        const qData = await qRes.json();
        setQuestionCounts(qData.counts || {});
      }
    } catch (err) {
      setError('Failed to load exams and batch data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  // Questions Modal State
  const [viewingQuestionsExam, setViewingQuestionsExam] = useState(null);
  const [loadingQuestions, setLoadingQuestions] = useState(false);
  const [activeSetIndex, setActiveSetIndex] = useState(0);

  const fetchExamQuestions = async (examId) => {
    setLoadingQuestions(true);
    setError('');
    try {
      const res = await fetch(`/api/institution/content/exams/${examId}/questions`, { credentials: 'include' });
      if (res.ok) {
        const data = await res.json();
        setViewingQuestionsExam(data);
        setActiveSetIndex(0);
      } else {
        const errData = await res.json().catch(() => ({}));
        setError(errData.message || 'Failed to load exam questions');
      }
    } catch (err) {
      setError('Network error fetching exam questions');
    } finally {
      setLoadingQuestions(false);
    }
  };

  const handleCreateExam = async (e) => {
    e.preventDefault();
    if (!examName.trim()) {
      setError('Please provide an exam name');
      return;
    }

    setCreating(true);
    setError('');
    setSuccessMsg('');

    try {
      const payload = {
        exam_name: examName.trim(),
        subject,
        batch_id: batchId || null,
        duration_minutes: Number(durationMinutes),
        total_marks: Number(totalMarks),
        question_count: Number(questionCount),
        scheduled_start: scheduledStart ? new Date(scheduledStart).toISOString() : null,
        scheduled_end: scheduledEnd ? new Date(scheduledEnd).toISOString() : null,
        is_published: isPublished,
      };

      const res = await fetch('/api/institution/content/exams', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(payload),
      });

      const data = await res.json();
      if (res.ok) {
<<<<<<< HEAD:frontend-react/src/pages/auto/InstitutionExams.jsx
        setSuccessMsg(`Exam "${data.exam_name}" created successfully and assigned to ${data.batch_name || 'All Batches'}!`);
=======
        setSuccessMsg(`Exam "${data.exam_name}" created successfully! Click "View Questions" below to inspect the assigned questions.`);
>>>>>>> ec47da2 (updated few features):frontend/src/pages/auto/InstitutionExams.jsx
        setExamName('');
        setScheduledStart('');
        setScheduledEnd('');
        fetchData();
        if (data.exam_id) {
          fetchExamQuestions(data.exam_id);
        }
      } else {
        setError(data.message || 'Failed to create exam');
      }
    } catch {
      setError('Network error creating exam');
    } finally {
      setCreating(false);
    }
  };

  const handleTogglePublish = async (examId, currentStatus) => {
    try {
      const res = await fetch(`/api/institution/content/exams/${examId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ is_published: !currentStatus }),
      });
      if (res.ok) {
        setExams(prev =>
          prev.map(ex => ex.exam_id === examId ? { ...ex, is_published: !currentStatus } : ex)
        );
        setSuccessMsg(`Exam status updated to ${!currentStatus ? 'Published' : 'Draft'}`);
      }
    } catch {
      setError('Failed to update exam status');
    }
  };

  const handleDeleteExam = async (examId, name) => {
    if (!window.confirm(`Delete exam "${name}"? This action cannot be undone.`)) return;
    try {
      const res = await fetch(`/api/institution/content/exams/${examId}`, {
        method: 'DELETE',
        credentials: 'include',
      });
      if (res.ok) {
        setSuccessMsg(`Exam "${name}" deleted successfully.`);
        fetchData();
      } else {
        const data = await res.json();
        setError(data.message || 'Failed to delete exam');
      }
    } catch {
      setError('Failed to delete exam');
    }
  };

  const filteredExams = exams.filter(ex => {
    if (filterSubject !== 'all' && ex.subject !== filterSubject) return false;
    if (filterBatch !== 'all') {
      if (filterBatch === 'all_batches' && ex.batch_id) return false;
      if (filterBatch !== 'all_batches' && ex.batch_id !== filterBatch) return false;
    }
    return true;
  });

  return (
    <>
      <div className="bg-mesh"></div>

      <div className="main-wrap">
        <header className="institution-page-header" style={{ marginBottom: '24px' }}>
          <div>
            <h1 className="institution-page-title">
              Weekly Test <span className="institution-page-title-accent">Builder</span>
            </h1>
            <p className="institution-page-sub">
              Create custom weekly exams, schedule time windows, and assign them directly to batches
            </p>
          </div>
          <div className="institution-page-actions">
            <button
              type="button"
              className="btn-institution-outline"
              onClick={fetchData}
              style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ width: '14px', height: '14px' }}><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 11-2.12-9.36L23 10"/></svg>
              Refresh
            </button>
          </div>
        </header>

        {error && (
          <div style={{ background: 'rgba(220,38,38,0.1)', border: '1px solid var(--red)', borderRadius: '8px', padding: '12px 16px', marginBottom: '20px', color: 'var(--red-l)' }}>
            {error}
          </div>
        )}

        {successMsg && (
          <div style={{ background: 'rgba(5,150,105,0.1)', border: '1px solid var(--green)', borderRadius: '8px', padding: '12px 16px', marginBottom: '20px', color: 'var(--green-l)' }}>
            {successMsg}
          </div>
        )}

        {/* 1. Test Builder Form */}
        <div className="section-card" style={{ marginBottom: '24px' }}>
          <div className="section-card-header">
            <div className="section-icon" style={{ background: 'linear-gradient(135deg, rgba(124,58,237,0.2), rgba(37,99,235,0.2))' }}>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>
            </div>
            <div>
              <h2>Create & Assign Weekly Test</h2>
              <p className="section-sub">Configure exam parameters and assign to a specific class cohort</p>
            </div>
          </div>

          <div className="section-body">
            <form onSubmit={handleCreateExam}>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px', marginBottom: '16px' }}>
                <div>
                  <label className="input-label" htmlFor="examName">Exam Title *</label>
                  <input
                    type="text"
                    id="examName"
                    className="text-input"
                    placeholder="e.g. Weekly Mock #2 - Calculus"
                    value={examName}
                    onChange={(e) => setExamName(e.target.value)}
                    required
                    style={{ width: '100%' }}
                  />
                </div>

                <div>
                  <label className="input-label" htmlFor="subject">Subject *</label>
                  <select
                    id="subject"
                    className="text-input"
                    value={subject}
                    onChange={(e) => setSubject(e.target.value)}
                    style={{ width: '100%' }}
                  >
                    <option value="Mathematics">Mathematics</option>
                    <option value="Biology">Biology</option>
                    <option value="Physics">Physics</option>
                    <option value="Chemistry">Chemistry</option>
                  </select>
                </div>

                <div>
                  <label className="input-label" htmlFor="batchId">Target Batch / Section</label>
                  <select
                    id="batchId"
                    className="text-input"
                    value={batchId}
                    onChange={(e) => setBatchId(e.target.value)}
                    style={{ width: '100%' }}
                  >
                    <option value="">All Batches (Entire Institution)</option>
                    {batches.map((b) => (
                      <option key={b.id} value={b.id}>{b.name} ({b.student_count} students)</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="input-label" htmlFor="duration">Duration (Minutes)</label>
                  <select
                    id="duration"
                    className="text-input"
                    value={durationMinutes}
                    onChange={(e) => setDurationMinutes(e.target.value)}
                    style={{ width: '100%' }}
                  >
                    <option value="30">30 Minutes (Quick Quiz)</option>
                    <option value="60">60 Minutes (Standard KCET)</option>
                    <option value="80">80 Minutes (Full Length)</option>
                    <option value="120">120 Minutes (Extended Mock)</option>
                  </select>
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px', marginBottom: '20px' }}>
                <div>
                  <label className="input-label" htmlFor="qCount">Questions per Set</label>
                  <select
                    id="qCount"
                    className="text-input"
                    value={questionCount}
                    onChange={(e) => setQuestionCount(e.target.value)}
                    style={{ width: '100%' }}
                  >
                    <option value="20">20 Questions</option>
                    <option value="40">40 Questions</option>
                    <option value="60">60 Questions (KCET Standard)</option>
                  </select>
                </div>

                <div>
                  <label className="input-label" htmlFor="marks">Max Marks</label>
                  <input
                    type="number"
                    id="marks"
                    className="text-input"
                    value={totalMarks}
                    onChange={(e) => setTotalMarks(e.target.value)}
                    style={{ width: '100%' }}
                  />
                </div>

                <div>
                  <label className="input-label" htmlFor="startDate">Start Window (Optional)</label>
                  <input
                    type="datetime-local"
                    id="startDate"
                    className="text-input"
                    value={scheduledStart}
                    onChange={(e) => setScheduledStart(e.target.value)}
                    style={{ width: '100%' }}
                  />
                </div>

                <div>
                  <label className="input-label" htmlFor="endDate">Due / End Window (Optional)</label>
                  <input
                    type="datetime-local"
                    id="endDate"
                    className="text-input"
                    value={scheduledEnd}
                    onChange={(e) => setScheduledEnd(e.target.value)}
                    style={{ width: '100%' }}
                  />
                </div>
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px', borderTop: '1px solid var(--border)', paddingTop: '16px' }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', fontSize: '0.88rem' }}>
                  <input
                    type="checkbox"
                    checked={isPublished}
                    onChange={(e) => setIsPublished(e.target.checked)}
                  />
                  Publish immediately (Students can view & take exam)
                </label>

                <button
                  type="submit"
                  className="btn-primary"
                  disabled={creating}
                  style={{ minWidth: '180px', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}
                >
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ width: '16px', height: '16px' }}><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
                  {creating ? 'Generating 4 Sets...' : 'Create & Schedule Exam'}
                </button>
              </div>
            </form>
          </div>
        </div>

        {/* 2. Scheduled Institution Exams Table */}
        <div className="section-card">
          <div className="section-card-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <div className="section-icon" style={{ background: 'linear-gradient(135deg, rgba(8,145,178,0.2), rgba(5,150,105,0.2))' }}>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><line x1="3" y1="9" x2="21" y2="9"/><line x1="9" y1="21" x2="9" y2="9"/></svg>
              </div>
              <div>
                <h2>Scheduled Weekly Exams ({exams.length})</h2>
                <p className="section-sub">Active tests distributed across your institution's batches</p>
              </div>
            </div>

            {/* Filters */}
            <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
              <select
                className="text-input"
                style={{ padding: '6px 12px', fontSize: '0.85rem' }}
                value={filterSubject}
                onChange={(e) => setFilterSubject(e.target.value)}
              >
                <option value="all">All Subjects</option>
                <option value="Mathematics">Mathematics</option>
                <option value="Biology">Biology</option>
                <option value="Physics">Physics</option>
                <option value="Chemistry">Chemistry</option>
              </select>

              <select
                className="text-input"
                style={{ padding: '6px 12px', fontSize: '0.85rem' }}
                value={filterBatch}
                onChange={(e) => setFilterBatch(e.target.value)}
              >
                <option value="all">All Batches</option>
                <option value="all_batches">Unassigned (Institution-wide)</option>
                {batches.map((b) => (
                  <option key={b.id} value={b.id}>{b.name}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="section-body" style={{ padding: 0 }}>
            {loading ? (
              <div style={{ textAlign: 'center', padding: '40px', color: 'var(--muted)' }}>Loading scheduled exams...</div>
            ) : filteredExams.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '50px 20px', color: 'var(--muted)' }}>
                <h3>No Exams Scheduled Yet</h3>
                <p style={{ marginTop: '6px' }}>Use the Test Builder above to create your first weekly test.</p>
              </div>
            ) : (
              <div className="table-scroll">
                <table className="results-table">
                  <thead>
                    <tr>
                      <th>Exam Name</th>
                      <th>Subject</th>
                      <th>Assigned Batch</th>
                      <th>Duration / Marks</th>
                      <th>Sets</th>
                      <th>Status</th>
                      <th>Submissions</th>
                      <th style={{ textAlign: 'right' }}>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredExams.map((exam) => (
                      <tr key={exam.exam_id}>
                        <td>
                          <div style={{ fontWeight: 600, color: 'var(--text)' }}>
                            {exam.exam_name || 'Weekly Exam'}
                          </div>
                          <span style={{ fontSize: '0.78rem', color: 'var(--muted)' }}>
                            Created {exam.created_at ? new Date(exam.created_at).toLocaleDateString() : '—'}
                          </span>
                        </td>
                        <td>
                          <span style={{
                            fontSize: '0.8rem',
                            padding: '3px 8px',
                            borderRadius: '4px',
                            background: 'rgba(59, 130, 246, 0.1)',
                            color: 'var(--blue)',
                            fontWeight: 500,
                          }}>
                            {exam.subject}
                          </span>
                        </td>
                        <td>
                          <span style={{
                            fontSize: '0.8rem',
                            padding: '3px 8px',
                            borderRadius: '4px',
                            background: exam.batch_id ? 'rgba(167, 139, 250, 0.1)' : 'rgba(255, 255, 255, 0.05)',
                            color: exam.batch_id ? 'var(--purple-l)' : 'var(--muted)',
                          }}>
                            👥 {exam.batch_name || 'All Batches'}
                          </span>
                        </td>
                        <td style={{ fontSize: '0.85rem' }}>
                          <strong>{exam.duration_minutes}m</strong> • {exam.total_marks} Marks
                        </td>
                        <td style={{ fontSize: '0.85rem' }}>
                          <span style={{ color: 'var(--muted)' }}>4 Sets (A-D)</span>
                        </td>
                        <td>
                          <button
                            type="button"
                            onClick={() => handleTogglePublish(exam.exam_id, exam.is_published)}
                            style={{
                              border: 'none',
                              cursor: 'pointer',
                              padding: '4px 10px',
                              borderRadius: '12px',
                              fontSize: '0.78rem',
                              fontWeight: 600,
                              background: exam.is_published ? 'rgba(16, 185, 129, 0.15)' : 'rgba(234, 179, 8, 0.15)',
                              color: exam.is_published ? '#10b981' : '#eab308',
                            }}
                            title="Click to toggle status"
                          >
                            {exam.is_published ? '● Published' : '○ Draft'}
                          </button>
                        </td>
                        <td style={{ fontSize: '0.88rem' }}>
                          <strong style={{ color: 'var(--text)' }}>{exam.completion_count || 0}</strong> completed
                        </td>
                        <td style={{ textAlign: 'right' }}>
                          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px', alignItems: 'center' }}>
                            <button
                              type="button"
                              className="btn-institution-outline"
                              onClick={() => fetchExamQuestions(exam.exam_id)}
                              disabled={loadingQuestions}
                              style={{ padding: '4px 10px', fontSize: '0.78rem', display: 'inline-flex', alignItems: 'center', gap: '4px', color: 'var(--purple-l)' }}
                              title="View questions assigned to this test"
                            >
                              👁 View Questions
                            </button>
                            <Link
                              to={`/institution/analytics?exam_id=${exam.exam_id}`}
                              className="btn-institution-outline"
                              style={{ padding: '4px 8px', fontSize: '0.78rem' }}
                            >
                              Results
                            </Link>
                            <button
                              type="button"
                              onClick={() => handleDeleteExam(exam.exam_id, exam.exam_name)}
                              style={{ background: 'none', border: 'none', color: 'var(--red-l)', cursor: 'pointer', fontSize: '0.8rem' }}
                              title="Delete Exam"
                            >
                              Delete
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* View Exam Questions Modal */}
      {viewingQuestionsExam && (
        <div
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'rgba(0,0,0,0.75)',
            backdropFilter: 'blur(6px)',
            zIndex: 9999,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '20px'
          }}
          onClick={() => setViewingQuestionsExam(null)}
        >
          <div
            className="section-card"
            style={{
              maxWidth: '850px',
              width: '100%',
              maxHeight: '85vh',
              display: 'flex',
              flexDirection: 'column',
              overflow: 'hidden',
              padding: '0',
              borderRadius: '16px',
              boxShadow: '0 20px 50px rgba(0,0,0,0.5)'
            }}
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header */}
            <div style={{ padding: '20px 24px', borderBottom: '1px solid var(--border)', background: 'var(--s2)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '4px' }}>
                  <h2 style={{ fontSize: '1.2rem', margin: 0, color: 'var(--text)' }}>{viewingQuestionsExam.exam_name}</h2>
                  <span style={{ fontSize: '0.75rem', padding: '2px 8px', borderRadius: '4px', background: 'rgba(124,58,237,0.15)', color: 'var(--purple-l)', fontWeight: 600 }}>
                    {viewingQuestionsExam.subject}
                  </span>
                </div>
                <p style={{ margin: 0, fontSize: '0.82rem', color: 'var(--muted)' }}>
                  {viewingQuestionsExam.duration_minutes} Minutes • {viewingQuestionsExam.total_marks} Marks • Only these questions are visible to students taking this test
                </p>
              </div>
              <button
                onClick={() => setViewingQuestionsExam(null)}
                style={{ background: 'none', border: 'none', fontSize: '1.4rem', cursor: 'pointer', color: 'var(--muted)' }}
              >
                ✕
              </button>
            </div>

            {/* Set Selector Tabs */}
            <div style={{ display: 'flex', borderBottom: '1px solid var(--border)', background: 'var(--s1)', padding: '0 24px' }}>
              {(viewingQuestionsExam.sets || []).map((setObj, idx) => (
                <button
                  key={setObj.set_label || idx}
                  onClick={() => setActiveSetIndex(idx)}
                  style={{
                    padding: '12px 20px',
                    border: 'none',
                    background: 'transparent',
                    borderBottom: activeSetIndex === idx ? '2px solid var(--purple-l)' : '2px solid transparent',
                    color: activeSetIndex === idx ? 'var(--purple-l)' : 'var(--muted)',
                    fontWeight: activeSetIndex === idx ? 700 : 500,
                    fontSize: '0.88rem',
                    cursor: 'pointer'
                  }}
                >
                  Set {setObj.set_label} ({setObj.question_count} Qs)
                </button>
              ))}
            </div>

            {/* Questions Content */}
            <div style={{ padding: '24px', overflowY: 'auto', flex: 1 }}>
              {viewingQuestionsExam.sets && viewingQuestionsExam.sets[activeSetIndex] ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                  {viewingQuestionsExam.sets[activeSetIndex].questions.map((q, qIdx) => (
                    <div
                      key={q.id || qIdx}
                      style={{
                        background: 'var(--s2)',
                        border: '1px solid var(--border)',
                        borderRadius: '12px',
                        padding: '16px'
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', flexWrap: 'wrap', gap: '8px' }}>
                        <span style={{ fontWeight: 700, fontSize: '0.9rem', color: 'var(--purple-l)' }}>
                          Question #{qIdx + 1}
                        </span>
                        <span style={{ fontSize: '0.75rem', color: 'var(--muted)', background: 'var(--s3)', padding: '2px 8px', borderRadius: '4px' }}>
                          {q.topic}
                        </span>
                      </div>
                      <p style={{ fontSize: '0.92rem', color: 'var(--text)', marginBottom: '12px', lineHeight: '1.5', fontWeight: 500 }}>
                        {q.question_text}
                      </p>

                      {/* Options */}
                      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '8px' }}>
                        {(q.options || []).map((opt, oIdx) => {
                          const corr = String(q.correct_option ?? '').trim();
                          const isCorrect = corr === String(oIdx) || (corr.toUpperCase() === String.fromCharCode(65 + oIdx));
                          return (
                            <div
                              key={oIdx}
                              style={{
                                padding: '8px 12px',
                                borderRadius: '8px',
                                border: isCorrect ? '1.5px solid var(--green-l)' : '1px solid var(--border)',
                                background: isCorrect ? 'rgba(5,150,105,0.08)' : 'var(--s1)',
                                fontSize: '0.85rem',
                                color: isCorrect ? 'var(--green-l)' : 'var(--text)',
                                fontWeight: isCorrect ? 600 : 400
                              }}
                            >
                              <strong style={{ marginRight: '6px' }}>{String.fromCharCode(65 + oIdx)}.</strong> {opt} {isCorrect && '✓ (Correct)'}
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div style={{ textAlign: 'center', padding: '40px', color: 'var(--muted)' }}>No questions found for this set.</div>
              )}
            </div>

            {/* Modal Footer */}
            <div style={{ padding: '16px 24px', borderTop: '1px solid var(--border)', background: 'var(--s2)', display: 'flex', justifyContent: 'flex-end' }}>
              <button className="btn-primary" onClick={() => setViewingQuestionsExam(null)}>
                Close Preview
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default InstitutionExams;
