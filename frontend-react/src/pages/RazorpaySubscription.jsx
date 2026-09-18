import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';

const loadRazorpay = () => new Promise((resolve, reject) => {
  if (window.Razorpay) {
    resolve(window.Razorpay);
    return;
  }

  const script = document.createElement('script');
  script.src = 'https://checkout.razorpay.com/v1/checkout.js';
  script.onload = () => resolve(window.Razorpay);
  script.onerror = () => reject(new Error('Could not load Razorpay Checkout.'));
  document.body.appendChild(script);
});

const apiRequest = async (url, options = {}) => {
  const token = localStorage.getItem('token');
  const response = await fetch(url, {
    ...options,
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(options.headers || {}),
    },
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = data?.detail;
    const message = typeof detail === 'string' ? detail : detail?.message || data?.message;
    throw new Error(message || `Request failed (${response.status}).`);
  }
  return data;
};

const planDetails = {
  Free: { key: 'free', tagline: 'Start your KCET journey for free', price: '0', period: '/mo', features: [['yes', '3–5 mock tests'], ['yes', 'Limited question bank access'], ['yes', 'Basic score analytics'], ['no', 'Unlimited mock tests'], ['no', 'Full topic analytics'], ['no', 'AI recommendations'], ['no', 'Weak-topic analysis']] },
  '7-Day Premium Trial': { key: 'trial', tagline: '7 days of full premium access — ₹99', price: '99', features: [['yes', 'Unlimited mock tests'], ['yes', 'KCET premium question bank'], ['yes', 'Topic-wise analytics'], ['yes', 'Weak-topic analysis'], ['yes', 'AI recommendations'], ['yes', 'Performance reports'], ['yes', 'Leaderboard ranking']] },
  'Pro Monthly': { key: 'monthly', tagline: 'Full premium access, billed monthly', price: '349', period: '/month', featured: true, features: [['yes', 'Unlimited mock tests'], ['yes', 'KCET premium question bank'], ['yes', 'Topic-wise analytics'], ['yes', 'Weak-topic analysis'], ['yes', 'AI recommendations'], ['yes', 'Performance reports'], ['yes', 'Leaderboard ranking + medals']] },
  'Pro Yearly': { key: 'yearly', tagline: 'Best value — save ₹1189 vs monthly', price: '2,999', period: '/year', save: 'Save ₹1,189/year', features: [['yes', 'Everything in Pro Monthly'], ['yes', '12 months full access'], ['yes', 'Unlimited mock tests'], ['yes', 'KCET premium question bank'], ['yes', 'AI recommendations'], ['yes', 'Advanced performance reports'], ['yes', 'Priority feature access']] },
};

const RazorpaySubscription = () => {
  const navigate = useNavigate();
  const [plans, setPlans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(null);
  const [message, setMessage] = useState(null);

  useEffect(() => {
    apiRequest('/api/payments/plans/student')
      .then((data) => setPlans(data.plans || []))
      .catch((error) => setMessage({ type: 'error', text: error.message }))
      .finally(() => setLoading(false));
  }, []);

  const startPayment = async (plan) => {
    if (!plan) return;
    if (plan.price <= 0) {
      setMessage({ type: 'success', text: 'Free plan selected.' });
      return;
    }
    setProcessing(plan.id);
    setMessage(null);

    try {
      const order = await apiRequest('/api/payments/create-order', {
        method: 'POST',
        body: JSON.stringify({ plan_id: plan.id }),
      });
      const Razorpay = await loadRazorpay();

      const checkout = new Razorpay({
        key: order.key_id,
        amount: order.amount,
        currency: order.currency,
        name: 'VyasaPrep',
        description: order.description,
        order_id: order.order_id,
        prefill: order.prefill,
        handler: async (payment) => {
          try {
            await apiRequest('/api/payments/verify', {
              method: 'POST',
              body: JSON.stringify({
                razorpay_order_id: payment.razorpay_order_id,
                razorpay_payment_id: payment.razorpay_payment_id,
                razorpay_signature: payment.razorpay_signature,
                plan_id: plan.id,
              }),
            });
            navigate('/dashboard', {
              replace: true,
              state: { paymentSuccess: true, planName: plan.name },
            });
          } catch (error) {
            setMessage({ type: 'error', text: error.message });
          } finally {
            setProcessing(null);
          }
        },
        modal: { ondismiss: () => setProcessing(null) },
        theme: { color: '#7c3aed' },
      });

      checkout.on('payment.failed', () => {
        setMessage({ type: 'error', text: 'Payment failed. Please try again.' });
        setProcessing(null);
      });
      checkout.open();
    } catch (error) {
      setMessage({ type: 'error', text: error.message });
      setProcessing(null);
    }
  };

  const choosePlan = (name) => startPayment(plans.find((plan) => plan.name === name));

  return (
    <div className="modal-overlay" style={{ display: 'flex' }} role="dialog" aria-modal="true" aria-labelledby="modalTitle">
      <div className="modal-dialog subscription-modal">
        <div className="modal-header">
          <div className="modal-header-content">
            <h2 id="modalTitle" className="modal-title">Choose Your <span className="grad">Plan</span></h2>
            <p className="modal-subtitle">Select the plan that best fits your exam preparation needs</p>
          </div>
        </div>
        <div className="modal-body">
          {loading && <div className="modal-loading" style={{ display: 'flex' }} role="status"><div className="spinner" /><p>Loading plans...</p></div>}
          {!loading && !plans.length && <div className="modal-error" style={{ display: 'flex' }} role="alert"><p className="error-message">{message?.text || message || 'No subscription plans are available.'}</p></div>}
          {!loading && plans.length > 0 && <div className="modal-plan-grid">
            {Object.entries(planDetails).map(([name, details]) => {
              const plan = plans.find((item) => item.name === name);
              return <div className={`pc${details.featured ? ' featured' : ''}`} data-plan={details.key} key={name}>
                {name === '7-Day Premium Trial' && <div className="pc-badge pc-trial-badge">Most Popular</div>}
                {details.featured && <div className="pc-badge">⭐ Best Value</div>}
                <div className="pc-name">{name}</div>
                <div className="pc-tagline">{details.tagline}</div>
                <div className="pc-price"><span className="sym">₹</span><span className="amt">{details.price}</span>{details.period && <span className="per">{details.period}</span>}</div>
                {details.save ? <div className="pc-save">{details.save}</div> : <div className="pc-nosave" />}
                <ul className="pc-feats">{details.features.map(([kind, text]) => <li className={kind} key={text}><span className="ic">{kind === 'yes' ? '✅' : '❌'}</span><span>{text}</span></li>)}</ul>
                <button className={`pc-cta ${details.key === 'trial' ? 'trial' : details.key === 'free' ? 'outline' : 'primary'}`} type="button" disabled={!plan || processing !== null} onClick={() => choosePlan(name)}>
                  {processing === plan?.id ? 'Opening checkout...' : details.key === 'free' ? 'Start Free' : details.key === 'trial' ? 'Start 7-Day Trial — ₹99' : details.key === 'monthly' ? 'Subscribe Monthly' : 'Subscribe Yearly'}
                </button>
              </div>;
            })}
          </div>}
          {message && plans.length > 0 && <div className="modal-error" style={{ display: 'flex' }} role="alert"><p className="error-message">{message.text || message}</p></div>}
        </div>
      </div>
    </div>
  );
};

export default RazorpaySubscription;
