// Mr.E — Auth Client Module
// Shared authentication helpers for login, register, logout, and role checks.
// All calls use credentials: 'include' so the httpOnly cookie is sent.
// Tokens are NEVER read from or written to localStorage (REQ-14.5).

var Auth = (function () {
  'use strict';

  // ── Internal helpers ─────────────────────────────────────────────────────

  /**
   * POST JSON to the given path with credentials: 'include'.
   * Returns the parsed JSON response and the raw Response object.
   */
  async function _post(path, body) {
    var res = await fetch(path, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify(body),
    });
    var data;
    try {
      data = await res.json();
    } catch (e) {
      data = null;
    }
    return { ok: res.ok, status: res.status, data: data };
  }

  /**
   * GET from the given path with credentials: 'include'.
   */
  async function _get(path) {
    var res = await fetch(path, {
      method: 'GET',
      credentials: 'include',
    });
    var data;
    try {
      data = await res.json();
    } catch (e) {
      data = null;
    }
    return { ok: res.ok, status: res.status, data: data };
  }

  // ── Public API ───────────────────────────────────────────────────────────

  /**
   * Student login.
   * POST /api/auth/login with email and password.
   * Returns { ok, status, data } where data contains role info on success.
   * On 503 (DB unavailable), returns a structured error blocking dashboard access.
   */
  async function login(email, password) {
    var result = await _post('/api/auth/login', { email: email, password: password });
    if (result.status === 503) {
      return {
        ok: false,
        status: 503,
        data: { message: 'Service temporarily unavailable. Please try again later.' },
      };
    }
    return result;
  }

  /**
   * Admin login.
   * POST /api/auth/admin/login with email and password.
   * Returns { ok, status, data } where data contains role info on success.
   * On 503 (DB unavailable), returns a structured error blocking dashboard access.
   */
  async function adminLogin(email, password) {
    var result = await _post('/api/auth/admin/login', { email: email, password: password });
    if (result.status === 503) {
      return {
        ok: false,
        status: 503,
        data: { message: 'Service temporarily unavailable. Please try again later.' },
      };
    }
    return result;
  }

  /**
   * Institution admin login.
   * POST /api/auth/institution/login with email and password.
   * Returns { ok, status, data } where data contains role info on success.
   */
  async function institutionLogin(email, password) {
    var result = await _post('/api/auth/institution/login', { email: email, password: password });
    if (result.status === 503) {
      return {
        ok: false,
        status: 503,
        data: { message: 'Service temporarily unavailable. Please try again later.' },
      };
    }
    return result;
  }

  /**
   * Register a new student account.
   * POST /api/auth/register with email, password, and displayName.
   * Returns { ok, status, data } where data contains kcet_student_id on success.
   */
  async function register(opts) {
    return _post('/api/auth/register', {
      email: opts.email,
      password: opts.password,
      display_name: opts.displayName,
    });
  }

  /**
   * Register a new institution.
   * POST /api/institution/register with institution_name, email, and password.
   * Returns { ok, status, data } where data contains institution_id on success.
   */
  async function institutionRegister(institutionName, email, password) {
    return _post('/api/institution/register', {
      name: institutionName,
      admin_email: email,
      admin_password: password,
    });
  }

  /**
   * Logout the current session.
   * POST /api/auth/logout, then redirect to /login.
   */
  async function logout() {
    await _post('/api/auth/logout', {});
    window.location.href = '/login';
  }

  /**
   * Get the current user's role by calling GET /api/auth/me.
   * Since the cookie is httpOnly, we cannot decode it client-side.
   * Returns { authenticated, role, sub, ... } on success, or null if not authenticated.
   * On the login page, silently returns null on any error (including 401)
   * to prevent redirect loops.
   */
  async function currentRole() {
    try {
      var result = await _get('/api/auth/me');
      if (result.ok && result.data && result.data.authenticated) {
        return result.data;
      }
      // On 401 or other errors, just return null (not authenticated)
      return null;
    } catch (e) {
      // Fetch errors (network, etc) - silently return null
      console.error('[Auth.currentRole] Error:', e);
      return null;
    }
  }

  /**
   * Check if the user is authenticated and redirect accordingly:
   * - Institution students → /student/institution/dashboard
   * - Personal students → /dashboard
   * - Platform admins → /admin/upload
   * - Institution admins → /institution/dashboard
   * Returns the user info if authenticated, or null if not.
   */
  async function redirectIfAuthenticated() {
    var user = await currentRole();
    if (user) {
      if (user.role === 'admin' || user.role === 'platform_admin') {
        window.location.href = '/admin/upload';
      } else if (user.role === 'student') {
        if (user.student_subtype === 'institution_linked') {
          window.location.href = '/student/institution/dashboard';
        } else {
          window.location.href = '/dashboard';
        }
      } else if (user.role === 'institution_admin') {
        window.location.href = '/institution/dashboard';
      }
    }
    return user;
  }

  // ── Expose public interface ──────────────────────────────────────────────

  return {
    login: login,
    adminLogin: adminLogin,
    institutionLogin: institutionLogin,
    register: register,
    institutionRegister: institutionRegister,
    logout: logout,
    currentRole: currentRole,
    redirectIfAuthenticated: redirectIfAuthenticated,
  };
})();
