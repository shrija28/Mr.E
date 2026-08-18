// Mr.E Admin — Core App Logic
// RAG API Integration Layer + Shared Utilities

// ── Constants ────────────────────────────────────────────────────────────────
const API_BASE = '/api';
const ADMIN_UPLOAD_URL = `${API_BASE}/admin/upload`;
const ADMIN_UPLOAD_SINGLE_URL = `${API_BASE}/admin/upload/single`;
const ADMIN_UPLOAD_FILES_URL = `${API_BASE}/admin/upload/files`;
const ADMIN_GENERATE_URL = `${API_BASE}/admin/generate`;

// ── Local Storage Store (UI state only, no auth/endpoint config) ─────────────
const Store = {
  get: k => { try { return JSON.parse(localStorage.getItem('ef_' + k)); } catch { return null; } },
  set: (k, v) => localStorage.setItem('ef_' + k, JSON.stringify(v)),
  del: k => localStorage.removeItem('ef_' + k),
  clear: () => Object.keys(localStorage).filter(k => k.startsWith('ef_')).forEach(k => localStorage.removeItem(k))
};

// ── RAG API Client ───────────────────────────────────────────────────────────
const RAG = {
  headers() {
    return { 'Content-Type': 'application/json' };
  },

  async health() {
    const res = await fetch(`${API_BASE}/health`, {
      headers: this.headers(),
      credentials: 'include'
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  },

  // POST /api/admin/upload — send PYQ files to RAG backend (admin only) — batch
  async uploadDocs(files, subject, fileType = 'question_paper') {
    if (!subject) throw new Error('Subject is required for upload');
    const form = new FormData();
    files.forEach(f => form.append('files', f));
    form.append('subject', subject);
    form.append('file_type', fileType);
    const res = await fetch(ADMIN_UPLOAD_URL, {
      method: 'POST',
      body: form,
      credentials: 'include'
    });
    if (!res.ok) throw new Error(`Upload failed: HTTP ${res.status}`);
    return res.json();
  },

  // POST /api/admin/upload/single — upload one file at a time for progress tracking
  async uploadSingleFile(file, subject, fileType = 'question_paper') {
    if (!subject) throw new Error('Subject is required for upload');
    const form = new FormData();
    form.append('file', file);
    form.append('subject', subject);
    form.append('file_type', fileType);
    const res = await fetch(ADMIN_UPLOAD_SINGLE_URL, {
      method: 'POST',
      body: form,
      credentials: 'include'
    });
    if (!res.ok) throw new Error(`Upload failed: HTTP ${res.status}`);
    return res.json();
  },

  // GET /api/admin/upload/files?subject=X — list indexed files
  async getIndexedFiles(subject) {
    if (!subject) throw new Error('Subject is required');
    const res = await fetch(`${ADMIN_UPLOAD_FILES_URL}?subject=${encodeURIComponent(subject)}`, {
      credentials: 'include'
    });
    if (!res.ok) throw new Error(`Failed to fetch indexed files: HTTP ${res.status}`);
    return res.json();
  },

  // POST /api/admin/generate — generate question sets (admin only)
  async generate(payload) {
    if (!payload.subject) throw new Error('Subject is required for generation');
    const res = await fetch(ADMIN_GENERATE_URL, {
      method: 'POST',
      headers: this.headers(),
      body: JSON.stringify(payload),
      credentials: 'include'
    });
    if (!res.ok) {
      let errMsg = `Generation failed: HTTP ${res.status}`;
      try {
        const errData = await res.json();
        if (errData.message) errMsg = errData.message;
        else if (errData.error) errMsg = errData.error;
      } catch (e) { /* response wasn't JSON */ }
      throw new Error(errMsg);
    }
    return res.json();
  },

  // POST /api/student/submit — analyze student answers
  async analyze(payload) {
    const res = await fetch(`${API_BASE}/student/submit`, {
      method: 'POST',
      headers: this.headers(),
      body: JSON.stringify(payload),
      credentials: 'include'
    });
    if (!res.ok) throw new Error(`Analysis failed: HTTP ${res.status}`);
    return res.json();
  }
};

// ── Helpers ──────────────────────────────────────────────────────────────────
function getMarks(type) {
  return { MCQ:'1 mark','True/False':'1 mark','Short Answer':'3 marks','Long Answer':'8 marks','Fill in the Blank':'2 marks' }[type] || '1 mark';
}
function getMarksNum(type) {
  return { MCQ:1,'True/False':1,'Short Answer':3,'Long Answer':8,'Fill in the Blank':2 }[type] || 1;
}
function delay(ms) { return new Promise(r => setTimeout(r, ms)); }
function showToast(msg, type = '') {
  document.querySelectorAll('.toast').forEach(t => t.remove());
  const t = document.createElement('div');
  t.className = `toast ${type}`;
  t.textContent = msg;
  document.body.appendChild(t);
  setTimeout(() => t?.remove(), 3500);
}
function distributeCounts(total, types) {
  const d = {}; const base = Math.floor(total / types.length); let rem = total - base * types.length;
  types.forEach(t => { d[t] = base; });
  types.forEach(t => { if (rem-- > 0) d[t]++; });
  return d;
}
function seededShuffle(arr, seed) {
  const a = [...arr]; let s = seed + 42;
  for (let i = a.length - 1; i > 0; i--) {
    s = (s * 1664525 + 1013904223) & 0xffffffff;
    const j = Math.abs(s) % (i + 1);
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

function localAnalyze(questions, answers) {
  let total = 0, earned = 0;
  const topicScores = {}, typeScores = {}, questionResults = [];
  questions.forEach((q, i) => {
    const m = getMarksNum(q.type);
    total += m;
    const topic = q.topic || 'General';
    const type = q.type;
    if (!topicScores[topic]) topicScores[topic] = { earned: 0, total: 0 };
    if (!typeScores[type]) typeScores[type] = { earned: 0, total: 0 };
    topicScores[topic].total += m;
    typeScores[type].total += m;
    const given = answers[i];
    let e = 0, status = 'wrong';
    if (given === undefined || given === '') { status = 'unanswered'; }
    else if (q.type === 'MCQ') { if (given === q.ans) { e = m; status = 'correct'; } }
    else if (q.type === 'True/False') { if (given === q.ans) { e = m; status = 'correct'; } }
    else {
      const kw = (String(q.ans || '')).toLowerCase().split(/[\s,./]+/).filter(w => w.length > 3);
      const gl = (String(given || '')).toLowerCase();
      const ratio = kw.length > 0 ? kw.filter(k => gl.includes(k)).length / kw.length : 0;
      if (ratio >= 0.6) { e = m; status = 'correct'; }
      else if (ratio >= 0.3) { e = Math.floor(m * 0.5); status = 'partial'; }
    }
    earned += e;
    topicScores[topic].earned += e;
    typeScores[type].earned += e;
    questionResults.push({ q: q.q, type, topic, given, correctAns: q.ans, earned: e, marks: m, status, opts: q.opts, exp: q.exp });
  });
  const pct = Math.round((earned / total) * 100);
  const strong = [], canImprove = [], weak = [];
  Object.entries(topicScores).forEach(([t, s]) => {
    const p = s.total > 0 ? Math.round((s.earned / s.total) * 100) : 0;
    if (p >= 70) strong.push({ topic: t, pct: p });
    else if (p >= 40) canImprove.push({ topic: t, pct: p });
    else weak.push({ topic: t, pct: p });
  });
  const avgScore = pct;
  let rec = avgScore >= 75 ? `Excellent performance (${avgScore}%). ` : avgScore >= 50 ? `Good effort (${avgScore}%). ` : `Needs improvement (${avgScore}%). `;
  if (weak.length) rec += `Focus on: ${weak.map(w => w.topic).join(', ')}. `;
  if (canImprove.length) rec += `Can improve: ${canImprove.map(c => c.topic).join(', ')}.`;
  return { percentage: pct, earnedMarks: earned, totalMarks: total, topicScores, typeScores, strong, canImprove, weak, questionResults, pass: pct >= 40, recommendation: rec };
}

// ═══════════════════════════════════════════════════════════════════════════
// ADMIN UPLOAD PAGE LOGIC (admin-upload.html)
// ═══════════════════════════════════════════════════════════════════════════
if (document.getElementById('dropZone')) {
  let uploadedFiles = [];
  const FIXED_COUNT = 20;
  let generatedSets = [];
  let currentSetView = 0;

  window.toggleSection = id => {
    const el = document.getElementById(id);
    if (el) el.style.display = el.style.display === 'none' ? 'block' : 'none';
  };

  // ── Subject Validation Helper ─────────────────────────────────────────────
  function getSelectedSubject() {
    const select = document.getElementById('subjectSelect');
    return select ? select.value : '';
  }

  function requireSubject(action) {
    const subject = getSelectedSubject();
    if (!subject) {
      showToast(`⚠️ Please select a subject before ${action}`, 'warning');
      const select = document.getElementById('subjectSelect');
      if (select) select.focus();
      return null;
    }
    return subject;
  }

  // ── Subject Change Handler ────────────────────────────────────────────────
  const subjectSelect = document.getElementById('subjectSelect');
  if (subjectSelect) {
    subjectSelect.addEventListener('change', () => {
      // Clear file queue on subject change
      uploadedFiles = [];
      renderFiles();

      // Load indexed files for the new subject
      const subject = getSelectedSubject();
      if (subject) {
        loadIndexedFiles(subject);
      } else {
        // Hide indexed files section if no subject selected
        const section = document.getElementById('indexedFilesSection');
        if (section) section.style.display = 'none';
      }
    });
  }

  // ── Load Indexed Files ────────────────────────────────────────────────────
  async function loadIndexedFiles(subject) {
    const section = document.getElementById('indexedFilesSection');
    const grid = document.getElementById('indexedFileGrid');
    if (!section || !grid) return;

    try {
      const data = await RAG.getIndexedFiles(subject);
      const files = data.files || [];

      if (files.length === 0) {
        section.style.display = 'none';
        return;
      }

      section.style.display = 'block';
      grid.innerHTML = files.map(f => {
        const sizeStr = f.file_size >= 1024 * 1024
          ? (f.file_size / (1024 * 1024)).toFixed(1) + ' MB'
          : (f.file_size / 1024).toFixed(1) + ' KB';
        const dateStr = f.indexed_at
          ? new Date(f.indexed_at).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })
          : '';
        return `
          <div class="file-card" style="border-color: #22c55e; background: rgba(34,197,94,0.05);">
            <div class="file-card-icon" style="color: #22c55e;">✓</div>
            <div class="file-card-info">
              <div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap;">
                <div class="file-card-name" style="margin: 0;">${f.filename}</div>
                <span style="font-size: 0.62rem; padding: 1px 6px; border-radius: 4px; font-weight: bold; background: ${f.file_type === 'textbook' ? '#8b5cf6' : '#3b82f6'}; color: #fff; text-transform: uppercase;">
                  ${f.file_type === 'textbook' ? 'Textbook' : 'PYQ'}
                </span>
              </div>
              <div class="file-card-size">${sizeStr} · ${f.chunk_count} chunks</div>
              <div class="file-card-status" style="color: #22c55e;">Indexed ${dateStr}</div>
            </div>
          </div>`;
      }).join('');

      // Show generate button if there are indexed files
      document.getElementById('genBtn').style.display = 'flex';
    } catch (e) {
      console.log('Could not load indexed files:', e.message);
      section.style.display = 'none';
    }
  }

  // ── File Upload ───────────────────────────────────────────────────────────
  const dropZone = document.getElementById('dropZone');
  dropZone.addEventListener('dragover', e => { e.preventDefault(); dropZone.closest('.drop-zone').classList.add('drag-over'); });
  dropZone.addEventListener('dragleave', () => dropZone.closest('.drop-zone').classList.remove('drag-over'));
  dropZone.addEventListener('drop', e => { e.preventDefault(); dropZone.closest('.drop-zone').classList.remove('drag-over'); handleFiles([...e.dataTransfer.files]); });
  document.getElementById('fileInput').addEventListener('change', e => handleFiles([...e.target.files]));

  function handleFiles(files) {
    files.forEach(f => {
      if (uploadedFiles.length >= 10) { showToast('⚠️ Maximum 10 files allowed'); return; }
      if (uploadedFiles.find(x => x.name === f.name)) return;
      uploadedFiles.push(f);
    });
    renderFiles();
  }

  function renderFiles() {
    const grid = document.getElementById('fileGrid');
    grid.innerHTML = uploadedFiles.map((f, i) => `
      <div class="file-card" id="fc${i}">
        <div class="file-card-icon">📄</div>
        <div class="file-card-info">
          <div class="file-card-name">${f.name}</div>
          <div class="file-card-size">${(f.size/1024).toFixed(1)} KB</div>
          <div class="file-card-status" id="fc${i}-status">✓ Ready to upload</div>
        </div>
        <button class="file-card-remove" onclick="removeFile(${i})">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
        </button>
      </div>`).join('');
    const pct = (uploadedFiles.length / 10) * 100;
    document.getElementById('uploadBarFill').style.width = pct + '%';
    document.getElementById('fileCount').textContent = uploadedFiles.length;
    document.getElementById('uploadToRAGBtn').style.display = uploadedFiles.length > 0 ? 'inline-flex' : 'none';
    // Show generate button when files have been uploaded to backend
    const hasBackendData = localStorage.getItem('ef_backendChunks') || '0';
    document.getElementById('genBtn').style.display = (parseInt(hasBackendData) > 0) ? 'flex' : 'none';
  }

  window.removeFile = i => { uploadedFiles.splice(i, 1); renderFiles(); };

  // ── Per-file status update helper ─────────────────────────────────────────
  function updateFileStatus(index, statusText, statusClass) {
    const statusEl = document.getElementById(`fc${index}-status`);
    if (statusEl) {
      statusEl.textContent = statusText;
      statusEl.className = 'file-card-status';
      if (statusClass) statusEl.style.color = statusClass;
    }
    const cardEl = document.getElementById(`fc${index}`);
    if (cardEl && statusClass === '#22c55e') {
      cardEl.style.borderColor = '#22c55e';
      cardEl.style.background = 'rgba(34,197,94,0.05)';
    }
  }

  // ── Upload files one at a time for progress tracking ──────────────────────
  window.uploadToRAG = async () => {
    const subject = getSelectedSubject();
    if (!subject) { showToast('⚠️ Please select a subject first', 'error'); return; }
    const fileType = document.getElementById('fileTypeSelect')?.value || 'question_paper';
    console.log('Files ready:', uploadedFiles.length);
    console.log('Subject:', subject);
    console.log('File Type:', fileType);

    if (uploadedFiles.length === 0) { showToast('⚠️ No files selected'); return; }

    const btn = document.getElementById('uploadToRAGBtn');
    btn.disabled = true;
    btn.innerHTML = '⏳ Uploading...';

    // Remove the remove buttons during upload
    document.querySelectorAll('.file-card-remove').forEach(el => el.style.display = 'none');

    let totalChunks = 0;
    let indexedCount = 0;
    let duplicateCount = 0;
    let errorCount = 0;

    try {
      // Step 1: Test connectivity
      console.log('1️⃣ Testing backend connectivity...');
      const healthTest = await Promise.race([
        fetch(`${API_BASE}/health`, { credentials: 'include' }),
        new Promise((_, reject) => setTimeout(() => reject(new Error('Health check timeout')), 8000))
      ]);

      if (!healthTest.ok) {
        throw new Error(`Backend health check failed: HTTP ${healthTest.status}`);
      }
      console.log('✅ Backend is accessible');

      // Step 2: Upload files one at a time
      for (let i = 0; i < uploadedFiles.length; i++) {
        const file = uploadedFiles[i];
        btn.innerHTML = `⏳ Processing ${i + 1}/${uploadedFiles.length}...`;

        // Update status: Uploading
        updateFileStatus(i, '⏳ Uploading...', '#f59e0b');

        try {
          // Update status: Extracting
          updateFileStatus(i, '📖 Extracting text...', '#3b82f6');

          const result = await RAG.uploadSingleFile(file, subject, fileType);
          console.log(`File ${i + 1} result:`, result);

          if (result.status === 'indexed') {
            const qInfo = result.questions_extracted ? `, ${result.questions_extracted} MCQs` : '';
            updateFileStatus(i, `✓ Indexed (${result.chunk_count} chunks${qInfo})`, '#22c55e');
            totalChunks += result.chunk_count;
            indexedCount++;
          } else if (result.status === 'duplicate') {
            updateFileStatus(i, `⚡ Already indexed (${result.chunk_count} chunks)`, '#8b5cf6');
            duplicateCount++;
          } else if (result.status === 'unsupported') {
            updateFileStatus(i, '⚠️ Unsupported file type', '#f59e0b');
            errorCount++;
          } else if (result.status === 'empty') {
            updateFileStatus(i, '⚠️ No text extracted', '#f59e0b');
            errorCount++;
          }
        } catch (fileErr) {
          console.error(`Error uploading file ${i + 1}:`, fileErr);
          updateFileStatus(i, '❌ Upload failed', '#ef4444');
          errorCount++;
        }
      }

      // Step 3: Summary
      localStorage.setItem('ef_backendChunks', totalChunks);

      let summaryParts = [];
      if (indexedCount > 0) summaryParts.push(`${indexedCount} indexed`);
      if (duplicateCount > 0) summaryParts.push(`${duplicateCount} duplicates skipped`);
      if (errorCount > 0) summaryParts.push(`${errorCount} failed`);

      if (indexedCount > 0) {
        showToast(`✅ ${summaryParts.join(', ')} — ${totalChunks} total chunks for ${subject}`, 'success');
        document.getElementById('genBtn').style.display = 'flex';
      } else if (duplicateCount > 0 && errorCount === 0) {
        showToast(`⚡ All files already indexed for ${subject}`, 'success');
        document.getElementById('genBtn').style.display = 'flex';
      } else {
        showToast(`⚠️ ${summaryParts.join(', ')}. Try different files.`, 'warning');
      }

      // Refresh indexed files list
      loadIndexedFiles(subject);

      // Clear the upload queue after successful processing
      uploadedFiles = [];
      renderFiles();

    } catch (e) {
      console.error('❌ Upload error:', e.message);

      let friendlyMsg = e.message;
      if (e.message.includes('Failed to fetch')) {
        friendlyMsg = '❌ Cannot reach backend. Is the server running?';
      } else if (e.message.includes('timeout')) {
        friendlyMsg = '❌ Upload timed out. Files may be too large or network is slow.';
      } else if (e.message.includes('HTTP 401') || e.message.includes('HTTP 403')) {
        friendlyMsg = '❌ Authentication error. Please log in again.';
      } else if (e.message.includes('HTTP')) {
        friendlyMsg = `❌ Server error: ${e.message}`;
      }

      showToast(friendlyMsg, 'error');
    } finally {
      btn.disabled = false;
      btn.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg> Send to Backend`;
    }
  };

  // ── Generate ──────────────────────────────────────────────────────────────
  window.generatePapers = async () => {
    // Require subject selection before generation
    const subject = requireSubject('generating questions');
    if (!subject) return;

    const types = ['MCQ'];
    const count = FIXED_COUNT;
    const difficulty = 'medium';
    const btn = document.getElementById('genBtn');
    btn.disabled = true;
    document.getElementById('genProgress').style.display = 'block';
    document.getElementById('setsOutput').style.display = 'none';

    const steps = ['Initializing RAG pipeline...','Retrieving relevant chunks...','Extracting question patterns...','Generating Set A...','Generating Set B...','Generating Set C...','Generating Set D...','Applying difficulty calibration...','Deduplicating questions...','Finalizing paper sets...'];
    const stepsEl = document.getElementById('genSteps');
    stepsEl.innerHTML = steps.map((s, i) => `<span class="gen-step" id="gs${i}">${s}</span>`).join('');

    async function tick(i, pct) {
      await delay(380);
      document.getElementById(`gs${i}`)?.classList.add('active');
      document.getElementById('genBarFill').style.width = pct + '%';
      document.getElementById('genBarLabel').textContent = steps[i];
      if (i > 0) document.getElementById(`gs${i-1}`)?.classList.replace('active','done');
    }

    for (let i = 0; i < steps.length; i++) await tick(i, ((i+1)/steps.length)*100);

    try {
      console.log(`🔄 Calling /api/admin/generate for subject: ${subject}...`);
      const data = await RAG.generate({ difficulty, count, types, subject, num_sets: 4 });

      // Handle generation success
      if (data.sets && data.sets.length) {
        // New format: sets are returned directly from DB-driven generation
        generatedSets = data.sets;
        if (data.added && data.added > 0) {
          showToast(`✅ ${data.added} questions organized into 4 sets for ${subject}!`, 'success');
        }
      } else if (data.added && data.added > 0) {
        // Legacy format: questions added to DB but no sets returned for display
        showToast(`✅ ${data.added} questions added to ${subject} question bank!`, 'success');
        generatedSets = [];
      } else if (data.added === 0 || data.warning) {
        // Zero-question completion — show warning state
        showToast(data.warning || '⚠️ No questions available. Upload question papers first.', 'warning');
        btn.disabled = false;
        document.getElementById('genProgress').style.display = 'none';
        return;
      } else {
        generatedSets = [];
      }
    } catch (e) {
      console.error('❌ Generation error:', e);
      showToast(`❌ ${e.message}`, 'error');
      generatedSets = [];
    }

    const config = { difficulty, count, types, subject, sets: generatedSets };
    Store.set('examConfig', config);

    btn.disabled = false;
    document.getElementById('genProgress').style.display = 'none';

    // Check if any sets have questions
    const totalQuestions = generatedSets.reduce((sum, set) => sum + (set ? set.length : 0), 0);
    if (totalQuestions === 0) {
      if (!generatedSets.length) {
        showToast('❌ No questions generated. Try uploading different papers.', 'error');
      }
      console.error('❌ All sets are empty:', generatedSets);
      return;
    }

    document.getElementById('setsOutput').style.display = 'block';
    ['A','B','C','D'].forEach((l,i) => {
      const count = generatedSets[i]?.length || 0;
      document.getElementById(`tabCount${i}`).textContent = count > 0 ? `${count} Qs` : 'Empty';
    });

    // Show first non-empty set
    let firstSet = 0;
    for (let i = 0; i < generatedSets.length; i++) {
      if (generatedSets[i] && generatedSets[i].length > 0) {
        firstSet = i;
        break;
      }
    }
    showSet(firstSet);
    document.getElementById('setsOutput').scrollIntoView({ behavior:'smooth' });
    console.log('✅ Sets generated successfully:', generatedSets.map((s,i) => `Set ${['A','B','C','D'][i]}: ${s?.length || 0} questions`).join(', '));

    // Clear the upload queue after sets are displayed
    uploadedFiles = [];
    renderFiles();
  };

  window.showSet = i => {
    currentSetView = i;
    document.querySelectorAll('.set-tab').forEach((t,idx) => t.classList.toggle('active', idx === i));
    const config = Store.get('examConfig');
    if (!config) return;
    renderPreview(config.sets[i], i, config);
  };

  function renderPreview(questions, setIdx, config) {
    const L = ['A','B','C','D'];
    const types = [...new Set(questions.map(q => q.type))];
    let html = `<div class="preview-paper-title">
      <h3>${config.subject} — Set ${L[setIdx]}</h3>
      <p>Difficulty: ${config.difficulty.charAt(0).toUpperCase()+config.difficulty.slice(1)} &nbsp;|&nbsp; ${questions.length} Questions &nbsp;|&nbsp; Total Marks: ${questions.reduce((s,q)=>s+getMarksNum(q.type),0)}</p>
    </div>
    <div class="preview-meta-row">
      <span>Set: ${L[setIdx]}</span>
      <span>Types: ${config.types.join(', ')}</span>
      <span>Date: ${new Date().toLocaleDateString('en-IN')}</span>
    </div>`;
    let n = 1;
    types.forEach((type, ti) => {
      const qs = questions.filter(q => q.type === type);
      html += `<div class="preview-section-head">Section ${String.fromCharCode(65+ti)} — ${type} (${getMarks(type)} each)</div>`;
      qs.forEach(q => {
        html += `<div class="preview-q-row">
          <div class="preview-q-num">${n++}</div>
          <div class="preview-q-body">${q.q}
            ${q.type==='MCQ'?`<div class="preview-opts">${q.opts.map((o,i)=>`<div class="preview-opt">${['A','B','C','D'][i]}) ${o}</div>`).join('')}</div>`:''}
            ${q.type==='True/False'?`<div style="font-size:0.75rem;color:var(--muted);margin-top:4px">[ True / False ]</div>`:''}
            ${q.type==='Fill in the Blank'?`<div style="font-size:0.75rem;color:var(--muted);margin-top:4px">Answer: ___________</div>`:''}
          </div>
          <div class="preview-marks">${getMarks(type)}</div>
        </div>`;
      });
    });
    document.getElementById('paperPreview').innerHTML = html;
  }

  window.downloadAll = () => {
    const config = Store.get('examConfig');
    if (!config) return;
    const L = ['A','B','C','D'];
    config.sets.forEach((set, i) => {
      let txt = `${config.subject} — Set ${L[i]}\nDifficulty: ${config.difficulty}\n${'─'.repeat(50)}\n\n`;
      set.forEach((q, idx) => {
        txt += `${idx+1}. [${q.type}] ${q.q}\n`;
        if (q.type==='MCQ') q.opts.forEach((o,oi)=>{ txt+=`   ${['A','B','C','D'][oi]}) ${o}\n`; });
        txt += '\n';
      });
      const a = document.createElement('a');
      a.href = URL.createObjectURL(new Blob([txt],{type:'text/plain'}));
      a.download = `Set_${L[i]}_${config.subject.replace(/\s+/g,'_')}.txt`;
      a.click();
    });
    showToast('⬇️ Downloading all 4 sets...');
  };
}
