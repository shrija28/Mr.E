// ═══════════════════════════════════════════════════════════════════════════
// STUDENT DASHBOARD PAGE LOGIC — Personal Analytics
// Fetches data from /api/student/submissions and /api/student/leaderboard/me
// ═══════════════════════════════════════════════════════════════════════════
let charts = {};
let allSubmissions = [];
let filteredSubs = [];
let leaderboardData = null;
let recommendationsData = null;
let currentRecTab = 'target';
let sortKey = 'submitted_at';
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

// ── Auto-subscription prompt for personal students ────────────────────────────
/**
 * PERSONAL STUDENT SUBSCRIPTION ONBOARDING
 * 
 * Auto-opens subscription modal for personal students (direct_subscriber) who have NO active subscription.
 * 
 * WHO SEES THIS:
 * ✅ role = student AND student_subtype = direct_subscriber AND no active subscription
 * 
 * WHO NEVER SEES THIS:
 * ❌ Institution students (student_subtype = institution_linked)
 * ❌ Personal students with active subscription (free/trial/monthly/yearly)
 * ❌ Admins
 * 
 * BEHAVIOR:
 * - Modal opens automatically after 500ms delay (allows dashboard to render first)
 * - No user click required
 * - Clean production UX (Netflix/Spotify style)
 */
async function _checkAndPromptSubscription() {
  console.log('='.repeat(80));
  console.log('[subscription-onboarding] ========== SUBSCRIPTION CHECK START ==========');
  console.log('[subscription-onboarding] Timestamp:', new Date().toISOString());
  console.log('='.repeat(80));
  
  try {
    // STEP 1: Verify required modules are loaded
    console.log('[subscription-onboarding] STEP 1: Checking module availability...');
    console.log('[subscription-onboarding]   → typeof Subscription:', typeof Subscription);
    console.log('[subscription-onboarding]   → Subscription.getStatus:', typeof Subscription !== 'undefined' ? typeof Subscription.getStatus : 'N/A');
    console.log('[subscription-onboarding]   → typeof SubscriptionModal:', typeof SubscriptionModal);
    console.log('[subscription-onboarding]   → SubscriptionModal.show:', typeof SubscriptionModal !== 'undefined' ? typeof SubscriptionModal.show : 'N/A');
    
    if (typeof Subscription === 'undefined' || typeof Subscription.getStatus !== 'function') {
      console.error('[subscription-onboarding] ❌ CRITICAL: Subscription module not loaded!');
      console.error('[subscription-onboarding]    This means subscription.js is not included in the page');
      return;
    }
    if (typeof SubscriptionModal === 'undefined' || typeof SubscriptionModal.show !== 'function') {
      console.error('[subscription-onboarding] ❌ CRITICAL: SubscriptionModal module not loaded!');
      console.error('[subscription-onboarding]    This means subscription-modal.js is not included in the page');
      return;
    }
    console.log('[subscription-onboarding] STEP 1: ✅ All modules available');

    // STEP 2: Fetch fresh subscription status (BYPASS CACHE after payment!)
    console.log('[subscription-onboarding] STEP 2: Fetching subscription status from API...');
    console.log('[subscription-onboarding]   → Calling Subscription.getStatus(true) to bypass cache');
    const sub = await Subscription.getStatus(true);  // ✅ FORCE REFRESH to bypass cache
    
    console.log('[SUB FIX] ========== SUBSCRIPTION DATA ==========');
    console.log('[SUB FIX] subscription status:', sub);
    console.log('[SUB FIX] is_active:', sub?.is_active);
    console.log('[SUB FIX] status:', sub?.status);
    console.log('[SUB FIX] has_subscription:', sub?.has_subscription);
    console.log('[SUB FIX] plan_type:', sub?.plan_type);
    console.log('[SUB FIX] plan_name:', sub?.plan_name);
    console.log('[SUB FIX] ==============================================');
    
    console.log('[subscription-onboarding] STEP 2: Subscription data received:');
    console.log('[subscription-onboarding]   → Full response:', JSON.stringify(sub, null, 2));
    console.log('[subscription-onboarding]   → is_active:', sub ? sub.is_active : 'NULL RESPONSE');
    console.log('[subscription-onboarding]   → status:', sub ? sub.status : 'NULL RESPONSE');
    console.log('[subscription-onboarding]   → plan_type:', sub ? sub.plan_type : 'NULL RESPONSE');
    console.log('[subscription-onboarding]   → plan_name:', sub ? sub.plan_name : 'NULL RESPONSE');

    // STEP 3: Apply gates - Check if user has VALID subscription
    console.log('[subscription-onboarding] STEP 3: Applying gate logic...');
    
    // Check if subscription banner is visible (extra safety gate)
    const banner = document.querySelector('.subscription-banner');
    if (banner && banner.style.display !== 'none' && !banner.classList.contains('hidden')) {
      console.log('[subscription-onboarding] GATE 0: ✅ Subscription banner visible → MODAL BLOCKED');
      console.log('[subscription-onboarding] User subscription UI is showing - modal will NOT show');
      return;
    }
    
    // Comprehensive validation: has_subscription flag OR active status check
    const hasValidSubscription = (
      // Check 1: has_subscription flag (if provided)
      (sub && sub.has_subscription === true) ||
      // Check 2: is_active flag (primary indicator)
      (sub && sub.is_active === true) ||
      // Check 3: Active status values
      (sub && ['trial', 'active', 'trialing', 'grace_period'].includes(sub.status))
    );
    
    if (hasValidSubscription) {
      console.log('[subscription-onboarding] GATE 1: ✅ VALID SUBSCRIPTION DETECTED → MODAL BLOCKED');
      console.log('[subscription-onboarding]   → has_subscription:', sub?.has_subscription);
      console.log('[subscription-onboarding]   → is_active:', sub?.is_active);
      console.log('[subscription-onboarding]   → status:', sub?.status);
      console.log('[subscription-onboarding] User has active/valid subscription - modal will NOT show');
      return;
    }
    console.log('[subscription-onboarding] GATE 1: ❌ No valid subscription → PASSED');

    // ALL GATES PASSED - User needs subscription
    console.log('='.repeat(80));
    console.log('[subscription-onboarding] 🚀 ALL GATES PASSED - USER NEEDS SUBSCRIPTION');
    console.log('[subscription-onboarding] 🚀 MODAL WILL OPEN IN 500ms');
    console.log('='.repeat(80));
    
    console.log('[SUB] OPENING MODAL');
    setTimeout(function() {
      console.log('[subscription-onboarding] STEP 4: Opening modal NOW...');
      console.log('[subscription-onboarding]   → Calling SubscriptionModal.show()');
      
      // Update modal heading for onboarding context (personalized messaging)
      const titleEl = document.getElementById('modalTitle');
      const subtitleEl = document.getElementById('modalSubtitle');
      if (titleEl) {
        titleEl.innerHTML = 'Choose Your <span class="grad">Plan</span>';
      }
      if (subtitleEl) {
        subtitleEl.textContent = 'Select the plan that best fits your exam preparation needs';
      }
      
      // Show the modal (SubscriptionModal handles all display logic)
      try {
        SubscriptionModal.show();
        console.log('[subscription-onboarding] ✅ SubscriptionModal.show() called successfully');
        console.log('[subscription-onboarding] ✅ Modal should now be visible on screen');
        
        // Verify modal is actually showing
        setTimeout(() => {
          const modalEl = document.getElementById('subscriptionModal');
          if (modalEl) {
            const isVisible = modalEl.style.display !== 'none' && modalEl.classList.contains('open');
            console.log('[subscription-onboarding] Modal visibility check:', isVisible ? '✅ VISIBLE' : '❌ NOT VISIBLE');
            console.log('[subscription-onboarding]   → display style:', modalEl.style.display);
            console.log('[subscription-onboarding]   → has .open class:', modalEl.classList.contains('open'));
          } else {
            console.error('[subscription-onboarding] ❌ #subscriptionModal element NOT FOUND in DOM!');
          }
        }, 100);
      } catch (err) {
        console.error('[subscription-onboarding] ❌ Error calling SubscriptionModal.show():', err);
        console.error('[subscription-onboarding] Stack trace:', err.stack);
      }
    }, 500);  // 500ms delay for smooth UX

  } catch (error) {
    console.error('[subscription-onboarding] ❌ FATAL ERROR during subscription check:', error);
    console.error('[subscription-onboarding] Stack trace:', error.stack);
  }
}

