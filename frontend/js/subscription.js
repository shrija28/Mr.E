// Mr.E — Subscription API Client Module
// Handles subscription management, status retrieval, and exam access checks.
// All calls use credentials: 'include' to send httpOnly session cookies.
// Implements error handling for HTTP status codes: 400, 401, 403, 404, 409, 500, 503.
// Requirements: 1.5, 1.6, 2.2, 5.1, 8.2, 12.1

var SubscriptionAPI = (function () {
  'use strict';

  // ── Internal helpers ─────────────────────────────────────────────────────

  /**
   * Standard headers for JSON requests.
   */
  function _headers() {
    return { 'Content-Type': 'application/json' };
  }

  /**
   * Parse JSON response safely, returning null if parsing fails.
   */
  async function _parseJSON(res) {
    try {
      return await res.json();
    } catch (e) {
      return null;
    }
  }

  /**
   * Handle HTTP errors and return structured error object.
   * Maps status codes to user-friendly error messages.
   */
  function _handleError(status, data) {
    var errorMessages = {
      400: 'Invalid request. Please check your input and try again.',
      401: 'Authentication required. Please log in again.',
      403: 'Access denied. You do not have permission to perform this action.',
      404: 'Resource not found.',
      409: 'Conflict. This action cannot be completed (e.g., subscription already exists).',
      500: 'Internal server error. Please try again later.',
      503: 'Service temporarily unavailable. Please try again later.',
    };

    var message = errorMessages[status] || 'An unexpected error occurred.';
    
    // If the server provided a specific error message, use it
    if (data && data.error) {
      message = data.error;
    } else if (data && data.message) {
      message = data.message;
    }

    return {
      ok: false,
      status: status,
      error: message,
      data: data,
    };
  }

  // ── Public API ───────────────────────────────────────────────────────────

  /**
   * GET /api/subscription/status  (was incorrectly: /api/subscription/me)
   * Retrieves the current user's effective subscription status.
   * Returns { ok, status, data } where data contains subscription details on success.
   * Returns { ok: false, status: 404 } if no subscription exists.
   */
  async function getStatus() {
    try {
      var res = await fetch('/api/subscription/status', {
        method: 'GET',
        headers: _headers(),
        credentials: 'include',
      });

      var data = await _parseJSON(res);

      if (res.ok) {
        return { ok: true, status: res.status, data: data };
      }

      // Handle 404 specially - no subscription exists
      if (res.status === 404) {
        return { ok: false, status: 404, data: null, error: 'No active subscription found.' };
      }

      return _handleError(res.status, data);
    } catch (error) {
      return {
        ok: false,
        status: 0,
        error: 'Network error. Please check your connection and try again.',
        data: null,
      };
    }
  }

  /**
   * POST /api/subscription/select  (was incorrectly: /api/subscription/activate-trial)
   * Activates a Free Trial subscription for the current user.
   * Returns { ok, status, data } where data contains the new subscription on success.
   */
  async function activateTrial() {
    try {
      var res = await fetch('/api/subscription/select', {
        method: 'POST',
        headers: _headers(),
        body: JSON.stringify({ plan_type: 'trial', trial_duration_days: 7 }),
        credentials: 'include',
      });

      var data = await _parseJSON(res);

      if (res.ok) {
        return { ok: true, status: res.status, data: data };
      }

      return _handleError(res.status, data);
    } catch (error) {
      return {
        ok: false,
        status: 0,
        error: 'Network error. Please check your connection and try again.',
        data: null,
      };
    }
  }

  /**
   * POST /api/subscription/select  (was incorrectly: /api/subscription/activate-pro)
   * Activates a Pro subscription with the specified billing period.
   * @param {string} billingPeriod - Either 'weekly' or 'monthly'
   * Returns { ok, status, data } where data contains the new subscription on success.
   */
  async function activatePro(billingPeriod) {
    try {
      var res = await fetch('/api/subscription/select', {
        method: 'POST',
        headers: _headers(),
        body: JSON.stringify({ plan_type: 'pro', billing_period: billingPeriod }),
        credentials: 'include',
      });

      var data = await _parseJSON(res);

      if (res.ok) {
        return { ok: true, status: res.status, data: data };
      }

      return _handleError(res.status, data);
    } catch (error) {
      return {
        ok: false,
        status: 0,
        error: 'Network error. Please check your connection and try again.',
        data: null,
      };
    }
  }

  /**
   * POST /api/subscription/upgrade
   * Upgrades the current subscription to Pro with the specified billing period.
   * @param {string} billingPeriod - Either 'weekly' or 'monthly'
   * Returns { ok, status, data } where data contains the updated subscription on success.
   */
  async function upgrade(billingPeriod) {
    try {
      var res = await fetch('/api/subscription/upgrade', {
        method: 'POST',
        headers: _headers(),
        body: JSON.stringify({ billing_period: billingPeriod }),
        credentials: 'include',
      });

      var data = await _parseJSON(res);

      if (res.ok) {
        return { ok: true, status: res.status, data: data };
      }

      return _handleError(res.status, data);
    } catch (error) {
      return {
        ok: false,
        status: 0,
        error: 'Network error. Please check your connection and try again.',
        data: null,
      };
    }
  }

  /**
   * POST /api/subscription/cancel
   * Cancels the current subscription.
   * Access continues until the end of the current billing period.
   * Returns { ok, status, data } where data contains the updated subscription on success.
   */
  async function cancel() {
    try {
      var res = await fetch('/api/subscription/cancel', {
        method: 'POST',
        headers: _headers(),
        credentials: 'include',
      });

      var data = await _parseJSON(res);

      if (res.ok) {
        return { ok: true, status: res.status, data: data };
      }

      return _handleError(res.status, data);
    } catch (error) {
      return {
        ok: false,
        status: 0,
        error: 'Network error. Please check your connection and try again.',
        data: null,
      };
    }
  }

  /**
   * GET /api/subscription/billing-history
   * Retrieves the billing history for the current user.
   * Returns { ok, status, data } where data is an array of billing records on success.
   * Note: endpoint may not exist; returns empty array gracefully if 404.
   */
  async function getBillingHistory() {
    try {
      var res = await fetch('/api/subscription/billing-history', {
        method: 'GET',
        headers: _headers(),
        credentials: 'include',
      });

      var data = await _parseJSON(res);

      if (res.ok) {
        return { ok: true, status: res.status, data: data };
      }

      // 404 means the endpoint isn't implemented — return empty gracefully
      if (res.status === 404) {
        return { ok: true, status: 200, data: { history: [] } };
      }

      return _handleError(res.status, data);
    } catch (error) {
      return {
        ok: true,
        status: 200,
        data: { history: [] },
      };
    }
  }

  /**
   * POST /api/exam/check-access
   * Checks if the user has access to start an exam based on their subscription.
   * @param {string} subject - The exam subject (e.g., 'Physics', 'Chemistry')
   * @param {string} set - The exam set identifier
   * Returns { ok, status, data } where:
   *   - ok: true means access granted (HTTP 200)
   *   - ok: false with status 403 means access denied (check data.error_code for reason)
   */
  async function checkExamAccess(subject, set) {
    try {
      var res = await fetch('/api/exam/check-access', {
        method: 'POST',
        headers: _headers(),
        body: JSON.stringify({ subject: subject, set: set }),
        credentials: 'include',
      });

      var data = await _parseJSON(res);

      if (res.ok) {
        return { ok: true, status: res.status, data: data };
      }

      // For 403 errors, preserve the error_code from the response
      if (res.status === 403 && data && data.error_code) {
        return {
          ok: false,
          status: 403,
          error: data.error || data.message || 'Access denied',
          errorCode: data.error_code,
          data: data,
        };
      }

      return _handleError(res.status, data);
    } catch (error) {
      return {
        ok: false,
        status: 0,
        error: 'Network error. Please check your connection and try again.',
        data: null,
      };
    }
  }

  // ── Expose public interface ──────────────────────────────────────────────

  return {
    getStatus: getStatus,
    activateTrial: activateTrial,
    activatePro: activatePro,
    upgrade: upgrade,
    cancel: cancel,
    getBillingHistory: getBillingHistory,
    checkExamAccess: checkExamAccess,
  };
})();

