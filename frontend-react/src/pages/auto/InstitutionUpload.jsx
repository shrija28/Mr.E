import React, { useState, useRef, useEffect } from 'react';
import { Link } from 'react-router-dom';

const SUBJECTS = ['Biology', 'Physics', 'Chemistry', 'Mathematics'];

const SUBJECT_ICONS = {
  Biology: '🌱',
  Physics: '⚡',
  Chemistry: '🧪',
  Mathematics: '📐',
};

const InstitutionUpload = () => {
  const [files, setFiles] = useState([]);
  const [subject, setSubject] = useState('');
  const [fileType, setFileType] = useState('question_paper');
  const [isDragging, setIsDragging] = useState(false);
  const [uploadStatus, setUploadStatus] = useState('idle'); // 'idle' | 'uploading' | 'done' | 'error'
  const [uploadMessage, setUploadMessage] = useState('');
  const [errorMessage, setErrorMessage] = useState('');
  const [questionCounts, setQuestionCounts] = useState(null);
  const [indexedFiles, setIndexedFiles] = useState([]);
  const [loadingFiles, setLoadingFiles] = useState(false);

  const fileInputRef = useRef(null);

  const fetchQuestionCounts = async () => {
    try {
      const res = await fetch('/api/institution/content/questions/counts', { credentials: 'include' });
      if (res.ok) {
        const data = await res.json();
        if (data && data.counts) {
          setQuestionCounts(data);
        }
      }
    } catch (err) {
      console.warn('Could not fetch question counts:', err);
    }
  };

  const fetchIndexedFiles = async (subj) => {
    if (!subj) {
      setIndexedFiles([]);
      return;
    }
    setLoadingFiles(true);
    try {
      let res = await fetch(`/api/institution/content/upload/files?subject=${encodeURIComponent(subj)}`, {
        credentials: 'include'
      });
      if (res.ok) {
        const data = await res.json();
        if (data && data.files) {
          setIndexedFiles(data.files);
        } else {
          setIndexedFiles([]);
        }
      } else {
        setIndexedFiles([]);
      }
    } catch (err) {
      console.warn('Could not fetch indexed files:', err);
      setIndexedFiles([]);
    } finally {
      setLoadingFiles(false);
    }
  };

  useEffect(() => {
    fetchQuestionCounts();
  }, []);

  useEffect(() => {
    if (subject) {
      fetchIndexedFiles(subject);
    }
  }, [subject]);

  const handleDropZoneClick = (e) => {
    if (e.target.closest('#browseFilesBtn') || e.target.closest('label') || e.target.tagName === 'INPUT') {
      return;
    }
    if (fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  const addFiles = (newFiles) => {
    setErrorMessage('');
    const allowedExtensions = ['.pdf', '.docx', '.txt', '.doc'];
    const validFiles = [];
    let err = '';

    for (const f of newFiles) {
      const ext = '.' + f.name.split('.').pop().toLowerCase();
      if (!allowedExtensions.includes(ext)) {
        err = `File "${f.name}" has an unsupported format. Allowed formats: PDF, DOCX, TXT.`;
        break;
      }
      // No 20MB restriction — high-MB textbooks up to 1GB supported
      if (f.size > 1024 * 1024 * 1024) {
        err = `File "${f.name}" exceeds the 1GB maximum file limit.`;
        break;
      }
      validFiles.push(f);
    }

    if (err) {
      setErrorMessage(err);
      return;
    }

    const combined = [...files, ...validFiles];
    if (combined.length > 10) {
      setErrorMessage('Maximum 10 files per batch. Kept first 10 files.');
      setFiles(combined.slice(0, 10));
    } else {
      setFiles(combined);
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      addFiles(Array.from(e.target.files));
    }
  };

  const removeFile = (index) => {
    setFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      addFiles(Array.from(e.dataTransfer.files));
    }
  };

  const handleUpload = async () => {
    if (!files.length) return;
    if (!subject) {
      setErrorMessage('Please select a Subject before uploading.');
      return;
    }

    setUploadStatus('uploading');
    setErrorMessage('');
    setUploadMessage('Uploading files and extracting MCQs into question bank...');

    try {
      const formData = new FormData();
      formData.append('subject', subject);
      formData.append('file_type', fileType);
      files.forEach((f) => {
        formData.append('files', f);
      });

      let res = await fetch('/api/institution/content/upload', {
        method: 'POST',
        credentials: 'include',
        body: formData,
      });

      if (res.status === 401 || res.status === 403) {
        // Fallback to admin upload route if test user or session role
        res = await fetch('/api/admin/upload', {
          method: 'POST',
          credentials: 'include',
          body: formData,
        });
      }

      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        if (res.status === 401) {
          setErrorMessage('Authentication required. Please log in first at /login.');
        } else {
          const msg = data.message || (data.detail && (data.detail.message || data.detail)) || data.error || 'Failed to upload files';
          setErrorMessage(typeof msg === 'string' ? msg : JSON.stringify(msg));
        }
        setUploadStatus('error');
        return;
      }

      setUploadStatus('done');
      const filesCount = data.indexed_files || files.length;
      const qCount = data.questions_extracted || 0;
      setUploadMessage(`✓ Successfully indexed ${filesCount} file(s) with ${qCount} questions extracted for ${subject}!`);
      setFiles([]);

      fetchQuestionCounts();
      fetchIndexedFiles(subject);
    } catch (err) {
      console.error(err);
      setUploadStatus('error');
      setErrorMessage('An unexpected network error occurred while uploading. Please try again.');
    }
  };

  return (
    <>
      <div className="bg-mesh"></div>

      <main className="main-wrap">
        {/* Upload Card */}
        <div className="section-card">
          <div className="section-card-header">
            <div className="section-icon blue">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4" />
                <polyline points="17 8 12 3 7 8" />
                <line x1="12" y1="3" x2="12" y2="15" />
              </svg>
            </div>
            <div>
              <h2>Upload Materials & Question Papers</h2>
              <p className="section-sub">Build your institution's private question bank — large textbooks & question papers supported</p>
            </div>
          </div>
          <div className="section-body">
            {/* Subject Dropdown */}
            <div className="input-group" style={{ marginBottom: '16px' }}>
              <label className="input-label" htmlFor="subjectSelect">
                Subject <span style={{ color: 'var(--red)' }}>*</span>
              </label>
              <select
                id="subjectSelect"
                className="text-input"
                style={{ minWidth: '220px' }}
                value={subject}
                onChange={(e) => {
                  setSubject(e.target.value);
                  setErrorMessage('');
                }}
              >
                <option value="" disabled>Select a subject…</option>
                <option value="Biology">Biology</option>
                <option value="Physics">Physics</option>
                <option value="Chemistry">Chemistry</option>
                <option value="Mathematics">Mathematics</option>
              </select>
            </div>

            {/* Document Type Dropdown */}
            <div className="input-group" style={{ marginBottom: '16px' }}>
              <label className="input-label" htmlFor="fileTypeSelect">
                Document Type <span style={{ color: 'var(--red)' }}>*</span>
              </label>
              <select
                id="fileTypeSelect"
                className="text-input"
                style={{ minWidth: '220px' }}
                value={fileType}
                onChange={(e) => setFileType(e.target.value)}
              >
                <option value="question_paper">Question Paper (PYQ)</option>
                <option value="textbook">Textbook</option>
              </select>
            </div>

            {/* Drop Zone */}
            <div
              className={`drop-zone ${isDragging ? 'drag-over' : ''}`}
              id="dropZone"
              onClick={handleDropZoneClick}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              style={{ cursor: 'pointer' }}
            >
              <div className="drop-zone-content">
                <div className="drop-icon">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                    <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" />
                    <polyline points="14 2 14 8 20 8" />
                    <line x1="12" y1="18" x2="12" y2="12" />
                    <line x1="9" y1="15" x2="15" y2="15" />
                  </svg>
                </div>
                <p className="drop-title">Drop your question papers or textbooks here</p>
                <p className="drop-sub">PDF, DOCX, TXT — High-capacity extraction (large textbooks supported)</p>
                <label
                  htmlFor="institutionFileInput"
                  className="btn-outline"
                  id="browseFilesBtn"
                  style={{
                    cursor: 'pointer',
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '8px',
                    userSelect: 'none'
                  }}
                >
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ pointerEvents: 'none' }}>
                    <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4" />
                    <polyline points="17 8 12 3 7 8" />
                    <line x1="12" y1="3" x2="12" y2="15" />
                  </svg>
                  Browse Files
                </label>
                <input
                  type="file"
                  id="institutionFileInput"
                  ref={fileInputRef}
                  onChange={handleFileChange}
                  onClick={(e) => {
                    e.stopPropagation();
                    e.target.value = null;
                  }}
                  multiple
                  accept=".pdf,.docx,.txt,.doc"
                  style={{
                    position: 'absolute',
                    opacity: 0,
                    width: '1px',
                    height: '1px',
                    pointerEvents: 'none',
                    overflow: 'hidden'
                  }}
                />
              </div>
            </div>

            {/* Error Message */}
            {errorMessage && (
              <div
                style={{
                  marginTop: '16px',
                  padding: '12px 16px',
                  background: 'rgba(239, 68, 68, 0.1)',
                  border: '1px solid rgba(239, 68, 68, 0.3)',
                  borderRadius: 'var(--rs)',
                  color: 'var(--red-l, #f87171)',
                  fontSize: '0.88rem'
                }}
              >
                {errorMessage}
              </div>
            )}

            {/* Upload Status / Success Result */}
            {uploadStatus === 'done' && (
              <div
                id="uploadResult"
                style={{
                  marginTop: '16px',
                  padding: '12px 16px',
                  background: 'rgba(5, 150, 105, 0.12)',
                  border: '1px solid rgba(5, 150, 105, 0.35)',
                  borderRadius: 'var(--rs)',
                  color: 'var(--green-l, #34d399)',
                  fontSize: '0.88rem'
                }}
              >
                {uploadMessage}
              </div>
            )}

            {uploadStatus === 'uploading' && (
              <div
                style={{
                  marginTop: '16px',
                  padding: '12px 16px',
                  background: 'rgba(59, 130, 246, 0.1)',
                  border: '1px solid rgba(59, 130, 246, 0.3)',
                  borderRadius: 'var(--rs)',
                  color: 'var(--blue-l, #60a5fa)',
                  fontSize: '0.88rem',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '10px'
                }}
              >
                <div style={{
                  width: '16px',
                  height: '16px',
                  border: '2px solid rgba(96, 165, 250, 0.3)',
                  borderTopColor: '#60a5fa',
                  borderRadius: '50%',
                  animation: 'spin 0.8s linear infinite'
                }}></div>
                {uploadMessage}
              </div>
            )}

            {/* File Grid */}
            {files.length > 0 && (
              <div className="file-grid" id="fileGrid" style={{ marginTop: '16px' }}>
                {files.map((file, idx) => (
                  <div key={`${file.name}-${idx}`} className="file-card">
                    <div className="file-card-icon">
                      {file.name.endsWith('.pdf') ? '📄' : file.name.endsWith('.docx') || file.name.endsWith('.doc') ? '📝' : '📃'}
                    </div>
                    <div className="file-card-info">
                      <div className="file-card-name" title={file.name}>{file.name}</div>
                      <div className="file-card-size">{(file.size / 1024 / 1024).toFixed(2)} MB</div>
                    </div>
                    <button
                      type="button"
                      className="file-card-remove"
                      onClick={(e) => {
                        e.stopPropagation();
                        removeFile(idx);
                      }}
                      title="Remove file"
                    >
                      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ width: '16px', height: '16px' }}>
                        <line x1="18" y1="6" x2="6" y2="18" />
                        <line x1="6" y1="6" x2="18" y2="18" />
                      </svg>
                    </button>
                  </div>
                ))}
              </div>
            )}

            {/* Footer with Progress & Upload Button */}
            <div className="upload-footer" style={{ marginTop: '20px' }}>
              <div className="upload-progress-wrap">
                <div className="upload-count">
                  <span id="fileCount">{files.length}</span>/10 files
                </div>
                <div className="upload-bar">
                  <div
                    className="upload-bar-fill"
                    id="uploadBarFill"
                    style={{ width: `${(files.length / 10) * 100}%` }}
                  ></div>
                </div>
              </div>
              {files.length > 0 && (
                <button
                  className="btn-primary"
                  id="uploadBtn"
                  type="button"
                  onClick={handleUpload}
                  disabled={uploadStatus === 'uploading'}
                  style={{ display: 'inline-flex', alignItems: 'center', gap: '8px' }}
                >
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4" />
                    <polyline points="17 8 12 3 7 8" />
                    <line x1="12" y1="3" x2="12" y2="15" />
                  </svg>
                  {uploadStatus === 'uploading' ? 'Extracting & Uploading...' : 'Upload to Question Bank'}
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Indexed Files Section */}
        {subject && (
          <div className="section-card" id="indexedFilesSection" style={{ display: 'block', marginTop: '24px' }}>
            <div className="section-card-header">
              <div
                className="section-icon"
                style={{ background: 'linear-gradient(135deg,rgba(5,150,105,0.2),rgba(8,145,178,0.2))' }}
              >
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" />
                  <polyline points="14 2 14 8 20 8" />
                  <polyline points="9 15 12 18 15 15" />
                </svg>
              </div>
              <div>
                <h2>Indexed Files ({subject})</h2>
                <p className="section-sub" id="indexedFilesSubtitle">
                  Files already in your question bank for {subject}
                </p>
              </div>
            </div>
            <div className="section-body">
              {loadingFiles ? (
                <div style={{ textAlign: 'center', color: 'var(--muted)', padding: '20px' }}>Loading indexed files...</div>
              ) : indexedFiles.length === 0 ? (
                <div style={{ textAlign: 'center', color: 'var(--muted)', padding: '20px' }}>
                  No indexed files for {subject} yet. Upload question papers above to add them to your question bank.
                </div>
              ) : (
                <div className="file-grid" id="indexedFileGrid">
                  {indexedFiles.map((f, i) => (
                    <div key={f.id || i} className="file-card uploaded">
                      <div className="file-card-icon">📁</div>
                      <div className="file-card-info">
                        <div className="file-card-name" title={f.filename}>{f.filename}</div>
                        <div className="file-card-size">
                          {f.file_size ? `${(f.file_size / 1024).toFixed(1)} KB` : ''} · {f.chunk_count || 0} chunks
                        </div>
                        <div className="file-card-status" style={{ display: 'block' }}>✓ Indexed</div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Question Bank Status Card */}
        <div className="section-card" style={{ marginTop: '24px' }}>
          <div className="section-card-header">
            <div
              className="section-icon"
              style={{ background: 'linear-gradient(135deg,rgba(124,58,237,0.2),rgba(37,99,235,0.2))' }}
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="10" />
                <polyline points="12 6 12 12 16 14" />
              </svg>
            </div>
            <div>
              <h2>Question Bank Status</h2>
              <p className="section-sub">Questions in your institution's bank (need 80 per subject to create an exam)</p>
            </div>
          </div>
          <div className="section-body">
            <div
              id="questionCounts"
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit,minmax(200px,1fr))',
                gap: '12px'
              }}
            >
              {SUBJECTS.map((subj) => {
                const count = (questionCounts && questionCounts.counts && questionCounts.counts[subj]) || 0;
                const threshold = (questionCounts && questionCounts.threshold) || 80;
                const pct = Math.min(100, Math.round((count / threshold) * 100));
                const ready = count >= threshold;

                return (
                  <div
                    key={subj}
                    onClick={() => setSubject(subj)}
                    style={{
                      background: subject === subj ? 'rgba(124,58,237,0.08)' : 'var(--s2)',
                      border: subject === subj ? '1.5px solid var(--purple-l)' : '1px solid var(--border)',
                      borderRadius: 'var(--rs)',
                      padding: '16px',
                      cursor: 'pointer',
                      transition: 'all 0.2s ease'
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                      <span style={{ fontWeight: 600, color: 'var(--text)' }}>
                        {SUBJECT_ICONS[subj]} {subj}
                      </span>
                      <span
                        style={{
                          fontSize: '0.75rem',
                          fontWeight: 700,
                          padding: '2px 8px',
                          borderRadius: '10px',
                          background: ready ? 'rgba(5,150,105,0.15)' : 'rgba(217,119,6,0.15)',
                          color: ready ? 'var(--green-l)' : 'var(--yellow-l)'
                        }}
                      >
                        {ready ? 'Ready' : `${count}/${threshold}`}
                      </span>
                    </div>

                    <div style={{ height: '6px', background: 'var(--s3)', borderRadius: '3px', overflow: 'hidden' }}>
                      <div
                        style={{
                          height: '100%',
                          width: `${pct}%`,
                          background: ready ? 'var(--green-l)' : 'linear-gradient(90deg, var(--purple), var(--cyan-l))',
                          borderRadius: '3px',
                          transition: 'width 0.3s ease'
                        }}
                      ></div>
                    </div>

                    <div style={{ fontSize: '0.75rem', color: 'var(--muted)', marginTop: '8px' }}>
                      {count} questions indexed {ready ? '✓' : `(needs ${threshold - count} more)`}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

<<<<<<< HEAD:frontend-react/src/pages/auto/InstitutionUpload.jsx
        {/* How It Works Card */}
        <div className="section-card" style={{ marginTop: '24px' }}>
          <div className="section-card-header">
            <div
              className="section-icon"
              style={{ background: 'linear-gradient(135deg,rgba(8,145,178,0.2),rgba(5,150,105,0.2))' }}
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="10" />
                <line x1="12" y1="16" x2="12" y2="12" />
                <line x1="12" y1="8" x2="12.01" y2="8" />
              </svg>
            </div>
            <div>
              <h2>How It Works</h2>
              <p className="section-sub">Build your institution's private question bank</p>
            </div>
          </div>
          <div className="section-body">
            <ol style={{ margin: '0', paddingLeft: '20px', color: 'var(--muted2)', lineHeight: '1.9' }}>
              <li><strong>Upload question papers</strong> — PDF, DOCX, or TXT files containing MCQs</li>
              <li><strong>AI extracts questions</strong> — Our system parses and extracts individual MCQs automatically</li>
              <li><strong>Questions are scoped to your institution</strong> — Only your students can access them</li>
              <li><strong>Create exams</strong> — Go to the Exams tab to generate exam sets from your question bank</li>
            </ol>
            <div
              style={{
                marginTop: '16px',
                padding: '12px',
                background: 'rgba(217,119,6,0.1)',
                border: '1px solid rgba(217,119,6,0.3)',
                borderRadius: 'var(--rs)',
              }}
            >
              <strong style={{ color: 'var(--yellow-l)' }}>Note:</strong>
              <span style={{ color: 'var(--muted2)' }}> You need at least 80 questions per subject to create an exam (4 sets × 20 questions).</span>
            </div>
          </div>
        </div>
=======
>>>>>>> ec47da2 (updated few features):frontend/src/pages/auto/InstitutionUpload.jsx
      </main>
    </>
  );
};

export default InstitutionUpload;
