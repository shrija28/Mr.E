// ═══════════════════════════════════════════════════════════════════════════
// ADMIN ANALYTICS PAGE — Aggregate analytics across all students
// Reuses Chart.js patterns from dashboard.js
// Requirements: 12.1, 12.2, 12.3, 12.4, 12.5, 12.6, 11.5, 15.3
// ═══════════════════════════════════════════════════════════════════════════

let charts = {};
let allSubmissions = [];
let filteredSubs = [];
let leaderboardEntries = [];
let sortKey = 'score';
let sortDir = -1;

const CHART_DEFAULTS = {
  color: '#e8e8f4',
  grid: 'rgba(255,255,255,0.05)',
  muted: '#6868a0',
  font: { family: "'Segoe UI', system-ui, sans-serif", size: 11 }
};

Chart.defaults.color = CHART_DEFAULTS.color;
Chart.defaults.font.family = CHART_DEFAULTS.font.family;
Chart.defaults.font.size = CHART_DEFAULTS.font.size;

// ── API Helpers ──────────────────────────────────────────────────────────────

async function fetchAnalytics(params = {}) {
  const query = new URLSearchParams();
  if (params.subject && params.subject !== 'all') query.set('subject', params.subject);
  if (params.student && params.student !== 'all') query.set('student', params.student);
  if (params.set && params.set !== 'all') query.set('set', params.set);
  if (params.status && params.status !== 'all') query.set('status', params.status);
  query.set('limit', '500');

  const res = await fetch(`/api/admin/analytics?${query.toString()}`, { credentials: 'include' });
  if (!res.ok) throw new Error(`Analytics fetch failed: ${res.status}`);
  return res.json();
}

async function fetchLeaderboard(subject) {
  const query = new URLSearchParams();
  if (subject && subject !== 'all') query.set('subject', subject);

  const res = await fetch(`/api/admin/leaderboard?${query.toString()}`, { credentials: 'include' });
  if (!res.ok) throw new Error(`Leaderboard fetch failed: ${res.status}`);
  return res.json();
}

// ── Init ─────────────────────────────────────────────────────────────────────

async function initAnalytics() {
  document.getElementById('lastUpdated').textContent = `Last updated: ${new Date().toLocaleTimeString()}`;

  try {
    await applyFilters();
  } catch (err) {
    console.error('Failed to load analytics:', err);
    showEmptyState('Failed to load analytics data. Please try again.');
  }
}

function showEmptyState(message) {
  document.getElementById('emptyState').style.display = 'block';
  document.getElementById('dashContent').querySelector('.kpi-row').style.display = 'none';
  document.querySelectorAll('.charts-row').forEach(el => el.style.display = 'none');
  document.querySelectorAll('.results-card').forEach(el => el.style.display = 'none');
  if (message) {
    document.querySelector('#emptyState p').textContent = message;
  }
}

function hideEmptyState() {
  document.getElementById('emptyState').style.display = 'none';
  document.getElementById('dashContent').querySelector('.kpi-row').style.display = '';
  document.querySelectorAll('.charts-row').forEach(el => el.style.display = '');
  document.querySelectorAll('.results-card').forEach(el => el.style.display = '');
}

// ── Filters ──────────────────────────────────────────────────────────────────

window.applyFilters = async () => {
  const subject = document.getElementById('filterSubject').value;
  const student = document.getElementById('filterStudent').value;
  const set = document.getElementById('filterSet').value;
  const status = document.getElementById('filterStatus').value;

  try {
    const data = await fetchAnalytics({ subject, student, set, status });

    allSubmissions = data.submissions || [];
    filteredSubs = allSubmissions;

    // REQ-12.6: When filtered subset is empty, show empty-state and do NOT render charts
    if (data.empty || filteredSubs.length === 0) {
      destroyCharts();
      showEmptyState('No submissions match the current filter criteria. Try adjusting the filters above.');
      updateExportButton(true);
      document.getElementById('tableFooter').textContent = 'Showing 0 submissions';
      document.getElementById('resultsBody').innerHTML = '';
      return;
    }

    hideEmptyState();
    updateExportButton(false);
    populateStudentFilter(filteredSubs);
    updateKPIs();
    renderCharts();
    renderTable();

    // Fetch leaderboard data
    const lbData = await fetchLeaderboard(subject);
    leaderboardEntries = lbData.entries || [];
    renderLeaderboard();

  } catch (err) {
    console.error('Filter error:', err);
    showEmptyState('Failed to load analytics data. Please try again.');
  }
};

