// SmartKCET Prep — Plan Comparison Modal (Task 7.2)
// -----------------------------------------------------------------------------
// Renders a "Compare Plans" modal that shows a detailed Free Trial vs Pro
// feature comparison table side-by-side. The modal is invoked from the
// upgrade-prompt banner / full-page CTA via `window.PlanComparison.show()`
// and from the dedicated subscription page's "Compare Plans" button.
//
// Design goals:
//   * Reuse the existing `#comparePlansModal` markup on the subscription
//     page when it is present (no duplicate DOM, no styling drift).
//   * Inject a self-contained modal with the same id/classes when invoked
//     from any other page (dashboard, exam) so the upgrade prompt's
//     "Compare Plans" CTA works everywhere.
//   * Re-use the existing `.modal-overlay`, `.modal-dialog`, `.compare-dialog`
//     and `.comparison-table` styles defined in `subscription.css`.
//   * Be idempotent — multiple show() calls do not stack overlays or
//     duplicate listeners; hide() always restores the previous state.
//   * Delegate to subscription-page.js global helpers when present, so we
//     don't double-trap focus or fight existing handlers on /subscription.
//   * Use the shared FocusTrap utility (Task 18.2) for accessibility:
//     focus is moved inside the dialog on open, Tab/Shift+Tab cycle within,
//     Escape closes, and focus is returned to the trigger on close.
//
// Public API:
//   window.PlanComparison.show()
//   window.PlanComparison.hide()
//   window.PlanComparison.isOpen()
//
// Requirements: 7.9

