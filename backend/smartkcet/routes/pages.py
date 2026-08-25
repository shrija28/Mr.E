"""HTML page routes with role-aware redirects and static file serving.

Routing truth table:

| Path                               | Role                     | Response                                    |
|------------------------------------|--------------------------|---------------------------------------------|
| /                                  | unauthenticated          | serve landing.html                          |
| /                                  | direct_subscriber        | 302 → /dashboard                            |
| /                                  | institution_linked       | 302 → /student/institution/dashboard        |
| /                                  | platform_admin           | 302 → /admin/dashboard                      |
| /                                  | institution_admin        | 302 → /institution/dashboard                |
| /login                             | any                      | serve login.html                            |
| /register                          | any                      | serve register.html                         |
| /dashboard                         | unauthenticated          | 302 → /login                                |
| /dashboard                         | institution_linked       | 302 → /student/institution/dashboard        |
| /dashboard                         | direct_subscriber        | serve dashboard.html                        |
| /dashboard                         | platform_admin           | 302 → /admin/dashboard                      |
| /exam                              | direct_subscriber        | serve exam.html                             |
| /exam                              | institution_linked       | serve exam.html (institution exams only)    |
| /subscription                      | direct_subscriber        | serve subscription.html                     |
| /subscription                      | institution_linked       | 302 → /student/institution/dashboard        |
| /pricing                           | direct_subscriber        | serve student-pricing.html                  |
| /pricing                           | institution_linked       | 302 → /student/institution/dashboard        |
| /student/institution/dashboard     | institution_linked       | serve student-institution-dashboard.html    |
| /student/institution/dashboard     | direct_subscriber        | 302 → /dashboard                            |
| /student/institution/*             | institution_linked       | serve respective page                       |
| /invitation-accept                 | any                      | serve invitation-accept.html                |
| /admin/*                           | platform_admin           | serve admin-*.html                          |
| /institution/*                     | institution_admin        | serve institution-*.html                    |

Static assets (/css/*, /js/*) are served via StaticFiles in main.py.
"""

from __future__ import annotations
import os

from pathlib import Path

import os
from flask import Blueprint, request, g, make_response, jsonify, Response
from fastapi.responses import FileResponse, RedirectResponse
from sqlalchemy.orm import Session

from ..db.session import get_session
from ..middleware.rbac import resolve_payload

router = Blueprint("routes_pages", __name__)

from pathlib import Path
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_HTML_DIR = _PROJECT_ROOT / "frontend" / "html"
_REDIRECT = 302


def _is_platform_admin(role: str)-> bool:
    """Accept both legacy 'admin' and new 'platform_admin' role strings."""
    return role in ("admin", "platform_admin")


def _is_institution_student(payload: dict)-> bool:
    """Return True for institution-linked students."""
    return (
        payload.get("role") == "student"
        and payload.get("student_subtype") == "institution_linked"
    )


def _is_personal_student(payload: dict)-> bool:
    """Return True for direct_subscriber (personal) students."""
    return (
        payload.get("role") == "student"
        and payload.get("student_subtype") != "institution_linked"
    )


# ---------------------------------------------------------------------------
# Root
# ---------------------------------------------------------------------------

@router.route("/", methods=["GET"])
@router.route("/index.html", methods=["GET"])
def root_page():    
    from flask import g
    db = getattr(g, "db", None)
    session = db
    
    from flask import g
    db = getattr(g, "db", None)
    session = db
    """Route root path to appropriate dashboard based on user role."""
    payload = resolve_payload(request, session)
    
    # No authentication
    if payload is None:
        return FileResponse(str(_HTML_DIR / "landing.html"), media_type="text/html")
    
    # Get role and student subtype
    role = payload.get("role", "").strip().lower()
    student_subtype = payload.get("student_subtype", "").strip().lower()
    
    # Institution-linked student
    if role == "student" and student_subtype == "institution_linked":
        return RedirectResponse(url="/student/institution/dashboard")
    
    # Direct subscriber student (role=student but NOT institution_linked)
    if role == "student":
        return RedirectResponse(url="/dashboard")
    
    # Platform admin
    if role in ("admin", "platform_admin"):
        return RedirectResponse(url="/admin/dashboard")
    
    # Institution admin
    if role == "institution_admin":
        return RedirectResponse(url="/institution/dashboard")
    
    # Fallback - no recognized role
    return FileResponse(str(_HTML_DIR / "landing.html"), media_type="text/html")


