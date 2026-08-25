import React, { useState, useMemo } from 'react';

const mockQuestions = Array.from({ length: 45 }, (_, i) => {
  const subjects = ['Biology', 'Physics', 'Chemistry', 'Mathematics'];
  const topics = {
    'Biology': ['Cell Biology', 'Genetics', 'Ecology', 'Human Anatomy'],
    'Physics': ['Mechanics', 'Thermodynamics', 'Electromagnetism', 'Optics'],
    'Chemistry': ['Organic', 'Inorganic', 'Physical', 'Biochemistry'],
    'Mathematics': ['Calculus', 'Algebra', 'Trigonometry', 'Geometry']
  };
  const subject = 'Biology';
  const topicList = topics[subject];
  return {
    id: i + 1,
    subject: subject,
    question: `Mock Question ${i + 1} for ${subject}: Which of the following is correct?`,
    topic: topicList[i % topicList.length]
  };
});

const AdminQuestions = () => {
  const [questions, setQuestions] = useState(mockQuestions);
  const [filterSubject, setFilterSubject] = useState("");
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 10;
  
  const [deleteId, setDeleteId] = useState(null);

  const filteredQuestions = useMemo(() => {
    if (!filterSubject) return questions;
    return questions.filter(q => q.subject === filterSubject);
  }, [questions, filterSubject]);

  const totalPages = Math.ceil(filteredQuestions.length / itemsPerPage);
  const currentQuestions = filteredQuestions.slice((currentPage - 1) * itemsPerPage, currentPage * itemsPerPage);

  const handleDeleteClick = (id) => {
    setDeleteId(id);
  };

  const confirmDelete = () => {
    setQuestions(questions.filter(q => q.id !== deleteId));
    setDeleteId(null);
  };

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
              <h2>Question Bank</h2>
              <p className="section-sub">Manage generated questions across all subjects</p>
            </div>
          </div>
          <div className="section-body">
            
            <div className="filter-row">
              <div className="filter-group">
                <label className="input-label" htmlFor="subjectFilter">Subject</label>
                <select 
                  className="select-input" 
                  id="subjectFilter" 
                  value={filterSubject}
                  onChange={(e) => {
                    setFilterSubject(e.target.value);
                    setCurrentPage(1);
                  }}
                >
                  <option value="">All Subjects</option>
                  <option value="Biology">Biology</option>
                  <option value="Physics">Physics</option>
                  <option value="Chemistry">Chemistry</option>
                  <option value="Mathematics">Mathematics</option>
                </select>
              </div>
            </div>

            <div id="subjectCounts" style={{display:"flex", gap:"12px", flexWrap:"wrap", marginTop:"16px"}}>
              {['Biology', 'Physics', 'Chemistry', 'Mathematics'].map(subj => {
                const count = questions.filter(q => q.subject === subj).length;
                if (count === 0) return null;
                return (
                  <div key={subj} style={{ background: 'var(--s2)', padding: '6px 12px', borderRadius: '4px', fontSize: '0.85rem' }}>
                    <span style={{ fontWeight: 'bold' }}>{subj}:</span> {count}
                  </div>
                )
              })}
            </div>
          </div>
        </div>

        <div className="section-card results-card">
          <div className="results-header">
            <h3 id="tableTitle">Questions</h3>
            <span id="pageInfo" style={{"fontSize":"0.82rem","color":"var(--muted)"}}>
              Page {totalPages === 0 ? 0 : currentPage} of {totalPages}
            </span>
          </div>
          <div className="table-scroll">
            <table className="results-table">
              <thead>
                <tr>
                  <th>#</th>
                  <th>Subject</th>
                  <th>Question</th>
                  <th>Topic</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {currentQuestions.length > 0 ? (
                  currentQuestions.map(q => (
                    <tr key={q.id}>
                      <td>{q.id}</td>
                      <td>{q.subject}</td>
                      <td>{q.question}</td>
                      <td>{q.topic}</td>
                      <td>
                        <button className="btn-outline small" onClick={() => handleDeleteClick(q.id)} style={{ color: 'var(--red)', borderColor: 'rgba(239,68,68,0.2)' }}>
                          Delete
                        </button>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan="5" style={{ textAlign: 'center', padding: '20px' }}>No questions found.</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
          <div className="table-footer" style={{"display":"flex","alignItems":"center","justifyContent":"space-between"}}>
            <span id="totalInfo" style={{"fontSize":"0.78rem","color":"var(--muted)"}}>
              Showing {filteredQuestions.length > 0 ? (currentPage - 1) * itemsPerPage + 1 : 0} to {Math.min(currentPage * itemsPerPage, filteredQuestions.length)} of {filteredQuestions.length} entries
            </span>
            <div style={{"display":"flex","gap":"8px"}}>
              <button 
                className="btn-outline small" 
                onClick={() => setCurrentPage(prev => Math.max(prev - 1, 1))}
                disabled={currentPage === 1}
              >
                Previous
              </button>
              <button 
                className="btn-outline small" 
                onClick={() => setCurrentPage(prev => Math.min(prev + 1, totalPages))}
                disabled={currentPage === totalPages || totalPages === 0}
              >
                Next
              </button>
            </div>
          </div>
        </div>

        {deleteId !== null && (
          <div id="deleteDialog" style={{"position":"fixed","inset":"0","background":"rgba(0,0,0,0.75)","backdropFilter":"blur(8px)","zIndex":"200", display:"flex","alignItems":"center","justifyContent":"center","padding":"20px"}}>
            <div style={{"background":"var(--s1)","border":"1px solid var(--border2)","borderRadius":"var(--r)","padding":"32px","maxWidth":"400px","width":"100%"}}>
              <h3 style={{"fontSize":"1.1rem","fontWeight":"700","marginBottom":"12px"}}>Delete Question</h3>
              <p style={{"color":"var(--muted2)","fontSize":"0.88rem","marginBottom":"24px"}}>Are you sure you want to delete this question? This action cannot be undone.</p>
              <div style={{"display":"flex","gap":"10px"}}>
                <button className="btn-outline" onClick={() => setDeleteId(null)} style={{"flex":"1","justifyContent":"center"}}>Cancel</button>
                <button className="btn-primary" onClick={confirmDelete} style={{"flex":"1","justifyContent":"center","background":"linear-gradient(135deg,var(--red),var(--orange))"}}>Delete</button>
              </div>
            </div>
          </div>
        )}
      </div>
    </>
  );
};

export default AdminQuestions;
