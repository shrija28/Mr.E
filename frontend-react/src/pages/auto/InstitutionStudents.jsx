import React from 'react';
import { Link } from 'react-router-dom';

const InstitutionStudents = () => {
  return (
    <>
      {/* Auto-injected styles from HTML head */}
      <style dangerouslySetInnerHTML={{ __html: `
    /* Copy code button styling */
    .btn-copy-code {
      background: none;
      border: none;
      cursor: pointer;
      padding: 4px;
      display: flex;
      align-items: center;
      justify-content: center;
      color: var(--muted);
      transition: color 0.2s, transform 0.15s;
      border-radius: 4px;
      flex-shrink: 0;
    }
    .btn-copy-code:hover {
      color: var(--purple-l, #a78bfa);
      transform: scale(1.1);
    }
    .btn-copy-code:active {
      transform: scale(0.95);
    }
    
    /* Fix table column alignment */
    .responsive-table-wrapper table {
      width: 100%;
      border-collapse: collapse;
    }
    
    .responsive-table-wrapper table thead th {
      text-align: left;
      padding: 12px 16px;
      border-bottom: 1px solid var(--border);
      font-weight: 600;
      font-size: 0.85rem;
      color: var(--muted);
    }
    
    .responsive-table-wrapper table thead th:last-child {
      text-align: right;
    }
    
    .responsive-table-wrapper table tbody td {
      padding: 12px 16px;
      border-bottom: 1px solid var(--border);
      vertical-align: middle;
    }
    
    .responsive-table-wrapper table tbody td:last-child {
      text-align: right;
    }
    
    /* Code cell with flex container */
    .code-cell-wrapper {
      display: flex;
      align-items: center;
      gap: 8px;
      width: 100%;
    }
    
    .invitation-code-cell {
      font-family: monospace;
      font-size: 0.85rem;
      background: rgba(167, 139, 250, 0.1);
      padding: 4px 8px;
      border-radius: 4px;
      white-space: nowrap;
      color: var(--purple-l, #a78bfa);
    }
    
    /* Invitation number label */
    .invitation-number-label {
      font-weight: 500;
      font-size: 0.95rem;
      color: var(--text);
      white-space: nowrap;
    }
  
` }} />
      
  <div className="bg-mesh"></div>

  
  

  <main className="institution-page" id="studentsPage">
    
    <header className="institution-page-header">
      <div>
        <h1 className="institution-page-title">Manage <span className="institution-page-title-accent">Students</span></h1>
        <p className="institution-page-sub">Invite new students and manage existing institution members</p>
      </div>
      <div className="institution-page-actions">
        <button
          type="button"
          id="inviteStudentBtn"
          className="btn-institution"
          aria-label="Generate a new student invitation"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true"><path d="M16 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="8.5" cy="7" r="4"/><line x1="20" y1="8" x2="20" y2="14"/><line x1="23" y1="11" x2="17" y2="11"/></svg>
          Invite Student
        </button>
      </div>
    </header>

    
    <div
      id="studentsPageError"
      className="page-error"
      role="alert"
      aria-live="polite"
      style={{"display":"none","background":"rgba(220,38,38,0.1)","border":"1px solid var(--red)","borderRadius":"var(--rs)","padding":"12px 16px","marginBottom":"20px","fontSize":"0.9rem","color":"var(--red-l)"}}
    ></div>

    
    <div
      id="studentsPageSuccess"
      className="page-success"
      role="status"
      aria-live="polite"
      style={{"display":"none","background":"rgba(5,150,105,0.1)","border":"1px solid var(--green)","borderRadius":"var(--rs)","padding":"12px 16px","marginBottom":"20px","fontSize":"0.9rem","color":"var(--green-l)"}}
    ></div>

    
    <section className="section-card" aria-labelledby="studentsListHeading">
      <div className="section-card-header">
        <div className="section-icon institution" aria-hidden="true">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 00-3-3.87"/><path d="M16 3.13a4 4 0 010 7.75"/></svg>
        </div>
        <div>
          <h2 id="studentsListHeading">Linked Students</h2>
          <p className="section-sub">Students currently linked to your institution</p>
        </div>
      </div>
      <div className="section-body">
        
        <div
          id="studentsLoading"
          role="status"
          aria-live="polite"
          style={{"textAlign":"center","padding":"24px 0","color":"var(--muted)","fontSize":"0.9rem"}}
        >
          Loading students…
        </div>

        
        <div
          id="studentsEmpty"
          className="empty-state"
          style={{"display":"none","padding":"24px 0","textAlign":"center"}}
        >
          <p className="empty-message" style={{"color":"var(--muted)","fontSize":"0.95rem"}}>
            No students linked yet. Click "Invite Student" to send an invitation.
          </p>
        </div>

        
        <div
          id="studentsError"
          role="alert"
          aria-live="polite"
          style={{"display":"none","padding":"16px","border":"1px solid var(--red)","borderRadius":"var(--rs)","background":"rgba(220,38,38,0.08)","color":"var(--red-l)","fontSize":"0.9rem"}}
        >
          <span id="studentsErrorMessage">Unable to load students.</span>
          <button type="button" className="btn-institution-outline" id="studentsRetryBtn" style={{"marginLeft":"12px"}}>
            Retry
          </button>
        </div>

        
        <div className="responsive-table-wrapper" id="studentsTableWrapper" style={{"display":"none"}}>
          <table aria-describedby="studentsListHeading">
            <thead>
              <tr>
                <th scope="col">Student Name</th>
                <th scope="col">Student ID</th>
                <th scope="col">Email</th>
                <th scope="col">Linked Date</th>
                <th scope="col" style={{"textAlign":"right"}}>Action</th>
              </tr>
            </thead>
            <tbody id="studentsTableBody">
              
            </tbody>
          </table>
        </div>
      </div>
    </section>

    
    <section className="section-card" aria-labelledby="invitationsListHeading" style={{"marginTop":"24px"}}>
      <div className="section-card-header" style={{"display":"flex","justifyContent":"space-between","alignItems":"flex-start"}}>
        <div style={{"display":"flex","alignItems":"flex-start","gap":"12px","flex":"1"}}>
          <div className="section-icon institution" aria-hidden="true">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"/></svg>
          </div>
          <div>
            <h2 id="invitationsListHeading">Pending Invitations</h2>
            <p className="section-sub">Invitations waiting for a student to accept</p>
          </div>
        </div>
        <div style={{"display":"flex","alignItems":"center","justifyContent":"center","minWidth":"48px","height":"48px","borderRadius":"8px","background":"rgba(167,139,250,0.1)","fontSize":"1.5rem","fontWeight":"600","color":"var(--purple-l,#a78bfa)"}} data-invitations-count>0</div>
      </div>
      <div className="section-body">
        
        <div
          id="invitationsLoading"
          role="status"
          aria-live="polite"
          style={{"textAlign":"center","padding":"24px 0","color":"var(--muted)","fontSize":"0.9rem"}}
        >
          Loading invitations…
        </div>

        
        <div
          id="invitationsEmpty"
          className="empty-state"
          style={{"display":"none","padding":"24px 0","textAlign":"center"}}
        >
          <p className="empty-message" style={{"color":"var(--muted)","fontSize":"0.95rem"}}>
            No pending invitations. Click "Invite Student" above to create one.
          </p>
        </div>

        
        <div
          id="invitationsError"
          role="alert"
          aria-live="polite"
          style={{"display":"none","padding":"16px","border":"1px solid var(--red)","borderRadius":"var(--rs)","background":"rgba(220,38,38,0.08)","color":"var(--red-l)","fontSize":"0.9rem"}}
        >
          <span id="invitationsErrorMessage">Unable to load invitations.</span>
          <button type="button" className="btn-institution-outline" id="invitationsRetryBtn" style={{"marginLeft":"12px"}}>
            Retry
          </button>
        </div>

        
        <div className="responsive-table-wrapper" id="invitationsTableWrapper" style={{"display":"none"}}>
          <table aria-describedby="invitationsListHeading">
            <thead>
              <tr>
                <th scope="col">Code</th>
                <th scope="col">Created Date</th>
                <th scope="col">Expiry Date</th>
                <th scope="col">Status</th>
              </tr>
            </thead>
            <tbody id="invitationsTableBody">
              
            </tbody>
          </table>
        </div>
      </div>
    </section>
  </main>

  
  <div
    className="modal-overlay"
    id="invitationModal"
    role="dialog"
    aria-modal="true"
    aria-labelledby="invitationModalTitle"
    aria-hidden="true"
    style={{"display":"none"}}
  >
    <div className="modal-dialog invitation-modal-dialog" role="document">
      <div className="modal-header">
        <h2 id="invitationModalTitle">Student Invitation Generated</h2>
        <button
          type="button"
          className="modal-close"
          id="invitationModalCloseBtn"
          aria-label="Close invitation dialog"
        >&times;</button>
      </div>

      <div className="modal-body">
        <p className="invitation-notice" id="invitationExpiryNotice">
          This invitation expires in 7 days.
        </p>

        
        <div className="invitation-link-box">
          <label htmlFor="invitationLinkInput">Invitation Link</label>
          <div className="invitation-input-row">
            <input
              type="text"
              id="invitationLinkInput"
              readonly
              value=""
              aria-describedby="invitationExpiryNotice"
            />
            <button
              type="button"
              className="btn-copy"
              id="copyLinkBtn"
              data-copy="link"
              aria-label="Copy invitation link to clipboard"
              aria-describedby="invitationCopyFeedback"
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg>
              Copy Link
            </button>
          </div>
        </div>

        
        <div className="invitation-code-box">
          <label htmlFor="invitationCodeInput">Invitation Code</label>
          <div className="invitation-input-row">
            <input
              type="text"
              id="invitationCodeInput"
              readonly
              value=""
              aria-describedby="invitationExpiryNotice"
            />
            <button
              type="button"
              className="btn-copy"
              id="copyCodeBtn"
              data-copy="code"
              aria-label="Copy invitation code to clipboard"
              aria-describedby="invitationCopyFeedback"
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg>
              Copy Code
            </button>
          </div>
        </div>

        
        <div
          className="copy-feedback"
          id="invitationCopyFeedback"
          role="status"
          aria-live="polite"
          style={{"display":"none"}}
        ></div>

        <div className="modal-actions">
          <button
            type="button"
            className="btn-institution"
            id="invitationModalDoneBtn"
          >
            Done
          </button>
        </div>
      </div>
    </div>
  </div>

  
  
  
  
  
  
  
  

    </>
  );
};

export default InstitutionStudents;
