import React from 'react';
import { Link } from 'react-router-dom';

const AdminTextbookUpload = () => {
  return (
    <>
      {/* Auto-injected styles from HTML head */}
      <style dangerouslySetInnerHTML={{ __html: `
    .subject-tabs { display:flex;gap:8px;flex-wrap:wrap;margin-bottom:20px; }
    .subject-tab { padding:8px 18px;border-radius:var(--rs);cursor:pointer;font-size:0.85rem;font-weight:600;border:1px solid var(--border);color:var(--muted2);background:var(--s2);transition:all 0.15s; }
    .subject-tab.active { background:var(--purple-l,#a78bfa);color:#fff;border-color:var(--purple-l,#a78bfa); }
    .puc-section { margin-bottom:28px; }
    .puc-label { font-size:0.75rem;text-transform:uppercase;letter-spacing:0.6px;color:var(--muted);font-weight:700;margin-bottom:10px;padding:6px 10px;background:var(--s2);border-radius:var(--rs);display:inline-block; }
    .chapter-row { display:grid;grid-template-columns:36px 1fr auto;align-items:center;gap:12px;padding:10px 14px;border:1px solid var(--border);border-radius:var(--rs);margin-bottom:6px;background:var(--card-bg);transition:border-color 0.15s; }
    .chapter-row.has-file { border-color:var(--purple-l,#a78bfa);background:rgba(124,58,237,0.05); }
    .chapter-row.uploaded { border-color:var(--green-l,#34d399);background:rgba(5,150,105,0.06); }
    .chapter-row.error { border-color:var(--red-l,#f87171);background:rgba(220,38,38,0.05); }
    .ch-num-badge { width:32px;height:32px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:0.72rem;font-weight:700;flex-shrink:0;background:rgba(124,58,237,0.15);color:var(--purple-l,#a78bfa); }
    .ch-info { min-width:0; }
    .ch-name { font-size:0.87rem;font-weight:600;color:var(--text);white-space:nowrap;overflow:hidden;text-overflow:ellipsis; }
    .ch-meta { font-size:0.75rem;color:var(--muted);margin-top:2px; }
    .ch-status { font-size:0.75rem;margin-top:3px; }
    .ch-status.ok { color:var(--green-l,#34d399); }
    .ch-status.err { color:var(--red-l,#f87171); }
    .file-drop-area { position:relative;display:flex;align-items:center;gap:8px;flex-shrink:0; }
    .file-pick-btn { padding:5px 12px;font-size:0.78rem;border-radius:var(--rs);border:1px dashed var(--border);color:var(--muted2);background:var(--s2);cursor:pointer;white-space:nowrap;transition:all 0.15s; }
    .file-pick-btn:hover { border-color:var(--purple-l,#a78bfa);color:var(--purple-l,#a78bfa); }
    .file-name-label { font-size:0.75rem;color:var(--muted);max-width:160px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis; }
    .clear-btn { width:20px;height:20px;border-radius:50%;border:none;background:rgba(220,38,38,0.15);color:var(--red-l,#f87171);cursor:pointer;font-size:0.85rem;display:flex;align-items:center;justify-content:center;flex-shrink:0;padding:0; }
    .sticky-footer { position:sticky;bottom:0;background:var(--card-bg);border-top:1px solid var(--border);padding:14px 24px;display:flex;align-items:center;gap:16px;z-index:10; }
    .progress-bar-wrap { flex:1;height:6px;background:var(--s2);border-radius:3px;overflow:hidden; }
    .progress-bar-fill { height:100%;background:var(--purple-l,#a78bfa);border-radius:3px;transition:width 0.3s; }
    .upload-stats { font-size:0.82rem;color:var(--muted);white-space:nowrap; }
    .existing-badge { display:inline-flex;align-items:center;gap:4px;font-size:0.72rem;color:var(--green-l,#34d399);background:rgba(5,150,105,0.12);border:1px solid rgba(5,150,105,0.2);border-radius:10px;padding:2px 8px;margin-left:6px; }
  
` }} />
      
  <div className="bg-mesh"></div>

  
  

  <div className="main-wrap" style={{"paddingBottom":"100px"}}>
    
    <div className="section-card">
      <div className="section-card-header">
        <div className="section-icon" style={{"background":"linear-gradient(135deg,rgba(124,58,237,0.2),rgba(37,99,235,0.2))"}}>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M4 19.5A2.5 2.5 0 016.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 014 19.5v-15A2.5 2.5 0 016.5 2z"/></svg>
        </div>
        <div>
          <h2>Bulk Textbook Upload</h2>
          <p className="section-sub">Assign a textbook (PDF, DOCX, TXT) to every chapter in one go · Files are indexed into the RAG engine automatically</p>
        </div>
        <div style={{"marginLeft":"auto","display":"flex","gap":"10px","alignItems":"center"}}>
          <span id="headerStats" style={{"fontSize":"0.82rem","color":"var(--muted)"}}></span>
          <button className="btn-outline small" id="selectAllSubjectBtn" style={{"display":"none"}}>Select All Visible</button>
        </div>
      </div>

      <div className="section-body">
        
        <div className="subject-tabs" id="subjectTabs">
          <div style={{"color":"var(--muted)","fontSize":"0.85rem"}}>Loading chapters…</div>
        </div>

        
        <div id="chaptersContainer">
          <div style={{"textAlign":"center","color":"var(--muted)","padding":"40px"}}>Loading…</div>
        </div>

        
        <div id="alertArea" style={{"display":"none","marginTop":"16px","padding":"12px 16px","borderRadius":"var(--rs)","fontSize":"0.85rem"}}></div>
      </div>
    </div>
  </div>

  
  <div className="sticky-footer" id="stickyFooter" style={{"display":"none"}}>
    <div>
      <div style={{"fontSize":"0.85rem","fontWeight":"600","color":"var(--text)"}} id="footerTitle">Ready to upload</div>
      <div className="upload-stats" id="footerSub"></div>
    </div>
    <div className="progress-bar-wrap" id="progressWrap" style={{"display":"none"}}>
      <div className="progress-bar-fill" id="progressBar" style={{"width":"0%"}}></div>
    </div>
    <div className="upload-stats" id="progressLabel" style={{"display":"none"}}></div>
    <button className="btn-primary" id="uploadAllBtn">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{"width":"14px","height":"14px"}}><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
      Upload All Selected
    </button>
  </div>

  
  

    </>
  );
};

export default AdminTextbookUpload;
