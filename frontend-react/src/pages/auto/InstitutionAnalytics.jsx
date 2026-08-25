import React from 'react';
import { Link } from 'react-router-dom';

const InstitutionAnalytics = () => {
  return (
    <>
      {/* Auto-injected styles from HTML head */}
      <style dangerouslySetInnerHTML={{ __html: `` }} />
      
  <div className="bg-mesh"></div>

  
  

  
  <div className="main-wrap">

    
    <div className="section-card">
      <div className="section-card-header">
        <div className="section-icon" style={{"background":"linear-gradient(135deg,rgba(124,58,237,0.2),rgba(37,99,235,0.2))"}}>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>
        </div>
        <div>
          <h2>Performance Overview</h2>
          <p className="section-sub">Aggregated analytics for your institution's students</p>
        </div>
      </div>
      <div className="section-body">
        <div id="summaryStats" style={{"display":"grid","gridTemplateColumns":"repeat(auto-fit,minmax(180px,1fr))","gap":"16px"}}>
          <div style={{"textAlign":"center","color":"var(--muted)","padding":"32px"}}>Loading analytics…</div>
        </div>
      </div>
    </div>

    
    <div className="section-card">
      <div className="section-card-header">
        <div className="section-icon" style={{"background":"linear-gradient(135deg,rgba(8,145,178,0.2),rgba(5,150,105,0.2))"}}>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
        </div>
        <div>
          <h2>Student Leaderboard</h2>
          <p className="section-sub" id="studentCount">Loading students…</p>
        </div>
      </div>
      <div className="section-body" style={{"padding":"0"}}>
        <div className="table-scroll">
          <table className="results-table">
            <thead>
              <tr>
                <th>Rank</th>
                <th>Student</th>
                <th>Email</th>
                <th>Attempts</th>
                <th>Avg Score</th>
              </tr>
            </thead>
            <tbody id="leaderboardBody">
              <tr><td colspan="5" style={{"textAlign":"center","color":"var(--muted)","padding":"32px"}}>Loading…</td></tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

  </div>

  
  
  
  

    </>
  );
};

export default InstitutionAnalytics;
