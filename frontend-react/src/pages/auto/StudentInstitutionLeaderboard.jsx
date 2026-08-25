import React from 'react';
import { Link } from 'react-router-dom';

const StudentInstitutionLeaderboard = () => {
  return (
    <>
      {/* Auto-injected styles from HTML head */}
      <style dangerouslySetInnerHTML={{ __html: `` }} />
      
  <div className="bg-mesh"></div>
  

  <main className="dash-main">
    <div className="dash-hero">
      <div>
        <h1 className="dash-title">Institution <span className="hero-gradient">Leaderboard</span></h1>
        <p className="dash-sub" id="lbSub">Top performers in your institution</p>
      </div>
      <div className="dash-hero-right">
        <div id="myRankBadge" style={{"background":"rgba(124,58,237,0.12)","border":"1px solid rgba(124,58,237,0.3)","borderRadius":"20px","padding":"6px 16px","fontSize":"0.82rem","color":"var(--purple-l)"}}>Your rank: —</div>
      </div>
    </div>

    <div className="section-card results-card">
      <div className="results-header"><h3>🏆 Institution Rankings</h3></div>
      <div className="table-scroll">
        <table className="results-table">
          <thead><tr>
            <th style={{"width":"56px"}}>Rank</th>
            <th>Student</th>
            <th>Student ID</th>
            <th>Avg Score</th>
            <th>Exams</th>
          </tr></thead>
          <tbody id="lbBody">
            <tr><td colspan="5" style={{"textAlign":"center","padding":"32px","color":"var(--muted)"}}>Loading leaderboard…</td></tr>
          </tbody>
        </table>
      </div>
    </div>
  </main>

  
  

    </>
  );
};

export default StudentInstitutionLeaderboard;
