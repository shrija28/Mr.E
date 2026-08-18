// Mr.E — Invitation Acceptance Module
// Handles the student-facing invitation acceptance flow on
// /invitation-accept?code={invitation_code}.
//
// Responsibilities:
//   - Read the invitation code from the URL query string
//   - Fetch invitation details via GET /api/institution/invite/{code}
//   - Render institution name, expiry, and benefits in the page
//   - Accept invitation via POST /api/institution/invite/{code}/accept
//   - Map backend errors to user-friendly messages and provide retry/decline
//   - Redirect to /dashboard with a success toast on acceptance
//
// Backend error codes handled (institution-specific slugs from
// InstitutionAPI._extractErrorCode):
//   - invalid_invitation (HTTP 400 on accept; HTTP 400/404 on details)
//   - already_linked     (HTTP 409 on accept)
//   - seats_full         (HTTP 409 on accept)
//
// Authentication (Requirement 11.8):
//   Before rendering invitation details, this module checks the user's
//   session via Auth.currentRole(). If the visitor is not authenticated,
//   they are redirected to /login?return=<current-url> so login.html can
//   send them back to this page (preserving the ?code= query parameter)
//   after a successful sign-in.
//
// Requirements: 11.2, 11.4, 11.5, 11.6, 11.7, 11.8, 11.9, 11.10