# ---------------------------------------------------------------------------
# Public pages
# ---------------------------------------------------------------------------

@router.route("/login", methods=["GET"])
def login_page():
    return FileResponse(str(_HTML_DIR / "login.html"), media_type="text/html")


@router.route("/favicon.ico", methods=["GET"])
def favicon():
    """Serve the brand favicon. Silences the browser's automatic
    /favicon.ico request (previously a 404 since no asset was mounted)."""
    return FileResponse(
        str(_PROJECT_ROOT / "frontend" / "favicon.svg"),
        media_type="image/svg+xml",
    )


@router.route("/register", methods=["GET"])
def register_page():
    return FileResponse(str(_HTML_DIR / "register.html"), media_type="text/html")


@router.route("/institution-register", methods=["GET"])
def institution_register_page():
    return FileResponse(str(_HTML_DIR / "institution-register.html"), media_type="text/html")


@router.route("/not-found", methods=["GET"])
def not_found_page():
    return FileResponse(str(_HTML_DIR / "not-found.html"), media_type="text/html")


@router.route("/invitation-accept", methods=["GET"])
def invitation_accept_page():
    """Public — auth is checked client-side by invitation.js."""
    return FileResponse(str(_HTML_DIR / "invitation-accept.html"), media_type="text/html")


# ---------------------------------------------------------------------------
# Personal Student pages (direct_subscriber only)
# ---------------------------------------------------------------------------

@router.route("/dashboard", methods=["GET"])
def dashboard_page():    
    from flask import g
    db = getattr(g, "db", None)
    session = db
    
    from flask import g
    db = getattr(g, "db", None)
    session = db
    payload = resolve_payload(request, session)
    if payload is None:
        return RedirectResponse(url="/login")
    # Institution students → their own dashboard
    if _is_institution_student(payload):
        return RedirectResponse(url="/student/institution/dashboard")
    role = payload.get("role", "")
    if _is_platform_admin(role):
        return RedirectResponse(url="/admin/dashboard")
    if role == "institution_admin":
        return RedirectResponse(url="/institution/dashboard")
    if role == "student":
        return FileResponse(str(_HTML_DIR / "dashboard.html"), media_type="text/html")
    return RedirectResponse(url="/login")


@router.route("/exam", methods=["GET"])
def exam_page():    
    from flask import g
    db = getattr(g, "db", None)
    session = db
    
    from flask import g
    db = getattr(g, "db", None)
    session = db
    payload = resolve_payload(request, session)
    if payload is None:
        return RedirectResponse(url="/login")
    role = payload.get("role", "")
    # Institution students: if they have a specific exam_set_id query param they're
    # starting an actual exam — allow exam.html. Otherwise redirect to their exams listing.
    if _is_institution_student(payload):
        exam_set_id = request.query_params.get("set")
        if exam_set_id:
            # Coming from institution exams page with a specific set — allow through
            return FileResponse(str(_HTML_DIR / "exam.html"), media_type="text/html")
        return RedirectResponse(url="/student/institution/exams")
    if role in ("student", "institution_admin") or _is_platform_admin(role):
        return FileResponse(str(_HTML_DIR / "exam.html"), media_type="text/html")
    return RedirectResponse(url="/login")


@router.route("/subscription", methods=["GET"])
def subscription_page():    
    from flask import g
    db = getattr(g, "db", None)
    session = db
    
    from flask import g
    db = getattr(g, "db", None)
    session = db
    payload = resolve_payload(request, session)
    if payload is None:
        return RedirectResponse(url="/login")
    role = payload.get("role", "")
    if role == "student":
        # Institution-linked students have no personal subscription UI
        if _is_institution_student(payload):
            return RedirectResponse(url="/student/institution/dashboard")
        return FileResponse(str(_HTML_DIR / "subscription.html"), media_type="text/html")
    if _is_platform_admin(role):
        return RedirectResponse(url="/admin/upload")
    if role == "institution_admin":
        return RedirectResponse(url="/institution/subscription")
    return RedirectResponse(url="/login")


