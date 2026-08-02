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

from pathlib import Path

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import FileResponse, RedirectResponse
from sqlalchemy.orm import Session

from ..db.session import get_session
from ..middleware.rbac import resolve_payload

router = APIRouter(tags=["pages"])

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_HTML_DIR = _PROJECT_ROOT / "frontend" / "html"
_REDIRECT = status.HTTP_302_FOUND


def _is_platform_admin(role: str) -> bool:
    """Accept both legacy 'admin' and new 'platform_admin' role strings."""
    return role in ("admin", "platform_admin")


def _is_institution_student(payload: dict) -> bool:
    """Return True for institution-linked students."""
    return (
        payload.get("role") == "student"
        and payload.get("student_subtype") == "institution_linked"
    )


def _is_personal_student(payload: dict) -> bool:
    """Return True for direct_subscriber (personal) students."""
    return (
        payload.get("role") == "student"
        and payload.get("student_subtype") != "institution_linked"
    )


# ---------------------------------------------------------------------------
# Root
# ---------------------------------------------------------------------------

@router.get("/", response_model=None)
@router.get("/index.html", response_model=None)
def root_page(request: Request, session: Session = Depends(get_session)):
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
        return RedirectResponse(url="/student/institution/dashboard", status_code=_REDIRECT)
    
    # Direct subscriber student (role=student but NOT institution_linked)
    if role == "student":
        return RedirectResponse(url="/dashboard", status_code=_REDIRECT)
    
    # Platform admin
    if role in ("admin", "platform_admin"):
        return RedirectResponse(url="/admin/dashboard", status_code=_REDIRECT)
    
    # Institution admin
    if role == "institution_admin":
        return RedirectResponse(url="/institution/dashboard", status_code=_REDIRECT)
    
    # Fallback - no recognized role
    return FileResponse(str(_HTML_DIR / "landing.html"), media_type="text/html")


# ---------------------------------------------------------------------------
# Public pages
# ---------------------------------------------------------------------------

@router.get("/login", response_model=None)
def login_page():
    return FileResponse(str(_HTML_DIR / "login.html"), media_type="text/html")


@router.get("/favicon.ico", response_model=None)
def favicon():
    """Serve the brand favicon. Silences the browser's automatic
    /favicon.ico request (previously a 404 since no asset was mounted)."""
    return FileResponse(
        str(_PROJECT_ROOT / "frontend" / "favicon.svg"),
        media_type="image/svg+xml",
    )


@router.get("/register", response_model=None)
def register_page():
    return FileResponse(str(_HTML_DIR / "register.html"), media_type="text/html")


@router.get("/institution-register", response_model=None)
def institution_register_page():
    return FileResponse(str(_HTML_DIR / "institution-register.html"), media_type="text/html")


@router.get("/not-found", response_model=None)
def not_found_page():
    return FileResponse(str(_HTML_DIR / "not-found.html"), media_type="text/html")


@router.get("/invitation-accept", response_model=None)
def invitation_accept_page():
    """Public — auth is checked client-side by invitation.js."""
    return FileResponse(str(_HTML_DIR / "invitation-accept.html"), media_type="text/html")


# ---------------------------------------------------------------------------
# Personal Student pages (direct_subscriber only)
# ---------------------------------------------------------------------------

@router.get("/dashboard", response_model=None)
def dashboard_page(request: Request, session: Session = Depends(get_session)):
    payload = resolve_payload(request, session)
    if payload is None:
        return RedirectResponse(url="/login", status_code=_REDIRECT)
    # Institution students → their own dashboard
    if _is_institution_student(payload):
        return RedirectResponse(url="/student/institution/dashboard", status_code=_REDIRECT)
    role = payload.get("role", "")
    if _is_platform_admin(role):
        return RedirectResponse(url="/admin/dashboard", status_code=_REDIRECT)
    if role == "institution_admin":
        return RedirectResponse(url="/institution/dashboard", status_code=_REDIRECT)
    if role == "student":
        return FileResponse(str(_HTML_DIR / "dashboard.html"), media_type="text/html")
    return RedirectResponse(url="/login", status_code=_REDIRECT)