var Invitation = (function () {
  'use strict';

  // ── DOM element IDs (must match invitation-accept.html) ──────────────────
  var IDS = {
    error: 'invitationError',
    loading: 'invitationLoading',
    details: 'invitationDetails',
    institutionName: 'institutionName',
    expiry: 'invitationExpiry',
    benefits: 'invitationBenefits',
    acceptBtn: 'acceptBtn',
    declineBtn: 'declineBtn',
    retry: 'invitationRetry',
    retryBtn: 'retryBtn',
  };

  // ── User-facing messages ─────────────────────────────────────────────────
  var MESSAGES = {
    missingCode:
      'No invitation code provided. Please check the link and try again.',
    loadFailed:
      'Unable to load invitation details. Please check the link and try again.',
    invalidOrExpired:
      'This invitation is invalid or has expired. ' +
      'Please contact your institution admin for a new invitation.',
    alreadyLinked:
      'You are already linked to another institution. ' +
      'You must leave your current institution before joining a new one.',
    seatsFull:
      'This institution has reached its maximum student capacity. ' +
      'Please contact your institution admin.',
    sessionExpired: 'Your session has expired. Please log in again.',
    genericAcceptError:
      'Unable to accept the invitation. Please try again.',
  };

  // Default benefits shown when the backend response does not provide any.
  // Mirrors the static fallback list in invitation-accept.html.
  var DEFAULT_BENEFITS = [
    "Access to your institution's curated exams",
    'Personalized analytics and progress tracking',
    "Coverage under your institution's subscription",
  ];

  // The code parsed from the page URL — captured at init() time.
  var _code = null;

  // Tracks an in-flight accept request so we don't fire duplicates.
  var _accepting = false;

  // ── DOM helpers ──────────────────────────────────────────────────────────

  function _$(id) {
    return document.getElementById(id);
  }

  function _show(id) {
    var el = _$(id);
    if (el) el.style.display = '';
  }

  function _hide(id) {
    var el = _$(id);
    if (el) el.style.display = 'none';
  }

  function _setText(id, text) {
    var el = _$(id);
    if (el) el.textContent = text == null ? '' : String(text);
  }

  function _showError(message) {
    var el = _$(IDS.error);
    if (!el) return;
    el.textContent = message || '';
    el.style.display = message ? '' : 'none';
  }

  function _clearError() {
    _showError('');
  }

  function _setAcceptBusy(isBusy) {
    var btn = _$(IDS.acceptBtn);
    if (!btn) return;
    btn.disabled = !!isBusy;
    btn.textContent = isBusy ? 'Accepting…' : 'Accept Invitation';
    btn.setAttribute('aria-busy', isBusy ? 'true' : 'false');
  }

  // ── URL helpers ──────────────────────────────────────────────────────────

  /**
   * Extract the `code` query parameter from the current URL.
   * Returns null if absent or empty.
   */
  function _getCodeFromUrl() {
    try {
      var params = new URLSearchParams(window.location.search);
      var code = params.get('code');
      if (!code) return null;
      code = code.trim();
      return code.length > 0 ? code : null;
    } catch (e) {
      return null;
    }
  }

  /**
   * Build the current URL (path + query string) used as the `return`
   * query parameter when redirecting an unauthenticated visitor to the
   * login page. Preserves the `?code=…` parameter so the login flow
   * can bounce the student back to the same invitation page.
   */
  function _currentReturnUrl() {
    var path = (window.location && window.location.pathname) || '/';
    var search = (window.location && window.location.search) || '';
    return path + search;
  }

  /**
   * Check whether the current visitor has an authenticated session.
   * Returns the user info on success, or null when unauthenticated /
   * when Auth is unavailable. Network errors are treated as
   * "unauthenticated" so the user is funneled through login rather
   * than seeing a stuck spinner on the invitation page.
   *
   * Requirement: 11.8
   */
  async function _checkAuth() {
    if (typeof Auth === 'undefined' || !Auth || typeof Auth.currentRole !== 'function') {
      return null;
    }
    try {
      return await Auth.currentRole();
    } catch (e) {
      return null;
    }
  }

  /**
   * Redirect the visitor to /login with a `return` query parameter
   * pointing back to the current invitation URL (including the
   * `?code=…` parameter). login.html honors the `return` parameter on
   * successful sign-in and bounces the student back here.
   *
   * Requirement: 11.8
   */
  function _redirectToLogin() {
    var ret = encodeURIComponent(_currentReturnUrl());
    window.location.href = '/login?return=' + ret;
  }

  // ── Formatting ───────────────────────────────────────────────────────────

  /**
   * Format an ISO 8601 datetime to a readable local string.
   * Falls back to the raw value when parsing fails.
   */
  function _formatExpiry(iso) {
    if (!iso) return '—';
    try {
      var d = new Date(iso);
      if (isNaN(d.getTime())) return String(iso);
      // Example: "Jan 15, 2025, 3:45 PM"
      return d.toLocaleString(undefined, {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: 'numeric',
        minute: '2-digit',
      });
    } catch (e) {
      return String(iso);
    }
  }

  /**
   * Render the invitation details into the DOM.
   * Falls back to placeholders when fields are missing.
   */
  function _renderDetails(details) {
    if (!details) details = {};

    var institutionName =
      details.institution_name ||
      details.institutionName ||
      'Your Institution';
    _setText(IDS.institutionName, institutionName);

    var expiresAt =
      details.expires_at || details.expiresAt || details.expiry || null;
    _setText(IDS.expiry, _formatExpiry(expiresAt));

    var benefits =
      Array.isArray(details.benefits) && details.benefits.length > 0
        ? details.benefits
        : DEFAULT_BENEFITS;

    var ul = _$(IDS.benefits);
    if (ul) {
      // Clear existing list items, then repopulate.
      while (ul.firstChild) ul.removeChild(ul.firstChild);
      for (var i = 0; i < benefits.length; i++) {
        var li = document.createElement('li');
        li.textContent = String(benefits[i]);
        ul.appendChild(li);
      }
    }
  }

  // ── Error mapping ────────────────────────────────────────────────────────

  /**
   * Map a failed accept-invitation response to a user-facing message.
   * Uses the institution-specific error slug when present, falling back to
   * status-code-based messages from InstitutionAPI.
   * Requirements: 11.5, 11.6, 11.7
   */
  function _mapAcceptError(result) {
    if (!result) return MESSAGES.genericAcceptError;

    var code = result.errorCode;
    if (code === 'invalid_invitation') return MESSAGES.invalidOrExpired;
    if (code === 'already_linked') return MESSAGES.alreadyLinked;
    if (code === 'seats_full') return MESSAGES.seatsFull;

    // Fall back to status-code mapping when the slug is missing.
    if (result.status === 400) return MESSAGES.invalidOrExpired;
    if (result.status === 409) {
      // Generic 409 — prefer the backend's message if available.
      return result.error || MESSAGES.alreadyLinked;
    }

    return result.error || MESSAGES.genericAcceptError;
  }

  // ── Public API ───────────────────────────────────────────────────────────

  /**
   * Fetch invitation details for the given code and render them.
   * Shows the loading indicator while the request is in flight.
   * On error, shows the error message and a Retry button.
   *
   * Requirements: 11.2, 11.10
   */
  async function getDetails(code) {
    code = code || _code;
    if (!code) {
      _hide(IDS.loading);
      _hide(IDS.details);
      _show(IDS.retry);
      _showError(MESSAGES.missingCode);
      return { ok: false, status: 0, error: MESSAGES.missingCode };
    }

    if (typeof InstitutionAPI === 'undefined') {
      _hide(IDS.loading);
      _show(IDS.retry);
      _showError(MESSAGES.loadFailed);
      return { ok: false, status: 0, error: MESSAGES.loadFailed };
    }

    _clearError();
    _show(IDS.loading);
    _hide(IDS.details);
    _hide(IDS.retry);

    var result = await InstitutionAPI.getInvitationDetails(code);

    _hide(IDS.loading);

    if (result && result.ok) {
      _renderDetails(result.data || {});
      _show(IDS.details);
      return result;
    }

    // Failure path — show retry option and a contextual message.
    var message;
    if (result && result.status === 401) {
      message = MESSAGES.sessionExpired;
    } else if (result && result.errorCode === 'invalid_invitation') {
      message = MESSAGES.invalidOrExpired;
    } else {
      message = MESSAGES.loadFailed;
    }

    _showError(message);
    _show(IDS.retry);
    return result || { ok: false, status: 0, error: message };
  }

  /**
   * Accept the invitation with the given code.
   * On success, redirects to /dashboard with a success message stashed in
   * sessionStorage (consumed by the dashboard, if it reads it) and as a
   * toast via ErrorHandler.showSuccess.
   * On error, displays the mapped message inline and keeps the page open.
   *
   * Requirements: 11.4, 11.5, 11.6, 11.7
   */
  async function accept(code) {
    code = code || _code;
    if (!code) {
      _showError(MESSAGES.missingCode);
      return { ok: false, status: 0, error: MESSAGES.missingCode };
    }

    if (typeof InstitutionAPI === 'undefined') {
      _showError(MESSAGES.genericAcceptError);
      return { ok: false, status: 0, error: MESSAGES.genericAcceptError };
    }

    if (_accepting) {
      // Guard against duplicate clicks while a request is in flight.
      return { ok: false, status: 0, error: 'Already in progress' };
    }
    _accepting = true;
    _clearError();
    _setAcceptBusy(true);

    var result;
    try {
      result = await InstitutionAPI.acceptInvitation(code);
    } finally {
      _accepting = false;
      _setAcceptBusy(false);
    }

    if (result && result.ok) {
      // Build success message using the institution name we already have on
      // screen (set by getDetails). Falls back to a generic message.
      var instEl = _$(IDS.institutionName);
      var instName =
        instEl && instEl.textContent && instEl.textContent !== '—'
          ? instEl.textContent.trim()
          : 'your institution';
      var successMsg = 'You have joined ' + instName;

      // Stash the message so the dashboard can surface it after redirect,
      // and also fire a toast immediately for visibility.
      try {
        sessionStorage.setItem('flash_success', successMsg);
      } catch (e) {
        // Ignore storage failures; the toast still appears.
      }
      if (typeof window !== 'undefined' && window.ErrorHandler) {
        window.ErrorHandler.showSuccess(successMsg);
      }

      // Brief delay so the user can perceive the success toast before redirect.
      setTimeout(function () {
        window.location.href = '/dashboard';
      }, 600);

      return result;
    }

    // Error path — surface a mapped, user-friendly message.
    var message = _mapAcceptError(result);
    _showError(message);

    // Special-case 401: session expired. ErrorHandler will redirect on its
    // next API call, but surface the message inline now.
    if (result && result.status === 401) {
      if (typeof window !== 'undefined' && window.ErrorHandler) {
        window.ErrorHandler.showError(MESSAGES.sessionExpired);
      }
    }

    return result || { ok: false, status: 0, error: message };
  }

  /**
   * Decline the invitation: simply navigate back to the Dashboard without
   * calling any API. The pending invitation remains until it expires or is
   * revoked by the institution admin.
   *
   * Requirements: 11.9
   */
  function decline() {
    window.location.href = '/dashboard';
  }

  // ── Page wiring ──────────────────────────────────────────────────────────

  /**
   * Wire up button handlers and kick off the initial details fetch.
   * Safe to call multiple times — handlers are bound once per element.
   *
   * Performs an authentication check before fetching invitation
   * details: unauthenticated visitors are redirected to /login with a
   * `return` query parameter pointing back to this page, so login.html
   * can bounce them back after sign-in (Requirement 11.8).
   */
  async function init() {
    _code = _getCodeFromUrl();

    // Authentication gate (Requirement 11.8). Run before binding any
    // handlers so we don't briefly render the page for users who are
    // about to be redirected away.
    var user = await _checkAuth();
    if (!user) {
      _redirectToLogin();
      return;
    }

    var acceptBtn = _$(IDS.acceptBtn);
    if (acceptBtn && !acceptBtn._invitationBound) {
      acceptBtn.addEventListener('click', function () { accept(); });
      acceptBtn._invitationBound = true;
    }

    var declineBtn = _$(IDS.declineBtn);
    if (declineBtn && !declineBtn._invitationBound) {
      declineBtn.addEventListener('click', function () { decline(); });
      declineBtn._invitationBound = true;
    }

    var retryBtn = _$(IDS.retryBtn);
    if (retryBtn && !retryBtn._invitationBound) {
      retryBtn.addEventListener('click', function () { getDetails(); });
      retryBtn._invitationBound = true;
    }

    // Initial fetch of invitation details (Requirement 11.2).
    getDetails();
  }

  // Auto-init when the DOM is ready, but only on the invitation page.
  if (typeof document !== 'undefined') {
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', function () {
        // Only run if the invitation acceptance container is present.
        if (document.getElementById(IDS.details)) {
          init();
        }
      });
    } else if (document.getElementById(IDS.details)) {
      init();
    }
  }

  // ── Expose public interface ──────────────────────────────────────────────
  return {
    init: init,
    getDetails: getDetails,
    accept: accept,
    decline: decline,
  };
})();

// Expose globally for legacy script-tag usage.
if (typeof window !== 'undefined') {
  window.Invitation = Invitation;
}