window.refreshAnalytics = () => {
  destroyCharts();
  initAnalytics();
};

// ── Export Button State ──────────────────────────────────────────────────────

function updateExportButton(disabled) {
  const btn = document.getElementById('exportBtn');
  if (btn) {
    btn.disabled = disabled;
    btn.style.opacity = disabled ? '0.5' : '1';
    btn.style.pointerEvents = disabled ? 'none' : 'auto';
  }
}

// ── Student Filter Population ────────────────────────────────────────────────

function populateStudentFilter(subs) {
  const sel = document.getElementById('filterStudent');
  const currentVal = sel.value;
  const seen = new Set();

  // Keep existing options if already populated
  if (sel.options.length > 1) return;

  sel.innerHTML = '<option value="all">All Students</option>';
  subs.forEach(s => {
    const id = s.kcet_student_id;
    if (id && !seen.has(id)) {
      seen.add(id);
      const o = document.createElement('option');
      o.value = id;
      o.textContent = `${s.student_name} (${id})`;
      sel.appendChild(o);
    }
  });

  // Restore selection
  if (currentVal && currentVal !== 'all') {
    sel.value = currentVal;
  }
}

// ── KPIs ─────────────────────────────────────────────────────────────────────

function updateKPIs() {
  const subs = filteredSubs;
  if (!subs.length) return;

  const students = new Set(subs.map(s => s.kcet_student_id)).size;
  const avgScore = Math.round(subs.reduce((a, s) => a + s.score_pct, 0) / subs.length);
  const passRate = Math.round(subs.filter(s => s.pass_flag).length / subs.length * 100);
  const avgTime = Math.round(subs.reduce((a, s) => a + s.time_taken_sec, 0) / subs.length / 60);

  document.getElementById('kpiStudents').textContent = students;
  document.getElementById('kpiSubmissions').textContent = subs.length;
  document.getElementById('kpiAvgScore').textContent = avgScore + '%';
  document.getElementById('kpiPassRate').textContent = passRate + '%';
  document.getElementById('kpiAvgTime').textContent = avgTime + 'm';
}

// ── Charts ───────────────────────────────────────────────────────────────────

function destroyCharts() {
  Object.values(charts).forEach(c => { try { c.destroy(); } catch {} });
  charts = {};
}

