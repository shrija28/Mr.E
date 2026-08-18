// Mr.E — Client-side Router Module
// Handles role-based access control, link interception, and browser
// back/forward navigation for the Mr.E frontend. Because the
// FastAPI backend serves the HTML files directly (see
// `backend/smartkcet/routes/pages.py`), this router primarily owns the
// client-side concerns:
//   * declaring the route table (path → htmlFile, allowedRoles, title)
//   * intercepting `<a href="/...">` clicks so we can validate roles
//     before the browser performs a full-page navigation
//   * responding to `popstate` (browser back/forward) by re-validating
//     the current route against the active session
//   * exposing `redirectByRole()` so other modules (e.g. login flow,
//     access guards) can send the user to their role's home page
//   * handling unknown routes via a custom 404 page (REQ-15.9)
//
// Public API mirrors the design doc:
//   Router.init()                       — install listeners, validate page
//   Router.navigate(path)               — programmatic navigation
//   Router.handleRoute(path?)           — validate the given/current path
//   Router.redirectByRole(role?)        — go to the role's home page
//   Router.requireAuth()                — guard helper for page scripts
//   Router.showNotFound(path?)          — navigate to the 404 page
//
// Requirements: 15.1, 15.5, 15.6, 15.7, 15.8, 15.9, 15.11

