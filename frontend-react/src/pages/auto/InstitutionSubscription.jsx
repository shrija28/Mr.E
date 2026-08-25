import React from 'react';
import { Link } from 'react-router-dom';

const InstitutionSubscription = () => {
  return (
    <>
      {/* Auto-injected styles from HTML head */}
      <style dangerouslySetInnerHTML={{ __html: `
              .billing-tbl { width:100%;border-collapse:collapse;font-size:0.85rem; }
              .billing-tbl th { text-align:left;padding:12px 16px;font-size:0.72rem;text-transform:uppercase;letter-spacing:0.5px;color:var(--muted);border-bottom:1px solid var(--border);white-space:nowrap; }
              .billing-tbl td { padding:14px 16px;border-bottom:1px solid rgba(255,255,255,0.04);vertical-align:middle; }
              .billing-tbl tr:hover td { background:rgba(255,255,255,0.02); }
              .billing-tbl .amt { font-weight:800;font-size:0.95rem;color:var(--text); }
              .billing-tbl .period { text-transform:capitalize;color:var(--muted2); }
              .billing-tbl .date { color:var(--muted2);white-space:nowrap; }
              .billing-tbl .txn { font-family:'JetBrains Mono',Consolas,monospace;font-size:0.78rem;color:var(--muted);max-width:160px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;display:inline-block;vertical-align:middle; }
              .billing-tbl .copy-btn { background:none;border:none;cursor:pointer;color:var(--muted);font-size:0.8rem;padding:2px 6px;border-radius:4px;transition:color 0.15s; }
              .billing-tbl .copy-btn:hover { color:var(--text); }
              .status-pill { display:inline-flex;align-items:center;gap:5px;padding:4px 12px;border-radius:20px;font-size:0.75rem;font-weight:700;white-space:nowrap; }
              .status-pill.success { background:rgba(5,150,105,0.15);color:var(--green-l); }
              .status-pill.pending { background:rgba(217,119,6,0.15);color:var(--yellow-l); }
              .status-pill.failed  { background:rgba(220,38,38,0.12);color:var(--red-l); }
              .status-pill.created { background:rgba(37,99,235,0.12);color:#60a5fa; }
              .status-pill.refunded { background:rgba(107,114,128,0.15);color:var(--muted); }
              .billing-tbl .actions-cell { white-space:nowrap; }
              .billing-tbl .action-link { font-size:0.78rem;color:var(--purple-l,#a78bfa);text-decoration:none;font-weight:600;transition:opacity 0.15s; }
              .billing-tbl .action-link:hover { opacity:0.7; }
              @media(max-width:700px) {
                .billing-tbl, .billing-tbl thead, .billing-tbl tbody, .billing-tbl th, .billing-tbl td, .billing-tbl tr { display:block;width:100%; }
                .billing-tbl thead { display:none; }
                .billing-tbl tr { margin-bottom:12px;border:1px solid var(--border);border-radius:var(--rs);padding:12px;background:var(--card-bg); }
                .billing-tbl td { padding:6px 0;border:none; }
                .billing-tbl td::before { content:attr(data-label);display:block;font-size:0.68rem;text-transform:uppercase;color:var(--muted);letter-spacing:0.4px;margin-bottom:2px; }
              }
            
` }} />
      
  <div className="bg-mesh"></div>

  
  

  <main className="institution-page" id="institutionSubscriptionPage">
    
    <header className="institution-page-header">
      <div>
        <h1 className="institution-page-title">
          Institution <span className="institution-page-title-accent">Subscription</span>
        </h1>
        <p className="institution-page-sub">Plan details, seat usage, test limits, and renewal information</p>
      </div>
      <div className="institution-page-actions">
        <Link to="/institution/pricing" className="btn-institution" style={{"textDecoration":"none","marginRight":"8px"}}>
          ⭐ Upgrade Plan
        </Link>
        <button className="btn-institution-outline" id="refreshSubscriptionBtn" type="button" aria-label="Refresh subscription details">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 11-2.12-9.36L23 10"/></svg>
          Refresh
        </button>
      </div>
    </header>

    
    <div
      className="institution-alert-banner"
      id="subscriptionAlertBanner"
      role="alert"
      aria-live="polite"
      style={{"display":"none"}}
    >
      <div className="alert-content">
        <span className="alert-icon" aria-hidden="true">⚠️</span>
        <div className="alert-text">
          <strong id="subscriptionAlertTitle">Payment Overdue</strong>
          <span id="subscriptionAlertMessage">Your institution's access will be suspended soon.</span>
        </div>
      </div>
      <button type="button" className="btn-institution" id="subscriptionAlertActionBtn">Pay Now</button>
    </div>

    
    <div
      id="subscriptionLoading"
      role="status"
      aria-live="polite"
      style={{"textAlign":"center","padding":"48px 24px","color":"var(--muted)","fontSize":"0.95rem"}}
    >
      Loading subscription details…
    </div>

    
    <div
      id="subscriptionError"
      className="empty-state"
      role="alert"
      aria-live="polite"
      style={{"display":"none"}}
    >
      <div className="empty-icon" aria-hidden="true">⚠️</div>
      <h3>Unable to load subscription details</h3>
      <p id="subscriptionErrorMessage">Please check your connection and try again.</p>
      <div className="empty-actions">
        <button className="btn-institution" id="subscriptionRetryBtn" type="button">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 11-2.12-9.36L23 10"/></svg>
          Retry
        </button>
      </div>
    </div>

    
    <div
      id="subscriptionEmpty"
      className="empty-state"
      style={{"display":"none"}}
    >
      <div className="empty-icon" aria-hidden="true">📋</div>
      <h3>No subscription found</h3>
      <p>Your institution does not currently have an active subscription. Choose a plan to get started.</p>
      <div className="empty-actions">
        <Link to="/institution/pricing" className="btn-institution" style={{"textDecoration":"none"}}>View Plans & Pricing →</Link>
      </div>
    </div>

    
    <div id="subscriptionContent" style={{"display":"none"}}>

      
      <section className="section-card" aria-labelledby="subscriptionDetailsHeading">
        <div className="section-card-header">
          <div className="section-icon institution" aria-hidden="true">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="2" y="5" width="20" height="14" rx="2"/><line x1="2" y1="10" x2="22" y2="10"/></svg>
          </div>
          <div>
            <h2 id="subscriptionDetailsHeading">Current Plan</h2>
            <p className="section-sub">Subscription details for your institution</p>
          </div>
        </div>
        <div className="section-body">
          
          <div className="subscription-plan-header" style={{"display":"flex","alignItems":"center","justifyContent":"space-between","flexWrap":"wrap","gap":"12px","marginBottom":"20px"}}>
            <div>
              <div
                id="subscriptionPlanName"
                style={{"fontSize":"1.4rem","fontWeight":"800","color":"var(--text)"}}
              >—</div>
              <div
                id="subscriptionInstitutionName"
                style={{"color":"var(--muted)","fontSize":"0.9rem","marginTop":"4px"}}
              ></div>
            </div>
            <span
              id="subscriptionStatusBadge"
              className="status-badge"
              data-status="active"
              role="status"
              aria-live="polite"
              style={{"display":"inline-flex","alignItems":"center","gap":"6px","padding":"6px 14px","borderRadius":"999px","fontSize":"0.78rem","fontWeight":"700","textTransform":"uppercase","letterSpacing":"0.04em"}}
            >—</span>
          </div>

          
          <div
            className="subscription-detail-grid"
            style={{"display":"grid","gridTemplateColumns":"repeat(auto-fit, minmax(220px, 1fr))","gap":"16px"}}
          >
            
            <div className="subscription-detail-item" style={{"padding":"14px 16px","background":"var(--s2,var(--s1))","border":"1px solid var(--border)","borderRadius":"var(--rs)"}}>
              <div style={{"fontSize":"0.72rem","fontWeight":"700","textTransform":"uppercase","letterSpacing":"0.06em","color":"var(--muted)","marginBottom":"6px"}}>Student Seats</div>
              <div style={{"fontSize":"1.2rem","fontWeight":"700","color":"var(--text)"}}>
                <span id="subscriptionSeatsUsed">—</span>
                <span style={{"color":"var(--muted)","fontWeight":"500"}}> / </span>
                <span id="subscriptionSeatsTotal">—</span>
              </div>
              <div id="subscriptionSeatsHint" style={{"fontSize":"0.78rem","color":"var(--muted2)","marginTop":"4px"}}>seats in use</div>
            </div>

            
            <div className="subscription-detail-item" style={{"padding":"14px 16px","background":"var(--s2,var(--s1))","border":"1px solid var(--border)","borderRadius":"var(--rs)"}}>
              <div style={{"fontSize":"0.72rem","fontWeight":"700","textTransform":"uppercase","letterSpacing":"0.06em","color":"var(--muted)","marginBottom":"6px"}}>Weekly Tests</div>
              <div style={{"fontSize":"1.2rem","fontWeight":"700","color":"var(--text)"}}>
                <span id="subscriptionWeeklyLimit">—</span>
              </div>
              <div id="subscriptionWeeklyRemaining" style={{"fontSize":"0.78rem","color":"var(--muted2)","marginTop":"4px"}}>— remaining</div>
            </div>

            
            <div className="subscription-detail-item" style={{"padding":"14px 16px","background":"var(--s2,var(--s1))","border":"1px solid var(--border)","borderRadius":"var(--rs)"}}>
              <div style={{"fontSize":"0.72rem","fontWeight":"700","textTransform":"uppercase","letterSpacing":"0.06em","color":"var(--muted)","marginBottom":"6px"}}>Monthly Tests</div>
              <div style={{"fontSize":"1.2rem","fontWeight":"700","color":"var(--text)"}}>
                <span id="subscriptionMonthlyLimit">—</span>
              </div>
              <div id="subscriptionMonthlyRemaining" style={{"fontSize":"0.78rem","color":"var(--muted2)","marginTop":"4px"}}>— remaining</div>
            </div>

            
            <div className="subscription-detail-item" style={{"padding":"14px 16px","background":"var(--s2,var(--s1))","border":"1px solid var(--border)","borderRadius":"var(--rs)"}}>
              <div
                id="subscriptionRenewalLabel"
                style={{"fontSize":"0.72rem","fontWeight":"700","textTransform":"uppercase","letterSpacing":"0.06em","color":"var(--muted)","marginBottom":"6px"}}
              >Next Renewal</div>
              <div id="subscriptionRenewalDate" style={{"fontSize":"1.05rem","fontWeight":"700","color":"var(--text)"}}>—</div>
              <div id="subscriptionRenewalHint" style={{"fontSize":"0.78rem","color":"var(--muted2)","marginTop":"4px"}}></div>
            </div>

            
            <div className="subscription-detail-item" style={{"padding":"14px 16px","background":"var(--s2,var(--s1))","border":"1px solid var(--border)","borderRadius":"var(--rs)"}}>
              <div style={{"fontSize":"0.72rem","fontWeight":"700","textTransform":"uppercase","letterSpacing":"0.06em","color":"var(--muted)","marginBottom":"6px"}}>Started</div>
              <div id="subscriptionStartDate" style={{"fontSize":"1.05rem","fontWeight":"700","color":"var(--text)"}}>—</div>
            </div>

            
            <div className="subscription-detail-item" id="subscriptionBillingPeriodItem" style={{"padding":"14px 16px","background":"var(--s2,var(--s1))","border":"1px solid var(--border)","borderRadius":"var(--rs)"}}>
              <div style={{"fontSize":"0.72rem","fontWeight":"700","textTransform":"uppercase","letterSpacing":"0.06em","color":"var(--muted)","marginBottom":"6px"}}>Billing Period</div>
              <div id="subscriptionBillingPeriod" style={{"fontSize":"1.05rem","fontWeight":"700","color":"var(--text)","textTransform":"capitalize"}}>—</div>
            </div>
          </div>
        </div>
      </section>

      
      <section className="section-card" aria-labelledby="paymentHistoryHeading" style={{"marginTop":"24px"}}>
        <div className="section-card-header">
          <div className="section-icon institution" aria-hidden="true">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 8v4l3 3"/><circle cx="12" cy="12" r="10"/></svg>
          </div>
          <div>
            <h2 id="paymentHistoryHeading">Payment History</h2>
            <p className="section-sub">Past billing records for your institution's subscription</p>
          </div>
        </div>
        <div className="section-body">
          
          <div
            id="paymentHistoryEmpty"
            className="empty-state"
            style={{"display":"none","padding":"32px 0","textAlign":"center","background":"transparent","border":"none"}}
          >
            <p className="empty-message" style={{"color":"var(--muted)","fontSize":"0.95rem"}}>
              No payment history available yet.
            </p>
          </div>

          
          <div
            id="paymentHistoryError"
            role="alert"
            aria-live="polite"
            style={{"display":"none","padding":"16px","border":"1px solid var(--red)","borderRadius":"var(--rs)","background":"rgba(220,38,38,0.08)","color":"var(--red-l)","fontSize":"0.9rem"}}
          >
            <span id="paymentHistoryErrorMessage">Unable to load payment history.</span>
            <button type="button" className="btn-institution-outline" id="paymentHistoryRetryBtn" style={{"marginLeft":"12px"}}>
              Retry
            </button>
          </div>

          
          <div className="responsive-table-wrapper" id="paymentHistoryWrapper" style={{"display":"none"}}>
            
            <table className="billing-tbl" aria-describedby="paymentHistoryHeading">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Amount</th>
                  <th>Plan</th>
                  <th>Status</th>
                  <th>Transaction ID</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody id="paymentHistoryBody">
              </tbody>
            </table>
          </div>
        </div>
      </section>
    </div>
  </main>

  
  
  
  
  
  
  

    </>
  );
};

export default InstitutionSubscription;