// ── Init ─────────────────────────────────────────────────────────────────────
async function initDashboard() {
  console.log('='.repeat(80));
  console.log('[dashboard] ==================== DASHBOARD INIT START ====================');
  console.log('[dashboard] Timestamp:', new Date().toISOString());
  console.log('='.repeat(80));
  
  // Initialize the persistent subscription banner (REQ-4.1, 4.2)
  if (typeof SubscriptionBanner !== 'undefined' && SubscriptionBanner.init) {
    try { SubscriptionBanner.init(); } catch (e) { console.error('Banner init failed:', e); }
  }

  // STEP 1: Detect role and subtype
  console.log('[dashboard] STEP 1: Fetching user info from Auth.currentRole()...');
  let currentUserRole = null;
  let currentUserSubtype = null;
  let userInfo = null;
  try {
    if (typeof Auth !== 'undefined' && Auth.currentRole) {
      userInfo = await Auth.currentRole();
      currentUserRole = userInfo && userInfo.role;
      currentUserSubtype = userInfo && userInfo.student_subtype;
      
      console.log('[dashboard] STEP 1: User info received:');
      console.log('[dashboard]   → Full response:', JSON.stringify(userInfo, null, 2));
      console.log('[dashboard]   → role:', currentUserRole);
      console.log('[dashboard]   → student_subtype:', currentUserSubtype);
      console.log('[dashboard]   → institution_id:', userInfo ? userInfo.institution_id : 'N/A');
    } else {
      console.error('[dashboard] STEP 1: Auth module NOT available!');
      console.log('[dashboard]   → typeof Auth:', typeof Auth);
      console.log('[dashboard]   → Auth.currentRole:', typeof Auth !== 'undefined' ? typeof Auth.currentRole : 'N/A');
    }
  } catch (e) { 
    console.error('[dashboard] STEP 1: Error fetching user info:', e);
    console.error('[dashboard] Stack trace:', e.stack);
  }

  console.log('[dashboard] STEP 2: Checking user type...');
  console.log('[dashboard]   → Is student?', currentUserRole === 'student');
  console.log('[dashboard]   → Is direct_subscriber?', currentUserSubtype === 'direct_subscriber');
  console.log('[dashboard]   → Is institution_linked?', currentUserSubtype === 'institution_linked');
  console.log('[dashboard]   → Is admin?', currentUserRole === 'admin' || currentUserRole === 'platform_admin');

  // Hard guard: institution students should never be on this page
  if (currentUserRole === 'student' && currentUserSubtype === 'institution_linked') {
    console.log('[dashboard.js] Institution student detected — redirecting to /student/institution/dashboard');
    window.location.replace('/student/institution/dashboard');
    return;
  }

  const isAdmin = currentUserRole === 'admin' || currentUserRole === 'platform_admin';

  if (isAdmin) {
    document.querySelectorAll('.navbar a[href="/exam"]').forEach(function(el) {
      el.style.display = 'none';
    });
    document.querySelectorAll('.navbar a[href="/subscription"]').forEach(function(el) {
      el.style.display = 'none';
    });
    const emptyExamBtn = document.getElementById('emptyStateTakeExamBtn');
    if (emptyExamBtn) emptyExamBtn.style.display = 'none';
  }

  // PERSONAL STUDENT SUBSCRIPTION ONBOARDING (direct_subscriber ONLY)
  // Auto-open subscription modal if:
  // 1. role = student
  // 2. student_subtype = direct_subscriber (NOT institution_linked)
  // 3. No active subscription exists
  //
  // Institution students (institution_linked) are NEVER shown this modal.
  console.log('[SUB] dashboard loaded');
  console.log('[SUB] me:', userInfo);
  console.log('[SUB] subtype:', currentUserSubtype);
  console.log('[SUB] checking subscription');
  
  if (currentUserRole === 'student' && currentUserSubtype === 'direct_subscriber') {
    console.log('[dashboard] ✅ Personal student (direct_subscriber) detected');
    console.log('[dashboard] → Initiating subscription check...');
    _checkAndPromptSubscription();
  } else if (currentUserRole === 'student' && currentUserSubtype === 'institution_linked') {
    console.log('[dashboard] ℹ️ Institution student detected - subscription modal will NOT be shown');
  } else if (currentUserRole === 'student' && !currentUserSubtype) {
    console.log('[dashboard] ⚠️ Student role but no subtype - defaulting to NO modal');
  }

  // Wire up the deferred subscription selection flow for "Take Exam" CTAs
  if (!isAdmin) {
    setupTakeExamInterceptors();
  }

  document.getElementById('lastUpdated').textContent = `Last updated: ${new Date().toLocaleTimeString()}`;

  // Hide the student filter (admin-only)
  const studentFilter = document.getElementById('filterStudent');
  if (studentFilter) {
    studentFilter.closest('.filter-group').style.display = 'none';
  }

  // ── Populate Student Profile Card ──────────────────────────────────────
  if (userInfo) {
    const displayName = userInfo.display_name || userInfo.sub || '—';
    const kcetId = userInfo.kcet_student_id || '—';
    
    const studentNameEl = document.getElementById('studentName');
    const studentIdEl = document.getElementById('studentKcetId');
    
    if (studentNameEl) studentNameEl.textContent = displayName;
    if (studentIdEl) studentIdEl.textContent = kcetId;
    
    console.log('[dashboard] Student profile populated:', { displayName, kcetId });
  }

  try {
    // Fetch submissions from API
    const subRes = await fetch('/api/student/submissions', { credentials: 'include' });
    if (!subRes.ok) {
      if (subRes.status === 401) {
        window.location.href = '/login';
        return;
      }
      throw new Error(`Failed to fetch submissions: HTTP ${subRes.status}`);
    }
    const subData = await subRes.json();
    allSubmissions = subData.submissions || [];

    // Fetch leaderboard data
    try {
      const lbRes = await fetch('/api/student/leaderboard/me', { credentials: 'include' });
      if (lbRes.ok) {
        leaderboardData = await lbRes.json();
      }
    } catch (e) {
      console.warn('Leaderboard data unavailable:', e.message);
      leaderboardData = null;
    }

    // Fetch college recommendations
    try {
      const recRes = await fetch('/api/student/college-recommendations', { credentials: 'include' });
      if (recRes.ok) {
        recommendationsData = await recRes.json();
      }
    } catch (e) {
      console.warn('Recommendations data unavailable:', e.message);
      recommendationsData = null;
    }
  } catch (e) {
    console.error('Dashboard init error:', e);
    renderEmptyDashboard();
    return;
  }

  if (allSubmissions.length === 0) {
    // REQ-1.2 — for students without exam data (including those without an
    // active subscription) we still render the full dashboard UI: KPI tiles,
    // chart placeholders, and the exam history table. The empty-state hint
    // sits above them so the user understands why everything reads zero.
    renderEmptyDashboard();
    return;
  }

  document.getElementById('emptyState').style.display = 'none';
  document.getElementById('dashContent').style.display = 'block';

  populateSubjectFilter();
  applyFilters();

  // Migrate any pre-existing localStorage submission data (REQ-14.1, REQ-14.4)
  migrateLegacySubmissions();

  document.getElementById('getRankSuggestionsBtn').addEventListener('click', async () => {
    const desiredRank = document.getElementById('desiredRankInput').value;
    if (!desiredRank) {
      showToast('Please enter a desired rank.', 'error');
      return;
    }
    const suggestions = await getRankSuggestions(desiredRank);
    renderRankSuggestions(suggestions);
  });

  // Load and render rank booster suggestions
  try {
    const boosterRes = await fetch('/api/student/rank-booster-suggestions?target_rank=5000', { credentials: 'include' });
    if (boosterRes.ok) {
      const boosterData = await boosterRes.json();
      renderRankBooster(boosterData);
    }
  } catch (e) {
    console.warn('Rank booster data unavailable:', e.message);
  }
}