@router.get("/exam", response_model=None)
def exam_page(request: Request, session: Session = Depends(get_session)):
    payload = resolve_payload(request, session)
    if payload is None:
        return RedirectResponse(url="/login", status_code=_REDIRECT)
    role = payload.get("role", "")
    # Institution students: if they have a specific exam_set_id query param they're
    # starting an actual exam — allow exam.html. Otherwise redirect to their exams listing.
    if _is_institution_student(payload):
        exam_set_id = request.query_params.get("set")
        if exam_set_id:
            # Coming from institution exams page with a specific set — allow through
            return FileResponse(str(_HTML_DIR / "exam.html"), media_type="text/html")
        return RedirectResponse(url="/student/institution/exams", status_code=_REDIRECT)
    if role in ("student", "institution_admin") or _is_platform_admin(role):
        return FileResponse(str(_HTML_DIR / "exam.html"), media_type="text/html")
    return RedirectResponse(url="/login", status_code=_REDIRECT)


@router.get("/subscription", response_model=None)
def subscription_page(request: Request, session: Session = Depends(get_session)):
    payload = resolve_payload(request, session)
    if payload is None:
        return RedirectResponse(url="/login", status_code=_REDIRECT)
    role = payload.get("role", "")
    if role == "student":
        # Institution-linked students have no personal subscription UI
        if _is_institution_student(payload):
            return RedirectResponse(url="/student/institution/dashboard", status_code=_REDIRECT)
        return FileResponse(str(_HTML_DIR / "subscription.html"), media_type="text/html")
    if _is_platform_admin(role):
        return RedirectResponse(url="/admin/upload", status_code=_REDIRECT)
    if role == "institution_admin":
        return RedirectResponse(url="/institution/subscription", status_code=_REDIRECT)
    return RedirectResponse(url="/login", status_code=_REDIRECT)


@router.get("/pricing", response_model=None)
def student_pricing_page(request: Request, session: Session = Depends(get_session)):
    """Student-facing subscription pricing page."""
    payload = resolve_payload(request, session)
    if payload is None:
        return RedirectResponse(url="/login", status_code=_REDIRECT)
    role = payload.get("role", "")
    if role == "student":
        # Institution-linked students cannot access personal pricing page
        if _is_institution_student(payload):
            return RedirectResponse(url="/student/institution/dashboard", status_code=_REDIRECT)
        return FileResponse(str(_HTML_DIR / "student-pricing.html"), media_type="text/html")
    if role == "institution_admin":
        return RedirectResponse(url="/institution/pricing", status_code=_REDIRECT)
    if _is_platform_admin(role):
        return RedirectResponse(url="/admin/subscriptions", status_code=_REDIRECT)
    return RedirectResponse(url="/login", status_code=_REDIRECT)


# ---------------------------------------------------------------------------
# Institution Student Platform  (/student/institution/*)
# ---------------------------------------------------------------------------

def _institution_student_page(request: Request, session: Session, html_file: str):
    """Guard: only institution_linked students can view these pages."""
    payload = resolve_payload(request, session)
    if payload is None:
        return RedirectResponse(url="/login", status_code=_REDIRECT)
    if _is_institution_student(payload):
        return FileResponse(str(_HTML_DIR / html_file), media_type="text/html")
    # Personal students → personal dashboard
    if payload.get("role") == "student":
        return RedirectResponse(url="/dashboard", status_code=_REDIRECT)
    if _is_platform_admin(payload.get("role", "")):
        return RedirectResponse(url="/admin/dashboard", status_code=_REDIRECT)
    if payload.get("role") == "institution_admin":
        return RedirectResponse(url="/institution/dashboard", status_code=_REDIRECT)
    return RedirectResponse(url="/login", status_code=_REDIRECT)


@router.get("/student/institution/dashboard", response_model=None)
def student_institution_dashboard_page(request: Request, session: Session = Depends(get_session)):
    return _institution_student_page(request, session, "student-institution-dashboard.html")


@router.get("/student/institution/exams", response_model=None)
def student_institution_exams_page(request: Request, session: Session = Depends(get_session)):
    return _institution_student_page(request, session, "student-institution-exams.html")


@router.get("/student/institution/performance", response_model=None)
def student_institution_performance_page(request: Request, session: Session = Depends(get_session)):
    return _institution_student_page(request, session, "student-institution-performance.html")


@router.get("/student/institution/leaderboard", response_model=None)
def student_institution_leaderboard_page(request: Request, session: Session = Depends(get_session)):
    return _institution_student_page(request, session, "student-institution-leaderboard.html")


