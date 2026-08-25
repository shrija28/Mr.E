import React from 'react';
import { Link } from 'react-router-dom';

const Syllabus = () => {
  return (
    <>
      {/* Auto-injected styles from HTML head */}
      <style dangerouslySetInnerHTML={{ __html: `
    .subject-tab { padding:10px 20px;border-radius:var(--rs);cursor:pointer;font-size:0.88rem;font-weight:600;border:1px solid var(--border);color:var(--muted2);background:var(--s2);transition:all 0.15s;display:flex;align-items:center;gap:6px; }
    .subject-tab.active { color:#fff;border-color:transparent; }
    .subject-tab.Physics.active { background:linear-gradient(135deg,#0891b2,#2563eb); }
    .subject-tab.Chemistry.active { background:linear-gradient(135deg,#059669,#0d9488); }
    .subject-tab.Mathematics.active { background:linear-gradient(135deg,#7c3aed,#4f46e5); }
    .subject-tab.Biology.active { background:linear-gradient(135deg,#d97706,#b45309); }

    .puc-section { margin-bottom:32px; }
    .puc-label { display:inline-block;padding:4px 14px;border-radius:20px;font-size:0.72rem;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:12px; }
    .puc-label.puc1 { background:rgba(37,99,235,0.15);color:#60a5fa; }
    .puc-label.puc2 { background:rgba(124,58,237,0.15);color:#a78bfa; }

    .chapter-row { display:flex;align-items:flex-start;gap:12px;padding:10px 14px;border-radius:var(--rs);border:1px solid var(--border);background:var(--s2);margin-bottom:6px;transition:border-color 0.15s; }
    .chapter-row:hover { border-color:rgba(255,255,255,0.12); }
    .ch-index { min-width:32px;height:32px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:0.75rem;font-weight:700;flex-shrink:0; }
    .ch-info { flex:1; }
    .ch-title { font-size:0.9rem;font-weight:600;color:var(--text);line-height:1.3; }
    .ch-sub { font-size:0.77rem;color:var(--muted);margin-top:3px;line-height:1.4; }

    .summary-bar { display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:10px;margin-bottom:20px; }
    .summary-tile { background:var(--s2);border:1px solid var(--border);border-radius:var(--rm);padding:12px;text-align:center; }
    .summary-tile .num { font-size:1.5rem;font-weight:700; }
    .summary-tile .lbl { font-size:0.72rem;color:var(--muted);margin-top:2px; }
  
` }} />
      
  <div className="bg-mesh"></div>

  
  

  <main className="main-wrap">

    
    <div style={{"textAlign":"center","padding":"32px 0 24px"}}>
      <h1 style={{"fontSize":"2rem","fontWeight":"800","margin":"0 0 8px"}}>KCET Official Syllabus</h1>
      <p style={{"color":"var(--muted)","fontSize":"0.95rem","margin":"0"}}>Karnataka PUC 1st &amp; 2nd Year — All subjects as per KEA / DPUE Karnataka</p>
    </div>

    
    <div className="summary-bar" id="summaryBar">
      <div className="summary-tile"><div className="num" id="sumTotal">—</div><div className="lbl">Total Chapters</div></div>
      <div className="summary-tile"><div className="num" style={{"color":"#60a5fa"}}>14+14</div><div className="lbl">Physics Chapters</div></div>
      <div className="summary-tile"><div className="num" style={{"color":"#34d399"}}>14+16</div><div className="lbl">Chemistry Chapters</div></div>
      <div className="summary-tile"><div className="num" style={{"color":"#a78bfa"}}>15+13</div><div className="lbl">Maths Chapters</div></div>
      <div className="summary-tile"><div className="num" style={{"color":"#fbbf24"}}>22+16</div><div className="lbl">Biology Chapters</div></div>
    </div>

    
    <div style={{"display":"flex","gap":"8px","flexWrap":"wrap","marginBottom":"24px"}}>
      <button className="subject-tab Physics active" data-subject="Physics">⚡ Physics</button>
      <button className="subject-tab Chemistry" data-subject="Chemistry">🧪 Chemistry</button>
      <button className="subject-tab Mathematics" data-subject="Mathematics">📐 Mathematics</button>
      <button className="subject-tab Biology" data-subject="Biology">🌱 Biology</button>
    </div>

    
    <div id="syllabusContent">
      <div style={{"textAlign":"center","color":"var(--muted)","padding":"60px"}}>Loading syllabus…</div>
    </div>

  </main>

  
  

    </>
  );
};

export default Syllabus;