@router.route("/pricing", methods=["GET"])
def student_pricing_page():    
    from flask import g
    db = getattr(g, "db", None)
    session = db
    
    from flask import g
    db = getattr(g, "db", None)
    session = db
    """Student-facing subscription pricing page."""
    payload = resolve_payload(request, session)
    if payload is None:
        return RedirectResponse(url="/login")
    role = payload.get("role", "")
    if role == "student":
        # Institution-linked students cannot access personal pricing page
        if _is_institution_student(payload):
            return RedirectResponse(url="/student/institution/dashboard")
        return FileResponse(str(_HTML_DIR / "student-pricing.html"), media_type="text/html")
    if role == "institution_admin":
        return RedirectResponse(url="/institution/pricing")
    if _is_platform_admin(role):
        return RedirectResponse(url="/admin/subscriptions")
    return RedirectResponse(url="/login")


# ---------------------------------------------------------------------------
# Institution Student Platform  (/student/institution/*)
# ---------------------------------------------------------------------------

def _institution_student_page(session: Session, html_file: str):
    """Guard: only institution_linked students can view these pages."""
    payload = resolve_payload(request, session)
    if payload is None:
        return RedirectResponse(url="/login")
    if _is_institution_student(payload):
        return FileResponse(str(_HTML_DIR / html_file), media_type="text/html")
    # Personal students → personal dashboard
    if payload.get("role") == "student":
        return RedirectResponse(url="/dashboard")
    if _is_platform_admin(payload.get("role", "")):
        return RedirectResponse(url="/admin/dashboard")
    if payload.get("role") == "institution_admin":
        return RedirectResponse(url="/institution/dashboard")
    return RedirectResponse(url="/login")


@router.route("/student/institution/dashboard", methods=["GET"])
def student_institution_dashboard_page():    
    from flask import g
    db = getattr(g, "db", None)
    session = db
    
    from flask import g
    db = getattr(g, "db", None)
    session = db
    return _institution_student_page(request, session, "student-institution-dashboard.html")


@router.route("/student/institution/exams", methods=["GET"])
def student_institution_exams_page():    
    from flask import g
    db = getattr(g, "db", None)
    session = db
    
    from flask import g
    db = getattr(g, "db", None)
    session = db
    return _institution_student_page(request, session, "student-institution-exams.html")


@router.route("/student/institution/performance", methods=["GET"])
def student_institution_performance_page():    
    from flask import g
    db = getattr(g, "db", None)
    session = db
    
    from flask import g
    db = getattr(g, "db", None)
    session = db
    return _institution_student_page(request, session, "student-institution-performance.html")


@router.route("/student/institution/leaderboard", methods=["GET"])
def student_institution_leaderboard_page():    
    from flask import g
    db = getattr(g, "db", None)
    session = db
    
    from flask import g
    db = getattr(g, "db", None)
    session = db
    return _institution_student_page(request, session, "student-institution-leaderboard.html")


# ---------------------------------------------------------------------------
# Platform admin pages
# ---------------------------------------------------------------------------

def _admin_page(session: Session, html_file: str):
    payload = resolve_payload(request, session)
    if payload is None:
        return RedirectResponse(url="/login")
    role = payload.get("role", "")
    if _is_platform_admin(role):
        return FileResponse(str(_HTML_DIR / html_file), media_type="text/html")
    if _is_institution_student(payload):
        return RedirectResponse(url="/student/institution/dashboard")
    if role == "student":
        return RedirectResponse(url="/dashboard")
    if role == "institution_admin":
        return RedirectResponse(url="/institution/dashboard")
    return RedirectResponse(url="/login")


@router.route("/admin", methods=["GET"])
def admin_root():    
    from flask import g
    db = getattr(g, "db", None)
    session = db
    
    from flask import g
    db = getattr(g, "db", None)
    session = db
    payload = resolve_payload(request, session)
    if payload is None:
        return RedirectResponse(url="/login")
    role = payload.get("role", "")
    if _is_platform_admin(role):
        return RedirectResponse(url="/admin/dashboard")
    if _is_institution_student(payload):
        return RedirectResponse(url="/student/institution/dashboard")
    if role == "student":
        return RedirectResponse(url="/dashboard")
    return RedirectResponse(url="/login")


@router.route("/admin/upload", methods=["GET"])
def admin_upload_page():    
    from flask import g
    db = getattr(g, "db", None)
    session = db
    
    from flask import g
    db = getattr(g, "db", None)
    session = db
    return _admin_page(request, session, "admin-upload.html")