function renderCharts() {
  destroyCharts();
  const subs = filteredSubs;
  
  // Hide or show chart wrappers based on data availability
  ['scoreDistChart', 'subjectChart', 'passChart'].forEach(id => {
    const el = document.getElementById(id);
    if (el) {
      const wrap = el.closest('.chart-wrap');
      if (wrap) wrap.style.display = subs.length ? 'block' : 'none';
    }
  });

  if (!subs.length) return;

  // Score Distribution Histogram
  const buckets = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]; // 0-10, 10-20, ..., 90-100
  subs.forEach(s => {
    const idx = Math.min(Math.floor(s.score_pct / 10), 9);
    buckets[idx]++;
  });
  charts.scoreDist = new Chart(document.getElementById('scoreDistChart'), {
    type: 'bar',
    data: {
      labels: ['0-10%', '10-20%', '20-30%', '30-40%', '40-50%', '50-60%', '60-70%', '70-80%', '80-90%', '90-100%'],
      datasets: [{
        label: 'Students',
        data: buckets,
        backgroundColor: buckets.map((_, i) => {
          if (i < 3) return 'rgba(220,38,38,0.7)';
          if (i < 5) return 'rgba(251,191,36,0.7)';
          return 'rgba(52,211,153,0.7)';
        }),
        borderRadius: 6,
        borderSkipped: false
      }]
    },
    options: { ...baseChartOpts(), plugins: { legend: { display: false } } }
  });

  // Subject-wise Average Score
  const subjects = ['Biology', 'Physics', 'Chemistry', 'Mathematics'];
  const subjectData = subjects.map(subj => {
    const f = subs.filter(s => s.subject === subj);
    return f.length ? Math.round(f.reduce((a, s) => a + s.score_pct, 0) / f.length) : 0;
  });
  charts.subject = new Chart(document.getElementById('subjectChart'), {
    type: 'bar',
    data: {
      labels: subjects,
      datasets: [{
        label: 'Avg Score %',
        data: subjectData,
        backgroundColor: ['rgba(124,58,237,0.7)', 'rgba(37,99,235,0.7)', 'rgba(8,145,178,0.7)', 'rgba(5,150,105,0.7)'],
        borderRadius: 6,
        borderSkipped: false
      }]
    },
    options: { ...baseChartOpts(), plugins: { legend: { display: false } } }
  });

  // Pass vs Fail Doughnut
  const pass = subs.filter(s => s.pass_flag).length;
  charts.pass = new Chart(document.getElementById('passChart'), {
    type: 'doughnut',
    data: {
      labels: ['Pass', 'Fail'],
      datasets: [{
        data: [pass, subs.length - pass],
        backgroundColor: ['rgba(5,150,105,0.8)', 'rgba(220,38,38,0.8)'],
        borderWidth: 0,
        hoverOffset: 6
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { position: 'bottom', labels: { color: CHART_DEFAULTS.color, padding: 12 } } }
    }
  });
}

function baseChartOpts() {
  return {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { labels: { color: CHART_DEFAULTS.color } } },
    scales: {
      x: { grid: { color: CHART_DEFAULTS.grid }, ticks: { color: CHART_DEFAULTS.muted } },
      y: { grid: { color: CHART_DEFAULTS.grid }, ticks: { color: CHART_DEFAULTS.muted }, beginAtZero: true }
    }
  };
}

// ── Leaderboard ──────────────────────────────────────────────────────────────

function renderLeaderboard() {
  const entries = leaderboardEntries;
  const medals = ['🥇', '🥈', '🥉'];

  // Bar chart for top entries
  if (charts.leaderboard) { try { charts.leaderboard.destroy(); } catch {} }

  const chartEntries = entries.slice(0, 10); // Show top 10 in chart
  const chartWrapper = document.getElementById('leaderboardChart')?.closest('.chart-wrap');
  if (chartWrapper) chartWrapper.style.display = chartEntries.length > 0 ? 'block' : 'none';

  if (chartEntries.length > 0) {
    charts.leaderboard = new Chart(document.getElementById('leaderboardChart'), {
      type: 'bar',
      data: {
        labels: chartEntries.map(e => e.display_name),
        datasets: [{
          label: 'Composite Score',
          data: chartEntries.map(e => e.composite_score),
          backgroundColor: chartEntries.map(e => {
            const s = e.composite_score;
            return s >= 70 ? 'rgba(52,211,153,0.8)' : s >= 40 ? 'rgba(251,191,36,0.8)' : 'rgba(248,113,113,0.8)';
          }),
          borderRadius: 6,
          borderSkipped: false
        }]
      },
      options: {
        ...baseChartOpts(),
        plugins: { legend: { display: false } },
        scales: {
          x: { grid: { color: CHART_DEFAULTS.grid }, ticks: { color: CHART_DEFAULTS.color } },
          y: { grid: { color: CHART_DEFAULTS.grid }, ticks: { color: CHART_DEFAULTS.muted }, min: 0, max: 100, beginAtZero: true }
        }
      }
    });
  }

  // Full ranked table (REQ-11.5)
  const tbody = document.getElementById('leaderboardBody');
  tbody.innerHTML = entries.map((e, i) => {
    const medal = i < 3 ? medals[i] : `#${e.rank}`;
    const scoreClass = e.composite_score >= 70 ? 'score-high' : e.composite_score >= 40 ? 'score-mid' : 'score-low';
    return `<tr>
      <td style="font-size:1.1rem;text-align:center">${medal}</td>
      <td><div style="font-weight:700">${e.display_name}</div></td>
      <td style="color:var(--muted)">${e.kcet_student_id}</td>
      <td><span class="score-badge ${scoreClass}">${e.composite_score.toFixed(2)}</span></td>
      <td style="color:var(--muted2)">${e.average_score.toFixed(1)}%</td>
      <td style="color:var(--muted)">${e.attempt_count}</td>
    </tr>`;
  }).join('');
}