/**
 * Render the dashboard skeleton with empty / zero values when the user has
 * no submission data yet (REQ-1.2). The empty-state hint remains visible
 * alongside so the page reads as "no data yet" rather than "broken".
 */
function renderEmptyDashboard() {
  const emptyEl = document.getElementById('emptyState');
  const dashEl = document.getElementById('dashContent');
  if (emptyEl) emptyEl.style.display = 'block';
  // Keep the dashboard skeleton visible (KPIs, charts, table placeholders)
  // so REQ-1.2 is satisfied even when the user has no exam data yet.
  if (dashEl) dashEl.style.display = 'block';

  // Hide the college recommendations card on empty/no-data dashboard
  const recSection = document.getElementById('collegeRecSection');
  if (recSection) recSection.style.display = 'none';

  // Reset KPI tiles to a clear "no data" state.
  const setText = (id, value) => {
    const el = document.getElementById(id);
    if (el) el.textContent = value;
  };
  setText('kpiStudents', '0');
  setText('kpiSubmissions', '0');
  setText('kpiAvgScore', '0%');
  setText('kpiPassRate', '0%');
  setText('kpiAvgTime', '0m');
  setText('kpiRankValue', '—');
  setText('kpiRankHint', 'Complete an exam to enter the leaderboard');

  // Render empty placeholders into the AI zones and tables.
  const emptyZone = '<li class="zone-item"><span class="zone-item-name" style="color:var(--muted)">No data yet</span></li>';
  ['strongItems', 'improveItems', 'weakItems'].forEach((id) => {
    const el = document.getElementById(id);
    if (el) el.innerHTML = emptyZone;
  });
  setText('strongCount', 0);
  setText('improveCount', 0);
  setText('weakCount', 0);
  setText('aiAnalysisFor', 'No submissions to analyse yet');
  const recBox = document.getElementById('aiRecommendationText');
  if (recBox) {
    recBox.textContent = 'Take your first exam to receive personalised AI recommendations.';
  }

  const rankingBody = document.getElementById('rankingBody');
  if (rankingBody) {
    rankingBody.innerHTML =
      '<tr><td colspan="5" style="text-align:center;color:var(--muted);padding:24px">No ranking data available yet</td></tr>';
  }
  const resultsBody = document.getElementById('resultsBody');
  if (resultsBody) {
    resultsBody.innerHTML =
      '<tr><td colspan="7" style="text-align:center;color:var(--muted);padding:24px">No exam history yet — your submissions will appear here.</td></tr>';
  }
  setText('tableFooter', 'Showing 0 of 0 submissions');

  // Tear down any leftover charts and leave the canvases blank.
  destroyCharts();
}

// ═══════════════════════════════════════════════════════════════════════════
// DEFERRED SUBSCRIPTION SELECTION FLOW (Task 4.2 — REQ-1.1, 1.2, 1.3, 1.8)
// ═══════════════════════════════════════════════════════════════════════════
// The dashboard is reachable without an active subscription. When the user
// clicks any "Take Exam" CTA on the dashboard we first check their
// subscription status and either:
//   • open SubscriptionModal — for users with no usable subscription
//     (no record / expired / cancelled), per REQ-1.3, OR
//   • allow navigation to /exam — for users with active access (trial /
//     active / overdue grace period / institution-linked), per REQ-1.8.
// The exam page itself performs the authoritative check via
// /api/exam/check-access (Task 4.1), so this client-side gate is purely a UX
// optimisation that surfaces the plan-selection modal before the student
// lands on the exam entry form.
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Wire click handlers on every "Take Exam" surface — the empty-state CTA on
 * the dashboard plus the navbar Exam link — so we can intercept navigation
 * and route the student through the subscription modal when appropriate.
 *
 * Idempotent: safe to call multiple times. Uses a `data-take-exam-bound`
 * marker so refreshes don't double-bind handlers.
 */
function setupTakeExamInterceptors() {
  if (typeof document === 'undefined') return;

  const targets = [];

  // Empty-state CTA (rendered in dashboard.html with data-take-exam).
  document.querySelectorAll('[data-take-exam]').forEach((el) => targets.push(el));

  // Navbar Exam link — `/exam` href on the dashboard navbar.
  document.querySelectorAll('.navbar a[href="/exam"]').forEach((el) => targets.push(el));

  targets.forEach((el) => {
    if (!el || el.dataset.takeExamBound === 'true') return;
    el.dataset.takeExamBound = 'true';
    el.addEventListener('click', handleTakeExamClick);
  });
}

/**
 * Intercept a "Take Exam" click. If the user has no usable subscription we
 * surface SubscriptionModal in-place (REQ-1.3); otherwise we let the click
 * proceed to /exam normally (REQ-1.8).
 *
 * If anything goes wrong — modal not loaded, network failure, etc. — we
 * fall back to letting the navigation happen so the user is never stranded
 * on the dashboard. The exam page will still enforce access via
 * /api/exam/check-access.
 */
