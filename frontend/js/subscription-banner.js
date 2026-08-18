// Mr.E — Subscription Banner Component
// Persistent status banner shown on every authenticated student page.
// Renders status, remaining attempts, renewal info, and quick actions.
// Pairs with `subscription.css` (banner styles) and `subscription.js`
// (Subscription module + status-change events).
//
// Public API mirrors the design doc:
//   SubscriptionBanner.init()
//   SubscriptionBanner.update(subscriptionData)
//   SubscriptionBanner.show()
//   SubscriptionBanner.hide()
//   SubscriptionBanner.toggleCollapse()
//   SubscriptionBanner.destroy()
//
// Requirements: 4.1, 4.3, 4.4, 4.5, 4.6, 4.7, 4.8, 4.11

var SubscriptionBanner = (function () {
  'use strict';

  // ── Constants ───────────────────────────────────────────────────────────

  var BANNER_ID = 'subscriptionBanner';
  var MOUNT_ID = 'subscription-banner-mount';
  var DETAILS_ID = 'subscriptionBannerDetails';
  var COLLAPSE_KEY = 'smartkcet_banner_collapsed';

  // Status → banner copy/icon helpers (REQ-4.3 … 4.7)
  var STATUS_LABELS = {
    trial:          'Trial Subscription Active',
    active:         'Pro Subscription Active',
    institution:    'Institution Access Active',
    overdue:        'Payment Overdue',
    grace_period:   'Payment Overdue',
    expiring_soon:  'Subscription Expiring Soon',
    expired:        'Subscription Expired',
    cancelled:      'Subscription Cancelled',
  };

  // ── Internal state ──────────────────────────────────────────────────────

  var _bannerEl = null;            // root .subscription-banner element
  var _initialized = false;        // guards against double init
  var _currentData = null;         // last subscription payload rendered
  var _expanded = false;           // mobile "Details" expansion state (REQ-13.3)
  var _statusChangeHandler = null; // window listener for cross-module updates
  var _docClickHandler = null;     // delegated click handler on banner

  // ── Helpers ─────────────────────────────────────────────────────────────

  function _getCollapsed() {
    try {
      var raw = sessionStorage.getItem(COLLAPSE_KEY);
      if (!raw) return false;
      var parsed = JSON.parse(raw);
      return !!(parsed && parsed.collapsed);
    } catch (e) {
      return false;
    }
  }

  function _setCollapsed(collapsed) {
    try {
      sessionStorage.setItem(
        COLLAPSE_KEY,
        JSON.stringify({ collapsed: !!collapsed })
      );
    } catch (e) {
      /* sessionStorage may be unavailable — ignore */
    }
  }

  function _escape(str) {
    if (str === null || str === undefined) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  function _formatDate(value) {
    if (!value) return '';
    try {
      var d = new Date(value);
      if (isNaN(d.getTime())) return '';
      return d.toLocaleDateString('en-IN', {
        day: 'numeric',
        month: 'short',
        year: 'numeric',
      });
    } catch (e) {
      return '';
    }
  }

  /**
   * Resolve the banner status code used as the `data-status` attribute.
   * Maps a subscription payload onto one of the canonical CSS states:
   *   trial | active | institution | overdue | grace_period |
   *   expiring_soon | expired | cancelled
   *
   * Implements REQ-4.8 (more permissive subscription wins for dual access).
   */
  function _resolveStatus(data) {
    if (!data) return null;

    var status = data.status || '';
    var planType = data.plan_type || '';

    // Terminal states take precedence over plan_type
    if (status === 'expired') return 'expired';
    if (status === 'cancelled') return 'cancelled';
    if (status === 'overdue') return 'overdue';
    if (status === 'grace_period') return 'grace_period';

    // Active / trial — disambiguate using plan_type, is_trial flag, and
    // plan_name so that purchased trial plans (plan_type='individual',
    // status='active', is_trial=true) are correctly classified as 'trial'.
    // REQ-4.8: more permissive subscription wins for dual access.
    //   Pro (active+unlimited) > Institution-active > Trial
    if (status === 'active' || status === 'trial') {
      // Explicit "expiring soon" hint from backend
      if (data.is_expiring_soon === true) return 'expiring_soon';

      if (planType === 'institution') return 'institution';

      // Detect trial by: explicit flag, plan_type, raw status, or plan_name.
      var isTrial =
        data.is_trial === true ||
        planType === 'trial' ||
        status === 'trial' ||
        (data.plan_name && data.plan_name.toLowerCase().indexOf('trial') !== -1);

      if (isTrial) return 'trial';

      // Remaining active paid plans (Pro Monthly, Pro Yearly, etc.)
      return 'active';
    }

    // Unknown / future states — treat as inactive so we still render.
    return status || null;
  }

  /**
   * Build the textual details line ("3 of 5 attempts remaining • 5 days left", etc.)
   * Returns an HTML string already escaped.
   */
  function _buildDetails(statusCode, data) {
    if (!data) return '';
    var parts = [];

    switch (statusCode) {
      case 'trial': {
        // REQ-4.3 — trial shows attempts + days remaining
        if (typeof data.remaining_attempts === 'number'
            && typeof data.total_attempts === 'number') {
          parts.push(
            _escape(data.remaining_attempts) + ' of '
            + _escape(data.total_attempts) + ' attempts remaining'
          );
        } else if (typeof data.remaining_attempts === 'number') {
          parts.push(_escape(data.remaining_attempts) + ' attempts remaining');
        }
        if (typeof data.days_remaining === 'number' && data.days_remaining >= 0) {
          parts.push(_escape(data.days_remaining) + ' day'
            + (data.days_remaining === 1 ? '' : 's') + ' left');
        }
        break;
      }
      case 'active': {
        // REQ-4.4 — Pro shows billing period + next renewal date
        if (data.billing_period) {
          var bp = String(data.billing_period);
          parts.push(_escape(bp.charAt(0).toUpperCase() + bp.slice(1)) + ' billing');
        }
        var renewal = _formatDate(data.next_renewal_date);
        if (renewal) parts.push('Renews ' + _escape(renewal));
        break;
      }
      case 'institution': {
        // REQ-4.7 — institution name + weekly/monthly remaining
        if (data.institution_name) {
          parts.push(_escape(data.institution_name));
        }
        var quotaBits = [];
        if (typeof data.weekly_tests_remaining === 'number') {
          quotaBits.push('Weekly: ' + _escape(data.weekly_tests_remaining));
        }
        if (typeof data.monthly_tests_remaining === 'number') {
          quotaBits.push('Monthly: ' + _escape(data.monthly_tests_remaining));
        }
        if (quotaBits.length) parts.push(quotaBits.join(' • ') + ' remaining');
        break;
      }
      case 'overdue':
      case 'grace_period': {
        // REQ-4.5 — overdue shows days remaining in grace period
        if (typeof data.days_remaining === 'number' && data.days_remaining >= 0) {
          parts.push(_escape(data.days_remaining) + ' day'
            + (data.days_remaining === 1 ? '' : 's')
            + ' left to pay');
        }
        break;
      }
      case 'expiring_soon': {
        if (typeof data.days_remaining === 'number' && data.days_remaining >= 0) {
          parts.push('Expires in ' + _escape(data.days_remaining) + ' day'
            + (data.days_remaining === 1 ? '' : 's'));
        }
        var nrd = _formatDate(data.next_renewal_date || data.end_date);
        if (nrd) parts.push('Renew by ' + _escape(nrd));
        break;
      }
      case 'expired':
      case 'cancelled': {
        // REQ-4.6 — expired prompts upgrade
        var ended = _formatDate(data.end_date);
        if (ended) parts.push('Ended ' + _escape(ended));
        break;
      }
      default: {
        if (data.plan_name) parts.push(_escape(data.plan_name));
      }
    }

    return parts.join(' • ');
  }

  /**
   * Resolve which CTA (if any) should be rendered on the right side.
   * Returns { label, href } or null when no action button is needed.
   */
  function _buildAction(statusCode) {
    switch (statusCode) {
      case 'overdue':
      case 'grace_period':
        return { label: 'Pay Now', href: '/subscription' };       // REQ-4.5
      case 'expired':
      case 'cancelled':
        return { label: 'Upgrade Now', href: '/subscription' };   // REQ-4.6
      case 'expiring_soon':
        return { label: 'Renew Now', href: '/subscription' };
      case 'trial':
        return { label: 'Upgrade Now', href: '/subscription' };
      default:
        return null;
    }
  }

  /**
   * Pick a sensible status label driven by the actual plan the user holds.
   *
   * Priority order:
   *  1. Terminal / warning states (overdue, expired, etc.) always use their
   *     fixed label — plan name is irrelevant when the subscription has lapsed.
   *  2. Active / trial states: use plan_name from the API when available,
   *     with " Active" appended, so a "7-Day Premium Trial" user sees
   *     "7-Day Premium Trial Active" rather than the generic
   *     "Pro Subscription Active".  If plan_name is absent, fall back to
   *     the STATUS_LABELS table.
   *
   * REQ-4.3 (trial copy), REQ-4.4 (pro copy).
   */
  function _buildStatusLabel(statusCode, data) {
    // Debug log to help verify the data being used for banner text
    console.log('[subscription-banner] subscription:', data);

    // Terminal / warning states always use their fixed label.
    var terminalStates = {
      overdue:       true,
      grace_period:  true,
      expiring_soon: true,
      expired:       true,
      cancelled:     true,
    };
    if (terminalStates[statusCode]) {
      return STATUS_LABELS[statusCode] || statusCode;
    }

    // For active-style states use plan_name when the backend provides it.
    // Append " Active" so it reads naturally ("7-Day Premium Trial Active").
    if (data && data.plan_name) {
      // Avoid double-appending " Active" if the name already ends with it.
      var name = data.plan_name;
      if (name.toLowerCase().indexOf('active') === -1) {
        return name + ' Active';
      }
      return name;
    }

    // Fall back to the STATUS_LABELS table (keeps existing behaviour for
    // cases where plan_name is not returned).
    if (STATUS_LABELS[statusCode]) return STATUS_LABELS[statusCode];
    return 'Subscription';
  }

  // ── Mount / render ──────────────────────────────────────────────────────

  /**
   * Locate (or lazily create) the banner element.
   * - If a `<div id="subscription-banner-mount">` exists, render inside it.
   * - Otherwise, insert the banner immediately after the page's <nav>
   *   (or as the first child of <body> if no nav exists).
   */
  function _ensureBannerEl() {
    // Already rendered — return it.
    var existing = document.getElementById(BANNER_ID);
    if (existing) {
      _bannerEl = existing;
      return existing;
    }

    var banner = document.createElement('div');
    banner.id = BANNER_ID;
    banner.className = 'subscription-banner';
    banner.setAttribute('role', 'status');
    banner.setAttribute('aria-live', 'polite');
    banner.hidden = true; // shown after first update

    var mount = document.getElementById(MOUNT_ID);
    if (mount) {
      mount.appendChild(banner);
    } else {
      // Insert directly after the first <nav> in the document, falling
      // back to prepending to <body> when no nav exists.
      var nav = document.querySelector('nav');
      if (nav && nav.parentNode) {
        nav.parentNode.insertBefore(banner, nav.nextSibling);
      } else if (document.body) {
        document.body.insertBefore(banner, document.body.firstChild);
      } else {
        // Nothing to mount onto yet — bail out; init will retry on DOM ready.
        return null;
      }
    }

    _bannerEl = banner;
    return banner;
  }

  /**
   * Render banner inner HTML based on subscription data.
   * Pure function over the DOM — call sites are responsible for
   * deciding when re-rendering is necessary.
   */
  function _render(data) {
    if (!_bannerEl) return;

    var statusCode = _resolveStatus(data);

    if (!statusCode) {
      // No active subscription — hide banner entirely.
      _bannerEl.hidden = true;
      _bannerEl.removeAttribute('data-status');
      _bannerEl.innerHTML = '';
      return;
    }

    _bannerEl.setAttribute('data-status', statusCode);
    _bannerEl.hidden = false;

    var label = _buildStatusLabel(statusCode, data);
    var details = _buildDetails(statusCode, data);
    var action = _buildAction(statusCode);

    var actionHtml = '';
    if (action) {
      actionHtml =
        '<button type="button" class="btn-banner-action" '
        + 'data-action="navigate" data-href="' + _escape(action.href) + '">'
        + _escape(action.label)
        + '</button>';
    }

    // Mobile-only "Details" toggle (REQ-13.3) — visibility is controlled by
    // CSS media query (visible only at < 768px). Only render the button when
    // there are extra details worth expanding; otherwise the toggle would be
    // meaningless. Wire up aria-expanded + aria-controls so screen readers
    // can announce the disclosure relationship.
    var hasDetails = !!details;
    var detailsToggleHtml = '';
    if (hasDetails) {
      detailsToggleHtml =
        '<button type="button" class="banner-details-toggle" '
        + 'data-action="toggle-details" '
        + 'aria-expanded="' + (_expanded ? 'true' : 'false') + '" '
        + 'aria-controls="' + DETAILS_ID + '" '
        + 'aria-label="' + (_expanded
            ? 'Hide subscription details'
            : 'Show subscription details') + '">'
        + (_expanded ? 'Hide' : 'Details')
        + '</button>';
    }

    var collapseHtml =
      '<button type="button" class="btn-collapse" '
      + 'aria-label="Collapse subscription banner" '
      + 'data-action="toggle-collapse">−</button>';

    _bannerEl.innerHTML =
      '<div class="banner-content">'
      +   '<div class="banner-icon" aria-hidden="true"></div>'
      +   '<div class="banner-text">'
      +     '<span class="banner-status">' + _escape(label) + '</span>'
      +     (details
              ? '<span class="banner-details" id="' + DETAILS_ID + '">'
                + details + '</span>'
              : '')
      +   '</div>'
      + '</div>'
      + '<div class="banner-actions">'
      +   detailsToggleHtml
      +   actionHtml
      +   collapseHtml
      + '</div>';

    // Restore collapsed state from sessionStorage (REQ-4.11)
    if (_getCollapsed()) {
      _bannerEl.classList.add('collapsed');
    } else {
      _bannerEl.classList.remove('collapsed');
    }

    // Preserve "Details" expanded state across re-renders (REQ-13.3).
    // When details disappear (e.g. status changes to one without extras),
    // reset the flag so the button doesn't return to a stuck "expanded" state.
    if (!hasDetails) {
      _expanded = false;
    }
    _bannerEl.classList.toggle('expanded', _expanded && hasDetails);
  }

  // ── Event handling ──────────────────────────────────────────────────────

  function _onBannerClick(evt) {
    var target = evt.target;
    while (target && target !== _bannerEl) {
      if (target.dataset && target.dataset.action) {
        var action = target.dataset.action;
        if (action === 'toggle-collapse') {
          evt.preventDefault();
          toggleCollapse();
          return;
        }
        if (action === 'toggle-details') {
          evt.preventDefault();
          _toggleDetails(target);
          return;
        }
        if (action === 'navigate') {
          evt.preventDefault();
          var href = target.dataset.href || '/subscription';
          window.location.href = href;
          return;
        }
      }
      target = target.parentNode;
    }
  }

  /**
   * Toggle the mobile "Details" disclosure (REQ-13.3).
   * Updates the .expanded class on the banner, the button's text/aria
   * attributes, and the persisted in-memory flag so the state survives
   * subsequent re-renders.
   */
  function _toggleDetails(btn) {
    if (!_bannerEl) return;
    _expanded = !_expanded;
    _bannerEl.classList.toggle('expanded', _expanded);
    if (btn) {
      btn.setAttribute('aria-expanded', _expanded ? 'true' : 'false');
      btn.setAttribute(
        'aria-label',
        _expanded ? 'Hide subscription details' : 'Show subscription details'
      );
      btn.textContent = _expanded ? 'Hide' : 'Details';
    }
  }

  function _onSubscriptionStatusChanged(evt) {
    if (evt && evt.detail && evt.detail.subscription) {
      update(evt.detail.subscription);
    }
  }

  function _attachListeners() {
    if (_bannerEl && !_docClickHandler) {
      _docClickHandler = _onBannerClick;
      _bannerEl.addEventListener('click', _docClickHandler);
    }
    if (!_statusChangeHandler) {
      _statusChangeHandler = _onSubscriptionStatusChanged;
      window.addEventListener('subscriptionStatusChanged', _statusChangeHandler);
    }
  }

  function _detachListeners() {
    if (_bannerEl && _docClickHandler) {
      _bannerEl.removeEventListener('click', _docClickHandler);
      _docClickHandler = null;
    }
    if (_statusChangeHandler) {
      window.removeEventListener('subscriptionStatusChanged', _statusChangeHandler);
      _statusChangeHandler = null;
    }
  }

  // ── Public API ──────────────────────────────────────────────────────────

  /**
   * Initialize the banner: mount the DOM, hook listeners, and render the
   * current subscription state. Safe to call multiple times.
   *
   * REQ-4.1: render on every authenticated student page.
   * REQ-4.11: restore collapsed state from sessionStorage.
   */
  async function init() {
    // Defer until DOM is ready so we can locate <nav> / mount node.
    if (document.readyState === 'loading') {
      return new Promise(function (resolve) {
        document.addEventListener('DOMContentLoaded', function () {
          init().then(resolve).catch(resolve);
        });
      });
    }

    var el = _ensureBannerEl();
    if (!el) return;

    _attachListeners();
    _initialized = true;

    // Fetch latest subscription state (uses cache when fresh).
    if (typeof Subscription !== 'undefined' && Subscription.getStatus) {
      try {
        var data = await Subscription.getStatus();
        update(data);
      } catch (e) {
        // Network/auth errors are non-fatal — leave the banner hidden.
        console.error('SubscriptionBanner: failed to load status', e);
      }
    }
  }

  /**
   * Update banner with new subscription data and re-render.
   * Pass `null`/`undefined` to clear the banner (no active subscription).
   */
  function update(subscriptionData) {
    _ensureBannerEl();
    if (!_bannerEl) return;
    _currentData = subscriptionData || null;
    _render(_currentData);
  }

  function show() {
    if (!_bannerEl) return;
    _bannerEl.hidden = false;
  }

  function hide() {
    if (!_bannerEl) return;
    _bannerEl.hidden = true;
  }

  /**
   * Toggle collapsed state and persist to sessionStorage (REQ-4.11).
   */
  function toggleCollapse() {
    if (!_bannerEl) return;
    var willCollapse = !_bannerEl.classList.contains('collapsed');
    _bannerEl.classList.toggle('collapsed', willCollapse);
    _setCollapsed(willCollapse);

    // Update collapse button affordance for screen readers.
    var btn = _bannerEl.querySelector('.btn-collapse');
    if (btn) {
      btn.textContent = willCollapse ? '+' : '−';
      btn.setAttribute(
        'aria-label',
        willCollapse ? 'Expand subscription banner' : 'Collapse subscription banner'
      );
    }
  }

  /**
   * Cleanup: remove listeners and detach the DOM node.
   * Safe to call multiple times.
   */
  function destroy() {
    _detachListeners();
    if (_bannerEl && _bannerEl.parentNode) {
      _bannerEl.parentNode.removeChild(_bannerEl);
    }
    _bannerEl = null;
    _currentData = null;
    _expanded = false;
    _initialized = false;
  }

  // ── Auto-mount ──────────────────────────────────────────────────────────
  // If a `subscription-banner-mount` placeholder exists on the page (e.g.
  // subscription.html), auto-initialize so individual pages don't have to
  // wire things up manually. Pages without the placeholder can still call
  // SubscriptionBanner.init() explicitly.

  function _autoMount() {
    if (_initialized) return;
    if (document.getElementById(MOUNT_ID)) {
      init();
    }
  }

  if (typeof document !== 'undefined') {
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', _autoMount);
    } else {
      _autoMount();
    }
  }

  // ── Expose public interface ─────────────────────────────────────────────

  return {
    init: init,
    update: update,
    show: show,
    hide: hide,
    toggleCollapse: toggleCollapse,
    destroy: destroy,
  };
})();
