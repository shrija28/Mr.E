import React, { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import {
  Chart as ChartJS, CategoryScale, LinearScale, BarElement, PointElement, LineElement, Title, Tooltip, Legend, Filler
} from 'chart.js';
import { Bar } from 'react-chartjs-2';

ChartJS.register(CategoryScale, LinearScale, BarElement, PointElement, LineElement, Title, Tooltip, Legend, Filler);

function formatRelativeTime(isoString) {
  if (!isoString) return '—';
  try {
    const date = new Date(isoString);
    const now = new Date();
    const diffSec = Math.floor((now.getTime() - date.getTime()) / 1000);
    if (diffSec < 5) return 'Just now';
    if (diffSec < 60) return `${diffSec}s ago`;
    if (diffSec < 3600) return `${Math.floor(diffSec / 60)}m ago`;
    if (diffSec < 86400) return `${Math.floor(diffSec / 3600)}h ago`;
    if (diffSec < 604800) return `${Math.floor(diffSec / 86400)}d ago`;
    return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' });
  } catch {
    return isoString;
  }
}

function formatExactTime(isoString) {
  if (!isoString) return '—';
  try {
    const date = new Date(isoString);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  } catch {
    return isoString;
  }
}

const SUBJECT_COLORS = {
  Biology: { bg: 'rgba(16, 185, 129, 0.85)', border: '#10b981' },
  Chemistry: { bg: 'rgba(245, 158, 11, 0.85)', border: '#f59e0b' },
  Mathematics: { bg: 'rgba(99, 102, 241, 0.85)', border: '#6366f1' },
  Physics: { bg: 'rgba(6, 182, 212, 0.85)', border: '#06b6d4' },
};

const AdminDashboard = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);

  const fetchDashboardData = useCallback(async (isManualRefresh = false) => {
    if (isManualRefresh) {
      setRefreshing(true);
    }
    setError(null);
    try {
      const res = await fetch('/api/admin/dashboard', {
        method: 'GET',
        headers: { 'Accept': 'application/json' },
        credentials: 'include'
      });
      if (!res.ok) {
        throw new Error(`Failed to load dashboard data (Status ${res.status})`);
      }
      const json = await res.json();
      setData(json);
    } catch (err) {
      console.error('Error fetching dashboard metrics:', err);
      setError(err.message || 'Unable to connect to live dashboard service.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    fetchDashboardData();
  }, [fetchDashboardData]);

  // Dynamic Question Bank Bar Chart Data
  const questionSubjects = data?.question_bank?.admin_by_subject ? Object.keys(data.question_bank.admin_by_subject) : [];
  const questionCounts = questionSubjects.map(sub => data.question_bank.admin_by_subject[sub]);
  const questionColors = questionSubjects.map(sub => SUBJECT_COLORS[sub]?.bg || 'rgba(124, 58, 237, 0.85)');
  const questionBorders = questionSubjects.map(sub => SUBJECT_COLORS[sub]?.border || '#7c3aed');

  const qChartData = {
    labels: questionSubjects.length > 0 ? questionSubjects : ['No data'],
    datasets: [{
      label: 'Questions in Bank',
      data: questionCounts.length > 0 ? questionCounts : [0],
      backgroundColor: questionColors,
      borderColor: questionBorders,
      borderWidth: 1,
      borderRadius: 6
    }]
  };

  // Dynamic Exams by Subject Bar Chart Data
  const examSubjects = data?.exams?.by_subject ? Object.keys(data.exams.by_subject) : [];
  const examCounts = examSubjects.map(sub => data.exams.by_subject[sub]);
  const examColors = examSubjects.map(sub => SUBJECT_COLORS[sub]?.bg || 'rgba(217, 119, 6, 0.85)');

  const examsChartData = {
    labels: examSubjects.length > 0 ? examSubjects : ['No exams'],
    datasets: [{
      label: 'Exams Created',
      data: examCounts.length > 0 ? examCounts : [0],
      backgroundColor: examColors,
      borderRadius: 6
    }]
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: {
        backgroundColor: 'rgba(15, 23, 42, 0.95)',
        titleColor: '#f8fafc',
        bodyColor: '#cbd5e1',
        borderColor: 'rgba(255, 255, 255, 0.1)',
        borderWidth: 1,
        padding: 10,
        boxPadding: 4
      }
    },
    scales: {
      y: {
        beginAtZero: true,
        grid: { color: 'rgba(255,255,255,0.06)' },
        ticks: { color: '#94a3b8', precision: 0 }
      },
      x: {
        grid: { display: false },
        ticks: { color: '#94a3b8' }
      }
    }
  };

  const overview = data?.overview || {
    total_institutions: 0,
    active_institutions: 0,
    total_students: 0,
    direct_students: 0,
    institution_linked_students: 0,
    total_questions: 0,
    admin_questions: 0,
    institution_questions: 0,
    total_exams: 0,
    published_exams: 0,
    total_exam_attempts: 0,
    avg_score: 0,
    active_subscriptions: 0,
    expired_subscriptions: 0,
    overdue_subscriptions: 0
  };

  return (
    <>
      <style dangerouslySetInnerHTML={{ __html: `
    /* ── Clickable KPI cards ── */
    .kpi-grid { display:grid;grid-template-columns:repeat(auto-fit,minmax(175px,1fr));gap:14px;margin-bottom:24px; }

    .kpi-card {
      background:var(--card-bg);
      border:1px solid var(--border);
      border-radius:var(--r);
      padding:18px 20px;
      position:relative;
      overflow:hidden;
      cursor:pointer;
      text-decoration:none;
      display:block;
      transition:border-color 0.18s, transform 0.15s, box-shadow 0.18s;
    }
    .kpi-card:hover {
      border-color:rgba(255,255,255,0.18);
      transform:translateY(-2px);
      box-shadow:0 8px 24px rgba(0,0,0,0.25);
    }
    .kpi-card:hover .kpi-arrow { opacity:1; transform:translateX(0); }
    .kpi-card .kpi-val { font-size:2rem;font-weight:800;line-height:1;margin-bottom:4px;color:var(--text); }
    .kpi-card .kpi-lbl { font-size:0.78rem;color:var(--muted);text-transform:uppercase;letter-spacing:0.4px; }
    .kpi-card .kpi-sub { font-size:0.72rem;color:var(--muted2);margin-top:4px; }
    .kpi-card .kpi-accent { position:absolute;bottom:0;left:0;height:3px;width:100%;opacity:0.6; }
    .kpi-arrow {
      position:absolute;right:14px;bottom:14px;
      font-size:0.75rem;color:var(--muted);
      opacity:0;transform:translateX(-4px);
      transition:opacity 0.15s, transform 0.15s;
    }

    /* ── Quick actions ── */
    .quick-actions {
      display:flex;gap:10px;flex-wrap:wrap;margin-bottom:24px;
      padding:16px 20px;
      background:var(--card-bg);
      border:1px solid var(--border);
      border-radius:var(--r);
      align-items:center;
    }
    .quick-actions-label {
      font-size:0.72rem;text-transform:uppercase;letter-spacing:0.5px;
      color:var(--muted);font-weight:700;margin-right:4px;white-space:nowrap;
    }
    .qa-btn {
      display:inline-flex;align-items:center;gap:6px;
      padding:7px 14px;border-radius:var(--rs);
      font-size:0.82rem;font-weight:600;
      border:1px solid var(--border);
      color:var(--muted2);background:var(--s2);
      text-decoration:none;cursor:pointer;
      transition:border-color 0.15s, color 0.15s, background 0.15s, transform 0.12s;
    }
    .qa-btn:hover { border-color:rgba(255,255,255,0.2);color:var(--text);background:var(--s3);transform:translateY(-1px); }
    .qa-btn svg { width:13px;height:13px;flex-shrink:0; }

    /* ── Section headers with "View All" ── */
    .section-nav { display:flex;align-items:center;justify-content:space-between;width:100%; }
    .view-all-link {
      font-size:0.78rem;font-weight:600;color:var(--purple-l,#a78bfa);
      text-decoration:none;display:flex;align-items:center;gap:4px;
      transition:opacity 0.15s;white-space:nowrap;
    }
    .view-all-link:hover { opacity:0.75; }

    /* ── Alert items with resolve link ── */
    .alert-item {
      display:flex;align-items:center;gap:10px;
      padding:10px 14px;border-radius:var(--rs);margin-bottom:6px;font-size:0.85rem;
      cursor:pointer;transition:opacity 0.15s;
    }
    .alert-item:hover { opacity:0.85; }
    .alert-warn  { background:rgba(217,119,6,0.12);border:1px solid rgba(217,119,6,0.3);color:var(--yellow-l); }
    .alert-error { background:rgba(220,38,38,0.12);border:1px solid rgba(220,38,38,0.3);color:var(--red-l); }
    .alert-info  { background:rgba(37,99,235,0.1);border:1px solid rgba(37,99,235,0.25);color:#60a5fa; }
    .alert-resolve { margin-left:auto;font-size:0.72rem;font-weight:700;white-space:nowrap; }

    /* ── Clickable institution rows ── */
    .inst-row { cursor:pointer;transition:background 0.12s; }
    .inst-row:hover td { background:rgba(255,255,255,0.03); }

    /* ── Clickable institution question bars ── */
    .inst-q-row {
      display:flex;align-items:center;gap:10px;
      padding:8px 10px;cursor:pointer;border-radius:var(--rs);
      transition:background 0.12s;
    }
    .inst-q-row:hover { background:rgba(255,255,255,0.04); }

    /* ── Activity panel ── */
    .activity-item {
      display:flex;align-items:flex-start;gap:12px;
      padding:12px 14px;border-bottom:1px solid rgba(255,255,255,0.04);
      transition:background 0.12s;text-decoration:none;
    }
    .activity-item:hover { background:rgba(255,255,255,0.02); }
    .activity-item:last-child { border-bottom:none; }
    .activity-dot {
      width:8px;height:8px;border-radius:50%;margin-top:6px;flex-shrink:0;
    }
    .activity-text { font-size:0.84rem;color:var(--text);line-height:1.4; }
    .activity-time { font-size:0.72rem;color:var(--muted);margin-top:3px; }

    /* ── Charts container ── */
    .charts-2col { display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-bottom:24px; }
    @media(max-width:900px) { .charts-2col { grid-template-columns:1fr; } }

    /* ── Sub-summary tiles ── */
    .sub-tile {
      border-radius:var(--rs);padding:14px;text-align:center;
      cursor:pointer;transition:transform 0.15s,opacity 0.15s;
      text-decoration:none;display:block;
    }
    .sub-tile:hover { transform:translateY(-2px);opacity:0.85; }

    .spin { animation: spin 1s linear infinite; }
    @keyframes spin { 100% { transform: rotate(360deg); } }
  ` }} />
      <div className="bg-mesh"></div>
      
      <div className="main-wrap">

        {/* Header with real-time status & refresh */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
          <div>
            <h1 style={{ fontSize: '1.6rem', fontWeight: '800', margin: '0 0 3px' }}>Platform Dashboard</h1>
            <p style={{ color: 'var(--muted)', margin: '0', fontSize: '0.82rem' }}>
              {loading
                ? 'Loading live platform metrics…'
                : error
                ? <span style={{ color: 'var(--red-l, #f87171)' }}>Error: {error}</span>
                : `Live metrics updated at ${formatExactTime(data?.generated_at)} (${formatRelativeTime(data?.generated_at)})`
              }
            </p>
          </div>
          <button
            onClick={() => fetchDashboardData(true)}
            disabled={refreshing || loading}
            className="btn-outline"
            style={{ display: 'flex', alignItems: 'center', gap: '6px', cursor: refreshing ? 'wait' : 'pointer' }}
          >
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              className={refreshing ? 'spin' : ''}
              style={{ width: '14px', height: '14px' }}
            >
              <polyline points="23 4 23 10 17 10" />
              <path d="M20.49 15a9 9 0 11-2.12-9.36L23 10" />
            </svg>
            {refreshing ? 'Refreshing…' : 'Refresh'}
          </button>
        </div>

        {/* Quick Actions */}
        <div className="quick-actions">
          <span className="quick-actions-label">⚡ Quick Actions</span>
          <Link to="/admin/student-manage?action=create" className="qa-btn">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
            Add Student
          </Link>
          <Link to="/admin/institutions" className="qa-btn">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>
            Add Institution
          </Link>
          <Link to="/admin/upload" className="qa-btn">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
            Upload Question Paper
          </Link>
          <Link to="/admin/exams" className="qa-btn">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11"/></svg>
            Create Exam
          </Link>
          <Link to="/admin/subscriptions" className="qa-btn">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="1" y="4" width="22" height="16" rx="2"/><line x1="1" y1="10" x2="23" y2="10"/></svg>
            Manage Subscriptions
          </Link>
          <Link to="/admin/syllabus" className="qa-btn">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M4 19.5A2.5 2.5 0 016.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 014 19.5v-15A2.5 2.5 0 016.5 2z"/></svg>
            Add KCET Topic
          </Link>
          <Link to="/admin/analytics" className="qa-btn">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>
            View Analytics
          </Link>
        </div>

        {/* Alerts Section (Real Alerts) */}
        {data?.alerts && data.alerts.length > 0 && (
          <div style={{ marginBottom: '20px' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
              <span style={{ fontSize: '0.72rem', textTransform: 'uppercase', letterSpacing: '0.5px', color: 'var(--muted)', fontWeight: '700' }}>
                ⚠️ Active System Alerts ({data.alerts.length})
              </span>
              <Link to="/admin/subscriptions" className="view-all-link">Resolve All →</Link>
            </div>
            <div>
              {data.alerts.map((alert, idx) => (
                <div
                  key={idx}
                  className={`alert-item ${alert.severity === 'error' ? 'alert-error' : alert.severity === 'warning' ? 'alert-warn' : 'alert-info'}`}
                >
                  <span>{alert.message}</span>
                  <Link to="/admin/subscriptions" className="alert-resolve">Resolve →</Link>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Platform Overview Real KPI Cards */}
        <div style={{ fontSize: '0.72rem', textTransform: 'uppercase', letterSpacing: '0.5px', color: 'var(--muted)', marginBottom: '10px', fontWeight: '700' }}>
          Platform Overview
        </div>
        <div className="kpi-grid">
          {/* Institutions */}
          <Link to="/admin/institutions" className="kpi-card">
            <div className="kpi-accent" style={{ background: 'linear-gradient(90deg,#2563eb,#0891b2)' }}></div>
            <div className="kpi-val">{loading ? '—' : overview.total_institutions}</div>
            <div className="kpi-lbl">Institutions</div>
            <div className="kpi-sub">
              {loading ? 'Loading…' : overview.total_institutions > 0 ? `${overview.active_institutions} active` : '0 registered'}
            </div>
            <span className="kpi-arrow">→</span>
          </Link>

          {/* Students */}
          <Link to="/admin/students" className="kpi-card">
            <div className="kpi-accent" style={{ background: 'linear-gradient(90deg,#7c3aed,#4f46e5)' }}></div>
            <div className="kpi-val">{loading ? '—' : overview.total_students}</div>
            <div className="kpi-lbl">Total Students</div>
            <div className="kpi-sub">
              {loading ? 'Loading…' : `${overview.direct_students} direct, ${overview.institution_linked_students} institutional`}
            </div>
            <span className="kpi-arrow">→</span>
          </Link>

          {/* Questions */}
          <Link to="/admin/questions" className="kpi-card">
            <div className="kpi-accent" style={{ background: 'linear-gradient(90deg,#059669,#0d9488)' }}></div>
            <div className="kpi-val">{loading ? '—' : overview.total_questions.toLocaleString()}</div>
            <div className="kpi-lbl">Total Questions</div>
            <div className="kpi-sub">
              {loading ? 'Loading…' : `${overview.admin_questions} platform, ${overview.institution_questions} inst.`}
            </div>
            <span className="kpi-arrow">→</span>
          </Link>

          {/* Exams */}
          <Link to="/admin/exams" className="kpi-card">
            <div className="kpi-accent" style={{ background: 'linear-gradient(90deg,#d97706,#b45309)' }}></div>
            <div className="kpi-val">{loading ? '—' : overview.total_exams}</div>
            <div className="kpi-lbl">Exams Created</div>
            <div className="kpi-sub">
              {loading ? 'Loading…' : `${overview.published_exams} published`}
            </div>
            <span className="kpi-arrow">→</span>
          </Link>

          {/* Attempts */}
          <Link to="/admin/analytics" className="kpi-card">
            <div className="kpi-accent" style={{ background: 'linear-gradient(90deg,#0891b2,#0d9488)' }}></div>
            <div className="kpi-val">{loading ? '—' : overview.total_exam_attempts}</div>
            <div className="kpi-lbl">Exam Attempts</div>
            <div className="kpi-sub">
              {loading ? 'Loading…' : overview.total_exam_attempts > 0 ? `${overview.avg_score}% avg score` : 'No attempts yet'}
            </div>
            <span className="kpi-arrow">→</span>
          </Link>

          {/* Subscriptions */}
          <Link to="/admin/subscriptions" className="kpi-card">
            <div className="kpi-accent" style={{ background: 'linear-gradient(90deg,#059669,#16a34a)' }}></div>
            <div className="kpi-val">{loading ? '—' : overview.active_subscriptions}</div>
            <div className="kpi-lbl">Active Subscriptions</div>
            <div className="kpi-sub">
              {loading ? 'Loading…' : `${overview.overdue_subscriptions} overdue, ${overview.expired_subscriptions} expired`}
            </div>
            <span className="kpi-arrow">→</span>
          </Link>
        </div>

        {/* Charts: Question Bank & Exams by Subject */}
        <div className="charts-2col">
          {/* Admin Question Bank by Subject */}
          <div className="section-card">
            <div className="section-card-header">
              <div className="section-nav">
                <div>
                  <h3 style={{ margin: '0', fontSize: '1rem' }}>Admin Question Bank</h3>
                  <p className="section-sub" style={{ margin: '0' }}>Subject distribution in question bank</p>
                </div>
                <Link to="/admin/questions" className="view-all-link">Manage →</Link>
              </div>
            </div>
            <div className="section-body" style={{ height: '240px' }}>
              {loading ? (
                <div style={{ display: 'flex', height: '100%', alignItems: 'center', justifyContent: 'center', color: 'var(--muted)' }}>
                  Loading questions data…
                </div>
              ) : questionSubjects.length > 0 ? (
                <div style={{ height: '210px' }}>
                  <Bar data={qChartData} options={chartOptions} />
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', height: '100%', alignItems: 'center', justifyContent: 'center', color: 'var(--muted)', gap: '8px' }}>
                  <span>No questions in database yet</span>
                  <Link to="/admin/upload" className="qa-btn" style={{ fontSize: '0.75rem' }}>+ Upload Questions</Link>
                </div>
              )}
            </div>
          </div>

          {/* Exams by Subject */}
          <div className="section-card">
            <div className="section-card-header">
              <div className="section-nav">
                <div>
                  <h3 style={{ margin: '0', fontSize: '1rem' }}>Exams by Subject</h3>
                  <p className="section-sub" style={{ margin: '0' }}>Distribution of created mock exams</p>
                </div>
                <Link to="/admin/exams" className="view-all-link">View All →</Link>
              </div>
            </div>
            <div className="section-body" style={{ height: '240px' }}>
              {loading ? (
                <div style={{ display: 'flex', height: '100%', alignItems: 'center', justifyContent: 'center', color: 'var(--muted)' }}>
                  Loading exams data…
                </div>
              ) : examSubjects.length > 0 ? (
                <div style={{ height: '210px' }}>
                  <Bar data={examsChartData} options={chartOptions} />
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', height: '100%', alignItems: 'center', justifyContent: 'center', color: 'var(--muted)', gap: '8px' }}>
                  <span>No exams created yet</span>
                  <Link to="/admin/exams" className="qa-btn" style={{ fontSize: '0.75rem' }}>+ Create Mock Exam</Link>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Two Columns: Institution Question Banks & Recent Activity */}
        <div className="charts-2col">
          {/* Institution Question Banks */}
          <div className="section-card">
            <div className="section-card-header">
              <div className="section-nav">
                <div>
                  <h3 style={{ margin: '0', fontSize: '1rem' }}>Institution Question Banks</h3>
                  <p className="section-sub" style={{ margin: '0' }}>Content uploaded by partner institutions</p>
                </div>
                <Link to="/admin/institutions" className="view-all-link">Manage →</Link>
              </div>
            </div>
            <div className="section-body">
              {loading ? (
                <div style={{ color: 'var(--muted)', textAlign: 'center', padding: '30px' }}>Loading…</div>
              ) : data?.question_bank?.institution_by_institution?.length > 0 ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {data.question_bank.institution_by_institution.map((inst, i) => (
                    <div key={i} className="inst-q-row">
                      <div style={{ flex: '1', fontWeight: '600', fontSize: '0.85rem' }}>{inst.name}</div>
                      <div style={{ fontSize: '0.82rem', color: 'var(--muted)' }}>{inst.count} questions</div>
                    </div>
                  ))}
                </div>
              ) : (
                <div style={{ color: 'var(--muted)', textAlign: 'center', padding: '36px 16px', fontSize: '0.85rem' }}>
                  <p style={{ margin: '0 0 10px' }}>No institution question banks yet.</p>
                  <p style={{ margin: 0, fontSize: '0.78rem', color: 'var(--muted2)' }}>
                    Partner institutions will appear here once registered and uploading questions.
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Recent Real Activity */}
          <div className="section-card">
            <div className="section-card-header">
              <div className="section-nav">
                <div>
                  <h3 style={{ margin: '0', fontSize: '1rem' }}>Recent Activity</h3>
                  <p className="section-sub" style={{ margin: '0' }}>Real-time student & platform events</p>
                </div>
                <Link to="/admin/analytics" className="view-all-link">Full Log →</Link>
              </div>
            </div>
            <div className="section-body" style={{ padding: '0' }}>
              {loading ? (
                <div style={{ color: 'var(--muted)', textAlign: 'center', padding: '30px' }}>Loading…</div>
              ) : data?.recent_activity?.length > 0 ? (
                <div style={{ display: 'flex', flexDirection: 'column' }}>
                  {data.recent_activity.map((act) => (
                    <div key={act.id} className="activity-item">
                      <div
                        className="activity-dot"
                        style={{
                          background: act.badge_color === 'green' ? '#10b981' : act.badge_color === 'purple' ? '#a855f7' : '#06b6d4'
                        }}
                      ></div>
                      <div style={{ flex: '1' }}>
                        <div className="activity-text">{act.title}</div>
                        <div className="activity-time">{act.subtitle} • {formatRelativeTime(act.timestamp)}</div>
                      </div>
                      <span
                        style={{
                          fontSize: '0.68rem',
                          fontWeight: '700',
                          textTransform: 'uppercase',
                          padding: '2px 6px',
                          borderRadius: '4px',
                          background: act.badge_color === 'green' ? 'rgba(16,185,129,0.15)' : act.badge_color === 'purple' ? 'rgba(168,85,247,0.15)' : 'rgba(6,182,212,0.15)',
                          color: act.badge_color === 'green' ? '#34d399' : act.badge_color === 'purple' ? '#c084fc' : '#38bdf8'
                        }}
                      >
                        {act.badge}
                      </span>
                    </div>
                  ))}
                </div>
              ) : (
                <div style={{ color: 'var(--muted)', textAlign: 'center', padding: '36px 16px', fontSize: '0.85rem' }}>
                  No recent events recorded.
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Two Columns: Recent Institutions & Subscription Overview */}
        <div className="charts-2col" style={{ marginTop: '0' }}>
          {/* Recent Institutions */}
          <div className="section-card">
            <div className="section-card-header">
              <div className="section-nav">
                <div>
                  <h3 style={{ margin: '0', fontSize: '1rem' }}>Recent Institutions</h3>
                  <p className="section-sub" style={{ margin: '0' }}>Latest registered partners</p>
                </div>
                <Link to="/admin/institutions" className="view-all-link">View All →</Link>
              </div>
            </div>
            <div className="section-body" style={{ padding: '0' }}>
              <table className="results-table" style={{ width: '100%' }}>
                <thead>
                  <tr>
                    <th>Institution</th>
                    <th>Status</th>
                    <th>Joined</th>
                  </tr>
                </thead>
                <tbody>
                  {loading ? (
                    <tr><td colSpan="3" style={{ textAlign: 'center', color: 'var(--muted)', padding: '24px' }}>Loading…</td></tr>
                  ) : data?.recent_institutions?.length > 0 ? (
                    data.recent_institutions.map((inst) => (
                      <tr key={inst.id} className="inst-row">
                        <td style={{ fontWeight: '600' }}>{inst.name}</td>
                        <td>
                          <span className={`badge ${inst.status === 'active' ? 'badge-green' : inst.status === 'trial' ? 'badge-blue' : 'badge-yellow'}`}>
                            {inst.status}
                          </span>
                        </td>
                        <td style={{ color: 'var(--muted)', fontSize: '0.82rem' }}>
                          {formatRelativeTime(inst.registered_at)}
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan="3" style={{ textAlign: 'center', color: 'var(--muted)', padding: '28px 16px' }}>
                        <div>No institutions registered yet</div>
                        <Link
                          to="/admin/institutions"
                          className="qa-btn"
                          style={{ display: 'inline-flex', marginTop: '10px', fontSize: '0.75rem' }}
                        >
                          + Register Institution
                        </Link>
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>

          {/* Subscription Overview */}
          <div className="section-card">
            <div className="section-card-header">
              <div className="section-nav">
                <div>
                  <h3 style={{ margin: '0', fontSize: '1rem' }}>Subscription Overview</h3>
                  <p className="section-sub" style={{ margin: '0' }}>Status across platform accounts</p>
                </div>
                <Link to="/admin/subscriptions" className="view-all-link">Manage →</Link>
              </div>
            </div>
            <div className="section-body">
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                <Link to="/admin/subscriptions" className="sub-tile" style={{ background: 'rgba(5,150,105,0.12)', border: '1px solid rgba(5,150,105,0.3)' }}>
                  <div style={{ fontSize: '1.6rem', fontWeight: '800', color: 'var(--green-l, #34d399)' }}>
                    {loading ? '—' : overview.active_subscriptions}
                  </div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--muted)' }}>Active</div>
                </Link>
                <Link to="/admin/subscriptions" className="sub-tile" style={{ background: 'rgba(220,38,38,0.1)', border: '1px solid rgba(220,38,38,0.25)' }}>
                  <div style={{ fontSize: '1.6rem', fontWeight: '800', color: 'var(--red-l, #f87171)' }}>
                    {loading ? '—' : overview.expired_subscriptions}
                  </div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--muted)' }}>Expired</div>
                </Link>
                <Link to="/admin/subscriptions" className="sub-tile" style={{ background: 'rgba(217,119,6,0.12)', border: '1px solid rgba(217,119,6,0.3)' }}>
                  <div style={{ fontSize: '1.6rem', fontWeight: '800', color: 'var(--yellow-l, #fbbf24)' }}>
                    {loading ? '—' : overview.overdue_subscriptions}
                  </div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--muted)' }}>Overdue</div>
                </Link>
                <Link to="/admin/subscriptions" className="sub-tile" style={{ background: 'rgba(37,99,235,0.1)', border: '1px solid rgba(37,99,235,0.25)' }}>
                  <div style={{ fontSize: '1.6rem', fontWeight: '800', color: '#60a5fa' }}>
                    {loading ? '—' : Math.max(0, overview.total_students - overview.active_subscriptions)}
                  </div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--muted)' }}>No Subscription</div>
                </Link>
              </div>
            </div>
          </div>
        </div>

        {/* Direct Subscriber Students */}
        <div className="section-card" style={{ marginTop: '20px' }}>
          <div className="section-card-header">
            <div className="section-nav">
              <div>
                <h3 style={{ margin: '0', fontSize: '1rem' }}>Direct Subscriber Students</h3>
                <p className="section-sub" style={{ margin: '0' }}>Personal/independent enrolled students</p>
              </div>
              <Link to="/admin/student-manage?action=create" className="view-all-link">+ Add Student</Link>
            </div>
          </div>
          <div className="section-body" style={{ padding: '0' }}>
            <table className="results-table" style={{ width: '100%' }}>
              <thead>
                <tr>
                  <th>Name</th>
                  <th>KCET ID</th>
                  <th>Email</th>
                  <th>Subscription Status</th>
                  <th>Joined</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr><td colSpan="5" style={{ textAlign: 'center', color: 'var(--muted)', padding: '24px' }}>Loading…</td></tr>
                ) : data?.direct_students?.length > 0 ? (
                  data.direct_students.map((stu) => (
                    <tr key={stu.id}>
                      <td style={{ fontWeight: '600' }}>{stu.name}</td>
                      <td>
                        <code style={{ background: 'rgba(255,255,255,0.06)', padding: '2px 6px', borderRadius: '4px' }}>
                          {stu.kcet_student_id}
                        </code>
                      </td>
                      <td style={{ color: 'var(--muted)' }}>{stu.email}</td>
                      <td>
                        <span className={`badge ${stu.subscription_status === 'active' || stu.subscription_status === 'trial' ? 'badge-green' : 'badge-yellow'}`}>
                          {stu.subscription_status}
                        </span>
                      </td>
                      <td style={{ color: 'var(--muted)', fontSize: '0.82rem' }}>
                        {formatRelativeTime(stu.created_at)}
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan="5" style={{ textAlign: 'center', color: 'var(--muted)', padding: '28px 16px' }}>
                      <div>No direct students registered yet</div>
                      <Link
                        to="/admin/student-manage?action=create"
                        className="qa-btn"
                        style={{ display: 'inline-flex', marginTop: '10px', fontSize: '0.75rem' }}
                      >
                        + Add Student
                      </Link>
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
            <div className="table-footer" style={{ textAlign: 'center', padding: '10px', fontSize: '0.8rem', color: 'var(--muted)' }}>
              {data?.direct_students?.length
                ? `Showing ${data.direct_students.length} registered direct student(s)`
                : 'Zero direct students'}
            </div>
          </div>
        </div>

      </div>
    </>
  );
};

export default AdminDashboard;