async function handleTakeExamClick(evt) {
  // Allow modifier-clicks (open in new tab, etc.) to bypass the gate.
  if (evt.metaKey || evt.ctrlKey || evt.shiftKey || evt.altKey || evt.button === 1) {
    return;
  }

  // If the modal module isn't on the page we can't gate the click — let it
  // proceed so the exam page handles the case.
  if (typeof SubscriptionModal === 'undefined' || typeof Subscription === 'undefined') {
    return;
  }

  let subscription = null;
  try {
    subscription = await Subscription.getStatus();
  } catch (e) {
    // Network/auth error — let the click through; exam page will handle it.
    console.warn('Take Exam gate: subscription lookup failed, allowing navigation.', e);
    return;
  }

  if (!SubscriptionModal.shouldShow(subscription)) {
    // Active / trial / institution / overdue grace — proceed to /exam (REQ-1.8).
    return;
  }

  // No usable subscription — open the modal and stop the navigation (REQ-1.3).
  evt.preventDefault();
  evt.stopPropagation();
  try {
    SubscriptionModal.show();
  } catch (e) {
    // If show() throws for any reason, fall back to navigating so the user
    // can still reach the exam page (which has its own gating).
    console.error('Take Exam gate: failed to show subscription modal, navigating instead.', e);
    const href = evt.currentTarget && evt.currentTarget.getAttribute
      ? evt.currentTarget.getAttribute('href')
      : null;
    if (href) {
      window.location.href = href;
    }
  }
}

// ── Subject Filter ───────────────────────────────────────────────────────────
function populateSubjectFilter() {
  const sel = document.getElementById('filterSubject');
  if (!sel) return;
  sel.innerHTML = '<option value="all">All Subjects</option>';
  const subjects = new Set();
  allSubmissions.forEach(s => {
    if (s.subject) subjects.add(s.subject);
  });
  subjects.forEach(subj => {
    const o = document.createElement('option');
    o.value = subj;
    o.textContent = subj;
    sel.appendChild(o);
  });
}

// ── Pro Access Check & Tier Gating ──────────────────────────────────────────
async function checkProAccess() {
  try {
    if (typeof Subscription !== 'undefined' && Subscription.getStatus) {
      const sub = await Subscription.getStatus();
      if (!sub) return false;
      
      const planType = (sub.plan_type || '').toLowerCase();
      const planName = (sub.plan_name || '').toLowerCase();
      const status = (sub.status || '').toLowerCase();

      const isActive = sub.is_active || ['active', 'trial', 'grace_period'].includes(status);
      if (!isActive) return false;

      if (planType === 'pro' || planType === 'trial' || planType === 'institution' || sub.quota_type === 'unlimited') {
        return true;
      }
      if (planName.includes('pro') || planName.includes('trial') || planName.includes('99')) {
        return true;
      }
    }
  } catch (e) {
    console.warn('checkProAccess error:', e);
  }
  return false;
}

function applyTierAccessControl(isPro) {
  const aiBlock = document.getElementById('aiBlock');
  const collegeRec = document.getElementById('collegeRecSection');
  const rankSuggestion = document.getElementById('rankSuggestionSection');
  const rankBooster = document.getElementById('rankBoosterSection');
  const topStudentsCard = document.getElementById('rankingBody')?.closest('.results-card');
  const chartsRows = document.querySelectorAll('.charts-row');

  if (isPro) {
    if (aiBlock) aiBlock.style.display = 'block';
    if (collegeRec) collegeRec.style.display = 'block';
    if (rankSuggestion) rankSuggestion.style.display = 'block';
    if (rankBooster) rankBooster.style.display = 'block';
    if (topStudentsCard) topStudentsCard.style.display = 'block';
    chartsRows.forEach(row => row.style.display = 'grid');

    const promoBanner = document.getElementById('freeUserProPromo');
    if (promoBanner) promoBanner.style.display = 'none';

    const rankVal = document.getElementById('kpiRankValue');
    if (rankVal && leaderboardData && typeof leaderboardData.my_rank === 'number') {
      rankVal.textContent = `#${leaderboardData.my_rank}`;
    }
  } else {
    // Free user — hide AI Analysis, College Match Predictor, Rank Suggestions, Rank Booster, and Top Students
    if (aiBlock) aiBlock.style.display = 'none';
    if (collegeRec) collegeRec.style.display = 'none';
    if (rankSuggestion) rankSuggestion.style.display = 'none';
    if (rankBooster) rankBooster.style.display = 'none';
    if (topStudentsCard) topStudentsCard.style.display = 'none';
    chartsRows.forEach(row => row.style.display = 'none');

    // Update Rank KPI tile
    const rankVal = document.getElementById('kpiRankValue');
    const rankHint = document.getElementById('kpiRankHint');
    if (rankVal) rankVal.textContent = '🔒 Pro';
    if (rankHint) rankHint.textContent = 'Upgrade to Pro (₹99/wk) to enter rankings';

    // Render Pro Upgrade Banner
    let promoBanner = document.getElementById('freeUserProPromo');
    if (!promoBanner) {
      promoBanner = document.createElement('div');
      promoBanner.id = 'freeUserProPromo';
      promoBanner.className = 'section-card';
      promoBanner.style.cssText = 'margin-top:20px;padding:24px;background:linear-gradient(135deg, rgba(124,58,237,0.12), rgba(99,102,241,0.12));border:1px dashed var(--purple);border-radius:var(--r);text-align:center;';
      promoBanner.innerHTML = `
        <div style="font-size:2rem;margin-bottom:8px;">🔒</div>
        <h3 style="font-size:1.15rem;font-weight:800;color:var(--text);margin-bottom:6px;">Unlock Pro Features &amp; AI Analytics</h3>
        <p style="font-size:0.88rem;color:var(--muted);max-width:560px;margin:0 auto 16px auto;line-height:1.5;">
          You are currently viewing the Free dashboard (Score, Correct/Wrong count &amp; Total Time). Upgrade to the <strong>Pro Plan (₹99/week)</strong> to unlock AI Performance Analysis, College Match Predictor, Rank Booster Action Plan, and Leaderboard Rankings!
        </p>
        <button class="btn-primary" onclick="if(typeof SubscriptionModal!=='undefined'){SubscriptionModal.show();}else{window.location.href='/subscription';}" style="padding:10px 24px;font-size:0.9rem;border-radius:10px;font-weight:700;cursor:pointer;">
          ⭐ Upgrade to Pro (₹99/week) →
        </button>
      `;
      const dashContent = document.getElementById('dashContent');
      if (dashContent) {
        const kpiRow = document.getElementById('kpiRow');
        if (kpiRow && kpiRow.nextSibling) {
          dashContent.insertBefore(promoBanner, kpiRow.nextSibling);
        } else {
          dashContent.appendChild(promoBanner);
        }
      }
    } else {
      promoBanner.style.display = 'block';
    }
  }
}

window.applyFilters = async () => {
  const subject = document.getElementById('filterSubject')?.value || 'all';
  const set = document.getElementById('filterSet')?.value || 'all';
  const status = document.getElementById('filterStatus')?.value || 'all';

  filteredSubs = allSubmissions.filter(s => {
    if (subject !== 'all' && s.subject !== subject) return false;
    if (set !== 'all' && s.set_label !== set) return false;
    if (status === 'pass' && !s.pass_flag) return false;
    if (status === 'fail' && s.pass_flag) return false;
    return true;
  });

  updateKPIs();
  renderCharts();
  renderAIAnalysis();
  renderRecommendations();
  renderRankings();
  renderTable();

  // Tier access control check
  const isPro = await checkProAccess();
  applyTierAccessControl(isPro);
};

