"""HTML page routes with role-aware redirects and static file serving for Flask."""

from __future__ import annotations

from pathlib import Path
from flask import Blueprint, redirect, request, send_file, send_from_directory
from sqlalchemy.orm import Session

from ..db.session import get_db
from ..middleware.rbac import resolve_payload

router = Blueprint("pages", __name__)

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_HTML_DIR = _PROJECT_ROOT / "frontend" / "html"


def _is_platform_admin(role: str) -> bool:
    return role in ("admin", "platform_admin")


def _is_institution_student(payload: dict) -> bool:
    return (
        payload.get("role") == "student"
        and payload.get("student_subtype") == "institution_linked"
    )


@router.route("/", methods=["GET"])
@router.route("/index.html", methods=["GET"])
def root_page():
    session: Session = get_db()
    payload = resolve_payload(request, session)

    if payload is None:
        return send_file(str(_HTML_DIR / "landing.html"), mimetype="text/html")

    role = payload.get("role", "").strip().lower()
    student_subtype = payload.get("student_subtype", "").strip().lower()

    if role == "student" and student_subtype == "institution_linked":
        return redirect("/student/institution/dashboard", code=302)

    if role == "student":
        return redirect("/dashboard", code=302)

    if role in ("admin", "platform_admin"):
        return redirect("/admin/dashboard", code=302)

    if role == "institution_admin":
        return redirect("/institution/dashboard", code=302)

    return send_file(str(_HTML_DIR / "landing.html"), mimetype="text/html")


@router.route("/login", methods=["GET"])
def login_page():
    return send_file(str(_HTML_DIR / "login.html"), mimetype="text/html")


@router.route("/favicon.ico", methods=["GET"])
def favicon():
    return send_file(str(_PROJECT_ROOT / "frontend" / "favicon.svg"), mimetype="image/svg+xml")


@router.route("/register", methods=["GET"])
def register_page():
    return send_file(str(_HTML_DIR / "register.html"), mimetype="text/html")


@router.route("/institution-register", methods=["GET"])
def institution_register_page():
    return send_file(str(_HTML_DIR / "institution-register.html"), mimetype="text/html")


@router.route("/not-found", methods=["GET"])
def not_found_page():
    return send_file(str(_HTML_DIR / "not-found.html"), mimetype="text/html")


@router.route("/invitation-accept", methods=["GET"])
def invitation_accept_page():
    return send_file(str(_HTML_DIR / "invitation-accept.html"), mimetype="text/html")


@router.route("/dashboard", methods=["GET"])
def dashboard_page():
    session: Session = get_db()
    payload = resolve_payload(request, session)
    if payload is None:
        return redirect("/login", code=302)
    if _is_institution_student(payload):
        return redirect("/student/institution/dashboard", code=302)
    role = payload.get("role", "")
    if _is_platform_admin(role):
        return redirect("/admin/dashboard", code=302)
    if role == "institution_admin":
        return redirect("/institution/dashboard", code=302)
    if role == "student":
        return send_file(str(_HTML_DIR / "dashboard.html"), mimetype="text/html")
    return redirect("/login", code=302)


@router.route("/exam", methods=["GET"])
def exam_page():
    session: Session = get_db()
    payload = resolve_payload(request, session)
    if payload is None:
        return redirect("/login", code=302)
    role = payload.get("role", "")
    if _is_institution_student(payload):
        exam_set_id = request.args.get("set")
        if exam_set_id:
            return send_file(str(_HTML_DIR / "exam.html"), mimetype="text/html")
        return redirect("/student/institution/exams", code=302)
    if role in ("student", "institution_admin") or _is_platform_admin(role):
        return send_file(str(_HTML_DIR / "exam.html"), mimetype="text/html")
    return redirect("/login", code=302)


@router.route("/subscription", methods=["GET"])
def subscription_page():
    session: Session = get_db()
    payload = resolve_payload(request, session)
    if payload is None:
        return redirect("/login", code=302)
    role = payload.get("role", "")
    if role == "student":
        if _is_institution_student(payload):
            return redirect("/student/institution/dashboard", code=302)
        return send_file(str(_HTML_DIR / "subscription.html"), mimetype="text/html")
    if _is_platform_admin(role):
        return redirect("/admin/upload", code=302)
    if role == "institution_admin":
        return redirect("/institution/subscription", code=302)
    return redirect("/login", code=302)