var Router = (function () {
  'use strict';

  // ── Route configuration ─────────────────────────────────────────────────
  //
  // Each route entry describes:
  //   * `htmlFile`      — path to the HTML file the backend serves
  //   * `allowedRoles`  — roles permitted to view this page (empty/omit
  //                        for public pages)
  //   * `requiresAuth`  — whether a valid session cookie is required
  //   * `title`         — used to update `document.title`
  //
  // Roles match the values returned by `GET /api/auth/me`:
  //   'student', 'institution_admin', 'platform_admin'.

  var ROUTES = {
    // ── Public routes ────────────────────────────────────────────────────
    '/': {
      htmlFile: '/html/landing.html',
      requiresAuth: false,
      title: 'Mr.E',
    },
    '/login': {
      htmlFile: '/html/login.html',
      requiresAuth: false,
      title: 'Login',
    },
    '/signup': {
      htmlFile: '/html/register.html',
      requiresAuth: false,
      title: 'Sign Up',
    },
    '/register': {
      htmlFile: '/html/register.html',
      requiresAuth: false,
      title: 'Register',
    },
    '/invitation-accept': {
      htmlFile: '/html/invitation-accept.html',
      requiresAuth: false,
      title: 'Accept Invitation',
    },
    '/invitation/accept': {
      htmlFile: '/html/invitation-accept.html',
      requiresAuth: false,
      title: 'Accept Invitation',
    },
    '/not-found': {
      htmlFile: '/html/not-found.html',
      requiresAuth: false,
      title: 'Page Not Found',
    },
    '/contact-us': {
      htmlFile: '/html/contact-us.html',
      requiresAuth: true,
      title: 'Contact Us',
    },

    // ── Student routes ───────────────────────────────────────────────────
    '/dashboard': {
      htmlFile: '/html/dashboard.html',
      requiresAuth: true,
      allowedRoles: ['student'],
      title: 'Dashboard',
    },
    '/exam': {
      htmlFile: '/html/exam.html',
      requiresAuth: true,
      allowedRoles: ['student'],
      title: 'Exam',
    },
    '/results': {
      htmlFile: '/html/results.html',
      requiresAuth: true,
      allowedRoles: ['student'],
      title: 'Results',
    },
    '/leaderboard': {
      htmlFile: '/html/leaderboard.html',
      requiresAuth: true,
      allowedRoles: ['student'],
      title: 'Leaderboard',
    },
    '/subscription': {
      htmlFile: '/html/subscription.html',
      requiresAuth: true,
      allowedRoles: ['student'],
      title: 'Subscription',
    },
    '/pricing': {
      htmlFile: '/html/student-pricing.html',
      requiresAuth: true,
      allowedRoles: ['student'],
      title: 'Premium Plans',
    },

    // ── Institution Student Platform routes ──────────────────────────────
    '/student/institution/dashboard': {
      htmlFile: '/html/student-institution-dashboard.html',
      requiresAuth: true,
      allowedRoles: ['student'],
      title: 'Institution Dashboard',
    },
    '/student/institution/exams': {
      htmlFile: '/html/student-institution-exams.html',
      requiresAuth: true,
      allowedRoles: ['student'],
      title: 'My Exams',
    },
    '/student/institution/performance': {
      htmlFile: '/html/student-institution-performance.html',
      requiresAuth: true,
      allowedRoles: ['student'],
      title: 'Performance',
    },
    '/student/institution/leaderboard': {
      htmlFile: '/html/student-institution-leaderboard.html',
      requiresAuth: true,
      allowedRoles: ['student'],
      title: 'Leaderboard',
    },

    // ── Institution admin routes ─────────────────────────────────────────
    '/institution/dashboard': {
      htmlFile: '/html/institution-dashboard.html',
      requiresAuth: true,
      allowedRoles: ['institution_admin'],
      title: 'Institution Dashboard',
    },
    '/institution/upload': {
      htmlFile: '/html/institution-upload.html',
      requiresAuth: true,
      allowedRoles: ['institution_admin'],
      title: 'Upload',
    },
    '/institution/questions': {
      htmlFile: '/html/institution-questions.html',
      requiresAuth: true,
      allowedRoles: ['institution_admin'],
      title: 'Questions',
    },
    '/institution/exams': {
      htmlFile: '/html/institution-exams.html',
      requiresAuth: true,
      allowedRoles: ['institution_admin'],
      title: 'Exams',
    },
    '/institution/students': {
      htmlFile: '/html/institution-students.html',
      requiresAuth: true,
      allowedRoles: ['institution_admin'],
      title: 'Manage Students',
    },
    '/institution/analytics': {
      htmlFile: '/html/institution-analytics.html',
      requiresAuth: true,
      allowedRoles: ['institution_admin'],
      title: 'Analytics',
    },
    '/institution/subscription': {
      htmlFile: '/html/institution-subscription.html',
      requiresAuth: true,
      allowedRoles: ['institution_admin'],
      title: 'Institution Subscription',
    },
    '/institution/pricing': {
      htmlFile: '/html/institution-pricing.html',
      requiresAuth: true,
      allowedRoles: ['institution_admin'],
      title: 'Institution Pricing',
    },
    '/institution/syllabus': {
      htmlFile: '/html/institution-syllabus.html',
      requiresAuth: true,
      allowedRoles: ['institution_admin'],
      title: 'KCET Syllabus',
    },

    // ── Platform admin routes ────────────────────────────────────────────
    '/admin': {
      htmlFile: '/html/admin-upload.html',
      requiresAuth: true,
      allowedRoles: ['platform_admin'],
      title: 'Admin',
    },
    '/admin/upload': {
      htmlFile: '/html/admin-upload.html',
      requiresAuth: true,
      allowedRoles: ['platform_admin'],
      title: 'Admin Upload',
    },
    '/admin/questions': {
      htmlFile: '/html/admin-questions.html',
      requiresAuth: true,
      allowedRoles: ['platform_admin'],
      title: 'Admin Questions',
    },
    '/admin/exams': {
      htmlFile: '/html/admin-exams.html',
      requiresAuth: true,
      allowedRoles: ['platform_admin'],
      title: 'Admin Exams',
    },
    '/admin/analytics': {
      htmlFile: '/html/admin-analytics.html',
      requiresAuth: true,
      allowedRoles: ['platform_admin'],
      title: 'Admin Analytics',
    },
    '/admin/dashboard': {
      htmlFile: '/html/admin-dashboard.html',
      requiresAuth: true,
      allowedRoles: ['platform_admin', 'admin'],
      title: 'Admin Dashboard',
    },
    '/admin/syllabus': {
      htmlFile: '/html/admin-syllabus.html',
      requiresAuth: true,
      allowedRoles: ['platform_admin', 'admin'],
      title: 'KCET Syllabus',
    },
    '/admin/institutions': {
      htmlFile: '/html/admin-institutions.html',
      requiresAuth: true,
      allowedRoles: ['platform_admin', 'admin'],
      title: 'Institutions',
    },
    '/admin/subscriptions': {
      htmlFile: '/html/admin-subscriptions.html',
      requiresAuth: true,
      allowedRoles: ['platform_admin', 'admin'],
      title: 'Subscriptions',
    },
    '/admin/students': {
      htmlFile: '/html/admin-students.html',
      requiresAuth: true,
      allowedRoles: ['platform_admin', 'admin'],
      title: 'Students',
    },
  };

  // Role → home page mapping used by `redirectByRole()` (REQ-15.6, 15.7, 15.8).
  // The legacy "admin" alias is retained for backward compatibility with
  // older /api/auth/me payloads that returned "admin" instead of
  // "platform_admin".
  var ROLE_HOME = {
    student: '/dashboard',               // personal students
    institution_student: '/student/institution/dashboard',  // institution-linked
    institution_admin: '/institution/dashboard',
    platform_admin: '/admin/dashboard',
    admin: '/admin/dashboard',
  };

  // Roles that should be normalised before role-table lookups. The
  // backend may return either the new "platform_admin" identifier or
  // the legacy "admin" alias; both should map to the same home page
  // and allowed-roles entry.
  var ROLE_ALIASES = {
    admin: 'platform_admin',
  };

  // Path of the static 404 page (REQ-15.9).
  var NOT_FOUND_PATH = '/not-found';

  // ── Internal state ──────────────────────────────────────────────────────

  var _initialized = false;
  var _clickHandler = null;
  var _popstateHandler = null;

  // ── Helpers ─────────────────────────────────────────────────────────────

  /**
   * Normalize a path by stripping query string, fragment, and any
   * trailing slash (except for the root "/"). Returns the cleaned path.
   */
  function _normalizePath(path) {
    if (!path) return '/';
    var cleaned = String(path).split('?')[0].split('#')[0];
    if (cleaned.length > 1 && cleaned.charAt(cleaned.length - 1) === '/') {
      cleaned = cleaned.slice(0, -1);
    }
    return cleaned || '/';
  }

  /**
   * Look up a route definition by path. Returns the matching entry or
   * `null` if the path does not correspond to a known route.
   */
  function _findRoute(path) {
    var key = _normalizePath(path);
    if (Object.prototype.hasOwnProperty.call(ROUTES, key)) {
      return ROUTES[key];
    }
    return null;
  }

  /**
   * Normalise a role string, applying any aliases configured in
   * `ROLE_ALIASES` (e.g. legacy "admin" → "platform_admin"). Returns
   * the original value when no alias is registered.
   */
  function _canonicalRole(role) {
    if (!role) return null;
    if (Object.prototype.hasOwnProperty.call(ROLE_ALIASES, role)) {
      return ROLE_ALIASES[role];
    }
    return role;
  }

  /**
   * Check whether `role` is allowed to view the given route. The
   * comparison considers role aliases so that e.g. a payload reporting
   * `role: "admin"` still matches an `allowedRoles: ["platform_admin"]`
   * entry.
   */
  function _isRoleAllowed(role, route) {
    if (!route || !route.allowedRoles || route.allowedRoles.length === 0) {
      return true;
    }
    if (!role) return false;
    if (route.allowedRoles.indexOf(role) !== -1) return true;
    var canonical = _canonicalRole(role);
    if (canonical && canonical !== role && route.allowedRoles.indexOf(canonical) !== -1) {
      return true;
    }
    return false;
  }

  /**
   * Resolve the home path for the given role, defaulting to "/login"
   * when the role is unknown or missing. Honors role aliases so the
   * legacy "admin" role resolves to the same destination as
   * "platform_admin" (REQ-15.6, 15.7, 15.8).
   */
  function _homeForRole(role) {
    if (role && Object.prototype.hasOwnProperty.call(ROLE_HOME, role)) {
      return ROLE_HOME[role];
    }
    var canonical = _canonicalRole(role);
    if (canonical && Object.prototype.hasOwnProperty.call(ROLE_HOME, canonical)) {
      return ROLE_HOME[canonical];
    }
    return '/login';
  }

  /**
   * Update `document.title` for the active route.
   */
  function _applyTitle(route) {
    if (route && route.title) {
      document.title = route.title + ' — Mr.E';
    }
  }

  /**
   * Build the login URL with a `return` query parameter so the user
   * can resume their original destination after authenticating
   * (REQ-15.5).
   */
  function _loginUrlWithReturn(returnTo) {
    var ret = encodeURIComponent(returnTo || '/');
    return '/login?return=' + ret;
  }

  /**
   * Build the 404 URL with the requested path preserved as a query
   * parameter so the static page can show what was requested
   * (REQ-15.9).
   */
  function _notFoundUrl(requestedPath) {
    var path = requestedPath ? String(requestedPath) : '';
    if (!path) return NOT_FOUND_PATH;
    return NOT_FOUND_PATH + '?path=' + encodeURIComponent(path);
  }

  /**
   * Determine whether a click event should be intercepted as a
   * client-side navigation. Skips:
   *   * non-anchor / no-href clicks
   *   * external URLs and protocol-relative URLs
   *   * `target="_blank"` and `download` attributes
   *   * modified clicks (Ctrl/Cmd/Shift/Alt or middle-click)
   *   * anchors that opt out via `data-no-router`
   */
  function _shouldInterceptClick(event, anchor) {
    if (event.defaultPrevented) return false;
    if (event.button !== undefined && event.button !== 0) return false;
    if (event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) {
      return false;
    }
    if (!anchor) return false;
    if (anchor.hasAttribute('data-no-router')) return false;
    if (anchor.hasAttribute('download')) return false;
    if (anchor.target && anchor.target !== '' && anchor.target !== '_self') {
      return false;
    }

    var href = anchor.getAttribute('href');
    if (!href) return false;
    // Only intercept absolute, in-app paths.
    if (href.charAt(0) !== '/') return false;
    // Skip protocol-relative URLs ("//example.com").
    if (href.charAt(1) === '/') return false;

    return true;
  }

  /**
   * Perform a real browser navigation to `path`. Used both as the
   * default navigate() implementation and as a fallback whenever a
   * route lacks a SPA handler (which is currently always true since
   * the backend serves all HTML).
   */
  function _hardNavigate(path) {
    window.location.href = path;
  }

  /**
   * Best-effort lookup of the current authenticated role. Uses
   * `Auth.currentRole()` if available; otherwise returns `null`.
   * Returns the role string or `null` when unauthenticated.
   * For students, if student_subtype is 'institution_linked', returns
   * 'institution_student' so routing treats them separately.
   */
  async function _currentRole() {
    if (typeof Auth === 'undefined' || !Auth || typeof Auth.currentRole !== 'function') {
      return null;
    }
    try {
      var user = await Auth.currentRole();
      if (user && user.role) {
        // Distinguish institution students from personal students
        if (user.role === 'student' && user.student_subtype === 'institution_linked') {
          return 'institution_student';
        }
        return user.role;
      }
    } catch (err) {
      // Network / auth errors are treated as "unauthenticated".
      // eslint-disable-next-line no-console
      console.warn('[Router] Auth.currentRole() failed:', err);
    }
    return null;
  }

  // ── Public API ──────────────────────────────────────────────────────────

  /**
   * Initialize the router.
   *
   * Installs event listeners for browser back/forward (`popstate`) and
   * link clicks, and runs an initial role validation against the
   * current page so that a user landing on a route they shouldn't see
   * is redirected to their role's home page (REQ-15.5 … 15.8) or the
   * 404 page when the path is unknown (REQ-15.9).
   *
   * Calling init() more than once is a no-op.
   */
  function init() {
    if (_initialized) return;
    _initialized = true;

    var currentRoute = _findRoute(window.location.pathname);
    _applyTitle(currentRoute);

    // popstate fires on browser back/forward. Re-validate the
    // destination route against the active session (REQ-15.11).
    _popstateHandler = function () {
      handleRoute(window.location.pathname);
    };
    window.addEventListener('popstate', _popstateHandler);

    // Intercept in-app link clicks so we can validate roles before
    // letting the browser perform a full-page navigation.
    _clickHandler = function (event) {
      var anchor = event.target && event.target.closest
        ? event.target.closest('a[href]')
        : null;
      if (!_shouldInterceptClick(event, anchor)) return;
      event.preventDefault();
      navigate(anchor.getAttribute('href'));
    };
    document.addEventListener('click', _clickHandler);

    // Validate the page the user landed on. Async, fire-and-forget —
    // any redirect will replace the document so subsequent code on
    // this page won't keep running.
    handleRoute(window.location.pathname);
  }

  /**
   * Navigate to `path`. Performs role validation (when the target
   * route requires auth / restricts roles) and then triggers a real
   * browser navigation, since each route is served as its own HTML
   * file by the FastAPI backend.
   *
   * Behaviour:
   *   * Unknown route → show the custom 404 page (REQ-15.9)
   *   * Public route  → navigate directly
   *   * Auth-required route while unauthenticated → /login?return=…
   *     (REQ-15.5)
   *   * Auth-required route with a role mismatch → redirect to that
   *     role's home page (REQ-15.6, 15.7, 15.8)
   */
  async function navigate(path) {
    var normalized = _normalizePath(path);
    var route = _findRoute(normalized);

    // Unknown route → custom 404 page (REQ-15.9). We pass the original
    // path through so the page can show what the user requested.
    if (!route) {
      _hardNavigate(_notFoundUrl(normalized));
      return;
    }

    // Public route — go directly.
    if (!route.requiresAuth) {
      _hardNavigate(path);
      return;
    }

    // Authenticated route — validate the session and role using
    // Auth.currentRole() (REQ-15.5 … 15.8).
    var role = await _currentRole();
    if (!role) {
      _hardNavigate(_loginUrlWithReturn(normalized));
      return;
    }

    // Institution students navigating to /dashboard → redirect to their platform
    if (role === 'institution_student' && normalized === '/dashboard') {
      _hardNavigate('/student/institution/dashboard');
      return;
    }

    var roleForCheck = role === 'institution_student' ? 'student' : role;
    if (!_isRoleAllowed(roleForCheck, route)) {
      _hardNavigate(_homeForRole(role));
      return;
    }

    _hardNavigate(path);
  }

  /**
   * Validate that the current (or supplied) path is appropriate for
   * the active session, redirecting if not.
   *
   * Behaviour:
   *   * Unknown route while on an unrelated page → no-op (the backend
   *     already responded; we don't want to loop on the 404 page
   *     itself).
   *   * Public route  → just update the document title.
   *   * Auth-required route while unauthenticated → redirect to /login
   *     with a `return` query parameter so the user can resume after
   *     signing in (REQ-15.5).
   *   * Auth-required route with a role mismatch → redirect to that
   *     role's home page (REQ-15.6, 15.7, 15.8).
   */
  async function handleRoute(path) {
    var target = path || window.location.pathname;
    var normalized = _normalizePath(target);
    var route = _findRoute(normalized);

    if (!route) return;

    _applyTitle(route);

    if (!route.requiresAuth) return;

    var role = await _currentRole();
    if (!role) {
      _hardNavigate(_loginUrlWithReturn(normalized));
      return;
    }

    // Institution students hitting /dashboard must go to their platform
    if (role === 'institution_student' && normalized === '/dashboard') {
      _hardNavigate('/student/institution/dashboard');
      return;
    }

    // Personal students hitting institution student pages must go to /dashboard
    if (role === 'student' && normalized.startsWith('/student/institution')) {
      _hardNavigate('/dashboard');
      return;
    }

    // For route allowedRoles check, institution_student maps to 'student'
    var roleForCheck = role === 'institution_student' ? 'student' : role;
    if (!_isRoleAllowed(roleForCheck, route)) {
      _hardNavigate(_homeForRole(role));
    }
  }

  /**
   * Guard helper for page scripts that want to assert authentication
   * up-front (e.g. dashboard, exam, subscription pages). Resolves to
   * the authenticated user object on success; redirects and returns
   * `null` otherwise.
   *
   *   - No session     → /login?return=<current>   (REQ-15.5)
   *   - Wrong role for the current route → role home (REQ-15.6 … 15.8)
   *
   * Public pages and unknown routes resolve without redirection.
   */
  async function requireAuth() {
    if (typeof Auth === 'undefined' || !Auth || typeof Auth.currentRole !== 'function') {
      return null;
    }

    var route = _findRoute(window.location.pathname);
    if (route && !route.requiresAuth) {
      // No guard needed for public routes.
      try {
        return await Auth.currentRole();
      } catch (err) {
        return null;
      }
    }

    var user;
    try {
      user = await Auth.currentRole();
    } catch (err) {
      user = null;
    }

    if (!user || !user.role) {
      _hardNavigate(_loginUrlWithReturn(window.location.pathname));
      return null;
    }

    if (route && !_isRoleAllowed(user.role, route)) {
      _hardNavigate(_homeForRole(user.role));
      return null;
    }

    return user;
  }

  /**
   * Redirect the browser to the home page for `role`. When `role` is
   * omitted, the current session's role is fetched first. Falls back
   * to the login page when no role can be determined.
   */
  async function redirectByRole(role) {
    var resolved = role || (await _currentRole());
    _hardNavigate(_homeForRole(resolved));
  }

  /**
   * Programmatically navigate to the custom 404 page, preserving the
   * originally requested path as a query parameter (REQ-15.9). Useful
   * for page scripts that detect a missing resource and want to show
   * a consistent error experience.
   */
  function showNotFound(requestedPath) {
    var path = requestedPath || window.location.pathname;
    _hardNavigate(_notFoundUrl(path));
  }

  // ── Expose ──────────────────────────────────────────────────────────────

  return {
    init: init,
    navigate: navigate,
    handleRoute: handleRoute,
    requireAuth: requireAuth,
    redirectByRole: redirectByRole,
    showNotFound: showNotFound,
    // Exposed for tests / advanced consumers; treat as read-only.
    _routes: ROUTES,
  };
})();
