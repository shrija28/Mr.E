import React from 'react';
import { Link } from 'react-router-dom';

const StudentInstitutionExams = () => {
  return (
    <>
      {/* Auto-injected styles from HTML head */}
      <style dangerouslySetInnerHTML={{ __html: `` }} />
      
      <div className="bg-mesh"></div>
      
      <main className="dash-main">
        <div className="dash-hero">
          <div>
            <h1 className="dash-title">My <span className="hero-gradient">Exams</span></h1>
            <p className="dash-sub">Only your institution's exams are shown here</p>
          </div>
        </div>
        <div id="examsContainer">
          <div className="section-card">
            <div className="section-body" style={{"padding":"0"}}>
              <ul style={{ listStyle: 'none', margin: 0, padding: 0 }}>
                {(() => {
                  const exams = JSON.parse(localStorage.getItem('mockAdminExams') || '[]').filter(e => e.status === 'Active');
                  if (exams.length === 0) {
                    return <li style={{"textAlign":"center","padding":"40px","color":"var(--muted)"}}>No exams available yet.</li>;
                  }
                  return exams.map((exam, i) => (
                    <li key={i} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '16px 20px', borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
                      <div>
                        <div style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--blue)' }}>{exam.name}</div>
                        <div style={{ fontSize: '0.85rem', color: 'var(--muted)', marginTop: '4px' }}>
                          <span style={{ color: 'var(--text)' }}>{exam.subject}</span> • {exam.source} • {exam.sets} Sets
                        </div>
                      </div>
                      <Link to={`/exam?subject=${exam.subject}&name=${encodeURIComponent(exam.name)}`} className="btn-primary">
                        Take Exam
                      </Link>
                    </li>
                  ));
                })()}
              </ul>
            </div>
          </div>
        </div>
      </main>
    </>
  );
};

export default StudentInstitutionExams;
