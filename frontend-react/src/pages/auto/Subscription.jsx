import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

const Subscription = () => {
  const [loading, setLoading] = useState(true);
  const [currentPlan, setCurrentPlan] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [processingPlan, setProcessingPlan] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    // Simulate loading the current subscription status
    setTimeout(() => {
      // Set to null to simulate no active subscription
      setCurrentPlan(null);
      setLoading(false);
    }, 800);
  }, []);

  const handleSubscribe = (planId) => {
    setProcessingPlan(planId);
    setTimeout(() => {
      setProcessingPlan(null);
      setIsModalOpen(false);
      setCurrentPlan({
        name: planId,
        status: 'Active',
        started: new Date().toLocaleDateString(),
        renewal: new Date(Date.now() + 30*24*60*60*1000).toLocaleDateString()
      });
      alert(`Success! You have successfully subscribed to the ${planId} plan.`);
    }, 1500);
  };

  return (
    <>
      <main className="main-wrap">
        {/* Page Header */}
        <div className="dash-hero">
          <div>
            <h1 className="dash-title">Subscription <span className="hero-gradient">Management</span></h1>
            <p className="dash-sub">Manage your subscription plan, billing, and payment details</p>
          </div>
        </div>

        {/* Loading State */}
        {loading && (
          <div className="loading-state" role="status" aria-live="polite">
            <div className="loading-spinner" aria-hidden="true"></div>
            <p>Loading subscription details...</p>
          </div>
        )}

        {/* No Subscription State */}
        {!loading && !currentPlan && (
          <section className="empty-state" aria-labelledby="noSubHeading">
            <div className="empty-icon" aria-hidden="true">💳</div>
            <h3 id="noSubHeading">No Active Subscription</h3>
            <p>Choose a plan to start taking exams and track your progress.</p>
            <div className="empty-actions">
              <button className="btn-primary" onClick={() => setIsModalOpen(true)}>Choose a Plan →</button>
            </div>
          </section>
        )}

        {/* Subscription Content */}
        {!loading && currentPlan && (
          <div id="subscriptionContent">
            <section className="section-card subscription-plan-card" aria-labelledby="currentPlanHeading">
              <div className="section-card-header">
                <div className="section-icon purple" aria-hidden="true">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
                </div>
                <div>
                  <h2 id="currentPlanHeading">Current Plan</h2>
                  <p className="section-sub">Your active subscription details</p>
                </div>
              </div>
              
              <div className="section-body">
                <div className="plan-details-grid">
                  <div className="plan-detail-item">
                    <div className="plan-detail-label">Plan</div>
                    <div className="plan-detail-value">{currentPlan.name}</div>
                  </div>
                  <div className="plan-detail-item">
                    <div className="plan-detail-label">Status</div>
                    <div className="plan-status-badge active" style={{ background: 'var(--green-l)', color: '#fff', padding: '4px 12px', borderRadius: '12px', fontSize: '0.8rem', fontWeight: 'bold' }}>{currentPlan.status}</div>
                  </div>
                  <div className="plan-detail-item">
                    <div className="plan-detail-label">Started</div>
                    <div className="plan-detail-value">{currentPlan.started}</div>
                  </div>
                  <div className="plan-detail-item">
                    <div className="plan-detail-label">Next Renewal</div>
                    <div className="plan-detail-value">{currentPlan.renewal}</div>
                  </div>
                </div>

                <div className="plan-actions" style={{ marginTop: '24px', display: 'flex', gap: '16px' }}>
                  <button className="btn-outline" onClick={() => setIsModalOpen(true)}>Change Plan</button>
                </div>
              </div>
            </section>
            
            <section className="section-card" style={{ marginTop: '24px' }}>
              <div className="section-card-header">
                <div className="section-icon blue" aria-hidden="true">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
                </div>
                <div>
                  <h2>Billing History</h2>
                  <p className="section-sub">Your past transactions and invoices</p>
                </div>
              </div>
              <div className="section-body" style={{ padding: '24px', textAlign: 'center', color: 'var(--muted)' }}>
                No billing history available yet.
              </div>
            </section>
          </div>
        )}
      </main>

      {/* Plan Selection Modal Overlay */}
      {isModalOpen && (
        <div className="modal-overlay" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', position: 'fixed', top: 0, left: 0, width: '100%', height: '100%', background: 'rgba(0,0,0,0.7)', zIndex: 9999 }}>
          <div className="modal-dialog subscription-modal" style={{ background: 'var(--bg)', borderRadius: '24px', width: '90%', maxWidth: '1200px', maxHeight: '90vh', overflowY: 'auto' }}>
            <div className="modal-header" style={{ padding: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid var(--border)' }}>
              <div>
                <h2 className="modal-title" style={{ fontSize: '1.8rem', margin: 0 }}>Choose Your <span className="hero-gradient">Plan</span></h2>
                <p className="modal-subtitle" style={{ color: 'var(--muted)', margin: '4px 0 0 0' }}>Select the plan that best fits your exam preparation needs</p>
              </div>
              <button 
                className="modal-close" 
                style={{ background: 'transparent', border: 'none', color: 'var(--text)', cursor: 'pointer' }}
                onClick={() => setIsModalOpen(false)}
              >
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="24" height="24">
                  <line x1="18" y1="6" x2="6" y2="18"/>
                  <line x1="6" y1="6" x2="18" y2="18"/>
                </svg>
              </button>
            </div>
            
            <div className="modal-body" style={{ padding: '32px' }}>
              <div className="modal-plan-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '24px' }}>
                
                {/* Free Plan Card */}
                <div className="pc" data-plan="free" style={{ background: 'var(--s1)', borderRadius: '16px', padding: '24px', border: '1px solid var(--border)', display: 'flex', flexDirection: 'column' }}>
                  <div className="pc-name" style={{ fontSize: '1.4rem', fontWeight: 'bold' }}>Free</div>
                  <div className="pc-tagline" style={{ color: 'var(--muted)', fontSize: '0.9rem', marginBottom: '16px' }}>Start your KCET journey</div>
                  <div className="pc-price" style={{ fontSize: '2rem', fontWeight: 'bold', marginBottom: '24px' }}>₹0<span style={{ fontSize: '1rem', color: 'var(--muted)' }}>/mo</span></div>
                  
                  <ul className="pc-feats" style={{ listStyle: 'none', padding: 0, margin: '0 0 24px 0', flex: 1 }}>
                    <li style={{ marginBottom: '12px' }}>✅ 3–5 mock tests</li>
                    <li style={{ marginBottom: '12px' }}>✅ Limited question bank</li>
                    <li style={{ marginBottom: '12px', color: 'var(--muted)' }}>❌ Unlimited mock tests</li>
                    <li style={{ marginBottom: '12px', color: 'var(--muted)' }}>❌ Topic-wise analytics</li>
                  </ul>
                  
                  <button 
                    className="btn-outline" 
                    style={{ width: '100%', justifyContent: 'center' }}
                    onClick={() => handleSubscribe('Free')}
                    disabled={processingPlan !== null}
                  >
                    {processingPlan === 'Free' ? 'Processing...' : 'Start Free'}
                  </button>
                </div>

                {/* 7-Day Trial Card */}
                <div className="pc" data-plan="trial" style={{ background: 'var(--s1)', borderRadius: '16px', padding: '24px', border: '1px solid var(--purple)', position: 'relative', display: 'flex', flexDirection: 'column' }}>
                  <div style={{ position: 'absolute', top: 0, left: '50%', transform: 'translate(-50%, -50%)', background: 'var(--orange)', color: '#fff', padding: '4px 12px', borderRadius: '12px', fontSize: '0.8rem', fontWeight: 'bold' }}>Most Popular</div>
                  <div className="pc-name" style={{ fontSize: '1.4rem', fontWeight: 'bold' }}>7-Day Trial</div>
                  <div className="pc-tagline" style={{ color: 'var(--muted)', fontSize: '0.9rem', marginBottom: '16px' }}>7 days full access</div>
                  <div className="pc-price" style={{ fontSize: '2rem', fontWeight: 'bold', marginBottom: '24px' }}>₹99</div>
                  
                  <ul className="pc-feats" style={{ listStyle: 'none', padding: 0, margin: '0 0 24px 0', flex: 1 }}>
                    <li style={{ marginBottom: '12px' }}>✅ Unlimited mock tests</li>
                    <li style={{ marginBottom: '12px' }}>✅ Full question bank</li>
                    <li style={{ marginBottom: '12px' }}>✅ Topic-wise analytics</li>
                    <li style={{ marginBottom: '12px' }}>✅ AI recommendations</li>
                  </ul>
                  
                  <button 
                    className="btn-primary" 
                    style={{ width: '100%', justifyContent: 'center', background: 'var(--orange)', borderColor: 'var(--orange)' }}
                    onClick={() => handleSubscribe('7-Day Trial')}
                    disabled={processingPlan !== null}
                  >
                    {processingPlan === '7-Day Trial' ? 'Processing...' : 'Start Trial — ₹99'}
                  </button>
                </div>

                {/* Pro Monthly */}
                <div className="pc" data-plan="monthly" style={{ background: 'var(--s1)', borderRadius: '16px', padding: '24px', border: '1px solid var(--purple)', display: 'flex', flexDirection: 'column' }}>
                  <div className="pc-name" style={{ fontSize: '1.4rem', fontWeight: 'bold' }}>Pro Monthly</div>
                  <div className="pc-tagline" style={{ color: 'var(--muted)', fontSize: '0.9rem', marginBottom: '16px' }}>Billed monthly</div>
                  <div className="pc-price" style={{ fontSize: '2rem', fontWeight: 'bold', marginBottom: '24px' }}>₹349<span style={{ fontSize: '1rem', color: 'var(--muted)' }}>/mo</span></div>
                  
                  <ul className="pc-feats" style={{ listStyle: 'none', padding: 0, margin: '0 0 24px 0', flex: 1 }}>
                    <li style={{ marginBottom: '12px' }}>✅ Unlimited mock tests</li>
                    <li style={{ marginBottom: '12px' }}>✅ Full question bank</li>
                    <li style={{ marginBottom: '12px' }}>✅ Topic-wise analytics</li>
                    <li style={{ marginBottom: '12px' }}>✅ AI recommendations</li>
                  </ul>
                  
                  <button 
                    className="btn-primary" 
                    style={{ width: '100%', justifyContent: 'center' }}
                    onClick={() => handleSubscribe('Pro Monthly')}
                    disabled={processingPlan !== null}
                  >
                    {processingPlan === 'Pro Monthly' ? 'Processing...' : 'Subscribe Monthly'}
                  </button>
                </div>

                {/* Pro Yearly */}
                <div className="pc" data-plan="yearly" style={{ background: 'var(--s1)', borderRadius: '16px', padding: '24px', border: '1px solid var(--border)', display: 'flex', flexDirection: 'column' }}>
                  <div className="pc-name" style={{ fontSize: '1.4rem', fontWeight: 'bold' }}>Pro Yearly</div>
                  <div className="pc-tagline" style={{ color: 'var(--muted)', fontSize: '0.9rem', marginBottom: '16px' }}>Save ₹1,189 vs monthly</div>
                  <div className="pc-price" style={{ fontSize: '2rem', fontWeight: 'bold', marginBottom: '24px' }}>₹2,999<span style={{ fontSize: '1rem', color: 'var(--muted)' }}>/yr</span></div>
                  
                  <ul className="pc-feats" style={{ listStyle: 'none', padding: 0, margin: '0 0 24px 0', flex: 1 }}>
                    <li style={{ marginBottom: '12px' }}>✅ All Pro features</li>
                    <li style={{ marginBottom: '12px' }}>✅ 12 months full access</li>
                    <li style={{ marginBottom: '12px' }}>✅ Priority support</li>
                  </ul>
                  
                  <button 
                    className="btn-primary" 
                    style={{ width: '100%', justifyContent: 'center' }}
                    onClick={() => handleSubscribe('Pro Yearly')}
                    disabled={processingPlan !== null}
                  >
                    {processingPlan === 'Pro Yearly' ? 'Processing...' : 'Subscribe Yearly'}
                  </button>
                </div>

              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default Subscription;
