import React from 'react';
import { Link } from 'react-router-dom';

const InstitutionExams = () => {
  return (
    <>
      {/* Auto-injected styles from HTML head */}
      <style dangerouslySetInnerHTML={{ __html: `` }} />
      
  <div className="bg-mesh"></div>

  
  

  
  <div className="main-wrap">

    
    <div className="section-card">
      <div className="section-card-header">
        <div className="section-icon" style={{"background":"linear-gradient(135deg,rgba(124,58,237,0.2),rgba(37,99,235,0.2))"}}>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>
        </div>
        <div>
          <h2>Create Institution Exam</h2>
          <p className="section-sub">Generate an exam from your institution's question bank (4 sets × 20 questions = 80 questions required)</p>
        </div>
      </div>
      <div className="section-body">
        <div style={{"display":"flex","gap":"12px","alignItems":"flex-end","flexWrap":"wrap"}}>
          <div className="input-group">
            <label className="input-label" htmlFor="examNameInput">Exam Name</label>
            <input type="text" id="examNameInput" className="text-input" placeholder="e.g. Mid-Term 2024" style={{"minWidth":"200px"}}/>
          </div>
          <div className="input-group">
            <label className="input-label" htmlFor="subjectSelect">Subject</label>
            <select id="subjectSelect" className="text-input" style={{"minWidth":"200px"}}>
              <option value="">Select subject…</option>
              <option value="Biology">Biology</option>
              <option value="Physics">Physics</option>
              <option value="Chemistry">Chemistry</option>
              <option value="Mathematics">Mathematics</option>
            </select>
          </div>
          <button id="createExamBtn" className="btn-primary">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{"width":"15px","height":"15px"}}><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
            Create Exam
          </button>
        </div>
        <div id="createMessage" style={{"marginTop":"12px","display":"none"}}></div>
      </div>
    </div>

    
    <div className="section-card">
      <div className="section-card-header">
        <div className="section-icon" style={{"background":"linear-gradient(135deg,rgba(217,119,6,0.2),rgba(234,179,8,0.2))"}}>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
        </div>
        <div>
          <h2>Question Bank Status</h2>
          <p className="section-sub">Questions available in your institution's bank (need 80 per subject for exam creation)</p>
        </div>
      </div>
      <div className="section-body">
        <div id="questionBankStatus" style={{"display":"grid","gridTemplateColumns":"repeat(auto-fit,minmax(180px,1fr))","gap":"12px"}}>
          <div style={{"textAlign":"center","color":"var(--muted)","padding":"24px"}}>Loading question counts…</div>
        </div>
      </div>
    </div>

    
    <div className="section-card">
      <div className="section-card-header">
        <div className="section-icon" style={{"background":"linear-gradient(135deg,rgba(8,145,178,0.2),rgba(5,150,105,0.2))"}}>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><line x1="3" y1="9" x2="21" y2="9"/><line x1="9" y1="21" x2="9" y2="9"/></svg>
        </div>
        <div>
          <h2>Institution Exams</h2>
          <p className="section-sub" id="examCount">Loading exams…</p>
        </div>
      </div>
      <div className="section-body" style={{"padding":"0"}}>
        <div className="table-scroll">
          <table className="results-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Subject</th>
                <th>Created</th>
                <th>Sets</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody id="examsTableBody">
              <tr><td colspan="6" style={{"textAlign":"center","color":"var(--muted)","padding":"32px"}}>Loading…</td></tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

  </div>

  
  
  
  

    </>
  );
};

export default InstitutionExams;
