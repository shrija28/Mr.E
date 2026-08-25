import React, { useState, useEffect } from 'react';
import {
  Chart as ChartJS, CategoryScale, LinearScale, BarElement, PointElement, LineElement, ArcElement, Title, Tooltip, Legend, Filler
} from 'chart.js';
import { Bar, Line, Doughnut } from 'react-chartjs-2';

ChartJS.register(CategoryScale, LinearScale, BarElement, PointElement, LineElement, ArcElement, Title, Tooltip, Legend, Filler);

const Dashboard = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setTimeout(() => {
      setData({
        kpis: { examsTaken: 12, submissions: 18, avgScore: 78, passRate: 85, avgTime: 45, rank: 124 },
        topicData: { labels: ['Physics', 'Chemistry', 'Math', 'Bio'], scores: [82, 65, 90, 45] },
        setData: { labels: ['Set A', 'Set B', 'Set C', 'Set D'], scores: [70, 75, 80, 85] },
        passFailData: { labels: ['Pass', 'Fail'], counts: [15, 3] },
        topStudents: [
          { rank: 1, name: 'Alice Smith', id: 'KCE-2024-001', score: 98, progress: '+5%' },
          { rank: 2, name: 'Bob Johnson', id: 'KCE-2024-045', score: 95, progress: '+2%' },
          { rank: 3, name: 'Charlie Davis', id: 'KCE-2024-112', score: 92, progress: '+8%' }
        ],
        examHistory: [
          { subject: 'Physics', set: 'Set A', score: '82%', time: '45m', status: 'Pass', date: 'Oct 12, 2023' },
          { subject: 'Chemistry', set: 'Set B', score: '65%', time: '50m', status: 'Pass', date: 'Oct 14, 2023' }
        ]
      });
      setLoading(false);
    }, 1000);
  }, []);

  const chartOptions = { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'bottom', labels: { color: '#e8e8f4' } } }, scales: { y: { beginAtZero: true, grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#6868a0' } }, x: { grid: { display: false }, ticks: { color: '#6868a0' } } } };
  const doughnutOptions = { ...chartOptions, scales: {}, cutout: '70%' };

  let topicChartData = null, setChartData = null, passFailChartData = null;
  
  if (data) {
    topicChartData = { labels: data.topicData.labels, datasets: [{ label: 'Average Score (%)', data: data.topicData.scores, backgroundColor: 'rgba(124, 58, 237, 0.6)', borderColor: 'rgba(124, 58, 237, 1)', borderWidth: 1, borderRadius: 4 }] };
    setChartData = { labels: data.setData.labels, datasets: [{ label: 'Score Trend', data: data.setData.scores, borderColor: 'rgba(16, 185, 129, 1)', backgroundColor: 'rgba(16, 185, 129, 0.1)', fill: true, tension: 0.4 }] };
    passFailChartData = { labels: data.passFailData.labels, datasets: [{ data: data.passFailData.counts, backgroundColor: ['rgba(16, 185, 129, 0.8)', 'rgba(239, 68, 68, 0.8)'], borderWidth: 0 }] };
  }

  return (
    <>
      <main className="dash-main">
    
    <div className="dash-hero">
      <div>
        <h1 className="dash-title">My <span className="hero-gradient">Dashboard</span></h1>
        <p className="dash-sub" id="dashSubtitle">Your personal performance analytics across all subjects</p>
      </div>
      <div className="dash-hero-right">
        <div className="last-updated" id="lastUpdated">Last updated: —</div>
        <button className="btn-outline" >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 11-2.12-9.36L23 10"/></svg>
          Refresh
        </button>
      </div>
    </div>

    
    <div className="section-card" style={{"marginBottom":"20px","padding":"16px"}}>
      <div style={{"display":"flex","alignItems":"center","justifyContent":"space-between"}}>
        <div>
          <div style={{"color":"var(--muted)","fontSize":"0.8rem","textTransform":"uppercase","letterSpacing":"0.5px","marginBottom":"4px"}}>Student Profile</div>
          <div style={{"display":"flex","alignItems":"center","gap":"16px"}}>
            <div>
              <div style={{"fontSize":"0.9rem","color":"var(--muted)"}}>Name:</div>
              <div style={{"fontSize":"1.1rem","fontWeight":"600","color":"var(--text)"}} id="studentName">—</div>
            </div>
            <div>
              <div style={{"fontSize":"0.9rem","color":"var(--muted)"}}>Student ID:</div>
              <div style={{"fontSize":"1.1rem","fontWeight":"600","color":"var(--purple-l)"}} id="studentKcetId">—</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    
    <div className="empty-state" id="emptyState" style={{"display":"none"}}>
      <div className="empty-icon">📊</div>
      <h3>No Submissions Yet</h3>
      <p>Complete and submit exams to see your performance analytics here.</p>
      <div className="empty-actions">
        <a href="/exam" className="btn-primary" id="emptyStateTakeExamBtn" data-take-exam>Take Exam →</a>
      </div>
    </div>

    <div id="dashContent">
      
      <div className="dash-filters section-card">
        <div className="filter-row">
          <div className="filter-group" style={{"display":"none"}}>
            <label className="input-label">Student</label>
            <select id="filterStudent" className="select-input" >
              <option value="all">All Students</option>
            </select>
          </div>
          <div className="filter-group">
            <label className="input-label">Subject</label>
            <select id="filterSubject" className="select-input" >
              <option value="all">All Subjects</option>
            </select>
          </div>
          <div className="filter-group">
            <label className="input-label">Paper Set</label>
            <select id="filterSet" className="select-input" >
              <option value="all">All Sets</option>
              <option value="Set A">Set A</option>
              <option value="Set B">Set B</option>
              <option value="Set C">Set C</option>
              <option value="Set D">Set D</option>
            </select>
          </div>
          <div className="filter-group">
            <label className="input-label">Status</label>
            <select id="filterStatus" className="select-input" >
              <option value="all">All</option>
              <option value="pass">Pass</option>
              <option value="fail">Fail</option>
            </select>
          </div>
        </div>
      </div>

      
      <div className="kpi-row" id="kpiRow">
        <div className="kpi-tile">
          <div className="kpi-tile-icon purple"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11"/></svg></div>
          <div className="kpi-tile-body">
            <div className="kpi-tile-val" id="kpiStudents">{data ? data.kpis.examsTaken : 0}</div>
            <div className="kpi-tile-label">Exams Taken</div>
          </div>
          <div className="kpi-tile-trend up" id="kpiStudentsTrend"></div>
        </div>
        <div className="kpi-tile">
          <div className="kpi-tile-icon blue"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/></svg></div>
          <div className="kpi-tile-body">
            <div className="kpi-tile-val" id="kpiSubmissions">{data ? data.kpis.submissions : 0}</div>
            <div className="kpi-tile-label">Submissions</div>
          </div>
          <div className="kpi-tile-trend" id="kpiSubTrend"></div>
        </div>
        <div className="kpi-tile">
          <div className="kpi-tile-icon cyan"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="8" r="6"/><path d="M15.477 12.89L17 22l-5-3-5 3 1.523-9.11"/></svg></div>
          <div className="kpi-tile-body">
            <div className="kpi-tile-val" id="kpiAvgScore">{data ? data.kpis.avgScore : 0}%</div>
            <div className="kpi-tile-label">Avg Score</div>
          </div>
          <div className="kpi-tile-trend" id="kpiScoreTrend"></div>
        </div>
        <div className="kpi-tile">
          <div className="kpi-tile-icon green"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg></div>
          <div className="kpi-tile-body">
            <div className="kpi-tile-val" id="kpiPassRate">{data ? data.kpis.passRate : 0}%</div>
            <div className="kpi-tile-label">Pass Rate</div>
          </div>
          <div className="kpi-tile-trend" id="kpiPassTrend"></div>
        </div>
        <div className="kpi-tile">
          <div className="kpi-tile-icon orange"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg></div>
          <div className="kpi-tile-body">
            <div className="kpi-tile-val" id="kpiAvgTime">{data ? data.kpis.avgTime : 0}m</div>
            <div className="kpi-tile-label">Avg Time</div>
          </div>
          <div className="kpi-tile-trend" id="kpiTimeTrend"></div>
        </div>
        <div className="kpi-tile">
          <div className="kpi-tile-icon purple"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 15l-3 3h6l-3-3z"/><path d="M5 9l7-7 7 7"/><path d="M4 19h16"/></svg></div>
          <div className="kpi-tile-body">
            <div className="kpi-tile-val" id="kpiRankValue">#{data ? data.kpis.rank : "—"}</div>
            <div className="kpi-tile-label">Your Rank</div>
            <div className="kpi-tile-hint" id="kpiRankHint" style={{"fontSize":"0.65rem","color":"var(--muted)","marginTop":"2px","lineHeight":"1.2"}}>score at least 30% on average to enter the leaderboard</div>
          </div>
        </div>
      </div>

      
      <div className="charts-row">
        <div className="chart-card section-card wide">
          <div className="chart-card-header">
            <h3>Topic Performance</h3>
          </div>
          <div className="chart-wrap">{data && <Bar data={topicChartData} options={chartOptions} />}</div>
        </div>
      </div>

      
      <div className="charts-row" style={{"marginTop":"20px"}}>
        <div className="chart-card section-card">
          <div className="chart-card-header"><h3>Set-wise Avg Score</h3></div>
          <div className="chart-wrap">{data && <Line data={setChartData} options={chartOptions} />}</div>
        </div>
        <div className="chart-card section-card">
          <div className="chart-card-header"><h3>Pass vs Fail</h3></div>
          <div className="chart-wrap">{data && <Doughnut data={passFailChartData} options={doughnutOptions} />}</div>
        </div>
      </div>

      
      <div className="ai-block section-card" id="aiBlock">
        <div className="ai-block-header">
          <div className="ai-block-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M19.07 4.93a10 10 0 010 14.14M4.93 4.93a10 10 0 000 14.14"/><path d="M15.54 8.46a5 5 0 010 7.07M8.46 8.46a5 5 0 000 7.07"/></svg>
          </div>
          <div>
            <h2>AI Performance Analysis</h2>
            <p className="section-sub" id="aiAnalysisFor">Analyzing all students</p>
          </div>
          <div className="ai-block-badge">RAG Powered</div>
        </div>

        <div className="ai-zones-grid">
          <div className="ai-zone strong">
            <div className="ai-zone-header">
              <span className="zone-icon">💪</span>
              <span>Strong Areas</span>
              <span className="zone-count" id="strongCount">0</span>
            </div>
            <ul className="zone-items" id="strongItems"></ul>
          </div>
          <div className="ai-zone improve">
            <div className="ai-zone-header">
              <span className="zone-icon">📈</span>
              <span>Can Improve</span>
              <span className="zone-count" id="improveCount">0</span>
            </div>
            <ul className="zone-items" id="improveItems"></ul>
          </div>
          <div className="ai-zone weak">
            <div className="ai-zone-header">
              <span className="zone-icon">⚠️</span>
              <span>Weak Areas</span>
              <span className="zone-count" id="weakCount">0</span>
            </div>
            <ul className="zone-items" id="weakItems"></ul>
          </div>
        </div>

        <div className="ai-recommendation-box" id="aiRecommendationBox">
          <div className="ai-rec-header">
            <span>🤖</span> AI Recommendation
          </div>
          <p id="aiRecommendationText"></p>
        </div>
      </div>

      
      <div className="section-card" id="collegeRecSection" style={{"marginTop":"20px","display":"none"}}>
        <div className="ai-block-header" style={{"paddingBottom":"12px","borderBottom":"1px solid var(--border)","display":"flex","alignItems":"center","justifyContent":"space-between","flexWrap":"wrap","gap":"12px"}}>
          <div style={{"display":"flex","alignItems":"center","gap":"12px"}}>
            <div className="ai-block-icon" style={{"fontSize":"1.5rem"}}>🎓</div>
            <div>
              <h2 style={{"fontSize":"1.2rem","fontWeight":"700","margin":"0"}}>College Match Predictor</h2>
              <p className="section-sub" style={{"margin":"2px 0 0 0"}} id="recSubtitle">Based on your average performance</p>
            </div>
          </div>
          <div className="ai-block-badge" id="predictedRankBadge" style={{"background":"var(--purple)","color":"white","fontWeight":"bold","fontSize":"0.8rem","padding":"4px 12px","borderRadius":"20px"}}>Projected Rank: Calculating...</div>
        </div>

        <div style={{"marginTop":"16px","display":"flex","justifyContent":"space-between","alignItems":"center","flexWrap":"wrap","gap":"12px"}}>
          
          <div style={{"display":"flex","gap":"8px"}} id="recTabs">
            <button className="nav-pill active" id="recTabTarget" >🎯 Target (<span id="targetCount">0</span>)</button>
            <button className="nav-pill" id="recTabReach" >🚀 Reach (<span id="reachCount">0</span>)</button>
            <button className="nav-pill" id="recTabSafe" >🛡️ Safe (<span id="safeCount">0</span>)</button>
          </div>
          
          <div className="results-search" style={{"margin":"0","maxWidth":"250px"}}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
            <input type="text" id="collegeSearchInput" className="search-input" placeholder="Search colleges..." />
          </div>
        </div>

        
        <div id="recLockOverlay" className="ai-recommendation-box" style={{"marginTop":"16px","background":"linear-gradient(135deg, rgba(124, 58, 237, 0.1) 0%, rgba(37, 99, 235, 0.1) 100%)","border":"1px dashed var(--purple)","textAlign":"center","padding":"24px","borderRadius":"var(--r)","display":"none"}}>
          <div style={{"fontSize":"2rem","marginBottom":"8px"}}>🔒</div>
          <h3 style={{"fontSize":"1.1rem","fontWeight":"700","color":"var(--text)","marginBottom":"8px"}}>Unlock Smart College Recommendations</h3>
          <p id="recLockText" style={{"fontSize":"0.85rem","color":"var(--muted)","maxWidth":"500px","margin":"0 auto 16px auto","lineHeight":"1.5"}}>
            Upgrade to the Pro Plan to unlock the full names, locations, and details of these matching colleges.
          </p>
          <a href="/subscription" className="btn-primary" style={{"display":"inline-block","padding":"8px 24px","fontSize":"0.85rem","textDecoration":"none"}}>Upgrade to Pro →</a>
        </div>

        <div id="collegesGrid" style={{"display":"grid","gridTemplateColumns":"repeat(auto-fit, minmax(280px, 1fr))","gap":"16px","marginTop":"16px"}}>
          
        </div>
      </div>

      
      <div className="section-card" id="rankSuggestionSection" style={{"marginTop":"20px"}}>
        <div className="ai-block-header">
            <div className="ai-block-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>
                </svg>
            </div>
            <div>
                <h2>Suggestions to Reach Desired Rank</h2>
                <p className="section-sub">Get personalized suggestions to achieve your goal</p>
            </div>
        </div>
        <div style={{"marginTop":"16px","display":"flex","gap":"16px","alignItems":"center"}}>
            <input type="number" id="desiredRankInput" className="select-input" placeholder="Enter desired rank (e.g., 1000)" />
            <button className="btn-primary" id="getRankSuggestionsBtn">Get Suggestions</button>
        </div>
        <div id="rankSuggestionsResult" style={{"marginTop":"16px"}}>
            
        </div>
      </div>

      
      <div className="section-card" id="rankBoosterSection" style={{"marginTop":"20px","display":"none"}}>
        <div className="ai-block-header">
          <div className="ai-block-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 15l-3 3h6l-3-3z"/><path d="M5 9l7-7 7 7"/><path d="M4 19h16"/>
            </svg>
          </div>
          <div>
            <h2>Rank Booster Action Plan</h2>
            <p className="section-sub">Personalized steps to improve your KCET rank — based on your actual scores</p>
          </div>
        </div>
        <div style={{"marginTop":"14px"}}>
          <div id="boosterMeta" style={{"fontSize":"0.85rem","color":"var(--muted2)","background":"var(--s2)","border":"1px solid var(--border)","borderRadius":"var(--rs)","padding":"10px 14px","marginBottom":"14px"}}></div>
          <ul id="boosterActionList" style={{"margin":"0","padding":"0 0 0 20px","fontSize":"0.88rem","color":"var(--text)","lineHeight":"2"}}></ul>
          <div id="boosterLockMsg" style={{"display":"none","marginTop":"10px","fontSize":"0.82rem","color":"var(--muted)","background":"rgba(124,58,237,0.07)","border":"1px solid rgba(124,58,237,0.2)","borderRadius":"var(--rs)","padding":"10px 14px"}}></div>
        </div>
      </div>

      
      <div className="section-card results-card" style={{"marginTop":"20px"}}>
        <div className="results-header">
          <h3>🏆 Top Students</h3>
        </div>
        <div className="chart-wrap" style={{"height":"280px","padding":"16px"}}>
          
        </div>
        <div className="table-scroll">
          <table className="results-table">
            <thead>
              <tr>
                <th>Rank</th>
                <th>Student</th>
                <th>KCET ID</th>
                <th>Score</th>
                <th>Progress</th>
              </tr>
            </thead>
            <tbody>
              {data && data.topStudents.map((s) => (
                <tr key={s.rank}>
                  <td><strong>#{s.rank}</strong></td>
                  <td>{s.name}</td>
                  <td style={{ color: 'var(--purple-l)' }}>{s.id}</td>
                  <td>{s.score}%</td>
                  <td style={{ color: s.progress.startsWith('+') ? 'var(--green-l)' : 'var(--red-l)' }}>{s.progress}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      
      <div className="section-card results-card">
        <div className="results-header">
          <h3>Exam History</h3>
          <div className="results-search">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
            <input type="text" id="searchInput" className="search-input" placeholder="Search subject or set..." />
          </div>
        </div>
        <div className="table-scroll">
          <table className="results-table">
            <thead>
              <tr>
                <th >Subject <span className="sort-icon">↕</span></th>
                <th >Set <span className="sort-icon">↕</span></th>
                <th >Score <span className="sort-icon">↕</span></th>
                <th >Time <span className="sort-icon">↕</span></th>
                <th >Status <span className="sort-icon">↕</span></th>
                <th >Date <span className="sort-icon">↕</span></th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {data && data.examHistory.map((h, i) => (
                <tr key={i}>
                  <td><strong>{h.subject}</strong></td>
                  <td>{h.set}</td>
                  <td>{h.score}</td>
                  <td>{h.time}</td>
                  <td>
                    <span style={{ 
                      padding: '4px 8px', borderRadius: '4px', fontSize: '0.8rem',
                      background: h.status === 'Pass' ? 'rgba(16,185,129,0.1)' : 'rgba(239,68,68,0.1)',
                      color: h.status === 'Pass' ? 'var(--green-l)' : 'var(--red-l)'
                    }}>
                      {h.status}
                    </span>
                  </td>
                  <td>{h.date}</td>
                  <td><button className="btn-outline" style={{ padding: '4px 12px', fontSize: '0.8rem' }}>View</button></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="table-footer" id="tableFooter"></div>
      </div>
    </div>
  </main>
    </>
  );
};

export default Dashboard;
