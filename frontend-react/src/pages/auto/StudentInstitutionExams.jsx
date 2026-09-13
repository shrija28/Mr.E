import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';

const StudentInstitutionExams = () => {
  const [subjects, setSubjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchExams = async () => {
      try {
        const res = await fetch('/api/student/exams', { credentials: 'include' });
        const data = await res.json();
        if (res.ok && data.subjects) {
          setSubjects(data.subjects);
        } else {
          setError(data.message || 'Could not load exams');
        }
      } catch (err) {
        setError('Network error while loading exams');
      } finally {
        setLoading(false);
      }
    };

    fetchExams();
  }, []);

  return (
    <>
      <div className="bg-mesh"></div>
      
      <main className="dash-main">
        <div className="dash-hero">
          <div>
            <h1 className="dash-title">Available <span className="hero-gradient">Exams</span></h1>
            <p className="dash-sub">Select an exam and question set to begin practice</p>
          </div>
        </div>

        {error && (
          <div style={{ padding: '12px 16px', background: 'rgba(239,68,68,0.1)', border: '1px solid var(--red)', borderRadius: '8px', color: 'var(--red)', marginBottom: '20px' }}>
            {error}
          </div>
        )}

        {loading ? (
          <div style={{ textAlign: 'center', padding: '60px', color: 'var(--muted)' }}>
            Loading available exams...
          </div>
        ) : (
          <div id="examsContainer">
            {subjects.length === 0 ? (
              <div className="section-card">
                <div style={{ textAlign: 'center', padding: '50px 20px', color: 'var(--muted)' }}>
                  <div style={{ fontSize: '2.5rem', marginBottom: '12px' }}>📝</div>
                  <h3>No Published Exams Available</h3>
                  <p style={{ marginTop: '6px' }}>New exams will appear here as soon as they are created and published by the administrator.</p>
                </div>
              </div>
            ) : (
              subjects.map(subjGroup => (
                <div key={subjGroup.subject} className="section-card" style={{ marginBottom: '24px' }}>
                  <div className="section-card-header" style={{ padding: '16px 20px', borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
                    <h2 style={{ fontSize: '1.25rem', color: 'var(--text)' }}>
                      📚 {subjGroup.subject}
                    </h2>
                    <span style={{ fontSize: '0.82rem', color: 'var(--muted)' }}>
                      {subjGroup.available_exams} {subjGroup.available_exams === 1 ? 'Exam' : 'Exams'} Available
                    </span>
                  </div>

                  <div className="section-body" style={{ padding: 0 }}>
                    <ul style={{ listStyle: 'none', margin: 0, padding: 0 }}>
                      {subjGroup.exams.map(exam => {
                        const defaultSet = exam.sets && exam.sets.length > 0 ? exam.sets[0] : null;
                        const defaultSetId = defaultSet ? defaultSet.exam_set_id : '';
                        
                        return (
                          <li 
                            key={exam.exam_id} 
                            style={{ 
                              padding: '20px', 
                              borderBottom: '1px solid rgba(255,255,255,0.04)',
                              display: 'flex',
                              flexWrap: 'wrap',
                              justifyContent: 'space-between',
                              alignItems: 'center',
                              gap: '16px'
                            }}
                          >
                            <div>
                              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap', marginBottom: '4px' }}>
                                <div style={{ fontSize: '1.1rem', fontWeight: 600, color: 'var(--blue)' }}>
                                  {exam.exam_name || `${subjGroup.subject} Examination`}
                                </div>
                                {exam.batch_name && exam.batch_name !== 'All Batches' ? (
                                  <span style={{ fontSize: '0.75rem', padding: '2px 8px', borderRadius: '4px', background: 'rgba(167, 139, 250, 0.15)', color: 'var(--purple-l)', fontWeight: 600 }}>
                                    👥 {exam.batch_name}
                                  </span>
                                ) : (
                                  <span style={{ fontSize: '0.75rem', padding: '2px 8px', borderRadius: '4px', background: 'rgba(255, 255, 255, 0.06)', color: 'var(--muted)' }}>
                                    👥 All Batches
                                  </span>
                                )}
                              </div>
                              <div style={{ fontSize: '0.85rem', color: 'var(--muted)', marginTop: '4px' }}>
                                Subject: <strong style={{ color: 'var(--text)' }}>{subjGroup.subject}</strong> • ⏱ {exam.duration_minutes || 60} Mins • 🎯 Max Marks: {exam.total_marks || 60}
                                {exam.scheduled_end && (
                                  <span style={{ marginLeft: '10px', color: '#eab308' }}>
                                    📅 Due {new Date(exam.scheduled_end).toLocaleDateString()}
                                  </span>
                                )}
                              </div>
                            </div>

                            {defaultSetId ? (
                              <Link 
                                to={`/exam?set=${defaultSetId}&subject=${encodeURIComponent(subjGroup.subject)}&name=${encodeURIComponent(exam.exam_name || subjGroup.subject)}&label=${defaultSet?.set_label || 'A'}`} 
                                className="btn-primary"
                                style={{ minWidth: '130px', textAlign: 'center' }}
                              >
                                Take Exam →
                              </Link>
                            ) : (
                              <button className="btn-primary" disabled style={{ opacity: 0.5 }}>
                                Unavailable
                              </button>
                            )}
                          </li>
                        );
                      })}
                    </ul>
                  </div>
                </div>
              ))
            )}
          </div>
        )}
      </main>
    </>
  );
};

export default StudentInstitutionExams;
