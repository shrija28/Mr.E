const test = require('node:test');
const assert = require('node:assert/strict');
const Mr.ELoginFlow = require('./login-flow');

test('redirects normal students immediately without showing subscription UI', () => {
  const result = Mr.ELoginFlow.resolveStudentLoginDecision({
    ok: true,
    data: {
      role: 'student',
      student_subtype: 'institution_linked',
      redirect: '/student/institution/dashboard'
    }
  });

  assert.equal(result.mode, 'redirect');
  assert.equal(result.redirectUrl, '/student/institution/dashboard');
});

test('keeps direct subscribers on the subscription path when selection is required', () => {
  const result = Mr.ELoginFlow.resolveStudentLoginDecision({
    ok: true,
    data: {
      role: 'student',
      student_subtype: 'direct_subscriber',
      needs_subscription_selection: true
    }
  });

  assert.equal(result.mode, 'subscription');
  assert.equal(result.redirectUrl, '/dashboard');
});

test('falls back to dashboard if the modal cannot be shown', () => {
  const result = Mr.ELoginFlow.buildStudentLoginFallback({
    redirectUrl: '/dashboard',
    message: 'Subscription options are unavailable right now. Redirecting you to your dashboard.'
  });

  assert.equal(result.redirectUrl, '/dashboard');
  assert.match(result.message, /Redirecting you to your dashboard/);
});
