import React, { useState, useEffect } from 'react';
import {
  Chart as ChartJS, CategoryScale, LinearScale, BarElement, PointElement, LineElement, ArcElement, Title, Tooltip, Legend, Filler
} from 'chart.js';
import { Bar, Line, Doughnut } from 'react-chartjs-2';

ChartJS.register(CategoryScale, LinearScale, BarElement, PointElement, LineElement, ArcElement, Title, Tooltip, Legend, Filler);

const Dashboard = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [availableSubjects, setAvailableSubjects] = useState([]);
  const [studentProfile, setStudentProfile] = useState({ name: 'Student', id: '—' });
  const [lastUpdated, setLastUpdated] = useState('—');

  // Filters & Search
  const [selectedSubject, setSelectedSubject] = useState('all');
  const [selectedStatus, setSelectedStatus] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');

  // KCET College Predictor based on Rank
  const [predictorRank, setPredictorRank] = useState('');
  const [predictorCategory, setPredictorCategory] = useState('GM');
  const [predictorLocation, setPredictorLocation] = useState('all');
  const [predictorLoading, setPredictorLoading] = useState(false);
  const [predictionResults, setPredictionResults] = useState(null);
  const [predictorError, setPredictorError] = useState('');
  const [activePredictionTab, setActivePredictionTab] = useState('all');

  // AI Rank Booster & Action Plan Checklist
  const [simulatedBoostPct, setSimulatedBoostPct] = useState(10);
  const [checkedActionSteps, setCheckedActionSteps] = useState(() => {
    try {
      const saved = localStorage.getItem('smartkcet_action_steps');
      return saved ? JSON.parse(saved) : {};
    } catch (e) {
      return {};
    }
  });

  const toggleActionStep = (stepId) => {
    setCheckedActionSteps((prev) => {
      const next = { ...prev, [stepId]: !prev[stepId] };
      try {
        localStorage.setItem('smartkcet_action_steps', JSON.stringify(next));
      } catch (e) {}
      return next;
    });
  };

  const resetActionSteps = () => {
    setCheckedActionSteps({});
    try {
      localStorage.removeItem('smartkcet_action_steps');
    } catch (e) {}
  };

  const fetchDashboardData = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/student/dashboard-stats', { credentials: 'include' });
      if (res.ok) {
        const d = await res.json();
        setData(d);
        const now = new Date();
        setLastUpdated(now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }));
      }
    } catch (err) {
      console.error('Failed to fetch real dashboard metrics:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // 1. Fetch authenticated student profile
    fetch('/api/auth/me', { credentials: 'include' })
      .then(res => res.json())
      .then(d => {
        if (d.authenticated) {
          setStudentProfile({
            name: d.display_name || d.sub || 'Student',
            id: d.kcet_student_id || d.sub || '—'
          });
        }
      })
      .catch(() => {});

    // 2. Fetch available exams created by admin
    fetch('/api/student/exams', { credentials: 'include' })
      .then(res => res.json())
      .then(d => {
        if (d.subjects) setAvailableSubjects(d.subjects);
      })
      .catch(() => {});

    // 3. Fetch real performance data
    fetchDashboardData();
  }, []);

  const handlePredictColleges = async (rankOverride = null) => {
    const targetRank = rankOverride !== null ? rankOverride : predictorRank;
    if (!targetRank || parseInt(targetRank, 10) <= 0) {
      setPredictorError('Please enter a valid KCET rank number greater than 0.');
      return;
    }
    setPredictorLoading(true);
    setPredictorError('');
    try {
      const res = await fetch(
        `/api/student/predict-colleges?rank=${encodeURIComponent(targetRank)}&category=${encodeURIComponent(predictorCategory)}&location=${encodeURIComponent(predictorLocation)}`,
        { credentials: 'include' }
      );
      if (res.ok) {
        const json = await res.json();
        setPredictionResults(json);
        if (json.matches?.safe?.length > 0) {
          setActivePredictionTab('safe');
        } else if (json.matches?.target?.length > 0) {
          setActivePredictionTab('target');
        } else {
          setActivePredictionTab('reach');
        }
      } else {
        const errJson = await res.json().catch(() => ({}));
        setPredictorError(errJson.message || 'Unable to predict colleges for this rank.');
      }
    } catch (err) {
      setPredictorError('Network error while predicting colleges.');
    } finally {
      setPredictorLoading(false);
    }
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'bottom',
        labels: { color: '#e8e8f4' }
      }
    },
    scales: {
      y: {
        beginAtZero: true,
        max: 100,
        grid: { color: 'rgba(255,255,255,0.05)' },
        ticks: { color: '#6868a0' }
      },
      x: {
        grid: { display: false },
        ticks: { color: '#6868a0' }
      }
    }
  };

  const doughnutOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'bottom',
        labels: { color: '#e8e8f4' }
      }
    },
    cutout: '70%'
  };

  let topicChartData = null;
  let setChartData = null;
  let passFailChartData = null;

  if (data) {
    topicChartData = {
      labels: data.topicData.labels,
      datasets: [{
        label: 'Average Score (%)',
        data: data.topicData.scores,
        backgroundColor: 'rgba(124, 58, 237, 0.65)',
        borderColor: 'rgba(124, 58, 237, 1)',
        borderWidth: 1,
        borderRadius: 6
      }]
    };

    setChartData = {
      labels: data.setData.labels.length > 0 ? data.setData.labels : ['No Attempts'],
      datasets: [{
        label: 'Score Trend (%)',
        data: data.setData.scores.length > 0 ? data.setData.scores : [0],
        borderColor: 'rgba(16, 185, 129, 1)',
        backgroundColor: 'rgba(16, 185, 129, 0.15)',
        fill: true,
        tension: 0.35,
        pointRadius: 4,
        pointBackgroundColor: 'rgba(16, 185, 129, 1)'
      }]
    };

    const hasPassFailData = data.passFailData.counts[0] > 0 || data.passFailData.counts[1] > 0;
    passFailChartData = {
      labels: hasPassFailData ? data.passFailData.labels : ['No Attempts'],
      datasets: [{
        data: hasPassFailData ? data.passFailData.counts : [1],
        backgroundColor: hasPassFailData
          ? ['rgba(16, 185, 129, 0.85)', 'rgba(239, 68, 68, 0.85)']
          : ['rgba(255, 255, 255, 0.1)'],
        borderWidth: 0
      }]
    };
  }

  // Score & Rank Impact Booster calculations
  const calcRankForScore = (score) => {
    const s = Math.max(0, Math.min(100, Number(score) || 0));
    if (s >= 90) return Math.round(100 + (100 - s) * 240);
    if (s >= 75) return Math.round(2500 + (90 - s) * 366.6);
    if (s >= 60) return Math.round(8000 + (75 - s) * 800);
    if (s >= 45) return Math.round(20000 + (60 - s) * 1666.6);
    return Math.round(45000 + (45 - s) * 1222.2);
  };

  const currentAvgScore = data?.kpis?.avgScore || 0;
  const currentRank = data?.aiAnalysis?.rank_booster?.current_rank || (currentAvgScore > 0 ? calcRankForScore(currentAvgScore) : 48000);
  const simulatedTargetScore = Math.min(98, +(currentAvgScore + simulatedBoostPct).toFixed(1));
  const simulatedBoostedRank = calcRankForScore(simulatedTargetScore);
  const simulatedRankLeap = Math.max(50, currentRank - simulatedBoostedRank);
  const simulatedMarksGain = +(simulatedBoostPct * 0.6).toFixed(1);

  const actionSteps = data?.aiAnalysis?.action_plan || [
    {
      id: 'step-1',
      title: 'Revise Core Formulas & NCERT Theory',
      desc: 'Review key formulas and summary definitions in your weakest topics.',
      category: 'Formulas & Theory',
      badge: 'Step 1'
    },
    {
      id: 'step-2',
      title: 'Solve 15-20 Timed PYQs',
      desc: 'Practice previous year questions with a 75-second timer per numerical.',
      category: 'Targeted Practice',
      badge: 'Step 2'
    },
    {
      id: 'step-3',
      title: 'Validate Mastery with a Mock Exam',
      desc: 'Retake a mock test aiming for >= 75% accuracy to secure your rank leap.',
      category: 'Mock Validation',
      badge: 'Step 3'
    }
  ];

  const completedStepsCount = actionSteps.filter((s) => !!checkedActionSteps[s.id]).length;
  const progressPct = Math.round((completedStepsCount / (actionSteps.length || 1)) * 100);

  // Filter exam history
  const filteredHistory = (data?.examHistory || []).filter(h => {
    if (selectedSubject !== 'all' && h.subject.toLowerCase() !== selectedSubject.toLowerCase()) return false;
    if (selectedStatus !== 'all' && h.status.toLowerCase() !== selectedStatus.toLowerCase()) return false;
    if (searchTerm.trim() !== '') {
      const term = searchTerm.toLowerCase();
      const matchSubj = h.subject.toLowerCase().includes(term);
      const matchName = (h.exam_name || '').toLowerCase().includes(term);
      if (!matchSubj && !matchName) return false;
    }
    return true;
  });

  return (
    <>
      <main className="dash-main">
        {/* Hero Header */}
        <div className="dash-hero">
          <div>
            <h1 className="dash-title">My <span className="hero-gradient">Dashboard</span></h1>
            <p className="dash-sub" id="dashSubtitle">Your live performance analytics calculated from your actual exam attempts</p>
          </div>
          <div className="dash-hero-right">
            <div className="last-updated" id="lastUpdated">Last updated: {lastUpdated}</div>
            <button className="btn-outline" onClick={fetchDashboardData} disabled={loading}>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ width: '16px', height: '16px' }}>
                <polyline points="23 4 23 10 17 10" />
                <path d="M20.49 15a9 9 0 11-2.12-9.36L23 10" />
              </svg>
              {loading ? 'Refreshing...' : 'Refresh'}
            </button>
          </div>
        </div>

        {/* Student Profile Card */}
        <div className="section-card" style={{ marginBottom: '20px', padding: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px' }}>
            <div>
              <div style={{ color: 'var(--muted)', fontSize: '0.8rem', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '4px' }}>
                Student Profile
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '24px', flexWrap: 'wrap' }}>
                <div>
                  <div style={{ fontSize: '0.85rem', color: 'var(--muted)' }}>Name:</div>
                  <div style={{ fontSize: '1.1rem', fontWeight: '600', color: 'var(--text)' }} id="studentName">
                    {studentProfile.name}
                  </div>
                </div>
                <div>
                  <div style={{ fontSize: '0.85rem', color: 'var(--muted)' }}>KCET Student ID:</div>
                  <div style={{ fontSize: '1.1rem', fontWeight: '600', color: 'var(--purple-l)' }} id="studentKcetId">
                    {studentProfile.id}
                  </div>
                </div>
              </div>
            </div>
            {data && !data.has_data && (
              <div style={{ background: 'rgba(124, 58, 237, 0.1)', border: '1px solid rgba(124, 58, 237, 0.25)', borderRadius: '8px', padding: '8px 14px', fontSize: '0.85rem', color: 'var(--purple-l)' }}>
                💡 Welcome! Complete your first mock exam below to see your live score, rank, and topic insights.
              </div>
            )}
          </div>
        </div>

        {/* Available Practice Exams Section */}
        <div className="section-card" style={{ marginBottom: '20px', padding: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <div>
              <h2 style={{ fontSize: '1.2rem', fontWeight: '600', color: 'var(--text)', margin: 0 }}>📝 Available Practice Exams</h2>
              <p style={{ fontSize: '0.82rem', color: 'var(--muted)', marginTop: '2px', marginBottom: 0 }}>
                Select an authentic mock exam created by your administrator
              </p>
            </div>
          </div>
          {availableSubjects.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '24px', color: 'var(--muted)', fontSize: '0.9rem' }}>
              No published exams available at the moment.
            </div>
          ) : (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '14px' }}>
              {availableSubjects.flatMap(sg => (sg.exams || []).map(ex => {
                const firstSet = ex.sets && ex.sets.length > 0 ? ex.sets[0] : null;
                return (
                  <div key={ex.exam_id} style={{ background: 'var(--s2)', border: '1px solid var(--border)', borderRadius: '10px', padding: '16px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between', gap: '12px' }}>
                    <div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                        <span style={{ fontSize: '0.75rem', fontWeight: '700', color: 'var(--purple-l)', background: 'rgba(124,58,237,0.15)', padding: '3px 8px', borderRadius: '4px' }}>
                          {sg.subject}
                        </span>
                        <span style={{ fontSize: '0.75rem', color: 'var(--muted)' }}>60 Qs • 80 Mins</span>
                      </div>
                      <h3 style={{ fontSize: '1.05rem', fontWeight: '600', color: 'var(--text)', marginTop: '8px', marginBottom: '4px' }}>
                        {ex.exam_name || `${sg.subject} Mock Exam`}
                      </h3>
                    </div>
                    {firstSet ? (
                      <a 
                        href={`/exam?set=${firstSet.exam_set_id}&subject=${encodeURIComponent(sg.subject)}&name=${encodeURIComponent(ex.exam_name || sg.subject)}&label=${firstSet.set_label}`}
                        className="btn-primary"
                        style={{ textAlign: 'center', padding: '8px 12px', fontSize: '0.85rem', textDecoration: 'none' }}
                      >
                        Take Exam →
                      </a>
                    ) : (
                      <button className="btn-primary" disabled style={{ opacity: 0.5 }}>Unavailable</button>
                    )}
                  </div>
                );
              }))}
            </div>
          )}
        </div>

        {/* Main Dashboard Content */}
        <div id="dashContent">
          {/* Filter Bar */}
          <div className="dash-filters section-card">
            <div className="filter-row">
              <div className="filter-group">
                <label className="input-label">Subject</label>
                <select 
                  id="filterSubject" 
                  className="select-input" 
                  value={selectedSubject} 
                  onChange={e => setSelectedSubject(e.target.value)}
                >
                  <option value="all">All Subjects</option>
                  <option value="Physics">Physics</option>
                  <option value="Chemistry">Chemistry</option>
                  <option value="Mathematics">Mathematics</option>
                  <option value="Biology">Biology</option>
                </select>
              </div>
              <div className="filter-group">
                <label className="input-label">Status</label>
                <select 
                  id="filterStatus" 
                  className="select-input" 
                  value={selectedStatus} 
                  onChange={e => setSelectedStatus(e.target.value)}
                >
                  <option value="all">All</option>
                  <option value="pass">Pass</option>
                  <option value="fail">Fail</option>
                </select>
              </div>
            </div>
          </div>

          {/* Real KPI Row */}
          <div className="kpi-row" id="kpiRow">
            <div className="kpi-tile">
              <div className="kpi-tile-icon purple">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M9 11l3 3L22 4" />
                  <path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11" />
                </svg>
              </div>
              <div className="kpi-tile-body">
                <div className="kpi-tile-val" id="kpiStudents">
                  {data ? data.kpis.examsTaken : 0}
                </div>
                <div className="kpi-tile-label">Exams Taken</div>
              </div>
            </div>

            <div className="kpi-tile">
              <div className="kpi-tile-icon blue">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" />
                  <polyline points="14 2 14 8 20 8" />
                </svg>
              </div>
              <div className="kpi-tile-body">
                <div className="kpi-tile-val" id="kpiSubmissions">
                  {data ? data.kpis.submissions : 0}
                </div>
                <div className="kpi-tile-label">Submissions</div>
              </div>
            </div>

            <div className="kpi-tile">
              <div className="kpi-tile-icon cyan">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="12" cy="8" r="6" />
                  <path d="M15.477 12.89L17 22l-5-3-5 3 1.523-9.11" />
                </svg>
              </div>
              <div className="kpi-tile-body">
                <div className="kpi-tile-val" id="kpiAvgScore">
                  {data ? data.kpis.avgScore : 0}%
                </div>
                <div className="kpi-tile-label">Avg Score</div>
              </div>
            </div>

            <div className="kpi-tile">
              <div className="kpi-tile-icon green">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
                </svg>
              </div>
              <div className="kpi-tile-body">
                <div className="kpi-tile-val" id="kpiPassRate">
                  {data ? data.kpis.passRate : 0}%
                </div>
                <div className="kpi-tile-label">Pass Rate</div>
              </div>
            </div>

            <div className="kpi-tile">
              <div className="kpi-tile-icon orange">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="12" cy="12" r="10" />
                  <polyline points="12 6 12 12 16 14" />
                </svg>
              </div>
              <div className="kpi-tile-body">
                <div className="kpi-tile-val" id="kpiAvgTime">
                  {data ? data.kpis.avgTime : 0}m
                </div>
                <div className="kpi-tile-label">Avg Time</div>
              </div>
            </div>

            <div className="kpi-tile">
              <div className="kpi-tile-icon purple">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M12 15l-3 3h6l-3-3z" />
                  <path d="M5 9l7-7 7 7" />
                  <path d="M4 19h16" />
                </svg>
              </div>
              <div className="kpi-tile-body">
                <div className="kpi-tile-val" id="kpiRankValue">
                  {data && data.kpis.rank && data.kpis.rank !== '—' ? `#${data.kpis.rank}` : '—'}
                </div>
                <div className="kpi-tile-label">Your Rank</div>
                <div className="kpi-tile-hint" id="kpiRankHint" style={{ fontSize: '0.68rem', color: 'var(--muted)', marginTop: '2px', lineHeight: '1.2' }}>
                  {data?.kpis?.rankHint || 'Score at least 30% on average to qualify on statewide leaderboard'}
                </div>
              </div>
            </div>
          </div>

          {/* Charts Row */}
          <div className="charts-row">
            <div className="chart-card section-card wide">
              <div className="chart-card-header">
                <h3>Subject Performance Average</h3>
              </div>
              <div className="chart-wrap" style={{ minHeight: '260px' }}>
                {data && <Bar data={topicChartData} options={chartOptions} />}
              </div>
            </div>
          </div>

          <div className="charts-row" style={{ marginTop: '20px' }}>
            <div className="chart-card section-card">
              <div className="chart-card-header">
                <h3>Score Progression Trend</h3>
              </div>
              <div className="chart-wrap" style={{ minHeight: '220px' }}>
                {data && <Line data={setChartData} options={chartOptions} />}
              </div>
            </div>
            <div className="chart-card section-card">
              <div className="chart-card-header">
                <h3>Pass vs Fail Distribution</h3>
              </div>
              <div className="chart-wrap" style={{ minHeight: '220px' }}>
                {data && <Doughnut data={passFailChartData} options={doughnutOptions} />}
              </div>
            </div>
          </div>

          {/* AI Performance Analysis Section */}
          <div className="ai-block section-card" id="aiBlock" style={{ marginTop: '20px' }}>
            <div className="ai-block-header">
              <div className="ai-block-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="12" cy="12" r="3" />
                  <path d="M19.07 4.93a10 10 0 010 14.14M4.93 4.93a10 10 0 000 14.14" />
                  <path d="M15.54 8.46a5 5 0 010 7.07M8.46 8.46a5 5 0 000 7.07" />
                </svg>
              </div>
              <div>
                <h2>Performance Analysis</h2>
                <p className="section-sub" id="aiAnalysisFor">
                  {data?.has_data 
                    ? `Live diagnostic across ${data.kpis.submissions} completed exam attempt${data.kpis.submissions > 1 ? 's' : ''}`
                    : 'Personalized KCET strengths & weaknesses will appear here once you take an exam'}
                </p>
              </div>
              <div className="ai-block-badge">RAG Powered</div>
            </div>

            <div className="ai-zones-grid">
              <div className="ai-zone strong">
                <div className="ai-zone-header">
                  <span className="zone-icon">💪</span>
                  <span>Strong Areas (≥ 75%)</span>
                  <span className="zone-count" id="strongCount">
                    {data?.aiAnalysis?.strong_areas?.length || 0}
                  </span>
                </div>
                <ul className="zone-items" id="strongItems">
                  {(data?.aiAnalysis?.strong_areas || []).length > 0 ? (
                    data.aiAnalysis.strong_areas.map((item, idx) => (
                      <li key={idx}>✓ {item}</li>
                    ))
                  ) : (
                    <li style={{ color: 'var(--muted)', fontStyle: 'italic' }}>
                      {data?.has_data ? 'No topics ≥ 75% yet' : 'Take exams to identify strengths'}
                    </li>
                  )}
                </ul>
              </div>

              <div className="ai-zone improve">
                <div className="ai-zone-header">
                  <span className="zone-icon">📈</span>
                  <span>Can Improve (50–74%)</span>
                  <span className="zone-count" id="improveCount">
                    {data?.aiAnalysis?.can_improve_areas?.length || 0}
                  </span>
                </div>
                <ul className="zone-items" id="improveItems">
                  {(data?.aiAnalysis?.can_improve_areas || []).length > 0 ? (
                    data.aiAnalysis.can_improve_areas.map((item, idx) => (
                      <li key={idx}>• {item}</li>
                    ))
                  ) : (
                    <li style={{ color: 'var(--muted)', fontStyle: 'italic' }}>
                      {data?.has_data ? 'No topics in 50–74% range' : 'Pending practice'}
                    </li>
                  )}
                </ul>
              </div>

              <div className="ai-zone weak">
                <div className="ai-zone-header">
                  <span className="zone-icon">⚠️</span>
                  <span>Weak Areas (&lt; 50%)</span>
                  <span className="zone-count" id="weakCount">
                    {data?.aiAnalysis?.weak_areas?.length || 0}
                  </span>
                </div>
                <ul className="zone-items" id="weakItems">
                  {(data?.aiAnalysis?.weak_areas || []).length > 0 ? (
                    data.aiAnalysis.weak_areas.map((item, idx) => (
                      <li key={idx}>! {item}</li>
                    ))
                  ) : (
                    <li style={{ color: 'var(--muted)', fontStyle: 'italic' }}>
                      {data?.has_data ? 'No weak areas detected!' : 'Take exams to pinpoint gaps'}
                    </li>
                  )}
                </ul>
              </div>
            </div>

            {/* Rank Booster ("What If I Improve?") + 3-Step Action Plan Checklist */}
            <div className="ai-enhancement-grid">
              {/* Option 3: Score & Rank Impact Booster */}
              <div className="enhancement-card booster">
                <div className="enhancement-header">
                  <div className="enhancement-title">
                    <span>🚀</span>
                    <span>Score &amp; Rank Impact Booster</span>
                  </div>
                  <span className="enhancement-badge badge-green">What If I Improve?</span>
                </div>

                <div className="rank-booster-comparison">
                  <div className="rank-tile">
                    <div className="rank-tile-label">Current Rank</div>
                    <div className="rank-tile-value" style={{ color: 'var(--muted)' }}>
                      #{currentRank.toLocaleString()}
                    </div>
                    <div className="rank-tile-sub">Score: {currentAvgScore}%</div>
                  </div>

                  <div className="rank-arrow-indicator">
                    <span className="rank-arrow-icon">➔</span>
                    <span className="rank-leap-badge">+{simulatedRankLeap.toLocaleString()} Ranks</span>
                  </div>

                  <div className="rank-tile">
                    <div className="rank-tile-label" style={{ color: '#10b981' }}>Projected Boost</div>
                    <div className="rank-tile-value" style={{ color: '#10b981' }}>
                      #{simulatedBoostedRank.toLocaleString()}
                    </div>
                    <div className="rank-tile-sub" style={{ color: '#10b981' }}>
                      Target: {simulatedTargetScore}%
                    </div>
                  </div>
                </div>

                <div className="simulator-controls">
                  <div className="simulator-label">
                    <span>Simulate Weak Topic Mastery:</span>
                    <span style={{ fontWeight: '700', color: '#10b981' }}>+{simulatedMarksGain} Marks in KCET</span>
                  </div>
                  <div className="simulator-buttons">
                    {[5, 10, 15, 20].map((boostVal) => (
                      <button
                        key={boostVal}
                        type="button"
                        className={`sim-btn ${simulatedBoostPct === boostVal ? 'active' : ''}`}
                        onClick={() => setSimulatedBoostPct(boostVal)}
                      >
                        +{boostVal}%
                      </button>
                    ))}
                  </div>
                </div>

                <div className="booster-footer-note">
                  🎯 <strong>Rank Opportunity:</strong> Gaining +{simulatedMarksGain} marks elevates your rank by ~{simulatedRankLeap.toLocaleString()} positions, unlocking more competitive CSE/ECE branches in the KCET Predictor below!
                </div>
              </div>

              {/* Option 2: 3-Step Action Plan & Interactive Checklist */}
              <div className="enhancement-card checklist">
                <div className="enhancement-header">
                  <div className="enhancement-title">
                    <span>📋</span>
                    <span>3-Step Study Action Plan</span>
                  </div>
                  <span className="enhancement-badge badge-purple">
                    {completedStepsCount} of {actionSteps.length} Done ({progressPct}%)
                  </span>
                </div>

                <div className="checklist-progress-container">
                  <div className="checklist-progress-header">
                    <span>Task Progress</span>
                    <span>{progressPct}% Completed</span>
                  </div>
                  <div className="checklist-progress-track">
                    <div className="checklist-progress-fill" style={{ width: `${progressPct}%` }} />
                  </div>
                </div>

                <ul className="action-checklist-list">
                  {actionSteps.map((step) => {
                    const isDone = !!checkedActionSteps[step.id];
                    return (
                      <li
                        key={step.id}
                        className={`checklist-item ${isDone ? 'done' : ''}`}
                        onClick={() => toggleActionStep(step.id)}
                      >
                        <div className="checklist-checkbox">
                          {isDone && (
                            <svg viewBox="0 0 24 24" width="13" height="13" stroke="currentColor" strokeWidth="3" fill="none">
                              <polyline points="20 6 9 17 4 12" />
                            </svg>
                          )}
                        </div>
                        <div className="checklist-content">
                          <div className="checklist-meta">
                            <span className="checklist-step-badge">{step.badge || 'Step'} • {step.category || 'Focus'}</span>
                          </div>
                          <div className="checklist-item-title">{step.title}</div>
                          <div className="checklist-item-desc">{step.desc}</div>
                        </div>
                      </li>
                    );
                  })}
                </ul>

                <div className="checklist-actions">
                  <span style={{ fontSize: '0.72rem', color: 'var(--muted)' }}>
                    {progressPct === 100 ? '🎉 All tasks completed! Great job.' : 'Click to check off tasks as you complete them'}
                  </span>
                  {completedStepsCount > 0 && (
                    <button type="button" className="checklist-reset-btn" onClick={resetActionSteps}>
                      Reset
                    </button>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* KCET College Prediction based on Rank Section */}
          <div className="section-card" id="collegePredictorSection" style={{ marginTop: '20px' }}>
            <div className="ai-block-header">
              <div className="ai-block-icon" style={{ background: 'rgba(16, 185, 129, 0.15)', color: '#10b981' }}>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M22 10v6M2 10l10-5 10 5-10 5z" />
                  <path d="M6 12v5c3 3 9 3 12 0v-5" />
                </svg>
              </div>
              <div>
                <h2>KCET College Predictor based on Rank</h2>
                <p className="section-sub">Enter your KCET rank to predict eligible engineering colleges & branches across Karnataka</p>
              </div>
            </div>

            {/* Controls Row */}
            <div style={{ marginTop: '18px', display: 'flex', gap: '12px', alignItems: 'center', flexWrap: 'wrap' }}>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', flex: '1 1 200px', minWidth: '180px' }}>
                <label style={{ fontSize: '0.78rem', color: 'var(--muted)', fontWeight: 600 }}>KCET Rank</label>
                <input 
                  type="number" 
                  id="predictorRankInput" 
                  className="select-input" 
                  placeholder="Enter KCET Rank (e.g. 5000)"
                  value={predictorRank}
                  onChange={e => setPredictorRank(e.target.value)}
                  onKeyDown={e => { if (e.key === 'Enter') handlePredictColleges(); }}
                  min="1"
                  style={{ width: '100%' }}
                />
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', flex: '0 1 180px', minWidth: '150px' }}>
                <label style={{ fontSize: '0.78rem', color: 'var(--muted)', fontWeight: 600 }}>Reservation Category</label>
                <select 
                  className="select-input"
                  value={predictorCategory}
                  onChange={e => setPredictorCategory(e.target.value)}
                  style={{ width: '100%', cursor: 'pointer' }}
                >
                  <option value="GM">General Merit (GM)</option>
                  <option value="2A">OBC Category 2A</option>
                  <option value="2B">OBC Category 2B</option>
                  <option value="3A">OBC Category 3A</option>
                  <option value="3B">OBC Category 3B</option>
                  <option value="SC">Scheduled Caste (SC)</option>
                  <option value="ST">Scheduled Tribe (ST)</option>
                  <option value="HK">Hyderabad-Karnataka (HK)</option>
                </select>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', flex: '0 1 170px', minWidth: '140px' }}>
                <label style={{ fontSize: '0.78rem', color: 'var(--muted)', fontWeight: 600 }}>Location / City</label>
                <select 
                  className="select-input"
                  value={predictorLocation}
                  onChange={e => setPredictorLocation(e.target.value)}
                  style={{ width: '100%', cursor: 'pointer' }}
                >
                  <option value="all">All Karnataka</option>
                  <option value="bangalore">Bangalore</option>
                  <option value="mysore">Mysore</option>
                </select>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', justifyContent: 'flex-end', flex: '0 0 auto' }}>
                <label style={{ fontSize: '0.78rem', color: 'transparent' }}>Action</label>
                <button 
                  className="btn-primary" 
                  id="predictCollegesBtn"
                  onClick={() => handlePredictColleges()}
                  disabled={predictorLoading || !predictorRank}
                  style={{
                    padding: '10px 22px',
                    fontSize: '0.92rem',
                    fontWeight: 700,
                    background: 'linear-gradient(135deg, #10b981, #2563eb)',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px'
                  }}
                >
                  {predictorLoading ? 'Predicting...' : 'Predict Colleges 🎓'}
                </button>
              </div>
            </div>

            {/* Quick Rank Chips */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap', marginTop: '12px' }}>
              <span style={{ fontSize: '0.78rem', color: 'var(--muted)', fontWeight: 600 }}>Quick Ranks:</span>
              {[
                { label: 'Rank #1,200', val: 1200 },
                { label: 'Rank #3,500', val: 3500 },
                { label: 'Rank #8,000', val: 8000 },
                { label: 'Rank #15,000', val: 15000 },
                { label: 'Rank #30,000', val: 30000 },
                { label: 'Rank #55,000', val: 55000 }
              ].map(chip => (
                <button
                  key={chip.val}
                  type="button"
                  onClick={() => {
                    setPredictorRank(String(chip.val));
                    handlePredictColleges(chip.val);
                  }}
                  style={{
                    background: 'var(--s2)',
                    border: '1px solid var(--border)',
                    color: 'var(--purple-l)',
                    padding: '3px 10px',
                    borderRadius: '12px',
                    fontSize: '0.76rem',
                    cursor: 'pointer',
                    fontWeight: 600,
                    transition: 'all 0.2s'
                  }}
                >
                  {chip.label}
                </button>
              ))}
            </div>

            {predictorError && (
              <div style={{ marginTop: '14px', color: 'var(--red-l)', fontSize: '0.86rem', padding: '8px 12px', background: 'rgba(239,68,68,0.1)', border: '1px solid var(--red)', borderRadius: '6px' }}>
                {predictorError}
              </div>
            )}

            {/* Prediction Results */}
            {predictionResults && (
              <div style={{ marginTop: '20px' }}>
                {/* Status / Metric Overview Banner */}
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  flexWrap: 'wrap',
                  gap: '12px',
                  background: 'var(--s2)',
                  border: '1px solid var(--border)',
                  borderRadius: '10px',
                  padding: '14px 18px',
                  marginBottom: '16px'
                }}>
                  <div>
                    <div style={{ fontSize: '0.98rem', fontWeight: 800, color: 'var(--text)' }}>
                      Prediction for KCET Rank #{parseInt(predictionResults.rank).toLocaleString()}
                    </div>
                    <div style={{ fontSize: '0.82rem', color: 'var(--muted)', marginTop: '2px' }}>
                      Category: <strong>{predictionResults.category}</strong> • Region: <strong>{predictionResults.location === 'all' ? 'All Karnataka' : predictionResults.location}</strong> • Total Matches: <strong>{predictionResults.total_colleges}</strong>
                    </div>
                  </div>
                  <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                    <span style={{ padding: '4px 12px', borderRadius: '16px', fontSize: '0.78rem', fontWeight: 700, background: 'rgba(16,185,129,0.18)', color: '#34d399', border: '1px solid rgba(16,185,129,0.4)' }}>
                      🟢 Safe: {predictionResults.counts?.safe || 0}
                    </span>
                    <span style={{ padding: '4px 12px', borderRadius: '16px', fontSize: '0.78rem', fontWeight: 700, background: 'rgba(234,179,8,0.18)', color: '#facc15', border: '1px solid rgba(234,179,8,0.4)' }}>
                      🟡 Target: {predictionResults.counts?.target || 0}
                    </span>
                    <span style={{ padding: '4px 12px', borderRadius: '16px', fontSize: '0.78rem', fontWeight: 700, background: 'rgba(239,68,68,0.18)', color: '#f87171', border: '1px solid rgba(239,68,68,0.4)' }}>
                      🔴 Reach: {predictionResults.counts?.reach || 0}
                    </span>
                  </div>
                </div>

                {/* Tabs */}
                <div style={{ display: 'flex', gap: '8px', borderBottom: '1px solid var(--border)', paddingBottom: '10px', marginBottom: '16px', flexWrap: 'wrap' }}>
                  <button
                    type="button"
                    onClick={() => setActivePredictionTab('safe')}
                    style={{
                      padding: '8px 16px',
                      borderRadius: '8px',
                      fontSize: '0.85rem',
                      fontWeight: 700,
                      cursor: 'pointer',
                      border: activePredictionTab === 'safe' ? '1px solid #10b981' : '1px solid var(--border)',
                      background: activePredictionTab === 'safe' ? 'rgba(16,185,129,0.2)' : 'var(--s1)',
                      color: activePredictionTab === 'safe' ? '#34d399' : 'var(--muted)'
                    }}
                  >
                    🟢 Safe Colleges ({predictionResults.counts?.safe || 0})
                  </button>
                  <button
                    type="button"
                    onClick={() => setActivePredictionTab('target')}
                    style={{
                      padding: '8px 16px',
                      borderRadius: '8px',
                      fontSize: '0.85rem',
                      fontWeight: 700,
                      cursor: 'pointer',
                      border: activePredictionTab === 'target' ? '1px solid #eab308' : '1px solid var(--border)',
                      background: activePredictionTab === 'target' ? 'rgba(234,179,8,0.2)' : 'var(--s1)',
                      color: activePredictionTab === 'target' ? '#facc15' : 'var(--muted)'
                    }}
                  >
                    🟡 Target Matches ({predictionResults.counts?.target || 0})
                  </button>
                  <button
                    type="button"
                    onClick={() => setActivePredictionTab('reach')}
                    style={{
                      padding: '8px 16px',
                      borderRadius: '8px',
                      fontSize: '0.85rem',
                      fontWeight: 700,
                      cursor: 'pointer',
                      border: activePredictionTab === 'reach' ? '1px solid #ef4444' : '1px solid var(--border)',
                      background: activePredictionTab === 'reach' ? 'rgba(239,68,68,0.2)' : 'var(--s1)',
                      color: activePredictionTab === 'reach' ? '#f87171' : 'var(--muted)'
                    }}
                  >
                    🔴 Ambitious / Reach ({predictionResults.counts?.reach || 0})
                  </button>
                  <button
                    type="button"
                    onClick={() => setActivePredictionTab('all')}
                    style={{
                      padding: '8px 16px',
                      borderRadius: '8px',
                      fontSize: '0.85rem',
                      fontWeight: 700,
                      cursor: 'pointer',
                      border: activePredictionTab === 'all' ? '1px solid var(--purple)' : '1px solid var(--border)',
                      background: activePredictionTab === 'all' ? 'rgba(124,58,237,0.2)' : 'var(--s1)',
                      color: activePredictionTab === 'all' ? 'var(--purple-l)' : 'var(--muted)'
                    }}
                  >
                    All Colleges ({predictionResults.total_colleges})
                  </button>
                </div>

                {/* College Cards Grid */}
                {(() => {
                  let listToDisplay = [];
                  if (activePredictionTab === 'safe') listToDisplay = predictionResults.matches?.safe || [];
                  else if (activePredictionTab === 'target') listToDisplay = predictionResults.matches?.target || [];
                  else if (activePredictionTab === 'reach') listToDisplay = predictionResults.matches?.reach || [];
                  else {
                    listToDisplay = [
                      ...(predictionResults.matches?.safe || []),
                      ...(predictionResults.matches?.target || []),
                      ...(predictionResults.matches?.reach || [])
                    ];
                  }

                  if (listToDisplay.length === 0) {
                    return (
                      <div style={{ textAlign: 'center', padding: '30px', color: 'var(--muted)', background: 'var(--s2)', borderRadius: '10px', fontSize: '0.9rem' }}>
                        No colleges found under this category filter. Try switching tabs or choosing 'All Karnataka'.
                      </div>
                    );
                  }

                  return (
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '14px' }}>
                      {listToDisplay.map((col, idx) => {
                        const isSafe = col.match_type === 'safe';
                        const isTarget = col.match_type === 'target';
                        const badgeColor = isSafe ? '#10b981' : isTarget ? '#eab308' : '#ef4444';
                        const badgeBg = isSafe ? 'rgba(16,185,129,0.15)' : isTarget ? 'rgba(234,179,8,0.15)' : 'rgba(239,68,68,0.15)';

                        return (
                          <div 
                            key={idx}
                            style={{
                              background: 'var(--s2)',
                              border: `1px solid ${isSafe ? 'rgba(16,185,129,0.3)' : isTarget ? 'rgba(234,179,8,0.3)' : 'var(--border)'}`,
                              borderRadius: '10px',
                              padding: '16px',
                              display: 'flex',
                              flexDirection: 'column',
                              justifyContent: 'space-between',
                              transition: 'transform 0.2s, box-shadow 0.2s'
                            }}
                          >
                            <div>
                              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '10px', marginBottom: '8px' }}>
                                <h3 style={{ fontSize: '1.02rem', fontWeight: 700, margin: 0, color: 'var(--text)', lineHeight: '1.4' }}>
                                  {col.name}
                                </h3>
                                <span style={{
                                  padding: '2px 8px',
                                  borderRadius: '12px',
                                  fontSize: '0.72rem',
                                  fontWeight: 800,
                                  background: col.tier === 1 ? 'rgba(124,58,237,0.2)' : 'rgba(255,255,255,0.08)',
                                  color: col.tier === 1 ? 'var(--purple-l)' : 'var(--muted)',
                                  whiteSpace: 'nowrap',
                                  border: col.tier === 1 ? '1px solid rgba(124,58,237,0.4)' : '1px solid var(--border)'
                                }}>
                                  {col.tier_label}
                                </span>
                              </div>

                              <div style={{ display: 'flex', gap: '8px', alignItems: 'center', marginBottom: '10px', flexWrap: 'wrap' }}>
                                <span style={{ fontSize: '0.78rem', color: 'var(--muted)', display: 'flex', alignItems: 'center', gap: '3px' }}>
                                  📍 {col.location}
                                </span>
                                <span style={{ fontSize: '0.78rem', color: 'var(--muted)' }}>•</span>
                                <span style={{ fontSize: '0.78rem', fontWeight: 600, color: 'var(--text)' }}>
                                  Cutoff: #{col.cutoff_rank.toLocaleString()}
                                </span>
                              </div>

                              <div style={{
                                display: 'inline-flex',
                                alignItems: 'center',
                                gap: '6px',
                                padding: '4px 10px',
                                borderRadius: '6px',
                                background: badgeBg,
                                color: badgeColor,
                                fontSize: '0.76rem',
                                fontWeight: 800,
                                marginBottom: '12px',
                                border: `1px solid ${badgeColor}40`
                              }}>
                                <span>{isSafe ? '✓' : isTarget ? '⚡' : '🎯'}</span>
                                <span>{col.chance_label} ({col.chance_pct}%)</span>
                              </div>

                              <p style={{ fontSize: '0.82rem', color: 'var(--muted)', lineHeight: '1.45', margin: '0 0 12px 0' }}>
                                {col.description}
                              </p>
                            </div>

                            <div>
                              <div style={{ fontSize: '0.74rem', color: 'var(--muted)', fontWeight: 600, marginBottom: '6px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                                Eligible Branches
                              </div>
                              <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
                                {col.branches && col.branches.map((b, bIdx) => (
                                  <span 
                                    key={bIdx}
                                    style={{
                                      fontSize: '0.72rem',
                                      padding: '2px 8px',
                                      borderRadius: '4px',
                                      background: 'rgba(255,255,255,0.05)',
                                      border: '1px solid var(--border)',
                                      color: 'var(--text)'
                                    }}
                                  >
                                    {b}
                                  </span>
                                ))}
                              </div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  );
                })()}
              </div>
            )}
          </div>


          {/* Exam History Section */}
          <div className="section-card results-card" style={{ marginTop: '20px' }}>
            <div className="results-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
              <h3>My Exam History ({filteredHistory.length})</h3>
              <div className="results-search" style={{ maxWidth: '280px' }}>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="11" cy="11" r="8" />
                  <line x1="21" y1="21" x2="16.65" y2="16.65" />
                </svg>
                <input 
                  type="text" 
                  id="searchInput" 
                  className="search-input" 
                  placeholder="Search subject or exam..." 
                  value={searchTerm}
                  onChange={e => setSearchTerm(e.target.value)}
                />
              </div>
            </div>
            <div className="table-scroll">
              <table className="results-table">
                <thead>
                  <tr>
                    <th>Subject</th>
                    <th>Exam</th>
                    <th>Score</th>
                    <th>Time</th>
                    <th>Status</th>
                    <th>Date</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredHistory.length > 0 ? (
                    filteredHistory.map((h, i) => (
                      <tr key={i}>
                        <td><strong>{h.subject}</strong></td>
                        <td>{h.exam_name || `${h.subject} Mock Exam`}</td>
                        <td style={{ fontWeight: '600' }}>{h.score}</td>
                        <td>{h.time}</td>
                        <td>
                          <span style={{ 
                            padding: '4px 10px', 
                            borderRadius: '4px', 
                            fontSize: '0.8rem',
                            fontWeight: '600',
                            background: h.status === 'Pass' ? 'rgba(16,185,129,0.15)' : 'rgba(239,68,68,0.15)',
                            color: h.status === 'Pass' ? 'var(--green-l)' : 'var(--red-l)'
                          }}>
                            {h.status}
                          </span>
                        </td>
                        <td>{h.date}</td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan="6" style={{ textAlign: 'center', padding: '36px', color: 'var(--muted)' }}>
                        {data?.has_data ? (
                          'No exam attempts match your current search and filters.'
                        ) : (
                          <div>
                            <div style={{ fontSize: '1.8rem', marginBottom: '8px' }}>📝</div>
                            <div style={{ fontWeight: '600', color: 'var(--text)', marginBottom: '4px' }}>
                              No Exam Attempts Yet
                            </div>
                            <div>Take an available practice exam from the top section to record your first score!</div>
                          </div>
                        )}
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </main>
    </>
  );
};

export default Dashboard;
