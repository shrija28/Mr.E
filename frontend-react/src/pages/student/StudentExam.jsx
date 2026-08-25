import React from 'react';

const StudentExam = () => {
  return (
    <main style={{ padding: '24px' }}>
      <header style={{ marginBottom: '24px' }}>
        <h1 style={{ fontSize: '1.8rem', fontWeight: '800' }}>Exams</h1>
        <p style={{ color: 'var(--muted)' }}>Take a new exam or review past attempts.</p>
      </header>

      <div style={{ display: 'grid', gap: '20px', gridTemplateColumns: '1fr' }}>
        <div className="section-card" style={{ padding: '24px' }}>
          <h2>Available Exams</h2>
          <p style={{ color: 'var(--muted)', marginTop: '8px', marginBottom: '16px' }}>Generate a new AI exam based on your syllabus.</p>
          <div style={{ display: 'flex', gap: '12px' }}>
            <button className="btn-primary">Generate New Exam</button>
          </div>
        </div>

        <div className="section-card" style={{ padding: '24px' }}>
          <h2>Past Exams</h2>
          <ul style={{ listStyle: 'none', padding: 0, marginTop: '16px' }}>
            <li style={{ display: 'flex', justifyContent: 'space-between', padding: '12px 0', borderBottom: '1px solid var(--border)' }}>
              <div>
                <strong>Physics Quiz 1</strong>
                <div style={{ fontSize: '0.85rem', color: 'var(--muted)' }}>Taken on Oct 12, 2026</div>
              </div>
              <div style={{ fontWeight: 'bold', color: 'var(--green-l)' }}>85%</div>
            </li>
            <li style={{ display: 'flex', justifyContent: 'space-between', padding: '12px 0', borderBottom: '1px solid var(--border)' }}>
              <div>
                <strong>Chemistry Mock</strong>
                <div style={{ fontSize: '0.85rem', color: 'var(--muted)' }}>Taken on Oct 10, 2026</div>
              </div>
              <div style={{ fontWeight: 'bold', color: 'var(--yellow-l)' }}>68%</div>
            </li>
            <li style={{ display: 'flex', justifyContent: 'space-between', padding: '12px 0' }}>
              <div>
                <strong>Biology Practice</strong>
                <div style={{ fontSize: '0.85rem', color: 'var(--muted)' }}>Taken on Oct 8, 2026</div>
              </div>
              <div style={{ fontWeight: 'bold', color: 'var(--red-l)' }}>45%</div>
            </li>
          </ul>
        </div>
      </div>
    </main>
  );
};

export default StudentExam;