window.refreshDashboard = () => { destroyCharts(); initDashboard(); };

// ── KPIs ─────────────────────────────────────────────────────────────────────
function updateKPIs() {
  const subs = filteredSubs;
  if (!subs.length) return;

  const examsTaken = subs.length;
  const avgScore = Math.round(subs.reduce((a, s) => a + s.score_pct, 0) / subs.length);
  const passRate = Math.round(subs.filter(s => s.pass_flag).length / subs.length * 100);
  const avgTime = Math.round(subs.reduce((a, s) => a + s.time_taken_sec, 0) / subs.length / 60);

  document.getElementById('kpiStudents').textContent = examsTaken;
  document.getElementById('kpiSubmissions').textContent = subs.length;
  document.getElementById('kpiAvgScore').textContent = avgScore + '%';
  document.getElementById('kpiPassRate').textContent = passRate + '%';
  document.getElementById('kpiAvgTime').textContent = avgTime + 'm';

  // Update "Your Rank" KPI
  const rankVal = document.getElementById('kpiRankValue');
  const rankHint = document.getElementById('kpiRankHint');
  if (rankVal) {
    if (leaderboardData && leaderboardData.my_rank !== '\u2014' && typeof leaderboardData.my_rank === 'number') {
      rankVal.textContent = `#${leaderboardData.my_rank}`;
      if (rankHint) rankHint.textContent = `of ${leaderboardData.total_ranked} ranked`;
    } else {
      rankVal.textContent = '\u2014';
      if (rankHint) rankHint.textContent = 'score at least 30% on average to enter the leaderboard';
    }
  }
}

// ── Charts ────────────────────────────────────────────────────────────────────
function destroyCharts() { Object.values(charts).forEach(c => { try { c.destroy(); } catch {} }); charts = {}; }

function renderCharts() {
  destroyCharts();
  const subs = filteredSubs;
  
  // Hide or show chart wrappers based on data availability
  ['topicChart', 'setChart', 'passChart'].forEach(id => {
    const el = document.getElementById(id);
    if (el) {
      const wrap = el.closest('.chart-wrap');
      if (wrap) wrap.style.display = subs.length ? 'block' : 'none';
    }
  });

  if (!subs.length) return;

  // Topic Radar — built from topic_breakdown if available, else from subject scores
  const topicMap = {};
  subs.forEach(s => {
    // Use subject as a topic grouping for the radar chart
    const subj = s.subject || 'General';
    if (!topicMap[subj]) topicMap[subj] = { e: 0, tot: 0, count: 0 };
    topicMap[subj].e += s.score_pct;
    topicMap[subj].tot += 100;
    topicMap[subj].count += 1;
  });
  const tLabels = Object.keys(topicMap);
  const tData = tLabels.map(t => topicMap[t].count > 0 ? Math.round(topicMap[t].e / topicMap[t].count) : 0);
  charts.topic = new Chart(document.getElementById('topicChart'), {
    type: 'radar',
    data: {
      labels: tLabels,
      datasets: [{ label: 'Avg %', data: tData, backgroundColor: 'rgba(124,58,237,0.15)', borderColor: '#a855f7', pointBackgroundColor: '#a855f7', borderWidth: 2, pointRadius: 4 }]
    },
    options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { labels: { color: CHART_DEFAULTS.color } } }, scales: { r: { grid: { color: CHART_DEFAULTS.grid }, ticks: { color: CHART_DEFAULTS.muted, backdropColor: 'transparent', font: { size: 9 } }, pointLabels: { color: CHART_DEFAULTS.color, font: { size: 10 } }, min: 0, max: 100 } } }
  });

  // Set-wise bar chart
  const setLabels = ['Set A', 'Set B', 'Set C', 'Set D'];
  const setValues = ['Set A', 'Set B', 'Set C', 'Set D'].map(label => {
    const f = subs.filter(s => s.set_label === label);
    return f.length ? Math.round(f.reduce((a, s) => a + s.score_pct, 0) / f.length) : 0;
  });
  charts.set = new Chart(document.getElementById('setChart'), {
    type: 'bar',
    data: { labels: setLabels, datasets: [{ label: 'Avg Score %', data: setValues, backgroundColor: ['rgba(124,58,237,0.7)', 'rgba(37,99,235,0.7)', 'rgba(8,145,178,0.7)', 'rgba(5,150,105,0.7)'], borderRadius: 6, borderSkipped: false }] },
    options: { ...baseChartOpts(), plugins: { legend: { display: false } } }
  });

  // Pass vs Fail doughnut
  const pass = subs.filter(s => s.pass_flag).length;
  charts.pass = new Chart(document.getElementById('passChart'), {
    type: 'doughnut',
    data: { labels: ['Pass', 'Fail'], datasets: [{ data: [pass, subs.length - pass], backgroundColor: ['rgba(5,150,105,0.8)', 'rgba(220,38,38,0.8)'], borderWidth: 0, hoverOffset: 6 }] },
    options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'bottom', labels: { color: CHART_DEFAULTS.color, padding: 12 } } } }
  });
}

function baseChartOpts() {
  return {
    responsive: true, maintainAspectRatio: false,
    plugins: { legend: { labels: { color: CHART_DEFAULTS.color } } },
    scales: {
      x: { grid: { color: CHART_DEFAULTS.grid }, ticks: { color: CHART_DEFAULTS.muted } },
      y: { grid: { color: CHART_DEFAULTS.grid }, ticks: { color: CHART_DEFAULTS.muted }, beginAtZero: true }
    }
  };
}

// ── AI Analysis ───────────────────────────────────────────────────────────────
function renderAIAnalysis() {
  const subs = filteredSubs;
  if (!subs.length) return;

  document.getElementById('aiAnalysisFor').textContent = `Analyzing ${subs.length} submission(s)`;

  // Build topic map from subjects for AI analysis
  const topicMap = {};
  subs.forEach(s => {
    const subj = s.subject || 'General';
    if (!topicMap[subj]) topicMap[subj] = { e: 0, tot: 0, count: 0 };
    topicMap[subj].e += s.score_pct;
    topicMap[subj].tot += 100;
    topicMap[subj].count += 1;
  });

  const strong = [], canImprove = [], weak = [];
  Object.entries(topicMap).forEach(([t, sc]) => {
    const p = sc.count > 0 ? Math.round(sc.e / sc.count) : 0;
    if (p >= 70) strong.push({ topic: t, pct: p });
    else if (p >= 40) canImprove.push({ topic: t, pct: p });
    else weak.push({ topic: t, pct: p });
  });

  const renderZone = (id, items) => {
    document.getElementById(id).innerHTML = items.length
      ? items.map(i => `<li class="zone-item"><span class="zone-item-name">${i.topic}</span><span class="zone-item-pct">${i.pct}%</span></li>`).join('')
      : '<li class="zone-item"><span class="zone-item-name" style="color:var(--muted)">No data</span></li>';
  };

  renderZone('strongItems', strong);
  renderZone('improveItems', canImprove);
  renderZone('weakItems', weak);
  document.getElementById('strongCount').textContent = strong.length;
  document.getElementById('improveCount').textContent = canImprove.length;
  document.getElementById('weakCount').textContent = weak.length;

  const avgScore = Math.round(subs.reduce((a, s) => a + s.score_pct, 0) / subs.length);
  const passRate = Math.round(subs.filter(s => s.pass_flag).length / subs.length * 100);
  let rec = '';
  if (avgScore >= 75) rec = `🎉 Outstanding performance! Average score is ${avgScore}% with a ${passRate}% pass rate. `;
  else if (avgScore >= 60) rec = `👍 Good performance overall. Average score is ${avgScore}%. `;
  else if (avgScore >= 40) rec = `📚 Moderate performance. Average score is ${avgScore}%. More practice needed. `;
  else rec = `⚠️ Performance needs significant improvement. Average score is ${avgScore}%. `;
  if (weak.length) rec += `Priority focus areas: ${weak.map(w => w.topic).join(', ')}. `;
  if (canImprove.length) rec += `Topics with growth potential: ${canImprove.map(c => c.topic).join(', ')}. `;
  if (strong.length) rec += `Strong topics to maintain: ${strong.map(s => s.topic).join(', ')}.`;

  document.getElementById('aiRecommendationText').textContent = rec;
}