@router.route("/pricing", methods=["GET"])
def student_pricing_page():
    session: Session = get_db()
    payload = resolve_payload(request, session)
    if payload is None:
        return redirect("/login", code=302)
    role = payload.get("role", "")
    if role == "student":
        if _is_institution_student(payload):
            return redirect("/student/institution/dashboard", code=302)
        return send_file(str(_HTML_DIR / "student-pricing.html"), mimetype="text/html")
    if role == "institution_admin":
        return redirect("/institution/pricing", code=302)
    if _is_platform_admin(role):
        return redirect("/admin/subscriptions", code=302)
    return redirect("/login", code=302)


def _institution_student_page(html_file: str):
    session: Session = get_db()
    payload = resolve_payload(request, session)
    if payload is None:
        return redirect("/login", code=302)
    if _is_institution_student(payload):
        return send_file(str(_HTML_DIR / html_file), mimetype="text/html")
    if payload.get("role") == "student":
        return redirect("/dashboard", code=302)
    if _is_platform_admin(payload.get("role", "")):
        return redirect("/admin/dashboard", code=302)
    if payload.get("role") == "institution_admin":
        return redirect("/institution/dashboard", code=302)
    return redirect("/login", code=302)


@router.route("/student/institution/dashboard", methods=["GET"])
def student_institution_dashboard_page():
    return _institution_student_page("student-institution-dashboard.html")


@router.route("/student/institution/exams", methods=["GET"])
def student_institution_exams_page():
    return _institution_student_page("student-institution-exams.html")


@router.route("/student/institution/performance", methods=["GET"])
def student_institution_performance_page():
    return _institution_student_page("student-institution-performance.html")


@router.route("/student/institution/leaderboard", methods=["GET"])
def student_institution_leaderboard_page():
    return _institution_student_page("student-institution-leaderboard.html")


def _admin_page(html_file: str):
    session: Session = get_db()
    payload = resolve_payload(request, session)
    if payload is None:
        return redirect("/login", code=302)
    role = payload.get("role", "")
    if _is_platform_admin(role):
        return send_file(str(_HTML_DIR / html_file), mimetype="text/html")
    if _is_institution_student(payload):
        return redirect("/student/institution/dashboard", code=302)
    if role == "student":
        return redirect("/dashboard", code=302)
    if role == "institution_admin":
        return redirect("/institution/dashboard", code=302)
    return redirect("/login", code=302)


@router.route("/admin", methods=["GET"])
def admin_root():
    session: Session = get_db()
    payload = resolve_payload(request, session)
    if payload is None:
        return redirect("/login", code=302)
    role = payload.get("role", "")
    if _is_platform_admin(role):
        return redirect("/admin/dashboard", code=302)
    if _is_institution_student(payload):
        return redirect("/student/institution/dashboard", code=302)
    if role == "student":
        return redirect("/dashboard", code=302)
    return redirect("/login", code=302)


@router.route("/admin/upload", methods=["GET"])
def admin_upload_page():
    return _admin_page("admin-upload.html")


@router.route("/admin/dashboard", methods=["GET"])
def admin_dashboard_page():
    return _admin_page("admin-dashboard.html")


@router.route("/admin/institutions", methods=["GET"])
def admin_institutions_page():
    return _admin_page("admin-institutions.html")


@router.route("/admin/subscriptions", methods=["GET"])
def admin_subscriptions_page():
    return _admin_page("admin-subscriptions.html")


@router.route("/admin/students", methods=["GET"])
def admin_students_page():
    return _admin_page("admin-students.html")


@router.route("/admin/student-manage", methods=["GET"])
def admin_student_manage_page():
    return _admin_page("admin-student-manage.html")


@router.route("/admin/questions", methods=["GET"])
def admin_questions_page():
    return _admin_page("admin-questions.html")


