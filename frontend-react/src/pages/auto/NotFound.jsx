import React from 'react';

const NotFound = () => {
  return (
    <>
      
      <style>{`
    /* Local styles for the 404 page so it does not depend on
       subscription.css or institution.css. */
    .nf-wrap {
      position: relative;
      z-index: 1;
      max-width: 560px;
      margin: 0 auto;
      padding: 80px 20px 60px;
      text-align: center;
    }
    .nf-code {
      font-size: 5rem;
      font-weight: 800;
      letter-spacing: -2px;
      line-height: 1;
      margin-bottom: 12px;
      background: linear-gradient(135deg, var(--purple-l), var(--cyan-l));
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
    }
    .nf-title {
      font-size: 1.6rem;
      font-weight: 700;
      margin-bottom: 12px;
    }
    .nf-message {
      color: var(--muted2);
      font-size: 1rem;
      margin-bottom: 28px;
    }
    .nf-path {
      display: inline-block;
      font-family: 'Consolas', 'Monaco', monospace;
      font-size: 0.85rem;
      color: var(--muted);
      background: var(--s2);
      border: 1px solid var(--border);
      border-radius: var(--rs);
      padding: 6px 12px;
      margin-bottom: 28px;
      max-width: 100%;
      overflow-wrap: break-word;
      word-break: break-all;
    }
    .nf-actions {
      display: flex;
      gap: 12px;
      justify-content: center;
      flex-wrap: wrap;
    }
  `}</style>
      <div dangerouslySetInnerHTML={{ __html: `
  

  <!-- Navbar -->
  

  <main class="nf-wrap" role="main">
    <div class="section-card" style="padding:48px 32px;">
      <div class="nf-code" aria-hidden="true">404</div>
      <h1 class="nf-title">Page not found</h1>
      <p class="nf-message">
        The page you are looking for does not exist or has been moved.
      </p>
      <div class="nf-path" id="nfRequestedPath" aria-label="Requested path"></div>
      <div class="nf-actions">
        <a href="/" id="nfHomeLink" class="btn-primary" data-no-router>Go to Home</a>
        <a href="#" id="nfBackLink" class="btn-outline" data-no-router>Go Back</a>
      </div>
    </div>
  </main>

  
  
` }} />
    </>
  );
};

export default NotFound;
