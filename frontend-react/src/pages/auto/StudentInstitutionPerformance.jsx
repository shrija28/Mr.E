import React from 'react';
import { Link } from 'react-router-dom';

const StudentInstitutionPerformance = () => {
  return (
    <>
      {/* Auto-injected styles from HTML head */}
      <style dangerouslySetInnerHTML={{ __html: `` }} />
      
  <div className="bg-mesh"></div>
  

  <main className="dash-main">
    <div className="dash-hero">
      <div>
        <h1 className="dash-title">My <span className="hero-gradient">Performance</span></h1>
        <p className="dash-sub">Detailed analytics for all your exam submissions</p>
      </div>
    </div>

    
    <div className="kpi-row" style={{"gridTemplateColumns":"repeat(3,1fr)","marginBottom":"24px"}}>
      <div className="kpi-tile">
        <div className="kpi-tile-icon purple"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M9 11l3 3L22 4"/></svg></div>
        <div className="kpi-tile-body"><div className="kpi-tile-val" id="kpiTotal">0</div><div className="kpi-tile-label">Total Exams</div></div>
      </div>
      <div className="kpi-tile">
        <div className="kpi-tile-icon cyan"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="8" r="6"/></svg></div>
        <div className="kpi-tile-body"><div className="kpi-tile-val" id="kpiAvg">0%</div><div className="kpi-tile-label">Avg Score</div></div>
      </div>
      <div className="kpi-tile">
        <div className="kpi-tile-icon green"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg></div>
        <div className="kpi-tile-body"><div className="kpi-tile-val" id="kpiPass">0%</div><div className="kpi-tile-label">Pass Rate</div></div>
      </div>
    </div>

    
    <div className="section-card" style={{"marginBottom":"20px"}}>
      <div className="section-card-header">
        <div className="section-icon purple"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg></div>
        <div><h2 style={{"marginBottom":"2px"}}>Score Trend</h2><p className="section-sub">Your recent exam scores</p></div>
      </div>
      <div className="chart-wrap" style={{"height":"200px","padding":"16px 20px","display":"none"}} id="trendChartWrap"><canvas id="trendChart"></canvas></div>
    </div>

    
    <div className="section-card" id="subjectChartCard" style={{"marginBottom":"20px","display":"none"}}>
      <div className="section-card-header">
        <div className="section-icon purple"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="3" y="3" width="18" height="18" rx="2"/><line x1="3" y1="9" x2="21" y2="9"/><line x1="9" y1="21" x2="9" y2="9"/></svg></div>
        <div><h2 style={{"marginBottom":"2px"}}>Subject Performance</h2><p className="section-sub">Average score per subject</p></div>
      </div>
      <div className="chart-wrap" style={{"height":"200px","padding":"16px 20px"}}><canvas id="subjectChart"></canvas></div>
    </div>

    
    <div className="section-card" id="aiGuidanceCard" style={{"marginBottom":"20px","display":"none"}}>
      <div className="section-card-header">
        <div className="section-icon purple"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg></div>
        <div><h2 style={{"marginBottom":"2px"}}>AI Performance Analysis</h2><p className="section-sub">Smart insights based on your exam results</p></div>
      </div>
      <div className="section-body" style={{"padding":"16px 20px"}}>
        <div style={{"display":"grid","gridTemplateColumns":"repeat(auto-fit,minmax(160px,1fr))","gap":"12px","marginBottom":"16px"}}>
          <div style={{"background":"rgba(5,150,105,0.08)","border":"1px solid rgba(5,150,105,0.2)","borderRadius":"var(--rs)","padding":"12px"}}>
            <div style={{"fontSize":"0.7rem","fontWeight":"700","color":"var(--green-l)","textTransform":"uppercase","letterSpacing":".05em","marginBottom":"6px"}}>✅ Strong</div>
            <ul id="perfStrongList" style={{"margin":"0","padding":"0","listStyle":"none","fontSize":"0.82rem"}}></ul>
          </div>
          <div style={{"background":"rgba(217,119,6,0.08)","border":"1px solid rgba(217,119,6,0.2)","borderRadius":"var(--rs)","padding":"12px"}}>
            <div style={{"fontSize":"0.7rem","fontWeight":"700","color":"var(--yellow-l,#fbbf24)","textTransform":"uppercase","letterSpacing":".05em","marginBottom":"6px"}}>📈 Can Improve</div>
            <ul id="perfImproveList" style={{"margin":"0","padding":"0","listStyle":"none","fontSize":"0.82rem"}}></ul>
          </div>
          <div style={{"background":"rgba(220,38,38,0.08)","border":"1px solid rgba(220,38,38,0.2)","borderRadius":"var(--rs)","padding":"12px"}}>
            <div style={{"fontSize":"0.7rem","fontWeight":"700","color":"var(--red-l,#f87171)","textTransform":"uppercase","letterSpacing":".05em","marginBottom":"6px"}}>⚠️ Needs Focus</div>
            <ul id="perfWeakList" style={{"margin":"0","padding":"0","listStyle":"none","fontSize":"0.82rem"}}></ul>
          </div>
        </div>
        <div id="perfAIRec" style={{"fontSize":"0.84rem","color":"var(--muted2)","background":"var(--s2)","border":"1px solid var(--border)","borderRadius":"var(--rs)","padding":"12px","lineHeight":"1.6"}}></div>
      </div>
    </div>

    
    <div className="section-card" id="rankBoosterCard" style={{"marginBottom":"20px","display":"none"}}>
      <div className="section-card-header">
        <div className="section-icon cyan"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 15l-3 3h6l-3-3z"/><path d="M5 9l7-7 7 7"/><path d="M4 19h16"/></svg></div>
        <div><h2 style={{"marginBottom":"2px"}}>Rank Predictor & Study Plan</h2><p className="section-sub">Your projected KCET rank and personalized action plan</p></div>
      </div>
      <div className="section-body" style={{"padding":"16px 20px"}}>
        <div id="boosterContent" style={{"fontSize":"0.84rem","color":"var(--muted2)","marginBottom":"16px"}}></div>
        <div style={{"background":"var(--s2)","border":"1px solid var(--border)","borderRadius":"var(--rs)","padding":"14px"}}>
          <div style={{"fontSize":"0.82rem","fontWeight":"700","color":"var(--muted2)","marginBottom":"10px"}}>🎯 Get Suggestions for a Specific Rank</div>
          <div style={{"display":"flex","gap":"8px","alignItems":"center","flexWrap":"wrap"}}>
            <input type="number" id="perfDesiredRank" className="text-input" placeholder="Enter desired rank e.g. 5000" min="1" style={{"flex":"1","minWidth":"180px","maxWidth":"260px","padding":"8px 12px","fontSize":"0.85rem"}}/>
            <button className="btn-primary small" id="perfGetSuggestionsBtn">Get Suggestions</button>
          </div>
          <div id="perfSuggestionsResult" style={{"marginTop":"12px","display":"none"}}></div>
        </div>
      </div>
    </div>

    
    <div className="section-card" id="perfCollegeRecSection" style={{"marginBottom":"20px","display":"none"}}>
      <div className="section-card-header">
        <div className="section-icon" style={{"background":"rgba(37,99,235,0.15)","fontSize":"1.2rem"}}>🎓</div>
        <div>
          <h2 style={{"marginBottom":"2px"}}>College Match Predictor</h2>
          <p className="section-sub" id="perfRecSubtitle">Based on your average performance</p>
        </div>
        <span className="inst-exam-tag platform" id="perfRankBadge" style={{"marginLeft":"auto","fontWeight":"700","fontSize":"0.8rem","padding":"4px 12px","borderRadius":"20px"}}>Calculating…</span>
      </div>
      <div className="section-body" style={{"padding":"16px 20px"}}>
        <div style={{"display":"flex","gap":"8px","flexWrap":"wrap","marginBottom":"14px"}}>
          <button className="nav-pill active" id="perfTabTarget" >🎯 Target (<span id="perfTargetCount">0</span>)</button>
          <button className="nav-pill" id="perfTabReach" >🚀 Reach (<span id="perfReachCount">0</span>)</button>
          <button className="nav-pill" id="perfTabSafe" >🛡️ Safe (<span id="perfSafeCount">0</span>)</button>
        </div>
        <div id="perfCollegesGrid" style={{"display":"grid","gridTemplateColumns":"repeat(auto-fit,minmax(260px,1fr))","gap":"14px"}}></div>
      </div>
    </div>

    
    <div className="section-card results-card">
      <div className="results-header"><h3>Exam History</h3></div>
      <div className="table-scroll">
        <table className="results-table">
          <thead><tr>
            <th>Subject</th><th>Set</th><th>Score</th><th>Time</th><th>Status</th><th>Date</th>
          </tr></thead>
          <tbody id="histBody">
            <tr><td colspan="6" style={{"textAlign":"center","padding":"24px","color":"var(--muted)"}}>Loading…</td></tr>
          </tbody>
        </table>
      </div>
    </div>
  </main>

  
  
  

    </>
  );
};

export default StudentInstitutionPerformance;
