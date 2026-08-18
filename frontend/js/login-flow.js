(function (root, factory) {
  var api = factory();
  if (typeof module !== 'undefined' && module.exports) {
    module.exports = api;
  }
  if (root) {
    root.Mr.ELoginFlow = api;
  }
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';

  function resolveStudentLoginDecision(result, getReturnUrl) {
    var data = (result && result.data) || {};
    var returnUrl = typeof getReturnUrl === 'function' ? getReturnUrl() : null;

    if (returnUrl) {
      return {
        mode: 'redirect',
        redirectUrl: returnUrl,
      };
    }

    if (!result || !result.ok || (data.role || '').toLowerCase() !== 'student') {
      return {
        mode: 'redirect',
        redirectUrl: '/dashboard',
      };
    }

    if (!data.needs_subscription_selection || data.student_subtype !== 'direct_subscriber') {
      return {
        mode: 'redirect',
        redirectUrl: data.redirect || (data.student_subtype === 'institution_linked' ? '/student/institution/dashboard' : '/dashboard'),
      };
    }

    return {
      mode: 'subscription',
      redirectUrl: data.redirect || '/dashboard',
    };
  }

  function buildStudentLoginFallback(options) {
    var redirectUrl = options && options.redirectUrl ? options.redirectUrl : '/dashboard';
    var message = options && options.message
      ? options.message
      : 'Subscription options are unavailable right now. Redirecting you to your dashboard.';

    return {
      mode: 'redirect',
      redirectUrl: redirectUrl,
      message: message,
    };
  }

  return {
    resolveStudentLoginDecision: resolveStudentLoginDecision,
    buildStudentLoginFallback: buildStudentLoginFallback,
  };
});
