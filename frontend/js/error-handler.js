// Mr.E — Error Handler Module
// Provides centralized error handling, user-facing toast notifications,
// a global handler for unhandled errors / promise rejections, and a
// universal session-expiry interceptor that catches HTTP 401 responses
// from any fetch-based API call.
//
// Requirements: 12.7, 14.1, 14.2, 14.6, 14.7, 14.8, 14.9
//
// Public API (exposed as window.ErrorHandler):
//   - statusMessages           Map of HTTP status codes → user-friendly messages
//   - showError(msg)           Display an error toast (auto-dismisses after 7s)
//   - showSuccess(msg)         Display a success toast (auto-dismisses after 5s)
//   - handleApiError(err, ctx) Normalize and surface API errors
//   - initGlobalHandler()      Attach window error / unhandledrejection listeners
//                              AND install the global fetch 401 interceptor
//   - installFetchInterceptor()  Standalone installer for the 401 interceptor
//                                (idempotent; called by initGlobalHandler)
//   - handleSessionExpiry()    Trigger session-expiry handling manually
//                              (clear sessionStorage + redirect to /login)
//
// Notes:
//   * Uses IIFE module pattern (vanilla JS, no build step required).
//   * Toasts are appended to document.body — no placeholder element needed.
//   * Toasts stack vertically (CSS positions them with offsets).
//   * On HTTP 401 the user is redirected to /login with a return URL and
//     sessionStorage is cleared (Requirements 12.7 / 14.8). The redirect
//     URL also carries `expired=1` so the login page can display the
//     "Your session has expired" message after navigation completes.
//   * The global fetch interceptor wraps window.fetch so every API client
//     (SubscriptionAPI, InstitutionAPI, Auth, raw fetch calls in pages)
//     gets uniform session-expiry handling without needing to opt in.