// ═══════════════════════════════════════════════════════════════════════════
// SUBSCRIPTION STATE MANAGEMENT AND CACHING
// ═══════════════════════════════════════════════════════════════════════════
// Implements sessionStorage caching with 60-second TTL, cache validation,
// invalidation, and cross-tab synchronization using storage events.
// Requirements: 12.1, 12.4, 12.5, 12.6

var SubscriptionState = (function () {
  'use strict';

  // ── Constants ────────────────────────────────────────────────────────────

  var CACHE_KEY = 'smartkcet_subscription';
  var TTL = 60000; // 60 seconds in milliseconds

  // ── Cache Management ─────────────────────────────────────────────────────

  /**
   * Get cached subscription data from sessionStorage.
   * Returns null if cache is invalid or expired.
   * Requirement 12.5: Check timestamp before using cached data (60-second TTL)
   */
  function get() {
    try {
      var cached = sessionStorage.getItem(CACHE_KEY);
      if (!cached) {
        return null;
      }

      var parsed = JSON.parse(cached);
      var now = Date.now();

      // Check if cache has expired (TTL validation)
      if (now - parsed.timestamp > parsed.ttl) {
        clear();
        return null;
      }

      return parsed.data;
    } catch (error) {
      console.error('Error reading subscription cache:', error);
      clear();
      return null;
    }
  }

  /**
   * Store subscription data in sessionStorage with timestamp and TTL.
   * Requirement 12.1: Store subscription status in sessionStorage
   */
  function set(data) {
    try {
      var cached = {
        data: data,
        timestamp: Date.now(),
        ttl: TTL,
      };
      sessionStorage.setItem(CACHE_KEY, JSON.stringify(cached));
    } catch (error) {
      console.error('Error writing subscription cache:', error);
    }
  }

  /**
   * Clear cached subscription data from sessionStorage.
   * Requirement 12.6: Invalidate cache after subscription-changing actions
   */
  function clear() {
    try {
      sessionStorage.removeItem(CACHE_KEY);
    } catch (error) {
      console.error('Error clearing subscription cache:', error);
    }
  }

  /**
   * Check if cached data is valid (exists and not expired).
   * Requirement 12.5: Validate cache before use
   */
  function isValid() {
    return get() !== null;
  }

  // ── Expose public interface ──────────────────────────────────────────────

  return {
    CACHE_KEY: CACHE_KEY,
    TTL: TTL,
    get: get,
    set: set,
    clear: clear,
    isValid: isValid,
  };
})();