// ── Results Table ────────────────────────────────────────────────────────────

function renderTable() {
  const search = document.getElementById('searchInput')?.value.toLowerCase() || '';
  let subs = filteredSubs.filter(s =>
    s.student_name.toLowerCase().includes(search) ||
    (s.kcet_student_id || '').toLowerCase().includes(search)
  );

  subs.sort((a, b) => {
    let va, vb;
    if (sortKey === 'score') { va = a.score_pct; vb = b.score_pct; }
    else if (sortKey === 'time') { va = a.time_taken_sec; vb = b.time_taken_sec; }
    else if (sortKey === 'name') { va = a.student_name; vb = b.student_name; }
    else if (sortKey === 'subject') { va = a.subject; vb = b.subject; }
    else if (sortKey === 'set') { va = a.set_label; vb = b.set_label; }
    else if (sortKey === 'status') { va = a.pass_flag ? 1 : 0; vb = b.pass_flag ? 1 : 0; }
    else { va = a.score_pct; vb = b.score_pct; }
    if (va < vb) return sortDir;
    if (va > vb) return -sortDir;
    return 0;
  });

  const tbody = document.getElementById('resultsBody');
  tbody.innerHTML = subs.map(s => {
    const p = Math.round(s.score_pct);
    const cls = p >= 70 ? 'score-high' : p >= 40 ? 'score-mid' : 'score-low';
    const m = Math.floor(s.time_taken_sec / 60);
    const sec = s.time_taken_sec % 60;
    return `<tr>
      <td><div style="font-weight:600">${s.student_name}</div></td>
      <td style="color:var(--muted)">${s.kcet_student_id}</td>
      <td style="color:var(--purple-l);font-weight:700">${s.subject || '—'}</td>
      <td><span style="font-weight:700;color:var(--purple-l)">${s.set_label || '—'}</span></td>
      <td><span class="score-badge ${cls}">${p}%</span></td>
      <td style="color:var(--muted)">${m}m ${sec}s</td>
      <td class="${s.pass_flag ? 'status-pass' : 'status-fail'}">${s.pass_flag ? '✅ Pass' : '❌ Fail'}</td>
      <td><button class="btn-view" onclick="openDrawer('${s.id}')">View →</button></td>
    </tr>`;
  }).join('');

  document.getElementById('tableFooter').textContent = `Showing ${subs.length} of ${allSubmissions.length} submissions`;
}

window.filterTable = () => renderTable();
window.sortTable = key => {
  if (sortKey === key) sortDir *= -1;
  else { sortKey = key; sortDir = -1; }
  renderTable();
};

// ── Detail Drawer (REQ-12.4) ─────────────────────────────────────────────────