var PlanComparison = (function () {
  'use strict';

  // ── Constants ───────────────────────────────────────────────────────────

  var MODAL_ID = 'comparePlansModal';
  var TITLE_ID = 'compareModalTitle';

  // Internal state
  var _listenersAttached = false; // overlay / close-button listeners
  var _trapActive = false;        // is the FocusTrap currently active?

  // ── Markup builder ──────────────────────────────────────────────────────

  /**
   * Build the modal DOM. Mirrors the markup in subscription.html so the
   * injected version inherits the same `.compare-dialog` styling.
   */
  function _buildMarkup() {
    var overlay = document.createElement('div');
    overlay.id = MODAL_ID;
    overlay.className = 'modal-overlay';
    overlay.style.display = 'none';
    overlay.setAttribute('role', 'dialog');
    overlay.setAttribute('aria-modal', 'true');
    overlay.setAttribute('aria-labelledby', TITLE_ID);
    overlay.setAttribute('aria-hidden', 'true');

    overlay.innerHTML =
      '<div class="modal-dialog compare-dialog">'
      +   '<div class="modal-header">'
      +     '<h2 id="' + TITLE_ID + '">Compare Plans</h2>'
      +     '<button type="button" class="modal-close" '
      +       'aria-label="Close compare plans dialog" '
      +       'data-action="close">&times;</button>'
      +   '</div>'
      +   '<div class="modal-body">'
      +     '<div class="comparison-table">'
      +       '<table aria-describedby="' + TITLE_ID + '">'
      +         '<thead>'
      +           '<tr>'
      +             '<th scope="col">Feature</th>'
      +             '<th scope="col">Free Trial</th>'
      +             '<th scope="col">Pro</th>'
      +           '</tr>'
      +         '</thead>'
      +         '<tbody>'
      +           '<tr>'
      +             '<td>Exam Attempts</td>'
      +             '<td>5 total</td>'
      +             '<td>Unlimited</td>'
      +           '</tr>'
      +           '<tr>'
      +             '<td>Duration</td>'
      +             '<td>7 days</td>'
      +             '<td>Weekly or Monthly</td>'
      +           '</tr>'
      +           '<tr>'
      +             '<td>Score Display</td>'
      +             '<td>\u2713 Basic</td>'
      +             '<td>\u2713 Detailed</td>'
      +           '</tr>'
      +           '<tr>'
      +             '<td>Performance Analytics</td>'
      +             '<td>\u2717</td>'
      +             '<td>\u2713 Full Analytics</td>'
      +           '</tr>'
      +           '<tr>'
      +             '<td>AI Recommendations</td>'
      +             '<td>\u2717</td>'
      +             '<td>\u2713 Personalized</td>'
      +           '</tr>'
      +           '<tr>'
      +             '<td>Leaderboard</td>'
      +             '<td>\u2717</td>'
      +             '<td>\u2713 Access &amp; Rankings</td>'
      +           '</tr>'
      +           '<tr>'
      +             '<td>Topic-wise Analysis</td>'
      +             '<td>\u2717</td>'
      +             '<td>\u2713 Detailed Breakdown</td>'
      +           '</tr>'
      +           '<tr>'
      +             '<td>Priority Support</td>'
      +             '<td>Community</td>'
      +             '<td>\u2713 Email Support</td>'
      +           '</tr>'
      +           '<tr>'
      +             '<td>Price</td>'
      +             '<td>Free</td>'
      +             '<td>\u20B999/week or \u20B9349/month</td>'
      +           '</tr>'
      +         '</tbody>'
      +       '</table>'
      +     '</div>'
      +   '</div>'
      + '</div>';

    return overlay;
  }

  /**
   * Resolve the modal element. Returns the existing `#comparePlansModal`
   * when present (e.g. on subscription.html) so we never duplicate DOM.
   * Otherwise injects a fresh copy at the end of <body>.
   */
  function _ensureModal() {
    var existing = document.getElementById(MODAL_ID);
    if (existing) return existing;

    if (!document.body) return null;

    var overlay = _buildMarkup();
    document.body.appendChild(overlay);
    return overlay;
  }

  /**
   * Detect whether the host page (subscription.html) already exposes its
   * own showComparePlansModal / closeComparePlansModal helpers from
   * subscription-page.js. When present we delegate to them so we do not
   * fight that page's own focus-trap and click-outside listeners.
   */
  function _hasPageHelpers() {
    return typeof window !== 'undefined'
      && typeof window.showComparePlansModal === 'function'
      && typeof window.closeComparePlansModal === 'function'
      // Guard against an infinite loop where subscription-page.js itself
      // delegates back to PlanComparison: its impl reads `comparePlansModal`
      // by id so we just check that the element is present too.
      && document.getElementById(MODAL_ID) !== null
      && window.showComparePlansModal !== show;
  }

  // ── Event handling ──────────────────────────────────────────────────────

  function _onOverlayClick(evt) {
    var modal = document.getElementById(MODAL_ID);
    if (!modal) return;
    // Click on the dim layer itself (not on the dialog body) closes it.
    if (evt.target === modal) {
      hide();
    }
  }

  function _onModalClick(evt) {
    var target = evt.target;
    var root = evt.currentTarget;
    while (target && target !== root) {
      if (target.dataset && target.dataset.action === 'close') {
        evt.preventDefault();
        hide();
        return;
      }
      target = target.parentNode;
    }
  }

  function _attachListeners(modal) {
    if (!modal || _listenersAttached) return;
    modal.addEventListener('click', _onOverlayClick);

    var dialog = modal.querySelector('.modal-dialog');
    if (dialog) {
      dialog.addEventListener('click', _onModalClick);
    }
    _listenersAttached = true;
  }

  // ── FocusTrap integration ──────────────────────────────────────────────

  function _activateTrap(modal) {
    if (!modal) return;
    if (typeof window === 'undefined' || !window.FocusTrap) return;
    window.FocusTrap.activate(modal, {
      onEscape: hide,
      initialFocus: '.modal-close',
    });
    _trapActive = true;
  }

  function _deactivateTrap(modal) {
    if (!modal) return;
    if (typeof window === 'undefined' || !window.FocusTrap) return;
    if (!_trapActive) return;
    window.FocusTrap.deactivate(modal);
    _trapActive = false;
  }

  // ── Public API ──────────────────────────────────────────────────────────

  /**
   * Show the plan comparison modal. Lazily injects the markup the first
   * time it is invoked from a page that does not already include one.
   * Delegates to subscription-page.js's helper when running on the
   * /subscription page so existing focus-trap and click-outside logic
   * stays in control.
   */
  function show() {
    if (_hasPageHelpers()) {
      window.showComparePlansModal();
      return;
    }

    var modal = _ensureModal();
    if (!modal) return;

    _attachListeners(modal);

    modal.style.display = 'flex';
    modal.setAttribute('aria-hidden', 'false');

    _activateTrap(modal);
  }

  /**
   * Hide the plan comparison modal. Idempotent — calling hide() when the
   * modal is already closed is a no-op.
   */
  function hide() {
    if (_hasPageHelpers()) {
      window.closeComparePlansModal();
      return;
    }

    var modal = document.getElementById(MODAL_ID);
    if (!modal) return;

    _deactivateTrap(modal);

    modal.style.display = 'none';
    modal.setAttribute('aria-hidden', 'true');
  }

  /**
   * Reports whether the modal is currently visible.
   */
  function isOpen() {
    var modal = document.getElementById(MODAL_ID);
    if (!modal) return false;
    var display = modal.style.display;
    return display !== '' && display !== 'none';
  }

  // ── Expose ──────────────────────────────────────────────────────────────

  return {
    show: show,
    hide: hide,
    isOpen: isOpen,
  };
})();

// Expose globally so upgrade-prompt.js and other scripts can invoke it.
if (typeof window !== 'undefined') {
  window.PlanComparison = PlanComparison;
}

// CommonJS export for unit tests (node / jest).
if (typeof module !== 'undefined' && module.exports) {
  module.exports = PlanComparison;
}