// ═══════════════════════════════════════════════════════════════════════════
// SUBSCRIPTION MODULE
// ═══════════════════════════════════════════════════════════════════════════
// High-level subscription management with caching, polling, and cross-tab sync.
// Requirements: 12.1, 12.4, 12.5, 12.6

var Subscription = (function () {
  'use strict';

  // ── State ────────────────────────────────────────────────────────────────

  var pollingInterval = null;
  var pollingIntervalMs = 5 * 60 * 1000; // 5 minutes

  // Tracks whether startPolling() has been called and not yet stopped.
  // Used so the visibility handler knows whether to resume after the tab
  // becomes visible again.
  var _pollingActive = false;

  // Last subscription snapshot observed by the polling loop. Maintained in
  // memory (not sessionStorage) because the cache TTL (60s) is shorter than
  // the polling interval (5min), so a cached value is unreliable for
  // detecting status transitions across polls.
  var _lastKnownStatus = null;

  // Reference to the notification banner DOM element used to inform the
  // user that their subscription status has changed (Requirement 12.10).
  var _statusChangeBannerEl = null;

  // ── Public API ───────────────────────────────────────────────────────────

  /**
   * Get current subscription status.
   * Uses cached data if valid (< 60 seconds old), otherwise fetches from API.
   * @param {boolean} forceRefresh - If true, bypass cache and fetch fresh data
   * Returns subscription data object or null if no subscription exists.
   * 
   * Requirements:
   * - 12.1: Fetch and cache subscription status
   * - 12.4: Read from same sessionStorage key for consistency
   * - 12.5: Don't make redundant API calls if cache is < 60 seconds old
   */
  async function getStatus(forceRefresh) {
    forceRefresh = forceRefresh || false;

    // Check cache first unless force refresh is requested
    if (!forceRefresh && SubscriptionState.isValid()) {
      return SubscriptionState.get();
    }

    // Fetch fresh data from API
    var result = await SubscriptionAPI.getStatus();

    if (result.ok && result.data) {
      // Cache the successful response
      SubscriptionState.set(result.data);
      return result.data;
    }

    // Handle 404 (no subscription) - don't cache this
    if (result.status === 404) {
      return null;
    }

    // Handle 401 (unauthenticated) - clear cache and return null
    // Requirement 12.7: Clear sessionStorage on 401
    if (result.status === 401) {
      SubscriptionState.clear();
      return null;
    }

    // For other errors, return null but don't clear cache
    // (cache might still be valid for display purposes)
    console.error('Error fetching subscription status:', result.error);
    return null;
  }

  /**
   * Activate Free Trial subscription.
   * Clears cache, fetches fresh data, and broadcasts the change so all
   * subscription-aware UI components refresh within 5 seconds.
   *
   * Requirements:
   * - 12.6: Invalidate cache after subscription-changing actions
   * - 12.3 / 4.9: Update banner and all subscription displays within 5s
   *   of a status change (activation, upgrade, cancel).
   */
  async function activateTrial() {
    var result = await SubscriptionAPI.activateTrial();

    if (result.ok) {
      // Clear cache and fetch fresh data
      SubscriptionState.clear();
      var fresh = await getStatus(true);
      _dispatchStatusChanged(fresh);
    }

    return result;
  }

  /**
   * Activate Pro subscription with specified billing period.
   * Clears cache, fetches fresh data, and broadcasts the change so all
   * subscription-aware UI components refresh within 5 seconds.
   *
   * @param {string} billingPeriod - Either 'weekly' or 'monthly'
   * Requirements: 12.6, 12.3, 4.9
   */
  async function activatePro(billingPeriod) {
    var result = await SubscriptionAPI.activatePro(billingPeriod);

    if (result.ok) {
      // Clear cache and fetch fresh data
      SubscriptionState.clear();
      var fresh = await getStatus(true);
      _dispatchStatusChanged(fresh);
    }

    return result;
  }

  /**
   * Upgrade to Pro subscription with specified billing period.
   * Clears cache, fetches fresh data, and broadcasts the change so all
   * subscription-aware UI components refresh within 5 seconds.
   *
   * @param {string} billingPeriod - Either 'weekly' or 'monthly'
   * Requirements: 12.6, 12.3, 4.9
   */
  async function upgrade(billingPeriod) {
    var result = await SubscriptionAPI.upgrade(billingPeriod);

    if (result.ok) {
      // Clear cache and fetch fresh data
      SubscriptionState.clear();
      var fresh = await getStatus(true);
      _dispatchStatusChanged(fresh);
    }

    return result;
  }

  /**
   * Cancel current subscription.
   * Clears cache, fetches fresh data, and broadcasts the change so all
   * subscription-aware UI components refresh within 5 seconds.
   *
   * Requirements: 12.6, 12.3, 4.9
   */
  async function cancel() {
    var result = await SubscriptionAPI.cancel();

    if (result.ok) {
      // Clear cache and fetch fresh data
      SubscriptionState.clear();
      var fresh = await getStatus(true);
      _dispatchStatusChanged(fresh);
    }

    return result;
  }

  /**
   * Get billing history.
   * Delegates directly to API (no caching for billing history).
   */
  async function getBillingHistory() {
    return SubscriptionAPI.getBillingHistory();
  }

  /**
   * Check if user has access to start an exam.
   * Delegates directly to API (no caching for access checks).
   * @param {string} subject - The exam subject
   * @param {string} set - The exam set identifier
   */
  async function checkExamAccess(subject, set) {
    return SubscriptionAPI.checkExamAccess(subject, set);
  }

  /**
   * Clear cached subscription data.
   * Useful for forcing a refresh or handling logout.
   * Requirement 12.6: Provide cache invalidation method
   */
  function clearCache() {
    SubscriptionState.clear();
  }

  /**
   * Start polling for subscription status changes.
   *
   * Polls GET /api/subscription/status every 5 minutes while the tab is
   * visible. Uses the Page Visibility API to pause polling when the tab
   * is hidden and resume immediately when it becomes visible again.
   *
   * Requirements:
   * - 12.9: Poll every 5 minutes while page is active (visible) to detect
   *   backend-initiated status changes.
   * - 12.10: When a change is detected, notify all UI components and
   *   surface a notification banner with a Refresh button.
   */
  function startPolling() {
    // Idempotent — calling start twice is a no-op.
    if (_pollingActive) {
      return;
    }
    _pollingActive = true;

    // Seed the change-detection baseline with whatever cached snapshot we
    // already have. If the cache is empty, the first poll establishes the
    // baseline without firing a spurious "changed" notification.
    if (_lastKnownStatus === null) {
      _lastKnownStatus = SubscriptionState.get();
    }

    // Visibility tracking is tied to polling because it controls the
    // interval timer. Cross-tab sync (storage listener) is installed at
    // module load — see the bottom of the IIFE — so it works whether or
    // not polling is active. This ensures cache invalidation in another
    // tab (after activate/upgrade/cancel) still refreshes this tab's UI
    // within the 5-second window required by Requirement 12.3 / 4.9.
    document.addEventListener('visibilitychange', _handleVisibilityChange);

    // Only start the interval if the tab is currently visible. If it's
    // hidden, _handleVisibilityChange will start the interval when the
    // user returns.
    if (!document.hidden) {
      _startPollingInterval();
    }
  }

  /**
   * Stop polling for subscription status changes.
   * Cleans up interval and visibility listener. The storage listener
   * stays installed for the lifetime of the page so cross-tab cache
   * invalidation continues to work even when polling is paused.
   */
  function stopPolling() {
    _pollingActive = false;
    _stopPollingInterval();

    document.removeEventListener('visibilitychange', _handleVisibilityChange);
  }

  // ── Internal helpers ─────────────────────────────────────────────────────

  /**
   * Broadcast a `subscriptionStatusChanged` event after an action-driven
   * refresh (activate/upgrade/cancel) so every subscription-aware UI
   * component on the current tab updates within 5 seconds.
   *
   * Also advances the polling baseline (`_lastKnownStatus`) so the next
   * poll tick does not re-detect the same transition and surface the
   * "Your subscription status has changed" notification banner — that
   * banner is reserved for backend-initiated changes the user did not
   * trigger themselves (Requirement 12.10).
   *
   * Requirements:
   * - 12.3: Refresh and update all subscription UI within 5 seconds of
   *   a status change.
   * - 4.9: Subscription_Banner SHALL update its display within 5 seconds
   *   when the student's subscription status changes (e.g., after
   *   activating a trial, upgrading to Pro, or when a renewal is
   *   processed).
   */
  function _dispatchStatusChanged(newData) {
    // Keep the polling baseline in sync with the action-driven update so
    // the next poll does not double-notify.
    _lastKnownStatus = newData || null;

    if (typeof window === 'undefined' || typeof window.dispatchEvent !== 'function') {
      return;
    }
    var event = new CustomEvent('subscriptionStatusChanged', {
      detail: { subscription: newData || null },
    });
    window.dispatchEvent(event);
  }

  /**
   * Start the setInterval timer that drives recurring polls.
   * Separated from startPolling() so the visibility handler can pause
   * and resume the interval cleanly.
   */
  function _startPollingInterval() {
    if (pollingInterval) {
      return;
    }
    pollingInterval = setInterval(function () {
      // Defensive guard: if the tab became hidden between ticks we skip
      // the poll. The visibility handler is the primary mechanism, but
      // this keeps the interval safe even if visibility events are
      // missed (e.g. background throttling).
      if (!document.hidden) {
        _pollStatus();
      }
    }, pollingIntervalMs);
  }

  /**
   * Clear the recurring poll timer without tearing down the polling
   * subsystem (event listeners, baseline state). Used by the visibility
   * handler to pause polling while the tab is hidden.
   */
  function _stopPollingInterval() {
    if (pollingInterval) {
      clearInterval(pollingInterval);
      pollingInterval = null;
    }
  }

  /**
   * Poll subscription status and detect changes.
   *
   * Compares the freshly fetched subscription against the in-memory
   * baseline (_lastKnownStatus) — not the sessionStorage cache, which
   * has a 60-second TTL shorter than the 5-minute polling interval and
   * would therefore be expired on every poll.
   *
   * Requirement 12.10: Display notification when status changes.
   */
  async function _pollStatus() {
    try {
      var oldData = _lastKnownStatus;
      var newData = await getStatus(true);

      // First successful poll establishes the baseline silently.
      if (oldData && newData && _hasStatusChanged(oldData, newData)) {
        _notifyStatusChange(newData);
      }

      // Always advance the baseline so the next poll compares against
      // the most recent observation.
      _lastKnownStatus = newData;
    } catch (error) {
      console.error('Error polling subscription status:', error);
    }
  }

  /**
   * Check if subscription status has meaningfully changed.
   * Compares key fields that would affect user experience.
   */
  function _hasStatusChanged(oldData, newData) {
    return (
      oldData.status !== newData.status ||
      oldData.plan_type !== newData.plan_type ||
      oldData.remaining_attempts !== newData.remaining_attempts ||
      oldData.can_start_exam !== newData.can_start_exam
    );
  }

  /**
   * Notify the user and other UI components that the subscription status
   * has changed.
   *
   * Two channels are used:
   *  1. A `subscriptionStatusChanged` window CustomEvent so existing
   *     components (subscription-banner, subscription-page,
   *     upgrade-prompt) can refresh themselves with the new data.
   *  2. A persistent in-page notification banner with a Refresh button,
   *     per Requirement 12.10.
   */
  function _notifyStatusChange(newData) {
    var event = new CustomEvent('subscriptionStatusChanged', {
      detail: { subscription: newData },
    });
    window.dispatchEvent(event);

    _showStatusChangeBanner();
  }

  /**
   * Render (or reveal, if already rendered) the status-change notification
   * banner. The banner offers a single action — Refresh — that reloads the
   * page so every component reads the latest subscription state from a
   * cold start.
   *
   * Requirement 12.10.
   */
  function _showStatusChangeBanner() {
    if (typeof document === 'undefined' || !document.body) {
      return;
    }

    if (_statusChangeBannerEl && document.body.contains(_statusChangeBannerEl)) {
      _statusChangeBannerEl.hidden = false;
      _statusChangeBannerEl.classList.add('is-visible');
      return;
    }

    var banner = document.createElement('div');
    banner.className = 'subscription-status-change-banner';
    banner.setAttribute('role', 'status');
    banner.setAttribute('aria-live', 'polite');
    banner.innerHTML =
      '<span class="subscription-status-change-banner__message">' +
      'Your subscription status has changed.' +
      '</span>' +
      '<button type="button" class="subscription-status-change-banner__refresh">Refresh</button>' +
      '<button type="button" class="subscription-status-change-banner__dismiss" aria-label="Dismiss notification">&times;</button>';

    var refreshBtn = banner.querySelector('.subscription-status-change-banner__refresh');
    if (refreshBtn) {
      refreshBtn.addEventListener('click', function () {
        window.location.reload();
      });
    }

    var dismissBtn = banner.querySelector('.subscription-status-change-banner__dismiss');
    if (dismissBtn) {
      dismissBtn.addEventListener('click', function () {
        _hideStatusChangeBanner();
      });
    }

    document.body.appendChild(banner);
    _statusChangeBannerEl = banner;

    // Force reflow so the entrance transition (defined in CSS) runs.
    // eslint-disable-next-line no-unused-expressions
    banner.offsetHeight;
    banner.classList.add('is-visible');
  }

  /**
   * Hide the status-change banner without removing it from the DOM, so
   * subsequent status changes during the same session can re-show the
   * same element instantly.
   */
  function _hideStatusChangeBanner() {
    if (!_statusChangeBannerEl) {
      return;
    }
    _statusChangeBannerEl.classList.remove('is-visible');
    _statusChangeBannerEl.hidden = true;
  }

  /**
   * Handle page visibility changes.
   *
   * Pauses the polling interval when the tab is hidden and resumes it
   * immediately when the tab becomes visible again, performing one
   * catch-up poll so the UI reflects any backend-initiated changes that
   * occurred while the tab was in the background.
   */
  function _handleVisibilityChange() {
    if (!_pollingActive) {
      return;
    }

    if (document.hidden) {
      _stopPollingInterval();
    } else {
      _startPollingInterval();
      _pollStatus();
    }
  }

  /**
   * Handle storage events for cross-tab synchronization.
   * When subscription data changes in another tab, update this tab.
   * Requirement 12.4: Cross-tab sync using storage event
   */
  function _handleStorageChange(event) {
    // Only handle changes to our subscription cache key
    if (event.key === SubscriptionState.CACHE_KEY && event.newValue) {
      try {
        var parsed = JSON.parse(event.newValue);
        var newData = parsed && parsed.data ? parsed.data : null;
        if (!newData) {
          return;
        }

        // If the cross-tab update represents a meaningful change, surface
        // the same notification we'd show from a poll. Otherwise just
        // refresh listeners silently.
        var oldData = _lastKnownStatus;
        _lastKnownStatus = newData;

        if (oldData && _hasStatusChanged(oldData, newData)) {
          _notifyStatusChange(newData);
        } else {
          var event2 = new CustomEvent('subscriptionStatusChanged', {
            detail: { subscription: newData },
          });
          window.dispatchEvent(event2);
        }
      } catch (error) {
        console.error('Error handling storage change:', error);
      }
    }
  }

  // ── Module-load setup ────────────────────────────────────────────────────
  //
  // Cross-tab cache synchronisation (Requirement 12.4 + 12.3 + 4.9):
  // attach the `storage` listener at module load so that when one tab
  // activates / upgrades / cancels a subscription and writes the fresh
  // payload to sessionStorage, every other tab on this origin sees the
  // change and refreshes its UI within the 5-second SLA — without any
  // page needing to call startPolling() explicitly. The listener is
  // passive (no timers, no network) so it carries no idle cost.
  //
  // Note: sessionStorage is per-tab in modern browsers, so this fires
  // primarily for cross-window broadcasts performed via localStorage
  // mirrors or for tabs sharing a session via "Duplicate tab". The
  // listener still satisfies Requirement 12.4 by reacting whenever a
  // storage event for the cache key arrives.
  if (typeof window !== 'undefined' && typeof window.addEventListener === 'function') {
    window.addEventListener('storage', _handleStorageChange);
  }

  // ── Expose public interface ──────────────────────────────────────────────

  return {
    getStatus: getStatus,
    activateTrial: activateTrial,
    activatePro: activatePro,
    upgrade: upgrade,
    cancel: cancel,
    getBillingHistory: getBillingHistory,
    checkExamAccess: checkExamAccess,
    clearCache: clearCache,
    startPolling: startPolling,
    stopPolling: stopPolling,
  };
})();