# ---------------------------------------------------------------------------
# Platform admin pages
# ---------------------------------------------------------------------------

def _admin_page(request: Request, session: Session, html_file: str):
    payload = resolve_payload(request, session)
    if payload is None:
        return RedirectResponse(url="/login", status_code=_REDIRECT)
    role = payload.get("role", "")
    if _is_platform_admin(role):
        return FileResponse(str(_HTML_DIR / html_file), media_type="text/html")
    if _is_institution_student(payload):
        return RedirectResponse(url="/student/institution/dashboard", status_code=_REDIRECT)
    if role == "student":
        return RedirectResponse(url="/dashboard", status_code=_REDIRECT)
    if role == "institution_admin":
        return RedirectResponse(url="/institution/dashboard", status_code=_REDIRECT)
    return RedirectResponse(url="/login", status_code=_REDIRECT)


@router.get("/admin", response_model=None)
def admin_root(request: Request, session: Session = Depends(get_session)):
    payload = resolve_payload(request, session)
    if payload is None:
        return RedirectResponse(url="/login", status_code=_REDIRECT)
    role = payload.get("role", "")
    if _is_platform_admin(role):
        return RedirectResponse(url="/admin/dashboard", status_code=_REDIRECT)
    if _is_institution_student(payload):
        return RedirectResponse(url="/student/institution/dashboard", status_code=_REDIRECT)
    if role == "student":
        return RedirectResponse(url="/dashboard", status_code=_REDIRECT)
    return RedirectResponse(url="/login", status_code=_REDIRECT)


@router.get("/admin/upload", response_model=None)
def admin_upload_page(request: Request, session: Session = Depends(get_session)):
    return _admin_page(request, session, "admin-upload.html")


@router.get("/admin/dashboard", response_model=None)
def admin_dashboard_page(request: Request, session: Session = Depends(get_session)):
    return _admin_page(request, session, "admin-dashboard.html")


@router.get("/admin/institutions", response_model=None)
def admin_institutions_page(request: Request, session: Session = Depends(get_session)):
    return _admin_page(request, session, "admin-institutions.html")


@router.get("/admin/subscriptions", response_model=None)
def admin_subscriptions_page(request: Request, session: Session = Depends(get_session)):
    return _admin_page(request, session, "admin-subscriptions.html")


@router.get("/admin/students", response_model=None)
def admin_students_page(request: Request, session: Session = Depends(get_session)):
    return _admin_page(request, session, "admin-students.html")


@router.get("/admin/student-manage", response_model=None)
def admin_student_manage_page(request: Request, session: Session = Depends(get_session)):
    return _admin_page(request, session, "admin-student-manage.html")


@router.get("/admin/questions", response_model=None)
def admin_questions_page(request: Request, session: Session = Depends(get_session)):
    return _admin_page(request, session, "admin-questions.html")


@router.get("/admin/exams", response_model=None)
def admin_exams_page(request: Request, session: Session = Depends(get_session)):
    payload = resolve_payload(request, session)
    if payload is None:
        return RedirectResponse(url="/login", status_code=_REDIRECT)
    role = payload.get("role", "")
    if _is_platform_admin(role):
        resp = FileResponse(str(_HTML_DIR / "admin-exams.html"), media_type="text/html")
        resp.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        resp.headers["Pragma"] = "no-cache"
        resp.headers["Expires"] = "0"
        return resp
    if _is_institution_student(payload):
        return RedirectResponse(url="/student/institution/dashboard", status_code=_REDIRECT)
    if role == "student":
        return RedirectResponse(url="/dashboard", status_code=_REDIRECT)
    if role == "institution_admin":
        return RedirectResponse(url="/institution/dashboard", status_code=_REDIRECT)
    return RedirectResponse(url="/login", status_code=_REDIRECT)


@router.get("/admin/analytics", response_model=None)
def admin_analytics_page(request: Request, session: Session = Depends(get_session)):
    return _admin_page(request, session, "admin-analytics.html")


# ---------------------------------------------------------------------------
# Institution admin pages
# ---------------------------------------------------------------------------