// ── Results Table ─────────────────────────────────────────────────────────────
function renderTable() {
  const search = document.getElementById('searchInput')?.value.toLowerCase() || '';
  let subs = filteredSubs.filter(s =>
    (s.subject || '').toLowerCase().includes(search) ||
    (s.set_label || '').toLowerCase().includes(search)
  );

  subs.sort((a, b) => {
    let va, vb;
    if (sortKey === 'score') { va = a.score_pct; vb = b.score_pct; }
    else if (sortKey === 'time') { va = a.time_taken_sec; vb = b.time_taken_sec; }
    else if (sortKey === 'subject') { va = a.subject || ''; vb = b.subject || ''; }
    else if (sortKey === 'set') { va = a.set_label || ''; vb = b.set_label || ''; }
    else if (sortKey === 'status') { va = a.pass_flag ? 1 : 0; vb = b.pass_flag ? 1 : 0; }
    else if (sortKey === 'submitted_at') { va = a.submitted_at || ''; vb = b.submitted_at || ''; }
    else { va = a.score_pct; vb = b.score_pct; }
    if (va < vb) return sortDir; if (va > vb) return -sortDir; return 0;
  });

  const tbody = document.getElementById('resultsBody');
  tbody.innerHTML = subs.map(s => {
    const p = Math.round(s.score_pct);
    const cls = p >= 70 ? 'score-high' : p >= 40 ? 'score-mid' : 'score-low';
    const m = Math.floor(s.time_taken_sec / 60), sec = s.time_taken_sec % 60;
    const date = s.submitted_at ? new Date(s.submitted_at).toLocaleDateString() : '—';
    return `<tr>
      <td><span style="font-weight:700;color:var(--purple-l)">${s.subject || '—'}</span></td>
      <td><span style="font-weight:600">${s.set_label || '—'}</span></td>
      <td><span class="score-badge ${cls}">${p}%</span></td>
      <td style="color:var(--muted)">${m}m ${sec}s</td>
      <td class="${s.pass_flag ? 'status-pass' : 'status-fail'}">${s.pass_flag ? '✅ Pass' : '❌ Fail'}</td>
      <td style="color:var(--muted2)">${date}</td>
      <td><button class="btn-view" onclick="openDrawer('${s.id}')">View →</button></td>
    </tr>`;
  }).join('');

  document.getElementById('tableFooter').textContent = `Showing ${subs.length} of ${allSubmissions.length} submissions`;
}

window.filterTable = () => renderTable();
window.sortTable = key => { if (sortKey === key) sortDir *= -1; else { sortKey = key; sortDir = -1; } renderTable(); };

