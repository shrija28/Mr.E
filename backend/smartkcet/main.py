"""FastAPI application factory.

Importing this module yields a configured :data:`app` object that mirrors
the legacy ``backend/app.py`` runtime, plus the new role-scoped routers
introduced by the SmartKCET upgrade.

REQ-3.5 startup config guard
----------------------------

The guard runs at module-import time, **before** ``app = FastAPI(...)``
is constructed and before any route is registered.  On a missing or
malformed admin/JWT/database configuration the guard logs a fatal error
and calls ``sys.exit(1)`` — Uvicorn never starts and the process exits
non-zero.  In production this means importing this module itself fails
fast.  Tests bypass the guard by setting
``SMARTKCET_SKIP_STARTUP_GUARD=1`` in the environment.

Router layout (task 3.5)
------------------------

* ``/api/auth/*``     — :mod:`smartkcet.auth.routes`
* ``/api/admin/*``    — :mod:`smartkcet.admin` (placeholder; admin RBAC)
* ``/api/student/*``  — :mod:`smartkcet.student` (placeholder; student RBAC)
* ``/api/health``     — public health probe defined in this module
* ``/dashboard``,
  ``/admin``,
  ``/admin/{path}``   — :mod:`smartkcet.routes.pages` (HTML redirects)
* ``/upload``,
  ``/generate``,
  ``/analyze``,
  ``/health``, ...    — :mod:`smartkcet.routes.legacy` (kept during the
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
# executes — Uvicorn therefore never binds a port and the FastAPI
# ``app`` symbol is never exposed.  On success the validated
# :class:`StartupConfig` is cached for subsequent lookups.
from .config import validate_startup_config  # noqa: E402

STARTUP_CONFIG = validate_startup_config()

# Validate Groq API key at startup (non-fatal — logs a warning if invalid
# so the server still starts for non-generation features).
# NOTE: groq library has critical compatibility issues on Python 3.14
# (hangs during import), so we skip validation on that version
import sys
try:
    if sys.version_info >= (3, 14):
        import logging as _logging
        _logging.getLogger("smartkcet.main").info(
            "Python 3.14 detected: skipping Groq validation (library incompatible). "
            "Generation features will be unavailable."
        )
    else:
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
from .contact import router as contact_router  # noqa: E402
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


from starlette.datastructures import MutableHeaders

class APINoCacheMiddleware:
    """Pure ASGI middleware to add Cache-Control headers without triggering anyio event loop bugs."""
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        path = scope.get("path", "")
        # Apply no-cache to API responses and HTML/JS files
        needs_cache_control = path.startswith("/api/") or path.endswith(".html") or path.endswith(".js") or path.startswith("/html/") or path.startswith("/js/")

        if not needs_cache_control:
            return await self.app(scope, receive, send)

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
                headers["Pragma"] = "no-cache"
                headers["Expires"] = "0"
            await send(message)

        await self.app(scope, receive, send_wrapper)

app.add_middleware(APINoCacheMiddleware)


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
    from .subscription.scheduler import (
        start_subscription_scheduler,
        get_scheduler_interval,
    )
    from .db.syllabus_seed import seed_syllabus
    from .db.seed import seed_admin, seed_subscription_plans
    from .db.session import SessionLocal
    import logging as _log

    # Create a direct session for seeding (bypass FastAPI dependency injection)
    db = SessionLocal()

    # ── Database Schema Self-Healing ──────────────────────────────────────────
    try:
        from sqlalchemy import text
        db.execute(text("ALTER TABLE syllabus_topics ADD COLUMN textbook_filename VARCHAR(255)"))
        db.execute(text("ALTER TABLE syllabus_topics ADD COLUMN textbook_path VARCHAR(255)"))
        db.commit()
        _log.getLogger("smartkcet.main").info("Database self-healing: added textbook columns to syllabus_topics")
    except Exception as schema_err:
        db.rollback()
        # Suppress error if columns already exist
        if "duplicate column" in str(schema_err).lower() or "already exists" in str(schema_err).lower() or "duplicate" in str(schema_err).lower():
            pass
        else:
            _log.getLogger("smartkcet.main").warning(
                "Database self-healing non-fatal warning: %s", schema_err
            )

    # ── source_type column on questions ───────────────────────────────────────
    try:
        from sqlalchemy import text
        db.execute(text("ALTER TABLE questions ADD COLUMN source_type VARCHAR(20) NOT NULL DEFAULT 'question_paper'"))
        db.commit()
        _log.getLogger("smartkcet.main").info("Database self-healing: added source_type column to questions")
    except Exception as schema_err:
        db.rollback()
        if "duplicate column" in str(schema_err).lower() or "already exists" in str(schema_err).lower() or "duplicate" in str(schema_err).lower():
            pass
        else:
            _log.getLogger("smartkcet.main").warning(
                "Database self-healing source_type non-fatal: %s", schema_err
            )

    # Seed admin user on first run (idempotent — skips if already exists)
    try:
        seeded = seed_admin()
        if seeded:
            _log.getLogger("smartkcet.main").info(
                "Admin user seeded successfully."
            )
    except Exception as _seed_err:
        _log.getLogger("smartkcet.main").warning(
            "Admin seed failed (non-fatal): %s", _seed_err
        )

    # Seed KCET syllabus on first run (idempotent — skips if already seeded)
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

    # Seed subscription plans on first run (idempotent — skips if already seeded)
    try:
        seeded = seed_subscription_plans()
        if seeded:
            _log.getLogger("smartkcet.main").info(
                "Subscription plans seeded: %d plans inserted.", seeded
            )
    except Exception as _seed_err:
        _log.getLogger("smartkcet.main").warning(
            "Subscription plans seed failed (non-fatal): %s", _seed_err
        )

    # Seed test institutions and students on first run (idempotent)
    try:
        from .db.seed_students import seed_test_institutions, seed_test_direct_subscribers, seed_test_institution_students, create_trial_subscriptions, create_institution_subscriptions
        from sqlalchemy import func
        from .db.subscription_models import Institution
        
        # Check if institutions already exist
        existing_count = db.query(func.count(Institution.id)).scalar()
        if existing_count == 0:
            institutions = seed_test_institutions(db, count=3)
            direct_students = seed_test_direct_subscribers(db, count=5)
            institution_students = seed_test_institution_students(db, institutions, count_per_institution=5)
            trial_subs = create_trial_subscriptions(db, direct_students)
            inst_subs = create_institution_subscriptions(db, institutions)
            
            _log.getLogger("smartkcet.main").info(
                "Test data seeded: %d institutions, %d direct students, %d institution students, %d trial subs, %d institution subs.",
                len(institutions), len(direct_students), len(institution_students), trial_subs, inst_subs
            )
    except Exception as _test_data_err:
        _log.getLogger("smartkcet.main").warning(
            "Test data seed failed (non-fatal): %s", _test_data_err
        )

    # SAFETY CHECK: Detect and fix incorrect USD/dev pricing (₹9.99, ₹99.99)
    # This prevents incorrect pricing from being served if database gets corrupted
    try:
        from sqlalchemy import update
        from .db.subscription_models import SubscriptionPlan
        from decimal import Decimal
        
        logger = _log.getLogger("smartkcet.main")
        
        # Check for incorrect USD pricing that should be INR
        wrong_prices = {
            Decimal("9.99"): Decimal("349.00"),      # Pro Monthly: ₹9.99 → ₹349
            Decimal("99.99"): Decimal("2999.00"),    # Pro Yearly: ₹99.99 → ₹2999
        }
        
        for wrong_price, correct_price in wrong_prices.items():
            wrong_plans = db.query(SubscriptionPlan).filter(
                SubscriptionPlan.price == wrong_price,
                SubscriptionPlan.plan_type == "individual"
            ).all()
            
            if wrong_plans:
                logger.warning(
                    "CRITICAL: Found %d plans with incorrect USD pricing (₹%s). Auto-correcting to INR (₹%s)",
                    len(wrong_plans), wrong_price, correct_price
                )
                
                for plan in wrong_plans:
                    old_price = plan.price
                    plan.price = correct_price
                    db.add(plan)
                    logger.warning(
                        "AUTO-CORRECTED: Plan '%s' price ₹%s → ₹%s",
                        plan.name, old_price, correct_price
                    )
                
                db.commit()
    except Exception as _safety_err:
        logger.warning(
            "Pricing safety check failed (non-fatal): %s", _safety_err
        )
        db.rollback()

    db.close()

    interval = get_scheduler_interval()
    await start_subscription_scheduler(SessionLocal(), interval_minutes=interval)


@app.on_event("shutdown")
async def shutdown_scheduler():
    """Stop the subscription lifecycle scheduler on application shutdown."""
    from .subscription.scheduler import stop_subscription_scheduler
    
    await stop_subscription_scheduler()


@app.get("/api/health", tags=["health"])
async def api_health() -> dict[str, str]:
    """Public health probe.  REQ-13/14 — used by uptime checks; no auth."""
    return {"status": "ok"}


# Auth_Service routes (task 2.x) under ``/api/auth``.
app.include_router(auth_router)

# Contact routes (support messages)
app.include_router(contact_router)

# Subscription routes (task 3.9) under ``/api/subscription``.
app.include_router(subscription_router)

# Institution routes (task 6.x) under ``/api/institution``.
app.include_router(institution_router)

# Role-scoped API routers (task 3.5) — currently placeholders that future
# tasks (6.x, 7.x, 8.x, 10.x, 11.x) extend.  RBAC is enforced per-endpoint
# via ``Depends(require_admin)`` / ``Depends(require_student)`` inside
# the routers themselves so a public endpoint can be added later without
# tearing down a router-wide dependency.
app.include_router(admin_api_router)
app.include_router(student_api_router)
app.include_router(payments_router)

# Exam-access router — exposes POST /api/exam/check-access
# This is the authoritative subscription gate called by exam.js before
# a student starts an exam. Separated from /api/student/* so the
# frontend can call it at the documented path.
from .student.exam_access import router as exam_access_router  # noqa: E402
app.include_router(exam_access_router)
# Public syllabus endpoint (no auth — accessible to students and institutions)
app.include_router(syllabus_public_router, prefix="/api", tags=["syllabus"])

# HTML pages with role-aware redirects (REQ-3.3, REQ-3.4, REQ-4.7).
app.include_router(pages_router)

# Static file serving using direct file reading instead of FileResponse
# (Python 3.14 + anyio has event-loop issues with async file operations)
from pathlib import Path as PathlibPath
from fastapi.responses import Response
_PROJECT_ROOT_STATIC = PathlibPath(__file__).resolve().parent.parent.parent
_FRONTEND_DIR_STATIC = _PROJECT_ROOT_STATIC / "frontend"

@app.get("/css/{filepath}")
def serve_css(filepath: str):
    file_path = _FRONTEND_DIR_STATIC / "css" / filepath
    if file_path.exists() and file_path.is_file():
        with open(file_path, "rb") as f:
            content = f.read()
        return Response(content, media_type="text/css")
    return Response({"error": "not_found"}, status_code=404, media_type="application/json")

@app.get("/js/{filepath}")
def serve_js(filepath: str):
    file_path = _FRONTEND_DIR_STATIC / "js" / filepath
    if file_path.exists() and file_path.is_file():
        with open(file_path, "rb") as f:
            content = f.read()
        return Response(content, media_type="text/javascript")
    return Response({"error": "not_found"}, status_code=404, media_type="application/json")


@app.get("/html/{filepath}")
def serve_html(filepath: str):
    file_path = _FRONTEND_DIR_STATIC / "html" / filepath
    if file_path.exists() and file_path.is_file():
        with open(file_path, "rb") as f:
            content = f.read()
        return Response(content, media_type="text/html")
    return Response({"error": "not_found"}, status_code=404, media_type="application/json")


__all__ = ["app", "STARTUP_CONFIG"]