def _institution_page(request: Request, session: Session, html_file: str):
    payload = resolve_payload(request, session)
    if payload is None:
        return RedirectResponse(url="/login", status_code=_REDIRECT)
    role = payload.get("role", "")
    if role == "institution_admin":
        return FileResponse(str(_HTML_DIR / html_file), media_type="text/html")
    if _is_institution_student(payload):
        return RedirectResponse(url="/student/institution/dashboard", status_code=_REDIRECT)
    if role == "student":
        return RedirectResponse(url="/dashboard", status_code=_REDIRECT)
    if _is_platform_admin(role):
        return RedirectResponse(url="/admin/upload", status_code=_REDIRECT)
    return RedirectResponse(url="/login", status_code=_REDIRECT)


@router.get("/institution", response_model=None)
def institution_root(request: Request, session: Session = Depends(get_session)):
    payload = resolve_payload(request, session)
    if payload is None:
        return RedirectResponse(url="/login", status_code=_REDIRECT)
    role = payload.get("role", "")
    if role == "institution_admin":
        return RedirectResponse(url="/institution/dashboard", status_code=_REDIRECT)
    if _is_institution_student(payload):
        return RedirectResponse(url="/student/institution/dashboard", status_code=_REDIRECT)
    if role == "student":
        return RedirectResponse(url="/dashboard", status_code=_REDIRECT)
    if _is_platform_admin(role):
        return RedirectResponse(url="/admin/upload", status_code=_REDIRECT)
    return RedirectResponse(url="/login", status_code=_REDIRECT)


@router.get("/institution/dashboard", response_model=None)
def institution_dashboard_page(request: Request, session: Session = Depends(get_session)):
    return _institution_page(request, session, "institution-dashboard.html")


@router.get("/institution/students", response_model=None)
def institution_students_page(request: Request, session: Session = Depends(get_session)):
    return _institution_page(request, session, "institution-students.html")


@router.get("/institution/subscription", response_model=None)
def institution_subscription_page(request: Request, session: Session = Depends(get_session)):
    return _institution_page(request, session, "institution-subscription.html")


@router.get("/institution/pricing", response_model=None)
def institution_pricing_page(request: Request, session: Session = Depends(get_session)):
    return _institution_page(request, session, "institution-pricing.html")


@router.get("/institution/upload", response_model=None)
def institution_upload_page(request: Request, session: Session = Depends(get_session)):
    return _institution_page(request, session, "institution-upload.html")


@router.get("/institution/exams", response_model=None)
def institution_exams_page(request: Request, session: Session = Depends(get_session)):
    return _institution_page(request, session, "institution-exams.html")


@router.get("/institution/questions", response_model=None)
def institution_questions_page(request: Request, session: Session = Depends(get_session)):
    return _institution_page(request, session, "institution-questions.html")


@router.get("/institution/analytics", response_model=None)
def institution_analytics_page(request: Request, session: Session = Depends(get_session)):
    return _institution_page(request, session, "institution-analytics.html")


# ---------------------------------------------------------------------------
# Syllabus pages (public/role-aware)
# ---------------------------------------------------------------------------

@router.get("/syllabus", response_model=None)
def syllabus_page(request: Request, session: Session = Depends(get_session)):
    """Student-facing syllabus viewer. Unauthenticated → landing; admin → admin syllabus."""
    payload = resolve_payload(request, session)
    if payload is None:
        return FileResponse(str(_HTML_DIR / "syllabus.html"), media_type="text/html")
    role = payload.get("role", "")
    if _is_platform_admin(role):
        return RedirectResponse(url="/admin/syllabus", status_code=_REDIRECT)
    return FileResponse(str(_HTML_DIR / "syllabus.html"), media_type="text/html")


@router.get("/admin/syllabus", response_model=None)
def admin_syllabus_page(request: Request, session: Session = Depends(get_session)):
    return _admin_page(request, session, "admin-syllabus.html")


@router.get("/admin/textbook-upload", response_model=None)
def admin_textbook_upload_page(request: Request, session: Session = Depends(get_session)):
    return _admin_page(request, session, "admin-textbook-upload.html")


@router.get("/contact-us", response_model=None)
def contact_us_page(request: Request, session: Session = Depends(get_session)):
    """Contact Us page - accessible to authenticated users."""
    payload = resolve_payload(request, session)
    if payload is None:
        return RedirectResponse(url="/login", status_code=_REDIRECT)

    return FileResponse(str(_HTML_DIR / "contact-us.html"), media_type="text/html")


@router.get("/institution/syllabus", response_model=None)
def institution_syllabus_page(request: Request, session: Session = Depends(get_session)):
    return _institution_page(request, session, "institution-syllabus.html")


__all__ = ["router"]
