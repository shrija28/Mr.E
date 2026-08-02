// SmartKCET Prep — Subscription Selection Modal Component (4-Plan Version)
// Handles plan selection (Free, 7-Day Trial, Pro Monthly, Pro Yearly),
// Razorpay payment integration, activation API calls, error display,
// loading states, and keyboard focus trap for accessibility.
//
// Pairs with:
//   - frontend/html/subscription_modal.html (DOM structure, id="subscriptionModal")
//   - frontend/css/subscription-modal-premium.css (styling)
//   - frontend/js/subscription.js (Subscription module + SubscriptionAPI)
//
// Public API:
//   SubscriptionModal.init()
//   SubscriptionModal.show()
//   SubscriptionModal.hide()
//   SubscriptionModal.selectFree()
//   SubscriptionModal.selectTrial()
//   SubscriptionModal.selectMonthly()
//   SubscriptionModal.selectYearly()
//   SubscriptionModal.shouldShow(subscriptionData)

var SubscriptionModal = (function () {
  'use strict';

  // ── Constants ───────────────────────────────────────────────────────────

  var MODAL_ID = 'subscriptionModal';
  var ERROR_ID = 'modalError';
  var ERROR_MESSAGE_ID = 'errorMessage';
  var LOADING_ID = 'modalLoading';

  // Statuses where the user effectively has no usable subscription and the
  // modal SHOULD be shown when they try to start an exam.
  var INACTIVE_STATUSES = {
    expired: true,
    cancelled: true,
  };

  // ── Internal state ──────────────────────────────────────────────────────

  var _modalEl = null;             // root #subscriptionModal element
  var _initialized = false;        // guards against double-binding listeners
  var _isOpen = false;             // whether the modal is currently visible
  var _isBusy = false;             // an activation request is in flight
  var _previouslyFocused = null;   // element to restore focus to on close
  var _lastAction = null;          // { type, planId }
  var _plans = [];                 // Available plans from API
  var _razorpayKeyId = '';         // Razorpay key ID

  // Bound event handler references (so we can remove them on hide / destroy)
  var _onKeyDown = null;
  var _onOverlayClick = null;

  // ── Helpers ─────────────────────────────────────────────────────────────

  function _qs(selector, root) {
    return (root || _modalEl || document).querySelector(selector);
  }

  function _qsa(selector, root) {
    return Array.prototype.slice.call(
      (root || _modalEl || document).querySelectorAll(selector)
    );
  }

  /**
   * Locate the modal element in the DOM. Returns null if the modal HTML
   * has not been included on the current page.
   */
  function _findModal() {
    if (_modalEl && document.body.contains(_modalEl)) return _modalEl;
    _modalEl = document.getElementById(MODAL_ID);
    return _modalEl;
  }

  /**
   * Map an HTTP status code / API error result onto a friendly user-facing message.
   */
  function _formatActivationError(result) {
    if (!result) return 'Something went wrong. Please try again.';
    // Prefer the server-provided error string when available.
    if (result.data && (result.data.error || result.data.message)) {
      return result.data.error || result.data.message;
    }
    switch (result.status) {
      case 400:
        return 'Invalid request. Please check your selection and try again.';
      case 401:
        return 'Your session has expired. Please log in again.';
      case 402:
      case 'payment_failed':
        return 'Payment failed. Please try a different payment method.';
      case 403:
        return 'You are not allowed to activate this plan.';
      case 409:
        return 'You already have an active subscription.';
      case 500:
      case 502:
      case 503:
        return 'Service temporarily unavailable. Please try again in a moment.';
      case 0:
        return 'Network error. Please check your connection and try again.';
      default:
        return result.error || 'Activation failed. Please try again.';
    }
  }

  // ── Loading / error / success display ───────────────────────────────────

  /**
   * Toggle loading state on plan-selection buttons.
   */
  function _setLoading(isLoading) {
    if (!_modalEl) return;

    var buttons = _qsa('[data-action^="select-"]');
    var closeBtn = _qs('.modal-close');
    var loadingEl = _qs('#' + LOADING_ID);

    buttons.forEach(function (btn) {
      if (!btn) return;
      btn.disabled = !!isLoading;
      btn.classList.toggle('is-loading', !!isLoading);
      btn.setAttribute('aria-busy', isLoading ? 'true' : 'false');
      
      // Visual feedback - add opacity
      btn.style.opacity = isLoading ? '0.5' : '1';
      btn.style.cursor = isLoading ? 'not-allowed' : 'pointer';
    });

    if (closeBtn) {
      closeBtn.disabled = !!isLoading;
      closeBtn.style.opacity = isLoading ? '0.5' : '1';
    }
    
    if (loadingEl) loadingEl.style.display = isLoading ? '' : 'none';
    
    console.log('[modal] Loading state:', isLoading ? 'ENABLED' : 'DISABLED');
  }

  /**
   * Show an error message inside the modal.
   */
  function _showError(message) {
    if (!_modalEl) return;
    var errorEl = _qs('#' + ERROR_ID);
    var messageEl = _qs('#' + ERROR_MESSAGE_ID);
    var retryBtn = _qs('.btn-retry', errorEl || _modalEl);

    if (messageEl) messageEl.textContent = message || '';
    if (errorEl) {
      errorEl.style.display = '';
      errorEl.classList.add('active');
    }
    if (retryBtn) {
      retryBtn.style.display = _lastAction ? '' : 'none';
    }
  }

  function _clearError() {
    if (!_modalEl) return;
    var errorEl = _qs('#' + ERROR_ID);
    var messageEl = _qs('#' + ERROR_MESSAGE_ID);
    if (messageEl) messageEl.textContent = '';
    if (errorEl) {
      errorEl.style.display = 'none';
      errorEl.classList.remove('active');
    }
  }

  /**
   * Close the modal and redirect to dashboard after successful subscription activation.
   * Check if we're on the login page with a pending login response.
   */
  function _onActivationSuccess(successMessage) {
    _lastAction = null;
    _clearError();

    if (successMessage && typeof window !== 'undefined' && window.ErrorHandler) {
      try {
        if (typeof window.ErrorHandler.setFlashSuccess === 'function') {
          window.ErrorHandler.setFlashSuccess(successMessage);
        }
        window.ErrorHandler.showSuccess(successMessage);
      } catch (e) { /* best-effort */ }
    }

    hide();
    
    // After successful subscription activation, redirect to dashboard
    setTimeout(function () {
      try {
        // Check if we have a pending login response from the login page
        var loginResponse = sessionStorage.getItem('_loginResponse');
        if (loginResponse) {
          var data = JSON.parse(loginResponse);
          sessionStorage.removeItem('_loginResponse');
          
          // Determine correct redirect URL
          var redirectUrl = data.redirect || '/dashboard';
          if (data.student_subtype === 'institution_linked') {
            redirectUrl = '/student/institution/dashboard';
          }
          
          console.log('[modal] Redirecting to:', redirectUrl);
          window.location.href = redirectUrl;
        } else {
          // Not on login page, just reload
          window.location.reload();
        }
      } catch (e) {
        console.error('[modal] Redirect error:', e);
        window.location.href = '/dashboard';
      }
    }, 50);
  }

  // ── Focus trap ──────────────────────────────────────────────────────────

  /**
   * Return all currently-focusable elements within the modal in document order.
   */
  function _getFocusableElements() {
    if (!_modalEl) return [];
    if (typeof window !== 'undefined' && window.FocusTrap &&
        typeof window.FocusTrap._getFocusable === 'function') {
      return window.FocusTrap._getFocusable(_modalEl);
    }
    var selector = [
      'a[href]',
      'area[href]',
      'button:not([disabled])',
      'input:not([disabled]):not([type="hidden"])',
      'select:not([disabled])',
      'textarea:not([disabled])',
      '[tabindex]:not([tabindex="-1"])',
    ].join(',');

    return _qsa(selector).filter(function (el) {
      if (el.hasAttribute('disabled')) return false;
      if (el.getAttribute('aria-hidden') === 'true') return false;
      if (el.offsetParent === null && el !== document.activeElement) {
        var style = window.getComputedStyle ? window.getComputedStyle(el) : null;
        if (!style || style.visibility === 'hidden' || style.display === 'none') {
          return false;
        }
      }
      return true;
    });
  }

  /**
   * Trap Tab / Shift+Tab cycling within the modal and close on Escape.
   */
  function _handleKeyDown(evt) {
    if (!_isOpen || !_modalEl) return;

    if (evt.key === 'Escape' || evt.keyCode === 27) {
      evt.preventDefault();
      if (!_isBusy) hide();
      return;
    }

    if (evt.key !== 'Tab' && evt.keyCode !== 9) return;

    var focusable = _getFocusableElements();
    if (focusable.length === 0) {
      evt.preventDefault();
      _modalEl.focus();
      return;
    }

    var first = focusable[0];
    var last = focusable[focusable.length - 1];
    var active = document.activeElement;

    if (evt.shiftKey) {
      if (active === first || !_modalEl.contains(active)) {
        evt.preventDefault();
        last.focus();
      }
    } else {
      if (active === last || !_modalEl.contains(active)) {
        evt.preventDefault();
        first.focus();
      }
    }
  }

  /**
   * Close on overlay click (clicks outside the dialog).
   */
  function _handleOverlayClick(evt) {
    if (!_modalEl) return;
    if (evt.target === _modalEl) {
      if (!_isBusy) hide();
    }
  }

  // ── Razorpay payment flow ───────────────────────────────────────────────

  /**
   * Initiate Razorpay payment for a paid plan.
   */
  async function _initiatePayment(plan) {
    // Guard: prevent duplicate calls
    if (_isBusy) {
      console.log('[payment] Already processing payment, ignoring duplicate request');
      return;
    }
    
    console.log('[payment] create-order called for plan:', plan.name, plan.id);
    
    _isBusy = true;
    _lastAction = { type: 'payment', planId: plan.id };
    _clearError();
    _setLoading(true);

    try {
      // Create Razorpay order
      var payload = { plan_id: plan.id };
      console.log('[payment] ========== CREATE ORDER REQUEST ==========');
      console.log('[payment] Request URL: /api/payments/create-order');
      console.log('[payment] Request Method: POST');
      console.log('[payment] Request Payload:', JSON.stringify(payload, null, 2));
      console.log('[payment] Plan details:', JSON.stringify({
        id: plan.id,
        name: plan.name,
        price: plan.price,
        billing_period: plan.billing_period
      }, null, 2));
      
      var createRes = await fetch('/api/payments/create-order', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(payload),
      });

      console.log('[payment] Response Status:', createRes.status, createRes.statusText);
      
      var createData = await createRes.json();
      
      console.log('[payment] ========== CREATE ORDER RESPONSE ==========');
      console.log('[payment] Response Body:', JSON.stringify(createData, null, 2));

      if (!createRes.ok) {
        console.error('[payment] ========== CREATE ORDER FAILED ==========');
        console.error('[payment] Status Code:', createRes.status);
        console.error('[payment] FULL ERROR RESPONSE:', JSON.stringify(createData, null, 2));
        console.error('[payment] Error detail:', createData.detail);
        console.error('[payment] Error message:', createData.message);
        console.error('[payment] ==============================================');
        
        _showError(createData.message || createData.detail?.message || 'Failed to create payment order.');
        _setLoading(false);
        _isBusy = false;  // Reset busy flag on error
        return;
      }
      
      console.log('[payment] create-order success, order_id:', createData.order_id);

      // Handle mock payment (dev mode)
      if (createData._mock) {
        console.log('[payment] Mock payment mode detected');
        _setLoading(false);
        _isBusy = false;
        
        _injectMockRazorpayStyles();
        _showMockCheckoutPopup(
          plan,
          createData.order_id,
          async function (paymentId, signature) {
            _isBusy = true;
            _setLoading(true);
            try {
              var verifyRes = await fetch('/api/payments/verify', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({
                  razorpay_order_id: createData.order_id,
                  razorpay_payment_id: paymentId,
                  razorpay_signature: signature,
                  plan_id: plan.id,
                }),
              });
              var verifyData = await verifyRes.json();
              if (verifyRes.ok && verifyData.verified) {
                _onActivationSuccess('✅ Payment successful! Your plan is now active.');
              } else {
                _showError('⚠️ Verification failed. Contact support. Order: ' + createData.order_id);
                _setLoading(false);
              }
            } catch (err) {
              _showError('Network error during verification. Please contact support.');
              _setLoading(false);
            }
          },
          function () {
            console.log('[payment] Mock checkout popup dismissed');
            _setLoading(false);
            _isBusy = false;
          }
        );
        return;
      }

      // Launch Razorpay checkout
      _setLoading(false);
      _isBusy = false;  // Allow Razorpay popup interaction
      
      console.log('[payment] Opening Razorpay checkout...');
      var razorpayOptions = {
        key: createData.key_id || _razorpayKeyId,
        amount: createData.amount,
        currency: createData.currency || 'INR',
        order_id: createData.order_id,
        name: 'SmartKCET Prep',
        description: createData.description || plan.name,
        prefill: createData.prefill || {},
        theme: { color: '#a78bfa' },
        handler: async function (response) {
          _isBusy = true;  // Re-enable busy flag during verification
          _setLoading(true);
          console.log('[payment] Payment successful, verifying...');
          try {
            var verifyRes = await fetch('/api/payments/verify', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              credentials: 'include',
              body: JSON.stringify({
                razorpay_order_id: response.razorpay_order_id,
                razorpay_payment_id: response.razorpay_payment_id,
                razorpay_signature: response.razorpay_signature,
                plan_id: plan.id,
              }),
            });

            var verifyData = await verifyRes.json();

            if (verifyRes.ok && verifyData.verified) {
              _onActivationSuccess('✅ Payment successful! Your plan is now active.');
            } else {
              _showError('⚠️ Verification failed. Contact support. Order: ' + response.razorpay_order_id);
              _setLoading(false);
            }
          } catch (err) {
            _showError('Network error during verification. Please contact support.');
            _setLoading(false);
          }
        },
        modal: {
          ondismiss: function () {
            console.log('[payment] Razorpay popup dismissed');
            _setLoading(false);
            _isBusy = false;  // Reset busy flag when user cancels
          },
        },
      };

      if (typeof window.Razorpay === 'undefined') {
        var script = document.createElement('script');
        script.src = 'https://checkout.razorpay.com/v1/checkout.js';
        script.onload = function () {
          new window.Razorpay(razorpayOptions).open();
        };
        script.onerror = function () {
          _showError('Failed to load payment gateway.');
          _setLoading(false);
          _isBusy = false;  // Reset busy flag on script load error
        };
        document.head.appendChild(script);
      } else {
        new window.Razorpay(razorpayOptions).open();
      }
    } catch (err) {
      console.error('[payment] Error during payment initiation:', err);
      _showError('Network error. Please try again.');
      _setLoading(false);
      _isBusy = false;  // Reset busy flag on error
    }
  }

  // ── Plan selection handlers ─────────────────────────────────────────────

  /**
   * Activate Free plan (instant activation, no payment).
   * Allowed only when user has no active subscription (new user or
   * expired/cancelled). Blocked with a friendly message otherwise.
   */
  async function selectFree() {
    if (_isBusy) return;
    _isBusy = true;
    _lastAction = { type: 'free' };
    _clearError();
    _setLoading(true);

    console.log('[free-plan] activating free plan');

    // Log current subscription state for debugging
    if (typeof Subscription !== 'undefined' && Subscription.getStatus) {
      try {
        var currentSub = await Subscription.getStatus();
        console.log('[free-plan] current subscription:', currentSub);
      } catch (e) { /* non-fatal */ }
    }

    try {
      var res = await fetch('/api/subscription/activate-free', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
      });

      var data = await res.json();
      console.log('[free-plan] response:', data);

      if (res.ok) {
        // SubscriptionResponse has a top-level `status` field ('active', etc.)
        _isBusy = false;
        _setLoading(false);
        _onActivationSuccess('✅ Free plan activated! Redirecting to dashboard...');
        return;
      }

      // 400 with subscription_active → user already has an active plan
      if (res.status === 400) {
        var msg = (data && data.detail && data.detail.message)
          || (data && data.message)
          || 'Current subscription active. Free plan available after expiry.';
        _setLoading(false);
        _isBusy = false;
        _showError(msg);
        return;
      }

      _setLoading(false);
      _isBusy = false;
      _showError(
        (data && data.detail && data.detail.message)
        || (data && data.message)
        || 'Failed to activate free plan. Please try again.'
      );
    } catch (err) {
      _setLoading(false);
      _isBusy = false;
      _showError('Network error. Please check your connection and try again.');
      console.error('[free-plan] Free plan activation error:', err);
    }
  }

  /**
   * Activate 7-Day Premium Trial (₹99 via Razorpay).
   */
  async function selectTrial() {
    var plan = _plans.find(function (p) { return p.name === '7-Day Premium Trial'; });
    if (!plan) {
      _showError('7-Day Trial plan not found. Please refresh and try again.');
      return;
    }
    await _initiatePayment(plan);
  }

  /**
   * Activate Pro Monthly (₹349/month via Razorpay).
   */
  async function selectMonthly() {
    var plan = _plans.find(function (p) { return p.name === 'Pro Monthly'; });
    if (!plan) {
      _showError('Pro Monthly plan not found. Please refresh and try again.');
      return;
    }
    await _initiatePayment(plan);
  }

  /**
   * Activate Pro Yearly (₹2999/year via Razorpay).
   */
  async function selectYearly() {
    var plan = _plans.find(function (p) { return p.name === 'Pro Yearly'; });
    if (!plan) {
      _showError('Pro Yearly plan not found. Please refresh and try again.');
      return;
    }
    await _initiatePayment(plan);
  }

  // ── Event wiring ────────────────────────────────────────────────────────

  // Store handler references to prevent duplicate listeners
  var _handlers = {
    close: null,
    free: null,
    trial: null,
    monthly: null,
    yearly: null,
    retry: null
  };

  function _bindListeners() {
    if (!_modalEl) return;
    
    // If already initialized, remove old listeners first to prevent duplicates
    if (_initialized) {
      // Remove old handlers if they exist
      Object.keys(_handlers).forEach(function(key) {
        if (_handlers[key]) {
          console.log('[modal] Cleanup: Removing old ' + key + ' handler');
          // This will be handled when we re-attach
        }
      });
      // Don't return early - rebind the listeners
    }

    // Close button
    var closeBtn = _qs('.modal-close');
    if (closeBtn && closeBtn !== _handlers._oldCloseBtn) {
      if (_handlers.close && _handlers._oldCloseBtn) {
        _handlers._oldCloseBtn.removeEventListener('click', _handlers.close);
      }
      _handlers.close = function (evt) {
        evt.preventDefault();
        if (!_isBusy) hide();
      };
      closeBtn.addEventListener('click', _handlers.close);
      _handlers._oldCloseBtn = closeBtn;
    }

    // Free plan button
    var freeBtn = _qs('[data-action="select-free"]');
    if (freeBtn && freeBtn !== _handlers._oldFreeBtn) {
      if (_handlers.free && _handlers._oldFreeBtn) {
        _handlers._oldFreeBtn.removeEventListener('click', _handlers.free);
      }
      _handlers.free = function (evt) {
        evt.preventDefault();
        if (_isBusy) {
          console.log('[modal] Button click ignored - already processing');
          return;
        }
        console.log('[modal] Free plan button clicked');
        selectFree();
      };
      freeBtn.addEventListener('click', _handlers.free);
      _handlers._oldFreeBtn = freeBtn;
    }

    // 7-Day Trial button
    var trialBtn = _qs('[data-action="select-trial"]');
    if (trialBtn && trialBtn !== _handlers._oldTrialBtn) {
      if (_handlers.trial && _handlers._oldTrialBtn) {
        _handlers._oldTrialBtn.removeEventListener('click', _handlers.trial);
      }
      _handlers.trial = function (evt) {
        evt.preventDefault();
        if (_isBusy) {
          console.log('[modal] Button click ignored - already processing');
          return;
        }
        console.log('[modal] Trial button clicked');
        selectTrial();
      };
      trialBtn.addEventListener('click', _handlers.trial);
      _handlers._oldTrialBtn = trialBtn;
    }

    // Pro Monthly button
    var monthlyBtn = _qs('[data-action="select-monthly"]');
    if (monthlyBtn && monthlyBtn !== _handlers._oldMonthlyBtn) {
      if (_handlers.monthly && _handlers._oldMonthlyBtn) {
        _handlers._oldMonthlyBtn.removeEventListener('click', _handlers.monthly);
      }
      _handlers.monthly = function (evt) {
        evt.preventDefault();
        if (_isBusy) {
          console.log('[modal] Button click ignored - already processing');
          return;
        }
        console.log('[modal] Monthly button clicked');
        selectMonthly();
      };
      monthlyBtn.addEventListener('click', _handlers.monthly);
      _handlers._oldMonthlyBtn = monthlyBtn;
    }

    // Pro Yearly button
    var yearlyBtn = _qs('[data-action="select-yearly"]');
    if (yearlyBtn && yearlyBtn !== _handlers._oldYearlyBtn) {
      if (_handlers.yearly && _handlers._oldYearlyBtn) {
        _handlers._oldYearlyBtn.removeEventListener('click', _handlers.yearly);
      }
      _handlers.yearly = function (evt) {
        evt.preventDefault();
        if (_isBusy) {
          console.log('[modal] Button click ignored - already processing');
          return;
        }
        console.log('[modal] Yearly button clicked');
        selectYearly();
      };
      yearlyBtn.addEventListener('click', _handlers.yearly);
      _handlers._oldYearlyBtn = yearlyBtn;
    }

    // Retry button inside the error block
    var retryBtn = _qs('.btn-retry');
    if (retryBtn && retryBtn !== _handlers._oldRetryBtn) {
      if (_handlers.retry && _handlers._oldRetryBtn) {
        _handlers._oldRetryBtn.removeEventListener('click', _handlers.retry);
      }
      _handlers.retry = function (evt) {
        evt.preventDefault();
        if (_isBusy) {
          console.log('[modal] Retry ignored - already processing');
          return;
        }
        if (!_lastAction) return;
        
        console.log('[modal] Retry button clicked, lastAction:', _lastAction.type);
        
        switch (_lastAction.type) {
          case 'free':
            selectFree();
            break;
          case 'payment':
            var plan = _plans.find(function (p) { return p.id === _lastAction.planId; });
            if (plan) _initiatePayment(plan);
            break;
        }
      };
      retryBtn.addEventListener('click', _handlers.retry);
      _handlers._oldRetryBtn = retryBtn;
    }

    if (!_initialized) {
      _initialized = true;
      console.log('[modal] Event listeners bound successfully (first time)');
    } else {
      console.log('[modal] Event listeners re-bound for updated DOM');
    }
  }

  // ── Initialize (load plans from API) ───────────────────────────────────

  /**
   * Load available plans from the backend API.
   * Call this once when the page loads, before showing the modal.
   */
  async function init() {
    try {
      // Fetch subscription plans
      var res = await fetch('/api/payments/plans/student', {
        method: 'GET',
        credentials: 'include',
      });

      var data = await res.json();

      if (res.ok && data.plans) {
        _plans = data.plans;
        _razorpayKeyId = data.key_id || '';

        // Update plan buttons with plan IDs
        var trialBtn = _qs('[data-action="select-trial"]');
        var monthlyBtn = _qs('[data-action="select-monthly"]');
        var yearlyBtn = _qs('[data-action="select-yearly"]');

        var trialPlan = _plans.find(function (p) { return p.name === '7-Day Premium Trial'; });
        var monthlyPlan = _plans.find(function (p) { return p.name === 'Pro Monthly'; });
        var yearlyPlan = _plans.find(function (p) { return p.name === 'Pro Yearly'; });

        if (trialBtn && trialPlan) trialBtn.setAttribute('data-plan-id', trialPlan.id);
        if (monthlyBtn && monthlyPlan) monthlyBtn.setAttribute('data-plan-id', monthlyPlan.id);
        if (yearlyBtn && yearlyPlan) yearlyBtn.setAttribute('data-plan-id', yearlyPlan.id);
      }

      // Check user's current subscription status
      try {
        var statusRes = await fetch('/api/subscription/user/subscription-status', {
          method: 'GET',
          credentials: 'include',
        });

        console.log('[subscription-modal] Subscription status response status:', statusRes.status);
        
        if (statusRes.ok) {
          var statusData = await statusRes.json();
          console.log('[subscription-modal] Subscription status data:', statusData);
          
          // If user has active subscription, disable buttons based on current plan
          if (statusData.has_active_subscription && statusData.current_plan_name) {
            console.log('[subscription-modal] Has active subscription:', statusData.current_plan_name);
            
            var daysRemaining = statusData.days_remaining || 'unknown';
            var currentPlan = statusData.current_plan_name;
            var tooltipText = 'Can be upgraded after ' + currentPlan + ' expires in ' + daysRemaining + ' days';
            
            var freeBtn = _qs('[data-action="select-free"]');
            var trialBtn = _qs('[data-action="select-trial"]');
            var monthlyBtn = _qs('[data-action="select-monthly"]');
            var yearlyBtn = _qs('[data-action="select-yearly"]');
            
            console.log('[subscription-modal] Button elements found:', {
              free: !!freeBtn,
              trial: !!trialBtn,
              monthly: !!monthlyBtn,
              yearly: !!yearlyBtn
            });
            
            // Determine which buttons to disable based on current plan
            var buttonsToDisable = [];
            
            if (currentPlan === 'Free') {
              // If on Free: enable all 3 paid buttons
              buttonsToDisable = [];
              console.log('[subscription-modal] Current plan: Free - all paid buttons enabled');
            } else if (currentPlan.includes('7-Day')) {
              // If on Trial: disable Free, Monthly, Yearly
              buttonsToDisable = [freeBtn, monthlyBtn, yearlyBtn];
              console.log('[subscription-modal] Current plan: 7-Day Trial - disabling Free, Monthly, Yearly');
            } else if (currentPlan.includes('Monthly')) {
              // If on Pro Monthly: disable Free, Trial, Yearly
              buttonsToDisable = [freeBtn, trialBtn, yearlyBtn];
              console.log('[subscription-modal] Current plan: Pro Monthly - disabling Free, Trial, Yearly');
            } else if (currentPlan.includes('Yearly')) {
              // If on Pro Yearly: disable Free, Trial, Monthly
              buttonsToDisable = [freeBtn, trialBtn, monthlyBtn];
              console.log('[subscription-modal] Current plan: Pro Yearly - disabling Free, Trial, Monthly');
            }
            
            console.log('[subscription-modal] Buttons to disable count:', buttonsToDisable.length);
            
            // Apply disabled state to all buttons in buttonsToDisable list
            buttonsToDisable.forEach(function (btn, idx) {
              if (!btn) {
                console.warn('[subscription-modal] Button at index ' + idx + ' is null/undefined');
                return;
              }
              console.log('[subscription-modal] Disabling button:', btn.getAttribute('data-action'));
              btn.disabled = true;
              btn.classList.add('disabled');
              btn.setAttribute('title', tooltipText);
              btn.setAttribute('aria-disabled', 'true');
              
              // Add visual disabled state
              btn.style.opacity = '0.5';
              btn.style.cursor = 'not-allowed';
              btn.style.pointerEvents = 'none';
            });
            
            console.log('[subscription-modal] Applied subscription-based button restrictions');
          } else {
            console.log('[subscription-modal] No active subscription or plan name missing');
            console.log('[subscription-modal] has_active_subscription:', statusData.has_active_subscription);
            console.log('[subscription-modal] current_plan_name:', statusData.current_plan_name);
          }
        } else {
          console.warn('[subscription-modal] Subscription status request failed with status:', statusRes.status);
        }
      } catch (err) {
        console.warn('[subscription-modal] Could not check subscription status:', err);
        // Non-fatal - continue anyway
      }
    } catch (err) {
      console.error('Failed to load plans:', err);
    }
  }

  // ── Public API ──────────────────────────────────────────────────────────

  /**
   * Reveal the modal and set up focus trap.
   */
  function show() {
    var modal = _findModal();
    if (!modal) {
      console.warn('SubscriptionModal: #' + MODAL_ID + ' not found in DOM.');
      return;
    }
    if (_isOpen) return;

    // Initialize modal data (fetch plans and subscription status) if not already initialized
    if (!_initialized) {
      console.log('[subscription-modal] First time showing modal - initializing...');
      init();  // This is async but we don't wait for it - data will populate as it arrives
    }

    // Always rebind listeners when showing modal (ensures buttons are clickable)
    _bindListeners();
    _clearError();
    _setLoading(false);

    _previouslyFocused = document.activeElement;

    modal.style.display = 'flex';
    modal.classList.add('open');
    modal.removeAttribute('hidden');
    modal.setAttribute('aria-hidden', 'false');

    document.body.classList.add('modal-open');

    _isOpen = true;

    var usedSharedTrap = false;
    if (typeof window !== 'undefined' && window.FocusTrap) {
      try {
        window.FocusTrap.activate(modal, {
          onEscape: function () { if (!_isBusy) hide(); },
        });
        usedSharedTrap = true;
      } catch (e) {
        usedSharedTrap = false;
      }
    }

    if (!usedSharedTrap && !_onKeyDown) {
      _onKeyDown = _handleKeyDown;
      document.addEventListener('keydown', _onKeyDown);
    }
    if (!_onOverlayClick) {
      _onOverlayClick = _handleOverlayClick;
      modal.addEventListener('click', _onOverlayClick);
    }

    if (!usedSharedTrap) {
      setTimeout(function () {
        var focusable = _getFocusableElements();
        var target = focusable[0] || modal;
        try {
          target.focus({ preventScroll: true });
        } catch (e) {
          target.focus();
        }
      }, 0);
    }
  }

  /**
   * Hide the modal and restore focus.
   */
  function hide() {
    var modal = _findModal();
    if (!modal || !_isOpen) {
      if (modal) {
        modal.style.display = 'none';
        modal.classList.remove('open');
        modal.setAttribute('aria-hidden', 'true');
      }
      return;
    }

    modal.classList.remove('open');
    modal.style.display = 'none';
    modal.setAttribute('aria-hidden', 'true');

    document.body.classList.remove('modal-open');

    if (typeof window !== 'undefined' && window.FocusTrap) {
      try { window.FocusTrap.deactivate(modal); } catch (e) { /* noop */ }
    }

    if (_onKeyDown) {
      document.removeEventListener('keydown', _onKeyDown);
      _onKeyDown = null;
    }
    if (_onOverlayClick) {
      modal.removeEventListener('click', _onOverlayClick);
      _onOverlayClick = null;
    }

    _isOpen = false;
    _setLoading(false);

    if (_previouslyFocused && typeof _previouslyFocused.focus === 'function') {
      try {
        _previouslyFocused.focus({ preventScroll: true });
      } catch (e) {
        try { _previouslyFocused.focus(); } catch (_) { /* noop */ }
      }
    }
    _previouslyFocused = null;
  }

  /**
   * Determine whether the modal should be shown for a given subscription payload.
   * Returns true when user has no usable access (should prompt for plan).
   * Returns false when user has access (trial/active/grace/institution).
   */
  function shouldShow(subscriptionData) {
    if (!subscriptionData) return true;

    if (typeof subscriptionData.is_active === 'boolean') {
      return !subscriptionData.is_active;
    }

    var status = subscriptionData.status;
    if (!status) return true;
    if (INACTIVE_STATUSES[status]) return true;
    return false;
  }

  // ── Auto-init ──────────────────────────────────────────────────────────

  function _autoInit() {
    if (_findModal()) {
      _bindListeners();
      init(); // Load plans from API
    }
  }

  if (typeof document !== 'undefined') {
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', _autoInit);
    } else {
      _autoInit();
    }
  }

  // ── Mock Razorpay UI Injection & Implementation ──────────────────────────

  function _injectMockRazorpayStyles() {
    if (document.getElementById('mock-rzp-styles')) return;
    var style = document.createElement('style');
    style.id = 'mock-rzp-styles';
    style.textContent = `
      .mock-rzp-overlay {
        position: fixed;
        inset: 0;
        z-index: 99999;
        background: rgba(0, 0, 0, 0.65);
        display: flex;
        align-items: center;
        justify-content: center;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        opacity: 0;
        transition: opacity 0.25s ease;
      }
      .mock-rzp-overlay.show {
        opacity: 1;
      }
      .mock-rzp-container {
        width: 375px;
        background: #ffffff;
        border-radius: 12px;
        box-shadow: 0 12px 36px rgba(0, 0, 0, 0.25);
        overflow: hidden;
        display: flex;
        flex-direction: column;
        color: #2b3040;
        transform: translateY(20px);
        transition: transform 0.25s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        box-sizing: border-box;
      }
      .mock-rzp-container * {
        box-sizing: border-box;
      }
      .mock-rzp-overlay.show .mock-rzp-container {
        transform: translateY(0);
      }
      .mock-rzp-header {
        background: #02042b;
        color: #ffffff;
        padding: 18px 24px;
        position: relative;
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 2px solid #528ff0;
      }
      .mock-rzp-merchant-info {
        display: flex;
        align-items: center;
        gap: 10px;
      }
      .mock-rzp-logo {
        width: 28px;
        height: 28px;
        background: #528ff0;
        border-radius: 6px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        font-size: 16px;
        color: #fff;
      }
      .mock-rzp-merchant-name {
        font-weight: 600;
        font-size: 15px;
        letter-spacing: 0.2px;
      }
      .mock-rzp-amount-info {
        text-align: right;
      }
      .mock-rzp-plan-name {
        font-size: 11px;
        color: #a0a5ba;
        font-weight: 500;
      }
      .mock-rzp-amount {
        font-weight: 700;
        font-size: 16px;
        color: #ffffff;
      }
      .mock-rzp-close-btn {
        background: transparent;
        border: none;
        color: #ffffff;
        font-size: 24px;
        cursor: pointer;
        position: absolute;
        top: 10px;
        right: 12px;
        opacity: 0.6;
        transition: opacity 0.2s;
        padding: 0;
        line-height: 1;
      }
      .mock-rzp-close-btn:hover {
        opacity: 1;
      }
      .mock-rzp-content {
        height: 380px;
        padding: 24px;
        overflow-y: auto;
        position: relative;
        background: #f8f9fc;
      }
      .mock-rzp-screen {
        display: none;
        flex-direction: column;
        height: 100%;
      }
      .mock-rzp-screen.active {
        display: flex;
      }
      .mock-rzp-title {
        font-size: 11px;
        font-weight: 700;
        color: #8c93a8;
        margin-bottom: 16px;
        text-transform: uppercase;
        letter-spacing: 0.8px;
      }
      .mock-rzp-method-list {
        display: flex;
        flex-direction: column;
        gap: 12px;
      }
      .mock-rzp-method-btn {
        background: #ffffff;
        border: 1px solid #e1e4ed;
        border-radius: 8px;
        padding: 14px 16px;
        display: flex;
        align-items: center;
        cursor: pointer;
        transition: all 0.2s ease;
        width: 100%;
        text-align: left;
      }
      .mock-rzp-method-btn:hover {
        border-color: #528ff0;
        background: #f5f8ff;
        box-shadow: 0 4px 12px rgba(82, 143, 240, 0.08);
      }
      .mock-rzp-method-icon {
        font-size: 20px;
        margin-right: 14px;
      }
      .mock-rzp-method-text {
        font-size: 14px;
        font-weight: 500;
        color: #2b3040;
        flex-grow: 1;
      }
      .mock-rzp-method-arrow {
        color: #a0a5ba;
        font-weight: bold;
      }
      .mock-rzp-back-btn {
        font-size: 13px;
        font-weight: 600;
        color: #528ff0;
        cursor: pointer;
        margin-bottom: 16px;
        align-self: flex-start;
        display: flex;
        align-items: center;
        gap: 4px;
      }
      .mock-rzp-back-btn:hover {
        text-decoration: underline;
      }
      .mock-rzp-form {
        display: flex;
        flex-direction: column;
        gap: 14px;
      }
      .mock-rzp-form-group {
        display: flex;
        flex-direction: column;
        gap: 6px;
      }
      .mock-rzp-form-group label {
        font-size: 10px;
        font-weight: 700;
        color: #8c93a8;
        text-transform: uppercase;
        letter-spacing: 0.5px;
      }
      .mock-rzp-form-group input {
        padding: 10px 14px;
        border: 1px solid #ccd2e0;
        border-radius: 6px;
        font-size: 14px;
        color: #2b3040;
        background: #ffffff;
        transition: border-color 0.2s;
        width: 100%;
        box-sizing: border-box;
      }
      .mock-rzp-form-group input:focus {
        outline: none;
        border-color: #528ff0;
      }
      .mock-rzp-card-input-wrapper {
        position: relative;
        display: flex;
        align-items: center;
        width: 100%;
      }
      .mock-rzp-card-brand {
        position: absolute;
        right: 14px;
        font-size: 11px;
        font-weight: 700;
        color: #528ff0;
        text-transform: uppercase;
      }
      .mock-rzp-form-row {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 12px;
      }
      .mock-rzp-pay-btn {
        background: #528ff0;
        color: #ffffff;
        border: none;
        border-radius: 6px;
        padding: 14px;
        font-size: 15px;
        font-weight: 600;
        cursor: pointer;
        transition: background 0.2s, transform 0.1s;
        margin-top: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 8px;
        width: 100%;
      }
      .mock-rzp-pay-btn:hover {
        background: #3c7ce6;
      }
      .mock-rzp-pay-btn:active {
        transform: scale(0.98);
      }
      .mock-rzp-upi-qr {
        display: flex;
        flex-direction: column;
        align-items: center;
        margin-bottom: 6px;
      }
      .mock-rzp-qr-box {
        width: 110px;
        height: 110px;
        border: 4px solid #000;
        background: #fff;
        position: relative;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 6px;
      }
      .mock-rzp-qr-logo {
        font-size: 9px;
        font-weight: 700;
        background: #fff;
        padding: 2px 4px;
        border: 1px solid #000;
        z-index: 5;
      }
      .mock-rzp-qr-dots {
        position: absolute;
        inset: 8px;
        background-image: radial-gradient(#000 30%, transparent 30%);
        background-size: 5px 5px;
      }
      .mock-rzp-qr-tip {
        font-size: 12px;
        color: #71778c;
        margin: 8px 0 0;
        font-weight: 500;
      }
      .mock-rzp-divider {
        display: flex;
        align-items: center;
        text-align: center;
        color: #a0a5ba;
        font-size: 11px;
        font-weight: 600;
        margin: 4px 0;
      }
      .mock-rzp-divider::before, .mock-rzp-divider::after {
        content: '';
        flex: 1;
        border-bottom: 1px solid #e1e4ed;
      }
      .mock-rzp-divider:not(:empty)::before {
        margin-right: .5em;
      }
      .mock-rzp-divider:not(:empty)::after {
        margin-left: .5em;
      }
      .mock-rzp-netbanking-list {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 10px;
      }
      .mock-rzp-bank-btn {
        background: #ffffff;
        border: 1px solid #e1e4ed;
        border-radius: 6px;
        padding: 12px;
        font-size: 13px;
        font-weight: 500;
        color: #2b3040;
        cursor: pointer;
        text-align: center;
        transition: all 0.2s;
        width: 100%;
      }
      .mock-rzp-bank-btn:hover {
        border-color: #528ff0;
        background: #f5f8ff;
        color: #528ff0;
      }
      .mock-rzp-processing-box {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        height: 100%;
        text-align: center;
      }
      .mock-rzp-spinner {
        width: 44px;
        height: 44px;
        border: 4px solid #e1e4ed;
        border-top-color: #528ff0;
        border-radius: 50%;
        animation: mockRzpSpin 1s infinite linear;
        margin-bottom: 20px;
      }
      @keyframes mockRzpSpin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
      }
      .mock-rzp-processing-title {
        font-size: 16px;
        font-weight: 600;
        color: #2b3040;
        margin-bottom: 8px;
      }
      .mock-rzp-processing-text {
        font-size: 12px;
        color: #71778c;
        margin: 0;
      }
      .mock-rzp-success-box {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        height: 100%;
        text-align: center;
      }
      .mock-rzp-success-checkmark {
        width: 80px;
        height: 80px;
        margin-bottom: 20px;
      }
      .mock-rzp-check-icon {
        width: 80px;
        height: 80px;
        position: relative;
        border-radius: 50%;
        box-sizing: border-box;
        border: 4px solid #4caf50;
        display: flex;
        align-items: center;
        justify-content: center;
      }
      .mock-rzp-icon-line {
        height: 5px;
        background-color: #4caf50;
        display: block;
        border-radius: 2px;
        position: absolute;
        z-index: 10;
      }
      .mock-rzp-line-tip {
        width: 18px;
        left: 21px;
        top: 44px;
        transform: rotate(45deg);
        transform-origin: left;
        animation: mockRzpTip 0.3s ease-out forwards;
      }
      .mock-rzp-line-long {
        width: 36px;
        left: 32px;
        top: 44px;
        transform: rotate(-45deg);
        transform-origin: left;
        animation: mockRzpLong 0.4s ease-out 0.25s forwards;
        opacity: 0;
      }
      @keyframes mockRzpTip {
        from { width: 0; }
        to { width: 18px; }
      }
      @keyframes mockRzpLong {
        from { width: 0; opacity: 0; }
        to { width: 36px; opacity: 1; }
      }
      .mock-rzp-success-title {
        font-size: 18px;
        font-weight: 700;
        color: #4caf50;
        margin-bottom: 8px;
      }
      .mock-rzp-success-text {
        font-size: 13px;
        color: #71778c;
        margin: 0;
      }
      .mock-rzp-footer {
        background: #f1f3f9;
        padding: 12px;
        text-align: center;
        font-size: 11px;
        font-weight: 600;
        color: #8c93a8;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 6px;
        border-top: 1px solid #e1e4ed;
      }
    `;
    document.head.appendChild(style);
  }

  function _showMockCheckoutPopup(plan, orderId, onVerified, onCancel) {
    var existing = document.getElementById('mockRazorpayOverlay');
    if (existing) {
      existing.remove();
    }

    var overlay = document.createElement('div');
    overlay.id = 'mockRazorpayOverlay';
    overlay.className = 'mock-rzp-overlay';
    
    var priceStr = plan.price ? plan.price.toLocaleString('en-IN', { minimumFractionDigits: 2 }) : '0.00';

    overlay.innerHTML = `
      <div class="mock-rzp-container">
        <div class="mock-rzp-header">
          <div class="mock-rzp-merchant-info">
            <div class="mock-rzp-logo">S</div>
            <div class="mock-rzp-merchant-name">SmartKCET Prep</div>
          </div>
          <div class="mock-rzp-amount-info">
            <div class="mock-rzp-plan-name">${plan.name}</div>
            <div class="mock-rzp-amount">₹${priceStr}</div>
          </div>
          <button class="mock-rzp-close-btn" id="mockRzpCloseBtn">&times;</button>
        </div>
        
        <div class="mock-rzp-content">
          <div class="mock-rzp-screen active" id="mockRzpScreenMethods">
            <div class="mock-rzp-title">Choose Payment Method</div>
            <div class="mock-rzp-method-list">
              <button class="mock-rzp-method-btn" id="mockRzpMethodCard">
                <span class="mock-rzp-method-icon">💳</span>
                <span class="mock-rzp-method-text">Card (Visa, Mastercard, RuPay)</span>
                <span class="mock-rzp-method-arrow">&rarr;</span>
              </button>
              <button class="mock-rzp-method-btn" id="mockRzpMethodUpi">
                <span class="mock-rzp-method-icon">📱</span>
                <span class="mock-rzp-method-text">UPI (GPay, PhonePe, QR)</span>
                <span class="mock-rzp-method-arrow">&rarr;</span>
              </button>
              <button class="mock-rzp-method-btn" id="mockRzpMethodNet">
                <span class="mock-rzp-method-icon">🏦</span>
                <span class="mock-rzp-method-text">Netbanking (SBI, HDFC, ICICI)</span>
                <span class="mock-rzp-method-arrow">&rarr;</span>
              </button>
            </div>
          </div>
          
          <div class="mock-rzp-screen" id="mockRzpScreenCard">
            <div class="mock-rzp-back-btn" id="mockRzpBackBtnCard">&larr; Back</div>
            <div class="mock-rzp-title">Enter Card Details</div>
            <div class="mock-rzp-form">
              <div class="mock-rzp-form-group">
                <label>Card Number</label>
                <div class="mock-rzp-card-input-wrapper">
                  <input type="text" id="mockRzpCardNumber" placeholder="4111 1111 1111 1111" maxlength="19">
                  <span class="mock-rzp-card-brand" id="mockRzpCardBrand">Visa</span>
                </div>
              </div>
              <div class="mock-rzp-form-row">
                <div class="mock-rzp-form-group">
                  <label>Expiry Date</label>
                  <input type="text" id="mockRzpCardExpiry" placeholder="MM/YY" maxlength="5">
                </div>
                <div class="mock-rzp-form-group">
                  <label>CVV</label>
                  <input type="password" id="mockRzpCardCvv" placeholder="•••" maxlength="3">
                </div>
              </div>
              <div class="mock-rzp-form-group">
                <label>Cardholder Name</label>
                <input type="text" id="mockRzpCardName" placeholder="Cardholder Name">
              </div>
              <div class="mock-rzp-form-group" style="margin-top: 4px;">
                <label style="font-size: 9px; color: #8c93a8; margin-bottom: 4px;">Test Card Shortcuts</label>
                <div style="display: flex; gap: 8px;">
                  <button type="button" id="mockRzpVisaFill" style="flex: 1; padding: 6px; font-size: 11px; font-weight: 600; background: #f1f3f9; border: 1px solid #ccd2e0; border-radius: 4px; color: #515970; cursor: pointer; text-align: center;">Visa (Success)</button>
                  <button type="button" id="mockRzpMcFill" style="flex: 1; padding: 6px; font-size: 11px; font-weight: 600; background: #f1f3f9; border: 1px solid #ccd2e0; border-radius: 4px; color: #515970; cursor: pointer; text-align: center;">Mastercard</button>
                </div>
              </div>
              <button class="mock-rzp-pay-btn" id="mockRzpCardPayBtn">Pay ₹${priceStr}</button>
            </div>
          </div>

          <div class="mock-rzp-screen" id="mockRzpScreenUpi">
            <div class="mock-rzp-back-btn" id="mockRzpBackBtnUpi">&larr; Back</div>
            <div class="mock-rzp-title">Pay via UPI</div>
            <div class="mock-rzp-form">
              <div class="mock-rzp-upi-qr">
                <div class="mock-rzp-qr-box">
                  <div class="mock-rzp-qr-logo">Razorpay</div>
                  <div class="mock-rzp-qr-dots"></div>
                </div>
                <p class="mock-rzp-qr-tip">Scan QR using your preferred UPI app</p>
              </div>
              <div class="mock-rzp-divider"><span>OR</span></div>
              <div class="mock-rzp-form-group">
                <label>Enter UPI ID</label>
                <input type="text" id="mockRzpUpiId" placeholder="username@upi">
              </div>
              <button class="mock-rzp-pay-btn" id="mockRzpUpiPayBtn">Pay ₹${priceStr}</button>
            </div>
          </div>

          <div class="mock-rzp-screen" id="mockRzpScreenNet">
            <div class="mock-rzp-back-btn" id="mockRzpBackBtnNet">&larr; Back</div>
            <div class="mock-rzp-title">Select Bank</div>
            <div class="mock-rzp-netbanking-list">
              <button class="mock-rzp-bank-btn" data-bank="SBI">SBI</button>
              <button class="mock-rzp-bank-btn" data-bank="HDFC">HDFC Bank</button>
              <button class="mock-rzp-bank-btn" data-bank="ICICI">ICICI Bank</button>
              <button class="mock-rzp-bank-btn" data-bank="AXIS">Axis Bank</button>
              <button class="mock-rzp-bank-btn" data-bank="KOTAK">Kotak Bank</button>
              <button class="mock-rzp-bank-btn" data-bank="YES">Yes Bank</button>
            </div>
          </div>
          
          <div class="mock-rzp-screen" id="mockRzpScreenProcessing">
            <div class="mock-rzp-processing-box">
              <div class="mock-rzp-spinner"></div>
              <div class="mock-rzp-processing-title">Securing your transaction...</div>
              <p class="mock-rzp-processing-text">Please do not refresh the page or click back.</p>
            </div>
          </div>
          
          <div class="mock-rzp-screen" id="mockRzpScreenSuccess">
            <div class="mock-rzp-success-box">
              <div class="mock-rzp-success-checkmark">
                <div class="mock-rzp-check-icon">
                  <span class="mock-rzp-icon-line mock-rzp-line-tip"></span>
                  <span class="mock-rzp-icon-line mock-rzp-line-long"></span>
                </div>
              </div>
              <div class="mock-rzp-success-title">Payment Successful!</div>
              <p class="mock-rzp-success-text">Redirecting you back to SmartKCET...</p>
            </div>
          </div>
        </div>
        
        <div class="mock-rzp-footer">
          <span class="mock-rzp-lock-icon">🔒</span>
          <span>Secured by Razorpay Sandbox Mock</span>
        </div>
      </div>
    `;

    document.body.appendChild(overlay);

    setTimeout(function () {
      overlay.classList.add('show');
    }, 10);

    var screenMethods = document.getElementById('mockRzpScreenMethods');
    var screenCard = document.getElementById('mockRzpScreenCard');
    var screenUpi = document.getElementById('mockRzpScreenUpi');
    var screenNet = document.getElementById('mockRzpScreenNet');
    var screenProcessing = document.getElementById('mockRzpScreenProcessing');
    var screenSuccess = document.getElementById('mockRzpScreenSuccess');

    var btnClose = document.getElementById('mockRzpCloseBtn');
    
    var btnCard = document.getElementById('mockRzpMethodCard');
    var btnUpi = document.getElementById('mockRzpMethodUpi');
    var btnNet = document.getElementById('mockRzpMethodNet');

    var btnBackCard = document.getElementById('mockRzpBackBtnCard');
    var btnBackUpi = document.getElementById('mockRzpBackBtnUpi');
    var btnBackNet = document.getElementById('mockRzpBackBtnNet');

    var inputCardNumber = document.getElementById('mockRzpCardNumber');
    var inputCardExpiry = document.getElementById('mockRzpCardExpiry');
    var inputCardCvv = document.getElementById('mockRzpCardCvv');
    var cardBrandText = document.getElementById('mockRzpCardBrand');

    var btnPayCard = document.getElementById('mockRzpCardPayBtn');
    var btnPayUpi = document.getElementById('mockRzpUpiPayBtn');
    var netBankButtons = document.querySelectorAll('.mock-rzp-bank-btn');

    function showScreen(screen) {
      [screenMethods, screenCard, screenUpi, screenNet, screenProcessing, screenSuccess].forEach(function (s) {
        s.classList.remove('active');
      });
      screen.classList.add('active');
    }

    function dismiss() {
      overlay.classList.remove('show');
      setTimeout(function () {
        overlay.remove();
      }, 250);
    }

    btnClose.onclick = function () {
      dismiss();
      onCancel();
    };

    btnCard.onclick = function () { showScreen(screenCard); };
    btnUpi.onclick = function () { showScreen(screenUpi); };
    btnNet.onclick = function () { showScreen(screenNet); };

    btnBackCard.onclick = function () { showScreen(screenMethods); };
    btnBackUpi.onclick = function () { showScreen(screenMethods); };
    btnBackNet.onclick = function () { showScreen(screenMethods); };

    inputCardNumber.oninput = function (e) {
      var val = e.target.value.replace(/\s+/g, '').replace(/[^0-9]/gi, '');
      var parts = [];
      for (var i = 0, len = val.length; i < len; i += 4) {
        parts.push(val.substring(i, i + 4));
      }
      e.target.value = parts.join(' ');

      if (val.startsWith('4')) {
        cardBrandText.innerText = 'Visa';
      } else if (val.startsWith('5')) {
        cardBrandText.innerText = 'Mastercard';
      } else {
        cardBrandText.innerText = 'Card';
      }
    };

    inputCardExpiry.oninput = function (e) {
      var val = e.target.value.replace(/\//g, '').replace(/[^0-9]/gi, '');
      if (val.length >= 2) {
        e.target.value = val.substring(0, 2) + '/' + val.substring(2, 4);
      } else {
        e.target.value = val;
      }
    };

    async function triggerSuccess() {
      showScreen(screenProcessing);
      setTimeout(async function () {
        showScreen(screenSuccess);
        setTimeout(async function () {
          dismiss();
          await onVerified('pay_mock_' + Date.now(), 'mock_sig');
        }, 1800);
      }, 1500);
    }

    btnPayCard.onclick = function () {
      var cardNum = inputCardNumber.value.replace(/\s+/g, '');
      var expiry = inputCardExpiry.value;
      var cvv = inputCardCvv.value;
      if (cardNum.length < 16) {
        alert('Please enter a valid 16-digit card number.');
        return;
      }
      if (expiry.length < 5) {
        alert('Please enter expiry in MM/YY format.');
        return;
      }
      if (cvv.length < 3) {
        alert('Please enter CVV.');
        return;
      }
      triggerSuccess();
    };

    btnPayUpi.onclick = function () {
      var upiId = document.getElementById('mockRzpUpiId').value;
      if (!upiId || !upiId.includes('@')) {
        alert('Please enter a valid UPI ID (e.g., success@razorpay).');
        return;
      }
      triggerSuccess();
    };

    netBankButtons.forEach(function (btn) {
      btn.onclick = function () {
        triggerSuccess();
      };
    });

    var visaFill = document.getElementById('mockRzpVisaFill');
    var mcFill = document.getElementById('mockRzpMcFill');

    visaFill.onclick = function (e) {
      e.preventDefault();
      inputCardNumber.value = '4111 1111 1111 1111';
      inputCardExpiry.value = '12/30';
      inputCardCvv.value = '123';
      document.getElementById('mockRzpCardName').value = 'John Doe';
      cardBrandText.innerText = 'Visa';
    };

    mcFill.onclick = function (e) {
      e.preventDefault();
      inputCardNumber.value = '5123 4567 8901 2345';
      inputCardExpiry.value = '12/30';
      inputCardCvv.value = '123';
      document.getElementById('mockRzpCardName').value = 'Jane Doe';
      cardBrandText.innerText = 'Mastercard';
    };
  }

  // ── Expose public interface ─────────────────────────────────────────────

  return {
    init: init,
    show: show,
    hide: hide,
    selectFree: selectFree,
    selectTrial: selectTrial,
    selectMonthly: selectMonthly,
    selectYearly: selectYearly,
    shouldShow: shouldShow,
  };
})();

// CommonJS export for unit tests (no-op in browsers).
if (typeof module !== 'undefined' && module.exports) {
  module.exports = SubscriptionModal;
}
