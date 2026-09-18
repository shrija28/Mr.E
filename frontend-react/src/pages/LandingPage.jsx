import React from 'react';
import { Link } from 'react-router-dom';

const LandingPage = () => {
  return (
    <>
      <div className="bg-mesh"></div>
      
      {/* Hero Section */}
      <main style={{ position: 'relative', zIndex: 1, padding: '60px 20px', maxWidth: '900px', margin: '0 auto' }}>
        <div className="section-card" style={{ textAlign: 'center', padding: '48px 32px', marginBottom: '32px' }}>
          <h1 style={{ fontSize: '2.2rem', marginBottom: '12px' }}>VyasaPrep</h1>
          <p style={{ color: 'var(--muted2)', fontSize: '1.1rem', maxWidth: '600px', margin: '0 auto 28px' }}>
            AI-powered KCET exam preparation platform. Practice with curated question sets across all four subjects and track your progress on the leaderboard.
          </p>
          <div style={{ display: 'flex', gap: '12px', justifyContent: 'center', flexWrap: 'wrap' }}>
            <Link to="/login" className="btn-primary" style={{ textDecoration: 'none' }}>Sign In</Link>
            <Link to="/register" className="btn-primary" style={{ textDecoration: 'none' }}>Create Account</Link>
          </div>
        </div>

        {/* Features */}
        <div className="section-card" style={{ padding: '32px', marginBottom: '32px' }}>
          <h2 style={{ marginBottom: '20px' }}>Key Features</h2>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '20px' }}>
            <div>
              <h3 style={{ fontSize: '1rem', marginBottom: '6px' }}>AI Question Generation</h3>
              <p style={{ fontSize: '0.85rem', color: 'var(--muted2)' }}>Questions generated from study materials using advanced RAG pipeline and Groq LLM.</p>
            </div>
            <div>
              <h3 style={{ fontSize: '1rem', marginBottom: '6px' }}>4 KCET Subjects</h3>
              <p style={{ fontSize: '0.85rem', color: 'var(--muted2)' }}>Biology, Physics, Chemistry, and Mathematics — all covered with dedicated question banks.</p>
            </div>
            <div>
              <h3 style={{ fontSize: '1rem', marginBottom: '6px' }}>Performance Analytics</h3>
              <p style={{ fontSize: '0.85rem', color: 'var(--muted2)' }}>Track your scores, identify weak areas, and get AI-powered study recommendations.</p>
            </div>
            <div>
              <h3 style={{ fontSize: '1rem', marginBottom: '6px' }}>Leaderboard</h3>
              <p style={{ fontSize: '0.85rem', color: 'var(--muted2)' }}>Compete with peers and see your rank based on composite performance scores.</p>
            </div>
          </div>
        </div>
      </main>
    </>
  );
};

export default LandingPage;
