import React from 'react';

const Landing = () => {
  return (
    <>
      <div dangerouslySetInnerHTML={{__html: `
  <div class="bg-mesh"></div>

  

  <!-- Hero Section -->
  <main style="position:relative;z-index:1;padding:60px 20px;max-width:900px;margin:0 auto;">
    <div class="section-card" style="text-align:center;padding:48px 32px;margin-bottom:32px;">
      <h1 style="font-size:2.2rem;margin-bottom:12px;">Mr.E</h1>
      <p style="color:var(--muted2);font-size:1.1rem;max-width:600px;margin:0 auto 28px;">
        AI-powered KCET exam preparation platform. Practice with curated question sets across all four subjects and track your progress on the leaderboard.
      </p>
      <div style="display:flex;gap:12px;justify-content:center;flex-wrap:wrap;">
        <a href="/login" class="btn-primary">Sign In</a>
        <a href="/register" class="btn-primary">Create Account</a>
      </div>
    </div>

    <!-- Features -->
    <div class="section-card" style="padding:32px;margin-bottom:32px;">
      <h2 style="margin-bottom:20px;">Key Features</h2>
      <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:20px;">
        <div>
          <h3 style="font-size:1rem;margin-bottom:6px;">AI Question Generation</h3>
          <p style="font-size:0.85rem;color:var(--muted2);">Questions generated from study materials using advanced RAG pipeline and Groq LLM.</p>
        </div>
        <div>
          <h3 style="font-size:1rem;margin-bottom:6px;">4 KCET Subjects</h3>
          <p style="font-size:0.85rem;color:var(--muted2);">Biology, Physics, Chemistry, and Mathematics — all covered with dedicated question banks.</p>
        </div>
        <div>
          <h3 style="font-size:1rem;margin-bottom:6px;">Performance Analytics</h3>
          <p style="font-size:0.85rem;color:var(--muted2);">Track your scores, identify weak areas, and get AI-powered study recommendations.</p>
        </div>
        <div>
          <h3 style="font-size:1rem;margin-bottom:6px;">Leaderboard</h3>
          <p style="font-size:0.85rem;color:var(--muted2);">Compete with peers and see your rank based on composite performance scores.</p>
        </div>
      </div>
    </div>

    <!-- Subjects -->
    <div class="section-card" style="padding:32px;margin-bottom:32px;">
      <h2 style="margin-bottom:20px;">KCET Subjects</h2>
      <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:16px;">
        <div style="background:var(--s2);border:1px solid var(--border);border-radius:var(--rs);padding:20px;text-align:center;">
          <h3 style="font-size:1rem;margin-bottom:4px;">Biology</h3>
          <p style="font-size:0.8rem;color:var(--muted);">Botany &amp; Zoology</p>
        </div>
        <div style="background:var(--s2);border:1px solid var(--border);border-radius:var(--rs);padding:20px;text-align:center;">
          <h3 style="font-size:1rem;margin-bottom:4px;">Physics</h3>
          <p style="font-size:0.8rem;color:var(--muted);">Mechanics, Optics &amp; more</p>
        </div>
        <div style="background:var(--s2);border:1px solid var(--border);border-radius:var(--rs);padding:20px;text-align:center;">
          <h3 style="font-size:1rem;margin-bottom:4px;">Chemistry</h3>
          <p style="font-size:0.8rem;color:var(--muted);">Organic, Inorganic &amp; Physical</p>
        </div>
        <div style="background:var(--s2);border:1px solid var(--border);border-radius:var(--rs);padding:20px;text-align:center;">
          <h3 style="font-size:1rem;margin-bottom:4px;">Mathematics</h3>
          <p style="font-size:0.8rem;color:var(--muted);">Algebra, Calculus &amp; Geometry</p>
        </div>
      </div>
    </div>

    <!-- CTA -->
    <div class="section-card" style="text-align:center;padding:32px;">
      <h2 style="margin-bottom:12px;">Ready to start preparing?</h2>
      <p style="color:var(--muted2);margin-bottom:20px;">Join Mr.E and begin your KCET exam preparation today.</p>
      <div style="display:flex;gap:12px;justify-content:center;flex-wrap:wrap;">
        <a href="/register" class="btn-primary">Get Started</a>
        <a href="/login" class="btn-primary">Sign In</a>
      </div>
    </div>
  </main>

  <!-- Auth bootstrap: redirect authenticated users -->
  <script src="../js/auth.js"></script>
  <script>
  (function () {
    // If the user is already authenticated, redirect them to their dashboard.
    Auth.redirectIfAuthenticated();
  })();
  </script>
`}} />
    </>
  );
};

export default Landing;
