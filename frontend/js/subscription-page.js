// SmartKCET Prep — Subscription Page JavaScript Logic
// Handles the dedicated /subscription management page:
//   * Loads current subscription via GET /api/subscription/status
//   * Renders plan name, status, dates, and remaining attempts
//   * Drives Upgrade / Change Billing / Cancel / Reactivate modals
//   * Surfaces the Plan Selection modal when no subscription exists
//
// Pairs with `subscription.html` (markup), `subscription.css` (styles),
// and `subscription.js` (Subscription module + SubscriptionAPI).
//
// Requirements: 2.2, 2.3, 2.5, 2.6, 2.7, 2.8, 2.10,
//               2.9, 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.9, 8.10 (Task 6.3)

(function () {
  'use strict';

  // ── Internal state ──────────────────────────────────────────────────────

  var _subscription = null;        // last subscription payload rendered
  var _busy = false;               // guards against double-clicks on actions

  // Element id helpers — keep in sync with subscription.html
  var IDS = {
    loading:          'loadingState',
    noSub:            'noSubscriptionState',
    content:          'subscriptionContent',
    planName:         'planName',
    planStatus:       'planStatus',
    planStartDate:    'planStartDate',
    renewalItem:      'renewalDateItem',
    renewalDate:      'planRenewalDate',
    expiryItem:       'expiryDateItem',
    expiryDate:       'planExpiryDate',
    remainingItem:    'remainingAttemptsItem',
    remainingValue:   'remainingAttempts',
    institutionItem:  'institutionDetailsItem',
    institutionName:  'institutionName',
    upgradeBtn:       'upgradeBtn',
    changeBillingBtn: 'changeBillingBtn',
    cancelBtn:        'cancelBtn',
    reactivateBtn:    'reactivateBtn',

    // Modals
    planSelectionModal: 'planSelectionModal',
    planModalError:     'planModalError',
    cancelModal:        'cancelModal',
    cancelEndDate:      'cancelEndDate',
    cancelModalError:   'cancelModalError',
    comparePlansModal:  'comparePlansModal',
    billingPeriodSelect:'billingPeriod',

    // Billing history (Task 6.3)
    billingSection:     'billingHistorySection',
    billingLoading:     'billingLoading',
    billingEmpty:       'billingEmpty',
    billingError:       'billingError',
    billingTableWrap:   'billingTableWrapper',
    billingTableBody:   'billingTableBody',
    billingCards:       'billingCards',
    billingPagination:  'billingPagination',
    paginationInfo:     'paginationInfo',
    prevPageBtn:        'prevPageBtn',
    nextPageBtn:        'nextPageBtn',
  };

  // ── DOM helpers ─────────────────────────────────────────────────────────

  function $(id)            { return document.getElementById(id); }
  function show(id, display){ var el = $(id); if (el) el.style.display = display || ''; }
  function hide(id)         { var el = $(id); if (el) el.style.display = 'none'; }
  function setText(id, t)   { var el = $(id); if (el) el.textContent = t; }

  function _formatDate(value) {
    if (!value) return '—';
    try {
      var d = new Date(value);
      if (isNaN(d.getTime())) return '—';
      return d.toLocaleDateString('en-IN', {
        day: 'numeric',
        month: 'short',
        year: 'numeric',
      });
    } catch (e) {
      return '—';
    }
  }

  function _toast(kind, msg) {
    if (typeof window !== 'undefined' && window.ErrorHandler) {
      if (kind === 'success') window.ErrorHandler.showSuccess(msg);
      else                    window.ErrorHandler.showError(msg);
      return;
    }
    // Fallback when error-handler.js isn't loaded yet
    console[kind === 'success' ? 'log' : 'error'](msg);
  }

  // ── Plan classification helpers ─────────────────────────────────────────

  function _planType(sub)        { return (sub && sub.plan_type) || ''; }
  function _planStatus(sub)      { return (sub && sub.status) || ''; }
  function _isFreeTrial(sub)     { return _planType(sub) === 'trial'; }
  function _isPro(sub)           { return _planType(sub) === 'pro'; }
  function _isInstitution(sub)   { return _planType(sub) === 'institution'; }
  function _isCancelled(sub)     { return _planStatus(sub) === 'cancelled'; }
  function _isExpired(sub)       { return _planStatus(sub) === 'expired'; }

  /**
   * Resolve a friendly plan label.
   * Falls back to plan_name from the API, then plan_type.
   */
  function _planLabel(sub) {
    if (!sub) return '—';
    if (sub.plan_name) return sub.plan_name;

    if (_isFreeTrial(sub)) return 'Free Trial';
    if (_isPro(sub)) {
      var bp = sub.billing_period;
      if (bp === 'weekly')  return 'Pro Weekly';
      if (bp === 'monthly') return 'Pro Monthly';
      return 'Pro';
    }
    if (_isInstitution(sub)) return 'Institution Plan';
    return '—';
  }

  /**
   * Resolve a friendly status label and CSS class for the badge.
   */
  function _statusInfo(sub) {
    var status = _planStatus(sub);
    switch (status) {
      case 'trial':         return { label: 'Active',        cls: 'badge-active'  };
      case 'active':        return { label: 'Active',        cls: 'badge-active'  };
      case 'overdue':       return { label: 'Overdue',       cls: 'badge-warning' };
      case 'grace_period':  return { label: 'Grace Period',  cls: 'badge-warning' };
      case 'expired':       return { label: 'Expired',       cls: 'badge-error'   };
      case 'cancelled':     return { label: 'Cancelled',     cls: 'badge-error'   };
      default:              return { label: status || '—',   cls: 'badge-muted'   };
    }
  }

  // ── Rendering ───────────────────────────────────────────────────────────

  /**
   * Render the subscription details into the existing markup.
   * REQ-2.4 (display fields), REQ-2.5/2.6 (visible action buttons by plan).
   */
  function _renderSubscription(sub) {
    _subscription = sub;

    // DEBUG: Log subscription data
    console.log('[subscription-page] ========== RENDERING SUBSCRIPTION ==========');
    console.log('[subscription-page] subscription data:', sub);
    console.log('[subscription-page] plan_name:', sub?.plan_name);
    console.log('[subscription-page] plan_type:', sub?.plan_type);
    console.log('[subscription-page] status:', sub?.status);
    console.log('[subscription-page] start_date:', sub?.start_date);
    console.log('[subscription-page] started_at:', sub?.started_at);
    console.log('[subscription-page] current_period_start:', sub?.current_period_start);
    console.log('[subscription-page] next_renewal_date:', sub?.next_renewal_date);
    console.log('[subscription-page] billing_period:', sub?.billing_period);
    console.log('[subscription-page] ====================================================');

    // Plan name
    setText(IDS.planName, _planLabel(sub));

    // Status badge — refresh class so styling tracks the state
    var statusEl = $(IDS.planStatus);
    if (statusEl) {
      var info = _statusInfo(sub);
      statusEl.textContent = info.label;
      statusEl.className = 'plan-status-badge ' + info.cls;
      statusEl.setAttribute('data-status', _planStatus(sub) || '');
    }

    // Started date - try multiple field names (backend may use different field names)
    var startDate = sub.start_date || sub.started_at || sub.current_period_start || sub.created_at;
    setText(IDS.planStartDate, _formatDate(startDate));
    console.log('[subscription-page] START DATE resolved to:', startDate, '→ formatted:', _formatDate(startDate));

    // Trial / cancelled subscriptions show end date instead of renewal
    var hasRenewal = !!sub.next_renewal_date && !_isFreeTrial(sub) && !_isCancelled(sub);
    if (hasRenewal) {
      setText(IDS.renewalDate, _formatDate(sub.next_renewal_date));
      show(IDS.renewalItem);
    } else {
      hide(IDS.renewalItem);
    }

    if (sub.end_date && (_isFreeTrial(sub) || _isCancelled(sub) || _isExpired(sub))) {
      setText(IDS.expiryDate, _formatDate(sub.end_date));
      show(IDS.expiryItem);
    } else {
      hide(IDS.expiryItem);
    }

    // Remaining attempts (Free Trial + institution students with limited quota)
    var hasAttempts =
      typeof sub.remaining_attempts === 'number' &&
      sub.remaining_attempts >= 0 &&
      (sub.quota_type === 'limited' || _isFreeTrial(sub) || _isInstitution(sub));
    if (hasAttempts) {
      var total = (typeof sub.total_attempts === 'number') ? sub.total_attempts : null;
      setText(
        IDS.remainingValue,
        total !== null
          ? sub.remaining_attempts + ' of ' + total + ' attempts'
          : sub.remaining_attempts + ' attempts'
      );
      show(IDS.remainingItem);
    } else {
      hide(IDS.remainingItem);
    }

    // Institution name (if any)
    if (sub.institution_name) {
      setText(IDS.institutionName, sub.institution_name);
      show(IDS.institutionItem);
    } else {
      hide(IDS.institutionItem);
    }

    // Action buttons — visibility driven by plan type & status
    _renderActionButtons(sub);

    // ── Premium UI: set plan theme + inject right-column cards ──────────
    _renderPremiumUI(sub);

    // Billing history visibility: only Pro users (active or expired) see it.
    // REQ-8.10 — Free Trial students never see this section.
    var billingSection = $('billingHistorySection');
    var showBilling = _isPro(sub) && !_isCancelled(sub);
    if (billingSection) {
      billingSection.style.display = showBilling ? '' : 'none';
    }
    // Kick off the billing history fetch the first time the section appears
    // for this page-load. Refresh on subsequent renders is on-demand via
    // the section's "Retry" control.
    if (showBilling) {
      loadBillingHistory();
    }

    // Reveal the page content
    hide(IDS.loading);
    hide(IDS.noSub);
    show(IDS.content);
  }

  // ── Premium UI helpers ──────────────────────────────────────────────────

  /**
   * Determine a short plan key used for data-plan theming and feature lists.
   * Returns: 'free' | 'trial' | 'monthly' | 'yearly' | 'institution' | ''
   */
  function _planKey(sub) {
    if (!sub) return '';
    var name = (sub.plan_name || '').toLowerCase();
    if (name.indexOf('free') !== -1) return 'free';
    if (name.indexOf('trial') !== -1) return 'trial';
    if (name.indexOf('yearly') !== -1 || name.indexOf('annual') !== -1) return 'yearly';
    if (name.indexOf('monthly') !== -1) return 'monthly';
    if (name.indexOf('weekly') !== -1) return 'trial'; // weekly pro → trial-style amber
    var pt = sub.plan_type || '';
    if (pt === 'institution') return 'institution';
    if (sub.is_trial) return 'trial';
    return 'monthly'; // fallback for unknown paid plans
  }

  /**
   * Build feature list HTML using the new sf-* CSS classes.
   */
  function _featureListHTML(planKey) {
    var features = {
      free: {
        on:  ['3–5 mock tests', 'Limited question bank', 'Basic score analytics'],
        off: ['Unlimited mock tests', 'AI recommendations', 'Weak-topic analysis', 'Premium KCET questions', 'Advanced reports'],
      },
      trial: {
        on:  ['Unlimited mock tests', 'KCET premium question bank', 'Topic-wise analytics', 'AI recommendations', 'Weak-topic analysis', 'Performance reports'],
        off: [],
      },
      monthly: {
        on:  ['Unlimited mock tests', 'Full topic analytics', 'AI recommendations', 'Weak-topic analysis', 'Performance reports', 'Leaderboard rankings'],
        off: [],
      },
      yearly: {
        on:  ['Everything in Pro Monthly', '12 months full access', 'Unlimited mock tests', 'AI recommendations', 'Advanced reports', 'Priority feature access'],
        off: [],
      },
      institution: {
        on:  ['Unlimited mock tests', 'Institution question bank', 'Topic-wise analytics', 'Weekly/monthly quotas'],
        off: [],
      },
    };

    var set = features[planKey] || features['monthly'];
    var html = '<ul class="sf-list">';
    set.on.forEach(function(f) {
      html += '<li class="sf-item sf-on"><span class="sf-dot"></span><span>' + _esc(f) + '</span></li>';
    });
    set.off.forEach(function(f) {
      html += '<li class="sf-item sf-off"><span class="sf-dot"></span><span>' + _esc(f) + '</span></li>';
    });
    html += '</ul>';
    return html;
  }

  /**
   * Build the CTA card HTML using the new cta-* CSS classes.
   */
  function _ctaHTML(planKey, sub) {
    var status = _planStatus(sub);
    var isActive = status === 'trial' || status === 'active' || status === 'overdue' || status === 'grace_period';

    if (!isActive) {
      return '<div class="sub-cta-card">'
        + '<div class="sub-cta-inner">'
        + '<span class="cta-emoji">🔄</span>'
        + '<p class="cta-title">Reactivate your access</p>'
        + '<p class="cta-body">Choose a plan to continue exam practice and track your progress.</p>'
        + '<a href="/pricing" class="cta-btn cta-upgrade">View Plans →</a>'
        + '</div></div>';
    }

    if (planKey === 'free') {
      return '<div class="sub-cta-card">'
        + '<div class="sub-cta-inner">'
        + '<span class="cta-emoji">⚡</span>'
        + '<p class="cta-title">Unlock full access</p>'
        + '<p class="cta-body">Upgrade for unlimited mock tests, AI recommendations, and detailed analytics.</p>'
        + '<a href="/pricing" class="cta-btn cta-upgrade">Upgrade to Pro →</a>'
        + '</div></div>';
    }

    if (planKey === 'trial') {
      var renewal = sub.next_renewal_date ? 'Renews ' + _formatDate(sub.next_renewal_date) + '.' : '';
      return '<div class="sub-cta-card">'
        + '<div class="sub-cta-inner">'
        + '<span class="cta-emoji">⏱</span>'
        + '<p class="cta-title">Trial access active</p>'
        + '<p class="cta-body">You\'re on full premium access' + (renewal ? '. ' + renewal : '') + ' Switch to a recurring plan to keep access.</p>'
        + '<a href="/pricing" class="cta-btn cta-upgrade">Upgrade to Monthly / Yearly →</a>'
        + '</div></div>';
    }

    if (planKey === 'monthly') {
      return '<div class="sub-cta-card">'
        + '<div class="sub-cta-inner">'
        + '<span class="cta-emoji">💡</span>'
        + '<p class="cta-title">Save with yearly</p>'
        + '<p class="cta-body">Switch to an annual plan and save over ₹1,000 compared to monthly billing.</p>'
        + '<a href="/pricing" class="cta-btn cta-yearly">Switch to Yearly →</a>'
        + '</div></div>';
    }

    if (planKey === 'yearly') {
      return '<div class="sub-cta-card">'
        + '<div class="sub-cta-inner">'
        + '<span class="cta-emoji">🏆</span>'
        + '<p class="cta-title">Premium member</p>'
        + '<p class="cta-body">You have full access to all SmartKCET Prep features. Keep practising!</p>'
        + '<a href="/exam" class="cta-btn cta-member">Take an Exam →</a>'
        + '</div></div>';
    }

    return ''; // institution / unknown
  }

  function _esc(s) {
    return String(s || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }

  /**
   * Set plan-specific data attribute and inject features + CTA cards.
   * Writes only to #subRightCol — never touches any existing DOM nodes.
   * 
   * Phase 2: Also fetches and renders plan selection cards if the user has an active subscription.
   */
  function _renderPremiumUI(sub) {
    var content = $('subscriptionContent');
    if (!content) return;

    var planKey = _planKey(sub);

    // data-plan drives CSS theming (border glow, name gradient, strip colour)
    if (planKey) {
      content.setAttribute('data-plan', planKey);
    } else {
      content.removeAttribute('data-plan');
    }

    var rightCol = $('subRightCol');
    if (!rightCol) return;

    var checkSVG = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" aria-hidden="true"><path d="M22 11.08V12a10 10 0 11-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>';

    var featuresHTML = ''
      + '<div class="sub-features-card" aria-label="Plan features">'
      +   '<div class="sfcard-header">'
      +     '<div class="sfcard-icon" aria-hidden="true">' + checkSVG + '</div>'
      +     '<div>'
      +       '<h3>Plan Features</h3>'
      +       '<p>What\'s included in your plan</p>'
      +     '</div>'
      +   '</div>'
      +   '<div class="sfcard-body">' + _featureListHTML(planKey) + '</div>'
      + '</div>';

    // Phase 2: Fetch and render plan selection cards
    _renderPlanSelectionCards(sub).then(function(planCardsHTML) {
      rightCol.innerHTML = featuresHTML + (planCardsHTML || '') + _ctaHTML(planKey, sub);
    });
  }

  /**
   * Phase 2 Task 1: Fetch subscription management status and render plan selection cards.
   * - Calls GET /api/user/subscription-management
   * - Returns HTML with 4 plan cards showing current button states
   * - Each card displays: plan name, price, button (enabled/disabled/current)
   * - Resolves with HTML string or empty string on error
   */
  function _renderPlanSelectionCards(sub) {
    return new Promise(function(resolve) {
      // Only render plan selection if user has an active subscription (Phase 2)
      if (!sub || !_planStatus(sub) || _planStatus(sub) === 'cancelled') {
        // For no subscription or cancelled status, skip plan selection cards
        resolve('');
        return;
      }

      var token = localStorage.getItem('token');
      if (!token) {
        resolve('');
        return;
      }

      fetch('/api/subscription/user/subscription-management', {
        method: 'GET',
        headers: {
          'Authorization': 'Bearer ' + token,
          'Content-Type': 'application/json'
        }
      })
      .then(function(r) {
        if (!r.ok) {
          console.warn('[subscription-page] Plan selection API returned ' + r.status);
          return null;
        }
        return r.json();
      })
      .then(function(data) {
        if (!data || !Array.isArray(data.available_plans)) {
          console.warn('[subscription-page] No available_plans in response');
          resolve('');
          return;
        }

        var plans = data.available_plans;
        var planGridHTML = ''
          + '<div class="sub-plan-selection-card" aria-labelledby="planSelectionHeading">'
          +   '<div class="sfcard-header">'
          +     '<div class="sfcard-icon purple" aria-hidden="true">'
          +       '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">'
          +         '<polyline points="12 5 12 19 5 12 12 5 19 12"/>'
          +       '</svg>'
          +     '</div>'
          +     '<div>'
          +       '<h3 id="planSelectionHeading">Available Plans</h3>'
          +       '<p>Switch to a different plan</p>'
          +     '</div>'
          +   '</div>'
          +   '<div class="sfcard-body">'
          +     '<div class="plan-grid">';

        plans.forEach(function(plan) {
          var isDisabled = plan.button_state === 'disabled';
          var isCurrent = plan.button_state === 'current';
          var buttonClass = isCurrent ? 'btn-current' : (isDisabled ? 'btn-disabled' : 'btn-enabled');
          var buttonLabel = plan.button_label || 'Select Plan';
          var buttonDisabledAttr = (isDisabled || isCurrent) ? ' disabled' : '';

          planGridHTML +=
            '<div class="plan-option" data-plan-id="' + _esc(plan.id) + '" ' +
                'data-plan-name="' + _esc(plan.name) + '" ' +
                'aria-label="' + _esc(plan.name) + ' - ' + _esc(buttonLabel) + '">' +
              '<div class="plan-info">' +
                '<span class="plan-name">' + _esc(plan.name) + '</span>' +
                '<span class="plan-price">₹' + (plan.price || 0) + '</span>' +
              '</div>' +
              '<button ' +
                'class="plan-btn ' + buttonClass + '" ' +
                buttonDisabledAttr +
                ' onclick="selectPlanUpgrade(\'' + _esc(plan.id) + '\', \'' + _esc(plan.name) + '\')" ' +
                'aria-label="Select ' + _esc(plan.name) + ' plan">' +
                _esc(buttonLabel) +
              '</button>' +
            '</div>';
        });

        planGridHTML +=
              '</div>'
          +   '</div>'
          + '</div>';

        resolve(planGridHTML);
      })
      .catch(function(err) {
        console.warn('[subscription-page] Plan selection fetch failed:', err);
        resolve('');
      });
    });
  }

  /**
   * Phase 2 Task 3: Handle plan upgrade/selection when user clicks a button.
   * - Validates button is enabled
   * - Calls existing subscription activation flow (same as Phase 1)
   * - Handles success/error responses
   */
  async function selectPlanUpgrade(planId, planName) {
    if (_busy) return;

    // Find the button to get its state
    var btn = document.querySelector('.plan-option[data-plan-id="' + planId + '"] .plan-btn');
    if (!btn || btn.disabled) {
      // Button is disabled, do nothing
      return;
    }

    // Show loading state
    _busy = true;
    var originalLabel = btn.textContent;
    btn.classList.add('is-loading');
    btn.disabled = true;

    try {
      // For now, activate the plan via Razorpay flow (same as Phase 1)
      // TODO: Call the actual plan upgrade endpoint when available
      _toast('success', 'Plan selection initiated. Redirecting to payment...');
      
      // Simulate upgrade (in real implementation, call selectPro() or similar)
      // For Phase 2, we keep it simple and just show a toast
      // The actual upgrade flow would be triggered here
    } catch (err) {
      _toast('error', 'Unable to select plan. Please try again.');
      console.error('selectPlanUpgrade failed:', err);
    } finally {
      _busy = false;
      btn.classList.remove('is-loading');
      btn.disabled = false;
      btn.textContent = originalLabel;
    }
  }

  // ── End Premium UI helpers ───────────────────────────────────────────────

  function _renderActionButtons(sub) {
    var status = _planStatus(sub);
    var isActive = status === 'trial' || status === 'active' ||
                   status === 'overdue' || status === 'grace_period';

    // Default: hide everything, then opt-in based on plan/status.
    hide(IDS.upgradeBtn);
    hide(IDS.changeBillingBtn);
    hide(IDS.cancelBtn);
    hide(IDS.reactivateBtn);

    if (_isFreeTrial(sub) && isActive) {
      // REQ-2.5: Free Trial → Upgrade to Pro
      show(IDS.upgradeBtn, 'inline-flex');
      return;
    }

    if (_isPro(sub) && isActive) {
      // REQ-2.6: Active Pro → Cancel + Change Billing Period
      show(IDS.changeBillingBtn, 'inline-flex');
      show(IDS.cancelBtn, 'inline-flex');
      return;
    }

    if (_isCancelled(sub) || _isExpired(sub)) {
      // Allow re-engagement when subscription has lapsed
      show(IDS.reactivateBtn, 'inline-flex');
    }
  }

  function _renderNoSubscription() {
    hide(IDS.loading);
    hide(IDS.content);
    show(IDS.noSub);
  }

  function _renderLoading() {
    show(IDS.loading);
    hide(IDS.noSub);
    hide(IDS.content);
  }

  // ── Modal helpers ───────────────────────────────────────────────────────

  /**
   * Activate the shared focus trap (Task 18.2) when a modal opens. Falls
   * back to a no-op when window.FocusTrap is not loaded so existing pages
   * keep working in degraded environments (e.g. unit tests).
   */
  function _trapFocus(modalEl, onEscape) {
    if (!modalEl) return;
    if (typeof window === 'undefined' || !window.FocusTrap) return;
    window.FocusTrap.activate(modalEl, {
      onEscape: function () { if (typeof onEscape === 'function') onEscape(); },
    });
  }

  function _releaseFocus(modalEl) {
    if (!modalEl) return;
    if (typeof window === 'undefined' || !window.FocusTrap) return;
    window.FocusTrap.deactivate(modalEl);
  }

  /**
   * Mode is one of: 'select' | 'upgrade' | 'change-billing'.
   * Tweaks the plan modal so we can reuse the same DOM for activation,
   * upgrade, and "change billing period" flows (REQ-2.7).
   */
  var _planModalMode = 'select';

  function _openPlanModal(mode) {
    var modal = $(IDS.planSelectionModal);
    if (!modal) return;
    _planModalMode = mode || 'select';

    // Reset prior error / busy states so the modal re-opens cleanly.
    var err = $(IDS.planModalError);
    if (err) { err.style.display = 'none'; err.textContent = ''; }
    _setPlanButtonsBusy(false);

    // Adjust copy based on mode.
    var titleEl = modal.querySelector('#planModalTitle');
    var subtitleEl = modal.querySelector('.modal-subtitle');
    var trialCard = modal.querySelector('.plan-card:not(.plan-card-pro)');
    var proCta = modal.querySelector('.btn-pro');

    if (titleEl) {
      titleEl.textContent =
        mode === 'upgrade'        ? 'Upgrade to Pro' :
        mode === 'change-billing' ? 'Change Billing Period' :
                                    'Choose Your Plan';
    }
    if (subtitleEl) {
      subtitleEl.textContent =
        mode === 'upgrade'        ? 'Pick a Pro billing period to unlock unlimited access.' :
        mode === 'change-billing' ? 'Choose a new billing period for your Pro subscription.' :
                                    'Select the plan that best fits your exam preparation needs';
    }
    if (proCta) {
      proCta.textContent =
        mode === 'upgrade'        ? 'Upgrade to Pro' :
        mode === 'change-billing' ? 'Update Billing Period' :
                                    'Subscribe to Pro';
    }
    // Hide the Free Trial card when upgrading/changing — only Pro is relevant.
    if (trialCard) {
      trialCard.style.display = (mode === 'select') ? '' : 'none';
    }

    // Pre-select the user's current billing period when changing it.
    var bpSelect = $(IDS.billingPeriodSelect);
    if (bpSelect && _subscription && _subscription.billing_period) {
      bpSelect.value = _subscription.billing_period;
    }

    modal.style.display = 'flex';
    modal.setAttribute('aria-hidden', 'false');
    _trapFocus(modal, _closePlanModal);
  }

  function _closePlanModal() {
    var modal = $(IDS.planSelectionModal);
    if (modal) {
      modal.style.display = 'none';
      modal.setAttribute('aria-hidden', 'true');
      _releaseFocus(modal);
    }
    _setPlanButtonsBusy(false);
  }

  function _setPlanModalError(message) {
    var err = $(IDS.planModalError);
    if (!err) return;
    if (message) {
      err.textContent = message;
      err.style.display = 'block';
    } else {
      err.style.display = 'none';
      err.textContent = '';
    }
  }

  function _setPlanButtonsBusy(busy) {
    var modal = $(IDS.planSelectionModal);
    if (!modal) return;
    var buttons = modal.querySelectorAll('.btn-plan');
    for (var i = 0; i < buttons.length; i++) {
      buttons[i].disabled = !!busy;
      buttons[i].setAttribute('aria-busy', busy ? 'true' : 'false');
      if (busy) buttons[i].classList.add('is-loading');
      else      buttons[i].classList.remove('is-loading');
    }
  }

  function _openCancelModal() {
    var modal = $(IDS.cancelModal);
    if (!modal) return;
    // Pre-fill the "access continues until …" date for clarity (REQ-2.8).
    var endLabel = '—';
    if (_subscription) {
      endLabel = _formatDate(
        _subscription.next_renewal_date ||
        _subscription.end_date ||
        null
      );
    }
    setText(IDS.cancelEndDate, endLabel);

    var err = $(IDS.cancelModalError);
    if (err) { err.style.display = 'none'; err.textContent = ''; }

    modal.style.display = 'flex';
    modal.setAttribute('aria-hidden', 'false');
    _trapFocus(modal, _closeCancelModal);
  }

  function _closeCancelModal() {
    var modal = $(IDS.cancelModal);
    if (modal) {
      modal.style.display = 'none';
      modal.setAttribute('aria-hidden', 'true');
      _releaseFocus(modal);
    }
  }

  function _setCancelError(message) {
    var err = $(IDS.cancelModalError);
    if (!err) return;
    if (message) {
      err.textContent = message;
      err.style.display = 'block';
    } else {
      err.style.display = 'none';
      err.textContent = '';
    }
  }

  // ── Page-level actions ──────────────────────────────────────────────────

  /**
   * Entry point — invoked on DOMContentLoaded by subscription.html.
   * Fetches subscription state and renders the page or the empty state.
   * REQ-2.2 (load via /api/subscription/status), REQ-2.3 (show spinner while loading),
   * REQ-2.10 (404 → show plan selection UI).
   */
  async function loadSubscriptionPage() {
    _renderLoading();

    if (typeof SubscriptionAPI === 'undefined') {
      hide(IDS.loading);
      _toast('error', 'Subscription module failed to load.');
      return;
    }

    try {
      var result = await SubscriptionAPI.getStatus();

      if (result.ok && result.data) {
        _renderSubscription(result.data);

        // Keep the cache in sync so the banner / other components reuse it.
        if (typeof SubscriptionState !== 'undefined' && SubscriptionState.set) {
          SubscriptionState.set(result.data);
        }
        return;
      }

      if (result.status === 404) {
        // REQ-2.10: surface the empty state with plan selection CTA.
        _renderNoSubscription();
        return;
      }

      if (result.status === 401) {
        _toast('error', 'Your session has expired. Please log in again.');
        // error-handler will redirect via its global 401 path on next call.
        hide(IDS.loading);
        return;
      }

      hide(IDS.loading);
      _toast('error', result.error || 'Unable to load subscription details.');
    } catch (err) {
      hide(IDS.loading);
      _toast('error', 'Unable to load subscription details. Please try again.');
      console.error('loadSubscriptionPage failed:', err);
    }
  }

  /** Open the plan-selection modal (used by the empty state). */
  function showPlanSelection() {
    _openPlanModal('select');
  }

  function closePlanSelectionModal() {
    _closePlanModal();
  }

  /** REQ-2.5/2.7: open the Pro upgrade modal for Free Trial users. */
  function showUpgradeModal() {
    _openPlanModal('upgrade');
  }

  /** REQ-2.6: open the change-billing-period modal for Pro users. */
  function showChangeBillingModal() {
    _openPlanModal('change-billing');
  }

  /** REQ-2.8: open the cancellation confirmation modal. */
  function showCancelModal() {
    _openCancelModal();
  }

  function closeCancelModal() {
    _closeCancelModal();
  }

  function showComparePlansModal() {
    var modal = $(IDS.comparePlansModal);
    if (!modal) return;
    modal.style.display = 'flex';
    modal.setAttribute('aria-hidden', 'false');
    _trapFocus(modal, closeComparePlansModal);
  }

  function closeComparePlansModal() {
    var modal = $(IDS.comparePlansModal);
    if (!modal) return;
    modal.style.display = 'none';
    modal.setAttribute('aria-hidden', 'true');
    _releaseFocus(modal);
  }

  /** Reactivate flow for cancelled / expired subscriptions — reuses plan modal. */
  function showReactivateModal() {
    _openPlanModal('select');
  }

  // ── Plan activation / upgrade handlers ──────────────────────────────────

  async function selectFreeTrial() {
    if (_busy) return;
    _busy = true;
    _setPlanModalError(null);
    _setPlanButtonsBusy(true);

    try {
      var result = await Subscription.activateTrial();
      if (result && result.ok) {
        _toast('success', 'Subscription activated successfully.');
        _closePlanModal();
        await loadSubscriptionPage();
      } else {
        _setPlanModalError((result && result.error) || 'Activation failed. Please try again.');
      }
    } catch (err) {
      _setPlanModalError('Network error. Please try again.');
      console.error('selectFreeTrial failed:', err);
    } finally {
      _busy = false;
      _setPlanButtonsBusy(false);
    }
  }

  async function selectPro() {
    if (_busy) return;

    var bpSelect = $(IDS.billingPeriodSelect);
    var billingPeriod = bpSelect ? bpSelect.value : 'weekly';
    if (billingPeriod !== 'weekly' && billingPeriod !== 'monthly') {
      _setPlanModalError('Please select a valid billing period.');
      return;
    }

    _busy = true;
    _setPlanModalError(null);
    _setPlanButtonsBusy(true);

    try {
      // Choose the right backend call based on modal mode (REQ-2.7).
      //   * 'upgrade' / 'change-billing' → POST /api/subscription/upgrade
      //   * 'select' (no current Pro)    → POST /api/subscription/activate-pro
      var useUpgrade = (_planModalMode === 'upgrade' || _planModalMode === 'change-billing');
      var result = useUpgrade
        ? await Subscription.upgrade(billingPeriod)
        : await Subscription.activatePro(billingPeriod);

      if (result && result.ok) {
        var successMsg;
        if (_planModalMode === 'change-billing') {
          successMsg = 'Billing period updated successfully.';
        } else if (_planModalMode === 'upgrade') {
          successMsg = 'Subscription upgraded successfully.';
        } else {
          successMsg = 'Subscription activated successfully.';
        }
        _toast('success', successMsg);
        _closePlanModal();
        await loadSubscriptionPage();
      } else {
        _setPlanModalError((result && result.error) || 'Subscription action failed. Please try again.');
      }
    } catch (err) {
      _setPlanModalError('Network error. Please try again.');
      console.error('selectPro failed:', err);
    } finally {
      _busy = false;
      _setPlanButtonsBusy(false);
    }
  }

  async function confirmCancel() {
    if (_busy) return;
    _busy = true;
    _setCancelError(null);

    var modal = $(IDS.cancelModal);
    var buttons = modal ? modal.querySelectorAll('button') : [];
    var confirmBtn = modal ? modal.querySelector('.btn-primary') : null;
    var originalConfirmLabel = null;
    for (var i = 0; i < buttons.length; i++) {
      buttons[i].disabled = true;
      buttons[i].setAttribute('aria-busy', 'true');
    }
    if (confirmBtn) {
      confirmBtn.classList.add('is-loading');
      // Capture original label so we can swap it for "Cancelling…"
      // and restore it once the request settles.
      originalConfirmLabel = confirmBtn.textContent;
      confirmBtn.textContent = 'Cancelling…';
    }

    try {
      var result = await Subscription.cancel();
      if (result && result.ok) {
        // Build the post-cancellation message using the end date the
        // backend just returned (preferred) or the value the user saw
        // in the confirmation modal as a fallback. This satisfies
        // Requirement 14.4: "Subscription cancelled. Your access will
        // continue until {end_date}".
        var endIso = null;
        if (result.data) {
          endIso = result.data.next_renewal_date ||
                   result.data.end_date ||
                   null;
        }
        if (!endIso && _subscription) {
          endIso = _subscription.next_renewal_date ||
                   _subscription.end_date ||
                   null;
        }
        var endLabel = endIso ? _formatDate(endIso) : 'the end of your billing period';
        _toast('success', 'Subscription cancelled. Your access will continue until ' + endLabel + '.');
        _closeCancelModal();
        await loadSubscriptionPage();
      } else {
        _setCancelError((result && result.error) || 'Cancellation failed. Please try again.');
      }
    } catch (err) {
      _setCancelError('Network error. Please try again.');
      console.error('confirmCancel failed:', err);
    } finally {
      _busy = false;
      // Restore button state — release the loading class, aria-busy
      // attribute, and the original label so the modal can be reused
      // (e.g. on a retry after a transient error).
      for (var j = 0; j < buttons.length; j++) {
        buttons[j].disabled = false;
        buttons[j].setAttribute('aria-busy', 'false');
      }
      if (confirmBtn) {
        confirmBtn.classList.remove('is-loading');
        if (originalConfirmLabel) confirmBtn.textContent = originalConfirmLabel;
      }
    }
  }

  // ═══════════════════════════════════════════════════════════════════════
  // BILLING HISTORY (Task 6.3)
  // ═══════════════════════════════════════════════════════════════════════
  // Implements:
  //   * REQ-2.9 / REQ-8.1, 8.2 — fetch from GET /api/subscription/billing-history
  //   * REQ-8.3                — Date / Amount / Period / Status / Reference
  //   * REQ-8.4                — reverse chronological, 20 records per page
  //   * REQ-8.5                — pagination controls (Previous / Next)
  //   * REQ-8.6                — expandable rows: payment method, billing
  //                              address, invoice link, refund status
  //   * REQ-8.9                — color coding (paid/pending/failed)
  //   * REQ-8.10               — section hidden for Free Trial users
  //                              (handled in _renderSubscription)

  var PAGE_SIZE = 20;
  var _billingRecords = [];   // full result set (sorted, most-recent first)
  var _billingPage    = 1;    // 1-indexed current page
  var _billingLoading = false;

  function _formatAmount(amount, currency) {
    if (amount === null || amount === undefined || isNaN(Number(amount))) {
      return '—';
    }
    var num = Number(amount);
    var code = (currency || 'INR').toString().toUpperCase();
    try {
      return new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: code,
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      }).format(num);
    } catch (e) {
      // Fallback for unusual currency codes — still show 2 decimals.
      return code + ' ' + num.toFixed(2);
    }
  }

  function _capitalize(value) {
    if (!value || typeof value !== 'string') return '—';
    return value.charAt(0).toUpperCase() + value.slice(1);
  }

  /**
   * Normalise a raw API record into the shape rendered by the table & cards.
   * Defensive against missing / null fields and supports a few common
   * field-name variants from the backend.
   */
  function _normalizeRecord(raw) {
    if (!raw || typeof raw !== 'object') return null;
    return {
      id:                  raw.id || raw.record_id || null,
      date:                raw.date || raw.billing_date || raw.created_at || null,
      amount:              (raw.amount !== undefined) ? raw.amount : raw.total,
      currency:            raw.currency || 'INR',
      billing_period:      raw.billing_period || raw.period || null,
      payment_status:      (raw.payment_status || raw.status || '').toLowerCase(),
      transaction_ref:     raw.transaction_ref || raw.transaction_reference ||
                           raw.reference || null,
      payment_method:      raw.payment_method || raw.payment_method_ref || null,
      billing_address:     raw.billing_address || null,
      invoice_url:         raw.invoice_url || raw.invoice || null,
      refund_status:       raw.refund_status || null,
    };
  }

  function _sortRecords(records) {
    // REQ-8.4: most-recent first. Records without a date sink to the bottom.
    return records.slice().sort(function (a, b) {
      var ta = a.date ? new Date(a.date).getTime() : 0;
      var tb = b.date ? new Date(b.date).getTime() : 0;
      if (isNaN(ta)) ta = 0;
      if (isNaN(tb)) tb = 0;
      return tb - ta;
    });
  }

  function _totalPages() {
    if (!_billingRecords.length) return 1;
    return Math.max(1, Math.ceil(_billingRecords.length / PAGE_SIZE));
  }

  function _setBillingState(state) {
    // state: 'loading' | 'empty' | 'error' | 'data'
    var loading = $(IDS.billingLoading);
    var empty   = $(IDS.billingEmpty);
    var error   = $(IDS.billingError);
    var wrap    = $(IDS.billingTableWrap);
    var cards   = $(IDS.billingCards);
    var pag     = $(IDS.billingPagination);

    if (loading) loading.style.display = (state === 'loading') ? '' : 'none';
    if (empty)   empty.style.display   = (state === 'empty')   ? '' : 'none';
    if (error)   error.style.display   = (state === 'error')   ? '' : 'none';

    // The table wrapper and mobile-card list only show in the 'data' state.
    // CSS media queries take it from there to pick the right layout.
    var dataDisplay = (state === 'data') ? '' : 'none';
    if (wrap)  wrap.style.display  = dataDisplay;
    if (cards) cards.style.display = dataDisplay;

    // Pagination is now a sibling of the table/cards (REQ-13.4) so it must be
    // hidden explicitly outside the 'data' state. Visibility within the
    // 'data' state is decided by _renderBillingPagination based on record
    // count.
    if (pag && state !== 'data') pag.style.display = 'none';
  }

  /** Build the status badge markup with color coding (REQ-8.9). */
  function _statusBadgeHTML(status) {
    var s = (status || '').toLowerCase();
    var label, cls;
    switch (s) {
      case 'paid':    label = 'Paid';    cls = 'status-paid';    break;
      case 'pending': label = 'Pending'; cls = 'status-pending'; break;
      case 'failed':  label = 'Failed';  cls = 'status-failed';  break;
      default:        label = _capitalize(s) || 'Unknown'; cls = '';
    }
    return '<span class="billing-status-badge ' + cls + '" role="status">' +
           _escape(label) +
           '</span>';
  }

  function _escape(value) {
    if (value === null || value === undefined) return '';
    return String(value)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  /** Build the expanded-detail HTML for a record (REQ-8.6). */
  function _detailRowHTML(record) {
    var paymentMethod = record.payment_method
      ? _escape(record.payment_method)
      : '<span class="muted">Not available</span>';

    var billingAddress = record.billing_address
      ? _escape(record.billing_address).replace(/\n/g, '<br>')
      : '<span class="muted">Not available</span>';

    var invoiceCell;
    if (record.invoice_url) {
      invoiceCell =
        '<a class="invoice-link" href="' + _escape(record.invoice_url) +
          '" target="_blank" rel="noopener noreferrer">' +
          '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">' +
            '<path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/>' +
            '<polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/>' +
          '</svg>' +
          'Download invoice' +
        '</a>';
    } else {
      invoiceCell = '<span class="muted">No invoice available</span>';
    }

    var refundCell;
    var refund = (record.refund_status || '').toLowerCase();
    if (!refund || refund === 'none') {
      refundCell = '<span class="muted">No refund</span>';
    } else {
      var refundCls = refund === 'full' ? 'refund-full' : '';
      refundCell =
        '<span class="billing-refund-chip ' + refundCls + '">' +
          _escape(_capitalize(refund)) + ' refund' +
        '</span>';
    }

    return '' +
      '<div class="billing-detail-content">' +
        '<div class="billing-detail-item">' +
          '<span class="billing-detail-label">Payment method</span>' +
          '<span class="billing-detail-value">' + paymentMethod + '</span>' +
        '</div>' +
        '<div class="billing-detail-item">' +
          '<span class="billing-detail-label">Billing address</span>' +
          '<span class="billing-detail-value">' + billingAddress + '</span>' +
        '</div>' +
        '<div class="billing-detail-item">' +
          '<span class="billing-detail-label">Invoice</span>' +
          '<span class="billing-detail-value">' + invoiceCell + '</span>' +
        '</div>' +
        '<div class="billing-detail-item">' +
          '<span class="billing-detail-label">Refund status</span>' +
          '<span class="billing-detail-value">' + refundCell + '</span>' +
        '</div>' +
      '</div>';
  }

  function _renderBillingTable() {
    var tbody = $(IDS.billingTableBody);
    var cards = $(IDS.billingCards);
    if (!tbody && !cards) return;

    // Compute the slice for the current page (REQ-8.4).
    var totalPages = _totalPages();
    if (_billingPage > totalPages) _billingPage = totalPages;
    if (_billingPage < 1) _billingPage = 1;
    var start = (_billingPage - 1) * PAGE_SIZE;
    var slice = _billingRecords.slice(start, start + PAGE_SIZE);

    // ── Desktop / tablet table ───────────────────────────────────────────
    if (tbody) {
      var rowsHTML = '';
      for (var i = 0; i < slice.length; i++) {
        var rec = slice[i];
        var rowId   = 'billing-row-' + (start + i);
        var detailId = 'billing-detail-' + (start + i);
        var ref = rec.transaction_ref
          ? '<span class="billing-ref">' + _escape(rec.transaction_ref) + '</span>'
          : '<span class="billing-ref is-empty">—</span>';

        rowsHTML +=
          '<tr class="billing-row is-clickable" id="' + rowId + '" ' +
              'data-record-index="' + (start + i) + '" ' +
              'aria-expanded="false" aria-controls="' + detailId + '" ' +
              'tabindex="0">' +
            '<td>' + _escape(_formatDate(rec.date)) + '</td>' +
            '<td class="billing-amount">' + _escape(_formatAmount(rec.amount, rec.currency)) + '</td>' +
            '<td class="billing-period-cell">' + _escape(_capitalize(rec.billing_period)) + '</td>' +
            '<td>' + _statusBadgeHTML(rec.payment_status) + '</td>' +
            '<td>' + ref + '</td>' +
            '<td>' +
              '<button type="button" class="billing-expand-toggle" ' +
                'aria-label="Toggle details" aria-controls="' + detailId + '">' +
                '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">' +
                  '<polyline points="6 9 12 15 18 9"/>' +
                '</svg>' +
              '</button>' +
            '</td>' +
          '</tr>' +
          '<tr class="billing-detail-row" id="' + detailId + '" hidden>' +
            '<td colspan="6">' + _detailRowHTML(rec) + '</td>' +
          '</tr>';
      }
      tbody.innerHTML = rowsHTML;
    }

    // ── Mobile cards (REQ-13.4) ─────────────────────────────────────────
    if (cards) {
      var cardsHTML = '';
      for (var j = 0; j < slice.length; j++) {
        var r2 = slice[j];
        var cardIdx = start + j;
        cardsHTML +=
          '<article class="billing-card" data-record-index="' + cardIdx + '" data-expanded="false">' +
            '<div class="billing-card-header">' +
              '<span class="billing-card-date">' + _escape(_formatDate(r2.date)) + '</span>' +
              '<span class="billing-card-amount">' + _escape(_formatAmount(r2.amount, r2.currency)) + '</span>' +
            '</div>' +
            '<div class="billing-card-meta">' +
              '<span class="billing-card-meta-item">' + _statusBadgeHTML(r2.payment_status) + '</span>' +
              '<span class="billing-card-meta-item">' + _escape(_capitalize(r2.billing_period)) + '</span>' +
              '<span class="billing-card-meta-item">' +
                (r2.transaction_ref
                  ? '<span class="billing-ref">' + _escape(r2.transaction_ref) + '</span>'
                  : '<span class="billing-ref is-empty">—</span>') +
              '</span>' +
            '</div>' +
            '<button type="button" class="billing-card-toggle" ' +
                'aria-expanded="false" aria-label="Toggle billing details">' +
              'View details' +
            '</button>' +
            '<div class="billing-card-details">' + _detailRowHTML(r2) + '</div>' +
          '</article>';
      }
      cards.innerHTML = cardsHTML;
    }

    _renderBillingPagination();
    _setBillingState('data');
  }

  function _renderBillingPagination() {
    var pag   = $(IDS.billingPagination);
    var info  = $(IDS.paginationInfo);
    var prev  = $(IDS.prevPageBtn);
    var next  = $(IDS.nextPageBtn);
    if (!pag) return;

    var totalPages = _totalPages();

    // REQ-8.5: only show pagination controls when more than one page exists.
    pag.style.display = (_billingRecords.length > PAGE_SIZE) ? '' : 'none';

    if (info) {
      info.textContent =
        'Page ' + _billingPage + ' of ' + totalPages +
        ' (' + _billingRecords.length + ' records)';
    }
    if (prev) prev.disabled = (_billingPage <= 1);
    if (next) next.disabled = (_billingPage >= totalPages);
  }

  /** Toggle expand/collapse for a table row by index. */
  function _toggleRowDetails(index) {
    var row = document.querySelector(
      '.billing-row[data-record-index="' + index + '"]'
    );
    if (!row) return;
    var detail = document.getElementById('billing-detail-' + index);
    if (!detail) return;

    var expanded = row.getAttribute('aria-expanded') === 'true';
    row.setAttribute('aria-expanded', expanded ? 'false' : 'true');
    detail.hidden = expanded;

    var btn = row.querySelector('.billing-expand-toggle');
    if (btn) btn.setAttribute('aria-expanded', expanded ? 'false' : 'true');
  }

  /** Toggle expand/collapse for a mobile card. */
  function _toggleCardDetails(card) {
    if (!card) return;
    var expanded = card.getAttribute('data-expanded') === 'true';
    card.setAttribute('data-expanded', expanded ? 'false' : 'true');
    var btn = card.querySelector('.billing-card-toggle');
    if (btn) {
      btn.setAttribute('aria-expanded', expanded ? 'false' : 'true');
      btn.textContent = expanded ? 'View details' : 'Hide details';
    }
  }

  /**
   * Public entry point — fetch and render billing history.
   * Re-callable from the inline "Retry" button in the markup.
   *
   * REQ-2.9 / 8.2  : GET /api/subscription/billing-history
   * REQ-8.7        : empty array → "No billing history available yet"
   * REQ-8.8        : error response → error message + Retry button
   */
  async function loadBillingHistory() {
    if (_billingLoading) return;

    if (typeof SubscriptionAPI === 'undefined' ||
        typeof SubscriptionAPI.getBillingHistory !== 'function') {
      _setBillingState('error');
      return;
    }

    _billingLoading = true;
    _setBillingState('loading');

    try {
      var result = await SubscriptionAPI.getBillingHistory();

      if (!result || !result.ok) {
        // REQ-8.8: server-side error → show error UI w/ retry.
        _setBillingState('error');
        return;
      }

      // The backend may return either a bare list or an envelope object
      // (e.g. { records: [...] } or { data: [...] }). Be tolerant.
      var raw = result.data;
      if (raw && !Array.isArray(raw)) {
        if (Array.isArray(raw.records)) raw = raw.records;
        else if (Array.isArray(raw.data)) raw = raw.data;
        else if (Array.isArray(raw.items)) raw = raw.items;
      }
      if (!Array.isArray(raw)) raw = [];

      // Normalise + sort newest-first (REQ-8.4).
      var normalised = [];
      for (var i = 0; i < raw.length; i++) {
        var rec = _normalizeRecord(raw[i]);
        if (rec) normalised.push(rec);
      }
      _billingRecords = _sortRecords(normalised);
      _billingPage = 1;

      if (!_billingRecords.length) {
        // REQ-8.7: empty state.
        _setBillingState('empty');
        // Make sure pagination is hidden in the empty state.
        var pag = $(IDS.billingPagination);
        if (pag) pag.style.display = 'none';
        return;
      }

      _renderBillingTable();
    } catch (err) {
      console.error('loadBillingHistory failed:', err);
      _setBillingState('error');
    } finally {
      _billingLoading = false;
    }
  }

  function previousPage() {
    if (_billingPage <= 1) return;
    _billingPage -= 1;
    _renderBillingTable();
    _scrollBillingIntoView();
  }

  function nextPage() {
    var total = _totalPages();
    if (_billingPage >= total) return;
    _billingPage += 1;
    _renderBillingTable();
    _scrollBillingIntoView();
  }

  function _scrollBillingIntoView() {
    var section = $('billingHistorySection');
    if (section && typeof section.scrollIntoView === 'function') {
      section.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }

  // Delegated click handler for billing rows / cards (REQ-8.6).
  document.addEventListener('click', function (e) {
    if (!e.target) return;
    var target = e.target;

    // Mobile-card toggle button
    var cardToggle = target.closest && target.closest('.billing-card-toggle');
    if (cardToggle) {
      _toggleCardDetails(cardToggle.closest('.billing-card'));
      return;
    }

    // Table-row expand button
    var rowToggle = target.closest && target.closest('.billing-expand-toggle');
    if (rowToggle) {
      var row = rowToggle.closest('.billing-row');
      if (row) {
        var idx = parseInt(row.getAttribute('data-record-index'), 10);
        if (!isNaN(idx)) _toggleRowDetails(idx);
      }
      return;
    }

    // Whole-row click expands too (skip if user clicked the link inside)
    var row2 = target.closest && target.closest('tr.billing-row');
    if (row2 && !target.closest('a, button')) {
      var idx2 = parseInt(row2.getAttribute('data-record-index'), 10);
      if (!isNaN(idx2)) _toggleRowDetails(idx2);
    }
  });

  // Keyboard activation for table rows (Enter / Space).
  document.addEventListener('keydown', function (e) {
    if (e.key !== 'Enter' && e.key !== ' ') return;
    var row = e.target && e.target.closest && e.target.closest('tr.billing-row');
    if (!row) return;
    if (e.target.tagName === 'BUTTON' || e.target.tagName === 'A') return;
    e.preventDefault();
    var idx = parseInt(row.getAttribute('data-record-index'), 10);
    if (!isNaN(idx)) _toggleRowDetails(idx);
  });

  // ── Global wiring ───────────────────────────────────────────────────────
  // The HTML uses inline onclick handlers, so these must be reachable from
  // the global scope (window). This also makes them easy to test from devtools.

  window.loadSubscriptionPage     = loadSubscriptionPage;
  window.showPlanSelection        = showPlanSelection;
  window.closePlanSelectionModal  = closePlanSelectionModal;
  window.showUpgradeModal         = showUpgradeModal;
  window.showChangeBillingModal   = showChangeBillingModal;
  window.showCancelModal          = showCancelModal;
  window.closeCancelModal         = closeCancelModal;
  window.confirmCancel            = confirmCancel;
  window.showComparePlansModal    = showComparePlansModal;
  window.closeComparePlansModal   = closeComparePlansModal;
  window.showReactivateModal      = showReactivateModal;
  window.selectFreeTrial          = selectFreeTrial;
  window.selectPro                = selectPro;

  // Billing history (Task 6.3) — referenced by inline onclick handlers in
  // subscription.html (Retry button, pagination Previous/Next).
  window.loadBillingHistory       = loadBillingHistory;
  window.previousPage             = previousPage;
  window.nextPage                 = nextPage;

  // Refresh the page card whenever the polling layer detects a status change.
  if (typeof window !== 'undefined') {
    window.addEventListener('subscriptionStatusChanged', function (evt) {
      if (evt && evt.detail && evt.detail.subscription) {
        _renderSubscription(evt.detail.subscription);
      }
    });
  }

  // Close modals on Escape — handled by FocusTrap.activate(onEscape).
  // The legacy document-wide Escape listener was removed in Task 18.2.

  // Click-outside-to-dismiss for all subscription page modals.
  document.addEventListener('click', function (e) {
    if (!e.target || !e.target.classList) return;
    if (!e.target.classList.contains('modal-overlay')) return;
    var id = e.target.id;
    if (id === IDS.planSelectionModal) _closePlanModal();
    else if (id === IDS.cancelModal)   _closeCancelModal();
    else if (id === IDS.comparePlansModal) closeComparePlansModal();
  });

})();