// ── Rankings (Top 3 only for student dashboard) ──────────────────────────────
function renderRankings() {
  const medals = ['🥇', '🥈', '🥉'];
  const chartWrapper = document.getElementById('rankingChart')?.closest('.chart-wrap');

  // Use leaderboard API data for top 3
  if (!leaderboardData || !leaderboardData.top_3 || leaderboardData.top_3.length === 0) {
    document.getElementById('rankingBody').innerHTML = '<tr><td colspan="5" style="text-align:center;color:var(--muted);padding:24px">No ranking data available yet</td></tr>';
    // Hide ranking chart when no data
    if (chartWrapper) chartWrapper.style.display = 'none';
    if (charts.ranking) { try { charts.ranking.destroy(); } catch {} }
    return;
  }

  if (chartWrapper) chartWrapper.style.display = 'block';

  const top3 = leaderboardData.top_3;

  // Bar chart for top 3
  if (charts.ranking) { try { charts.ranking.destroy(); } catch {} }
  charts.ranking = new Chart(document.getElementById('rankingChart'), {
    type: 'bar',
    data: {
      labels: top3.map(s => s.display_name),
      datasets: [{
        label: 'Composite Score',
        data: top3.map(s => Math.round(s.composite_score)),
        backgroundColor: top3.map((s, i) => {
          if (i === 0) return 'rgba(255,215,0,0.8)';
          if (i === 1) return 'rgba(192,192,192,0.8)';
          return 'rgba(205,127,50,0.8)';
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

  // Render top 3 table rows with medal indicators
  document.getElementById('rankingBody').innerHTML = top3.map((s, i) => {
    const score = Math.round(s.composite_score);
    const cls = score >= 70 ? 'score-high' : score >= 40 ? 'score-mid' : 'score-low';
    const medal = medals[i] || `#${s.rank}`;
    return `<tr>
      <td style="font-size:1.1rem;text-align:center">${medal}</td>
      <td><div style="font-weight:700">${s.display_name}</div></td>
      <td style="color:var(--muted)">${s.kcet_student_id}</td>
      <td><span class="score-badge ${cls}">${score}</span></td>
      <td style="min-width:140px">
        <div style="background:var(--s3);border-radius:4px;height:8px;overflow:hidden">
          <div style="width:${score}%;height:100%;border-radius:4px;background:${score >= 70 ? 'var(--green-l)' : score >= 40 ? 'var(--yellow-l)' : 'var(--red-l)'};transition:width 0.6s ease"></div>
        </div>
      </td>
    </tr>`;
  }).join('');
}

// ── Detail Drawer ─────────────────────────────────────────────────────────────
window.openDrawer = async (submissionId) => {
  try {
    const res = await fetch(`/api/student/submissions/${submissionId}`, { credentials: 'include' });
    if (!res.ok) {
      showToast('Failed to load submission details');
      return;
    }
    const s = await res.json();

    document.getElementById('drawerName').textContent = s.subject || 'Exam';
    document.getElementById('drawerMeta').textContent = `${s.set_label || ''} · ${new Date(s.submitted_at).toLocaleString()}`;

    const m = Math.floor(s.time_taken_sec / 60), sec = s.time_taken_sec % 60;
    const icons = { correct: '✅', wrong: '❌', partial: '🟡', unanswered: '⬜' };

    const isPro = await checkProAccess();
    const isPremium = isPro || s.is_premium_subscriber === true;

    const qList = s.questions || [];
    const correctCount = qList.filter(q => q.status === 'correct').length;
    const wrongCount = qList.filter(q => q.status === 'wrong').length;

    let reviewContentHtml = '';
    if (isPremium) {
      reviewContentHtml = `
        <div class="answer-review-list">
          ${qList.map((r, i) => {
            const timeTag = r.time_taken_sec != null ? ` <span style="font-size:11px;font-weight:700;color:var(--purple-l,#a78bfa);background:rgba(124,58,237,0.12);padding:2px 8px;border-radius:10px;margin-left:6px;">⏱ ${r.time_taken_sec}s taken</span>` : '';
            const givenText = r.given !== undefined && r.given !== null && r.given !== '' ? (r.opts ? r.opts[parseInt(r.given)] : r.given) : 'Not answered';
            const correctText = r.correctAns !== undefined && r.correctAns !== null ? (r.opts ? r.opts[parseInt(r.correctAns)] : r.correctAns) : null;
            return `
              <div class="answer-row ${r.status}">
                <span class="ans-status-icon">${icons[r.status] || '⬜'}</span>
                <div class="ans-content">
                  <div class="ans-q-text">Q${r.order_index != null ? r.order_index + 1 : i + 1}. ${r.q} ${timeTag}</div>
                  <div class="ans-given">Your answer: <strong>${givenText}</strong></div>
                  ${r.status !== 'correct' && correctText ? `<div class="ans-correct-text">✓ Correct: ${correctText}</div>` : ''}
                  ${r.exp ? `<div class="ans-exp" style="margin-top:6px;font-size:13px;color:var(--text-color, #333);"><strong>Explanation:</strong> ${r.exp}</div>` : ''}
                  <div class="ans-meta">${r.topic || ''}</div>
                </div>
              </div>`;
          }).join('')}
        </div>`;
    } else {
      reviewContentHtml = `
        <div style="background:linear-gradient(135deg, rgba(124,58,237,0.15), rgba(99,102,241,0.15));border:1px solid rgba(124,58,237,0.35);border-radius:14px;padding:22px;text-align:center;margin-bottom:20px;">
          <div style="font-size:1.8rem;margin-bottom:6px;">🔒 Pro Plan Feature</div>
          <h4 style="margin:0 0 6px;font-size:1.1rem;font-weight:800;color:var(--text);">Detailed Question Breakdown &amp; Time Spent Per Question</h4>
          <p style="font-size:0.85rem;color:var(--muted);margin:0 0 16px;">Exact per-question time analysis, question-by-question explanations, and step-by-step corrections are reserved for Pro subscribers (₹99/week).</p>
          <button class="btn-primary" onclick="if(window.SubscriptionModal){SubscriptionModal.show();}else{window.location.href='/subscription';}" style="padding:10px 22px;font-size:0.92rem;border-radius:10px;font-weight:800;cursor:pointer;">⭐ Upgrade to Pro (₹99/week)</button>
        </div>`;
    }

    document.getElementById('drawerBody').innerHTML = `
      <div class="drawer-kpi-row">
        <div class="drawer-kpi"><div class="drawer-kpi-val">${Math.round(s.score_pct)}%</div><div class="drawer-kpi-label">Score</div></div>
        <div class="drawer-kpi"><div class="drawer-kpi-val" style="color:var(--green-l)">${correctCount}</div><div class="drawer-kpi-label">Correct</div></div>
        <div class="drawer-kpi"><div class="drawer-kpi-val" style="color:var(--red-l)">${wrongCount}</div><div class="drawer-kpi-label">Wrong</div></div>
        <div class="drawer-kpi"><div class="drawer-kpi-val">${m}m ${sec}s</div><div class="drawer-kpi-label">Entire Test Time</div></div>
      </div>
      <div class="drawer-section-title">Test Summary (${qList.length} questions)</div>
      ${reviewContentHtml}`;

    document.getElementById('drawerOverlay').style.display = 'block';
    document.getElementById('detailDrawer').classList.add('open');
  } catch (e) {
    console.error('Error opening drawer:', e);
    showToast('Error loading submission details');
  }
};

window.closeDrawer = () => {
  document.getElementById('drawerOverlay').style.display = 'none';
  document.getElementById('detailDrawer').classList.remove('open');
};

// ── Export ────────────────────────────────────────────────────────────────────
window.exportReport = () => {
  const subs = filteredSubs;
  if (!subs.length) { showToast('No data to export'); return; }
  let csv = 'Subject,Set,Score%,Time(s),Status,Date\n';
  subs.forEach(s => {
    const date = s.submitted_at ? new Date(s.submitted_at).toLocaleDateString() : '';
    csv += `"${s.subject || ''}","${s.set_label || ''}",${Math.round(s.score_pct)},${s.time_taken_sec},${s.pass_flag ? 'Pass' : 'Fail'},"${date}"\n`;
  });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(new Blob([csv], { type: 'text/csv' }));
  a.download = `Mr.E_Report_${new Date().toISOString().slice(0, 10)}.csv`;
  a.click();
  showToast('📊 Report exported as CSV', 'success');
};

// Remove clearAllData — no longer relevant for server-backed dashboard

// ── Boot ──────────────────────────────────────────────────────────────────────
// Utility: showToast (self-contained, no dependency on app.js)
function showToast(msg, type = '') {
  document.querySelectorAll('.toast').forEach(t => t.remove());
  const t = document.createElement('div');
  t.className = `toast ${type}`;
  t.textContent = msg;
  document.body.appendChild(t);
  setTimeout(() => t?.remove(), 3500);
}

// ── Legacy localStorage Migration (REQ-14.1, REQ-14.4) ──────────────────────
/**
 * Detect legacy `ef_submissions` entries in localStorage and attempt to
 * upload them to /api/student/submit. On success, clear the legacy key.
 * On failure (not authenticated, server error), leave data for next attempt.
 */
async function migrateLegacySubmissions() {
  var raw = localStorage.getItem('ef_submissions');
  if (!raw) return;

  var submissions;
  try {
    submissions = JSON.parse(raw);
  } catch (e) {
    // Corrupted data — remove it
    localStorage.removeItem('ef_submissions');
    return;
  }

  if (!Array.isArray(submissions) || submissions.length === 0) {
    localStorage.removeItem('ef_submissions');
    return;
  }

  var allSucceeded = true;

  for (var i = 0; i < submissions.length; i++) {
    var sub = submissions[i];
    // Generate a deterministic idempotency key from the legacy data to prevent duplicates
    var idempotencyKey = 'legacy-' + (sub.id || sub.timestamp || Date.now() + '-' + i);

    var body = {
      exam_set_id: sub.exam_set_id || null,
      answers: sub.answers || {},
      time_taken_sec: typeof sub.time_taken_sec === 'number' ? sub.time_taken_sec : 0,
      idempotency_key: idempotencyKey,
    };

    // Skip entries without a valid exam_set_id (can't submit without one)
    if (!body.exam_set_id) {
      continue;
    }

    try {
      var res = await fetch('/api/student/submit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(body),
      });

      if (!res.ok) {
        // Not authenticated or server error — leave data for next attempt
        allSucceeded = false;
        break;
      }
    } catch (e) {
      // Network error — leave data for next attempt
      allSucceeded = false;
      break;
    }
  }

  if (allSucceeded) {
    localStorage.removeItem('ef_submissions');
  }
}

// ── College Recommendations Rendering ─────────────────────────────────────────
function renderRecommendations() {
  const section = document.getElementById('collegeRecSection');
  if (!section) return;

  if (!recommendationsData || recommendationsData.no_data) {
    section.style.display = 'none';
    return;
  }

  section.style.display = 'block';

  // Update predicted rank and subtitle
  const rankBadge = document.getElementById('predictedRankBadge');
  if (rankBadge) {
    rankBadge.textContent = `Projected Rank: ${recommendationsData.projected_rank_range}`;
  }

  const subtitle = document.getElementById('recSubtitle');
  if (subtitle) {
    subtitle.textContent = `Based on your overall average score of ${recommendationsData.average_score}% (${recommendationsData.student_tier})`;
  }

  // Update count badges
  const counts = recommendationsData.counts || { target: 0, reach: 0, safe: 0 };
  const targetCountEl = document.getElementById('targetCount');
  if (targetCountEl) targetCountEl.textContent = counts.target;
  const reachCountEl = document.getElementById('reachCount');
  if (reachCountEl) reachCountEl.textContent = counts.reach;
  const safeCountEl = document.getElementById('safeCount');
  if (safeCountEl) safeCountEl.textContent = counts.safe;

  // Handle lock overlay
  const lockOverlay = document.getElementById('recLockOverlay');
  if (lockOverlay) {
    if (recommendationsData.is_locked) {
      lockOverlay.style.display = 'block';
      const lockText = document.getElementById('recLockText');
      if (lockText && recommendationsData.lock_message) {
        lockText.textContent = recommendationsData.lock_message;
      }
    } else {
      lockOverlay.style.display = 'none';
    }
  }

  // Populate list
  populateCollegesList();
}

window.switchRecTab = (tab) => {
  currentRecTab = tab;
  
  // Update active pill styling
  ['target', 'reach', 'safe'].forEach(t => {
    const btn = document.getElementById(`recTab${t.charAt(0).toUpperCase() + t.slice(1)}`);
    if (btn) {
      if (t === tab) {
        btn.classList.add('active');
        btn.setAttribute('aria-current', 'page');
      } else {
        btn.classList.remove('active');
        btn.removeAttribute('aria-current');
      }
    }
  });

  populateCollegesList();
};

function populateCollegesList() {
  const grid = document.getElementById('collegesGrid');
  if (!grid || !recommendationsData || !recommendationsData.matches) return;

  const colleges = recommendationsData.matches[currentRecTab] || [];
  const searchVal = (document.getElementById('collegeSearchInput')?.value || '').toLowerCase().trim();

  const filtered = colleges.filter(c => {
    if (!searchVal) return true;
    return c.name.toLowerCase().includes(searchVal) || 
           c.location.toLowerCase().includes(searchVal) || 
           c.description.toLowerCase().includes(searchVal);
  });

  if (filtered.length === 0) {
    grid.innerHTML = `<div style="grid-column: 1 / -1; text-align: center; color: var(--muted); padding: 24px; font-size: 0.85rem;">No matches found for "${searchVal}" in this category.</div>`;
    return;
  }

  const isLocked = recommendationsData.is_locked;

  grid.innerHTML = filtered.map(col => {
    const lockIcon = isLocked ? '<span style="font-size: 0.85rem; margin-left: 6px;" title="Pro Feature">🔒</span>' : '';
    return `
      <div class="kpi-tile" style="flex-direction: column; align-items: flex-start; gap: 8px; padding: 16px; border: 1px solid var(--border); background: var(--s2); border-radius: var(--rs); position: relative;">
        <div style="display: flex; justify-content: space-between; width: 100%; align-items: center; gap: 8px;">
          <span class="inst-exam-tag ${col.tier === 1 ? 'platform' : 'institution'}" style="font-weight: bold; padding: 2px 8px; font-size: 0.7rem;">Tier ${col.tier}</span>
          <span style="font-size: 0.72rem; color: var(--muted); font-weight: 600;">Cutoff: ~${col.cutoff_rank}</span>
        </div>
        <h3 style="font-size: 0.95rem; font-weight: 700; margin: 4px 0; color: var(--text); display: flex; align-items: center;">
          ${col.name} ${lockIcon}
        </h3>
        <div style="font-size: 0.78rem; color: var(--purple-l); font-weight: 600; display: flex; align-items: center; gap: 4px;">
          📍 ${col.location}
        </div>
        <p style="font-size: 0.78rem; color: var(--muted); margin: 4px 0; line-height: 1.4; text-align: left; font-weight: 500;">
          ${col.description}
        </p>
      </div>
    `;
  }).join('');
}

window.filterRecommendations = () => {
  populateCollegesList();
};

async function getRankSuggestions(desiredRank) {
  try {
    const res = await fetch(`/api/student/rank-suggestions?desired_rank=${desiredRank}`, { credentials: 'include' });
    if (!res.ok) {
      console.error('Failed to fetch rank suggestions');
      return null;
    }
    return await res.json();
  } catch (error) {
    console.error('Error fetching rank suggestions:', error);
    return null;
  }
}

function renderRankSuggestions(suggestions) {
  const resultDiv = document.getElementById('rankSuggestionsResult');
  if (!suggestions) {
    resultDiv.innerHTML = '<p>Could not fetch suggestions. Please try again later.</p>';
    return;
  }

  let html = `
    <div class="ai-recommendation-box">
        <div class="ai-rec-header">
            <span>🎯</span> Suggestions for Rank ${suggestions.desired_rank}
        </div>
        <ul>
  `;
  suggestions.suggestions.forEach(suggestion => {
    html += `<li>${suggestion}</li>`;
  });
  html += '</ul></div>';
  resultDiv.innerHTML = html;
}

function renderRankBooster(data) {
  const section = document.getElementById('rankBoosterSection');
  if (!section) return;
  if (!data || data.no_data) { section.style.display = 'none'; return; }

  section.style.display = 'block';

  const metaEl = document.getElementById('boosterMeta');
  const listEl = document.getElementById('boosterActionList');

  if (metaEl) {
    const gapText = data.score_gap > 0
      ? `Close a <strong>${data.score_gap}%</strong> gap (${data.current_average_score}% → ${data.required_average_score}% avg)`
      : `✅ Already on track for <strong>${data.target_label}</strong>!`;
    metaEl.innerHTML = `Target: <strong>${data.target_label}</strong> · ${gapText}`;
  }

  if (listEl && data.action_items && data.action_items.length) {
    listEl.innerHTML = data.action_items.map(item =>
      `<li>${item.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')}</li>`
    ).join('');
  }

  if (data.is_locked) {
    const lockMsg = document.getElementById('boosterLockMsg');
    if (lockMsg) { lockMsg.style.display = 'block'; lockMsg.textContent = data.lock_message || '🔒 Upgrade to Pro to unlock full personalized study plan.'; }
  }
}

initDashboard();
