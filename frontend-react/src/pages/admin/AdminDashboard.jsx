import React from 'react';
import { Link } from 'react-router-dom';

const AdminDashboard = () => {
  return (
    <main style={{ padding: '24px' }}>
      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <div>
          <h1 style={{ fontSize: '1.8rem', fontWeight: '800' }}>Admin Dashboard</h1>
          <p style={{ color: 'var(--muted)' }}>Platform overview and quick actions.</p>
        </div>
        <Link to="/admin/upload" className="btn-primary">Upload Materials</Link>
      </header>

      {/* KPI Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '20px', marginBottom: '24px' }}>
        <div className="section-card" style={{ padding: '20px' }}>
          <h3 style={{ fontSize: '0.85rem', color: 'var(--muted)', textTransform: 'uppercase', marginBottom: '8px' }}>Total Students</h3>
          <div style={{ fontSize: '2rem', fontWeight: '800', color: 'var(--text)' }}>15,243</div>
          <div style={{ fontSize: '0.8rem', color: 'var(--green-l)', marginTop: '4px' }}>+124 this week</div>
        </div>
        <div className="section-card" style={{ padding: '20px' }}>
          <h3 style={{ fontSize: '0.85rem', color: 'var(--muted)', textTransform: 'uppercase', marginBottom: '8px' }}>Institutions</h3>
          <div style={{ fontSize: '2rem', fontWeight: '800', color: 'var(--purple-l)' }}>48</div>
          <div style={{ fontSize: '0.8rem', color: 'var(--green-l)', marginTop: '4px' }}>+2 this week</div>
        </div>
        <div className="section-card" style={{ padding: '20px' }}>
          <h3 style={{ fontSize: '0.85rem', color: 'var(--muted)', textTransform: 'uppercase', marginBottom: '8px' }}>Active Subscriptions</h3>
          <div style={{ fontSize: '2rem', fontWeight: '800', color: 'var(--blue-l)' }}>3,892</div>
          <div style={{ fontSize: '0.8rem', color: 'var(--green-l)', marginTop: '4px' }}>+45 this week</div>
        </div>
        <div className="section-card" style={{ padding: '20px' }}>
          <h3 style={{ fontSize: '0.85rem', color: 'var(--muted)', textTransform: 'uppercase', marginBottom: '8px' }}>Questions Gen.</h3>
          <div style={{ fontSize: '2rem', fontWeight: '800', color: 'var(--yellow-l)' }}>1.2M</div>
          <div style={{ fontSize: '0.8rem', color: 'var(--green-l)', marginTop: '4px' }}>+12k today</div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '20px' }}>
        {/* Main Content Area */}
        <div className="section-card" style={{ padding: '24px' }}>
          <h2 style={{ marginBottom: '16px' }}>Platform Activity (30 Days)</h2>
          <div style={{ height: '300px', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'var(--s2)', borderRadius: 'var(--r)' }}>
            <p style={{ color: 'var(--muted)' }}>[Activity Chart Placeholder]</p>
          </div>
        </div>

        {/* Sidebar Actions */}
        <div className="section-card" style={{ padding: '24px' }}>
          <h2 style={{ marginBottom: '16px' }}>Quick Links</h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <Link to="/admin/institutions" className="btn-outline" style={{ textAlign: 'center' }}>Manage Institutions</Link>
            <Link to="/admin/questions" className="btn-outline" style={{ textAlign: 'center' }}>Review Questions</Link>
            <Link to="/admin/exams" className="btn-outline" style={{ textAlign: 'center' }}>Monitor Exams</Link>
          </div>
        </div>
      </div>
    </main>
  );
};

export default AdminDashboard;
