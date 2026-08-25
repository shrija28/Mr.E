import React from 'react';
import { Link } from 'react-router-dom';

const AdminSubscriptions = () => {
  return (
    <>
      {/* Auto-injected styles from HTML head */}
      <style dangerouslySetInnerHTML={{ __html: `
    .main-wrap { max-width: 100%; }
    .sub-table td { white-space:normal;word-break:break-word;vertical-align:top; }
    .sub-table { table-layout:fixed; }
    .sub-table col.col-inst   { width:20%; }
    .sub-table col.col-plan   { width:12%; }
    .sub-table col.col-type   { width:8%; }
    .sub-table col.col-status { width:10%; }
    .sub-table col.col-start  { width:11%; }
    .sub-table col.col-renew  { width:11%; }
    .sub-table col.col-price  { width:10%; }
    .sub-table col.col-acts   { width:18%; }
    
    /* Plan tables - ensure features column wraps properly */
    table.results-table td { white-space: normal; word-break: break-word; vertical-align: top; overflow-wrap: break-word; }
    table.results-table td:last-child { white-space: nowrap; text-align: center; }
    
    /* Plans table feature column - allow full content display */
    table.plans-table { table-layout: fixed; }
    table.plans-table td { word-wrap: break-word; overflow-wrap: break-word; hyphens: auto; }
    table.plans-table tbody td { font-size: 0.75rem; line-height: 1.4; }
    table.plans-table tbody td:nth-child(6) { max-width: none; word-break: break-word; }
  
` }} />
      
  <div className="bg-mesh"></div>

  


  <div className="main-wrap" style={{"maxWidth":"100%","padding":"24px 28px 80px"}}>

    
    <div style={{"display":"flex","alignItems":"center","justifyContent":"space-between","marginBottom":"20px"}}>
      <div>
        <h1 style={{"fontSize":"1.6rem","fontWeight":"800","margin":"0 0 3px"}}>Subscriptions Management</h1>
        <p style={{"color":"var(--muted)","margin":"0","fontSize":"0.82rem"}}>Monitor all active and inactive subscriptions for institutions and direct subscribers</p>
      </div>
      <button className="btn-outline" style={{"display":"flex","alignItems":"center","gap":"6px"}} >
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{"width":"14px","height":"14px"}}><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 11-2.12-9.36L23 10"/></svg>
        Refresh
      </button>
    </div>

    
    <div style={{"display":"grid","gridTemplateColumns":"repeat(auto-fit,minmax(150px,1fr))","gap":"12px","marginBottom":"24px"}} id="subTiles">
      <div style={{"background":"var(--card-bg)","border":"1px solid var(--border)","borderRadius":"var(--r)","padding":"16px","textAlign":"center"}}>
        <div style={{"fontSize":"1.6rem","fontWeight":"800","color":"var(--green-l)"}} id="tilActive">—</div>
        <div style={{"fontSize":"0.75rem","color":"var(--muted)"}}>Active</div>
      </div>
      <div style={{"background":"var(--card-bg)","border":"1px solid var(--border)","borderRadius":"var(--r)","padding":"16px","textAlign":"center"}}>
        <div style={{"fontSize":"1.6rem","fontWeight":"800","color":"var(--yellow-l)"}} id="tilOverdue">—</div>
        <div style={{"fontSize":"0.75rem","color":"var(--muted)"}}>Overdue</div>
      </div>
      <div style={{"background":"var(--card-bg)","border":"1px solid var(--border)","borderRadius":"var(--r)","padding":"16px","textAlign":"center"}}>
        <div style={{"fontSize":"1.6rem","fontWeight":"800","color":"var(--red-l)"}} id="tilExpired">—</div>
        <div style={{"fontSize":"0.75rem","color":"var(--muted)"}}>Expired</div>
      </div>
      <div style={{"background":"var(--card-bg)","border":"1px solid var(--border)","borderRadius":"var(--r)","padding":"16px","textAlign":"center"}}>
        <div style={{"fontSize":"1.6rem","fontWeight":"800","color":"var(--muted)"}} id="tilNone">—</div>
        <div style={{"fontSize":"0.75rem","color":"var(--muted)"}}>No Sub</div>
      </div>
    </div>

    
    <div className="section-card">
      <div className="section-card-header" style={{"flexDirection":"column","alignItems":"flex-start"}}>
        <div style={{"display":"flex","alignItems":"center","gap":"12px","width":"100%"}}>
          <div className="section-icon" style={{"background":"linear-gradient(135deg,rgba(5,150,105,0.2),rgba(8,145,178,0.2))"}}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>
          </div>
          <div>
            <h2 style={{"margin":"0"}}>Institution Subscriptions</h2>
            <p className="section-sub" style={{"margin":"2px 0 0"}}>All institution subscription records — plan, status, and renewal</p>
          </div>
        </div>
        <div style={{"alignSelf":"flex-end","marginTop":"0"}}>
          <select id="filterSubStatus" className="text-input" style={{"minWidth":"140px"}}>
            <option value="">All Statuses</option>
            <option value="active">Active</option>
            <option value="trial">Trial</option>
            <option value="overdue">Overdue</option>
            <option value="grace_period">Grace Period</option>
            <option value="expired">Expired</option>
            <option value="cancelled">Cancelled</option>
          </select>
        </div>
      </div>

      <div className="section-body" style={{"padding":"0"}}>
        <div className="table-scroll">
          <table className="results-table sub-table">
            <colgroup>
              <col className="col-inst"/><col className="col-plan"/><col className="col-type"/>
              <col className="col-status"/><col className="col-start"/><col className="col-renew"/>
              <col className="col-price"/><col className="col-acts"/>
            </colgroup>
            <thead>
              <tr>
                <th>Institution</th><th>Plan</th><th>Type</th>
                <th>Status</th><th>Start Date</th><th>Renewal</th>
                <th>Price</th><th>Actions</th>
              </tr>
            </thead>
            <tbody id="subTableBody">
              <tr><td colspan="8" style={{"textAlign":"center","color":"var(--muted)","padding":"40px"}}>Loading…</td></tr>
            </tbody>
          </table>
        </div>
        <div style={{"padding":"12px 20px","borderTop":"1px solid var(--border)"}}>
          <span id="tableFooter" style={{"fontSize":"0.82rem","color":"var(--muted)"}}>—</span>
        </div>
      </div>
    </div>

    
    <div className="section-card" style={{"marginTop":"20px"}}>
      <div className="section-card-header" style={{"flexDirection":"column","alignItems":"flex-start"}}>
        <div style={{"display":"flex","alignItems":"center","gap":"12px","width":"100%"}}>
          <div className="section-icon" style={{"background":"linear-gradient(135deg,rgba(37,99,235,0.2),rgba(124,58,237,0.2))"}}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
          </div>
          <div>
            <h2 style={{"margin":"0"}}>Direct Subscriber Subscriptions</h2>
            <p className="section-sub" style={{"margin":"2px 0 0"}}>Individual student subscriptions (non-institution-linked) — manage and monitor</p>
          </div>
        </div>
        <div style={{"alignSelf":"flex-end","marginTop":"0"}}>
          <select id="filterDirectStatus" className="text-input" style={{"minWidth":"140px"}}>
            <option value="">All Statuses</option>
            <option value="active">Active</option>
            <option value="trial">Trial</option>
            <option value="overdue">Overdue</option>
            <option value="grace_period">Grace Period</option>
            <option value="expired">Expired</option>
            <option value="cancelled">Cancelled</option>
          </select>
        </div>
      </div>

      <div className="section-body" style={{"padding":"0"}}>
        <div className="table-scroll">
          <table className="results-table" style={{"tableLayout":"fixed"}}>
            <colgroup>
              <col style={{"width":"14%"}}/><col style={{"width":"12%"}}/><col style={{"width":"14%"}}/>
              <col style={{"width":"10%"}}/><col style={{"width":"10%"}}/><col style={{"width":"10%"}}/>
              <col style={{"width":"10%"}}/><col style={{"width":"10%"}}/><col style={{"width":"10%"}}/>
            </colgroup>
            <thead>
              <tr>
                <th>Student Name</th><th>KCET ID</th><th>Email</th>
                <th>Plan</th><th>Status</th><th>Start Date</th>
                <th>Renewal</th><th>Price</th><th>Actions</th>
              </tr>
            </thead>
            <tbody id="directSubTableBody">
              <tr><td colspan="9" style={{"textAlign":"center","color":"var(--muted)","padding":"40px"}}>Loading…</td></tr>
            </tbody>
          </table>
        </div>
        <div style={{"padding":"12px 20px","borderTop":"1px solid var(--border)"}}>
          <span id="directTableFooter" style={{"fontSize":"0.82rem","color":"var(--muted)"}}>—</span>
        </div>
      </div>
    </div>

    
    <div className="section-card" style={{"marginTop":"20px"}}>
      <div className="section-card-header" style={{"flexDirection":"column","alignItems":"flex-start"}}>
        <div style={{"display":"flex","alignItems":"center","gap":"12px"}}>
          <div className="section-icon" style={{"background":"linear-gradient(135deg,rgba(124,58,237,0.2),rgba(37,99,235,0.2))"}}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>
          </div>
          <div>
            <h2 style={{"margin":"0"}}>Subscription Plans</h2>
            <p className="section-sub" style={{"margin":"2px 0 0"}}>Available plans in the system</p>
          </div>
        </div>
      </div>

      
      <div style={{"marginBottom":"20px"}}>
        <h3 style={{"margin":"16px 20px 0","fontSize":"0.95rem","color":"var(--text)"}}>Individual/Direct Subscriber Plans</h3>
        <div className="section-body" style={{"padding":"0"}}>
          <div className="table-scroll">
            <table className="results-table plans-table" style={{"tableLayout":"fixed"}}>
              <colgroup>
                <col style={{"width":"14%"}}/><col style={{"width":"10%"}}/><col style={{"width":"10%"}}/>
                <col style={{"width":"10%"}}/><col style={{"width":"10%"}}/><col style={{"width":"26%"}}/>
                <col style={{"width":"10%"}}/>
              </colgroup>
              <thead>
                <tr><th>Plan Name</th><th>Billing</th><th>Price</th><th>Max Tests</th><th>Max Exams</th><th>Features</th><th>Active</th></tr>
              </thead>
              <tbody id="directPlansTableBody">
                <tr><td colspan="7" style={{"textAlign":"center","color":"var(--muted)","padding":"24px"}}>Loading…</td></tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      
      <div>
        <h3 style={{"margin":"16px 20px 0","fontSize":"0.95rem","color":"var(--text)"}}>Institution Plans</h3>
        <div className="section-body" style={{"padding":"0"}}>
          <div className="table-scroll">
            <table className="results-table plans-table" style={{"tableLayout":"fixed"}}>
              <colgroup>
                <col style={{"width":"14%"}}/><col style={{"width":"10%"}}/><col style={{"width":"10%"}}/>
                <col style={{"width":"10%"}}/><col style={{"width":"10%"}}/><col style={{"width":"26%"}}/>
                <col style={{"width":"10%"}}/>
              </colgroup>
              <thead>
                <tr><th>Plan Name</th><th>Billing</th><th>Price</th><th>Max Seats</th><th>Max Tests</th><th>Features</th><th>Active</th></tr>
              </thead>
              <tbody id="institutionPlansTableBody">
                <tr><td colspan="7" style={{"textAlign":"center","color":"var(--muted)","padding":"24px"}}>Loading…</td></tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>

  </div>

  
  

    </>
  );
};

export default AdminSubscriptions;