@router.route("/admin/exams", methods=["GET"])
def admin_exams_page():
    session: Session = get_db()
    payload = resolve_payload(request, session)
    if payload is None:
        return redirect("/login", code=302)
    role = payload.get("role", "")
    if _is_platform_admin(role):
        res = send_file(str(_HTML_DIR / "admin-exams.html"), mimetype="text/html")
        res.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        res.headers["Pragma"] = "no-cache"
        res.headers["Expires"] = "0"
        return res
    if _is_institution_student(payload):
        return redirect("/student/institution/dashboard", code=302)
    if role == "student":
        return redirect("/dashboard", code=302)
    if role == "institution_admin":
        return redirect("/institution/dashboard", code=302)
    return redirect("/login", code=302)


@router.route("/admin/analytics", methods=["GET"])
def admin_analytics_page():
    return _admin_page("admin-analytics.html")


def _institution_page(html_file: str):
    session: Session = get_db()
    payload = resolve_payload(request, session)
    if payload is None:
        return redirect("/login", code=302)
    role = payload.get("role", "")
    if role == "institution_admin":
        return send_file(str(_HTML_DIR / html_file), mimetype="text/html")
    if _is_institution_student(payload):
        return redirect("/student/institution/dashboard", code=302)
    if role == "student":
        return redirect("/dashboard", code=302)
    if _is_platform_admin(role):
        return redirect("/admin/upload", code=302)
    return redirect("/login", code=302)


@router.route("/institution", methods=["GET"])
def institution_root():
    session: Session = get_db()
    payload = resolve_payload(request, session)
    if payload is None:
        return redirect("/login", code=302)
    role = payload.get("role", "")
    if role == "institution_admin":
        return redirect("/institution/dashboard", code=302)
    if _is_institution_student(payload):
        return redirect("/student/institution/dashboard", code=302)
    if role == "student":
        return redirect("/dashboard", code=302)
    if _is_platform_admin(role):
        return redirect("/admin/upload", code=302)
    return redirect("/login", code=302)


@router.route("/institution/dashboard", methods=["GET"])
def institution_dashboard_page():
    return _institution_page("institution-dashboard.html")


@router.route("/institution/students", methods=["GET"])
def institution_students_page():
    return _institution_page("institution-students.html")


@router.route("/institution/subscription", methods=["GET"])
def institution_subscription_page():
    return _institution_page("institution-subscription.html")


@router.route("/institution/pricing", methods=["GET"])
def institution_pricing_page():
    return _institution_page("institution-pricing.html")


@router.route("/institution/upload", methods=["GET"])
def institution_upload_page():
    return _institution_page("institution-upload.html")


@router.route("/institution/exams", methods=["GET"])
def institution_exams_page():
    return _institution_page("institution-exams.html")


@router.route("/institution/questions", methods=["GET"])
def institution_questions_page():
    return _institution_page("institution-questions.html")


@router.route("/institution/analytics", methods=["GET"])
def institution_analytics_page():
    return _institution_page("institution-analytics.html")


@router.route("/syllabus", methods=["GET"])
def syllabus_page():
    session: Session = get_db()
    payload = resolve_payload(request, session)
    if payload is None:
        return send_file(str(_HTML_DIR / "syllabus.html"), mimetype="text/html")
    role = payload.get("role", "")
    if _is_platform_admin(role):
        return redirect("/admin/syllabus", code=302)
    return send_file(str(_HTML_DIR / "syllabus.html"), mimetype="text/html")


@router.route("/admin/syllabus", methods=["GET"])
def admin_syllabus_page():
    return _admin_page("admin-syllabus.html")


@router.route("/admin/textbook-upload", methods=["GET"])
def admin_textbook_upload_page():
    return _admin_page("admin-textbook-upload.html")


@router.route("/contact-us", methods=["GET"])
def contact_us_page():
    session: Session = get_db()
    payload = resolve_payload(request, session)
    if payload is None:
        return redirect("/login", code=302)
    return send_file(str(_HTML_DIR / "contact-us.html"), mimetype="text/html")


@router.route("/institution/syllabus", methods=["GET"])
def institution_syllabus_page():
    return _institution_page("institution-syllabus.html")


__all__ = ["router"]
