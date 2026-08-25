import React from 'react';
import { Link } from 'react-router-dom';

const InstitutionPricing = () => {
  return (
    <>
      {/* Auto-injected styles from HTML head */}
      <style dangerouslySetInnerHTML={{ __html: `
    /* ── Page base ── */
    body { min-height:100vh; }

    /* ── Hero ── */
    .ph { text-align:center;padding:52px 20px 32px; }
    .ph h1 { font-size:2.4rem;font-weight:900;margin:0 0 10px;line-height:1.15; }
    .ph p  { color:var(--muted);font-size:1rem;margin:0; }
    .ph .grad { background:linear-gradient(90deg,#a78bfa,#60a5fa);-webkit-background-clip:text;-webkit-text-fill-color:transparent; }

    /* ── Grid ── */
    .pg { display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:24px;max-width:1200px;margin:0 auto 60px;padding:0 24px; }
    @media(max-width:640px){ .pg { grid-template-columns:1fr; } }
    @media(min-width:1000px){ .pg { grid-template-columns:repeat(4,1fr); } }

    /* ── Card ── */
    .pc { background:var(--card-bg);border:1px solid var(--border);border-radius:16px;padding:32px 24px;display:flex;flex-direction:column;gap:0;position:relative;transition:transform .15s,box-shadow .15s,border-color .18s; }
    .pc:hover { transform:translateY(-4px);box-shadow:0 16px 40px rgba(0,0,0,.32); }
    .pc.featured { border-color:var(--purple-l,#a78bfa);box-shadow:0 0 0 1px var(--purple-l,#a78bfa),0 8px 28px rgba(124,58,237,.18); }

    .pc-badge { position:absolute;top:-13px;left:50%;transform:translateX(-50%);background:linear-gradient(90deg,#a78bfa,#60a5fa);color:#fff;font-size:.72rem;font-weight:800;padding:4px 16px;border-radius:20px;white-space:nowrap;letter-spacing:.02em; }
    .pc-premium-badge { background:linear-gradient(90deg,#fbbf24,#f59e0b); }

    .pc-name { font-size:1.15rem;font-weight:800;margin-bottom:4px;color:var(--text); }
    .pc-tagline { font-size:.8rem;color:var(--muted);margin-bottom:20px;min-height:32px;line-height:1.4; }

    .pc-price { margin-bottom:6px;display:flex;align-items:baseline;gap:2px; }
    .pc-price .amt  { font-size:2.8rem;font-weight:900;line-height:1;color:var(--text); }
    .pc-price .sym  { font-size:1.4rem;font-weight:700;vertical-align:super;color:var(--text); }
    .pc-price .per  { font-size:.82rem;color:var(--muted);margin-left:4px; }
    .pc-price .contact { font-size:1.2rem;color:var(--muted);font-weight:600; }
    
    .pc-save { font-size:.75rem;font-weight:700;color:var(--green-l);background:rgba(5,150,105,.15);padding:2px 10px;border-radius:12px;display:inline-block;margin-bottom:18px; }
    .pc-nosave { height:22px;margin-bottom:18px; }

    .pc-feats { list-style:none;margin:0 0 24px;padding:0;flex:1;display:flex;flex-direction:column;gap:12px; }
    .pc-feats li { display:flex;align-items:flex-start;gap:10px;font-size:.88rem;line-height:1.4;color:var(--text); }
    .pc-feats li .ic { flex-shrink:0;margin-top:2px;font-size:.9rem;color:var(--purple-l); }

    .pc-cta { width:100%;padding:13px;border-radius:10px;font-size:.92rem;font-weight:700;cursor:pointer;border:none;transition:opacity .15s,transform .12s,background .15s;margin-top:auto; }
    .pc-cta:hover:not(:disabled) { opacity:.88;transform:translateY(-1px); }
    .pc-cta.primary { background:linear-gradient(135deg,#a78bfa,#6366f1);color:#fff;box-shadow:0 4px 16px rgba(124,58,237,.3); }
    .pc-cta.secondary { background:transparent;border:1px solid var(--border);color:var(--text);transition:all .15s; }
    .pc-cta.secondary:hover { background:var(--s2);border-color:var(--purple-l); }
    .pc-cta.contact { background:transparent;border:2px solid var(--purple-l);color:var(--purple-l);font-weight:700; }
    .pc-cta.contact:hover { background:rgba(167,139,250,.1); }
    .pc-cta.current { background:rgba(5,150,105,.15);border:1px solid rgba(5,150,105,.35);color:var(--green-l);cursor:default; }
    .pc-cta:disabled { cursor:not-allowed;opacity:.6; }

    /* ── Pay modal ── */
    .pmo { display:none;position:fixed;inset:0;background:rgba(0,0,0,.78);z-index:1000;align-items:center;justify-content:center; }
    .pmd { background:var(--card-bg);border:1px solid var(--border);border-radius:16px;padding:36px;max-width:460px;width:90%;position:relative; }
    .pmd h3 { font-size:1.25rem;font-weight:800;margin:0 0 4px; }
    .pmd .pmo-sub { color:var(--muted);font-size:.85rem;margin-bottom:16px; }
    .pmo-amt { font-size:2.6rem;font-weight:900;color:var(--purple-l,#a78bfa);margin-bottom:20px; }
    .pmo-methods { display:flex;flex-wrap:wrap;gap:8px;margin-bottom:20px; }
    .pm-badge { padding:5px 13px;border-radius:20px;font-size:.75rem;font-weight:600;background:var(--s2);border:1px solid var(--border);color:var(--muted2); }
    .pmo-status { display:none;padding:12px 16px;border-radius:10px;font-size:.87rem;margin-bottom:14px; }
    .pmo-actions { display:flex;gap:10px; }
    .pmo-close { position:absolute;top:18px;right:18px;background:none;border:none;color:var(--muted);cursor:pointer;font-size:1.3rem;line-height:1; }

    /* ── Test panel ── */
    #testPanel { background:rgba(217,119,6,0.08);border:1px solid rgba(217,119,6,0.3);border-radius:12px;padding:14px 18px; }
    #testPanel h4 { color:#d97706;font-size:.9rem;font-weight:700;margin:0 0 8px; }
    #testPanel .tp-row { display:grid;grid-template-columns:1fr 1fr;gap:16px;font-size:.8rem;margin-bottom:8px; }
    #testPanel .tp-row:last-child { margin-bottom:0; }
    #testPanel code { background:rgba(0,0,0,.2);padding:2px 6px;border-radius:4px;font-family:monospace;color:var(--green-l);font-weight:600; }
  
` }} />
      
  <div className="bg-mesh"></div>

  

  <main>
    
    <div className="ph">
      <h1>Empower Your <span className="grad">Institution</span></h1>
      <p>Simple, transparent pricing. Everything your institution needs to excel at KCET.</p>
    </div>

    
    <div id="testPanel" style={{"display":"none","maxWidth":"1060px","margin":"0 auto 24px","padding":"0 24px"}}>
      <h4>🧪 TEST MODE — DEMO PAYMENT CREDENTIALS</h4>
      <div className="tp-row">
        <div>
          <strong>Test Card (Domestic)</strong><br/>
          Number: <code>4111 1111 8199 5449</code><br/>
          Expiry: any future date (e.g. 12/25)<br/>
          CVV: any 3 digits (e.g. 123)<br/>
          Name: anything (e.g. Test User)
        </div>
        <div>
          <strong>Test UPI</strong><br/>
          Success: <code>success@razorpay</code><br/>
          Failure: <code>failure@razorpay</code>
        </div>
      </div>
      <div className="tp-row">
        <div style={{"gridColumn":"1/-1"}}>
          <strong style={{"color":"#d97706"}}>⚠️ Important</strong><br/>
          Do NOT use real cards — use test credentials above
        </div>
      </div>
    </div>

    
    <div className="pg" id="plansGrid">
      
      <div style={{"gridColumn":"1/-1","textAlign":"center","padding":"40px","color":"var(--muted)"}}>Loading pricing plans...</div>
    </div>

    
    <div style={{"textAlign":"center","color":"var(--muted)","fontSize":".85rem","marginBottom":"40px","padding":"0 24px"}}>
      All plans include 24/7 platform access · Monthly billing · Cancel anytime
    </div>
  </main>

  
  <div id="payModal" className="pmo">
    <div className="pmd">
      <button className="pmo-close" >✕</button>
      <h3 id="payModalTitle">Institution Starter</h3>
      <p className="pmo-sub" id="payModalSub">Institution Starter · monthly billing</p>
      <div className="pmo-amt" id="payModalAmt">₹1,499/month</div>
      <div className="pmo-methods">
        <div className="pm-badge">💳 Razorpay Secure</div>
      </div>
      <div className="pmo-status" id="payStatus"></div>
      <div className="pmo-actions">
        <button className="pc-cta secondary"  style={{"flex":"1"}}>Cancel</button>
        <button className="pc-cta primary" id="payNowBtn"  style={{"flex":"2"}}>Pay Now →</button>
      </div>
      <p style={{"fontSize":".72rem","color":"var(--muted)","textAlign":"center","marginTop":"14px"}}>🔒 Secured by Razorpay · Payment data is never stored here</p>
    </div>
  </div>

  
  

    </>
  );
};

export default InstitutionPricing;
