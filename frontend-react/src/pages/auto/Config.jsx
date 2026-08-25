import React from 'react';
import { Link } from 'react-router-dom';

const Config = () => {
  return (
    <>
      {/* Auto-injected styles from HTML head */}
      <style dangerouslySetInnerHTML={{ __html: `` }} />
      
  <div className="bg-mesh"></div>

  
  

  <main className="main-wrap">
    
    <div className="section-card">
      <div className="section-card-header">
        <div className="section-icon purple">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-4 0v-.09a1.65 1.65 0 00-1-1.51 1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83-2.83l.06-.06a1.65 1.65 0 00.33-1.82 1.65 1.65 0 00-1.51-1H3a2 2 0 010-4h.09a1.65 1.65 0 001.51-1 1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 012.83-2.83l.06.06a1.65 1.65 0 001.82.33h.09a1.65 1.65 0 001-1.51V3a2 2 0 014 0v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 2.83l-.06.06a1.65 1.65 0 00-.33 1.82v.09a1.65 1.65 0 001.51 1H21a2 2 0 010 4h-.09a1.65 1.65 0 00-1.51 1z"/></svg>
        </div>
        <div>
          <h2>Backend Diagnostics</h2>
          <p className="section-sub">Developer diagnostic page — test backend connectivity</p>
        </div>
      </div>
      <div className="section-body">
        
        <div className="input-group" style={{"marginBottom":"20px"}}>
          <label className="input-label">API Endpoint</label>
          <input
            type="text"
            className="text-input"
            value="/api"
            disabled
            aria-label="Fixed API endpoint"
          />
        </div>

        
        <div className="rag-actions">
          <button type="button" className="btn-outline" id="testBtn" >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>
            Test Connection
          </button>
        </div>

        
        <div id="connectionResult" className="connection-result" style={{"display":"none"}}></div>
      </div>
    </div>
  </main>

  
  

    </>
  );
};

export default Config;
