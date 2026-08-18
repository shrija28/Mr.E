// Mr.E — Upgrade Prompt Component (Task 7.1)
// -----------------------------------------------------------------------------
// Renders contextual upgrade prompts that nudge Free Trial / expired students
// to upgrade to a Pro subscription. Handles two visual flavours:
//
//   1. Banner prompt — sticky banner below the subscription banner, used for:
//        • REQ-7.1  4 of 5 attempts used (1 attempt remaining)
//        • REQ-7.2  ≤ 2 days remaining in trial
//
//   2. Full-page prompt — overlay that covers the page, used for:
//        • REQ-7.3  Free Trial attempts exhausted (Exam_Page)
//        • REQ-7.4  Free Trial expired (all student pages)
//        • REQ-7.8  Subscription expired on Dashboard_Page
//
// Both flavours are dismissible (REQ-7.5) and remember the dismissal in
// sessionStorage for the current session only — prompts reappear next login.
//
// Public API:
//   UpgradePrompt.show(subscriptionData, options?)
//   UpgradePrompt.hide()
//   UpgradePrompt.dismiss()
//   UpgradePrompt.shouldShow(subscriptionData, options?)
//
// Pairs with `subscription.css` (`.upgrade-prompt-banner`,
// `.upgrade-prompt-fullpage`) and `subscription.js` (Subscription module).
//
// Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.8

