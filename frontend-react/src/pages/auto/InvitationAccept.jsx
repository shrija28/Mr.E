import React from 'react';
import { Link } from 'react-router-dom';

const InvitationAccept = () => {
  return (
    <>
      {/* Auto-injected styles from HTML head */}
      <style dangerouslySetInnerHTML={{ __html: `` }} />
      
  <div className="bg-mesh"></div>

  
  

  
  <main style={{"display":"flex","alignItems":"center","justifyContent":"center","minHeight":"calc(100vh - 60px)","padding":"20px"}}>
    <section className="section-card" style={{"maxWidth":"520px","width":"100%","padding":"32px"}} aria-labelledby="invitationTitle">
      <h1 id="invitationTitle" style={{"marginBottom":"8px"}}>Institution Invitation</h1>
      <p className="input-label" style={{"marginBottom":"24px","textTransform":"none","fontSize":"0.9rem"}}>
        Review the invitation details below and choose to accept or decline.
      </p>

      
      <div
        id="invitationError"
        role="alert"
        aria-live="polite"
        style={{"display":"none","background":"rgba(220,38,38,0.1)","border":"1px solid var(--red)","borderRadius":"var(--rs)","padding":"10px 14px","marginBottom":"16px","fontSize":"0.85rem","color":"var(--red-l)"}}
      ></div>

      
      <div
        id="invitationLoading"
        role="status"
        aria-live="polite"
        style={{"textAlign":"center","padding":"24px 0","color":"var(--muted)","fontSize":"0.9rem"}}
      >
        Loading invitation details…
      </div>

      
      <section
        id="invitationDetails"
        style={{"display":"none"}}
        aria-labelledby="invitationDetailsHeading"
      >
        <h2 id="invitationDetailsHeading" className="visually-hidden">
          Invitation Details
        </h2>

        
        <div className="input-group" style={{"marginBottom":"16px"}}>
          <span className="input-label" id="institutionNameLabel">Institution</span>
          <p
            id="institutionName"
            aria-labelledby="institutionNameLabel"
            style={{"fontSize":"1.1rem","fontWeight":"600","color":"var(--text)","margin":"0"}}
          >—</p>
        </div>

        
        <div className="input-group" style={{"marginBottom":"16px"}}>
          <span className="input-label" id="invitationExpiryLabel">Invitation Expires</span>
          <p
            id="invitationExpiry"
            aria-labelledby="invitationExpiryLabel"
            style={{"fontSize":"0.95rem","color":"var(--text)","margin":"0"}}
          >—</p>
        </div>

        
        <div className="input-group" style={{"marginBottom":"24px"}}>
          <span className="input-label" id="invitationBenefitsLabel">What You'll Get</span>
          <ul
            id="invitationBenefits"
            aria-labelledby="invitationBenefitsLabel"
            style={{"margin":"8px 0 0","paddingLeft":"20px","color":"var(--text)","fontSize":"0.9rem","lineHeight":"1.6"}}
          >
            <li>Access to your institution's curated exams</li>
            <li>Personalized analytics and progress tracking</li>
            <li>Coverage under your institution's subscription</li>
          </ul>
        </div>

        
        <div style={{"display":"flex","gap":"12px","flexWrap":"wrap"}}>
          <button
            type="button"
            id="acceptBtn"
            className="btn-primary"
            aria-describedby="invitationBenefitsLabel"
            style={{"flex":"1","minWidth":"140px","justifyContent":"center"}}
          >
            Accept Invitation
          </button>
          <button
            type="button"
            id="declineBtn"
            className="btn-outline"
            style={{"flex":"1","minWidth":"140px","justifyContent":"center"}}
          >
            Decline
          </button>
        </div>
      </section>

      
      <div id="invitationRetry" style={{"display":"none","textAlign":"center","marginTop":"16px"}}>
        <button type="button" id="retryBtn" className="btn-secondary" aria-label="Retry loading invitation details" style={{"justifyContent":"center"}}>
          Retry
        </button>
      </div>
    </section>
  </main>

  
  
  
  
  
  
  
  
  

    </>
  );
};

export default InvitationAccept;
