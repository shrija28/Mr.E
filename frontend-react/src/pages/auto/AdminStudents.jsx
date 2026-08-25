import React from 'react';
import { Link } from 'react-router-dom';

const AdminStudents = () => {
  return (
    <>
      {/* Auto-injected styles from HTML head */}
      <style dangerouslySetInnerHTML={{ __html: `
    .main-wrap { max-width: 100%; }
    
    /* Filter section */
    .filter-section {
      display: flex;
      gap: 12px;
      margin-bottom: 20px;
      flex-wrap: wrap;
      align-items: center;
    }
    
    .filter-section label {
      font-size: 0.85rem;
      color: var(--muted);
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.4px;
    }
    
    /* Student type tabs */
    .tab-group {
      display: flex;
      gap: 0;
      margin-bottom: 20px;
      border-bottom: 1px solid var(--border);
    }
    
    .tab-btn {
      padding: 12px 16px;
      background: transparent;
      border: none;
      color: var(--muted);
      cursor: pointer;
      font-size: 0.88rem;
      font-weight: 600;
      transition: all 0.2s;
      border-bottom: 2px solid transparent;
      margin-bottom: -1px;
    }
    
    .tab-btn:hover {
      color: var(--text);
    }
    
    .tab-btn.active {
      color: var(--purple-l, #a78bfa);
      border-bottom-color: var(--purple-l, #a78bfa);
    }
    
    /* Student table styles */
    .student-table {
      table-layout: fixed;
    }
    
    .student-table colgroup col {
      /* Column widths will be set via colgroup */
    }
    
    .student-table col.col-name { width: 18%; }
    .student-table col.col-id { width: 12%; }
    .student-table col.col-email { width: 18%; }
    .student-table col.col-type { width: 12%; }
    .student-table col.col-institution { width: 18%; }
    .student-table col.col-subscription { width: 12%; }
    .student-table col.col-joined { width: 10%; }
    
    /* Make rows clickable */
    .student-row {
      cursor: pointer;
      transition: background 0.15s;
    }
    
    .student-row:hover td {
      background: rgba(255, 255, 255, 0.03);
    }
    
    /* Status badges */
    .sub-badge {
      display: inline-block;
      padding: 3px 8px;
      border-radius: 4px;
      font-size: 0.7rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.3px;
    }
    
    .sub-badge.active {
      background: rgba(5, 150, 105, 0.15);
      color: var(--green-l);
    }
    
    .sub-badge.trial {
      background: rgba(5, 150, 105, 0.1);
      color: var(--green-l);
    }
    
    .sub-badge.no_subscription {
      background: rgba(107, 114, 128, 0.1);
      color: var(--muted2);
    }
    
    .sub-badge.overdue {
      background: rgba(217, 119, 6, 0.15);
      color: var(--yellow-l);
    }
    
    .sub-badge.expired {
      background: rgba(220, 38, 38, 0.12);
      color: var(--red-l);
    }
    
    /* Empty state */
    .empty-state {
      text-align: center;
      padding: 40px 20px;
      color: var(--muted);
    }
    
    .empty-state-icon {
      font-size: 3rem;
      margin-bottom: 12px;
      opacity: 0.5;
    }
    
    .empty-state-title {
      font-size: 1.1rem;
      font-weight: 600;
      margin-bottom: 6px;
      color: var(--text);
    }
    
    .empty-state-sub {
      font-size: 0.85rem;
      color: var(--muted2);
    }
  
` }} />
      
  <div className="bg-mesh"></div>

  
  

  <div className="main-wrap" style={{"maxWidth":"100%","padding":"24px 28px 80px"}}>

    
    <div style={{"display":"flex","alignItems":"center","justifyContent":"space-between","marginBottom":"20px"}}>
      <div>
        <h1 style={{"fontSize":"1.6rem","fontWeight":"800","margin":"0 0 3px"}}>Students Management</h1>
        <p style={{"color":"var(--muted)","margin":"0","fontSize":"0.82rem"}}>View and manage all students — institution-linked and direct subscribers</p>
      </div>
      <button className="btn-outline" style={{"display":"flex","alignItems":"center","gap":"6px"}} >
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{"width":"14px","height":"14px"}}><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 11-2.12-9.36L23 10"/></svg>
        Refresh
      </button>
    </div>

    
    <div style={{"display":"grid","gridTemplateColumns":"repeat(auto-fit,minmax(150px,1fr))","gap":"12px","marginBottom":"24px"}}>
      <div style={{"background":"var(--card-bg)","border":"1px solid var(--border)","borderRadius":"var(--r)","padding":"16px","textAlign":"center"}}>
        <div style={{"fontSize":"1.6rem","fontWeight":"800","color":"var(--purple-l,#a78bfa)"}} id="tilTotal">—</div>
        <div style={{"fontSize":"0.75rem","color":"var(--muted)"}}>Total Students</div>
      </div>
      <div style={{"background":"var(--card-bg)","border":"1px solid var(--border)","borderRadius":"var(--r)","padding":"16px","textAlign":"center"}}>
        <div style={{"fontSize":"1.6rem","fontWeight":"800","color":"var(--blue-l,#60a5fa)"}} id="tilInstitution">—</div>
        <div style={{"fontSize":"0.75rem","color":"var(--muted)"}}>Institution-linked</div>
      </div>
      <div style={{"background":"var(--card-bg)","border":"1px solid var(--border)","borderRadius":"var(--r)","padding":"16px","textAlign":"center"}}>
        <div style={{"fontSize":"1.6rem","fontWeight":"800","color":"var(--purple-l,#a78bfa)"}} id="tilDirect">—</div>
        <div style={{"fontSize":"0.75rem","color":"var(--muted)"}}>Direct Subscribers</div>
      </div>
      <div style={{"background":"var(--card-bg)","border":"1px solid var(--border)","borderRadius":"var(--r)","padding":"16px","textAlign":"center"}}>
        <div style={{"fontSize":"1.6rem","fontWeight":"800","color":"var(--green-l)"}} id="tilWithSub">—</div>
        <div style={{"fontSize":"0.75rem","color":"var(--muted)"}}>Active Subscriptions</div>
      </div>
    </div>

    
    <div className="section-card">
      <div className="section-card-header" style={{"flexDirection":"column","alignItems":"flex-start"}}>
        <div style={{"display":"flex","alignItems":"center","gap":"12px","width":"100%","marginBottom":"16px"}}>
          <div className="section-icon" style={{"background":"linear-gradient(135deg,rgba(37,99,235,0.2),rgba(124,58,237,0.2))"}}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
          </div>
          <div style={{"flex":"1"}}>
            <h2 style={{"margin":"0","fontSize":"1.1rem"}}>All Students</h2>
            <p className="section-sub" style={{"margin":"2px 0 0"}}>Click to view student details</p>
          </div>
        </div>

        
        <div className="tab-group" style={{"width":"100%"}}>
          <button className="tab-btn active" data-filter="all">All Students</button>
          <button className="tab-btn" data-filter="institution">Institution-linked</button>
          <button className="tab-btn" data-filter="direct">Direct Subscribers</button>
        </div>
      </div>

      <div className="section-body" style={{"padding":"0"}}>
        <div className="table-scroll">
          <table className="results-table student-table">
            <colgroup>
              <col className="col-name"/><col className="col-id"/><col className="col-email"/>
              <col className="col-type"/><col className="col-institution"/><col className="col-subscription"/>
              <col className="col-joined"/>
            </colgroup>
            <thead>
              <tr>
                <th>Name</th><th>Student ID</th><th>Email</th>
                <th>Type</th><th>Institution</th><th>Subscription</th>
                <th>Joined</th>
              </tr>
            </thead>
            <tbody id="studentTableBody">
              <tr><td colspan="7" style={{"textAlign":"center","color":"var(--muted)","padding":"40px"}}>Loading…</td></tr>
            </tbody>
          </table>
        </div>
        <div style={{"padding":"12px 20px","borderTop":"1px solid var(--border)"}}>
          <span id="tableFooter" style={{"fontSize":"0.82rem","color":"var(--muted)"}}>—</span>
        </div>
      </div>
    </div>

  </div>

  
  

    </>
  );
};

export default AdminStudents;