var ErrorHandler = (function () {
  'use strict';

  // ── Configuration ────────────────────────────────────────────────────────

  /**
   * Map HTTP status codes to user-friendly messages.
   * Aligned with the design document and Requirement 14.2.
   */
  var statusMessages = {
    400: 'Invalid request. Please check your input.',
    401: 'Your session has expired. Please log in again.',
    403: 'Access denied.',
    404: 'Resource not found.',
    409: 'Conflict with current state.',
    500: 'Server error. Please try again.',
    503: 'Service unavailable. Please try again later.',
  };

  // Auto-dismiss durations
  var SUCCESS_DURATION_MS = 5000; // Requirement 14.3, 14.4
  var ERROR_DURATION_MS = 7000;

  // Global handler installation flag — prevents duplicate listeners.
  var globalHandlerInstalled = false;

  // Fetch-interceptor installation flag — prevents wrapping fetch twice
  // even if installFetchInterceptor() is called from multiple modules.
  var fetchInterceptorInstalled = false;

  // Session-expiry guard — once a 401 has been observed and the user is
  // being redirected to /login, suppress subsequent 401 handling so we
  // don't queue up multiple redirects (e.g. when a page issues several
  // parallel API calls that all return 401).
  var sessionExpiryHandled = false;

  // URL paths where a 401 is part of the normal flow (e.g. failed login
  // attempts) and MUST NOT trigger a global session-expired redirect.
  // Matched as path prefixes against the request URL's pathname.
  var AUTH_ENDPOINT_PREFIXES = [
    '/api/auth/login',
    '/api/auth/admin/login',
    '/api/auth/register',
    '/api/auth/logout',
  ];

  // Pages where suppressing the redirect makes sense — if the user is
  // already on the login page, don't bounce them away from it.
  var LOGIN_PATH_PREFIXES = ['/login', '/html/login.html', '/register', '/html/register.html'];

  // ── Internal helpers ─────────────────────────────────────────────────────

  /**
   * Build a toast DOM element and append it to document.body.
   * Toasts of the same type stack vertically; new toasts appear above older
   * ones (closest to the bottom-right corner).
   */
  function _createToast(message, variantClass) {
    var toast = document.createElement('div');
    toast.className = 'toast ' + variantClass;
    toast.setAttribute('role', variantClass === 'toast-error' ? 'alert' : 'status');
    toast.setAttribute('aria-live', variantClass === 'toast-error' ? 'assertive' : 'polite');
    toast.textContent = message;
    document.body.appendChild(toast);
    _restack();
    return toast;
  }

  /**
   * Remove a toast from the DOM (idempotent) and restack remaining toasts.
   */
  function _removeToast(toast) {
    if (toast && toast.parentNode) {
      toast.parentNode.removeChild(toast);
    }
    _restack();
  }

  /**
   * Recompute vertical offsets so multiple toasts stack from bottom-up.
   * Newest toast (last child) sits at the bottom; older toasts shift up.
   */
  function _restack() {
    var toasts = document.querySelectorAll('.toast');
    var bottomOffset = 24; // matches existing .toast { bottom: 24px } in style.css
    var gap = 8;
    // Iterate from newest (last) to oldest (first).
    for (var i = toasts.length - 1; i >= 0; i--) {
      var el = toasts[i];
      el.style.bottom = bottomOffset + 'px';
      bottomOffset += el.offsetHeight + gap;
    }
  }

  /**
   * Extract HTTP status code from an Error message of the form "HTTP <code>".
   * Returns null if no status code is found.
   */
  function _extractStatus(errorMessage) {
    if (!errorMessage || typeof errorMessage !== 'string') return null;
    var match = errorMessage.match(/HTTP (\d+)/);
    return match ? parseInt(match[1], 10) : null;
  }

  /**
   * Determine whether a request URL is an authentication endpoint where
   * a 401 is part of normal credential failure (and not an expired
   * session). Accepts either a full URL or a path-only string.
   */
  function _isAuthEndpoint(url) {
    if (!url) return false;
    var path;
    try {
      // Parse against window.location so relative URLs ("/api/...") work.
      path = new URL(url, window.location.origin).pathname;
    } catch (e) {
      // Fall back to raw matching when URL is non-standard.
      path = String(url);
    }
    for (var i = 0; i < AUTH_ENDPOINT_PREFIXES.length; i++) {
      if (path.indexOf(AUTH_ENDPOINT_PREFIXES[i]) === 0) return true;
    }
    return false;
  }

  /**
   * Return true when the user is already on the login page — in that
   * case we must not redirect again (would create a loop and erase any
   * `?expired=1` / `?return=…` query parameters the page is showing).
   */
  function _isOnLoginPage() {
    try {
      var path = window.location.pathname || '';
      for (var i = 0; i < LOGIN_PATH_PREFIXES.length; i++) {
        if (path.indexOf(LOGIN_PATH_PREFIXES[i]) === 0) return true;
      }
      return false;
    } catch (e) {
      return false;
    }
  }

  /**
   * Resolve a request input (string | URL | Request) to its URL string.
   * Used by the fetch interceptor to inspect the request target.
   */
  function _resolveFetchUrl(input) {
    if (!input) return '';
    if (typeof input === 'string') return input;
    if (typeof Request !== 'undefined' && input instanceof Request) return input.url;
    if (typeof URL !== 'undefined' && input instanceof URL) return input.toString();
    // Last resort: stringify whatever was passed in.
    try { return String(input); } catch (e) { return ''; }
  }

  /**
   * Handle an HTTP 401 by clearing session state and redirecting to the
   * login page with `?return=<currentPath>&expired=1` so the login page
   * can show the "Your session has expired" message after navigation.
   *
   * Idempotent: subsequent calls are no-ops while a redirect is in
   * flight (handles the parallel-request case where multiple API calls
   * all return 401 in the same tick).
   *
   * Requirements 12.7, 14.8.
   */
  function handleSessionExpiry() {
    if (sessionExpiryHandled) return;
    sessionExpiryHandled = true;

    // Surface the 14.8 message immediately for users still on the
    // current page (the toast is short-lived and the redirect happens
    // on the next event-loop turn).
    try {
      showError(statusMessages[401]);
    } catch (e) { /* ignore — toast is best-effort */ }

    // Clear all session-scoped state. sessionStorage holds the
    // subscription cache (Requirement 12.7) and any other per-tab
    // state the app has accumulated.
    try {
      sessionStorage.clear();
    } catch (e) {
      // Ignore storage errors — proceed with redirect regardless.
    }

    // Skip the redirect if we're already on /login — bouncing the user
    // back would just clobber any return-URL/error state already set
    // by the page bootstrap.
    if (_isOnLoginPage()) return;

    var currentPath = (window.location.pathname || '/') + (window.location.search || '');
    var returnUrl = encodeURIComponent(currentPath);
    window.location.href = '/login?return=' + returnUrl + '&expired=1';
  }

  /**
   * @deprecated Internal alias — kept so existing call sites in this
   * file continue to work. New code SHOULD call handleSessionExpiry().
   */
  function _redirectToLogin() {
    handleSessionExpiry();
  }

  // ── Public API ───────────────────────────────────────────────────────────

  /**
   * Show an error toast that auto-dismisses after 7 seconds.
   * Requirement 14.1, 14.2, 14.6.
   */
  function showError(message) {
    if (!message) return null;
    var toast = _createToast(String(message), 'toast-error');
    setTimeout(function () { _removeToast(toast); }, ERROR_DURATION_MS);
    return toast;
  }

  /**
   * Show a success toast that auto-dismisses after 5 seconds.
   * Requirement 14.3, 14.4.
   */
  function showSuccess(message) {
    if (!message) return null;
    var toast = _createToast(String(message), 'toast-success');
    setTimeout(function () { _removeToast(toast); }, SUCCESS_DURATION_MS);
    return toast;
  }

  // ── Flash messages (survive page reloads) ────────────────────────────────

  // sessionStorage key used to stash a success message that should be
  // surfaced on the next page load. Useful when a subscription action
  // forces a full page reload (e.g. SubscriptionModal) and the toast
  // would otherwise be torn down before the user sees it.
  var FLASH_SUCCESS_KEY = 'flash_success';
  var FLASH_ERROR_KEY = 'flash_error';

  /**
   * Stash a success message to be shown as a toast after the next page
   * load. Used by flows that trigger a full-page reload after an async
   * action so the success notification (Requirement 14.3 / 14.4) is
   * not lost.
   */
  function setFlashSuccess(message) {
    if (!message) return;
    try { sessionStorage.setItem(FLASH_SUCCESS_KEY, String(message)); }
    catch (e) { /* storage may be unavailable; toast is best-effort */ }
  }

  /**
   * Stash an error message to be shown as a toast after the next page
   * load. Symmetrical to setFlashSuccess.
   */
  function setFlashError(message) {
    if (!message) return;
    try { sessionStorage.setItem(FLASH_ERROR_KEY, String(message)); }
    catch (e) { /* storage may be unavailable; toast is best-effort */ }
  }

  /**
   * Read any pending flash messages out of sessionStorage and surface
   * them as toasts. Called automatically on DOMContentLoaded by
   * initGlobalHandler() so callers don't need to opt in.
   *
   * Idempotent within a single page load: subsequent calls are no-ops
   * because the underlying storage keys are removed on the first call.
   */
  function flushFlashMessages() {
    try {
      var success = sessionStorage.getItem(FLASH_SUCCESS_KEY);
      if (success) {
        sessionStorage.removeItem(FLASH_SUCCESS_KEY);
        showSuccess(success);
      }
      var error = sessionStorage.getItem(FLASH_ERROR_KEY);
      if (error) {
        sessionStorage.removeItem(FLASH_ERROR_KEY);
        showError(error);
      }
    } catch (e) { /* ignore — flash messages are best-effort */ }
  }

  /**
   * Handle an API error consistently.
   * Logs the error to console with context (Requirement 14.9), maps known HTTP
   * status codes to user-friendly messages (Requirement 14.2), and falls back
   * to a generic message otherwise (Requirement 14.1).
   *
   * @param {Error|object} error  Error thrown by an API call. May expose either
   *   `.message` (e.g. "HTTP 500") or `.status` (numeric status code).
   * @param {string} context      Short label (e.g. "activateTrial") used in
   *   console logs for debugging.
   */
  async function handleApiError(error, context) {
    var label = context || 'api';
    // Log without exposing sensitive payload data (Requirement 14.9).
    console.error('[' + label + '] API Error:', {
      message: error && error.message,
      status: error && error.status,
      timestamp: new Date().toISOString(),
    });

    var message = error && error.message ? String(error.message) : '';

    // Network errors thrown by fetch (no response received).
    if (message === 'Failed to fetch' || message.toLowerCase().indexOf('networkerror') !== -1) {
      showError('Network error. Please check your connection and try again.');
      return;
    }

    // Determine status either from a numeric .status or from "HTTP <code>".
    var status = (error && typeof error.status === 'number') ? error.status : _extractStatus(message);

    if (status !== null && status !== undefined) {
      // Special handling for 401 — clear session and redirect to login
      // (Requirements 12.7, 14.8). handleSessionExpiry shows the toast
      // and is idempotent so it's safe to call from multiple sites.
      if (status === 401) {
        handleSessionExpiry();
        return;
      }
      var mapped = statusMessages[status] || statusMessages[500];
      showError(mapped);
      return;
    }

    // Fallback for non-HTTP errors.
    showError('An unexpected error occurred. Please try again.');
  }

  /**
   * Install a global wrapper around `window.fetch` that detects HTTP 401
   * responses on application API calls (`/api/*`) and triggers the
   * shared session-expiry handler.
   *
   * The interceptor:
   *   - Skips known auth endpoints (login/register/logout/admin login)
   *     where a 401 indicates failed credentials, NOT an expired session.
   *   - Skips redirect when the current page is already /login.
   *   - Is idempotent — calling installFetchInterceptor() repeatedly
   *     never wraps fetch more than once.
   *   - Preserves the original Response so callers continue to see the
   *     401 status and can run their own error logic if desired. The
   *     session-expiry handler clears storage and redirects, so most
   *     downstream handlers will be cancelled by the navigation.
   *
   * Requirements 12.7, 14.8.
   */
  function installFetchInterceptor() {
    if (fetchInterceptorInstalled) return;
    if (typeof window === 'undefined' || typeof window.fetch !== 'function') return;
    fetchInterceptorInstalled = true;

    var originalFetch = window.fetch.bind(window);

    window.fetch = function (input, init) {
      var requestUrl = _resolveFetchUrl(input);
      var promise = originalFetch(input, init);

      return promise.then(function (response) {
        try {
          // Only intercept successful HTTP responses with status 401.
          if (response && response.status === 401) {
            // Skip endpoints where 401 is a normal credential failure.
            if (!_isAuthEndpoint(requestUrl)) {
              handleSessionExpiry();
            }
          }
        } catch (e) {
          // Never let interceptor errors break the caller's promise chain.
          console.error('[ErrorHandler] fetch interceptor error:', e);
        }
        return response;
      });
    };
  }

  // Test/utility hook — resets the singleton flags so unit tests can
  // exercise installFetchInterceptor() and handleSessionExpiry()
  // repeatedly. Not part of the public API; only used by tests.
  function _resetForTests() {
    sessionExpiryHandled = false;
    fetchInterceptorInstalled = false;
    globalHandlerInstalled = false;
  }

  /**
   * Install global handlers for unhandled errors and promise rejections,
   * AND the global fetch 401 interceptor that powers session-expiry
   * handling for every API client (Requirements 12.7, 14.7, 14.8).
   * Idempotent — calling more than once has no additional effect.
   */
  function initGlobalHandler() {
    // Always (re-)attempt to install the fetch interceptor — it has its
    // own idempotency guard and pages may load error-handler.js before
    // calling initGlobalHandler() at different points in their bootstrap.
    installFetchInterceptor();

    if (globalHandlerInstalled) return;
    globalHandlerInstalled = true;

    window.addEventListener('error', function (event) {
      console.error('Unhandled error:', {
        message: event.message,
        filename: event.filename,
        lineno: event.lineno,
        colno: event.colno,
        timestamp: new Date().toISOString(),
      });
      showError('An unexpected error occurred. Please refresh the page.');
    });

    window.addEventListener('unhandledrejection', function (event) {
      console.error('Unhandled promise rejection:', {
        reason: event.reason && (event.reason.message || event.reason),
        timestamp: new Date().toISOString(),
      });
      showError('An unexpected error occurred. Please refresh the page.');
    });

    // Surface any flash messages stashed by a previous page (e.g. a
    // subscription action that forced a reload). Defer until the DOM
    // is ready so the toast container exists.
    if (typeof document !== 'undefined') {
      if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', flushFlashMessages);
      } else {
        flushFlashMessages();
      }
    }
  }

  // ── Expose public interface ──────────────────────────────────────────────

  return {
    statusMessages: statusMessages,
    showError: showError,
    showSuccess: showSuccess,
    setFlashSuccess: setFlashSuccess,
    setFlashError: setFlashError,
    flushFlashMessages: flushFlashMessages,
    handleApiError: handleApiError,
    handleSessionExpiry: handleSessionExpiry,
    installFetchInterceptor: installFetchInterceptor,
    initGlobalHandler: initGlobalHandler,
    // Internal — exported for unit tests only.
    _resetForTests: _resetForTests,
  };
})();

// Expose globally for legacy script-tag usage.
if (typeof window !== 'undefined') {
  window.ErrorHandler = ErrorHandler;

  // Install the universal fetch 401 interceptor as soon as this script
  // loads so every API client (SubscriptionAPI, InstitutionAPI, Auth,
  // and inline fetch calls in HTML pages) inherits session-expiry
  // handling without needing explicit opt-in. Pages that also call
  // ErrorHandler.initGlobalHandler() will reuse this same install.
  // Requirements 12.7, 14.8.
  try {
    ErrorHandler.installFetchInterceptor();
  } catch (e) {
    console.error('[ErrorHandler] auto-install of fetch interceptor failed:', e);
  }

  // Auto-flush flash messages stashed across page reloads so success
  // toasts (Requirements 14.3, 14.4) survive the navigation. Pages that
  // also call initGlobalHandler() will reuse the same idempotent flush.
  try {
    if (typeof document !== 'undefined') {
      if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', ErrorHandler.flushFlashMessages);
      } else {
        ErrorHandler.flushFlashMessages();
      }
    }
  } catch (e) {
    console.error('[ErrorHandler] auto-flush of flash messages failed:', e);
  }
}
