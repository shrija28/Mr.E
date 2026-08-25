import React from 'react';
import { Link } from 'react-router-dom';

const InstitutionQuestions = () => {
  return (
    <>
      {/* Auto-injected styles from HTML head */}
      <style dangerouslySetInnerHTML={{ __html: `
    /* ── Questions table — scoped overrides ──────────────────────────────
       The global .results-table td has white-space:nowrap which collapses
       long MCQ text. These scoped rules fix layout without touching other
       tables in the app.
    ───────────────────────────────────────────────────────────────────── */
    #questionsTable {
      table-layout: fixed;
      width: 100%;
    }

    /* Column widths: fixed so they never collapse regardless of content */
    #questionsTable col.col-question  { width: 44%; }
    #questionsTable col.col-subject   { width: 10%; }
    #questionsTable col.col-topic     { width: 12%; }
    #questionsTable col.col-options   { width: 28%; }
    #questionsTable col.col-action    { width: 6%;  }

    /* All cells in this table: allow wrapping */
    #questionsTable td,
    #questionsTable th {
      white-space: normal;
      word-break: break-word;
      overflow-wrap: anywhere;
      vertical-align: top;
    }

    /* Question text */
    .q-text {
      font-size: 0.87rem;
      line-height: 1.5;
      font-weight: 500;
      color: var(--text);
      word-break: break-word;
      overflow-wrap: anywhere;
      white-space: normal;
    }

    /* Options list inside the options cell */
    .q-options {
      display: flex;
      flex-direction: column;
      gap: 3px;
    }
    .q-option {
      font-size: 0.77rem;
      line-height: 1.4;
      color: var(--muted2);
      word-break: break-word;
      overflow-wrap: anywhere;
      white-space: normal;
    }
    .q-option.correct {
      color: var(--green-l);
      font-weight: 600;
    }

    /* Subject badge — keep it on one line but allow shrink */
    #questionsTable .score-badge {
      white-space: nowrap;
      display: inline-block;
    }

    /* Topic cell */
    .q-topic {
      font-size: 0.8rem;
      color: var(--muted);
      word-break: break-word;
      overflow-wrap: anywhere;
      white-space: normal;
    }

    /* Mobile: collapse to card layout below 640px */
    @media (max-width: 640px) {
      #questionsTable,
      #questionsTable thead,
      #questionsTable tbody,
      #questionsTable th,
      #questionsTable td,
      #questionsTable tr {
        display: block;
        width: 100%;
      }
      #questionsTable thead { display: none; }
      #questionsTable tr {
        margin-bottom: 12px;
        border: 1px solid var(--border);
        border-radius: var(--rs);
        padding: 12px;
        background: var(--card-bg);
      }
      #questionsTable td {
        padding: 6px 0;
        border: none;
      }
      #questionsTable td::before {
        content: attr(data-label);
        display: block;
        font-size: 0.7rem;
        color: var(--muted);
        text-transform: uppercase;
        letter-spacing: 0.4px;
        margin-bottom: 2px;
      }
    }
  
` }} />
      
  <div className="bg-mesh"></div>

  
  

  <main className="main-wrap">

    
    <div className="section-card">
      <div className="section-card-header">
        <div className="section-icon" style={{"background":"linear-gradient(135deg,rgba(124,58,237,0.2),rgba(37,99,235,0.2))"}}>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
        </div>
        <div>
          <h2>Institution Question Bank</h2>
          <p className="section-sub">Questions extracted from your uploaded papers — scoped exclusively to your institution</p>
        </div>
        <div style={{"marginLeft":"auto"}}>
          <Link to="/institution/upload" className="btn-primary" style={{"textDecoration":"none"}}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{"width":"14px","height":"14px"}}><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
            Upload More
          </Link>
        </div>
      </div>
      <div className="section-body">
        
        <div id="countTiles" style={{"display":"grid","gridTemplateColumns":"repeat(auto-fit,minmax(180px,1fr))","gap":"12px","marginBottom":"20px"}}>
          <div style={{"textAlign":"center","color":"var(--muted)","padding":"24px"}}>Loading…</div>
        </div>
      </div>
    </div>

    
    <div className="section-card">
      <div className="section-card-header">
        <div className="section-icon" style={{"background":"linear-gradient(135deg,rgba(8,145,178,0.2),rgba(5,150,105,0.2))"}}>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><line x1="3" y1="9" x2="21" y2="9"/><line x1="9" y1="21" x2="9" y2="9"/></svg>
        </div>
        <div>
          <h2>All Questions</h2>
          <p className="section-sub" id="questionSubtitle">Loading…</p>
        </div>
      </div>
      <div className="section-body" style={{"paddingBottom":"0"}}>
        
        <div style={{"display":"flex","gap":"12px","alignItems":"center","flexWrap":"wrap","marginBottom":"16px"}}>
          <div className="input-group" style={{"margin":"0"}}>
            <label className="input-label" htmlFor="subjectFilter">Filter by subject</label>
            <select id="subjectFilter" className="text-input" style={{"minWidth":"180px"}}>
              <option value="">All Subjects</option>
              <option value="Biology">Biology</option>
              <option value="Physics">Physics</option>
              <option value="Chemistry">Chemistry</option>
              <option value="Mathematics">Mathematics</option>
            </select>
          </div>
          <div style={{"marginTop":"18px"}}>
            <button className="btn-outline small" id="refreshBtn">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{"width":"13px","height":"13px"}}><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 11-2.12-9.36L23 10"/></svg>
              Refresh
            </button>
          </div>
        </div>
      </div>

      <div className="section-body" style={{"padding":"0"}}>
        <div className="table-scroll">
          <table className="results-table" id="questionsTable">
            <colgroup>
              <col className="col-question"/>
              <col className="col-subject"/>
              <col className="col-topic"/>
              <col className="col-options"/>
              <col className="col-action"/>
            </colgroup>
            <thead>
              <tr>
                <th>Question</th>
                <th>Subject</th>
                <th>Topic</th>
                <th>Options (✓ = correct)</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody id="questionsTableBody">
              <tr><td colspan="5" style={{"textAlign":"center","color":"var(--muted)","padding":"40px"}}>Loading…</td></tr>
            </tbody>
          </table>
        </div>

        
        <div id="paginationBar" style={{"display":"flex","alignItems":"center","justifyContent":"space-between","padding":"14px 20px","borderTop":"1px solid var(--border)"}}>
          <span id="paginationInfo" style={{"fontSize":"0.82rem","color":"var(--muted)"}}>—</span>
          <div style={{"display":"flex","gap":"8px"}}>
            <button className="btn-outline small" id="prevBtn" disabled>← Prev</button>
            <button className="btn-outline small" id="nextBtn" disabled>Next →</button>
          </div>
        </div>
      </div>
    </div>

  </main>

  
  <div id="deleteModal" style={{"display":"none","position":"fixed","inset":"0","background":"rgba(0,0,0,0.6)","zIndex":"1000","alignItems":"center","justifyContent":"center"}}>
    <div style={{"background":"var(--card-bg)","border":"1px solid var(--border)","borderRadius":"var(--r)","padding":"28px","maxWidth":"420px","width":"90%"}}>
      <h3 style={{"margin":"0 0 12px","fontSize":"1.1rem"}}>Delete Question?</h3>
      <p style={{"color":"var(--muted)","fontSize":"0.9rem","margin":"0 0 20px"}}>This will permanently remove the question from your bank. This cannot be undone.</p>
      <div style={{"display":"flex","gap":"10px","justifyContent":"flex-end"}}>
        <button className="btn-outline small" id="deleteCancelBtn">Cancel</button>
        <button className="btn-primary small" id="deleteConfirmBtn" style={{"background":"var(--red)","borderColor":"var(--red)"}}>Delete</button>
      </div>
    </div>
  </div>

  
  
  

    </>
  );
};

export default InstitutionQuestions;
