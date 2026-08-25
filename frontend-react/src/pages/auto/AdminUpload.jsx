import React, { useState, useRef } from 'react';

const AdminUpload = () => {
  const [files, setFiles] = useState([]);
  const [uploadStatus, setUploadStatus] = useState('idle'); // idle, uploading, done
  const [generateStatus, setGenerateStatus] = useState('idle'); // idle, generating, done
  const [activeTab, setActiveTab] = useState(0);
  const fileInputRef = useRef(null);

  const [subject, setSubject] = useState("");
  const [docType, setDocType] = useState("question_paper");
  const [browseError, setBrowseError] = useState("");
  
  const handleBrowseClick = () => {
    if (!subject) {
      setBrowseError("Please select a Subject before browsing files.");
      return;
    }
    if (!docType) {
      setBrowseError("Please select a Document Type before browsing files.");
      return;
    }
    setBrowseError("");
    fileInputRef.current.click();
  };

  const handleFileChange = (e) => {
    if (e.target.files) {
      // Append new files instead of replacing
      setFiles([...files, ...Array.from(e.target.files)]);
    }
  };

  const removeFile = (index) => {
    setFiles(files.filter((_, i) => i !== index));
  };

  const handleUpload = () => {
    setUploadStatus('uploading');
    setTimeout(() => {
      setUploadStatus('done');
    }, 1500);
  };

  const handleGenerate = () => {
    setGenerateStatus('generating');
    setTimeout(() => {
      setGenerateStatus('done');
    }, 2000);
  };

  const mockQuestionsTemplate = [
    {
      q: "If the roots of the equation x² - bx + c = 0 are two consecutive integers, then b² - 4c is",
      options: ["A) 1", "B) 2", "C) 3", "D) 4"],
      ans: "A) 1"
    },
    {
      q: "The velocity of a particle at an instant is 10 m/s. After 5 sec, the velocity of the particle is 20 m/s. The velocity 3 seconds earlier to that instant is",
      options: ["A) 4 m/s", "B) 6 m/s", "C) 8 m/s", "D) 10 m/s"],
      ans: "A) 4 m/s"
    },
    {
      q: "Which of the following is an amphoteric oxide?",
      options: ["A) Na2O", "B) SO2", "C) Al2O3", "D) P4O10"],
      ans: "C) Al2O3"
    },
    {
      q: "The number of ATP molecules produced when one molecule of glucose undergoes fermentation is",
      options: ["A) 2", "B) 4", "C) 36", "D) 38"],
      ans: "A) 2"
    },
    {
      q: "If A is a square matrix of order 3 such that |A| = 5, then the value of |adj A| is",
      options: ["A) 5", "B) 25", "C) 125", "D) 625"],
      ans: "B) 25"
    }
  ];

  // Generate 60 questions by repeating the template
  const fullMockQuestions = Array.from({ length: 60 }, (_, i) => {
    const template = mockQuestionsTemplate[i % mockQuestionsTemplate.length];
    return {
      ...template,
      // Slightly randomize or append the number to make them look distinct if needed, but for now just repeating is fine
    };
  });

  return (
    <>
      <div className="bg-mesh"></div>
      <main className="main-wrap">
        
        <div className="section-card" id="uploadCard">
          <div className="section-card-header">
            <div className="section-icon blue">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
            </div>
            <div>
              <h2><span className="step-num">01</span> Upload Previous Year Papers</h2>
              <p className="section-sub">Upload a minimum of 10 PYQ papers — RAG will extract question patterns</p>
            </div>
          </div>
          <div className="section-body">
            
            <div style={{"marginBottom":"16px"}}>
              <label htmlFor="subjectSelect" style={{"display":"block","marginBottom":"6px","fontSize":"0.85rem","color":"var(--muted2)"}}>Subject <span style={{"color":"var(--red)"}}>*</span></label>
              <select id="subjectSelect" className="text-input" required value={subject} onChange={(e) => setSubject(e.target.value)}>
                <option value="" disabled>Select a subject…</option>
                <option value="Biology">Biology</option>
                <option value="Physics">Physics</option>
                <option value="Chemistry">Chemistry</option>
                <option value="Mathematics">Mathematics</option>
              </select>
            </div>

            <div style={{"marginBottom":"16px"}}>
              <label htmlFor="fileTypeSelect" style={{"display":"block","marginBottom":"6px","fontSize":"0.85rem","color":"var(--muted2)"}}>Document Type <span style={{"color":"var(--red)"}}>*</span></label>
              <select id="fileTypeSelect" className="text-input" required value={docType} onChange={(e) => setDocType(e.target.value)}>
                <option value="question_paper">Question Paper (PYQ)</option>
                <option value="textbook">Textbook</option>
              </select>
            </div>

            <div className="drop-zone" id="dropZone" onClick={handleBrowseClick} style={{ cursor: 'pointer' }}>
              <div className="drop-zone-content">
                <div className="drop-icon">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="12" y1="18" x2="12" y2="12"/><line x1="9" y1="15" x2="15" y2="15"/></svg>
                </div>
                <p className="drop-title">Drop your PYQ papers here</p>
                <p className="drop-sub">PDF, DOC, DOCX, TXT — Minimum 10 files</p>
                {/* Changed btn-outline to btn-primary and added custom style to make it blue */}
                <button type="button" className="btn-primary" style={{ backgroundColor: 'var(--blue)', color: '#fff', border: 'none' }}>
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
                  Browse Files
                </button>
                <input type="file" ref={fileInputRef} onChange={handleFileChange} multiple accept=".pdf,.doc,.docx,.txt" hidden/>
              </div>
            </div>
            
            {browseError && (
              <p style={{ color: 'var(--red)', marginTop: '8px', fontSize: '0.9rem', textAlign: 'center', fontWeight: 'bold' }}>
                {browseError}
              </p>
            )}

            {files.length > 0 && (
              <div className="file-grid" style={{ marginTop: '16px' }}>
                {files.map((file, idx) => (
                  <div key={idx} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '8px', border: '1px solid #ddd', borderRadius: '4px', marginBottom: '8px' }}>
                    <span style={{ fontSize: '0.9rem' }}>{file.name}</span>
                    <button type="button" onClick={(e) => { e.stopPropagation(); removeFile(idx); }} style={{ color: 'var(--red)', border: 'none', background: 'none', cursor: 'pointer' }}>X</button>
                  </div>
                ))}
              </div>
            )}

            {files.length > 0 && files.length < 10 && (
              <p style={{ color: 'var(--red)', marginTop: '8px', fontSize: '0.9rem', textAlign: 'center' }}>
                Please select at least 10 papers or textbooks to continue.
              </p>
            )}

            <div className="upload-footer" style={{ marginTop: '20px' }}>
              <div className="upload-progress-wrap">
                <div className="upload-count"><span style={{ color: files.length < 10 ? 'var(--red)' : 'inherit' }}>{files.length}</span>/10+ papers</div>
                <div className="upload-bar"><div className="upload-bar-fill" style={{ width: `${Math.min((files.length / 10) * 100, 100)}%` }}></div></div>
              </div>
              {files.length >= 10 && uploadStatus === 'idle' && (
                <button className="btn-primary" onClick={handleUpload}>
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
                  Send to Backend
                </button>
              )}
              {uploadStatus === 'uploading' && <span style={{ color: 'var(--blue)' }}>Uploading...</span>}
              {uploadStatus === 'done' && <span style={{ color: 'var(--green)' }}>✓ Uploaded</span>}
            </div>
          </div>
        </div>

        {uploadStatus === 'done' && (
          <div className="section-card generate-card" id="generateCard">
            <div className="section-card-header">
              <div className="section-icon green">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
              </div>
              <div>
                <h2><span className="step-num">02</span> Generate 4 Paper Sets</h2>
              </div>
            </div>
            <div className="section-body">
              <div className="generate-info-row">
                <div className="gen-info-chip">Set A</div>
                <div className="gen-info-chip">Set B</div>
                <div className="gen-info-chip">Set C</div>
                <div className="gen-info-chip">Set D</div>
              </div>
              {generateStatus === 'idle' && (
                <button className="btn-generate" onClick={handleGenerate} style={{ display: 'block', margin: '20px auto' }}>
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
                  Generate 4 Sets
                </button>
              )}
              {generateStatus === 'generating' && (
                <div className="gen-progress" style={{ display: 'block' }}>
                  <p className="gen-bar-label" style={{ textAlign: 'center' }}>Initializing RAG pipeline...</p>
                </div>
              )}
            </div>
          </div>
        )}

        {generateStatus === 'done' && (
          <div id="setsOutput">
            <div className="output-header-row">
              <div>
                <h2 className="output-title">📋 Generated Paper Sets</h2>
              </div>
              <div className="output-header-actions">
                <button className="btn-outline">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
                  Download All
                </button>
              </div>
            </div>

            <div className="sets-tab-bar">
              {['Set A', 'Set B', 'Set C', 'Set D'].map((set, idx) => (
                <button key={idx} className={`set-tab ${activeTab === idx ? 'active' : ''}`} onClick={() => setActiveTab(idx)}>
                  <span className="tab-label">{set}</span>
                  <span className="tab-count">60 Qs</span>
                </button>
              ))}
            </div>

            <div className="paper-preview-card section-card" style={{ padding: '24px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid #eee', paddingBottom: '16px', marginBottom: '20px' }}>
                <h3 style={{ margin: 0, color: 'var(--blue)' }}>Karnataka CET Prototype - Set {String.fromCharCode(65 + activeTab)}</h3>
                <span style={{ fontSize: '0.85rem', color: '#666', background: '#f5f5f5', padding: '4px 8px', borderRadius: '4px' }}>Time: 80 Mins | Max Marks: 60</span>
              </div>
              
              <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
                {fullMockQuestions.map((item, i) => (
                  <div key={i} style={{ padding: '16px', background: '#fafafa', borderRadius: '8px', border: '1px solid #eee' }}>
                    <p style={{ margin: '0 0 12px 0', fontSize: '1rem', color: '#222', fontWeight: 500, lineHeight: 1.5 }}>
                      <span style={{ color: 'var(--blue)', fontWeight: 600, marginRight: '8px' }}>Q{i + 1}.</span> 
                      {item.q}
                    </p>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                      {item.options.map((opt, optIdx) => (
                        <div key={optIdx} style={{ padding: '10px 16px', background: '#fff', border: '1px solid #ddd', borderRadius: '6px', fontSize: '0.9rem', color: '#444' }}>
                          {opt}
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </main>
    </>
  );
};

export default AdminUpload;
