import React from 'react';

const StudentSyllabus = () => {
  return (
    <main style={{ padding: '24px' }}>
      <header style={{ marginBottom: '24px' }}>
        <h1 style={{ fontSize: '1.8rem', fontWeight: '800' }}>Syllabus</h1>
        <p style={{ color: 'var(--muted)' }}>Review topics and track your mastery.</p>
      </header>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '20px' }}>
        {['Physics', 'Chemistry', 'Mathematics', 'Biology'].map(subject => (
          <div key={subject} className="section-card" style={{ padding: '24px' }}>
            <h2 style={{ marginBottom: '12px', fontSize: '1.2rem' }}>{subject}</h2>
            <div style={{ height: '8px', background: 'var(--s2)', borderRadius: '4px', overflow: 'hidden', marginBottom: '12px' }}>
              <div style={{ width: `${Math.floor(Math.random() * 60) + 20}%`, height: '100%', background: 'var(--purple-l)' }}></div>
            </div>
            <p style={{ fontSize: '0.85rem', color: 'var(--muted)' }}>Mastery level based on recent exams.</p>
            <button className="btn-outline" style={{ marginTop: '16px', width: '100%' }}>View Topics</button>
          </div>
        ))}
      </div>
    </main>
  );
};

export default StudentSyllabus;
