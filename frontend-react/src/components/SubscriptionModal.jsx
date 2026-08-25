import React from 'react';
import { Link } from 'react-router-dom';

const SubscriptionModal = ({ isOpen, onClose }) => {
  if (!isOpen) return null;

  return (
    <>
      

<div id="subscriptionModal" className="modal-overlay" style={{ display: isOpen ? "flex" : "none" }} role="dialog" aria-labelledby="modalTitle" aria-describedby="modalSubtitle" aria-modal="true" aria-hidden="true">
  <div className="modal-dialog subscription-modal">
    <div className="modal-header">
      <div className="modal-header-content">
        <h2 id="modalTitle" className="modal-title">Choose Your <span className="grad">Plan</span></h2>
        <p id="modalSubtitle" className="modal-subtitle">Select the plan that best fits your exam preparation needs</p>
      </div>
      <button className="modal-close" aria-label="Close plan selection dialog" type="button">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
          <line x1="18" y1="6" x2="6" y2="18"/>
          <line x1="6" y1="6" x2="18" y2="18"/>
        </svg>
      </button>
    </div>
    
    <div className="modal-body">
      <div className="modal-plan-grid">
        
        <div className="pc" data-plan="free">
          <div className="pc-name">Free</div>
          <div className="pc-tagline">Start your KCET journey for free</div>
          <div className="pc-price"><span className="sym">₹</span><span className="amt">0</span><span className="per">/mo</span></div>
          <div className="pc-nosave"></div>
          <ul className="pc-feats">
            <li className="yes"><span className="ic">✅</span><span>3–5 mock tests</span></li>
            <li className="yes"><span className="ic">✅</span><span>Limited question bank access</span></li>
            <li className="yes"><span className="ic">✅</span><span>Basic score analytics</span></li>
            <li className="no"><span className="ic">❌</span><span>Unlimited mock tests</span></li>
            <li className="no"><span className="ic">❌</span><span>Full topic analytics</span></li>
            <li className="no"><span className="ic">❌</span><span>AI recommendations</span></li>
            <li className="no"><span className="ic">❌</span><span>Weak-topic analysis</span></li>
          </ul>
          <button className="pc-cta outline" type="button" data-action="select-free" aria-label="Start with Free Plan">Start Free</button>
        </div>
        
        
        <div className="pc" data-plan="trial">
          <div className="pc-badge pc-trial-badge">Most Popular</div>
          <div className="pc-name">7-Day Premium Trial</div>
          <div className="pc-tagline">7 days of full premium access — ₹99</div>
          <div className="pc-price"><span className="sym">₹</span><span className="amt">99</span></div>
          <div className="pc-nosave"></div>
          <ul className="pc-feats">
            <li className="yes"><span className="ic">✅</span><span>Unlimited mock tests</span></li>
            <li className="yes"><span className="ic">✅</span><span>KCET premium question bank</span></li>
            <li className="yes"><span className="ic">✅</span><span>Topic-wise analytics</span></li>
            <li className="yes"><span className="ic">✅</span><span>Weak-topic analysis</span></li>
            <li className="yes"><span className="ic">✅</span><span>AI recommendations</span></li>
            <li className="yes"><span className="ic">✅</span><span>Performance reports</span></li>
            <li className="yes"><span className="ic">✅</span><span>Leaderboard ranking</span></li>
          </ul>
          <button className="pc-cta trial" type="button" data-action="select-trial" data-plan-id="" aria-label="Start 7-Day Premium Trial for ₹99">Start 7-Day Trial — ₹99</button>
        </div>
        
        
        <div className="pc featured" data-plan="monthly">
          <div className="pc-badge">⭐ Best Value</div>
          <div className="pc-name">Pro Monthly</div>
          <div className="pc-tagline">Full premium access, billed monthly</div>
          <div className="pc-price"><span className="sym">₹</span><span className="amt">349</span><span className="per">/month</span></div>
          <div className="pc-nosave"></div>
          <ul className="pc-feats">
            <li className="yes"><span className="ic">✅</span><span>Unlimited mock tests</span></li>
            <li className="yes"><span className="ic">✅</span><span>KCET premium question bank</span></li>
            <li className="yes"><span className="ic">✅</span><span>Topic-wise analytics</span></li>
            <li className="yes"><span className="ic">✅</span><span>Weak-topic analysis</span></li>
            <li className="yes"><span className="ic">✅</span><span>AI recommendations</span></li>
            <li className="yes"><span className="ic">✅</span><span>Performance reports</span></li>
            <li className="yes"><span className="ic">✅</span><span>Leaderboard ranking + medals</span></li>
          </ul>
          <button className="pc-cta primary" type="button" data-action="select-monthly" data-plan-id="" aria-label="Subscribe to Pro Monthly for ₹349/month">Subscribe Monthly</button>
        </div>
        
        
        <div className="pc" data-plan="yearly">
          <div className="pc-name">Pro Yearly</div>
          <div className="pc-tagline">Best value — save ₹1189 vs monthly</div>
          <div className="pc-price"><span className="sym">₹</span><span className="amt">2,999</span><span className="per">/year</span></div>
          <div className="pc-save">Save ₹1,189/year</div>
          <ul className="pc-feats">
            <li className="yes"><span className="ic">✅</span><span>Everything in Pro Monthly</span></li>
            <li className="yes"><span className="ic">✅</span><span>12 months full access</span></li>
            <li className="yes"><span className="ic">✅</span><span>Unlimited mock tests</span></li>
            <li className="yes"><span className="ic">✅</span><span>KCET premium question bank</span></li>
            <li className="yes"><span className="ic">✅</span><span>AI recommendations</span></li>
            <li className="yes"><span className="ic">✅</span><span>Advanced performance reports</span></li>
            <li className="yes"><span className="ic">✅</span><span>Priority feature access</span></li>
          </ul>
          <button className="pc-cta primary" type="button" data-action="select-yearly" data-plan-id="" aria-label="Subscribe to Pro Yearly for ₹2,999/year">Subscribe Yearly</button>
        </div>
      </div>
      
      
      <div className="modal-error" id="modalError" role="alert" aria-live="polite" style={{ display: isOpen ? "flex" : "none" }}>
        <svg className="error-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
          <circle cx="12" cy="12" r="10"/>
          <line x1="12" y1="8" x2="12" y2="12"/>
          <line x1="12" y1="16" x2="12.01" y2="16"/>
        </svg>
        <div className="error-content">
          <p className="error-message" id="errorMessage"></p>
          <button className="btn-retry" type="button" style={{ display: isOpen ? "flex" : "none" }} aria-label="Retry the previous action">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
              <polyline points="23 4 23 10 17 10"/>
              <path d="M20.49 15a9 9 0 11-2.12-9.36L23 10"/>
            </svg>
            Retry
          </button>
        </div>
      </div>
      
      
      <div className="modal-loading" id="modalLoading" style={{ display: isOpen ? "flex" : "none" }} role="status" aria-live="polite">
        <div className="spinner" aria-hidden="true"></div>
        <p>Processing your selection...</p>
      </div>
    </div>
  </div>
</div>

    </>
  );
};

export default SubscriptionModal;