var UpgradePrompt = (function () {
  'use strict';

  // ── Constants ───────────────────────────────────────────────────────────

  var BANNER_ID = 'upgradePromptBanner';
  var FULLPAGE_ID = 'upgradePromptFullpage';
  var DISMISS_KEY = 'smartkcet_upgrade_prompt_dismissed';

  // Threshold values (REQ-7.1, REQ-7.2)
  var ATTEMPTS_LOW_THRESHOLD = 1; // remaining ≤ 1 → banner
  var DAYS_LOW_THRESHOLD = 2;     // days_remaining ≤ 2 → banner

  // Internal state
  var _bannerEl = null;
  var _fullpageEl = null;
  var _currentVariant = null;
  var _statusChangeHandler = null;
  // Tracks whether the shared FocusTrap is currently active on the
  // full-page overlay so we don't double-activate or double-release it
  // (Task 18.2, REQ-13.6, REQ-13.7).
  var _fullpageTrapActive = false;

  // ── Helpers ─────────────────────────────────────────────────────────────

  function _escape(str) {
    if (str === null || str === undefined) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  /**
   * Build the dismissal record key for a specific variant so different
   * prompts (banner vs full-page, attempts vs trial-expired) are tracked
   * independently within the same session.
   */
  function _dismissKey(variant) {
    return DISMISS_KEY + ':' + (variant || 'default');
  }

  function _isDismissed(variant) {
    try {
      var raw = sessionStorage.getItem(_dismissKey(variant));
      if (!raw) return false;
      var parsed = JSON.parse(raw);
      return !!(parsed && parsed.dismissed);
    } catch (e) {
      return false;
    }
  }

  function _setDismissed(variant) {
    try {
      sessionStorage.setItem(
        _dismissKey(variant),
        JSON.stringify({ dismissed: true, timestamp: Date.now() })
      );
    } catch (e) {
      /* sessionStorage may be unavailable — silently ignore */
    }
  }

  /**
   * Determine the appropriate variant for the given subscription data.
   * Returns one of:
   *   'attempts-exhausted' (full-page, REQ-7.3)   — trial, 0 attempts left
   *   'trial-expired'      (full-page, REQ-7.4)   — trial period ended
   *   'subscription-expired' (full-page, REQ-7.8) — pro/expired on dashboard
   *   'attempts-low'       (banner, REQ-7.1)      — trial, 1 attempt left
   *   'days-low'           (banner, REQ-7.2)      — trial, ≤ 2 days left
   *   null                                        — no prompt warranted
   *
   * REQ-7.7: Pro / institution access never sees an upgrade prompt.
   */
  function _classify(data, options) {
    if (!data) return null;

    var planType = data.plan_type || '';
    var status = data.status || '';

    // REQ-7.7 — never prompt Pro or institution-linked users.
    if (planType === 'pro' && status === 'active') return null;
    if (planType === 'institution' && status === 'active') return null;

    var pageHint = (options && options.page) || _detectPage();

    // ── Full-page variants ────────────────────────────────────────────
    // REQ-7.4: Trial expired → all student pages.
    if (planType === 'trial' && (status === 'expired' || status === 'cancelled')) {
      return 'trial-expired';
    }

    // REQ-7.8: Subscription expired on dashboard → full-page overlay.
    if (status === 'expired' || status === 'cancelled') {
      // Show full-page overlay on dashboard; on other pages let the banner
      // in subscription-banner.js handle the messaging.
      if (pageHint === 'dashboard') return 'subscription-expired';
      // On the exam page treat as exhausted-style block (REQ-7.3 scope)
      if (pageHint === 'exam') return 'subscription-expired';
    }

    // REQ-7.3: Trial attempts exhausted on the exam page.
    if (planType === 'trial' && status !== 'expired'
        && typeof data.remaining_attempts === 'number'
        && data.remaining_attempts <= 0
        && pageHint === 'exam') {
      return 'attempts-exhausted';
    }

    // ── Banner variants (only for active trial subscriptions) ─────────
    if (planType === 'trial' && (status === 'active' || status === 'trial')) {
      // REQ-7.1: 1 attempt remaining.
      if (typeof data.remaining_attempts === 'number'
          && data.remaining_attempts <= ATTEMPTS_LOW_THRESHOLD
          && data.remaining_attempts > 0) {
        return 'attempts-low';
      }

      // REQ-7.2: ≤ 2 days remaining in trial.
      if (typeof data.days_remaining === 'number'
          && data.days_remaining >= 0
          && data.days_remaining <= DAYS_LOW_THRESHOLD) {
        return 'days-low';
      }
    }

    return null;
  }

  /**
   * Best-effort detection of the current page using the URL path. Used
   * to scope full-page prompts (e.g. dashboard vs exam page).
   */
  function _detectPage() {
    try {
      var path = (window.location.pathname || '').toLowerCase();
      if (path.indexOf('/dashboard') !== -1) return 'dashboard';
      if (path.indexOf('/exam') !== -1) return 'exam';
      if (path.indexOf('/subscription') !== -1) return 'subscription';
      // Fallback: use the file name (works for /frontend/html/dashboard.html)
      if (path.indexOf('dashboard') !== -1) return 'dashboard';
      if (path.indexOf('exam') !== -1) return 'exam';
      if (path.indexOf('subscription') !== -1) return 'subscription';
    } catch (e) { /* no-op */ }
    return 'other';
  }

  function _isBannerVariant(variant) {
    return variant === 'attempts-low' || variant === 'days-low';
  }

  function _isFullpageVariant(variant) {
    return variant === 'attempts-exhausted'
        || variant === 'trial-expired'
        || variant === 'subscription-expired';
  }

  // ── Copy builders ───────────────────────────────────────────────────────

  function _bannerCopy(variant, data) {
    if (variant === 'attempts-low') {
      // REQ-7.1 — "1 attempt remaining. Upgrade to Pro for unlimited access"
      var remaining = (typeof data.remaining_attempts === 'number')
        ? data.remaining_attempts : 1;
      return {
        tone: 'warning',
        headline: remaining + ' attempt remaining',
        subtext: 'Upgrade to Pro for unlimited access.',
      };
    }
    if (variant === 'days-low') {
      // REQ-7.2 — "Your trial expires in X days. Upgrade to keep full access"
      var days = (typeof data.days_remaining === 'number')
        ? data.days_remaining : 0;
      var dayWord = (days === 1 ? 'day' : 'days');
      var headline;
      if (days <= 0) {
        headline = 'Your trial expires today';
      } else {
        headline = 'Your trial expires in ' + days + ' ' + dayWord;
      }
      return {
        tone: (days <= 1 ? 'urgent' : 'warning'),
        headline: headline,
        subtext: 'Upgrade to keep full access.',
      };
    }
    return { tone: 'warning', headline: 'Upgrade to Pro', subtext: '' };
  }

  function _fullpageCopy(variant /*, data */) {
    if (variant === 'attempts-exhausted') {
      // REQ-7.3
      return {
        title: "You've used all your Free Trial attempts",
        body: 'Upgrade to Pro for unlimited exam attempts, full analytics,'
            + ' AI-driven recommendations, and leaderboard access.',
        primaryLabel: 'Upgrade to Pro',
        showCompare: true,
      };
    }
    if (variant === 'trial-expired') {
      // REQ-7.4
      return {
        title: 'Your Free Trial has expired',
        body: 'Upgrade to Pro to continue practising with unlimited exams,'
            + ' personalised analytics, and AI recommendations.',
        primaryLabel: 'Upgrade to Pro',
        showCompare: true,
      };
    }
    if (variant === 'subscription-expired') {
      // REQ-7.8
      return {
        title: 'Renew your subscription to continue',
        body: 'Your subscription has expired. Renew now to restore full access'
            + ' to exams, analytics, and the leaderboard.',
        primaryLabel: 'Renew Now',
        showCompare: false,
      };
    }
    return {
      title: 'Upgrade to Pro',
      body: '',
      primaryLabel: 'Upgrade Now',
      showCompare: false,
    };
  }

  // ── Mount helpers ───────────────────────────────────────────────────────

  /**
   * Resolve (or lazily create) the banner element. The banner is inserted
   * immediately after the subscription banner mount/element so it sits
   * directly below the persistent subscription banner.
   */
  function _ensureBannerEl() {
    var existing = document.getElementById(BANNER_ID);
    if (existing) {
      _bannerEl = existing;
      return existing;
    }

    var banner = document.createElement('div');
    banner.id = BANNER_ID;
    banner.className = 'upgrade-prompt-banner';
    banner.setAttribute('role', 'status');
    banner.setAttribute('aria-live', 'polite');
    banner.hidden = true;

    var anchor =
      document.getElementById('subscriptionBanner')
      || document.getElementById('subscription-banner-mount');

    if (anchor && anchor.parentNode) {
      anchor.parentNode.insertBefore(banner, anchor.nextSibling);
    } else {
      var nav = document.querySelector('nav');
      if (nav && nav.parentNode) {
        nav.parentNode.insertBefore(banner, nav.nextSibling);
      } else if (document.body) {
        document.body.insertBefore(banner, document.body.firstChild);
      } else {
        return null;
      }
    }

    _bannerEl = banner;
    return banner;
  }

  function _ensureFullpageEl() {
    var existing = document.getElementById(FULLPAGE_ID);
    if (existing) {
      _fullpageEl = existing;
      return existing;
    }

    var overlay = document.createElement('div');
    overlay.id = FULLPAGE_ID;
    overlay.className = 'upgrade-prompt-fullpage';
    overlay.setAttribute('role', 'dialog');
    overlay.setAttribute('aria-modal', 'true');
    overlay.setAttribute('aria-labelledby', 'upgradePromptTitle');
    overlay.hidden = true;

    if (document.body) {
      document.body.appendChild(overlay);
    } else {
      return null;
    }

    _fullpageEl = overlay;
    return overlay;
  }

  // ── Renderers ───────────────────────────────────────────────────────────

  function _renderBanner(variant, data) {
    var el = _ensureBannerEl();
    if (!el) return;

    var copy = _bannerCopy(variant, data || {});

    el.setAttribute('data-variant', variant);
    el.setAttribute('data-tone', copy.tone);
    el.hidden = false;

    el.innerHTML =
      '<div class="prompt-content">'
      +   '<span class="prompt-icon" aria-hidden="true"></span>'
      +   '<div class="prompt-text">'
      +     '<span class="prompt-headline">' + _escape(copy.headline) + '</span>'
      +     (copy.subtext
              ? '<span class="prompt-subtext">' + _escape(copy.subtext) + '</span>'
              : '')
      +   '</div>'
      + '</div>'
      + '<div class="prompt-actions">'
      +   '<button type="button" class="btn-prompt-compare" '
      +     'data-action="compare">Compare Plans</button>'
      +   '<button type="button" class="btn-prompt-action" '
      +     'data-action="upgrade">Upgrade Now</button>'
      +   '<button type="button" class="btn-prompt-dismiss" '
      +     'aria-label="Dismiss upgrade prompt" '
      +     'data-action="dismiss">×</button>'
      + '</div>';
  }

  function _renderFullpage(variant /*, data */) {
    var el = _ensureFullpageEl();
    if (!el) return;

    var copy = _fullpageCopy(variant);

    var compareHtml = '';
    if (copy.showCompare) {
      compareHtml =
        '<table class="prompt-compare" aria-label="Plan comparison">'
        +   '<thead><tr>'
        +     '<th>Feature</th>'
        +     '<th>Free Trial</th>'
        +     '<th>Pro</th>'
        +   '</tr></thead>'
        +   '<tbody>'
        +     '<tr>'
        +       '<td>Exam attempts</td>'
        +       '<td>5 total</td>'
        +       '<td><span class="compare-yes">Unlimited</span></td>'
        +     '</tr>'
        +     '<tr>'
        +       '<td>Analytics &amp; AI recommendations</td>'
        +       '<td><span class="compare-no">Basic</span></td>'
        +       '<td><span class="compare-yes">Full</span></td>'
        +     '</tr>'
        +     '<tr>'
        +       '<td>Leaderboard access</td>'
        +       '<td><span class="compare-no">No</span></td>'
        +       '<td><span class="compare-yes">Yes</span></td>'
        +     '</tr>'
        +     '<tr>'
        +       '<td>Duration</td>'
        +       '<td>7 days</td>'
        +       '<td>Weekly / Monthly billing</td>'
        +     '</tr>'
        +   '</tbody>'
        + '</table>';
    }

    el.setAttribute('data-variant', variant);

    el.innerHTML =
      '<div class="prompt-card" role="document">'
      +   '<div class="prompt-card-icon" aria-hidden="true"></div>'
      +   '<h2 id="upgradePromptTitle">' + _escape(copy.title) + '</h2>'
      +   '<p>' + _escape(copy.body) + '</p>'
      +   compareHtml
      +   '<div class="prompt-card-actions">'
      +     '<button type="button" class="btn-prompt-secondary" '
      +       'data-action="dismiss">Dismiss</button>'
      +     '<button type="button" class="btn-prompt-primary" '
      +       'data-action="upgrade">' + _escape(copy.primaryLabel) + '</button>'
      +   '</div>'
      + '</div>';

    // Reveal with transition (requires the .open class)
    el.hidden = false;
    // Force reflow so the transition picks up the open class
    /* eslint-disable no-unused-expressions */
    el.offsetHeight;
    /* eslint-enable no-unused-expressions */
    el.classList.add('open');

    // Activate the shared focus trap (Task 18.2, REQ-13.6/13.7).
    // The full-page prompt is a modal dialog (role="dialog"
    // aria-modal="true") so keyboard users must have:
    //   • Tab / Shift+Tab cycling restricted to the prompt's buttons
    //   • Escape key dismissing the prompt (uses dismiss() so the
    //     dismissal is remembered for the session, matching the
    //     behaviour of the in-prompt Dismiss button)
    //   • Focus returned to the element that triggered the prompt
    //     once it closes
    _activateFullpageTrap(el);
  }

  // ── FocusTrap integration (Task 18.2) ───────────────────────────────────

  function _activateFullpageTrap(overlay) {
    if (!overlay) return;
    if (typeof window === 'undefined' || !window.FocusTrap) return;
    // Idempotent — refresh the trap rather than stacking duplicates.
    window.FocusTrap.activate(overlay, {
      onEscape: function () { dismiss(); },
      // Prefer the primary CTA so keyboard users land on the most
      // common action (Upgrade / Renew). Falls back to the first
      // focusable button when the primary isn't present.
      initialFocus: '.btn-prompt-primary',
    });
    _fullpageTrapActive = true;
  }

  function _deactivateFullpageTrap(overlay) {
    if (!overlay) return;
    if (!_fullpageTrapActive) return;
    if (typeof window === 'undefined' || !window.FocusTrap) {
      _fullpageTrapActive = false;
      return;
    }
    try { window.FocusTrap.deactivate(overlay); }
    catch (e) { /* noop — trap may already have been released */ }
    _fullpageTrapActive = false;
  }

  // ── Event handling ──────────────────────────────────────────────────────

  function _handleClick(evt) {
    var target = evt.target;
    var root = evt.currentTarget;
    while (target && target !== root) {
      if (target.dataset && target.dataset.action) {
        var action = target.dataset.action;
        if (action === 'dismiss') {
          evt.preventDefault();
          dismiss();
          return;
        }
        if (action === 'upgrade') {
          evt.preventDefault();
          window.location.href = '/subscription';
          return;
        }
        if (action === 'compare') {
          evt.preventDefault();
          // Hand-off to plan-comparison modal if available (Task 7.2);
          // until then the dedicated comparison modal lives on the
          // subscription page.
          if (typeof window.PlanComparison !== 'undefined'
              && typeof window.PlanComparison.show === 'function') {
            window.PlanComparison.show();
          } else {
            window.location.href = '/subscription';
          }
          return;
        }
      }
      target = target.parentNode;
    }
  }

  function _onSubscriptionStatusChanged(evt) {
    if (evt && evt.detail && evt.detail.subscription) {
      show(evt.detail.subscription);
    }
  }

  function _attachListeners() {
    if (_bannerEl) {
      // Avoid duplicate handlers: remove first then re-add.
      _bannerEl.removeEventListener('click', _handleClick);
      _bannerEl.addEventListener('click', _handleClick);
    }
    if (_fullpageEl) {
      _fullpageEl.removeEventListener('click', _handleClick);
      _fullpageEl.addEventListener('click', _handleClick);
    }
    if (!_statusChangeHandler) {
      _statusChangeHandler = _onSubscriptionStatusChanged;
      window.addEventListener('subscriptionStatusChanged', _statusChangeHandler);
    }
  }

  function _detachListeners() {
    if (_bannerEl) _bannerEl.removeEventListener('click', _handleClick);
    if (_fullpageEl) _fullpageEl.removeEventListener('click', _handleClick);
    if (_statusChangeHandler) {
      window.removeEventListener('subscriptionStatusChanged', _statusChangeHandler);
      _statusChangeHandler = null;
    }
  }

  // ── Public API ──────────────────────────────────────────────────────────

  /**
   * Returns whether a prompt should be shown for the given subscription
   * payload. Honours per-variant dismissal state stored in sessionStorage
   * (REQ-7.5). Pure — does not mutate the DOM.
   */
  function shouldShow(subscriptionData, options) {
    var variant = _classify(subscriptionData, options);
    if (!variant) return false;
    if (_isDismissed(variant)) return false;
    return true;
  }

  /**
   * Show the appropriate upgrade prompt for the given subscription data.
   * Picks between the banner and full-page variants automatically.
   * No-op if the user is on a Pro / institution plan, the data does not
   * meet any threshold, or the user has already dismissed the prompt
   * during the current session.
   */
  function show(subscriptionData, options) {
    var variant = _classify(subscriptionData, options);

    // Nothing to render — make sure any stale prompt is hidden.
    if (!variant) {
      hide();
      return null;
    }

    // Dismissed for this session — keep prompts hidden.
    if (_isDismissed(variant)) {
      hide();
      return null;
    }

    _currentVariant = variant;

    if (_isBannerVariant(variant)) {
      // Hide any stale full-page prompt before switching to a banner.
      var fp = document.getElementById(FULLPAGE_ID);
      if (fp) {
        // Release the trap before hiding so focus is restored
        // (Task 18.2, REQ-13.7).
        _deactivateFullpageTrap(fp);
        fp.classList.remove('open');
        fp.hidden = true;
      }
      _renderBanner(variant, subscriptionData || {});
    } else if (_isFullpageVariant(variant)) {
      // Hide any stale banner before switching to the full-page prompt.
      var bn = document.getElementById(BANNER_ID);
      if (bn) bn.hidden = true;
      _renderFullpage(variant, subscriptionData || {});
    }

    _attachListeners();
    return variant;
  }

  /**
   * Hide both the banner and full-page prompts without persisting a
   * dismissal record. Used when the underlying subscription data no
   * longer warrants a prompt (e.g. user upgraded to Pro mid-session).
   */
  function hide() {
    var bn = document.getElementById(BANNER_ID);
    if (bn) {
      bn.hidden = true;
      bn.removeAttribute('data-variant');
      bn.removeAttribute('data-tone');
    }
    var fp = document.getElementById(FULLPAGE_ID);
    if (fp) {
      // Release the focus trap before hiding so focus is restored to
      // the previously-focused element (Task 18.2, REQ-13.7).
      _deactivateFullpageTrap(fp);
      fp.classList.remove('open');
      fp.hidden = true;
      fp.removeAttribute('data-variant');
    }
    _currentVariant = null;
  }

  /**
   * Dismiss the currently-displayed prompt and remember the choice for
   * the rest of the session (REQ-7.5). The prompt will reappear on the
   * next login because sessionStorage is per-tab/per-session.
   */
  function dismiss() {
    if (_currentVariant) {
      _setDismissed(_currentVariant);
    }
    hide();
  }

  /**
   * Tear down DOM nodes and remove listeners. Safe to call multiple times.
   */
  function destroy() {
    _detachListeners();
    var bn = document.getElementById(BANNER_ID);
    if (bn && bn.parentNode) bn.parentNode.removeChild(bn);
    var fp = document.getElementById(FULLPAGE_ID);
    if (fp) {
      // Release the trap before tearing down the DOM node so the
      // shared FocusTrap stack stays in a clean state.
      _deactivateFullpageTrap(fp);
      if (fp.parentNode) fp.parentNode.removeChild(fp);
    }
    _bannerEl = null;
    _fullpageEl = null;
    _currentVariant = null;
  }

  // ── Auto-init ───────────────────────────────────────────────────────────
  // If the Subscription module is available, auto-fetch the current status
  // once the DOM is ready and render the appropriate prompt. Pages that
  // prefer manual control can call UpgradePrompt.show() with their own
  // payload instead.

  function _autoInit() {
    if (typeof Subscription === 'undefined' || !Subscription.getStatus) return;

    Promise.resolve(Subscription.getStatus())
      .then(function (data) {
        if (data) show(data);
      })
      .catch(function () { /* silent — no prompt on errors */ });
  }

  if (typeof document !== 'undefined') {
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', _autoInit);
    } else {
      _autoInit();
    }
  }

  // ── Expose ──────────────────────────────────────────────────────────────

  return {
    show: show,
    hide: hide,
    dismiss: dismiss,
    shouldShow: shouldShow,
    destroy: destroy,
  };
})();

// Expose globally for other scripts and tests.
if (typeof window !== 'undefined') {
  window.UpgradePrompt = UpgradePrompt;
}

// CommonJS export for unit tests (node / jest).
if (typeof module !== 'undefined' && module.exports) {
  module.exports = UpgradePrompt;
}