@router.route("/admin/dashboard", methods=["GET"])
def admin_dashboard_page():    
    from flask import g
    db = getattr(g, "db", None)
    session = db
    
    from flask import g
    db = getattr(g, "db", None)
    session = db
    return _admin_page(request, session, "admin-dashboard.html")


@router.route("/admin/institutions", methods=["GET"])
def admin_institutions_page():    
    from flask import g
    db = getattr(g, "db", None)
    session = db
    
    from flask import g
    db = getattr(g, "db", None)
    session = db
    return _admin_page(request, session, "admin-institutions.html")


@router.route("/admin/subscriptions", methods=["GET"])
def admin_subscriptions_page():    
    from flask import g
    db = getattr(g, "db", None)
    session = db
    
    from flask import g
    db = getattr(g, "db", None)
    session = db
    return _admin_page(request, session, "admin-subscriptions.html")


@router.route("/admin/students", methods=["GET"])
def admin_students_page():    
    from flask import g
    db = getattr(g, "db", None)
    session = db
    
    from flask import g
    db = getattr(g, "db", None)
    session = db
    return _admin_page(request, session, "admin-students.html")


@router.route("/admin/student-manage", methods=["GET"])
def admin_student_manage_page():    
    from flask import g
    db = getattr(g, "db", None)
    session = db
    
    from flask import g
    db = getattr(g, "db", None)
    session = db
    return _admin_page(request, session, "admin-student-manage.html")


@router.route("/admin/questions", methods=["GET"])
def admin_questions_page():    
    from flask import g
    db = getattr(g, "db", None)
    session = db
    
    from flask import g
    db = getattr(g, "db", None)
    session = db
    return _admin_page(request, session, "admin-questions.html")


@router.route("/admin/exams", methods=["GET"])
def admin_exams_page():    
    from flask import g
    db = getattr(g, "db", None)
    session = db
    
    from flask import g
    db = getattr(g, "db", None)
    session = db
    payload = resolve_payload(request, session)
    if payload is None:
        return RedirectResponse(url="/login")
    role = payload.get("role", "")
    if _is_platform_admin(role):
        resp = FileResponse(str(_HTML_DIR / "admin-exams.html"), media_type="text/html")
        resp.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        resp.headers["Pragma"] = "no-cache"
        resp.headers["Expires"] = "0"
        return resp
    if _is_institution_student(payload):
        return RedirectResponse(url="/student/institution/dashboard")
    if role == "student":
        return RedirectResponse(url="/dashboard")
    if role == "institution_admin":
        return RedirectResponse(url="/institution/dashboard")
    return RedirectResponse(url="/login")


@router.route("/admin/analytics", methods=["GET"])
def admin_analytics_page():    
    from flask import g
    db = getattr(g, "db", None)
    session = db
    
    from flask import g
    db = getattr(g, "db", None)
    session = db
    return _admin_page(request, session, "admin-analytics.html")


# ---------------------------------------------------------------------------
# Institution admin pages
# ---------------------------------------------------------------------------

def _institution_page(session: Session, html_file: str):
    payload = resolve_payload(request, session)
    if payload is None:
        return RedirectResponse(url="/login")
    role = payload.get("role", "")
    if role == "institution_admin":
        return FileResponse(str(_HTML_DIR / html_file), media_type="text/html")
    if _is_institution_student(payload):
        return RedirectResponse(url="/student/institution/dashboard")
    if role == "student":
        return RedirectResponse(url="/dashboard")
    if _is_platform_admin(role):
        return RedirectResponse(url="/admin/upload")
    return RedirectResponse(url="/login")


@router.route("/institution", methods=["GET"])
def institution_root():    
    from flask import g
    db = getattr(g, "db", None)
    session = db
    
    from flask import g
    db = getattr(g, "db", None)
    session = db
    payload = resolve_payload(request, session)
    if payload is None:
        return RedirectResponse(url="/login")
    role = payload.get("role", "")
    if role == "institution_admin":
        return RedirectResponse(url="/institution/dashboard")
    if _is_institution_student(payload):
        return RedirectResponse(url="/student/institution/dashboard")
    if role == "student":
        return RedirectResponse(url="/dashboard")
    if _is_platform_admin(role):
        return RedirectResponse(url="/admin/upload")
    return RedirectResponse(url="/login")


