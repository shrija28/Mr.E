"""FastAPI application factory.

Importing this module yields a configured :data:`app` object that mirrors
the legacy ``backend/app.py`` runtime, plus the new role-scoped routers
introduced by the SmartKCET upgrade.

REQ-3.5 startup config guard
----------------------------

The guard runs at module-import time, **before** ``app = FastAPI(...)``
is constructed and before any route is registered.  On a missing or
malformed admin/JWT/database configuration the guard logs a fatal error
and calls ``sys.exit(1)`` ΓÇö Uvicorn never starts and the process exits
non-zero.  In production this means importing this module itself fails
fast.  Tests bypass the guard by setting
``SMARTKCET_SKIP_STARTUP_GUARD=1`` in the environment.

Router layout (task 3.5)
------------------------

* ``/api/auth/*``     ΓÇö :mod:`smartkcet.auth.routes`
* ``/api/admin/*``    ΓÇö :mod:`smartkcet.admin` (placeholder; admin RBAC)
* ``/api/student/*``  ΓÇö :mod:`smartkcet.student` (placeholder; student RBAC)
* ``/api/health``     ΓÇö public health probe defined in this module
* ``/dashboard``,
  ``/admin``,
  ``/admin/{path}``   ΓÇö :mod:`smartkcet.routes.pages` (HTML redirects)
* ``/upload``,
  ``/generate``,
  ``/analyze``,
  ``/health``, ...    ΓÇö :mod:`smartkcet.routes.legacy` (kept during the
                         refactor; renaming lands in tasks 4.x and 8.x)
"""

from __future__ import annotations

import warnings
from pathlib import Path
import os

# Python 3.14 compatibility fix for anyio event loop detection
os.environ["PYTHONUNBUFFERED"] = "1"

import nest_asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Match the noise-suppression done by the legacy entry point.
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)
nest_asyncio.apply()

# Run the startup config guard FIRST.  On invalid configuration this
# call invokes ``sys.exit(1)`` and the rest of this module never
# executes ΓÇö Uvicorn therefore never binds a port and the FastAPI
# ``app`` symbol is never exposed.  On success the validated
# :class:`StartupConfig` is cached for subsequent lookups.
from .config import validate_startup_config  # noqa: E402

STARTUP_CONFIG = validate_startup_config()

# Validate Groq API key at startup (non-fatal ΓÇö logs a warning if invalid
# so the server still starts for non-generation features).
try:
    from .rag.groq_client import validate_groq_api_key, reset_groq_client
    reset_groq_client()  # Force fresh client on every server start
    validate_groq_api_key()
except Exception as _groq_err:
    import logging as _logging
    _logging.getLogger("smartkcet.main").warning(
        "Groq API key validation failed at startup: %s. "
        "The /api/admin/generate endpoint will not work until this is fixed.",
        _groq_err,
    )

from .admin import router as admin_api_router  # noqa: E402
from .auth import router as auth_router  # noqa: E402
from .institution import router as institution_router  # noqa: E402
from .payments import router as payments_router  # noqa: E402
from .routes.legacy import router as legacy_router  # noqa: E402
from .routes.pages import router as pages_router  # noqa: E402
from .student import router as student_api_router  # noqa: E402
from .subscription import router as subscription_router  # noqa: E402
from .admin.syllabus import public_router as syllabus_public_router  # noqa: E402

app = FastAPI(title="ExamForge Backend")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# 404 handling for HTML page requests (REQ-15.9).
#
# When a browser navigates to an unknown URL we want to show the custom
# 404 page (frontend/html/not-found.html) rather than FastAPI's default
# JSON ``{"detail": "Not Found"}`` body. API clients (anything under
# ``/api/`` or anything that explicitly accepts JSON) keep the JSON
# response so error handlers like ``Subscription.handleApiError()``
# continue to work unchanged.
# ---------------------------------------------------------------------------

from starlette.exceptions import HTTPException as StarletteHTTPException  # noqa: E402
from fastapi.responses import JSONResponse, RedirectResponse  # noqa: E402
from starlette.middleware.base import BaseHTTPMiddleware  # noqa: E402


class NoCacheHTMLMiddleware(BaseHTTPMiddleware):
    """Add Cache-Control: no-cache to HTML and JS responses so browsers
    always fetch the latest version during development."""

    async def dispatch(self, request, call_next):
        import asyncio
        # Ensure we're in an async context
        try:
            response = await call_next(request)
            content_type = response.headers.get("content-type", "")
            path = request.url.path or ""
            is_js = path.startswith("/js/") or path.endswith(".js")
            if "text/html" in content_type or is_js:
                response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
                response.headers["Pragma"] = "no-cache"
                response.headers["Expires"] = "0"
            return response
        except RuntimeError as e:
            # Fallback for sync context
            import logging
            logging.getLogger("smartkcet.main").warning(f"Middleware error: {e}")
            return await call_next(request)


# Temporarily disabled due to async event loop issue
# app.add_middleware(NoCacheHTMLMiddleware)


