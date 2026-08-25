import React from 'react';
import { Link } from 'react-router-dom';

const StudentDashboard = () => {
  return (
    <main style={{ padding: '24px' }}>
      <header style={{ marginBottom: '24px' }}>
        <h1 style={{ fontSize: '1.8rem', fontWeight: '800' }}>Dashboard</h1>
        <p style={{ color: 'var(--muted)' }}>Welcome back! Here's your study progress.</p>
      </header>

      {/* KPI Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '20px', marginBottom: '24px' }}>
        <div className="section-card" style={{ padding: '20px' }}>
          <h3 style={{ fontSize: '0.85rem', color: 'var(--muted)', textTransform: 'uppercase', marginBottom: '8px' }}>Exams Taken</h3>
          <div style={{ fontSize: '2rem', fontWeight: '800', color: 'var(--text)' }}>12</div>
        </div>
        <div className="section-card" style={{ padding: '20px' }}>
          <h3 style={{ fontSize: '0.85rem', color: 'var(--muted)', textTransform: 'uppercase', marginBottom: '8px' }}>Avg. Score</h3>
          <div style={{ fontSize: '2rem', fontWeight: '800', color: 'var(--green-l)' }}>78%</div>
        </div>
        <div className="section-card" style={{ padding: '20px' }}>
          <h3 style={{ fontSize: '0.85rem', color: 'var(--muted)', textTransform: 'uppercase', marginBottom: '8px' }}>Global Rank</h3>
          <div style={{ fontSize: '2rem', fontWeight: '800', color: 'var(--purple-l)' }}>#1,240</div>
        </div>
        <div className="section-card" style={{ padding: '20px' }}>
          <h3 style={{ fontSize: '0.85rem', color: 'var(--muted)', textTransform: 'uppercase', marginBottom: '8px' }}>Questions Attempted</h3>
          <div style={{ fontSize: '2rem', fontWeight: '800', color: 'var(--blue-l)' }}>560</div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '20px' }}>
        {/* Main Content Area */}
        <div className="section-card" style={{ padding: '24px' }}>
          <h2 style={{ marginBottom: '16px' }}>Recent Performance</h2>
          <div style={{ height: '300px', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'var(--s2)', borderRadius: 'var(--r)' }}>
            <p style={{ color: 'var(--muted)' }}>[Chart Placeholder]</p>
          </div>
        </div>

        {/* Sidebar Actions */}
        <div className="section-card" style={{ padding: '24px' }}>
          <h2 style={{ marginBottom: '16px' }}>Quick Actions</h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <Link to="/exam" className="btn-primary" style={{ textAlign: 'center' }}>Take New Exam</Link>
            <Link to="/syllabus" className="btn-outline" style={{ textAlign: 'center' }}>View Syllabus</Link>
          </div>

          <h2 style={{ marginTop: '32px', marginBottom: '16px', fontSize: '1.1rem' }}>Subject Strength</h2>
          <ul style={{ listStyle: 'none', padding: 0 }}>
            <li style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}><span>Physics</span><span style={{ color: 'var(--green-l)' }}>High</span></li>
            <li style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}><span>Chemistry</span><span style={{ color: 'var(--blue-l)' }}>Medium</span></li>
            <li style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}><span>Mathematics</span><span style={{ color: 'var(--yellow-l)' }}>Medium</span></li>
            <li style={{ display: 'flex', justifyContent: 'space-between' }}><span>Biology</span><span style={{ color: 'var(--red-l)' }}>Needs Work</span></li>
          </ul>
        </div>
      </div>
    </main>
  );
};

export default StudentDashboard;
