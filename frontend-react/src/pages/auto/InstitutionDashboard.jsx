import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';

const InstitutionDashboard = () => {
  const [dashboardData, setDashboardData] = useState(null);
  const [batches, setBatches] = useState([]);
  const [exams, setExams] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchDashboard = async () => {
    setLoading(true);
    setError('');
    try {
      // 1. Dashboard summary
      const dashRes = await fetch('/api/institution/dashboard', { credentials: 'include' });
      if (dashRes.ok) {
        const dData = await dashRes.json();
        setDashboardData(dData);
      }

      // 2. Batches
      const batchRes = await fetch('/api/institution/batches', { credentials: 'include' });
      if (batchRes.ok) {
        const bData = await batchRes.json();
        setBatches(bData.batches || []);
      }

      // 3. Exams
      const examRes = await fetch('/api/institution/content/exams', { credentials: 'include' });
      if (examRes.ok) {
        const eData = await examRes.json();
        setExams(eData.exams || []);
      }
    } catch (err) {
      setError('Unable to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboard();
  }, []);

  const totalStudents = dashboardData?.total_students ?? 0;
  const institutionName = dashboardData?.institution_name || 'Your Institution';
  const subStatus = dashboardData?.subscription_status || 'active';

  return (
    <>
      <div className="bg-mesh"></div>

      <main className="institution-page" id="institutionDashboardPage">
        {/* Header */}
        <div className="institution-page-header" style={{ marginBottom: '24px' }}>
          <div>
            <h1 className="institution-page-title">
              {institutionName} <span className="institution-page-title-accent">Dashboard</span>
            </h1>
            <p className="institution-page-sub">
              Command center for managing your classes, weekly mock tests, and student rankings
            </p>
          </div>
          <div className="institution-page-header-actions">
            <button
              className="btn-institution-outline"
              type="button"
              onClick={fetchDashboard}
              style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ width: '14px', height: '14px' }}><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 11-2.12-9.36L23 10"/></svg>
              Refresh Data
            </button>
          </div>
        </div>

        {error && (
          <div style={{ background: 'rgba(220,38,38,0.1)', border: '1px solid var(--red)', borderRadius: '8px', padding: '12px 16px', marginBottom: '20px', color: 'var(--red-l)' }}>
            {error}
          </div>
        )}

        {/* 1. Real KPI Summary Tiles */}
        <section className="kpi-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px', marginBottom: '24px' }}>
          <Link to="/institution/students" style={{ textDecoration: 'none' }}>
            <div className="kpi-tile" style={{ background: 'var(--card)', border: '1px solid var(--border)', borderRadius: '12px', padding: '20px', transition: 'transform 0.2s', cursor: 'pointer' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                <span style={{ fontSize: '0.85rem', color: 'var(--muted)', fontWeight: 600 }}>TOTAL STUDENTS</span>
                <span style={{ fontSize: '1.4rem' }}>👥</span>
              </div>
              <div style={{ fontSize: '2.2rem', fontWeight: 700, color: 'var(--text)' }}>
                {loading ? '—' : totalStudents}
              </div>
              <span style={{ fontSize: '0.8rem', color: 'var(--blue)' }}>Manage & Invite Students →</span>
            </div>
          </Link>

          <Link to="/institution/students" style={{ textDecoration: 'none' }}>
            <div className="kpi-tile" style={{ background: 'var(--card)', border: '1px solid var(--border)', borderRadius: '12px', padding: '20px', transition: 'transform 0.2s', cursor: 'pointer' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                <span style={{ fontSize: '0.85rem', color: 'var(--muted)', fontWeight: 600 }}>ACTIVE BATCHES</span>
                <span style={{ fontSize: '1.4rem' }}>🏫</span>
              </div>
              <div style={{ fontSize: '2.2rem', fontWeight: 700, color: 'var(--purple-l, #a78bfa)' }}>
                {loading ? '—' : batches.length}
              </div>
              <span style={{ fontSize: '0.8rem', color: 'var(--purple-l, #a78bfa)' }}>View & Create Sections →</span>
            </div>
          </Link>

          <Link to="/institution/exams" style={{ textDecoration: 'none' }}>
            <div className="kpi-tile" style={{ background: 'var(--card)', border: '1px solid var(--border)', borderRadius: '12px', padding: '20px', transition: 'transform 0.2s', cursor: 'pointer' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                <span style={{ fontSize: '0.85rem', color: 'var(--muted)', fontWeight: 600 }}>WEEKLY EXAMS</span>
                <span style={{ fontSize: '1.4rem' }}>📝</span>
              </div>
              <div style={{ fontSize: '2.2rem', fontWeight: 700, color: 'var(--text)' }}>
                {loading ? '—' : exams.length}
              </div>
              <span style={{ fontSize: '0.8rem', color: 'var(--blue)' }}>Build & Schedule Tests →</span>
            </div>
          </Link>

          <Link to="/institution/subscription" style={{ textDecoration: 'none' }}>
            <div className="kpi-tile" style={{ background: 'var(--card)', border: '1px solid var(--border)', borderRadius: '12px', padding: '20px', transition: 'transform 0.2s', cursor: 'pointer' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                <span style={{ fontSize: '0.85rem', color: 'var(--muted)', fontWeight: 600 }}>SUBSCRIPTION</span>
                <span style={{ fontSize: '1.4rem' }}>✓</span>
              </div>
              <div style={{ fontSize: '2.2rem', fontWeight: 700, color: '#10b981', textTransform: 'capitalize' }}>
                {subStatus}
              </div>
              <span style={{ fontSize: '0.8rem', color: 'var(--muted)' }}>Manage Plan & Quota →</span>
            </div>
          </Link>
        </section>

        {/* 2. Getting Started & Quick Action Workflow */}
        <section className="section-card" style={{ marginBottom: '24px', background: 'linear-gradient(135deg, rgba(124, 58, 237, 0.08), rgba(37, 99, 235, 0.08))', border: '1px solid rgba(124, 58, 237, 0.3)' }}>
          <div className="section-card-header">
            <div>
              <h2 style={{ fontSize: '1.25rem', color: 'var(--text)' }}>🚀 Teacher-Led Next Steps: What You Can Do</h2>
              <p className="section-sub">Follow these 3 simple steps to start testing and grading your students</p>
            </div>
          </div>

          <div className="section-body" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '16px' }}>
            <div style={{ background: 'rgba(0,0,0,0.2)', border: '1px solid var(--border)', borderRadius: '10px', padding: '20px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
              <div>
                <div style={{ fontSize: '1.8rem', marginBottom: '8px' }}>👥</div>
                <h3 style={{ fontSize: '1.05rem', margin: '0 0 6px', color: 'var(--text)' }}>1. Create Batches & Invite Students</h3>
                <p style={{ fontSize: '0.85rem', color: 'var(--muted)', margin: 0 }}>
                  Create class sections (e.g. <em>PUC-II Section A</em>) and generate a single invitation link to share with your students.
                </p>
              </div>
              <Link to="/institution/students" className="btn-primary" style={{ marginTop: '16px', textAlign: 'center', justifyContent: 'center' }}>
                Manage Students & Batches →
              </Link>
            </div>

            <div style={{ background: 'rgba(0,0,0,0.2)', border: '1px solid var(--border)', borderRadius: '10px', padding: '20px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
              <div>
                <div style={{ fontSize: '1.8rem', marginBottom: '8px' }}>📝</div>
                <h3 style={{ fontSize: '1.05rem', margin: '0 0 6px', color: 'var(--text)' }}>2. Build & Assign Weekly Tests</h3>
                <p style={{ fontSize: '0.85rem', color: 'var(--muted)', margin: 0 }}>
                  Pick a subject (Mathematics, Biology, Physics, Chemistry), choose questions count, set a 60-min timer, and assign to your batch.
                </p>
              </div>
              <Link to="/institution/exams" className="btn-primary" style={{ marginTop: '16px', textAlign: 'center' }}>
                Open Test Builder →
              </Link>
            </div>

            <div style={{ background: 'rgba(0,0,0,0.2)', border: '1px solid var(--border)', borderRadius: '10px', padding: '20px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
              <div>
                <div style={{ fontSize: '1.8rem', marginBottom: '8px' }}>📊</div>
                <h3 style={{ fontSize: '1.05rem', margin: '0 0 6px', color: 'var(--text)' }}>3. View Batch Rank Lists</h3>
                <p style={{ fontSize: '0.85rem', color: 'var(--muted)', margin: 0 }}>
                  Instantly track student submissions, view leaderboard rankings (#1 🥇, #2 🥈), and analyze class average scores.
                </p>
              </div>
              <Link to="/institution/analytics" className="btn-primary" style={{ marginTop: '16px', textAlign: 'center', justifyContent: 'center' }}>
                View Batch Analytics →
              </Link>
            </div>
          </div>
        </section>

        {/* 3. Scheduled Tests Overview */}
        <section className="section-card">
          <div className="section-card-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <div className="section-icon" style={{ background: 'rgba(59, 130, 246, 0.2)' }}>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 8v4l3 3"/><circle cx="12" cy="12" r="10"/></svg>
              </div>
              <div>
                <h2>Your Institution's Active Exams</h2>
                <p className="section-sub">Tests currently available to your students</p>
              </div>
            </div>
            <Link to="/institution/exams" className="btn-institution-outline" style={{ padding: '6px 12px', fontSize: '0.85rem' }}>
              + Create New Test
            </Link>
          </div>

          <div className="section-body" style={{ padding: 0 }}>
            {exams.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '40px 20px', color: 'var(--muted)' }}>
                <div style={{ fontSize: '2rem', marginBottom: '8px' }}>📝</div>
                <p>No exams created yet. Click the button below to schedule your first weekly mock test.</p>
                <Link to="/institution/exams" className="btn-primary" style={{ display: 'inline-block', marginTop: '12px' }}>
                  Create First Weekly Test
                </Link>
              </div>
            ) : (
              <div className="responsive-table-wrapper">
                <table>
                  <thead>
                    <tr>
                      <th>Exam Name</th>
                      <th>Subject</th>
                      <th>Assigned Batch</th>
                      <th>Duration</th>
                      <th>Status</th>
                      <th style={{ textAlign: 'right' }}>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {exams.slice(0, 5).map((exam) => (
                      <tr key={exam.exam_id}>
                        <td>
                          <div style={{ fontWeight: 600, color: 'var(--text)' }}>{exam.exam_name}</div>
                          <span style={{ fontSize: '0.75rem', color: 'var(--muted)' }}>
                            {exam.created_at ? new Date(exam.created_at).toLocaleDateString() : '—'}
                          </span>
                        </td>
                        <td>
                          <span style={{ fontSize: '0.8rem', padding: '2px 8px', borderRadius: '4px', background: 'rgba(59, 130, 246, 0.15)', color: 'var(--blue)' }}>
                            {exam.subject}
                          </span>
                        </td>
                        <td>
                          <span style={{ fontSize: '0.8rem', padding: '2px 8px', borderRadius: '4px', background: exam.batch_id ? 'rgba(167, 139, 250, 0.15)' : 'rgba(255, 255, 255, 0.06)', color: exam.batch_id ? 'var(--purple-l)' : 'var(--muted)' }}>
                            👥 {exam.batch_name || 'All Batches'}
                          </span>
                        </td>
                        <td style={{ fontSize: '0.85rem' }}>{exam.duration_minutes || 60} mins</td>
                        <td>
                          <span style={{
                            fontSize: '0.78rem',
                            padding: '2px 8px',
                            borderRadius: '12px',
                            background: exam.is_published ? 'rgba(16, 185, 129, 0.15)' : 'rgba(234, 179, 8, 0.15)',
                            color: exam.is_published ? '#10b981' : '#eab308',
                            fontWeight: 600,
                          }}>
                            {exam.is_published ? 'Published' : 'Draft'}
                          </span>
                        </td>
                        <td style={{ textAlign: 'right' }}>
                          <Link to="/institution/exams" className="btn-institution-outline" style={{ padding: '4px 8px', fontSize: '0.78rem' }}>
                            View in Builder →
                          </Link>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </section>
      </main>
    </>
  );
};

export default InstitutionDashboard;