@router.route("/institution/dashboard", methods=["GET"])
def institution_dashboard_page():    
    from flask import g
    db = getattr(g, "db", None)
    session = db
    
    from flask import g
    db = getattr(g, "db", None)
    session = db
    return _institution_page(request, session, "institution-dashboard.html")


@router.route("/institution/students", methods=["GET"])
def institution_students_page():    
    from flask import g
    db = getattr(g, "db", None)
    session = db
    
    from flask import g
    db = getattr(g, "db", None)
    session = db
    return _institution_page(request, session, "institution-students.html")


@router.route("/institution/subscription", methods=["GET"])
def institution_subscription_page():    
    from flask import g
    db = getattr(g, "db", None)
    session = db
    
    from flask import g
    db = getattr(g, "db", None)
    session = db
    return _institution_page(request, session, "institution-subscription.html")


@router.route("/institution/pricing", methods=["GET"])
def institution_pricing_page():    
    from flask import g
    db = getattr(g, "db", None)
    session = db
    
    from flask import g
    db = getattr(g, "db", None)
    session = db
    return _institution_page(request, session, "institution-pricing.html")


@router.route("/institution/upload", methods=["GET"])
def institution_upload_page():    
    from flask import g
    db = getattr(g, "db", None)
    session = db
    
    from flask import g
    db = getattr(g, "db", None)
    session = db
    return _institution_page(request, session, "institution-upload.html")


@router.route("/institution/exams", methods=["GET"])
def institution_exams_page():    
    from flask import g
    db = getattr(g, "db", None)
    session = db
    
    from flask import g
    db = getattr(g, "db", None)
    session = db
    return _institution_page(request, session, "institution-exams.html")


@router.route("/institution/questions", methods=["GET"])
def institution_questions_page():    
    from flask import g
    db = getattr(g, "db", None)
    session = db
    
    from flask import g
    db = getattr(g, "db", None)
    session = db
    return _institution_page(request, session, "institution-questions.html")


@router.route("/institution/analytics", methods=["GET"])
def institution_analytics_page():    
    from flask import g
    db = getattr(g, "db", None)
    session = db
    
    from flask import g
    db = getattr(g, "db", None)
    session = db
    return _institution_page(request, session, "institution-analytics.html")


# ---------------------------------------------------------------------------
# Syllabus pages (public/role-aware)
# ---------------------------------------------------------------------------

@router.route("/syllabus", methods=["GET"])
def syllabus_page():    
    from flask import g
    db = getattr(g, "db", None)
    session = db
    
    from flask import g
    db = getattr(g, "db", None)
    session = db
    """Student-facing syllabus viewer. Unauthenticated → landing; admin → admin syllabus."""
    payload = resolve_payload(request, session)
    if payload is None:
        return FileResponse(str(_HTML_DIR / "syllabus.html"), media_type="text/html")
    role = payload.get("role", "")
    if _is_platform_admin(role):
        return RedirectResponse(url="/admin/syllabus")
    return FileResponse(str(_HTML_DIR / "syllabus.html"), media_type="text/html")


@router.route("/admin/syllabus", methods=["GET"])
def admin_syllabus_page():    
    from flask import g
    db = getattr(g, "db", None)
    session = db
    
    from flask import g
    db = getattr(g, "db", None)
    session = db
    return _admin_page(request, session, "admin-syllabus.html")


@router.route("/admin/textbook-upload", methods=["GET"])
def admin_textbook_upload_page():    
    from flask import g
    db = getattr(g, "db", None)
    session = db
    
    from flask import g
    db = getattr(g, "db", None)
    session = db
    return _admin_page(request, session, "admin-textbook-upload.html")


@router.route("/contact-us", methods=["GET"])
def contact_us_page():    
    from flask import g
    db = getattr(g, "db", None)
    session = db
    
    from flask import g
    db = getattr(g, "db", None)
    session = db
    """Contact Us page - accessible to authenticated users."""
    payload = resolve_payload(request, session)
    if payload is None:
        return RedirectResponse(url="/login")

    return FileResponse(str(_HTML_DIR / "contact-us.html"), media_type="text/html")


@router.route("/institution/syllabus", methods=["GET"])
def institution_syllabus_page():    
    from flask import g
    db = getattr(g, "db", None)
    session = db
    
    from flask import g
    db = getattr(g, "db", None)
    session = db
    return _institution_page(request, session, "institution-syllabus.html")


__all__ = ["router"]
