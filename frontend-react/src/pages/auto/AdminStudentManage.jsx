import React from 'react';
import { Link } from 'react-router-dom';

const AdminStudentManage = () => {
  return (
    <>
      {/* Auto-injected styles from HTML head */}
      <style dangerouslySetInnerHTML={{ __html: `
    .form-section {
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: var(--r);
      padding: 20px;
      margin-bottom: 20px;
    }
    
    .form-section h3 {
      margin: 0 0 16px;
      font-size: 1rem;
      font-weight: 600;
    }
    
    .form-row {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 16px;
      margin-bottom: 16px;
    }
    
    .form-row.full {
      grid-template-columns: 1fr;
    }
    
    .form-group {
      display: flex;
      flex-direction: column;
    }
    
    .form-group label {
      font-size: 0.85rem;
      font-weight: 600;
      color: var(--text);
      margin-bottom: 6px;
    }
    
    .form-group input,
    .form-group select {
      padding: 8px 12px;
      border: 1px solid var(--border);
      border-radius: var(--rs);
      background: var(--s2);
      color: var(--text);
      font-size: 0.9rem;
    }
    
    .form-group input:focus,
    .form-group select:focus {
      outline: none;
      border-color: var(--purple-l, #a78bfa);
      background: var(--s3);
    }
    
    .form-group small {
      font-size: 0.75rem;
      color: var(--muted2);
      margin-top: 4px;
    }
    
    .section-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 20px;
      margin-bottom: 20px;
    }
    
    @media (max-width: 900px) {
      .section-grid {
        grid-template-columns: 1fr;
      }
      
      .form-row {
        grid-template-columns: 1fr;
      }
    }
    
    .info-tile {
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: var(--r);
      padding: 16px;
    }
    
    .info-tile-label {
      font-size: 0.75rem;
      color: var(--muted);
      text-transform: uppercase;
      letter-spacing: 0.3px;
      font-weight: 700;
      margin-bottom: 4px;
    }
    
    .info-tile-value {
      font-size: 1.1rem;
      font-weight: 600;
      color: var(--text);
    }
    
    .action-buttons {
      display: flex;
      gap: 10px;
      margin-top: 20px;
      justify-content: flex-end;
    }
    
    .empty-state {
      text-align: center;
      padding: 60px 20px;
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
    
    .status-badge {
      display: inline-block;
      padding: 4px 10px;
      border-radius: 4px;
      font-size: 0.72rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.3px;
    }
    
    .status-badge.active {
      background: rgba(5, 150, 105, 0.15);
      color: var(--green-l);
    }
    
    .status-badge.trial {
      background: rgba(5, 150, 105, 0.1);
      color: var(--green-l);
    }
    
    .status-badge.no_subscription {
      background: rgba(107, 114, 128, 0.1);
      color: var(--muted2);
    }
    
    .status-badge.overdue {
      background: rgba(217, 119, 6, 0.15);
      color: var(--yellow-l);
    }
    
    .status-badge.expired {
      background: rgba(220, 38, 38, 0.12);
      color: var(--red-l);
    }
  
` }} />
      
  <div className="bg-mesh"></div>

  
  

  <div className="main-wrap" style={{"maxWidth":"100%","padding":"24px 28px 80px"}}>

    
    <div style={{"display":"flex","alignItems":"center","justifyContent":"space-between","marginBottom":"20px"}}>
      <div>
        <h1 style={{"fontSize":"1.6rem","fontWeight":"800","margin":"0 0 3px"}} id="pageTitle">Manage Student</h1>
        <p style={{"color":"var(--muted)","margin":"0","fontSize":"0.82rem"}} id="pageSubtitle">View and manage student details and subscription</p>
      </div>
    </div>

    
    <div id="loadingState" style={{"textAlign":"center","padding":"60px 20px","color":"var(--muted)"}}>
      <div style={{"fontSize":"3rem","marginBottom":"12px","opacity":"0.5"}}>⏳</div>
      <div style={{"fontSize":"1.1rem","fontWeight":"600","marginBottom":"6px"}}>Loading…</div>
    </div>

    <div id="contentArea" style={{"display":"none"}}>

      
      <div className="section-grid">
        <div className="form-section">
          <h3>Student Information</h3>
          <div className="form-row">
            <div className="form-group">
              <label>Name *</label>
              <input type="text" id="fieldName" placeholder="Student name" required/>
            </div>
            <div className="form-group">
              <label>Email *</label>
              <input type="email" id="fieldEmail" placeholder="student@example.com" required/>
            </div>
          </div>
          <div className="form-row">
            <div className="form-group">
              <label>KCET Student ID</label>
              <input type="text" id="fieldKcetId" placeholder="Optional KCET ID"/>
            </div>
            <div className="form-group">
              <label>User ID</label>
              <input type="text" id="fieldUserId" placeholder="User ID" readonly style={{"background":"var(--s1)","color":"var(--muted)"}}/>
            </div>
          </div>
        </div>

        <div className="form-section">
          <h3>Password & Security</h3>
          <div style={{"display":"flex","flexDirection":"column","gap":"12px"}}>
            <div style={{"background":"rgba(37,99,235,0.1)","border":"1px solid rgba(37,99,235,0.2)","borderRadius":"var(--rs)","padding":"14px"}}>
              <div style={{"fontWeight":"600","color":"var(--blue-l,#60a5fa)","marginBottom":"8px"}}>🔐 Password Management</div>
              <p style={{"fontSize":"0.85rem","color":"var(--muted)","margin":"0","lineHeight":"1.5"}}>
                Passwords are securely hashed in the database and cannot be viewed. 
                Use the "Reset Password" button below to set a new password for this student if they forgot theirs.
              </p>
            </div>
            
            <div id="resetPasswordSection" style={{"display":"none","border":"1px solid rgba(220,38,38,0.2)","borderRadius":"var(--rs)","padding":"14px","background":"rgba(220,38,38,0.05)"}}>
              <div style={{"fontWeight":"600","color":"var(--red-l)","marginBottom":"12px"}}>⚠️ Set New Password</div>
              <div className="form-group" style={{"marginBottom":"12px"}}>
                <label htmlFor="newPassword">New Password *</label>
                <input type="password" id="newPassword" placeholder="Enter new password" style={{"width":"100%","padding":"10px 14px","border":"1px solid var(--border)","borderRadius":"var(--rs)","background":"var(--s2)","color":"var(--text)"}}/>
                <small style={{"color":"var(--muted2)"}}>Minimum 8 characters. Student will use this to login.</small>
              </div>
              <div className="form-group" style={{"marginBottom":"12px"}}>
                <label htmlFor="confirmPassword">Confirm Password *</label>
                <input type="password" id="confirmPassword" placeholder="Confirm new password" style={{"width":"100%","padding":"10px 14px","border":"1px solid var(--border)","borderRadius":"var(--rs)","background":"var(--s2)","color":"var(--text)"}}/>
              </div>
              <div style={{"display":"flex","gap":"8px","justifyContent":"flex-end"}}>
                <button type="button" className="btn-outline small" id="btnCancelReset" >Cancel</button>
                <button type="button" className="btn-primary small" id="btnSavePassword" style={{"color":"var(--red-l)","borderColor":"var(--red-l)"}}>Confirm Reset</button>
              </div>
            </div>

            <button className="btn-outline small" id="btnResetPassword" style={{"width":"100%","textAlign":"center","color":"var(--red-l)","borderColor":"var(--red-l)"}}>Reset Student Password</button>
          </div>
        </div>
      </div>

      
      <div className="form-section">
        <h3>Subscription Status</h3>
        <div id="subscriptionInfo" style={{"display":"grid","gridTemplateColumns":"1fr 1fr 1fr","gap":"12px","marginBottom":"16px"}}>
          <div className="info-tile">
            <div className="info-tile-label">Current Status</div>
            <div className="info-tile-value">
              <span className="status-badge no_subscription" id="subStatus">No Subscription</span>
            </div>
          </div>
          <div className="info-tile">
            <div className="info-tile-label">Plan</div>
            <div className="info-tile-value" id="subPlan">—</div>
          </div>
          <div className="info-tile">
            <div className="info-tile-label">Renewal Date</div>
            <div className="info-tile-value" id="subRenewal">—</div>
          </div>
        </div>
      </div>

      
      <div className="form-section">
        <h3>Manage Subscription</h3>
        <div className="form-row">
          <div className="form-group">
            <label htmlFor="selectPlan">Change Plan</label>
            <select id="selectPlan">
              <option value="">Select a plan...</option>
            </select>
            <small>Choose a plan to update student subscription</small>
          </div>
          <div className="form-group">
            <label htmlFor="selectDuration">Duration</label>
            <select id="selectDuration">
              <option value="1">1 Month</option>
              <option value="3">3 Months</option>
              <option value="6">6 Months</option>
              <option value="12">1 Year</option>
            </select>
          </div>
        </div>
        <div className="form-row full">
          <div className="form-group">
            <label htmlFor="selectRenewFrom">Renewal From</label>
            <input type="date" id="selectRenewFrom"/>
            <small>Leave empty to renew from today</small>
          </div>
        </div>
        <div style={{"marginTop":"12px","display":"flex","justifyContent":"flex-end"}}>
          <button type="button" className="btn-outline small" id="btnRemoveSub" style={{"color":"var(--red-l)","borderColor":"var(--red-l)"}}>🚫 Remove Subscription (Set INACTIVE)</button>
        </div>
      </div>

      
      <div className="action-buttons">
        <button className="btn-outline" >Back</button>
        <button className="btn-primary" id="btnSave">Save Changes</button>
      </div>

    </div>

    
    <div id="createForm" style={{"display":"none"}}>
      <div className="form-section">
        <h3>Create New Direct Subscriber Student</h3>
        <div className="form-row">
          <div className="form-group">
            <label>Name *</label>
            <input type="text" id="createFieldName" placeholder="Student name" required/>
          </div>
          <div className="form-group">
            <label>Email *</label>
            <input type="email" id="createFieldEmail" placeholder="student@example.com" required/>
          </div>
        </div>
        <div className="form-row">
          <div className="form-group">
            <label>KCET Student ID</label>
            <input type="text" id="createFieldKcetId" placeholder="Optional KCET ID"/>
          </div>
          <div className="form-group">
            <label>Initial Plan</label>
            <select id="createFieldPlan">
              <option value="">No subscription (free)</option>
            </select>
          </div>
        </div>
      </div>

      <div className="action-buttons">
        <button className="btn-outline" >Cancel</button>
        <button className="btn-primary" id="btnCreate">Create Student</button>
      </div>
    </div>

  </div>

  
  

    </>
  );
};

export default AdminStudentManage;
