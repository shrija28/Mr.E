import React, { useState } from 'react';
import { Link } from 'react-router-dom';

const initialExams = [];

const AdminExams = () => {
  const [exams, setExams] = useState(() => {
    const saved = localStorage.getItem('mockAdminExams');
    return saved ? JSON.parse(saved) : [];
  });
  const [examName, setExamName] = useState('');
  const [subject, setSubject] = useState('');
  const [source, setSource] = useState('');
  const [viewExam, setViewExam] = useState(null);
  
  const [message, setMessage] = useState('');
  const [isError, setIsError] = useState(false);

  React.useEffect(() => {
    localStorage.setItem('mockAdminExams', JSON.stringify(exams));
  }, [exams]);

  const handleCreateExam = () => {
    if (!examName.trim()) {
      setMessage('Please enter an Exam Name.');
      setIsError(true);
      return;
    }
    if (!subject) {
      setMessage('Please select a Subject.');
      setIsError(true);
      return;
    }
    
    const newExam = {
      id: Date.now(),
      name: examName.trim(),
      subject: subject,
      source: source === 'question_paper' ? 'Previous Year Papers' : source === 'textbook' ? 'Textbooks (AI-Generated)' : 'Both',
      created: new Date().toISOString().split('T')[0],
      sets: 4,
      status: 'Draft'
    };

    setExams([newExam, ...exams]);
    setExamName('');
    setSubject('');
    setSource('');
    
    setMessage('Exam created successfully!');
    setIsError(false);
    
    setTimeout(() => {
      setMessage('');
    }, 3000);
  };

  const getSourceHint = () => {
    if (source === 'question_paper') return 'Only questions from uploaded PYQs';
    if (source === 'textbook') return 'Only questions extracted from Textbooks';
    return 'Mix of PYQ and textbook questions';
  };

  const togglePublish = (id) => {
    setExams(exams.map(exam => {
      if (exam.id === id) {
        return {
          ...exam,
          status: exam.status === 'Draft' ? 'Active' : 'Draft'
        };
      }
      return exam;
    }));
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
              <p className="section-sub">Generate a new exam set (4 sets × 20 questions = 80 questions) · Choose source: Previous Year Papers or Textbooks</p>
            </div>
          </div>
          <div className="section-body">
            <div style={{"display":"flex","gap":"12px","alignItems":"flex-end","flexWrap":"wrap"}}>
              <div className="input-group">
                <label className="input-label" htmlFor="examNameInput">Exam Name</label>
                <input 
                  type="text" 
                  id="examNameInput" 
                  className="text-input" 
                  placeholder="e.g. Mid-Term 2024" 
                  style={{"minWidth":"200px"}}
                  value={examName}
                  onChange={(e) => setExamName(e.target.value)}
                />
              </div>
              <div className="input-group">
                <label className="input-label" htmlFor="subjectSelect">Subject</label>
                <select 
                  id="subjectSelect" 
                  className="text-input" 
                  style={{"minWidth":"200px"}}
                  value={subject}
                  onChange={(e) => setSubject(e.target.value)}
                >
                  <option value="" disabled>Select subject…</option>
                  <option value="Biology">Biology</option>
                  <option value="Physics">Physics</option>
                  <option value="Chemistry">Chemistry</option>
                  <option value="Mathematics">Mathematics</option>
                </select>
              </div>
              <div className="input-group">
                <label className="input-label" htmlFor="sourceSelect">Question Source</label>
                <select 
                  id="sourceSelect" 
                  className="text-input" 
                  style={{"minWidth":"220px"}}
                  value={source}
                  onChange={(e) => setSource(e.target.value)}
                >
                  <option value="">Both (any source)</option>
                  <option value="question_paper">Previous Year Papers</option>
                  <option value="textbook">Textbooks (AI-Generated)</option>
                </select>
                <div style={{"fontSize":"0.72rem","color":"var(--muted)","marginTop":"2px"}}>
                  <span>{getSourceHint()}</span>
                </div>
              </div>
              <button className="btn-primary" onClick={handleCreateExam}>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{"width":"15px","height":"15px"}}><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
                Create Exam
              </button>
            </div>
            {message && (
              <div style={{"marginTop":"12px", color: isError ? 'var(--red)' : 'var(--green)', fontSize: '0.9rem', fontWeight: 'bold'}}>
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
              <h2>All Exams</h2>
              <p className="section-sub">{exams.length} total exams found</p>
            </div>
          </div>
          <div className="section-body" style={{"padding":"0"}}>
            <div className="table-scroll">
              <table className="results-table">
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Subject</th>
                    <th>Source</th>
                    <th>Created</th>
                    <th>Sets</th>
                    <th>Status</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {exams.length > 0 ? (
                    exams.map(exam => (
                      <tr key={exam.id}>
                        <td style={{fontWeight: 600, color: 'var(--blue)'}}>{exam.name}</td>
                        <td>{exam.subject}</td>
                        <td>{exam.source}</td>
                        <td>{exam.created}</td>
                        <td>{exam.sets}</td>
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
                          <button 
                            className="btn-outline small"
                            onClick={() => togglePublish(exam.id)}
                            style={exam.status === 'Draft' ? {borderColor: 'var(--blue)', color: 'var(--blue)'} : {borderColor: 'var(--red)', color: 'var(--red)'}}
                          >
                            {exam.status === 'Draft' ? 'Publish' : 'Unpublish'}
                          </button>
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr><td colSpan="7" style={{"textAlign":"center","color":"var(--muted)","padding":"32px"}}>No exams found.</td></tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

export default AdminExams;