window.openDrawer = async (submissionId) => {
  const s = filteredSubs.find(x => x.id === submissionId);
  if (!s) return;

  document.getElementById('drawerName').textContent = s.student_name;
  document.getElementById('drawerMeta').textContent = `${s.kcet_student_id} · ${s.subject || ''} · ${s.set_label || ''} · ${s.submitted_at ? new Date(s.submitted_at).toLocaleString() : '—'}`;

  const m = Math.floor(s.time_taken_sec / 60);
  const sec = s.time_taken_sec % 60;
  const p = Math.round(s.score_pct);

  document.getElementById('drawerBody').innerHTML = `
    <div class="drawer-kpi-row">
      <div class="drawer-kpi"><div class="drawer-kpi-val">${p}%</div><div class="drawer-kpi-label">Score</div></div>
      <div class="drawer-kpi"><div class="drawer-kpi-val">${m}m ${sec}s</div><div class="drawer-kpi-label">Time</div></div>
      <div class="drawer-kpi"><div class="drawer-kpi-val">${s.pass_flag ? '✅ Pass' : '❌ Fail'}</div><div class="drawer-kpi-label">Status</div></div>
    </div>
    <div class="drawer-section-title">Submission Details</div>
    <div style="background:var(--s2);border-radius:var(--rs);padding:14px;font-size:0.82rem;color:var(--muted2);line-height:1.7;margin-bottom:16px">
      <p><strong>Student:</strong> ${s.student_name} (${s.kcet_student_id})</p>
      <p><strong>Subject:</strong> ${s.subject || '—'}</p>
      <p><strong>Set:</strong> ${s.set_label || '—'}</p>
      <p><strong>Score:</strong> ${p}%</p>
      <p><strong>Time Taken:</strong> ${m}m ${sec}s</p>
      <p><strong>Submitted:</strong> ${s.submitted_at ? new Date(s.submitted_at).toLocaleString() : '—'}</p>
      <p><strong>Status:</strong> ${s.status || '—'}</p>
    </div>`;

  document.getElementById('drawerOverlay').style.display = 'block';
  document.getElementById('detailDrawer').classList.add('open');
};

window.closeDrawer = () => {
  document.getElementById('drawerOverlay').style.display = 'none';
  document.getElementById('detailDrawer').classList.remove('open');
};

// ── CSV Export (REQ-12.5) ────────────────────────────────────────────────────

window.exportReport = () => {
  const subs = filteredSubs;
  if (!subs.length) {
    showToast && showToast('No data to export');
    return;
  }

  let csv = 'Name,KCET ID,Subject,Set,Score%,Time(s),Submitted,Status\n';
  subs.forEach(s => {
    csv += `"${s.student_name}","${s.kcet_student_id}","${s.subject || ''}","${s.set_label || ''}",${Math.round(s.score_pct)},${s.time_taken_sec},"${s.submitted_at || ''}",${s.pass_flag ? 'Pass' : 'Fail'}\n`;
  });

  const a = document.createElement('a');
  a.href = URL.createObjectURL(new Blob([csv], { type: 'text/csv' }));
  a.download = `Mr.E_Admin_Report_${new Date().toISOString().slice(0, 10)}.csv`;
  a.click();

  if (typeof showToast === 'function') {
    showToast('📊 Report exported as CSV', 'success');
  }
};

// ── Toast Helper (fallback if app.js not loaded) ─────────────────────────────

if (typeof showToast === 'undefined') {
  window.showToast = (msg, type) => {
    const toast = document.createElement('div');
    toast.style.cssText = 'position:fixed;bottom:24px;right:24px;padding:12px 20px;border-radius:8px;background:var(--s2);color:var(--text);border:1px solid var(--border2);font-size:0.85rem;z-index:9999;animation:fadeIn 0.3s ease';
    toast.textContent = msg;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
  };
}

// ── Logout ───────────────────────────────────────────────────────────────────

document.getElementById('logoutBtn')?.addEventListener('click', async (e) => {
  e.preventDefault();
  try {
    await fetch('/api/auth/logout', { method: 'POST', credentials: 'include' });
  } catch {}
  window.location.href = 'login.html';
});

// ── Boot ─────────────────────────────────────────────────────────────────────

initAnalytics();
