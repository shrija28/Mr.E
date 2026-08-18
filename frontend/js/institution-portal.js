// Mr.E — Institution Portal API Client Module
// Handles institution admin operations: dashboard, student management,
// invitation generation/revocation, and institution subscription details.
// Also exposes invitation lookup and acceptance for student-side flows.
// All calls use credentials: 'include' to send httpOnly session cookies.
// Implements error handling for institution-specific error codes returned
// by the backend (max_invitations_reached, seats_full, already_linked,
// invalid_invitation, student_not_found, institution_not_found, forbidden).
// Requirements: 3.5, 3.7, 10.2, 10.9, 11.2

var InstitutionAPI = (function () {
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
   * Extract the institution-specific error code from a FastAPI error
   * response. The backend returns errors as `{ detail: { error, message, ... } }`
   * with a stable `error` slug we can match against in the UI.
   * Falls back to generic codes when the slug is not present.
   */
  function _extractErrorCode(data) {
    if (!data) return null;
    if (data.detail && typeof data.detail === 'object' && data.detail.error) {
      return data.detail.error;
    }
    if (data.error) return data.error;
    return null;
  }

  /**
   * Extract a human-readable message from the response payload, preferring
   * the backend's structured `detail.message`.
   */
  function _extractMessage(data, fallback) {
    if (data) {
      if (data.detail && typeof data.detail === 'object' && data.detail.message) {
        return data.detail.message;
      }
      if (typeof data.detail === 'string') return data.detail;
      if (data.message) return data.message;
      if (data.error && typeof data.error === 'string') return data.error;
    }
    return fallback;
  }

  /**
   * Map HTTP status codes and institution-specific error codes to
   * user-friendly messages so callers can show consistent UX without
   * duplicating mapping logic in every page.
   */
  function _handleError(status, data) {
    var statusMessages = {
      400: 'Invalid request. Please check your input and try again.',
      401: 'Authentication required. Please log in again.',
      403: 'Access denied. You do not have permission to perform this action.',
      404: 'Resource not found.',
      409: 'This action conflicts with the current state.',
      500: 'Internal server error. Please try again later.',
      503: 'Service temporarily unavailable. Please try again later.',
    };

    // Institution-specific error codes (slugs returned by backend)
    var errorCodeMessages = {
      forbidden: 'You do not have permission to access institution resources.',
      validation_error: 'Invalid request. Please check your input and try again.',
      duplicate_email: 'This email is already registered.',
      max_invitations_reached:
        'You have reached the maximum of 50 pending invitations. ' +
        'Please wait for students to accept existing invitations or let them expire.',
      seats_full:
        'Your institution has reached its maximum student capacity. ' +
        'Upgrade your plan or remove students to invite more.',
      already_linked:
        'You are already linked to another institution. ' +
        'You must leave your current institution before joining a new one.',
      invalid_invitation:
        'This invitation is invalid or has expired. ' +
        'Please contact your institution admin for a new invitation.',
      student_not_found: 'Student not found or not linked to this institution.',
      institution_not_found: 'Institution not found.',
      invalid_plan: 'The selected plan is invalid or inactive.',
      active_subscription_exists:
        'An active subscription already exists. The new plan will take effect at the end of the current billing period.',
      service_unavailable:
        'Service temporarily unavailable. Please try again later.',
      internal_error: 'An unexpected error occurred. Please try again.',
    };

    var errorCode = _extractErrorCode(data);
    var fallback = statusMessages[status] || 'An unexpected error occurred.';
    var message = errorCode && errorCodeMessages[errorCode]
      ? errorCodeMessages[errorCode]
      : _extractMessage(data, fallback);

    return {
      ok: false,
      status: status,
      errorCode: errorCode,
      error: message,
      data: data,
    };
  }

  /**
   * Wrap a fetch call with a uniform success/error envelope so every API
   * method returns the same shape: `{ ok, status, data, error?, errorCode? }`.
   */
  async function _request(url, options) {
    try {
      var res = await fetch(url, options);
      var data = await _parseJSON(res);

      if (res.ok) {
        return { ok: true, status: res.status, data: data };
      }

      return _handleError(res.status, data);
    } catch (error) {
      return {
        ok: false,
        status: 0,
        errorCode: 'network_error',
        error: 'Network error. Please check your connection and try again.',
        data: null,
      };
    }
  }

  // ── Public API ───────────────────────────────────────────────────────────

  /**
   * GET /api/institution/dashboard
   * Retrieves the institution dashboard data: KPI metrics, recent activity,
   * and per-subject performance summary.
   * Requirements: 9.2 (display dashboard data)
   */
  async function getDashboard() {
    return _request('/api/institution/dashboard', {
      method: 'GET',
      headers: _headers(),
      credentials: 'include',
    });
  }

  /**
   * GET /api/institution/students
   * Retrieves the list of students linked to the institution.
   * Returns columns used by the management table: name, KCET ID, email, linked date.
   * Requirements: 3.5
   */
  async function getStudents() {
    return _request('/api/institution/students', {
      method: 'GET',
      headers: _headers(),
      credentials: 'include',
    });
  }

  /**
   * POST /api/institution/invite
   * Generates a new invitation code (valid for 7 days, max 50 pending).
   * Returns the code so the caller can render copy-link / copy-code UI.
   *
   * Backend may respond with:
   *   - 409 max_invitations_reached: pending invitation cap (50) reached
   *   - 403 seats_full: institution has no available seats
   *
   * Requirements: 10.2
   */
  async function generateInvitation() {
    return _request('/api/institution/invite', {
      method: 'POST',
      headers: _headers(),
      // Backend currently accepts an empty body for invitation creation.
      body: JSON.stringify({}),
      credentials: 'include',
    });
  }

  /**
   * DELETE /api/institution/invite/{code}
   * Revokes a pending invitation so it can no longer be redeemed.
   * @param {string} code - The invitation code to revoke
   *
   * Backend may respond with:
   *   - 404 invalid_invitation: code not found, already consumed, or expired
   *
   * Requirements: 10.9, 10.10
   */
  async function revokeInvitation(code) {
    var encoded = encodeURIComponent(code);
    return _request('/api/institution/invite/' + encoded, {
      method: 'DELETE',
      headers: _headers(),
      credentials: 'include',
    });
  }

  /**
   * GET /api/institution/invitations
   * Lists pending invitations for the current institution so the admin
   * can review and revoke them. Returns an array of invitation records
   * with code, created_at, expires_at, and status fields.
   *
   * The Manage Students page (task 10.3) renders this list as a table.
   * If the backend returns 404 (endpoint not yet deployed) the caller
   * may treat the result as an empty list so the page degrades gracefully.
   *
   * Requirements: 10.9
   */
  async function getInvitations() {
    return _request('/api/institution/invitations', {
      method: 'GET',
      headers: _headers(),
      credentials: 'include',
    });
  }

  /**
   * GET /api/institution/subscription
   * Retrieves the institution's current subscription details: plan name,
   * max seats, current usage, weekly/monthly test limits and usage,
   * status, and next renewal date.
   * Requirements: 3.7
   */
  async function getSubscription() {
    return _request('/api/institution/subscription', {
      method: 'GET',
      headers: _headers(),
      credentials: 'include',
    });
  }

  /**
   * GET /api/institution/invite/{code}
   * Retrieves invitation details so the student can preview the institution
   * before accepting. Used by the invitation acceptance page.
   * @param {string} code - The invitation code from the URL parameter
   *
   * Backend may respond with:
   *   - 400 invalid_invitation: invitation does not exist or has expired
   *
   * Requirements: 11.2
   */
  async function getInvitationDetails(code) {
    var encoded = encodeURIComponent(code);
    return _request('/api/institution/invite/' + encoded, {
      method: 'GET',
      headers: _headers(),
      credentials: 'include',
    });
  }

  /**
   * POST /api/institution/invite/{code}/accept
   * Accepts an invitation, linking the authenticated student to the institution.
   * @param {string} code - The invitation code to accept
   *
   * Backend may respond with:
   *   - 400 invalid_invitation: code is invalid or has expired
   *   - 409 already_linked: student is already linked to another institution
   *   - 409 seats_full: institution has reached its student capacity
   *
   * Requirements: 11.4, 11.5, 11.6
   */
  async function acceptInvitation(code) {
    var encoded = encodeURIComponent(code);
    return _request('/api/institution/invite/' + encoded + '/accept', {
      method: 'POST',
      headers: _headers(),
      credentials: 'include',
    });
  }

  // ── Expose public interface ──────────────────────────────────────────────

  return {
    getDashboard: getDashboard,
    getStudents: getStudents,
    generateInvitation: generateInvitation,
    revokeInvitation: revokeInvitation,
    getInvitations: getInvitations,
    getSubscription: getSubscription,
    getInvitationDetails: getInvitationDetails,
    acceptInvitation: acceptInvitation,
  };
})();


// ─────────────────────────────────────────────────────────────────────────
// Institution Subscription Page Logic (Task 11.2)
// ─────────────────────────────────────────────────────────────────────────
// Drives the /institution/subscription page (institution-subscription.html):
//   * Loads subscription details via GET /api/institution/subscription
//   * Renders plan name, seats, test limits, status, renewal date, etc.
//   * Surfaces an alert banner for overdue / grace_period / expired states
//   * Wires the Refresh and Retry buttons
//
// Pairs with the markup in `institution-subscription.html` (task 11.1) and
// the InstitutionAPI client defined above. Exposes `loadInstitutionSubscription`
// on `window` so the inline page bootstrap can invoke it on DOMContentLoaded.
//
// Requirements: 3.7

