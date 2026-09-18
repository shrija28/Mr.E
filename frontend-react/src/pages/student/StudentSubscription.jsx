import React from 'react';

const StudentSubscription = () => {
  return (
    <main style={{ padding: '24px' }}>
      <header style={{ marginBottom: '24px' }}>
        <h1 style={{ fontSize: '1.8rem', fontWeight: '800' }}>Subscription</h1>
        <p style={{ color: 'var(--muted)' }}>Manage your VyasaPrep premium subscription.</p>
      </header>

      <div className="section-card" style={{ padding: '32px', textAlign: 'center', maxWidth: '600px', margin: '0 auto' }}>
        <h2 style={{ marginBottom: '16px' }}>Current Plan: Free</h2>
        <p style={{ color: 'var(--muted)', marginBottom: '24px' }}>
          You are currently on the free plan which includes limited exams. Upgrade to Premium for unlimited AI-generated exams, advanced analytics, and priority support.
        </p>
        <button className="btn-primary" style={{ padding: '12px 24px', fontSize: '1.1rem' }}>Upgrade to Premium - ₹499/month</button>
      </div>
    </main>
  );
};

export default StudentSubscription;
