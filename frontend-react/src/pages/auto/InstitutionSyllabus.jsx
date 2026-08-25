import React from 'react';
import { Link } from 'react-router-dom';

const InstitutionSyllabus = () => {
  return (
    <>
      {/* Auto-injected styles from HTML head */}
      <style dangerouslySetInnerHTML={{ __html: `
    .chapter-card { background:var(--s2);border:1px solid var(--border);border-radius:var(--rs);padding:12px 16px;display:flex;align-items:flex-start;gap:10px; }
    .ch-num { min-width:28px;height:28px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:0.72rem;font-weight:700;flex-shrink:0; }
    .ch-body { flex:1; }
    .ch-name { font-size:0.88rem;font-weight:600;color:var(--text); }
    .ch-desc { font-size:0.77rem;color:var(--muted);margin-top:3px;line-height:1.4; }
    .puc-header { font-size:0.72rem;text-transform:uppercase;letter-spacing:0.6px;color:var(--muted);font-weight:700;margin:16px 0 8px; }
    .subject-tab { padding:8px 16px;border-radius:var(--rs);cursor:pointer;font-size:0.85rem;font-weight:600;border:1px solid var(--border);color:var(--muted2);background:var(--s2);transition:all 0.15s; }
    .subject-tab.active { background:var(--purple-l,#a78bfa);color:#fff;border-color:var(--purple-l,#a78bfa); }
  
` }} />
      
  <div className="bg-mesh"></div>

  
  

  <main className="main-wrap">
    <div className="section-card">
      <div className="section-card-header">
        <div className="section-icon" style={{"background":"linear-gradient(135deg,rgba(124,58,237,0.2),rgba(37,99,235,0.2))"}}>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M4 19.5A2.5 2.5 0 016.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 014 19.5v-15A2.5 2.5 0 016.5 2z"/></svg>
        </div>
        <div>
          <h2>KCET Syllabus</h2>
          <p className="section-sub">Official Karnataka PUC syllabus — 1st &amp; 2nd PUC chapters for all subjects · Source: KEA / DPUE Karnataka</p>
        </div>
      </div>
      <div className="section-body">
        
        <div style={{"display":"flex","gap":"8px","flexWrap":"wrap","marginBottom":"20px"}}>
          <button className="subject-tab active" data-subject="Physics">⚡ Physics</button>
          <button className="subject-tab" data-subject="Chemistry">🧪 Chemistry</button>
          <button className="subject-tab" data-subject="Mathematics">📐 Mathematics</button>
          <button className="subject-tab" data-subject="Biology">🌱 Biology</button>
        </div>

        <div id="syllabusContent">
          <div style={{"textAlign":"center","color":"var(--muted)","padding":"40px"}}>Loading syllabus…</div>
        </div>
      </div>
    </div>
  </main>

  
  

    </>
  );
};

export default InstitutionSyllabus;
