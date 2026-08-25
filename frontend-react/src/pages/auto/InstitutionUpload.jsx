import React from 'react';
import { Link } from 'react-router-dom';

const InstitutionUpload = () => {
  return (
    <>
      {/* Auto-injected styles from HTML head */}
      <style dangerouslySetInnerHTML={{ __html: `` }} />
      
  <div className="bg-mesh"></div>

  
  

  <main className="main-wrap">

    
    <div className="section-card">
      <div className="section-card-header">
        <div className="section-icon blue">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
        </div>
        <div>
          <h2>Upload Question Papers</h2>
          <p className="section-sub">Build your institution's private question bank (max 10 files, 20MB each)</p>
        </div>
      </div>
      <div className="section-body">

        
        <div className="input-group" style={{"marginBottom":"16px"}}>
          <label className="input-label" htmlFor="subjectSelect">Subject <span style={{"color":"var(--red)"}}>*</span></label>
          <select id="subjectSelect" className="text-input" style={{"minWidth":"220px"}}>
            <option value="" disabled selected>Select a subject…</option>
            <option value="Biology">Biology</option>
            <option value="Physics">Physics</option>
            <option value="Chemistry">Chemistry</option>
            <option value="Mathematics">Mathematics</option>
          </select>
        </div>

        
        <div className="input-group" style={{"marginBottom":"16px"}}>
          <label className="input-label" htmlFor="fileTypeSelect">Document Type <span style={{"color":"var(--red)"}}>*</span></label>
          <select id="fileTypeSelect" className="text-input" style={{"minWidth":"220px"}}>
            <option value="question_paper" selected>Question Paper (PYQ)</option>
            <option value="textbook">Textbook</option>
          </select>
        </div>

        
        <div className="drop-zone" id="dropZone">
          <div className="drop-zone-content">
            <div className="drop-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="12" y1="18" x2="12" y2="12"/><line x1="9" y1="15" x2="15" y2="15"/></svg>
            </div>
            <p className="drop-title">Drop your question papers here</p>
            <p className="drop-sub">PDF, DOCX, TXT — Maximum 10 files per batch</p>
            <button className="btn-outline" type="button" id="browseFilesBtn">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
              Browse Files
            </button>
            <input type="file" id="fileInput" multiple accept=".pdf,.docx,.txt" hidden/>
          </div>
        </div>

        
        <div className="file-grid" id="fileGrid"></div>

        
        <div className="upload-footer">
          <div className="upload-progress-wrap">
            <div className="upload-count"><span id="fileCount">0</span>/10 files</div>
            <div className="upload-bar"><div className="upload-bar-fill" id="uploadBarFill"></div></div>
          </div>
          <button className="btn-primary" id="uploadBtn" style={{"display":"none"}} type="button">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
            Upload to Question Bank
          </button>
        </div>

        <div id="uploadResult" style={{"display":"none","marginTop":"16px"}}></div>
      </div>
    </div>

    
    <div className="section-card" id="indexedFilesSection" style={{"display":"none"}}>
      <div className="section-card-header">
        <div className="section-icon" style={{"background":"linear-gradient(135deg,rgba(5,150,105,0.2),rgba(8,145,178,0.2))"}}>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/><polyline points="9 15 12 18 15 15"/></svg>
        </div>
        <div>
          <h2>Indexed Files</h2>
          <p className="section-sub" id="indexedFilesSubtitle">Files already in your question bank</p>
        </div>
      </div>
      <div className="section-body">
        <div className="file-grid" id="indexedFileGrid"></div>
      </div>
    </div>

    
    <div className="section-card">
      <div className="section-card-header">
        <div className="section-icon" style={{"background":"linear-gradient(135deg,rgba(124,58,237,0.2),rgba(37,99,235,0.2))"}}>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
        </div>
        <div>
          <h2>Question Bank Status</h2>
          <p className="section-sub">Questions in your institution's bank (need 80 per subject to create an exam)</p>
        </div>
      </div>
      <div className="section-body">
        <div id="questionCounts" style={{"display":"grid","gridTemplateColumns":"repeat(auto-fit,minmax(180px,1fr))","gap":"12px"}}>
          <div style={{"textAlign":"center","color":"var(--muted)","padding":"24px"}}>Select a subject and upload files to see counts.</div>
        </div>
      </div>
    </div>

    
    <div className="section-card">
      <div className="section-card-header">
        <div className="section-icon" style={{"background":"linear-gradient(135deg,rgba(8,145,178,0.2),rgba(5,150,105,0.2))"}}>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>
        </div>
        <div>
          <h2>How It Works</h2>
          <p className="section-sub">Build your institution's private question bank</p>
        </div>
      </div>
      <div className="section-body">
        <ol style={{"margin":"0","paddingLeft":"20px","color":"var(--muted2)","lineHeight":"1.9"}}>
          <li><strong>Upload question papers</strong> — PDF, DOCX, or TXT files containing MCQs</li>
          <li><strong>AI extracts questions</strong> — Our system parses and extracts individual MCQs automatically</li>
          <li><strong>Questions are scoped to your institution</strong> — Only your students can access them</li>
          <li><strong>Create exams</strong> — Go to the Exams tab to generate exam sets from your question bank</li>
        </ol>
        <div style={{"marginTop":"16px","padding":"12px","background":"rgba(217,119,6,0.1)","border":"1px solid rgba(217,119,6,0.3)","borderRadius":"var(--rs)"}}>
          <strong style={{"color":"var(--yellow-l)"}}>Note:</strong>
          <span style={{"color":"var(--muted2)"}}> You need at least 80 questions per subject to create an exam (4 sets × 20 questions).</span>
        </div>
      </div>
    </div>

  </main>

  
  
  

    </>
  );
};

export default InstitutionUpload;
