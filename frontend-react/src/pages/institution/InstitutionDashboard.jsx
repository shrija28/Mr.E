import React from 'react';
import { Link } from 'react-router-dom';

const InstitutionDashboard = () => {
  return (
    <main style={{ padding: '24px' }}>
      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <div>
          <h1 style={{ fontSize: '1.8rem', fontWeight: '800' }}>Institution Dashboard</h1>
          <p style={{ color: 'var(--muted)' }}>Overview of your students and performance.</p>
        </div>
        <Link to="/institution/students" className="btn-primary">Manage Students</Link>
      </header>

      {/* KPI Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '20px', marginBottom: '24px' }}>
        <div className="section-card" style={{ padding: '20px' }}>
          <h3 style={{ fontSize: '0.85rem', color: 'var(--muted)', textTransform: 'uppercase', marginBottom: '8px' }}>Total Enrolled</h3>
          <div style={{ fontSize: '2rem', fontWeight: '800', color: 'var(--text)' }}>342</div>
        </div>
        <div className="section-card" style={{ padding: '20px' }}>
          <h3 style={{ fontSize: '0.85rem', color: 'var(--muted)', textTransform: 'uppercase', marginBottom: '8px' }}>Avg. Score</h3>
          <div style={{ fontSize: '2rem', fontWeight: '800', color: 'var(--green-l)' }}>82%</div>
        </div>
        <div className="section-card" style={{ padding: '20px' }}>
          <h3 style={{ fontSize: '0.85rem', color: 'var(--muted)', textTransform: 'uppercase', marginBottom: '8px' }}>Exams Scheduled</h3>
          <div style={{ fontSize: '2rem', fontWeight: '800', color: 'var(--purple-l)' }}>5</div>
        </div>
        <div className="section-card" style={{ padding: '20px' }}>
          <h3 style={{ fontSize: '0.85rem', color: 'var(--muted)', textTransform: 'uppercase', marginBottom: '8px' }}>Join Code</h3>
          <div style={{ fontSize: '1.5rem', fontWeight: '800', color: 'var(--blue-l)', letterSpacing: '2px' }}>INST-8942</div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '20px' }}>
        {/* Main Content Area */}
        <div className="section-card" style={{ padding: '24px' }}>
          <h2 style={{ marginBottom: '16px' }}>Student Performance Trends</h2>
          <div style={{ height: '300px', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'var(--s2)', borderRadius: 'var(--r)' }}>
            <p style={{ color: 'var(--muted)' }}>[Analytics Chart Placeholder]</p>
          </div>
        </div>

        {/* Sidebar Actions */}
        <div className="section-card" style={{ padding: '24px' }}>
          <h2 style={{ marginBottom: '16px' }}>Quick Links</h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <Link to="/institution/analytics" className="btn-outline" style={{ textAlign: 'center' }}>Detailed Analytics</Link>
            <Link to="/institution/upload" className="btn-outline" style={{ textAlign: 'center' }}>Upload Materials</Link>
            <Link to="/institution/exams" className="btn-outline" style={{ textAlign: 'center' }}>Create Exam</Link>
          </div>
        </div>
      </div>
    </main>
  );
};

export default InstitutionDashboard;