@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request, exc):
    """Redirect HTML page 404s to the custom not-found page."""
    if exc.status_code == 404:
        path = request.url.path or ""
        # Only redirect for browser-style navigation. API and static
        # asset requests should retain the standard JSON 404.
        is_api = path.startswith("/api/")
        is_static = path.startswith("/css/") or path.startswith("/js/")
        accept = request.headers.get("accept", "")
        wants_html = "text/html" in accept

        if not is_api and not is_static and wants_html and path != "/not-found":
            from urllib.parse import quote

            return RedirectResponse(
                url=f"/not-found?path={quote(path)}",
                status_code=302,
            )

    # Default: fall back to a JSON response that matches FastAPI's
    # standard error shape so existing API clients keep working.
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


# ---------------------------------------------------------------------------
# Subscription Lifecycle Scheduler
# ---------------------------------------------------------------------------

@app.on_event("startup")
async def startup_scheduler():
    """Start the subscription lifecycle scheduler and seed KCET syllabus."""
    from .db.session import get_session
    from .subscription.scheduler import (
        start_subscription_scheduler,
        get_scheduler_interval,
    )
    from .db.syllabus_seed import seed_syllabus
    import logging as _log

    db = next(get_session())

    # Seed KCET syllabus on first run (idempotent ΓÇö skips if already seeded)
    try:
        seeded = seed_syllabus(db)
        if seeded:
            _log.getLogger("smartkcet.main").info(
                "KCET syllabus seeded: %d topics inserted.", seeded
            )
    except Exception as _seed_err:
        _log.getLogger("smartkcet.main").warning(
            "Syllabus seed failed (non-fatal): %s", _seed_err
        )

    interval = get_scheduler_interval()
    await start_subscription_scheduler(db, interval_minutes=interval)


@app.on_event("shutdown")
async def shutdown_scheduler():
    """Stop the subscription lifecycle scheduler on application shutdown."""
    from .subscription.scheduler import stop_subscription_scheduler
    
    await stop_subscription_scheduler()


@app.get("/api/health", tags=["health"])
async def api_health() -> dict[str, str]:
    """Public health probe.  REQ-13/14 ΓÇö used by uptime checks; no auth."""
    return {"status": "ok"}


# Auth_Service routes (task 2.x) under ``/api/auth``.
app.include_router(auth_router)

# Subscription routes (task 3.9) under ``/api/subscription``.
app.include_router(subscription_router)

# Institution routes (task 6.x) under ``/api/institution``.
app.include_router(institution_router)

# Role-scoped API routers (task 3.5) ΓÇö currently placeholders that future
# tasks (6.x, 7.x, 8.x, 10.x, 11.x) extend.  RBAC is enforced per-endpoint
# via ``Depends(require_admin)`` / ``Depends(require_student)`` inside
# the routers themselves so a public endpoint can be added later without
# tearing down a router-wide dependency.
app.include_router(admin_api_router)
app.include_router(student_api_router)
app.include_router(payments_router)

# Exam-access router ΓÇö exposes POST /api/exam/check-access
# This is the authoritative subscription gate called by exam.js before
# a student starts an exam. Separated from /api/student/* so the
# frontend can call it at the documented path.
from .student.exam_access import router as exam_access_router  # noqa: E402
app.include_router(exam_access_router)
# Public syllabus endpoint (no auth ΓÇö accessible to students and institutions)
app.include_router(syllabus_public_router, prefix="/api", tags=["syllabus"])

# HTML pages with role-aware redirects (REQ-3.3, REQ-3.4, REQ-4.7).
app.include_router(pages_router)

# Legacy ExamForge endpoints kept at their original paths for backward
# compat during the refactor.  Renaming (``/api/admin/upload``,
# ``/api/admin/generate``, ``/api/student/submit``) lands in tasks 4.x
# and 8.x.
app.include_router(legacy_router)

# ---------------------------------------------------------------------------
# Static file serving for frontend CSS and JS assets.
# Mounted AFTER routers so explicit route handlers take priority.
# ---------------------------------------------------------------------------

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_FRONTEND_DIR = _PROJECT_ROOT / "frontend"

# /css/* ΓåÆ frontend/css/
if (_FRONTEND_DIR / "css").is_dir():
    app.mount("/css", StaticFiles(directory=str(_FRONTEND_DIR / "css")), name="css")

# /js/* ΓåÆ frontend/js/
if (_FRONTEND_DIR / "js").is_dir():
    app.mount("/js", StaticFiles(directory=str(_FRONTEND_DIR / "js")), name="js")

# /html/* ΓåÆ frontend/html/ (modal includes and shared HTML assets)
@app.get("/html/{filepath}")
def serve_frontend_html(filepath: str):
    file_path = _FRONTEND_DIR / "html" / filepath
    if file_path.exists() and file_path.is_file():
        with open(file_path, "rb") as f:
            content = f.read()
        return Response(content, media_type="text/html")
    return Response({"error": "not_found"}, status_code=404, media_type="application/json")


__all__ = ["app", "STARTUP_CONFIG"]