(function () {
  'use strict';

  // ── DOM id map (kept in sync with institution-subscription.html) ─────────

  var IDS = {
    // State containers
    loading:           'subscriptionLoading',
    error:             'subscriptionError',
    errorMessage:      'subscriptionErrorMessage',
    retryBtn:          'subscriptionRetryBtn',
    empty:             'subscriptionEmpty',
    content:           'subscriptionContent',
    refreshBtn:        'refreshSubscriptionBtn',

    // Alert banner (overdue / grace_period / expired)
    alertBanner:       'subscriptionAlertBanner',
    alertTitle:        'subscriptionAlertTitle',
    alertMessage:      'subscriptionAlertMessage',
    alertActionBtn:    'subscriptionAlertActionBtn',

    // Plan + status
    planName:          'subscriptionPlanName',
    institutionName:   'subscriptionInstitutionName',
    statusBadge:       'subscriptionStatusBadge',

    // Detail tiles
    seatsUsed:         'subscriptionSeatsUsed',
    seatsTotal:        'subscriptionSeatsTotal',
    seatsHint:         'subscriptionSeatsHint',
    weeklyLimit:       'subscriptionWeeklyLimit',
    weeklyRemaining:   'subscriptionWeeklyRemaining',
    monthlyLimit:      'subscriptionMonthlyLimit',
    monthlyRemaining:  'subscriptionMonthlyRemaining',
    renewalLabel:      'subscriptionRenewalLabel',
    renewalDate:       'subscriptionRenewalDate',
    renewalHint:       'subscriptionRenewalHint',
    startDate:         'subscriptionStartDate',
    billingPeriodItem: 'subscriptionBillingPeriodItem',
    billingPeriod:     'subscriptionBillingPeriod',
  };

  // ── DOM helpers ──────────────────────────────────────────────────────────

  function $(id)             { return document.getElementById(id); }
  function show(id, display) { var el = $(id); if (el) el.style.display = display || ''; }
  function hide(id)          { var el = $(id); if (el) el.style.display = 'none'; }
  function setText(id, t)    { var el = $(id); if (el) el.textContent = t; }

  // ── Formatting helpers ───────────────────────────────────────────────────

  /**
   * Format an ISO date string as "DD MMM YYYY" (en-IN locale).
   * Returns the placeholder if the value is missing or unparseable.
   */
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

  /**
   * Compute whole days remaining between now and the given ISO date.
   * Returns null if the date is missing/invalid. Negative values are clamped
   * to 0 so the UI never shows negative day counts.
   */
  function _daysUntil(value) {
    if (!value) return null;
    try {
      var d = new Date(value);
      if (isNaN(d.getTime())) return null;
      var diffMs = d.getTime() - Date.now();
      var days = Math.ceil(diffMs / (1000 * 60 * 60 * 24));
      return days < 0 ? 0 : days;
    } catch (e) {
      return null;
    }
  }

  /**
   * Render a numeric value, treating null/undefined as "Unlimited" (for plan
   * limits) or as a literal "0" / number otherwise. Used for test-limit tiles.
   */
  function _formatLimit(value) {
    if (value === null || value === undefined) return 'Unlimited';
    var n = Number(value);
    if (isNaN(n)) return '—';
    return String(n);
  }

  function _formatNumber(value, fallback) {
    if (value === null || value === undefined) return fallback || '—';
    var n = Number(value);
    if (isNaN(n)) return fallback || '—';
    return String(n);
  }

  /**
   * Human-friendly status label + CSS class for the status badge.
   * Mirrors the labels used on the student subscription page so the user
   * sees consistent terminology across both portals.
   */
  function _statusInfo(status) {
    switch ((status || '').toLowerCase()) {
      case 'trial':        return { label: 'Active',       cls: 'badge-active'  };
      case 'active':       return { label: 'Active',       cls: 'badge-active'  };
      case 'overdue':      return { label: 'Overdue',      cls: 'badge-warning' };
      case 'grace_period': return { label: 'Grace Period', cls: 'badge-warning' };
      case 'expired':      return { label: 'Expired',      cls: 'badge-error'   };
      case 'cancelled':    return { label: 'Cancelled',    cls: 'badge-error'   };
      default:             return { label: status || '—',  cls: 'badge-muted'   };
    }
  }

  /**
   * Pick the first defined value from a list of keys on the payload.
   * Lets us tolerate small differences in API field naming without breaking.
   */
  function _pick(data) {
    for (var i = 1; i < arguments.length; i++) {
      var key = arguments[i];
      if (data && data[key] !== undefined && data[key] !== null) return data[key];
    }
    return undefined;
  }

  // ── State helpers ────────────────────────────────────────────────────────

  function _renderLoading() {
    show(IDS.loading);
    hide(IDS.error);
    hide(IDS.empty);
    hide(IDS.content);
    hide(IDS.alertBanner);
  }

  function _renderError(message) {
    hide(IDS.loading);
    hide(IDS.empty);
    hide(IDS.content);
    hide(IDS.alertBanner);
    setText(IDS.errorMessage, message || 'Please check your connection and try again.');
    show(IDS.error);
  }

  function _renderEmpty() {
    hide(IDS.loading);
    hide(IDS.error);
    hide(IDS.content);
    hide(IDS.alertBanner);
    show(IDS.empty);
  }

  // ── Alert banner ─────────────────────────────────────────────────────────

  /**
   * Show an alert banner for at-risk subscription states (Requirement 3.7
   * surfaces these inline; the language matches the dashboard banner used
   * elsewhere in the institution portal).
   */
  function _renderAlertBanner(status, daysRemaining) {
    var banner = $(IDS.alertBanner);
    if (!banner) return;

    var s = (status || '').toLowerCase();
    var titleText = '';
    var messageText = '';
    var actionText = 'Pay Now';
    var bannerStatus = s;

    if (s === 'overdue' || s === 'grace_period') {
      titleText = 'Payment Overdue';
      messageText = (typeof daysRemaining === 'number' && daysRemaining >= 0)
        ? "Your institution's access will be suspended in " +
          daysRemaining + ' day' + (daysRemaining === 1 ? '' : 's') + '.'
        : "Your institution's access will be suspended soon.";
      actionText = 'Pay Now';
    } else if (s === 'expired') {
      titleText = 'Subscription Expired';
      messageText = "Your institution's subscription has expired. Renew to restore access for your students.";
      actionText = 'Renew Subscription';
    } else if (s === 'cancelled') {
      titleText = 'Subscription Cancelled';
      messageText = 'Your institution\'s subscription has been cancelled. Reactivate to restore access.';
      actionText = 'Reactivate';
    } else {
      // Active / trial — no alert needed.
      hide(IDS.alertBanner);
      return;
    }

    setText(IDS.alertTitle, titleText);
    setText(IDS.alertMessage, messageText);

    var btn = $(IDS.alertActionBtn);
    if (btn) btn.textContent = actionText;

    banner.setAttribute('data-status', bannerStatus);
    banner.style.display = 'flex';
  }

  // ── Main renderer ────────────────────────────────────────────────────────

  /**
   * Render the institution subscription payload into the page.
   *
   * Tolerates both the canonical SubscriptionResponse shape (plan_name,
   * start_date, billing_period, status, …) and the institution-specific
   * dashboard shape (max_students, total_students, weekly_test_limit, …)
   * documented in the design — many fields may live on either object.
   */
  function _renderSubscription(data) {
    if (!data || typeof data !== 'object') {
      _renderEmpty();
      return;
    }

    // ── Plan name ────────────────────────────────────────────────────────
    var planName = _pick(data, 'plan_name', 'planName');
    if (!planName) {
      var planObj = data.plan;
      if (planObj && (planObj.name || planObj.plan_name)) {
        planName = planObj.name || planObj.plan_name;
      } else {
        planName = 'Institution Plan';
      }
    }
    setText(IDS.planName, planName);

    // ── Institution name (sub-line under plan) ──────────────────────────
    var institutionName = _pick(data, 'institution_name', 'institutionName');
    if (institutionName) {
      setText(IDS.institutionName, institutionName);
      show(IDS.institutionName, 'block');
    } else {
      hide(IDS.institutionName);
    }

    // ── Status badge ─────────────────────────────────────────────────────
    var status = _pick(data, 'status', 'subscription_status') || 'active';
    var info = _statusInfo(status);
    var badge = $(IDS.statusBadge);
    if (badge) {
      badge.textContent = info.label;
      badge.className = 'status-badge ' + info.cls;
      badge.setAttribute('data-status', String(status).toLowerCase());
    }

    // ── Seat usage (max student seats + current usage) ──────────────────
    var maxSeats = _pick(data, 'max_students', 'max_student_seats', 'maxSeats');
    var seatsUsed = _pick(data, 'total_students', 'seats_used', 'current_seats');

    // Plan object often holds max_student_seats when the response is the
    // canonical SubscriptionResponse shape.
    if ((maxSeats === undefined) && data.plan && data.plan.max_student_seats !== undefined) {
      maxSeats = data.plan.max_student_seats;
    }

    setText(IDS.seatsUsed,  _formatNumber(seatsUsed, '0'));
    setText(IDS.seatsTotal, _formatLimit(maxSeats));

    if (maxSeats !== undefined && maxSeats !== null && seatsUsed !== undefined && seatsUsed !== null) {
      var seatsRemaining = Math.max(0, Number(maxSeats) - Number(seatsUsed));
      setText(IDS.seatsHint, seatsRemaining + ' seat' + (seatsRemaining === 1 ? '' : 's') + ' available');
    } else {
      setText(IDS.seatsHint, 'seats in use');
    }

    // ── Weekly test limit + usage ───────────────────────────────────────
    var weeklyLimit = _pick(data, 'weekly_test_limit', 'weeklyTestLimit');
    if ((weeklyLimit === undefined) && data.plan && data.plan.weekly_test_limit !== undefined) {
      weeklyLimit = data.plan.weekly_test_limit;
    }
    var weeklyUsed      = _pick(data, 'tests_this_week', 'weekly_tests_used');
    var weeklyRemaining = _pick(data, 'weekly_tests_remaining');
    if (weeklyRemaining === undefined && weeklyLimit !== undefined && weeklyLimit !== null && weeklyUsed !== undefined && weeklyUsed !== null) {
      weeklyRemaining = Math.max(0, Number(weeklyLimit) - Number(weeklyUsed));
    }

    setText(IDS.weeklyLimit, _formatLimit(weeklyLimit));
    if (weeklyLimit === null || weeklyLimit === undefined) {
      setText(IDS.weeklyRemaining,
        (weeklyUsed !== undefined && weeklyUsed !== null)
          ? _formatNumber(weeklyUsed, '0') + ' used this week'
          : 'No weekly limit'
      );
    } else if (weeklyRemaining !== undefined && weeklyRemaining !== null) {
      setText(IDS.weeklyRemaining,
        _formatNumber(weeklyRemaining, '0') + ' remaining'
        + (weeklyUsed !== undefined && weeklyUsed !== null
            ? ' (' + _formatNumber(weeklyUsed, '0') + ' used)'
            : '')
      );
    } else {
      setText(IDS.weeklyRemaining, '— remaining');
    }

    // ── Monthly test limit + usage ──────────────────────────────────────
    var monthlyLimit = _pick(data, 'monthly_test_limit', 'monthlyTestLimit');
    if ((monthlyLimit === undefined) && data.plan && data.plan.monthly_test_limit !== undefined) {
      monthlyLimit = data.plan.monthly_test_limit;
    }
    var monthlyUsed      = _pick(data, 'tests_this_month', 'monthly_tests_used');
    var monthlyRemaining = _pick(data, 'monthly_tests_remaining');
    if (monthlyRemaining === undefined && monthlyLimit !== undefined && monthlyLimit !== null && monthlyUsed !== undefined && monthlyUsed !== null) {
      monthlyRemaining = Math.max(0, Number(monthlyLimit) - Number(monthlyUsed));
    }

    setText(IDS.monthlyLimit, _formatLimit(monthlyLimit));
    if (monthlyLimit === null || monthlyLimit === undefined) {
      setText(IDS.monthlyRemaining,
        (monthlyUsed !== undefined && monthlyUsed !== null)
          ? _formatNumber(monthlyUsed, '0') + ' used this month'
          : 'No monthly limit'
      );
    } else if (monthlyRemaining !== undefined && monthlyRemaining !== null) {
      setText(IDS.monthlyRemaining,
        _formatNumber(monthlyRemaining, '0') + ' remaining'
        + (monthlyUsed !== undefined && monthlyUsed !== null
            ? ' (' + _formatNumber(monthlyUsed, '0') + ' used)'
            : '')
      );
    } else {
      setText(IDS.monthlyRemaining, '— remaining');
    }

    // ── Renewal / end date ──────────────────────────────────────────────
    var renewalDate = _pick(data, 'next_renewal_date', 'renewal_date');
    var endDate     = _pick(data, 'end_date', 'expiry_date', 'expires_at');
    var displayDate = renewalDate || endDate;
    var daysToRenewal = _daysUntil(displayDate);

    var statusLower = String(status).toLowerCase();
    var renewalLabel = 'Next Renewal';
    if (statusLower === 'expired')  renewalLabel = 'Expired On';
    else if (statusLower === 'cancelled') renewalLabel = 'Access Until';
    else if (!renewalDate && endDate) renewalLabel = 'Ends On';

    setText(IDS.renewalLabel, renewalLabel);
    setText(IDS.renewalDate, _formatDate(displayDate));

    if (typeof daysToRenewal === 'number') {
      var hint = daysToRenewal === 0
        ? 'today'
        : daysToRenewal + ' day' + (daysToRenewal === 1 ? '' : 's')
            + (statusLower === 'expired' ? ' ago' : ' from now');
      setText(IDS.renewalHint, hint);
    } else {
      setText(IDS.renewalHint, '');
    }

    // ── Start date ──────────────────────────────────────────────────────
    var startDate = _pick(data, 'start_date', 'started_at', 'created_at');
    setText(IDS.startDate, _formatDate(startDate));

    // ── Billing period (only shown when present) ────────────────────────
    var billingPeriod = _pick(data, 'billing_period', 'billingPeriod');
    if (billingPeriod) {
      setText(IDS.billingPeriod, String(billingPeriod));
      show(IDS.billingPeriodItem);
    } else {
      hide(IDS.billingPeriodItem);
    }

    // ── Reveal content + alert (if applicable) ──────────────────────────
    hide(IDS.loading);
    hide(IDS.error);
    hide(IDS.empty);
    show(IDS.content);
    _renderAlertBanner(status, daysToRenewal);
  }

  // ── Public entry point ───────────────────────────────────────────────────

  /**
   * Load and render the institution subscription details.
   *
   * Calls GET /api/institution/subscription via the InstitutionAPI client,
   * then renders the page or surfaces an empty/error state. Wired to
   * DOMContentLoaded by the inline bootstrap in institution-subscription.html
   * and re-invoked by the Refresh / Retry buttons.
   *
   * Requirements: 3.7
   */
  async function loadInstitutionSubscription() {
    _renderLoading();

    if (typeof InstitutionAPI === 'undefined' || !InstitutionAPI.getSubscription) {
      _renderError('Institution module failed to load. Please refresh the page.');
      return;
    }

    try {
      var result = await InstitutionAPI.getSubscription();

      if (result && result.ok && result.data) {
        _renderSubscription(result.data);
        return;
      }

      // 404 → no institution subscription on file (empty state).
      if (result && result.status === 404) {
        _renderEmpty();
        return;
      }

      // 401 → session expired; defer to global error handler if available.
      if (result && result.status === 401) {
        if (typeof window !== 'undefined' && window.ErrorHandler) {
          window.ErrorHandler.handleApiError(
            { status: 401, message: 'HTTP 401' },
            'loadInstitutionSubscription'
          );
        }
        _renderError('Your session has expired. Please log in again.');
        return;
      }

      _renderError(
        (result && result.error) ||
        'Unable to load subscription details. Please try again later.'
      );
    } catch (err) {
      console.error('loadInstitutionSubscription failed:', err);
      _renderError('Unable to load subscription details. Please check your connection and try again.');
    }
  }

  // ── Wiring ───────────────────────────────────────────────────────────────

  function _wireButtons() {
    var refreshBtn = $(IDS.refreshBtn);
    if (refreshBtn && !refreshBtn._wired) {
      refreshBtn._wired = true;
      refreshBtn.addEventListener('click', function () {
        loadInstitutionSubscription();
      });
    }

    var retryBtn = $(IDS.retryBtn);
    if (retryBtn && !retryBtn._wired) {
      retryBtn._wired = true;
      retryBtn.addEventListener('click', function () {
        loadInstitutionSubscription();
      });
    }

    // Alert banner action button → navigate to pricing page for renewal/upgrade
    var alertBtn = $(IDS.alertActionBtn);
    if (alertBtn && !alertBtn._wired) {
      alertBtn._wired = true;
      alertBtn.addEventListener('click', function () {
        window.location.href = '/institution/pricing';
      });
    }
  }

  // Wire buttons as soon as the DOM is available; the page bootstrap also
  // invokes loadInstitutionSubscription() directly on DOMContentLoaded.
  if (typeof document !== 'undefined') {
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', _wireButtons);
    } else {
      _wireButtons();
    }
  }

  // Expose globally so the inline bootstrap in institution-subscription.html
  // can locate the function via `typeof loadInstitutionSubscription`.
  if (typeof window !== 'undefined') {
    window.loadInstitutionSubscription = loadInstitutionSubscription;
  }
})();


