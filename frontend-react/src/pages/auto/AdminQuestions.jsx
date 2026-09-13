import React, { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';

const AdminQuestions = () => {
  const [questions, setQuestions] = useState([]);
  const [counts, setCounts] = useState({});
  const [filterSubject, setFilterSubject] = useState("");
  const [filterSource, setFilterSource] = useState("");
  const [currentPage, setCurrentPage] = useState(1);
  const [totalQuestions, setTotalQuestions] = useState(0);
  const [pageSize, setPageSize] = useState(15);
  const [loading, setLoading] = useState(false);
  const [deleteId, setDeleteId] = useState(null);
  const [deleting, setDeleting] = useState(false);
  const [expandedId, setExpandedId] = useState(null);

  // Clear modal state
  const [showClearConfirm, setShowClearConfirm] = useState(false);
  const [clearing, setClearing] = useState(false);

  const fetchCounts = useCallback(async () => {
    try {
      const res = await fetch('/api/admin/questions/counts', { credentials: 'include' });
      const data = await res.json();
      if (res.ok && data.counts) {
        setCounts(data.counts);
      }
    } catch (err) {
      console.error('Failed to fetch counts', err);
    }
  }, []);

  const fetchQuestions = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      params.append('page', currentPage);
      params.append('page_size', pageSize);
      if (filterSubject) params.append('subject', filterSubject);
      if (filterSource) params.append('source', filterSource);

      const res = await fetch(`/api/admin/questions?${params.toString()}`, { credentials: 'include' });
      const data = await res.json();
      if (res.ok && data.questions) {
        setQuestions(data.questions);
        setTotalQuestions(data.total || 0);
        if (data.counts_by_subject) {
          setCounts(data.counts_by_subject);
        }
      }
    } catch (err) {
      console.error('Failed to fetch questions', err);
    } finally {
      setLoading(false);
    }
  }, [currentPage, pageSize, filterSubject, filterSource]);

  useEffect(() => {
    fetchCounts();
  }, [fetchCounts]);

  useEffect(() => {
    fetchQuestions();
  }, [fetchQuestions]);

  const totalPages = Math.ceil(totalQuestions / pageSize) || 1;

  const handleDeleteClick = (id) => {
    setDeleteId(id);
  };

  const confirmDelete = async () => {
    if (!deleteId) return;
    setDeleting(true);
    try {
      const res = await fetch(`/api/admin/questions/${deleteId}`, {
        method: 'DELETE',
        credentials: 'include',
      });
      if (res.ok) {
        setDeleteId(null);
        fetchQuestions();
        fetchCounts();
      } else {
        const data = await res.json().catch(() => ({}));
        alert(data.message || 'Failed to delete question');
      }
    } catch (err) {
      console.error('Error deleting question', err);
      alert('Network error while deleting question');
    } finally {
      setDeleting(false);
    }
  };

  const handleClearQuestions = async () => {
    setClearing(true);
    try {
      const res = await fetch('/api/admin/questions/clear', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ subject: filterSubject || null })
      });
      if (res.ok) {
        setShowClearConfirm(false);
        setCurrentPage(1);
        fetchQuestions();
        fetchCounts();
      } else {
        const data = await res.json().catch(() => ({}));
        alert(data.message || 'Failed to clear questions');
      }
    } catch (err) {
      console.error('Failed to clear questions', err);
      alert('Network error while clearing questions');
    } finally {
      setClearing(false);
    }
  };

  const totalStored = Object.values(counts).reduce((a, b) => a + (Number(b) || 0), 0);

  return (
    <>
      <div className="bg-mesh"></div>
      
      <div className="main-wrap">
        <div className="section-card">
          <div className="section-card-header">
            <div className="section-icon purple">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>
            </div>
            <div>
              <h2>Question Bank (Stored Questions)</h2>
              <p className="section-sub">
                {totalStored} questions stored · Only questions uploaded and generated in the Upload section are saved here
              </p>
            </div>
          </div>
          <div className="section-body">
            
            <div className="filter-row" style={{ display: 'flex', gap: '16px', flexWrap: 'wrap', alignItems: 'center' }}>
              <div className="filter-group">
                <label className="input-label" htmlFor="subjectFilter">Filter by Subject</label>
                <select 
                  className="select-input" 
                  id="subjectFilter" 
                  value={filterSubject}
                  onChange={(e) => {
                    setFilterSubject(e.target.value);
                    setCurrentPage(1);
                  }}
                  style={{ minWidth: '180px' }}
                >
                  <option value="">All Subjects</option>
                  <option value="Biology">Biology</option>
                  <option value="Physics">Physics</option>
                  <option value="Chemistry">Chemistry</option>
                  <option value="Mathematics">Mathematics</option>
                </select>
              </div>

              <div className="filter-group">
                <label className="input-label" htmlFor="sourceFilter">Filter by Source</label>
                <select 
                  className="select-input" 
                  id="sourceFilter" 
                  value={filterSource}
                  onChange={(e) => {
                    setFilterSource(e.target.value);
                    setCurrentPage(1);
                  }}
                  style={{ minWidth: '180px' }}
                >
                  <option value="">All Sources</option>
                  <option value="textbook">Textbook Generated</option>
                  <option value="question_paper">Question Paper Extracted</option>
                </select>
              </div>

              <div className="filter-group">
                <label className="input-label" htmlFor="pageSizeSelect">Per Page</label>
                <select 
                  className="select-input" 
                  id="pageSizeSelect" 
                  value={pageSize}
                  onChange={(e) => {
                    setPageSize(Number(e.target.value));
                    setCurrentPage(1);
                  }}
                  style={{ minWidth: '100px' }}
                >
                  <option value={10}>10</option>
                  <option value={15}>15</option>
                  <option value={25}>25</option>
                  <option value={50}>50</option>
                </select>
              </div>

              {totalStored > 0 && (
                <div style={{ marginLeft: 'auto' }}>
                  <button 
                    className="btn-outline small"
                    onClick={() => setShowClearConfirm(true)}
                    style={{ color: 'var(--red)', borderColor: 'rgba(239, 68, 68, 0.3)', padding: '6px 14px' }}
                  >
                    🗑 Clear {filterSubject ? `${filterSubject} Questions` : 'All Questions'}
                  </button>
                </div>
              )}
            </div>

            <div id="subjectCounts" style={{ display: "flex", gap: "10px", flexWrap: "wrap", marginTop: "16px" }}>
              {['Biology', 'Physics', 'Chemistry', 'Mathematics'].map(subj => {
                const count = counts[subj] || 0;
                const isSelected = filterSubject === subj;
                return (
                  <button 
                    key={subj} 
                    onClick={() => {
                      setFilterSubject(isSelected ? "" : subj);
                      setCurrentPage(1);
                    }}
                    style={{ 
                      background: isSelected ? 'var(--blue)' : 'var(--card-bg)', 
                      color: isSelected ? '#fff' : 'var(--text)',
                      border: isSelected ? '1px solid var(--blue)' : '1px solid var(--border)',
                      padding: '6px 14px', 
                      borderRadius: '20px', 
                      fontSize: '0.85rem',
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '6px',
                      fontWeight: 500,
                      transition: 'all 0.2s ease'
                    }}
                  >
                    <span>{subj}</span>
                    <span style={{ 
                      background: isSelected ? 'rgba(255,255,255,0.25)' : 'rgba(0,0,0,0.06)',
                      padding: '2px 8px', 
                      borderRadius: '10px', 
                      fontSize: '0.78rem',
                      fontWeight: 'bold'
                    }}>
                      {count}
                    </span>
                  </button>
                );
              })}
            </div>
          </div>
        </div>

        <div className="section-card results-card">
          <div className="results-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '16px 20px', borderBottom: '1px solid var(--border)' }}>
            <h3 id="tableTitle" style={{ margin: 0 }}>
              {filterSubject ? `${filterSubject} Questions` : 'Stored Questions'} ({totalQuestions})
            </h3>
            {totalQuestions > 0 && (
              <span id="pageInfo" style={{ fontSize: "0.85rem", color: "var(--muted)" }}>
                Page {totalQuestions === 0 ? 0 : currentPage} of {totalPages}
              </span>
            )}
          </div>

          {loading ? (
            <div style={{ textAlign: 'center', padding: '50px', color: 'var(--muted)' }}>
              ⏳ Loading stored questions from database...
            </div>
          ) : questions.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '60px 20px', color: 'var(--muted)' }}>
              <div style={{ fontSize: '3rem', marginBottom: '16px' }}>📚</div>
              <h3 style={{ margin: '0 0 8px 0', color: 'var(--text)' }}>
                {filterSubject ? `No ${filterSubject} Questions in Bank` : 'Your Question Bank is Clean (0 Questions)'}
              </h3>
              <p style={{ margin: '0 0 20px 0', fontSize: '0.92rem', maxWidth: '500px', marginInline: 'auto', lineHeight: 1.5 }}>
                Questions will only be stored here when you upload materials in the Upload section and generate question sets.
              </p>
              <Link to="/admin/upload" className="btn-primary" style={{ textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: '8px' }}>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ width: '16px', height: '16px' }}>
                  <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/>
                </svg>
                Upload Materials &amp; Generate Questions →
              </Link>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column' }}>
              {questions.map((q, idx) => {
                const questionIndex = (currentPage - 1) * pageSize + idx + 1;
                const isExpanded = expandedId === q.id;
                const opts = Array.isArray(q.options) ? q.options : [];
                const correctIdx = parseInt(q.correct_option, 10);
                const optLabels = ['A', 'B', 'C', 'D'];

                return (
                  <div 
                    key={q.id} 
                    style={{ 
                      padding: '16px 20px', 
                      borderBottom: '1px solid var(--border)',
                      background: isExpanded ? 'rgba(59, 130, 246, 0.02)' : 'transparent',
                      transition: 'background 0.15s ease'
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '12px' }}>
                      <div style={{ flex: 1 }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
                          <span style={{ fontWeight: 'bold', color: 'var(--blue)', fontSize: '0.9rem' }}>
                            #{questionIndex}
                          </span>
                          <span style={{ 
                            fontSize: '0.75rem', 
                            padding: '2px 8px', 
                            borderRadius: '10px', 
                            background: q.subject === 'Biology' ? 'rgba(16, 185, 129, 0.1)' : q.subject === 'Physics' ? 'rgba(59, 130, 246, 0.1)' : 'rgba(245, 158, 11, 0.1)',
                            color: q.subject === 'Biology' ? '#059669' : q.subject === 'Physics' ? '#2563eb' : '#d97706',
                            fontWeight: 600
                          }}>
                            {q.subject}
                          </span>
                          {q.topic && (
                            <span style={{ fontSize: '0.75rem', color: 'var(--muted)', background: 'var(--card-bg)', border: '1px solid var(--border)', padding: '2px 8px', borderRadius: '10px' }}>
                              {q.topic}
                            </span>
                          )}
                          {q.source_type && (
                            <span style={{ fontSize: '0.72rem', color: '#6b7280', padding: '1px 6px', borderRadius: '4px', background: 'rgba(0,0,0,0.03)' }}>
                              {q.source_type}
                            </span>
                          )}
                        </div>
                        <p style={{ margin: 0, fontSize: '0.96rem', fontWeight: 500, color: 'var(--text)', lineHeight: 1.5 }}>
                          {q.question || q.question_text}
                        </p>
                      </div>

                      <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                        <button 
                          className="btn-outline small"
                          onClick={() => setExpandedId(isExpanded ? null : q.id)}
                          style={{ fontSize: '0.78rem' }}
                        >
                          {isExpanded ? 'Hide Options' : 'View Options'}
                        </button>
                        <button 
                          className="btn-outline small" 
                          onClick={() => handleDeleteClick(q.id)} 
                          style={{ color: 'var(--red)', borderColor: 'rgba(239,68,68,0.3)', fontSize: '0.78rem' }}
                          title="Delete Question"
                        >
                          Delete
                        </button>
                      </div>
                    </div>

                    {isExpanded && (
                      <div style={{ marginTop: '14px', paddingTop: '12px', borderTop: '1px dashed var(--border)' }}>
                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '8px', marginBottom: '10px' }}>
                          {opts.map((opt, optIdx) => {
                            const isCorrect = optIdx === correctIdx;
                            return (
                              <div 
                                key={optIdx} 
                                style={{ 
                                  padding: '8px 12px', 
                                  borderRadius: '6px',
                                  fontSize: '0.85rem',
                                  background: isCorrect ? 'rgba(16, 185, 129, 0.08)' : 'rgba(0,0,0,0.02)',
                                  border: isCorrect ? '1px solid #10b981' : '1px solid var(--border)',
                                  color: 'var(--text)',
                                  display: 'flex',
                                  alignItems: 'center',
                                  gap: '6px'
                                }}
                              >
                                <strong style={{ color: isCorrect ? '#10b981' : 'var(--muted)' }}>
                                  ({optLabels[optIdx]})
                                </strong>
                                <span>{opt}</span>
                                {isCorrect && <span style={{ marginLeft: 'auto', color: '#10b981', fontSize: '0.75rem', fontWeight: 'bold' }}>✓ Correct</span>}
                              </div>
                            );
                          })}
                        </div>
                        {q.explanation && (
                          <div style={{ fontSize: '0.82rem', color: 'var(--muted)', fontStyle: 'italic', background: 'rgba(59, 130, 246, 0.04)', padding: '8px 12px', borderRadius: '6px' }}>
                            💡 <strong>Explanation:</strong> {q.explanation}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}

          {totalQuestions > 0 && (
            <div className="table-footer" style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: '16px 20px', borderTop: '1px solid var(--border)' }}>
              <span id="totalInfo" style={{ fontSize: "0.82rem", color: "var(--muted)" }}>
                Showing {(currentPage - 1) * pageSize + 1} to {Math.min(currentPage * pageSize, totalQuestions)} of {totalQuestions} entries
              </span>
              <div style={{ display: "flex", gap: "8px" }}>
                <button 
                  className="btn-outline small" 
                  onClick={() => setCurrentPage(prev => Math.max(prev - 1, 1))}
                  disabled={currentPage === 1 || loading}
                >
                  Previous
                </button>
                <button 
                  className="btn-outline small" 
                  onClick={() => setCurrentPage(prev => Math.min(prev + 1, totalPages))}
                  disabled={currentPage === totalPages || totalPages === 0 || loading}
                >
                  Next
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Delete Single Question Modal */}
        {deleteId !== null && (
          <div id="deleteDialog" style={{ position: "fixed", inset: "0", background: "rgba(0,0,0,0.75)", backdropFilter: "blur(8px)", zIndex: "200", display: "flex", alignItems: "center", justifyContent: "center", padding: "20px" }}>
            <div style={{ background: "var(--card-bg, #fff)", border: "1px solid var(--border)", borderRadius: "8px", padding: "28px", maxWidth: "420px", width: "100%", boxShadow: '0 10px 25px rgba(0,0,0,0.2)' }}>
              <h3 style={{ fontSize: "1.15rem", fontWeight: "700", marginBottom: "10px", color: 'var(--text)' }}>Delete Question</h3>
              <p style={{ color: "var(--muted)", fontSize: "0.88rem", marginBottom: "20px", lineHeight: 1.5 }}>
                Are you sure you want to permanently delete this question from the Question Bank?
              </p>
              <div style={{ display: "flex", gap: "12px" }}>
                <button 
                  className="btn-outline" 
                  onClick={() => setDeleteId(null)} 
                  disabled={deleting}
                  style={{ flex: "1", justifyContent: "center" }}
                >
                  Cancel
                </button>
                <button 
                  className="btn-primary" 
                  onClick={confirmDelete} 
                  disabled={deleting}
                  style={{ flex: "1", justifyContent: "center", background: "#ef4444", color: "#fff", border: "none" }}
                >
                  {deleting ? 'Deleting...' : 'Delete'}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Clear Question Bank Modal */}
        {showClearConfirm && (
          <div style={{ position: "fixed", inset: "0", background: "rgba(0,0,0,0.75)", backdropFilter: "blur(8px)", zIndex: "200", display: "flex", alignItems: "center", justifyContent: "center", padding: "20px" }}>
            <div style={{ background: "var(--card-bg, #fff)", border: "1px solid var(--border)", borderRadius: "8px", padding: "28px", maxWidth: "440px", width: "100%", boxShadow: '0 10px 25px rgba(0,0,0,0.2)' }}>
              <h3 style={{ fontSize: "1.15rem", fontWeight: "700", marginBottom: "10px", color: '#ef4444' }}>
                ⚠️ Clear {filterSubject ? `${filterSubject} Questions` : 'All Questions'}?
              </h3>
              <p style={{ color: "var(--muted)", fontSize: "0.88rem", marginBottom: "20px", lineHeight: 1.5 }}>
                This will delete {filterSubject ? `all ${filterSubject}` : 'all'} questions from the Question Bank. Only new questions that you generate from the Upload section will be stored going forward.
              </p>
              <div style={{ display: "flex", gap: "12px" }}>
                <button 
                  className="btn-outline" 
                  onClick={() => setShowClearConfirm(false)} 
                  disabled={clearing}
                  style={{ flex: "1", justifyContent: "center" }}
                >
                  Cancel
                </button>
                <button 
                  className="btn-primary" 
                  onClick={handleClearQuestions} 
                  disabled={clearing}
                  style={{ flex: "1", justifyContent: "center", background: "#ef4444", color: "#fff", border: "none" }}
                >
                  {clearing ? 'Clearing...' : 'Yes, Clear Questions'}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </>
  );
};

export default AdminQuestions;
