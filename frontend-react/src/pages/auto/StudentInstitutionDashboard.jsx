import React from 'react';
import { Link } from 'react-router-dom';

const StudentInstitutionDashboard = () => {
  return (
    <>
      {/* Auto-injected styles from HTML head */}
      <style dangerouslySetInnerHTML={{ __html: `
    /* ── Institution-specific overrides (built on top of style.css) ────── */

    /* Institution access banner */
    .inst-access-bar {
      position: relative; z-index: 1;
      background: linear-gradient(90deg, rgba(37,99,235,0.14), rgba(124,58,237,0.14));
      border-bottom: 1px solid rgba(124,58,237,0.22);
      padding: 9px 28px;
      display: flex; align-items: center; gap: 14px; flex-wrap: wrap;
    }
    .inst-label-badge {
      display: inline-flex; align-items: center; gap: 6px;
      background: rgba(124,58,237,0.15);
      border: 1px solid rgba(124,58,237,0.3);
      border-radius: 20px; padding: 3px 12px;
      font-size: 0.72rem; font-weight: 700;
      color: var(--purple-l); letter-spacing: 0.06em; text-transform: uppercase;
    }
    .inst-name-label { font-size: 0.9rem; font-weight: 700; color: var(--text); }
    .inst-access-status {
      margin-left: auto; display: inline-flex; align-items: center; gap: 5px;
      border-radius: 20px; padding: 3px 12px;
      font-size: 0.72rem; font-weight: 700;
    }
    .inst-access-status.active  { background: rgba(5,150,105,0.14); border: 1px solid rgba(5,150,105,0.3); color: var(--green-l); }
    .inst-access-status.inactive{ background: rgba(220,38,38,0.12);  border: 1px solid rgba(220,38,38,0.3);  color: var(--red-l); }

    /* Profile cards grid */
    .profile-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 14px; margin-bottom: 24px;
    }
    .profile-card {
      background: var(--s1); border: 1px solid var(--border);
      border-radius: var(--r); padding: 16px 18px;
    }
    .profile-card-label {
      font-size: 0.68rem; text-transform: uppercase; letter-spacing: 0.07em;
      color: var(--muted); margin-bottom: 5px; font-weight: 700;
    }
    .profile-card-val {
      font-size: 0.95rem; font-weight: 700; color: var(--text);
      word-break: break-word;
    }
    .profile-card-val.mono { font-family: 'Cascadia Code', monospace; color: var(--purple-l); }

    /* 4-column KPI row for this dashboard */
    .inst-kpi-row {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 14px; margin-bottom: 24px;
    }
    @media(max-width: 800px) { .inst-kpi-row { grid-template-columns: repeat(2,1fr); } }
    @media(max-width: 480px) { .inst-kpi-row { grid-template-columns: 1fr; } }

    /* Section grid (2 cols) */
    .inst-section-grid {
      display: grid; grid-template-columns: 1fr 1fr; gap: 20px;
    }
    @media(max-width: 880px) { .inst-section-grid { grid-template-columns: 1fr; } }

    /* Section header icon — constrained size */
    .inst-sec-icon {
      width: 30px; height: 30px; border-radius: 8px;
      display: flex; align-items: center; justify-content: center;
      flex-shrink: 0; font-size: 1rem;
    }

    /* Exam list inside sections */
    .inst-exam-list { list-style: none; padding: 0; margin: 0; }
    .inst-exam-row {
      display: flex; align-items: center; gap: 10px;
      padding: 10px 0; border-bottom: 1px solid rgba(255,255,255,0.04);
    }
    .inst-exam-row:last-child { border-bottom: none; }
    .inst-exam-subject { flex: 1; font-size: 0.85rem; font-weight: 600; }
    .inst-exam-tag {
      font-size: 0.68rem; font-weight: 700; padding: 2px 8px;
      border-radius: 8px; white-space: nowrap;
    }
    .inst-exam-tag.platform    { background: rgba(8,145,178,0.12); border: 1px solid rgba(8,145,178,0.25); color: var(--cyan-l); }
    .inst-exam-tag.institution { background: rgba(124,58,237,0.12); border: 1px solid rgba(124,58,237,0.25); color: var(--purple-l); }
    .inst-exam-sets { font-size: 0.68rem; color: var(--muted); }
    .inst-start-btn {
      font-size: 0.72rem; padding: 4px 10px; border-radius: 6px;
      background: rgba(124,58,237,0.12); border: 1px solid rgba(124,58,237,0.3);
      color: var(--purple-l); cursor: pointer; text-decoration: none;
      transition: background 0.15s; white-space: nowrap;
    }
    .inst-start-btn:hover { background: rgba(124,58,237,0.22); }

    /* Leaderboard table */
    .inst-lb-table { width: 100%; border-collapse: collapse; font-size: 0.82rem; }
    .inst-lb-table th {
      text-align: left; padding: 8px 12px; font-size: 0.68rem;
      text-transform: uppercase; letter-spacing: 0.05em;
      color: var(--muted); border-bottom: 1px solid var(--border); font-weight: 700;
    }
    .inst-lb-table td { padding: 10px 12px; border-bottom: 1px solid rgba(255,255,255,0.03); }
    .inst-lb-table tr:last-child td { border-bottom: none; }
    .inst-lb-table tr.mine { background: rgba(124,58,237,0.07); }
    .lb-rank { text-align: center; font-size: 1rem; }
    .lb-name { font-weight: 600; }
    .lb-id   { font-size: 0.72rem; color: var(--muted); font-family: monospace; }
    .lb-you  { font-size: 0.68rem; color: var(--purple-l); margin-left: 4px; }

    /* Empty state for sections */
    .inst-empty { text-align: center; padding: 28px 16px; color: var(--muted); font-size: 0.83rem; }

    /* Quick-action buttons full width */
    .qa-btn {
      display: flex; align-items: center; justify-content: center; gap: 8px;
      width: 100%; padding: 10px 16px; border-radius: var(--rs);
      font-size: 0.85rem; font-weight: 600; cursor: pointer;
      text-decoration: none; transition: all 0.18s;
    }
    .qa-btn svg { width: 15px; height: 15px; flex-shrink: 0; }
    .qa-btn.primary { background: linear-gradient(135deg, var(--purple), var(--blue)); border: none; color: white; box-shadow: 0 2px 12px rgba(124,58,237,0.3); }
    .qa-btn.primary:hover { transform: translateY(-1px); box-shadow: 0 4px 18px rgba(124,58,237,0.45); }
    .qa-btn.outline { background: transparent; border: 1px solid var(--border2); color: var(--text); }
    .qa-btn.outline:hover { border-color: rgba(124,58,237,0.4); background: rgba(124,58,237,0.06); }
  
` }} />
      
  <div className="bg-mesh"></div>

  
  

  
  <div className="inst-access-bar" id="accessBar">
    <span className="inst-label-badge">🏫 Institution Student</span>
    <span className="inst-name-label" id="instName">Loading…</span>
    <span className="inst-access-status inactive" id="accessStatus">Checking…</span>
  </div>

  <main className="dash-main">

    
    <div className="dash-hero">
      <div>
        <h1 className="dash-title">Institution <span className="hero-gradient">Dashboard</span></h1>
        <p className="dash-sub" id="dashSub">Your institution exam platform</p>
      </div>
      <div className="dash-hero-right">
        <div className="last-updated" id="lastUpdated">Last updated: —</div>
        <button className="btn-outline" >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{"width":"14px","height":"14px"}}><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 11-2.12-9.36L23 10"/></svg>
          Refresh
        </button>
      </div>
    </div>

    
    <div id="stateLoading" style={{"textAlign":"center","padding":"60px 20px","color":"var(--muted)"}}>
      <div style={{"fontSize":"1.8rem","marginBottom":"10px"}}>⏳</div>
      <p>Loading your dashboard…</p>
    </div>
    <div id="stateError" style={{"display":"none","textAlign":"center","padding":"60px 20px","color":"var(--muted)"}}>
      <div style={{"fontSize":"1.8rem","marginBottom":"10px"}}>⚠️</div>
      <p id="errMsg">Could not load profile. Please refresh.</p>
    </div>

    
    <div id="mainContent" style={{"display":"none"}}>

      
      <div className="profile-grid" id="profileGrid"></div>

      
      <div className="inst-kpi-row">
        <div className="kpi-tile">
          <div className="kpi-tile-icon purple">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11"/></svg>
          </div>
          <div className="kpi-tile-body">
            <div className="kpi-tile-val" id="kpiExams">0</div>
            <div className="kpi-tile-label">Exams Taken</div>
          </div>
        </div>
        <div className="kpi-tile">
          <div className="kpi-tile-icon cyan">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="8" r="6"/><path d="M15.477 12.89L17 22l-5-3-5 3 1.523-9.11"/></svg>
          </div>
          <div className="kpi-tile-body">
            <div className="kpi-tile-val" id="kpiAvg">0%</div>
            <div className="kpi-tile-label">Avg Score</div>
          </div>
        </div>
        <div className="kpi-tile">
          <div className="kpi-tile-icon green">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>
          </div>
          <div className="kpi-tile-body">
            <div className="kpi-tile-val" id="kpiPass">0%</div>
            <div className="kpi-tile-label">Pass Rate</div>
          </div>
        </div>
        <div className="kpi-tile">
          <div className="kpi-tile-icon orange">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 15l-3 3h6l-3-3z"/><path d="M5 9l7-7 7 7"/><path d="M4 19h16"/></svg>
          </div>
          <div className="kpi-tile-body">
            <div className="kpi-tile-val" id="kpiRank">—</div>
            <div className="kpi-tile-label">Institution Rank</div>
          </div>
        </div>
      </div>

      
      <div className="section-card" id="collegeRecSection" style={{"marginBottom":"24px","display":"none"}}>
        <div className="ai-block-header" style={{"paddingBottom":"12px","borderBottom":"1px solid var(--border)","display":"flex","alignItems":"center","justifyContent":"space-between","flexWrap":"wrap","gap":"12px","marginBottom":"16px"}}>
          <div style={{"display":"flex","alignItems":"center","gap":"12px"}}>
            <div style={{"fontSize":"1.5rem"}}>🎓</div>
            <div>
              <h2 style={{"fontSize":"1rem","fontWeight":"700","margin":"0"}}>College Match Predictor</h2>
              <p className="section-sub" style={{"margin":"2px 0 0 0"}} id="recSubtitle">Based on your average performance</p>
            </div>
          </div>
          <div className="inst-exam-tag platform" id="predictedRankBadge" style={{"fontWeight":"bold","fontSize":"0.8rem","padding":"4px 12px","borderRadius":"20px","textTransform":"none"}}>Projected Rank: Calculating...</div>
        </div>

        <div style={{"display":"flex","justifyContent":"space-between","alignItems":"center","flexWrap":"wrap","gap":"12px","marginBottom":"16px"}}>
          
          <div style={{"display":"flex","gap":"8px"}} id="recTabs">
            <button className="nav-pill active" id="recTabTarget" >🎯 Target (<span id="targetCount">0</span>)</button>
            <button className="nav-pill" id="recTabReach" >🚀 Reach (<span id="reachCount">0</span>)</button>
            <button className="nav-pill" id="recTabSafe" >🛡️ Safe (<span id="safeCount">0</span>)</button>
          </div>
          
          <div className="results-search" style={{"margin":"0","maxWidth":"250px"}}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
            <input type="text" id="collegeSearchInput" className="search-input" placeholder="Search colleges..." />
          </div>
        </div>

        <div id="collegesGrid" style={{"display":"grid","gridTemplateColumns":"repeat(auto-fit, minmax(280px, 1fr))","gap":"16px"}}>
          
        </div>
      </div>

      
      <div className="section-card" id="aiGuidanceSection" style={{"marginBottom":"24px","display":"none"}}>
        <div className="section-card-header">
          <div className="inst-sec-icon" style={{"background":"rgba(124,58,237,0.18)","fontSize":"1.3rem"}}>🤖</div>
          <div>
            <h2 style={{"fontSize":"0.97rem","marginBottom":"2px"}}>Personalized AI Guidance</h2>
            <p className="section-sub">Smart recommendations based on your scores</p>
          </div>
        </div>
        <div className="section-body" style={{"padding":"16px 20px"}}>

          
          <div style={{"display":"grid","gridTemplateColumns":"repeat(auto-fit,minmax(170px,1fr))","gap":"12px","marginBottom":"20px"}}>
            <div style={{"background":"rgba(5,150,105,0.08)","border":"1px solid rgba(5,150,105,0.2)","borderRadius":"var(--rs)","padding":"12px"}}>
              <div style={{"fontSize":"0.72rem","fontWeight":"700","color":"var(--green-l)","textTransform":"uppercase","letterSpacing":".05em","marginBottom":"6px"}}>✅ Strong</div>
              <ul id="instStrongList" style={{"margin":"0","padding":"0","listStyle":"none","fontSize":"0.82rem","color":"var(--text)"}}></ul>
            </div>
            <div style={{"background":"rgba(217,119,6,0.08)","border":"1px solid rgba(217,119,6,0.2)","borderRadius":"var(--rs)","padding":"12px"}}>
              <div style={{"fontSize":"0.72rem","fontWeight":"700","color":"var(--yellow-l,#fbbf24)","textTransform":"uppercase","letterSpacing":".05em","marginBottom":"6px"}}>📈 Can Improve</div>
              <ul id="instImproveList" style={{"margin":"0","padding":"0","listStyle":"none","fontSize":"0.82rem","color":"var(--text)"}}></ul>
            </div>
            <div style={{"background":"rgba(220,38,38,0.08)","border":"1px solid rgba(220,38,38,0.2)","borderRadius":"var(--rs)","padding":"12px"}}>
              <div style={{"fontSize":"0.72rem","fontWeight":"700","color":"var(--red-l,#f87171)","textTransform":"uppercase","letterSpacing":".05em","marginBottom":"6px"}}>⚠️ Needs Focus</div>
              <ul id="instWeakList" style={{"margin":"0","padding":"0","listStyle":"none","fontSize":"0.82rem","color":"var(--text)"}}></ul>
            </div>
          </div>

          
          <div id="boosterBlock" style={{"display":"none","marginBottom":"20px"}}>
            <div style={{"fontSize":"0.82rem","fontWeight":"700","color":"var(--muted2)","marginBottom":"8px"}}>🚀 Rank Booster Action Plan</div>
            <div id="boosterMeta" style={{"fontSize":"0.8rem","color":"var(--muted)","marginBottom":"10px"}}></div>
            <ul id="boosterList" style={{"margin":"0","padding":"0 0 0 18px","fontSize":"0.84rem","color":"var(--text)","lineHeight":"1.8"}}></ul>
          </div>

          
          <div style={{"background":"var(--s2)","border":"1px solid var(--border)","borderRadius":"var(--rs)","padding":"14px"}}>
            <div style={{"fontSize":"0.82rem","fontWeight":"700","color":"var(--muted2)","marginBottom":"10px"}}>🎯 Suggestions to Reach a Specific Rank</div>
            <div style={{"display":"flex","gap":"8px","alignItems":"center","flexWrap":"wrap"}}>
              <input type="number" id="instDesiredRank" className="text-input" placeholder="Enter desired rank e.g. 5000" min="1" style={{"flex":"1","minWidth":"180px","maxWidth":"260px","padding":"8px 12px","fontSize":"0.85rem"}}/>
              <button className="btn-primary small" id="instGetSuggestionsBtn">Get Suggestions</button>
            </div>
            <div id="instSuggestionsResult" style={{"marginTop":"12px","display":"none"}}></div>
          </div>

        </div>
      </div>

      
      <div className="inst-section-grid">

        
        <div className="section-card">
          <div className="section-card-header">
            <div className="inst-sec-icon" style={{"background":"rgba(124,58,237,0.15)"}}>📚</div>
            <div>
              <h2 style={{"fontSize":"0.88rem","marginBottom":"2px"}}>Available Exams</h2>
              <p className="section-sub">Institution &amp; platform exams</p>
            </div>
            <span id="examCountBadge" style={{"marginLeft":"auto","fontSize":"0.72rem","color":"var(--muted)","background":"var(--s3)","borderRadius":"10px","padding":"2px 8px","marginRight":"8px"}}>
              {JSON.parse(localStorage.getItem('mockAdminExams') || '[]').filter(e => e.status === 'Active').length}
            </span>
            <Link to="/student/institution/exams" style={{"fontSize":"0.72rem","color":"var(--purple-l)","textDecoration":"none"}}>View all →</Link>
          </div>
          <div className="section-body" style={{"padding":"16px 20px"}}>
            <ul className="inst-exam-list" id="examList">
              {(() => {
                const exams = JSON.parse(localStorage.getItem('mockAdminExams') || '[]').filter(e => e.status === 'Active');
                if (exams.length === 0) {
                  return <li className="inst-empty">No exams available yet.</li>;
                }
                return exams.map((exam, i) => (
                  <li key={i} className="inst-exam-row">
                    <div style={{ flex: 1 }}>
                      <div className="inst-exam-subject">{exam.name}</div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--muted)' }}>{exam.subject} • {exam.sets} Sets</div>
                    </div>
                    <Link to={`/exam?subject=${exam.subject}&name=${encodeURIComponent(exam.name)}`} className="inst-start-btn">Take Exam</Link>
                  </li>
                ));
              })()}
            </ul>
          </div>
        </div>

        
        <div className="section-card">
          <div className="section-card-header">
            <div className="inst-sec-icon" style={{"background":"rgba(217,119,6,0.15)"}}>🏆</div>
            <div>
              <h2 style={{"fontSize":"0.88rem","marginBottom":"2px"}}>Institution Leaderboard</h2>
              <p className="section-sub">Top performers in your institution</p>
            </div>
            <Link to="/student/institution/leaderboard" style={{"marginLeft":"auto","fontSize":"0.72rem","color":"var(--purple-l)","textDecoration":"none"}}>View all →</Link>
          </div>
          <div className="section-body" style={{"padding":"0"}}>
            <table className="inst-lb-table">
              <thead><tr>
                <th style={{"width":"42px"}}>Rank</th>
                <th>Student</th>
                <th>Avg</th>
                <th>Exams</th>
              </tr></thead>
              <tbody id="lbBody">
                <tr><td colspan="4" className="inst-empty">Loading…</td></tr>
              </tbody>
            </table>
          </div>
        </div>

        
        <div className="section-card">
          <div className="section-card-header">
            <div className="inst-sec-icon" style={{"background":"rgba(5,150,105,0.15)"}}>📈</div>
            <div>
              <h2 style={{"fontSize":"0.88rem","marginBottom":"2px"}}>My Performance</h2>
              <p className="section-sub">Recent exam results</p>
            </div>
            <Link to="/student/institution/performance" style={{"marginLeft":"auto","fontSize":"0.72rem","color":"var(--purple-l)","textDecoration":"none"}}>Full history →</Link>
          </div>
          <div className="section-body" style={{"padding":"0","maxHeight":"300px","overflowY":"auto"}}>
            <table className="results-table">
              <thead><tr>
                <th>Subject</th><th>Set</th><th>Score</th><th>Status</th>
              </tr></thead>
              <tbody id="perfBody">
                <tr><td colspan="4" style={{"textAlign":"center","padding":"20px","color":"var(--muted)"}}>Loading…</td></tr>
              </tbody>
            </table>
          </div>
        </div>

        
        <div className="section-card">
          <div className="section-card-header">
            <div className="inst-sec-icon" style={{"background":"rgba(37,99,235,0.15)"}}>⚡</div>
            <div>
              <h2 style={{"fontSize":"0.88rem","marginBottom":"2px"}}>Quick Actions</h2>
              <p className="section-sub">Jump to key features</p>
            </div>
          </div>
          <div className="section-body" style={{"display":"flex","flexDirection":"column","gap":"10px"}}>
            <Link to="/student/institution/exams" className="qa-btn primary">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11"/></svg>
              View My Exams
            </Link>
            <Link to="/student/institution/performance" className="qa-btn outline">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>
              Full Analytics
            </Link>
            <Link to="/student/institution/leaderboard" className="qa-btn outline">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 15l-3 3h6l-3-3z"/><path d="M5 9l7-7 7 7"/></svg>
              Institution Rankings
            </Link>
            <Link to="/syllabus" className="qa-btn outline">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z"/></svg>
              KCET Syllabus
            </Link>
          </div>
        </div>

      </div>
    </div>
  </main>

  
  
  

    </>
  );
};

export default StudentInstitutionDashboard;