// ─────────────────────────────────────────────────────────────────────────────
// InstitutionStudents — Manage Students page controller (task 10.2)
// ─────────────────────────────────────────────────────────────────────────────
//
// Wires the "Invite Student" button on /institution/students to:
//   1. Call POST /api/institution/invite via InstitutionAPI.generateInvitation()
//   2. Render the generated invitation link + code into the existing
//      #invitationModal markup
//   3. Provide "Copy Link" and "Copy Code" buttons backed by the async
//      Clipboard API with a synchronous document.execCommand('copy') fallback
//      for older browsers and non-secure contexts
//   4. Display a confirmation message inside the modal for 3 seconds after
//      a successful copy (REQ-10.4, 10.5)
//
// Task 10.3 will additionally fetch and render the pending invitations table
// and add revoke handling — only invitation generation + copy lives here.
//
// Requirements: 10.2, 10.3, 10.4, 10.5

var InstitutionStudents = (function () {
  'use strict';

  // ── DOM cache (populated by init()) ──────────────────────────────────────
  var els = {
    inviteBtn: null,
    modal: null,
    closeBtn: null,
    doneBtn: null,
    linkInput: null,
    codeInput: null,
    copyLinkBtn: null,
    copyCodeBtn: null,
    feedback: null,
    pageError: null,
    pageSuccess: null,
    // Pending invitations section (task 10.3)
    invitationsLoading: null,
    invitationsEmpty: null,
    invitationsError: null,
    invitationsErrorMessage: null,
    invitationsRetryBtn: null,
    invitationsTableWrapper: null,
    invitationsTableBody: null,
  };

  // Tracks the last-focused element so focus can be restored on close.
  var lastFocusedEl = null;
  // Holds the active feedback timer so consecutive copies reset cleanly.
  var feedbackTimer = null;
  // Holds active "is-copied" timers per button.
  var buttonCopiedTimers = new WeakMap();
  // Auto-dismiss timer for the page-level success banner.
  var pageSuccessTimer = null;

  // ── Helpers ──────────────────────────────────────────────────────────────

  /**
   * Build the full invitation URL pointing at the existing
   * /invitation/accept page. Falls back to window.location.origin so the
   * link works in any environment (dev, staging, prod).
   */
  function _buildInvitationUrl(code) {
    var origin = (window.location && window.location.origin) || '';
    return origin + '/invitation/accept?code=' + encodeURIComponent(code);
  }

  /**
   * Show the invitation modal, populate fields, and trap initial focus on
   * the "Copy Link" button so keyboard users can copy immediately.
   */
  function _openModal(invitation) {
    if (!els.modal) return;

    var url = _buildInvitationUrl(invitation.code);
    if (els.linkInput) els.linkInput.value = url;
    if (els.codeInput) els.codeInput.value = invitation.code;

    // Reset previous copy state so the modal always opens clean.
    _hideFeedback();
    _resetCopyButton(els.copyLinkBtn, 'Copy Link');
    _resetCopyButton(els.copyCodeBtn, 'Copy Code');

    lastFocusedEl = document.activeElement;
    els.modal.style.display = 'flex';
    els.modal.setAttribute('aria-hidden', 'false');

    // Activate the shared focus trap (Task 18.2). The trap handles Tab
    // cycling and Escape internally — the previous setTimeout focus
    // call below remains as a no-op safety net for environments where
    // window.FocusTrap isn't loaded (e.g. older bundles).
    if (typeof window !== 'undefined' && window.FocusTrap) {
      window.FocusTrap.activate(els.modal, {
        onEscape: _closeModal,
        initialFocus: els.copyLinkBtn || null,
      });
    } else {
      // Fallback: move focus into the dialog. Defer so the browser
      // registers the visibility change before focusing.
      setTimeout(function () {
        if (els.copyLinkBtn) els.copyLinkBtn.focus();
      }, 0);
    }
  }

  function _closeModal() {
    if (!els.modal) return;
    els.modal.style.display = 'none';
    els.modal.setAttribute('aria-hidden', 'true');

    if (typeof window !== 'undefined' && window.FocusTrap) {
      window.FocusTrap.deactivate(els.modal);
    }

    _hideFeedback();

    if (lastFocusedEl && typeof lastFocusedEl.focus === 'function') {
      try { lastFocusedEl.focus(); } catch (e) { /* ignore */ }
    }
    lastFocusedEl = null;
  }

  /**
   * Display a copy confirmation message inside the modal for 3 seconds.
   * Subsequent copies cancel the previous timer so the message is always
   * shown for the full duration of the most recent copy (REQ-10.4, 10.5).
   */
  function _showFeedback(type) {
    if (!els.feedback) return;
    var message = type === 'link'
      ? '✓ Link copied to clipboard'
      : '✓ Code copied to clipboard';
    els.feedback.textContent = message;
    els.feedback.style.display = 'block';

    if (feedbackTimer) {
      clearTimeout(feedbackTimer);
      feedbackTimer = null;
    }
    feedbackTimer = setTimeout(function () {
      _hideFeedback();
    }, 3000);
  }

  function _hideFeedback() {
    if (feedbackTimer) {
      clearTimeout(feedbackTimer);
      feedbackTimer = null;
    }
    if (els.feedback) {
      els.feedback.style.display = 'none';
      els.feedback.textContent = '';
    }
  }

  /**
   * Briefly flip a copy button's label to "Copied!" so users get a
   * focus-anchored confirmation alongside the live-region message.
   */
  function _markButtonCopied(button, originalLabel) {
    if (!button) return;
    var existing = buttonCopiedTimers.get(button);
    if (existing) clearTimeout(existing);

    button.classList.add('is-copied');
    // Replace text node only — preserve the leading SVG icon.
    _setButtonText(button, 'Copied!');

    var t = setTimeout(function () {
      _resetCopyButton(button, originalLabel);
    }, 2000);
    buttonCopiedTimers.set(button, t);
  }

  function _resetCopyButton(button, originalLabel) {
    if (!button) return;
    button.classList.remove('is-copied');
    _setButtonText(button, originalLabel);
    var existing = buttonCopiedTimers.get(button);
    if (existing) {
      clearTimeout(existing);
      buttonCopiedTimers.delete(button);
    }
  }

  /**
   * Replace the trailing text node of a button (after its <svg> icon) with
   * a new label without disturbing the icon markup.
   */
  function _setButtonText(button, label) {
    if (!button) return;
    var found = false;
    for (var i = 0; i < button.childNodes.length; i++) {
      var node = button.childNodes[i];
      if (node.nodeType === Node.TEXT_NODE && node.textContent.trim().length > 0) {
        node.textContent = ' ' + label;
        found = true;
        break;
      }
    }
    if (!found) {
      // No existing label text node — append one.
      button.appendChild(document.createTextNode(' ' + label));
    }
  }

  /**
   * Copy `text` to the clipboard. Uses the async Clipboard API when
   * available (HTTPS / focused contexts) and falls back to the legacy
   * document.execCommand('copy') trick for older browsers and insecure
   * contexts. Resolves to true on success, false on failure.
   *
   * Implements the design's "Copy to Clipboard" snippet (REQ-10.4, 10.5).
   */
  async function _copyToClipboard(text) {
    if (!text) return false;

    // Modern path — Clipboard API (requires secure context in most browsers).
    if (navigator && navigator.clipboard && typeof navigator.clipboard.writeText === 'function') {
      try {
        await navigator.clipboard.writeText(text);
        return true;
      } catch (err) {
        // Fall through to the execCommand fallback.
      }
    }

    // Legacy fallback — create an off-screen <textarea>, select it, copy,
    // then remove. Works in older browsers and non-secure contexts.
    try {
      var ta = document.createElement('textarea');
      ta.value = text;
      // Position off-screen but keep it focusable / selectable.
      ta.setAttribute('readonly', '');
      ta.style.position = 'fixed';
      ta.style.top = '0';
      ta.style.left = '0';
      ta.style.width = '1px';
      ta.style.height = '1px';
      ta.style.padding = '0';
      ta.style.border = 'none';
      ta.style.outline = 'none';
      ta.style.boxShadow = 'none';
      ta.style.background = 'transparent';
      ta.style.opacity = '0';
      document.body.appendChild(ta);

      // Preserve the selection range of any active textarea/input.
      var prevActive = document.activeElement;

      ta.focus();
      ta.select();
      ta.setSelectionRange(0, ta.value.length);

      var ok = false;
      try {
        ok = document.execCommand('copy');
      } catch (e) {
        ok = false;
      }

      document.body.removeChild(ta);

      if (prevActive && typeof prevActive.focus === 'function') {
        try { prevActive.focus(); } catch (e) { /* ignore */ }
      }

      return !!ok;
    } catch (err) {
      return false;
    }
  }

  /**
   * Surface a page-level error (e.g. seats_full, max_invitations_reached)
   * via the existing #studentsPageError region. Falls back to a toast
   * notification when ErrorHandler is available so the message is still
   * visible even if the inline region is hidden.
   */
  function _showPageError(message) {
    if (els.pageError) {
      els.pageError.textContent = message;
      els.pageError.style.display = 'block';
      // Auto-dismiss after 7s to match the toast convention.
      setTimeout(function () {
        if (els.pageError && els.pageError.textContent === message) {
          els.pageError.textContent = '';
          els.pageError.style.display = 'none';
        }
      }, 7000);
    }
    if (typeof window !== 'undefined' && window.ErrorHandler && typeof window.ErrorHandler.showError === 'function') {
      window.ErrorHandler.showError(message);
    }
  }

  /**
   * Surface a page-level success message (e.g. "Invitation revoked")
   * via the existing #studentsPageSuccess region. Mirrors _showPageError
   * and uses the shared toast for consistency.
   */
  function _showPageSuccess(message) {
    if (els.pageSuccess) {
      els.pageSuccess.textContent = message;
      els.pageSuccess.style.display = 'block';
      if (pageSuccessTimer) clearTimeout(pageSuccessTimer);
      pageSuccessTimer = setTimeout(function () {
        if (els.pageSuccess && els.pageSuccess.textContent === message) {
          els.pageSuccess.textContent = '';
          els.pageSuccess.style.display = 'none';
        }
        pageSuccessTimer = null;
      }, 5000);
    }
    if (typeof window !== 'undefined' && window.ErrorHandler && typeof window.ErrorHandler.showSuccess === 'function') {
      window.ErrorHandler.showSuccess(message);
    }
  }

  // ── Pending invitations table (task 10.3) ────────────────────────────────

  /** Escape arbitrary text for safe insertion into HTML attribute/text. */
  function _escapeHtml(value) {
    if (value === null || value === undefined) return '';
    return String(value)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  /** Format an ISO date as "DD MMM YYYY" (en-IN locale). */
  function _formatInvitationDate(value) {
    if (!value) return '—';
    try {
      var d = new Date(value);
      if (isNaN(d.getTime())) return '—';
      return d.toLocaleDateString('en-IN', {
        day: 'numeric', month: 'short', year: 'numeric',
      });
    } catch (e) {
      return '—';
    }
  }

  /**
   * Pick the first non-null/non-undefined value from a list of object keys.
   * Lets us tolerate small differences in API response shape.
   */
  function _pickField(obj) {
    if (!obj) return undefined;
    for (var i = 1; i < arguments.length; i++) {
      var k = arguments[i];
      if (obj[k] !== undefined && obj[k] !== null) return obj[k];
    }
    return undefined;
  }

  /**
   * Translate the backend's invitation status slug to a user-friendly
   * label + CSS class for the status badge column.
   */
  function _invitationStatusInfo(status, expiresAt) {
    var s = (status || '').toLowerCase();
    // If still marked pending but already expired, show "Expired".
    if (s === 'pending' && expiresAt) {
      try {
        var d = new Date(expiresAt);
        if (!isNaN(d.getTime()) && d.getTime() < Date.now()) {
          return { label: 'Expired', cls: 'badge-error' };
        }
      } catch (e) { /* ignore */ }
    }
    switch (s) {
      case 'pending':  return { label: 'Pending',  cls: 'badge-warning' };
      case 'consumed': return { label: 'Consumed', cls: 'badge-active'  };
      case 'expired':  return { label: 'Expired',  cls: 'badge-error'   };
      case 'revoked':  return { label: 'Revoked',  cls: 'badge-muted'   };
      default:         return { label: status || '—', cls: 'badge-muted' };
    }
  }

  function _showInvitationsLoading() {
    if (els.invitationsLoading) els.invitationsLoading.style.display = '';
    if (els.invitationsEmpty) els.invitationsEmpty.style.display = 'none';
    if (els.invitationsError) els.invitationsError.style.display = 'none';
    if (els.invitationsTableWrapper) els.invitationsTableWrapper.style.display = 'none';
  }

  function _showInvitationsEmpty() {
    if (els.invitationsLoading) els.invitationsLoading.style.display = 'none';
    if (els.invitationsError) els.invitationsError.style.display = 'none';
    if (els.invitationsTableWrapper) els.invitationsTableWrapper.style.display = 'none';
    if (els.invitationsEmpty) els.invitationsEmpty.style.display = '';
  }

  function _showInvitationsError(message) {
    if (els.invitationsLoading) els.invitationsLoading.style.display = 'none';
    if (els.invitationsEmpty) els.invitationsEmpty.style.display = 'none';
    if (els.invitationsTableWrapper) els.invitationsTableWrapper.style.display = 'none';
    if (els.invitationsErrorMessage) {
      els.invitationsErrorMessage.textContent = message ||
        'Unable to load invitations.';
    }
    if (els.invitationsError) els.invitationsError.style.display = '';
  }

  /**
   * Render the pending invitations table. Filters out non-pending records
   * client-side as a safety net, since the table is intended only for
   * actionable (pending) invitations the admin can revoke.
   */
  function _renderInvitations(rows) {
    if (!els.invitationsTableBody || !els.invitationsTableWrapper) return;

    var list = Array.isArray(rows) ? rows : [];
    // Show only pending (and not yet expired) invitations
    var pending = list.filter(function (inv) {
      var s = String(_pickField(inv, 'status') || '').toLowerCase();
      return s === '' || s === 'pending';
    });

    if (pending.length === 0) {
      _showInvitationsEmpty();
      return;
    }

    // Sort newest first by created_at when available.
    pending.sort(function (a, b) {
      var ad = new Date(_pickField(a, 'created_at', 'createdAt') || 0).getTime();
      var bd = new Date(_pickField(b, 'created_at', 'createdAt') || 0).getTime();
      return bd - ad;
    });

    // Show total count of invitations
    var countEl = document.querySelector('[data-invitations-count]');
    if (countEl) {
      countEl.textContent = pending.length;
    }

    var html = '';
    for (var i = 0; i < pending.length; i++) {
      var inv = pending[i];
      var sequenceNumber = _pickField(inv, 'sequence_number', 'sequenceNumber');
      var code = _pickField(inv, 'code') || '';
      var createdAt = _pickField(inv, 'created_at', 'createdAt');
      var expiresAt = _pickField(inv, 'expires_at', 'expiresAt');
      var status = _pickField(inv, 'status') || 'pending';
      var info = _invitationStatusInfo(status, expiresAt);
      
      // Display invitation number
      var displayLabel = sequenceNumber ? 'Invitation #' + sequenceNumber : 'Invitation';

      html += '<tr data-code="' + _escapeHtml(code) + '">' +
        '<td><div class="code-cell-wrapper"><span class="invitation-number-label">' + _escapeHtml(displayLabel) + '</span><button type="button" class="btn-copy-code" data-code="' + _escapeHtml(code) + '" title="Copy full code" aria-label="Copy invitation code for ' + _escapeHtml(displayLabel) + '"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:16px;height:16px;" aria-hidden="true"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg></button></div></td>' +
        '<td>' + _escapeHtml(_formatInvitationDate(createdAt)) + '</td>' +
        '<td>' + _escapeHtml(_formatInvitationDate(expiresAt)) + '</td>' +
        '<td><span class="invitation-status-badge ' + info.cls + '">' +
          _escapeHtml(info.label) + '</span></td>' +
      '</tr>';
    }

    els.invitationsTableBody.innerHTML = html;
    if (els.invitationsLoading) els.invitationsLoading.style.display = 'none';
    if (els.invitationsEmpty) els.invitationsEmpty.style.display = 'none';
    if (els.invitationsError) els.invitationsError.style.display = 'none';
    els.invitationsTableWrapper.style.display = '';

    // Wire copy code buttons. Copy the full invitation code to clipboard.
    var copyButtons = els.invitationsTableBody.querySelectorAll('.btn-copy-code');
    for (var k = 0; k < copyButtons.length; k++) {
      copyButtons[k].addEventListener('click', _onCopyCodeClick);
    }
  }

  /**
   * Handle copy button click in the pending invitations table.
   * Copies the full invitation code to clipboard.
   */
  function _onCopyCodeClick(evt) {
    evt.preventDefault();
    var btn = evt.currentTarget;
    var code = btn.getAttribute('data-code');
    if (!code) return;

    navigator.clipboard.writeText(code).then(function() {
      // Visual feedback: change icon color to green briefly
      var originalColor = btn.style.color;
      btn.style.color = 'var(--green-l)';
      btn.setAttribute('title', '✓ Copied!');
      
      setTimeout(function() {
        btn.style.color = originalColor;
        btn.setAttribute('title', 'Copy full code');
      }, 2000);
    }).catch(function(err) {
      console.error('Failed to copy code:', err);
      alert('Failed to copy code. Please try again.');
    });
  }

  /**
   * Fetch and render the pending invitations list.
   *
   * Fault tolerance:
   *   • 404 from a missing list endpoint → render the empty state so the
   *     page still loads cleanly while the backend catches up.
   *   • 401 → defer to the global error handler / login redirect; show
   *     the inline error region as a fallback.
   *   • Other failures → show the inline error region with a retry button.
   *
   * Requirements: 10.9
   */
  async function _loadInvitations() {
    if (typeof InstitutionAPI === 'undefined' || !InstitutionAPI.getInvitations) {
      _showInvitationsEmpty();
      return;
    }

    _showInvitationsLoading();

    try {
      var result = await InstitutionAPI.getInvitations();

      if (result && result.ok) {
        // Accept either a bare array or a wrapped object (e.g. { invitations: [] }).
        var rows = result.data;
        if (rows && !Array.isArray(rows)) {
          rows = rows.invitations || rows.items || rows.data || [];
        }
        _renderInvitations(rows || []);
        return;
      }

      // 404 → endpoint not available yet; treat as empty state so the
      // page still renders cleanly. The admin can still create / revoke
      // invitations once individual endpoints exist.
      if (result && result.status === 404) {
        _showInvitationsEmpty();
        return;
      }

      _showInvitationsError(
        (result && result.error) ||
        'Unable to load invitations. Please try again.'
      );
    } catch (err) {
      console.error('loadInvitations failed:', err);
      _showInvitationsError(
        'Unable to load invitations. Please check your connection and try again.'
      );
    }
  }

  /**
   * Revoke a pending invitation. On success the row is removed from the
   * table and a confirmation message is shown (Requirement 10.10). On
   * the institution-specific error codes the user gets a clear message
   * via _showPageError (which falls back to a toast).
   */
  async function _onRevokeClick(e) {
    var button = e.currentTarget;
    if (!button) return;
    var code = button.getAttribute('data-code');
    if (!code) return;
    if (button.disabled) return;

    // Light confirmation prompt — revocation is destructive but cheap.
    var ok = (typeof window !== 'undefined' && typeof window.confirm === 'function')
      ? window.confirm('Revoke this invitation? The link will no longer be usable.')
      : true;
    if (!ok) return;

    button.disabled = true;
    button.setAttribute('aria-busy', 'true');
    var originalLabel = button.textContent;
    button.textContent = 'Revoking…';

    try {
      var result = await InstitutionAPI.revokeInvitation(code);

      if (result && result.ok) {
        // Remove the row optimistically — the backend has already
        // marked the invitation as non-redeemable.
        var row = button.closest('tr');
        if (row && row.parentNode) row.parentNode.removeChild(row);

        // If the table is now empty, swap to the empty state.
        if (els.invitationsTableBody && els.invitationsTableBody.children.length === 0) {
          _showInvitationsEmpty();
        }

        _showPageSuccess('Invitation revoked');
        return;
      }

      // Map the most common backend errors to user-friendly messages.
      // Status codes follow the design: 404 invalid_invitation, 403/409
      // for institution-specific business rule failures.
      var msg;
      if (result && result.errorCode === 'max_invitations_reached') {
        msg = 'You have reached the maximum of 50 pending invitations. ' +
              'Please wait for students to accept existing invitations or let them expire.';
      } else if (result && result.errorCode === 'seats_full') {
        msg = 'Your institution has reached its maximum student capacity. ' +
              'Upgrade your plan or remove students to invite more.';
      } else if (result && result.status === 404) {
        // Invitation already gone — treat as success and refresh the list.
        _showPageSuccess('Invitation no longer exists');
        await _loadInvitations();
        return;
      } else {
        msg = (result && result.error) ||
              'Unable to revoke invitation. Please try again.';
      }
      _showPageError(msg);
    } catch (err) {
      console.error('revokeInvitation failed:', err);
      _showPageError('Unable to revoke invitation. Please check your connection and try again.');
    } finally {
      button.disabled = false;
      button.setAttribute('aria-busy', 'false');
      button.textContent = originalLabel;
    }
  }

  // ── Event handlers ───────────────────────────────────────────────────────

  async function _onInviteClick() {
    if (!els.inviteBtn) return;
    if (els.inviteBtn.disabled) return;

    els.inviteBtn.disabled = true;
    els.inviteBtn.setAttribute('aria-busy', 'true');
    var originalLabel = els.inviteBtn.getAttribute('data-original-label');
    if (!originalLabel) {
      // Capture the original label once so we can restore it.
      originalLabel = els.inviteBtn.textContent.trim();
      els.inviteBtn.setAttribute('data-original-label', originalLabel);
    }
    // Surface an in-flight indicator so the admin can see the request is
    // being processed (Requirement 14.10). The button is also disabled,
    // which prevents duplicate POSTs to /api/institution/invite.
    els.inviteBtn.textContent = 'Generating…';

    try {
      var result = await InstitutionAPI.generateInvitation();

      if (result && result.ok && result.data && result.data.code) {
        _openModal(result.data);
        // Surface a success toast (Requirement 14.3) so the admin gets
        // the same affordance as other subscription actions even though
        // the modal already shows the generated link/code.
        _showPageSuccess('Invitation generated');
        // Refresh the pending invitations table so the new code shows up
        // without requiring a manual page reload (Requirement 10.9).
        _loadInvitations();
      } else {
        // Surface the API client's mapped error message; falls back to
        // a generic message when no error string is provided.
        var msg = (result && result.error)
          ? result.error
          : 'Unable to generate invitation. Please try again.';
        _showPageError(msg);
      }
    } catch (err) {
      _showPageError('Unable to generate invitation. Please try again.');
    } finally {
      els.inviteBtn.disabled = false;
      els.inviteBtn.setAttribute('aria-busy', 'false');
      els.inviteBtn.textContent = originalLabel;
    }
  }

  async function _onCopyClick(e) {
    var button = e.currentTarget;
    if (!button) return;
    var type = button.getAttribute('data-copy') || 'link';
    var text = type === 'link'
      ? (els.linkInput && els.linkInput.value)
      : (els.codeInput && els.codeInput.value);

    if (!text) return;

    var ok = await _copyToClipboard(text);
    if (ok) {
      _showFeedback(type);
      _markButtonCopied(
        button,
        type === 'link' ? 'Copy Link' : 'Copy Code'
      );
    } else {
      // Last-resort UX: select the text in the input so the user can
      // manually copy it. This matches the design's "Display text for
      // manual copying if both methods fail" risk fallback.
      var input = type === 'link' ? els.linkInput : els.codeInput;
      if (input && typeof input.select === 'function') {
        input.focus();
        input.select();
      }
      if (typeof window !== 'undefined' && window.ErrorHandler && typeof window.ErrorHandler.showError === 'function') {
        window.ErrorHandler.showError(
          'Unable to copy automatically. The text has been selected — press Ctrl+C / Cmd+C to copy.'
        );
      }
    }
  }

  function _onModalKeydown(e) {
    if (e.key === 'Escape' || e.keyCode === 27) {
      e.preventDefault();
      _closeModal();
    }
  }

  function _onOverlayClick(e) {
    // Close only when the click lands on the overlay itself, not the dialog.
    if (e.target === els.modal) {
      _closeModal();
    }
  }

  // ── Public API ───────────────────────────────────────────────────────────

  /**
   * Initialise the Manage Students page. Idempotent — safe to call
   * multiple times (e.g. after dynamic page reloads).
   */
  function init() {
    els.inviteBtn = document.getElementById('inviteStudentBtn');
    els.modal = document.getElementById('invitationModal');
    els.closeBtn = document.getElementById('invitationModalCloseBtn');
    els.doneBtn = document.getElementById('invitationModalDoneBtn');
    els.linkInput = document.getElementById('invitationLinkInput');
    els.codeInput = document.getElementById('invitationCodeInput');
    els.copyLinkBtn = document.getElementById('copyLinkBtn');
    els.copyCodeBtn = document.getElementById('copyCodeBtn');
    els.feedback = document.getElementById('invitationCopyFeedback');
    els.pageError = document.getElementById('studentsPageError');
    els.pageSuccess = document.getElementById('studentsPageSuccess');

    // Pending invitations section (task 10.3)
    els.invitationsLoading = document.getElementById('invitationsLoading');
    els.invitationsEmpty = document.getElementById('invitationsEmpty');
    els.invitationsError = document.getElementById('invitationsError');
    els.invitationsErrorMessage = document.getElementById('invitationsErrorMessage');
    els.invitationsRetryBtn = document.getElementById('invitationsRetryBtn');
    els.invitationsTableWrapper = document.getElementById('invitationsTableWrapper');
    els.invitationsTableBody = document.getElementById('invitationsTableBody');

    if (els.inviteBtn && !els.inviteBtn._inviteHandlerAttached) {
      els.inviteBtn.addEventListener('click', _onInviteClick);
      els.inviteBtn._inviteHandlerAttached = true;
    }

    if (els.copyLinkBtn && !els.copyLinkBtn._copyHandlerAttached) {
      els.copyLinkBtn.addEventListener('click', _onCopyClick);
      els.copyLinkBtn._copyHandlerAttached = true;
    }

    if (els.copyCodeBtn && !els.copyCodeBtn._copyHandlerAttached) {
      els.copyCodeBtn.addEventListener('click', _onCopyClick);
      els.copyCodeBtn._copyHandlerAttached = true;
    }

    if (els.closeBtn && !els.closeBtn._closeHandlerAttached) {
      els.closeBtn.addEventListener('click', _closeModal);
      els.closeBtn._closeHandlerAttached = true;
    }

    if (els.doneBtn && !els.doneBtn._closeHandlerAttached) {
      els.doneBtn.addEventListener('click', _closeModal);
      els.doneBtn._closeHandlerAttached = true;
    }

    if (els.modal && !els.modal._modalHandlerAttached) {
      els.modal.addEventListener('click', _onOverlayClick);
      els.modal.addEventListener('keydown', _onModalKeydown);
      els.modal._modalHandlerAttached = true;
    }

    // Wire the invitations-table retry button so the user can recover
    // from transient load failures without a full page reload.
    if (els.invitationsRetryBtn && !els.invitationsRetryBtn._retryHandlerAttached) {
      els.invitationsRetryBtn.addEventListener('click', function () {
        _loadInvitations();
      });
      els.invitationsRetryBtn._retryHandlerAttached = true;
    }

    // Kick off the initial load of pending invitations (task 10.3).
    if (els.invitationsTableBody) {
      _loadInvitations();
    }
  }

  /**
   * Programmatically trigger the invite flow. Exposed so other components
   * (e.g. a "Quick action: Invite Student" button on the dashboard) can
   * reuse the same modal and clipboard flow without duplicating logic.
   */
  async function generateInvitation() {
    return _onInviteClick();
  }

  return {
    init: init,
    generateInvitation: generateInvitation,
    loadInvitations: _loadInvitations,
    // Exposed for unit tests / property tests (task 10.4).
    _copyToClipboard: _copyToClipboard,
    _buildInvitationUrl: _buildInvitationUrl,
  };
})();

// Expose globally so the page bootstrap script can call init().
if (typeof window !== 'undefined') {
  window.InstitutionStudents = InstitutionStudents;
}


// ─────────────────────────────────────────────────────────────────────────────
// loadInstitutionDashboard — Institution Dashboard page controller
// (tasks 9.2 + 9.3)
// ─────────────────────────────────────────────────────────────────────────────
//
// Fetches institution dashboard data from GET /api/institution/dashboard and
// renders:
//   • KPI tiles (Total Students, Tests This Week, Tests This Month,
//     Subscription Status) — Requirements 9.2, 9.3
//   • Recent Activity table with the 10 most recent exam submissions —
//     Requirement 9.4
//   • Alert banner for overdue / grace_period / expired subscription states —
//     Requirements 9.6, 9.7
//   • Error state + Retry button when the API call fails — Requirement 9.9
//   • Auto-refresh every 60 seconds with a Page-Visibility-aware pause and
//     a "Last updated: X seconds ago" ticker that updates every second —
//     Requirement 9.10 (task 9.3)
//
// The function is exposed globally as `loadInstitutionDashboard` so the inline
// bootstrap in institution-dashboard.html can invoke it on DOMContentLoaded.
//
// Requirements: 9.2, 9.6, 9.7, 9.9, 9.10

(function () {
  'use strict';

  // ── DOM id map (kept in sync with institution-dashboard.html) ────────────

  var IDS = {
    // State containers
    loading:              'dashboardLoading',
    error:                'dashboardError',
    errorMessage:         'dashboardErrorMessage',
    retryBtn:             'retryDashboardBtn',
    refreshBtn:           'refreshDashboardBtn',
    content:              'dashboardContent',
    lastUpdated:          'lastUpdated',
    institutionName:      'institutionName',

    // Alert banner (overdue / grace_period / expired)
    alertBanner:          'subscriptionAlertBanner',
    alertTitle:           'alertTitle',
    alertMessage:         'alertMessage',
    alertActionBtn:       'alertActionBtn',

    // KPI tiles
    kpiTotalStudents:     'kpiTotalStudents',
    kpiTestsThisWeek:     'kpiTestsThisWeek',
    kpiTestsThisMonth:    'kpiTestsThisMonth',
    kpiSubscriptionStatus:'kpiSubscriptionStatus',
    kpiTileStatus:        'kpiTileStatus',

    // Recent activity
    recentActivityEmpty:  'recentActivityEmpty',
    recentActivityWrapper:'recentActivityWrapper',
    recentActivityBody:   'recentActivityBody',
  };

  // Maximum number of recent submissions to render (Requirement 9.4).
  var RECENT_ACTIVITY_LIMIT = 10;

  // ── DOM helpers ──────────────────────────────────────────────────────────

  function $(id)              { return document.getElementById(id); }
  function show(id, display)  { var el = $(id); if (el) el.style.display = display || ''; }
  function hide(id)           { var el = $(id); if (el) el.style.display = 'none'; }
  function setText(id, text)  { var el = $(id); if (el) el.textContent = text; }

  /**
   * Escape a value for safe insertion as an HTML text node. Used when
   * building the recent activity table rows via innerHTML so we never
   * trust API payload strings (student names, subjects).
   */
  function _escapeHtml(value) {
    if (value === null || value === undefined) return '';
    return String(value)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  // ── Formatting helpers ───────────────────────────────────────────────────

  /**
   * Format an ISO date string as "DD MMM YYYY, HH:MM" (en-IN locale) for
   * the recent activity table. Falls back to the raw value if parsing
   * fails so the user always sees something.
   */
  function _formatDateTime(value) {
    if (!value) return '—';
    try {
      var d = new Date(value);
      if (isNaN(d.getTime())) return '—';
      var datePart = d.toLocaleDateString('en-IN', {
        day: 'numeric', month: 'short', year: 'numeric',
      });
      var timePart = d.toLocaleTimeString('en-IN', {
        hour: '2-digit', minute: '2-digit', hour12: true,
      });
      return datePart + ' · ' + timePart;
    } catch (e) {
      return String(value);
    }
  }

  /**
   * Convert a duration in seconds (the canonical `time_taken_sec` field on
   * student submissions) into a human-friendly "Xm Ys" string.
   */
  function _formatTimeTaken(seconds) {
    if (seconds === null || seconds === undefined) return '—';
    var total = Number(seconds);
    if (isNaN(total) || total < 0) return '—';
    total = Math.floor(total);
    var minutes = Math.floor(total / 60);
    var secs = total % 60;
    if (minutes === 0) return secs + 's';
    return minutes + 'm ' + secs + 's';
  }

  /**
   * Render a "used / limit" string for KPI tiles. Treats null/undefined
   * limits as "Unlimited" (consistent with the institution subscription
   * page) and ensures the used count always renders as a non-negative
   * number.
   */
  function _formatUsageOverLimit(used, limit) {
    var u = (used === null || used === undefined) ? 0 : Number(used);
    if (isNaN(u) || u < 0) u = 0;
    if (limit === null || limit === undefined) {
      return u + ' / Unlimited';
    }
    var l = Number(limit);
    if (isNaN(l)) return String(u);
    return u + ' / ' + l;
  }

  /**
   * Render a "X of Y" string for the Total Students KPI. Mirrors the design
   * for the seat-usage tile on the institution subscription page.
   */
  function _formatStudentsOfMax(total, max) {
    var t = (total === null || total === undefined) ? 0 : Number(total);
    if (isNaN(t) || t < 0) t = 0;
    if (max === null || max === undefined) return String(t);
    var m = Number(max);
    if (isNaN(m)) return String(t);
    return t + ' / ' + m;
  }

  /**
   * Status label + tile-class for the Subscription Status KPI tile.
   * When status is null, returns "No active subscription" with inactive key.
   */
  function _statusInfo(status) {
    // Handle null/undefined status explicitly
    if (status === null || status === undefined) {
      return { label: 'No active subscription', key: 'inactive' };
    }
    
    switch ((status || '').toLowerCase()) {
      case 'trial':        return { label: 'Active',       key: 'active'       };
      case 'active':       return { label: 'Active',       key: 'active'       };
      case 'overdue':      return { label: 'Overdue',      key: 'overdue'      };
      case 'grace_period': return { label: 'Grace Period', key: 'grace_period' };
      case 'expired':      return { label: 'Expired',      key: 'expired'      };
      case 'cancelled':    return { label: 'Cancelled',    key: 'expired'      };
      default:             return { label: status || '—',  key: 'active'       };
    }
  }

  /**
   * Whole days from now until the given ISO date. Returns null when the
   * value is missing/unparseable; never returns negative numbers (clamped
   * to 0) so the alert banner copy stays sensible.
   */
  function _daysUntil(value) {
    if (!value) return null;
    try {
      var d = new Date(value);
      if (isNaN(d.getTime())) return null;
      var diffMs = d.getTime() - Date.now();
      var days = Math.ceil(diffMs / (1000 * 60 * 60 * 24));
      return days < 0 ? 0 : days;
    } catch (e) {
      return null;
    }
  }

  /** Current time as "Last updated: HH:MM:SS". */
  function _nowTimestamp() {
    try {
      return 'Last updated: ' + new Date().toLocaleTimeString();
    } catch (e) {
      return 'Last updated: just now';
    }
  }

  // ── Auto-refresh + relative-time ticker (task 9.3, Requirement 9.10) ─────
  //
  // The dashboard refreshes every 60 seconds while the tab is visible and
  // pauses entirely while it is hidden (Page Visibility API), so we don't
  // burn API calls on background tabs. Whenever the tab becomes visible
  // again we run an immediate refresh so the user sees fresh data on
  // return, then restart the 60-second interval.
  //
  // Independently, a 1-second ticker re-renders the "Last updated: X
  // seconds ago" label so the timestamp is always accurate without
  // requiring a full data refresh. The ticker also pauses while the tab
  // is hidden.

  var REFRESH_INTERVAL_MS = 60 * 1000; // 60 seconds (Requirement 9.10)
  var TIMESTAMP_TICK_MS   = 1000;      // Update relative time every second

  // Timestamp (ms since epoch) of the last successful render. Drives the
  // relative-time label. Null until the first successful load.
  var _lastUpdatedAt = null;

  // Handles for the two intervals so we can stop them on visibility change.
  var _refreshTimer = null;
  var _tickTimer = null;

  // Tracks whether auto-refresh is currently armed. We only stop/restart
  // the interval when the user has actually started auto-refresh (i.e.
  // after the first successful load wired from `loadInstitutionDashboard`).
  var _autoRefreshActive = false;

  // Set to true while a refresh is already in flight so the visibility
  // and interval handlers don't stack concurrent fetches on top of each
  // other (e.g. when the user toggles tabs rapidly).
  var _refreshInFlight = false;

  /**
   * Format a duration (in milliseconds) as a short human-readable
   * "Last updated: …" label. Mirrors the conventions used elsewhere on
   * the platform (Hindi/Arabic numerals, en-IN locale-friendly).
   *
   * Examples:
   *   0–4s     → "Last updated: just now"
   *   5–59s    → "Last updated: 12 seconds ago"
   *   60s+     → "Last updated: 3 minutes ago"
   *   1h+      → "Last updated: 2 hours ago"
   *   24h+     → "Last updated: 3 days ago"
   */
  function _formatRelativeTime(deltaMs) {
    if (deltaMs === null || deltaMs === undefined || isNaN(deltaMs) || deltaMs < 0) {
      deltaMs = 0;
    }
    var seconds = Math.floor(deltaMs / 1000);
    if (seconds < 5)  return 'Last updated: just now';
    if (seconds < 60) return 'Last updated: ' + seconds + ' seconds ago';

    var minutes = Math.floor(seconds / 60);
    if (minutes === 1) return 'Last updated: 1 minute ago';
    if (minutes < 60)  return 'Last updated: ' + minutes + ' minutes ago';

    var hours = Math.floor(minutes / 60);
    if (hours === 1)  return 'Last updated: 1 hour ago';
    if (hours < 24)   return 'Last updated: ' + hours + ' hours ago';

    var days = Math.floor(hours / 24);
    if (days === 1)   return 'Last updated: 1 day ago';
    return 'Last updated: ' + days + ' days ago';
  }

  /**
   * Re-render the relative-time label using `_lastUpdatedAt` as the
   * anchor. Safe to call before the first successful load — it leaves
   * the placeholder ("Last updated: —") untouched in that case.
   */
  function _updateRelativeTimestamp() {
    if (_lastUpdatedAt === null) return;
    setText(IDS.lastUpdated, _formatRelativeTime(Date.now() - _lastUpdatedAt));
  }

  /**
   * Start the 1-second ticker that keeps the "Last updated: …" label in
   * sync with wall-clock time. Idempotent.
   */
  function _startTimestampTicker() {
    if (_tickTimer !== null) return;
    _tickTimer = setInterval(_updateRelativeTimestamp, TIMESTAMP_TICK_MS);
  }

  /**
   * Stop the relative-time ticker. Safe to call when the ticker is not
   * running.
   */
  function _stopTimestampTicker() {
    if (_tickTimer === null) return;
    clearInterval(_tickTimer);
    _tickTimer = null;
  }

  /**
   * Start the 60-second auto-refresh interval. Pulls fresh data from the
   * dashboard endpoint on each tick. Concurrent fetches are coalesced
   * via `_refreshInFlight`. Idempotent.
   */
  function _startRefreshTimer() {
    if (_refreshTimer !== null) return;
    _refreshTimer = setInterval(function () {
      // Defensive: if the tab became hidden between visibility events
      // and this tick (e.g. background throttling lag), skip.
      if (typeof document !== 'undefined' && document.hidden) return;
      _refreshDashboard();
    }, REFRESH_INTERVAL_MS);
  }

  /** Stop the 60-second auto-refresh interval. */
  function _stopRefreshTimer() {
    if (_refreshTimer === null) return;
    clearInterval(_refreshTimer);
    _refreshTimer = null;
  }

  /**
   * Fetch fresh dashboard data without flipping the page back into the
   * loading state — used by the auto-refresh interval and the visibility
   * "wake up" handler. Errors are swallowed silently so a transient
   * network blip on a background refresh doesn't replace the existing
   * dashboard with an error screen.
   */
  async function _refreshDashboard() {
    if (_refreshInFlight) return;
    if (typeof InstitutionAPI === 'undefined' || !InstitutionAPI.getDashboard) return;

    _refreshInFlight = true;
    try {
      var result = await InstitutionAPI.getDashboard();
      if (result && result.ok && result.data) {
        _renderDashboard(result.data);
      }
      // Non-OK responses (e.g. 401 session expired) are ignored here so
      // the user keeps the last-known-good dashboard until they take an
      // explicit action (clicking Refresh / navigating). The next manual
      // refresh path will surface the error normally.
    } catch (err) {
      // Background-refresh failures should not be disruptive.
      console.warn('Dashboard auto-refresh failed:', err);
    } finally {
      _refreshInFlight = false;
    }
  }

  /**
   * Visibility change handler.
   *
   * • Tab hidden  → stop both the refresh timer and the relative-time
   *                 ticker so we don't waste cycles or burn API calls
   *                 on a background tab.
   * • Tab visible → kick off an immediate refresh (so the user sees
   *                 fresh data on return), restart the 60-second
   *                 interval, and resume the 1-second ticker.
   */
  function _handleVisibilityChange() {
    if (!_autoRefreshActive) return;

    if (document.hidden) {
      _stopRefreshTimer();
      _stopTimestampTicker();
    } else {
      // Refresh immediately so the dashboard isn't stale after the user
      // returns. We don't await this — the visibility handler should
      // remain synchronous so the browser doesn't hold us back.
      _refreshDashboard();
      _startRefreshTimer();
      _startTimestampTicker();
      // Update the label once now so the user sees the correct value
      // before the first 1-second tick.
      _updateRelativeTimestamp();
    }
  }

  /**
   * Arm the auto-refresh subsystem. Called once after the first
   * successful render. Idempotent: subsequent calls only restart timers
   * when the tab is visible.
   */
  function _startAutoRefresh() {
    if (_autoRefreshActive) {
      // Already armed — just make sure timers are running for the
      // current visibility state.
      if (typeof document !== 'undefined' && !document.hidden) {
        _startRefreshTimer();
        _startTimestampTicker();
      }
      return;
    }

    _autoRefreshActive = true;

    if (typeof document !== 'undefined') {
      document.addEventListener('visibilitychange', _handleVisibilityChange);
      if (!document.hidden) {
        _startRefreshTimer();
        _startTimestampTicker();
      }
    } else {
      _startRefreshTimer();
      _startTimestampTicker();
    }

    // Cleanup on navigation away / tab close. We listen on `pagehide`
    // (preferred over `beforeunload` — fires reliably for bfcache,
    // mobile Safari, and modern Chromium) so the 60-second refresh and
    // 1-second ticker don't keep doing work while the page is being
    // torn down or frozen into the back/forward cache.
    if (typeof window !== 'undefined') {
      window.addEventListener('pagehide', _stopAutoRefresh);
    }
  }

  /**
   * Tear down the auto-refresh subsystem. Stops both intervals and
   * removes the visibility listener so we leave no timers behind on
   * page unload (Requirement 9.10 — cleanup on unload).
   */
  function _stopAutoRefresh() {
    _stopRefreshTimer();
    _stopTimestampTicker();
    if (typeof document !== 'undefined') {
      document.removeEventListener('visibilitychange', _handleVisibilityChange);
    }
    _autoRefreshActive = false;
  }

  /**
   * Pick the first defined value from a list of keys on the payload.
   * Mirrors the helper used by loadInstitutionSubscription so we tolerate
   * minor differences between the two API response shapes.
   */
  function _pick(data) {
    for (var i = 1; i < arguments.length; i++) {
      var key = arguments[i];
      if (data && data[key] !== undefined && data[key] !== null) return data[key];
    }
    return undefined;
  }

  // ── State helpers ────────────────────────────────────────────────────────

  function _renderLoading() {
    show(IDS.loading);
    hide(IDS.error);
    hide(IDS.content);
    hide(IDS.alertBanner);
  }

  function _renderError(message) {
    hide(IDS.loading);
    hide(IDS.content);
    hide(IDS.alertBanner);
    setText(IDS.errorMessage, message || 'Please check your connection and try again.');
    show(IDS.error);
  }

  // ── Alert banner (Requirements 9.6, 9.7) ─────────────────────────────────

  /**
   * Surface a top-of-page alert banner when the institution subscription
   * is overdue, in a grace period, expired, or cancelled. The banner
   * already lives in the HTML — we just toggle visibility, fill in the
   * status-specific copy, and choose an appropriate CTA label.
   *
   * For "expired" / "cancelled" states the banner remains inline (the
   * dashboard error state covers truly fatal cases); the visual urgency
   * is conveyed by the `data-status` attribute (red treatment).
   *
   * For newly registered institutions with no subscription yet (status = null),
   * no alert is displayed.
   */
  function _renderAlertBanner(status, daysRemaining) {
    var banner = $(IDS.alertBanner);
    if (!banner) return;

    var s = (status || '').toLowerCase();
    var titleText = '';
    var messageText = '';
    var actionText = 'Pay Now';

    if (!status) {
      // No subscription yet (newly registered) — no alert needed.
      hide(IDS.alertBanner);
      return;
    } else if (s === 'overdue' || s === 'grace_period') {
      titleText = 'Payment Overdue';
      messageText = (typeof daysRemaining === 'number' && daysRemaining >= 0)
        ? "Your institution's access will be suspended in " +
          daysRemaining + ' day' + (daysRemaining === 1 ? '' : 's') + '.'
        : "Your institution's access will be suspended soon.";
      actionText = 'Pay Now';
    } else if (s === 'expired') {
      titleText = 'Subscription Expired';
      messageText = "Your institution's subscription has expired. Renew to restore access for your students.";
      actionText = 'Renew Subscription';
    } else if (s === 'cancelled') {
      titleText = 'Subscription Cancelled';
      messageText = "Your institution's subscription has been cancelled. Reactivate to restore access.";
      actionText = 'Reactivate';
    } else {
      // Active / trial → no alert needed.
      hide(IDS.alertBanner);
      return;
    }

    setText(IDS.alertTitle, titleText);
    setText(IDS.alertMessage, messageText);

    var btn = $(IDS.alertActionBtn);
    if (btn) btn.textContent = actionText;

    banner.setAttribute('data-status', s);
    banner.style.display = 'flex';
  }

  // ── KPI tiles (Requirements 9.2, 9.3) ────────────────────────────────────

  function _renderKpis(data) {
    // Total Students — "X of max" or "X" when max is not provided.
    var totalStudents = _pick(data, 'total_students', 'totalStudents');
    var maxStudents   = _pick(data, 'max_students', 'maxStudents', 'max_student_seats');
    setText(IDS.kpiTotalStudents, _formatStudentsOfMax(totalStudents, maxStudents));

    // Tests This Week — "X of weekly_test_limit" or "X / Unlimited".
    var testsThisWeek    = _pick(data, 'tests_this_week', 'testsThisWeek');
    var weeklyTestLimit  = _pick(data, 'weekly_test_limit', 'weeklyTestLimit');
    setText(IDS.kpiTestsThisWeek, _formatUsageOverLimit(testsThisWeek, weeklyTestLimit));

    // Tests This Month — "X of monthly_test_limit" or "X / Unlimited".
    var testsThisMonth   = _pick(data, 'tests_this_month', 'testsThisMonth');
    var monthlyTestLimit = _pick(data, 'monthly_test_limit', 'monthlyTestLimit');
    setText(IDS.kpiTestsThisMonth, _formatUsageOverLimit(testsThisMonth, monthlyTestLimit));

    // Subscription Status — label + status-coloured tile via data-status.
    var status = _pick(data, 'subscription_status', 'status');
    var info = _statusInfo(status);  // This will handle null/undefined properly
    setText(IDS.kpiSubscriptionStatus, info.label);
    var tile = $(IDS.kpiTileStatus);
    if (tile) tile.setAttribute('data-status', info.key);
  }

  // ── Recent Activity table (Requirement 9.4) ──────────────────────────────

  /**
   * Render the 10 most recent exam submissions into the activity table.
   * Toggles between the table and an empty-state message when the API
   * returns no submissions.
   */
  function _renderRecentActivity(submissions) {
    var list = Array.isArray(submissions) ? submissions.slice(0, RECENT_ACTIVITY_LIMIT) : [];

    var emptyEl = $(IDS.recentActivityEmpty);
    var wrapperEl = $(IDS.recentActivityWrapper);
    var tbody = $(IDS.recentActivityBody);

    if (!tbody) return;

    if (list.length === 0) {
      tbody.innerHTML = '';
      if (wrapperEl) wrapperEl.style.display = 'none';
      if (emptyEl) emptyEl.style.display = 'block';
      return;
    }

    if (emptyEl) emptyEl.style.display = 'none';
    if (wrapperEl) wrapperEl.style.display = '';

    var rows = list.map(function (sub) {
      var name = _pick(sub, 'student_name', 'studentName', 'name') || '—';
      var subject = _pick(sub, 'subject') || '—';
      var scoreRaw = _pick(sub, 'score', 'score_pct', 'scorePct');
      var score;
      if (scoreRaw === null || scoreRaw === undefined) {
        score = '—';
      } else {
        var n = Number(scoreRaw);
        score = isNaN(n) ? '—' : Math.round(n) + '%';
      }
      var date = _formatDateTime(_pick(sub, 'date', 'submitted_at', 'submittedAt'));
      var timeTaken = _formatTimeTaken(_pick(sub, 'time_taken', 'time_taken_sec', 'timeTakenSec'));

      // Apply a colour-coded badge to the score, matching the patterns
      // used on the student dashboard / admin analytics tables.
      var scoreCls = '';
      if (typeof scoreRaw === 'number' || (scoreRaw !== null && scoreRaw !== undefined && !isNaN(Number(scoreRaw)))) {
        var p = Math.round(Number(scoreRaw));
        scoreCls = p >= 70 ? 'score-high' : (p >= 40 ? 'score-mid' : 'score-low');
      }

      return '<tr>'
        + '<td>' + _escapeHtml(name) + '</td>'
        + '<td>' + _escapeHtml(subject) + '</td>'
        + '<td>' + (scoreCls
            ? '<span class="score-badge ' + scoreCls + '">' + _escapeHtml(score) + '</span>'
            : _escapeHtml(score)) + '</td>'
        + '<td>' + _escapeHtml(date) + '</td>'
        + '<td>' + _escapeHtml(timeTaken) + '</td>'
        + '</tr>';
    }).join('');

    tbody.innerHTML = rows;
  }

  // ── Main renderer ────────────────────────────────────────────────────────

  function _renderDashboard(data) {
    if (!data || typeof data !== 'object') {
      _renderError('Dashboard data was empty or malformed.');
      return;
    }

    // Optional: institution name in page sub-header.
    var institutionName = _pick(data, 'institution_name', 'institutionName');
    if (institutionName) {
      var instEl = $(IDS.institutionName);
      if (instEl) instEl.textContent = institutionName;
    }

    _renderKpis(data);

    var submissions = _pick(data, 'recent_submissions', 'recentSubmissions') || [];
    _renderRecentActivity(submissions);

    var status = _pick(data, 'subscription_status', 'status');
    var renewalDate = _pick(data, 'next_renewal_date', 'nextRenewalDate');
    var daysRemaining = _daysUntil(renewalDate);
    _renderAlertBanner(status, daysRemaining);

    // Stamp the render time and refresh the relative-time label. The
    // 1-second ticker (started by _startAutoRefresh) keeps this label
    // updated thereafter without us having to re-render the dashboard.
    _lastUpdatedAt = Date.now();
    _updateRelativeTimestamp();

    hide(IDS.loading);
    hide(IDS.error);
    show(IDS.content);

    // Dashboard is always visible, even without subscription.
    // Access control to features (upload, questions, exams, etc.) is handled by
    // institution-access-control.js which blocks access when trying to navigate to
    // protected pages. Users can view dashboard KPIs and alerts but cannot use
    // feature pages until they have an active subscription.
  }

  /**
   * Show the subscription selection modal when institution has no active subscription.
   * Modal is non-dismissible (cannot close without selecting a plan).
   */
  function _showSubscriptionModal() {
    // Fade out the dashboard content and show modal overlay
    var contentEl = $(IDS.content);
    if (contentEl) {
      contentEl.style.opacity = '0.3';
      contentEl.style.pointerEvents = 'none';
    }

    // Create modal overlay if it doesn't exist
    var existingOverlay = document.getElementById('institutionSubscriptionBlocker');
    if (!existingOverlay) {
      var overlay = document.createElement('div');
      overlay.id = 'institutionSubscriptionBlocker';
      overlay.style.cssText = `
        position: fixed;
        inset: 0;
        background: rgba(0, 0, 0, 0.75);
        backdrop-filter: blur(8px);
        z-index: 300;
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 20px;
      `;

      var dialog = document.createElement('div');
      dialog.style.cssText = `
        background: var(--s1);
        border: 1px solid var(--border2);
        border-radius: 14px;
        padding: 36px;
        max-width: 480px;
        width: 100%;
        box-shadow: 0 24px 60px rgba(0, 0, 0, 0.45);
      `;
      dialog.innerHTML = `
        <div style="text-align: center; margin-bottom: 28px;">
          <div style="font-size: 2.8rem; margin-bottom: 12px;">📋</div>
          <h2 style="font-size: 1.4rem; font-weight: 800; margin: 0 0 6px;">No Active Subscription</h2>
          <p style="color: var(--muted); font-size: 0.88rem; margin: 0;">Please select a subscription plan to access features</p>
        </div>
        <div style="display: flex; flex-direction: column; gap: 12px;">
          <button class="btn-institution" style="width: 100%; display: flex; align-items: center; justify-content: center; gap: 8px;" id="selectPlanBtn">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width: 16px; height: 16px;"><rect x="2" y="5" width="20" height="14" rx="2"/><line x1="2" y1="10" x2="22" y2="10"/></svg>
            Select a Plan
          </button>
        </div>
      `;

      overlay.appendChild(dialog);
      document.body.appendChild(overlay);

      // Wire the select plan button
      var selectBtn = document.getElementById('selectPlanBtn');
      if (selectBtn) {
        selectBtn.addEventListener('click', function () {
          // Navigate to subscription management page
          window.location.href = '/institution/subscription';
        });
      }
    } else {
      existingOverlay.style.display = 'flex';
    }
  }

  // ── Public entry point ───────────────────────────────────────────────────

  /**
   * Load and render the institution dashboard.
   *
   * Calls GET /api/institution/dashboard via InstitutionAPI, renders the
   * KPI tiles, recent activity table, and any subscription alert banner,
   * or surfaces an error state with a Retry button when the call fails.
   *
   * Wired to DOMContentLoaded by the inline bootstrap in
   * institution-dashboard.html and re-invoked by the Refresh / Retry
   * buttons.
   *
   * Requirements: 9.2, 9.6, 9.7, 9.9
   */
  async function loadInstitutionDashboard() {
    _renderLoading();

    if (typeof InstitutionAPI === 'undefined' || !InstitutionAPI.getDashboard) {
      _renderError('Institution module failed to load. Please refresh the page.');
      return;
    }

    try {
      var result = await InstitutionAPI.getDashboard();

      if (result && result.ok && result.data) {
        _renderDashboard(result.data);
        // Arm auto-refresh after the first successful render so the
        // user always has data on screen before background updates
        // begin (Requirement 9.10). Idempotent — safe on subsequent
        // manual refreshes.
        _startAutoRefresh();
        return;
      }

      // 401 → session expired; defer to global error handler if available
      // so the user is redirected to /login with a return URL.
      if (result && result.status === 401) {
        if (typeof window !== 'undefined' && window.ErrorHandler) {
          window.ErrorHandler.handleApiError(
            { status: 401, message: 'HTTP 401' },
            'loadInstitutionDashboard'
          );
        }
        _renderError('Your session has expired. Please log in again.');
        return;
      }

      // 403 → not an institution admin / forbidden.
      if (result && result.status === 403) {
        _renderError(
          (result && result.error) ||
          'You do not have permission to view this dashboard.'
        );
        return;
      }

      _renderError(
        (result && result.error) ||
        'Unable to load dashboard data. Please try again later.'
      );
    } catch (err) {
      console.error('loadInstitutionDashboard failed:', err);
      _renderError('Unable to load dashboard data. Please check your connection and try again.');
    }
  }

  // ── Students Modal ───────────────────────────────────────────────────────

  /**
   * Open the students list modal showing institution-linked and direct subscribers
   */
  function _openStudentsModal() {
    var modal = $('studentsModal');
    if (!modal) return;
    modal.setAttribute('aria-hidden', 'false');
    modal.style.display = 'flex';
    _loadStudentsList();
  }

  /**
   * Close the students list modal
   */
  function _closeStudentsModal() {
    var modal = $('studentsModal');
    if (!modal) return;
    modal.setAttribute('aria-hidden', 'true');
    modal.style.display = 'none';
  }

  /**
   * Load and display all students from the API
   */
  function _loadStudentsList() {
    fetch('/api/institution/students', {
      method: 'GET',
      credentials: 'include',
      headers: {
        'Accept': 'application/json'
      }
    })
    .then(function (res) {
      if (!res.ok) throw new Error('Failed to load students: ' + res.status);
      return res.json();
    })
    .then(function (data) {
      _renderStudentsList(data);
    })
    .catch(function (err) {
      console.error('Error loading students:', err);
      var tbody = $('institutionStudentsBody');
      if (tbody) {
        tbody.innerHTML = '<tr><td colspan="3" style="text-align: center; color: var(--red-l); padding: 20px;">Failed to load students</td></tr>';
      }
    });
  }

  /**
   * Render students list in the modal
   */
  function _renderStudentsList(data) {
    // Institution students
    var institutionData = data.institution || {};
    var institutionName = institutionData.name || 'Institution';
    var institutionStudents = institutionData.students || [];
    
    var nameEl = $('institutionName');
    if (nameEl) nameEl.textContent = institutionName;

    var tbody = $('institutionStudentsBody');
    if (tbody) {
      if (institutionStudents.length === 0) {
        tbody.innerHTML = '<tr><td colspan="3" style="text-align: center; color: var(--muted); padding: 20px;">No institution students</td></tr>';
      } else {
        tbody.innerHTML = institutionStudents.map(function (student) {
          return '<tr>' +
            '<td>' + _escapeHtml(student.name) + '</td>' +
            '<td><code style="font-size: 0.9rem; color: var(--purple-l, #a78bfa);">' + _escapeHtml(student.email) + '</code></td>' +
            '<td><strong style="color: var(--purple-l, #a78bfa);">' + _escapeHtml(student.id) + '</strong></td>' +
            '</tr>';
        }).join('');
      }
    }

    // Direct subscribers
    var directSubscribers = data.direct_subscribers || [];
    tbody = $('directSubscribersBody');
    if (tbody) {
      if (directSubscribers.length === 0) {
        tbody.innerHTML = '<tr><td colspan="3" style="text-align: center; color: var(--muted); padding: 20px;">No direct subscribers</td></tr>';
      } else {
        tbody.innerHTML = directSubscribers.map(function (student) {
          return '<tr>' +
            '<td>' + _escapeHtml(student.name) + '</td>' +
            '<td><code style="font-size: 0.9rem; color: var(--green-l, #86efac);">' + _escapeHtml(student.email) + '</code></td>' +
            '<td><strong style="color: var(--green-l, #86efac);">' + _escapeHtml(student.id) + '</strong></td>' +
            '</tr>';
        }).join('');
      }
    }

    // Update counts
    setText('institutionStudentCount', institutionStudents.length);
    setText('directSubscriberCount', directSubscribers.length);
    setText('totalStudentCount', institutionStudents.length + directSubscribers.length);
  }

  // ── Wiring ───────────────────────────────────────────────────────────────

  function _wireButtons() {
    var refreshBtn = $(IDS.refreshBtn);
    if (refreshBtn && !refreshBtn._wired) {
      refreshBtn._wired = true;
      refreshBtn.addEventListener('click', function () {
        loadInstitutionDashboard();
      });
    }

    var retryBtn = $(IDS.retryBtn);
    if (retryBtn && !retryBtn._wired) {
      retryBtn._wired = true;
      retryBtn.addEventListener('click', function () {
        loadInstitutionDashboard();
      });
    }

    // Wire Total Students KPI to open modal
    var kpiTileStudents = $('kpiTileStudents');
    if (kpiTileStudents && !kpiTileStudents._wired) {
      kpiTileStudents._wired = true;
      kpiTileStudents.style.cursor = 'pointer';
      kpiTileStudents.addEventListener('click', _openStudentsModal);
    }

    // Wire modal close button
    var modalClose = $('studentsModalClose');
    if (modalClose && !modalClose._wired) {
      modalClose._wired = true;
      modalClose.addEventListener('click', _closeStudentsModal);
    }

    // Wire modal backdrop to close
    var modal = $('studentsModal');
    if (modal && !modal._wired) {
      modal._wired = true;
      modal.addEventListener('click', function (e) {
        if (e.target === modal) {
          _closeStudentsModal();
        }
      });
    }
  }

  if (typeof document !== 'undefined') {
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', _wireButtons);
    } else {
      _wireButtons();
    }
  }

  // Expose globally so the inline bootstrap script in
  // institution-dashboard.html can invoke loadInstitutionDashboard().
  if (typeof window !== 'undefined') {
    window.loadInstitutionDashboard = loadInstitutionDashboard;
  }
})();
