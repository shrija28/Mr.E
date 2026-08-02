// SmartKCET Prep — Institution Portal Access Control
// Blocks access to feature pages when institution has no active subscription.
// Protected pages: /institution/upload, /institution/questions, /institution/exams, 
// /institution/students, /institution/analytics
//
// When user tries to access a protected page without a subscription:
// 1. Fetch subscription status from API
// 2. If null → show blocking popup
// 3. User must select a subscription plan or return to dashboard

var InstitutionAccessControl = (function () {
  'use strict';

  // List of protected feature pages that require active subscription
  var PROTECTED_PAGES = [
    '/institution/upload',
    '/institution/questions',
    '/institution/exams',
    '/institution/students',
    '/institution/analytics',
  ];

  // Check if current page is a protected page
  function _isProtectedPage() {
    var pathname = window.location.pathname;
    return PROTECTED_PAGES.some(function (page) {
      return pathname.startsWith(page);
    });
  }

  /**
   * Fetch the current subscription status from the API.
   * Returns: { subscription_status: null|'active'|'trial'|'overdue'|etc }
   */
  async function _checkSubscriptionStatus() {
    try {
      var response = await fetch('/api/institution/subscription', {
        method: 'GET',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
      });

      if (!response.ok) {
        // If 404, assume no subscription
        if (response.status === 404) {
          return { subscription_status: null };
        }
        // If 401, user is not authenticated
        if (response.status === 401) {
          return { error: 'unauthorized' };
        }
        return { error: 'failed' };
      }

      return await response.json();
    } catch (error) {
      console.error('Failed to check subscription status:', error);
      return { error: 'network_error' };
    }
  }

  /**
   * Show blocking popup when user tries to access a protected page without subscription.
   * User can either navigate to subscription page or return to dashboard.
   */
  function _showAccessBlockedPopup(currentPage) {
    // Create overlay
    var overlay = document.createElement('div');
    overlay.id = 'institutionAccessBlocker';
    overlay.style.cssText = `
      position: fixed;
      inset: 0;
      background: rgba(0, 0, 0, 0.75);
      backdrop-filter: blur(8px);
      z-index: 400;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 20px;
    `;

    // Create dialog
    var dialog = document.createElement('div');
    dialog.style.cssText = `
      background: var(--s1);
      border: 1px solid var(--border2);
      border-radius: 14px;
      padding: 36px;
      max-width: 480px;
      width: 100%;
      box-shadow: 0 24px 60px rgba(0, 0, 0, 0.45);
      animation: modalPop 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
    `;
    dialog.innerHTML = `
      <div style="text-align: center; margin-bottom: 28px;">
        <div style="font-size: 2.8rem; margin-bottom: 12px;">🔒</div>
        <h2 style="font-size: 1.4rem; font-weight: 800; margin: 0 0 6px;">Subscription Required</h2>
        <p style="color: var(--muted); font-size: 0.88rem; margin: 0;">This feature requires an active subscription. Please select a plan to continue.</p>
      </div>
      <div style="display: flex; gap: 10px; margin-bottom: 16px;">
        <button class="btn-institution" style="flex: 1; display: flex; align-items: center; justify-content: center; gap: 8px;" id="goToPlanBtn">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width: 16px; height: 16px;"><rect x="2" y="5" width="20" height="14" rx="2"/><line x1="2" y1="10" x2="22" y2="10"/></svg>
          Select Plan
        </button>
      </div>
      <button class="btn-institution-outline" style="width: 100%; display: flex; align-items: center; justify-content: center; gap: 8px;" id="returnToDashboardBtn">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width: 16px; height: 16px;"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></svg>
        Back to Dashboard
      </button>
    `;

    overlay.appendChild(dialog);
    document.body.appendChild(overlay);

    // Wire buttons
    var planBtn = document.getElementById('goToPlanBtn');
    if (planBtn) {
      planBtn.addEventListener('click', function () {
        window.location.href = '/institution/subscription';
      });
    }

    var dashboardBtn = document.getElementById('returnToDashboardBtn');
    if (dashboardBtn) {
      dashboardBtn.addEventListener('click', function () {
        window.location.href = '/institution/dashboard';
      });
    }

    // Prevent scrolling on the background
    document.body.style.overflow = 'hidden';
    
    // Allow clicks ONLY on the overlay and its buttons (not on the disabled page)
    document.addEventListener('click', function (e) {
      // Allow clicks on overlay and buttons inside it
      if (!overlay.contains(e.target)) {
        e.preventDefault();
        e.stopPropagation();
      }
    }, true);
  }

  /**
   * Check subscription and block access if needed.
   * Call this on DOMContentLoaded for all protected pages.
   */
  async function checkAccess() {
    // Only run on protected pages
    if (!_isProtectedPage()) {
      return;
    }

    // Check subscription status
    var status = await _checkSubscriptionStatus();

    // If there's an error, allow access (don't block on network errors)
    if (status.error) {
      console.warn('Access control check failed:', status.error);
      return;
    }

    // If subscription_status is null, block access
    if (status.subscription_status === null || status.subscription_status === undefined) {
      // Show blocking popup
      _showAccessBlockedPopup(window.location.pathname);

      // Prevent navigation away from the modal (block clicks on page content)
      document.addEventListener('click', function (e) {
        // Allow clicks only if they're inside the overlay
        var overlay = document.getElementById('institutionAccessBlocker');
        if (overlay && !overlay.contains(e.target)) {
          e.preventDefault();
          e.stopPropagation();
        }
      }, true);

      return false;
    }

    // If subscription is active, allow access
    return true;
  }

  /**
   * Expose public interface
   */
  return {
    checkAccess: checkAccess,
    isProtectedPage: _isProtectedPage,
  };
})();

// Run access control check on page load
if (typeof document !== 'undefined') {
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () {
      if (typeof InstitutionAccessControl !== 'undefined') {
        InstitutionAccessControl.checkAccess();
      }
    });
  } else {
    // DOM already loaded
    if (typeof InstitutionAccessControl !== 'undefined') {
      InstitutionAccessControl.checkAccess();
    }
  }
}
