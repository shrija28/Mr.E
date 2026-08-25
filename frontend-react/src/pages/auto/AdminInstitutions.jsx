import React from 'react';
import { Link } from 'react-router-dom';

const AdminInstitutions = () => {
  return (
    <>
      {/* Auto-injected styles from HTML head */}
      <style dangerouslySetInnerHTML={{ __html: `
    .inst-table td { white-space:normal;word-break:break-word;vertical-align:top; }
    .inst-table { table-layout:fixed; }
    .inst-table col.col-name   { width:24%; }
    .inst-table col.col-status { width:11%; }
    .inst-table col.col-sub    { width:12%; }
    .inst-table col.col-stud   { width:8%; }
    .inst-table col.col-quest  { width:8%; }
    .inst-table col.col-exams  { width:8%; }
    .inst-table col.col-renew  { width:12%; }
    .inst-table col.col-acts   { width:17%; }
  
` }} />
      
  <div className="bg-mesh"></div>

  

  <div className="main-wrap" style={{"maxWidth":"100%","padding":"24px 28px 80px"}}>
    <div style={{"display":"flex","alignItems":"center","justifyContent":"space-between","marginBottom":"20px"}}>
      <div>
        <h1 style={{"fontSize":"1.6rem","fontWeight":"800","margin":"0 0 3px"}}>Institution Management</h1>
        <p style={{"color":"var(--muted)","margin":"0","fontSize":"0.82rem"}}>Activate, suspend, view details and monitor all institutions</p>
      </div>
      <button className="btn-outline" id="refreshBtn" style={{"display":"flex","alignItems":"center","gap":"6px"}}>
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{"width":"14px","height":"14px"}}><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 11-2.12-9.36L23 10"/></svg>
        Refresh
      </button>
    </div>

    <div className="section-card">
      <div className="section-body" style={{"paddingBottom":"0"}}>
        
        <div style={{"display":"flex","gap":"12px","flexWrap":"wrap","marginBottom":"16px"}}>
          <div className="input-group" style={{"margin":"0"}}>
            <label className="input-label" htmlFor="filterStatus">Status</label>
            <select id="filterStatus" className="text-input">
              <option value="">All</option>
              <option value="active">Active</option>
              <option value="inactive">Inactive</option>
              <option value="overdue">Overdue</option>
              <option value="grace_period">Grace Period</option>
              <option value="expired">Expired</option>
            </select>
          </div>

        </div>
      </div>

      <div className="section-body" style={{"padding":"0"}}>
        <div className="table-scroll">
          <table className="results-table inst-table">
            <colgroup>
              <col className="col-name"/><col className="col-status"/><col className="col-sub"/>
              <col className="col-stud"/><col className="col-quest"/><col className="col-exams"/>
              <col className="col-renew"/><col className="col-acts"/>
            </colgroup>
            <thead>
              <tr>
                <th>Institution</th><th>Status</th><th>Subscription</th>
                <th>Students</th><th>Questions</th><th>Exams</th>
                <th>Renewal</th><th>Actions</th>
              </tr>
            </thead>
            <tbody id="instTableBody">
              <tr><td colspan="8" style={{"textAlign":"center","color":"var(--muted)","padding":"40px"}}>Loading…</td></tr>
            </tbody>
          </table>
        </div>
        <div style={{"padding":"12px 20px","borderTop":"1px solid var(--border)"}}>
          <span id="tableFooter" style={{"fontSize":"0.82rem","color":"var(--muted)"}}>—</span>
        </div>
      </div>
    </div>
  </div>

  
  <div id="confirmModal" style={{"display":"none","position":"fixed","inset":"0","background":"rgba(0,0,0,0.6)","zIndex":"1000","alignItems":"center","justifyContent":"center"}}>
    <div style={{"background":"var(--card-bg)","border":"1px solid var(--border)","borderRadius":"var(--r)","padding":"28px","maxWidth":"400px","width":"90%"}}>
      <h3 id="confirmTitle" style={{"margin":"0 0 10px","fontSize":"1.05rem"}}>Confirm Action</h3>
      <p id="confirmMsg" style={{"color":"var(--muted)","fontSize":"0.88rem","margin":"0 0 20px"}}></p>
      <div style={{"display":"flex","gap":"10px","justifyContent":"flex-end"}}>
        <button className="btn-outline small" id="confirmCancelBtn">Cancel</button>
        <button className="btn-primary small" id="confirmOkBtn">Confirm</button>
      </div>
    </div>
  </div>

  
  

    </>
  );
};

export default AdminInstitutions;
