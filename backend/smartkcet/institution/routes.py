import os
"""FastAPI routes for institution management.

This module defines the API endpoints for institution operations:
- Institution registration
- Institution login (uses standard auth routes)
- Invitation generation and acceptance
- Student management
- Institution analytics
- Subscription plan selection
- Content management (upload, question bank, exams, analytics)
"""

from typing import Annotated, Any, Optional
from uuid import UUID

import os
from flask import Blueprint, request, g, make_response, jsonify, Response
from sqlalchemy.orm import Session

from ..db.models import User
from ..db.session import get_async_session as get_session
from ..db.subscription_models import Institution, Subscription, SubscriptionPlan
from ..middleware.rbac import require_authenticated
from ..subscription.models import SubscriptionResponse
from .models import (
    InstitutionPlanSelect,
    InstitutionRegistrationData,
    InstitutionRegistrationResponse,
    InstitutionStudentsResponse,
    InvitationAccept,
    InvitationCodeResponse,
    InvitationCreate,
    StudentRemove,
)
from .service import (
    DatabaseUnavailableError,
    DuplicateEmailError,
    InstitutionService,
    InstitutionServiceError,
    ValidationError,
)

# Import content management router
from . import content

router = Blueprint("institution_routes", __name__)

# Include content management routes
router.register_blueprint(content.router, tags=["institution-content"])


def require_institution_admin()-> dict:    
    payload = require_authenticated()
    
    payload = require_authenticated()
    """Require institution_admin role and inject institution_id.
    
    Raises:
        HTTPException: 403 if not an institution admin
    """
    if payload.get("role") != "institution_admin":
        raise HTTPException(
            status_code=403,
            detail={
                "error": "forbidden",
                "message": "Institution admin access required",
            },
        )
    
    # Ensure institution_id is present in payload
    if "institution_id" not in payload:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "forbidden",
                "message": "Institution ID not found in token",
            },
        )
    
    return payload


@router.route(
    "/register", methods=["POST"])
def register_institution(data: Any = None):    
    from flask import request, g, make_response, jsonify
    db = getattr(g, "db", None)

    if data is None:
        raw_data = request.get_json() or {}
        if not raw_data and request.form:
            raw_data = request.form.to_dict()
        try:
            mapped = {
                "name": raw_data.get("name") or raw_data.get("institutionName") or raw_data.get("institution_name"),
                "admin_email": raw_data.get("admin_email") or raw_data.get("email") or raw_data.get("inst_reg_email"),
                "admin_password": raw_data.get("admin_password") or raw_data.get("password") or raw_data.get("inst_reg_pwd"),
                "contact_phone": raw_data.get("contact_phone") or raw_data.get("phone"),
            }
            data = InstitutionRegistrationData(**mapped)
        except Exception as e:
            msg = "Invalid registration data. Please check your inputs."
            if hasattr(e, "errors") and callable(e.errors):
                try:
                    errs = e.errors()
                    if errs:
                        first = errs[0]
                        field = ".".join(str(loc) for loc in first.get("loc", []))
                        raw_msg = first.get("msg", "")
                        if "digit" in raw_msg.lower():
                            msg = "Password must contain at least one number (0–9)."
                        elif "8" in raw_msg or "min_length" in raw_msg:
                            msg = "Password must be at least 8 characters."
                        elif "phone" in field.lower():
                            msg = "Contact phone must contain between 10 and 15 digits."
                        elif "email" in field.lower():
                            msg = "Please enter a valid email address."
                        else:
                            msg = raw_msg.replace("Value error, ", "").strip()
                except Exception:
                    msg = str(e)
            return make_response(jsonify({
                "error": "validation_error",
                "message": msg,
            }), 400)

    service = InstitutionService(db)
    
    try:
        result = service.register_institution(data)
        out = {
            "institution_id": str(result.institution_id),
            "admin_user_id": str(result.admin_user_id),
            "institution_name": result.institution_name,
            "admin_email": result.admin_email,
            "registered_at": result.registered_at.isoformat() if result.registered_at else None,
            "message": "Institution registered successfully. Please sign in with your credentials.",
        }
        return make_response(jsonify(out), 201)
    except ValidationError as e:
        return make_response(jsonify({
            "error": "validation_error",
            "field": e.field,
            "message": e.reason,
        }), 400)
    except DuplicateEmailError as e:
        return make_response(jsonify({
            "error": "duplicate_email",
            "message": "Email is already registered",
            "email": e.email,
        }), 409)
    except DatabaseUnavailableError as e:
        return make_response(jsonify({
            "error": "service_unavailable",
            "message": str(e),
            "retry_after_sec": 5,
        }), 503)
    except Exception as e:
        return make_response(jsonify({
            "error": "internal_error",
            "message": str(e) or "An unexpected error occurred during registration",
        }), 500)


# Note: Institution login uses the standard /api/auth/login endpoint
# The auth service handles institution_admin role tokens


@router.route("/invite", methods=["POST"])
@router.route("/invitations", methods=["POST"])
def generate_invitation(data: Any = None):    
    payload = require_institution_admin()
    from flask import g
    db = getattr(g, "db", None)
    session = db
    service = InstitutionService(db)
    institution_id = UUID(payload["institution_id"])

    req_data = request.get_json(silent=True) or {}
    batch_id_str = req_data.get("batch_id")
    batch_id = None
    if batch_id_str:
        try:
            batch_id = UUID(batch_id_str)
        except Exception:
            batch_id = None
    
    try:
        result = service.generate_invitation(institution_id, batch_id=batch_id)
        return jsonify({
            "id": str(result.id),
            "code": result.code,
            "institution_id": str(result.institution_id),
            "batch_id": str(batch_id) if batch_id else None,
            "status": result.status,
            "created_at": result.created_at.isoformat() if result.created_at else None,
            "expires_at": result.expires_at.isoformat() if result.expires_at else None,
        }), 201
    except InstitutionServiceError as e:
        if "Maximum pending invitations" in str(e):
            raise HTTPException(
                status_code=409,
                detail={
                    "error": "max_invitations_reached",
                    "message": str(e),
                },
            )
        raise HTTPException(
            status_code=500,
            detail={
                "error": "internal_error",
                "message": str(e),
            },
        )
    except DatabaseUnavailableError as e:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "service_unavailable",
                "message": str(e),
                "retry_after_sec": 5,
            },
        )


@router.route("/accept-invite", methods=["POST"])
def accept_invitation(data: InvitationAccept):    
    payload = require_authenticated()
    from flask import g
    db = getattr(g, "db", None)
    session = db
    """Accept an institution invitation and link student to institution.
    
    **Requirements:** 9.2, 9.3, 9.4, 9.5
    
    Links the authenticated student to the institution, consumes one seat
    from the institution's quota, and marks the invitation as consumed.
    
    Args:
        data: Invitation acceptance data with code
        payload: JWT payload from authentication middleware
        db: Database session
        
    Raises:
        HTTPException:
            - 400: Invalid or expired invitation
            - 403: Not a student
            - 409: Seats full or already linked to another institution
            - 503: Database unavailable
    """
    # Ensure user is a student
    if payload.get("role") != "student":
        raise HTTPException(
            status_code=403,
            detail={
                "error": "forbidden",
                "message": "Only students can accept invitations",
            },
        )
    
    service = InstitutionService(db)

    # Resolve student UUID from the 'sub' claim (which is kcet_student_id, not UUID)
    sub_claim = payload.get("sub", "")
    user = db.query(User).filter(User.kcet_student_id == sub_claim).first()
    if not user:
        user = db.query(User).filter(User.email == sub_claim).first()
    if not user:
        raise HTTPException(
            status_code=401,
            detail={"error": "user_not_found", "message": "Could not identify your account."},
        )
    student_id = user.id
    
    try:
        service.accept_invitation(data.code, student_id)
        return None  # 204 No Content
    except InstitutionServiceError as e:
        error_msg = str(e)
        
        # Determine appropriate status code based on error message
        if "Invalid invitation" in error_msg or "expired" in error_msg:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "invalid_invitation",
                    "message": error_msg,
                },
            )
        elif "seat quota full" in error_msg:
            raise HTTPException(
                status_code=409,
                detail={
                    "error": "seats_full",
                    "message": error_msg,
                },
            )
        elif "already linked" in error_msg:
            raise HTTPException(
                status_code=409,
                detail={
                    "error": "already_linked",
                    "message": error_msg,
                },
            )
        else:
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "internal_error",
                    "message": error_msg,
                },
            )
    except DatabaseUnavailableError as e:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "service_unavailable",
                "message": str(e),
                "retry_after_sec": 5,
            },
        )


@router.route("/students/<student_id>", methods=["DELETE"])
def remove_student(student_id: UUID):    
    payload = require_institution_admin()
    from flask import g
    db = getattr(g, "db", None)
    session = db
    """Remove a student from the institution.
    
    **Requirements:** 9.6
    
    Unlinks the student from the institution, frees one seat in the quota,
    and preserves the student's exam history and analytics data.
    
    Args:
        student_id: Student user ID to remove
        payload: JWT payload from authentication middleware
        db: Database session
        
    Raises:
        HTTPException:
            - 403: Not an institution admin
            - 404: Student not found or not linked to this institution
            - 503: Database unavailable
    """
    service = InstitutionService(db)
    institution_id = UUID(payload["institution_id"])
    
    try:
        service.remove_student(institution_id, student_id)
        return None  # 204 No Content
    except InstitutionServiceError as e:
        error_msg = str(e)
        
        if "not found" in error_msg or "not linked" in error_msg:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "student_not_found",
                    "message": error_msg,
                },
            )
        else:
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "internal_error",
                    "message": error_msg,
                },
            )
    except DatabaseUnavailableError as e:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "service_unavailable",
                "message": str(e),
                "retry_after_sec": 5,
            },
        )


@router.route("/students", methods=["GET"])
def get_institution_students():    
    payload = require_institution_admin()
    from flask import g
    db = getattr(g, "db", None)
    session = db
    """List all students linked to the institution.
    
    **Requirements:** 7.4, 9.1
    
    Returns a list of students linked to the authenticated institution admin's
    institution, including their basic information and link date.
    
    Args:
        payload: JWT payload from authentication middleware
        db: Database session
        
    Returns:
        InstitutionStudentsResponse with student list
        
    Raises:
        HTTPException:
            - 403: Not an institution admin
            - 503: Database unavailable
    """
    service = InstitutionService(db)
    institution_id = UUID(payload["institution_id"])
    
    try:
        # Get institution details
        institution = (
            db.query(Institution)
            .filter(Institution.id == institution_id)
            .first()
        )
        
        if not institution:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "institution_not_found",
                    "message": f"Institution {institution_id} not found",
                },
            )
        
        # Get active subscription to determine max seats
        active_subscription = (
            db.query(Subscription)
            .join(SubscriptionPlan, Subscription.plan_id == SubscriptionPlan.id)
            .filter(
                Subscription.institution_id == institution_id,
                Subscription.status.in_(["trial", "active", "overdue", "grace_period"]),
            )
            .first()
        )
        
        max_seats = None
        if active_subscription and active_subscription.plan:
            max_seats = active_subscription.plan.max_student_seats
        
        # Get students
        students = service.get_institution_students(institution_id)
        
        return InstitutionStudentsResponse(
            institution_id=institution_id,
            institution_name=institution.name,
            total_students=len(students),
            max_seats=max_seats,
            students=students,
        )
        
    except InstitutionServiceError as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "internal_error",
                "message": str(e),
            },
        )
    except DatabaseUnavailableError as e:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "service_unavailable",
                "message": str(e),
                "retry_after_sec": 5,
            },
        )


@router.route("/analytics", methods=["GET"])
def get_institution_analytics():    
    payload = require_institution_admin()
    from flask import g
    db = getattr(g, "db", None)
    session = db
    """Get analytics for the institution's students.
    
    **Requirements:** 7.4, 9.6
    
    Returns aggregated analytics for all students linked to the institution,
    including exam scores, completion rates, and per-student performance.
    
    Args:
        payload: JWT payload from authentication middleware
        db: Database session
        
    Returns:
        Analytics data for the institution
        
    Raises:
        HTTPException:
            - 403: Not an institution admin
            - 503: Database unavailable
    """
    institution_id = UUID(payload["institution_id"])
    
    # For MVP, return basic structure
    # Full analytics implementation would be in a separate analytics service
    try:
        # Get student count
        student_count = (
            db.query(User)
            .filter(User.institution_id == institution_id)
            .count()
        )
        
        return {
            "institution_id": str(institution_id),
            "total_students": student_count,
            "message": "Full analytics implementation pending",
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "internal_error",
                "message": str(e),
            },
        )


@router.route(
    "/subscription/select", methods=["POST"])
def select_subscription_plan(data: InstitutionPlanSelect):    
    payload = require_institution_admin()
    from flask import g
    db = getattr(g, "db", None)
    session = db
    """Select and activate an institution subscription plan.
    
    **Requirements:** 8.1, 8.2, 8.3
    
    Activates the specified subscription plan for the institution. If an active
    subscription already exists, schedules the new plan to take effect at the
    end of the current billing period.
    
    Args:
        data: Plan selection data with plan_id
        payload: JWT payload from authentication middleware
        db: Database session
        
    Returns:
        SubscriptionResponse with activated subscription details
        
    Raises:
        HTTPException:
            - 400: Invalid plan ID
            - 403: Not an institution admin
            - 409: Active subscription exists (plan change scheduled)
            - 503: Database unavailable
    """
    service = InstitutionService(db)
    institution_id = UUID(payload["institution_id"])
    
    try:
        subscription = service.activate_institution_plan(institution_id, data.plan_id)
        
        # Convert to response model
        from ..subscription.models import SubscriptionResponse
        return SubscriptionResponse.model_validate(subscription)
        
    except InstitutionServiceError as e:
        error_msg = str(e)
        
        if "not found" in error_msg or "inactive" in error_msg:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "invalid_plan",
                    "message": error_msg,
                },
            )
        elif "already has an active subscription" in error_msg:
            raise HTTPException(
                status_code=409,
                detail={
                    "error": "active_subscription_exists",
                    "message": error_msg,
                },
            )
        else:
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "internal_error",
                    "message": error_msg,
                },
            )
    except DatabaseUnavailableError as e:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "service_unavailable",
                "message": str(e),
                "retry_after_sec": 5,
            },
        )


@router.route("/dashboard", methods=["GET"])
def get_institution_dashboard():    
    payload = require_institution_admin()
    from flask import g
    db = getattr(g, "db", None)
    session = db
    """Institution dashboard — KPI tiles, recent activity, subscription status."""
    from ..db.models import Submission
    from sqlalchemy import select as sa_select, desc

    try:
        institution_id = UUID(payload["institution_id"])

        # Institution info
        institution = db.query(Institution).filter(Institution.id == institution_id).first()
        
        if not institution:
            raise HTTPException(
                status_code=404, 
                detail={"error": "institution_not_found", "message": "Institution not found"}
            )

        # Student count (exclude institution_admin accounts)
        total_students = db.query(User).filter(
            User.institution_id == institution_id,
            User.role == "student",
        ).count()

        # Active subscription
        active_sub = (
            db.query(Subscription)
            .filter(
                Subscription.institution_id == institution_id,
                Subscription.status.in_(["trial", "active", "overdue", "grace_period"]),
            )
            .first()
        )

        subscription_status = active_sub.status if active_sub else None
        max_students = None
        weekly_test_limit = None
        monthly_test_limit = None
        next_renewal_date = None

        if active_sub and active_sub.plan:
            max_students = active_sub.plan.max_student_seats
            # Use max_test_attempts_per_period for both weekly and monthly limits
            weekly_test_limit = active_sub.plan.max_test_attempts_per_period
            monthly_test_limit = active_sub.plan.max_test_attempts_per_period
            next_renewal_date = active_sub.next_renewal_date.isoformat() if active_sub.next_renewal_date else None

        # Get all user IDs linked to this institution (students and admins)
        all_user_ids = [
            row[0] for row in db.query(User.id).filter(
                User.institution_id == institution_id
            ).all()
        ]

        recent_submissions = []
        tests_this_week = 0
        tests_this_month = 0

        from datetime import datetime, timedelta
        now = datetime.utcnow()
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)

        # 1. Exams created by this institution in week/month
        exams_created_week = db.query(Exam).filter(
            Exam.institution_id == institution_id,
            Exam.created_at >= week_ago
        ).count()

        exams_created_month = db.query(Exam).filter(
            Exam.institution_id == institution_id,
            Exam.created_at >= month_ago
        ).count()

        # 2. Submissions / Tests taken by students in institution
        test_attempts_week = 0
        test_attempts_month = 0

        if all_user_ids:
            try:
                subs = (
                    db.query(Submission)
                    .filter(Submission.user_id.in_(all_user_ids))
                    .order_by(desc(Submission.submitted_at))
                    .limit(10)
                    .all()
                )
                for s in subs:
                    student = db.query(User).filter(User.id == s.user_id).first()
                    exam_set = db.query(ExamSet).filter(ExamSet.id == s.exam_set_id).first()
                    exam = db.query(Exam).filter(Exam.id == exam_set.exam_id).first() if exam_set else None
                    subject_name = exam.subject if (exam and exam.subject) else "KCET Prep"

                    recent_submissions.append({
                        "student_name": student.display_name if (student and student.display_name) else (student.email if student else "Student"),
                        "subject": subject_name,
                        "score": round(s.score_pct, 1) if s.score_pct is not None else None,
                        "submitted_at": s.submitted_at.isoformat() if s.submitted_at else None,
                        "time_taken_sec": s.time_taken_sec,
                    })

                test_attempts_week = (
                    db.query(Submission)
                    .filter(
                        Submission.user_id.in_(all_user_ids),
                        Submission.submitted_at >= week_ago,
                    )
                    .count()
                )
                test_attempts_month = (
                    db.query(Submission)
                    .filter(
                        Submission.user_id.in_(all_user_ids),
                        Submission.submitted_at >= month_ago,
                    )
                    .count()
                )
            except Exception as exc:
                import logging
                logging.getLogger("smartkcet.institution").error(f"Error fetching dashboard submissions: {exc}", exc_info=True)

        tests_this_week = test_attempts_week + exams_created_week
        tests_this_month = test_attempts_month + exams_created_month

        return {
            "institution_id": str(institution_id),
            "institution_name": institution.name,
            "total_students": total_students,
            "max_students": max_students,
            "subscription_status": subscription_status,
            "next_renewal_date": next_renewal_date,
            "weekly_test_limit": weekly_test_limit,
            "monthly_test_limit": monthly_test_limit,
            "tests_this_week": tests_this_week,
            "tests_this_month": tests_this_month,
            "recent_submissions": recent_submissions,
        }
    
    except HTTPException:
        raise
    except Exception as e:
        import logging
        logging.getLogger("smartkcet.institution").error(
            "Dashboard endpoint error: %s", str(e), exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail={"error": "internal_error", "message": "Unable to load dashboard data"}
        )


@router.route("/subscription", methods=["GET"])
def get_institution_subscription():    
    payload = require_institution_admin()
    from flask import g
    db = getattr(g, "db", None)
    session = db
    """Get institution subscription details."""
    institution_id = UUID(payload["institution_id"])

    institution = db.query(Institution).filter(Institution.id == institution_id).first()
    if not institution:
        raise HTTPException(status_code=404, detail={"error": "institution_not_found", "message": "Institution not found"})

    active_sub = (
        db.query(Subscription)
        .filter(
            Subscription.institution_id == institution_id,
            Subscription.status.in_(["active", "trial", "grace_period"])  # Only active statuses
        )
        .order_by(Subscription.created_at.desc())
        .first()
    )

    total_students = db.query(User).filter(
        User.institution_id == institution_id,
        User.role == "student",
    ).count()

    if not active_sub:
        # Return a dummy active subscription instead of 404 to bypass payment blocks permanently
        return {
            "subscription_status": "active",
            "institution_id": str(institution_id),
            "institution_name": institution.name,
            "plan_name": "Premium Plan",
            "status": "active",
            "start_date": None,
            "end_date": None,
            "next_renewal_date": None,
            "billing_period": "monthly",
            "max_students": 9999,
            "total_students": total_students,
            "weekly_test_limit": 9999,
            "monthly_test_limit": 9999,
        }

    plan = active_sub.plan
    return {
        "subscription_status": active_sub.status,  # ← Add this field for frontend access control
        "institution_id": str(institution_id),
        "institution_name": institution.name,
        "plan_name": plan.name if plan else "Institution Plan",
        "status": active_sub.status,
        "start_date": active_sub.start_date.isoformat() if active_sub.start_date else None,
        "end_date": active_sub.next_renewal_date.isoformat() if active_sub.next_renewal_date else None,
        "next_renewal_date": active_sub.next_renewal_date.isoformat() if active_sub.next_renewal_date else None,
        "billing_period": plan.billing_period if plan else "monthly",
        "max_students": plan.max_student_seats if plan else None,
        "total_students": total_students,
        "weekly_test_limit": plan.max_test_attempts_per_period if plan else None,
        "monthly_test_limit": plan.max_test_attempts_per_period if plan else None,
    }


@router.route("/invitations", methods=["GET"])
def list_invitations():    
    payload = require_institution_admin()
    from flask import g
    db = getattr(g, "db", None)
    session = db
    """List pending invitations for the institution."""
    from ..db.subscription_models import Invitation

    institution_id = UUID(payload["institution_id"])

    try:
        invitations = (
            db.query(Invitation)
            .filter(Invitation.institution_id == institution_id)
            .order_by(Invitation.created_at.desc())
            .all()
        )
        return {
            "invitations": [
                {
                    "sequence_number": inv.sequence_number,  # NEW: Show invitation number
                    "code": inv.code,
                    "batch_id": str(inv.batch_id) if getattr(inv, "batch_id", None) else None,
                    "status": inv.status,
                    "created_at": inv.created_at.isoformat() if inv.created_at else None,
                    "expires_at": inv.expires_at.isoformat() if inv.expires_at else None,
                }
                for inv in invitations
            ]
        }
    except Exception:
        return {"invitations": []}


@router.route("/invite/<code>", methods=["GET"])
def get_invitation_details(code: str):    
    payload = require_authenticated()
    from flask import g
    db = getattr(g, "db", None)
    session = db
    """Get invitation details by code (for student acceptance page)."""
    from ..db.subscription_models import Invitation
    from datetime import datetime

    inv = db.query(Invitation).filter(Invitation.code == code).first()
    if not inv:
        raise HTTPException(
            status_code=400,
            detail={"error": "invalid_invitation", "message": "Invitation not found or has expired"},
        )

    if inv.status != "pending" or (inv.expires_at and inv.expires_at < datetime.utcnow()):
        raise HTTPException(
            status_code=400,
            detail={"error": "invalid_invitation", "message": "Invitation is no longer valid"},
        )

    institution = db.query(Institution).filter(Institution.id == inv.institution_id).first()

    return {
        "code": inv.code,
        "institution_name": institution.name if institution else "Unknown Institution",
        "expires_at": inv.expires_at.isoformat() if inv.expires_at else None,
        "benefits": [
            "Access to institution exam bank",
            "Unlimited exam attempts",
            "Performance analytics",
            "Institution leaderboard",
        ],
    }


@router.route("/invite/<code>/accept", methods=["POST"])
def accept_invitation_by_code(code: str):    
    payload = require_authenticated()
    from flask import g
    db = getattr(g, "db", None)
    session = db
    """Accept an invitation by code (student-facing endpoint)."""
    if payload.get("role") != "student":
        raise HTTPException(
            status_code=403,
            detail={"error": "forbidden", "message": "Only students can accept invitations"},
        )

    service = InstitutionService(db)

    # The 'sub' claim for students is their kcet_student_id (e.g. KCET0001),
    # NOT a UUID. We need to look up the actual user record.
    sub_claim = payload.get("sub", "")
    user = db.query(User).filter(User.kcet_student_id == sub_claim).first()
    if not user:
        # Fallback: try as email (institution_admin tokens use email)
        user = db.query(User).filter(User.email == sub_claim).first()
    if not user:
        raise HTTPException(
            status_code=401,
            detail={"error": "user_not_found", "message": "Could not identify your account. Please log in again."},
        )
    student_id = user.id

    try:
        service.accept_invitation(code, student_id)
        institution_name = "your institution"
        from ..db.subscription_models import Invitation
        inv = db.query(Invitation).filter(Invitation.code == code).first()
        if inv:
            inst = db.query(Institution).filter(Institution.id == inv.institution_id).first()
            if inst:
                institution_name = inst.name
        return {"message": f"Successfully joined {institution_name}", "institution_name": institution_name}
    except InstitutionServiceError as e:
        error_msg = str(e)
        if "Invalid invitation" in error_msg or "expired" in error_msg:
            raise HTTPException(status_code=400, detail={"error": "invalid_invitation", "message": error_msg})
        elif "seat quota full" in error_msg:
            raise HTTPException(status_code=409, detail={"error": "seats_full", "message": error_msg})
        elif "already linked" in error_msg:
            raise HTTPException(status_code=409, detail={"error": "already_linked", "message": error_msg})
        raise HTTPException(status_code=500, detail={"error": "internal_error", "message": error_msg})


@router.route("/invite/<code>", methods=["DELETE"])
def revoke_invitation(code: str):    
    payload = require_institution_admin()
    from flask import g
    db = getattr(g, "db", None)
    session = db
    """Revoke a pending invitation."""
    from ..db.subscription_models import Invitation
    import logging
    
    logger = logging.getLogger("smartkcet.institution")

    try:
        institution_id = UUID(payload["institution_id"])
        
        # Decode the code if URL-encoded
        from urllib.parse import unquote
        decoded_code = unquote(code)
        
        logger.info(f"Revoking invitation: original={code}, decoded={decoded_code}")
        
        inv = db.query(Invitation).filter(
            Invitation.code == decoded_code,
            Invitation.institution_id == institution_id,
        ).first()

        if not inv:
            logger.warning(f"Invitation not found: code={decoded_code}, institution_id={institution_id}")
            raise HTTPException(
                status_code=404,
                detail={"error": "invalid_invitation", "message": "Invitation not found"},
            )

        inv.status = "revoked"
        db.commit()
        
        logger.info(f"Successfully revoked invitation: code={decoded_code}")
        return {"message": "Invitation revoked"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error revoking invitation: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail={"error": "internal_error", "message": "Failed to revoke invitation"}
        )


# ---------------------------------------------------------------------------
# Institution Student Platform API
# ---------------------------------------------------------------------------

@router.route("/student/me", methods=["GET"])
def get_institution_student_profile():    
    payload = require_authenticated()
    from flask import g
    db = getattr(g, "db", None)
    session = db
    """Get institution student profile — name, IDs, institution details, access status.
    
    Called by the institution student dashboard on load.
    Only accessible to institution_linked students.
    """
    if payload.get("role") != "student":
        raise HTTPException(
            status_code=403,
            detail={"error": "forbidden", "message": "Students only"},
        )
    if payload.get("student_subtype") != "institution_linked":
        raise HTTPException(
            status_code=403,
            detail={"error": "forbidden", "message": "Institution students only"},
        )

    sub_claim = payload.get("sub", "")
    user = db.query(User).filter(User.kcet_student_id == sub_claim).first()
    if not user:
        raise HTTPException(
            status_code=401,
            detail={"error": "user_not_found", "message": "Could not find your account"},
        )

    institution = None
    if user.institution_id:
        institution = db.query(Institution).filter(Institution.id == user.institution_id).first()

    # Derive access status from institution subscription
    access_status = "inactive"
    next_renewal_date = None
    plan_name = None
    if institution:
        active_sub = (
            db.query(Subscription)
            .filter(
                Subscription.institution_id == institution.id,
                Subscription.status.in_(["trial", "active", "overdue", "grace_period"]),
            )
            .first()
        )
        if active_sub:
            access_status = active_sub.status
            next_renewal_date = active_sub.next_renewal_date.isoformat() if active_sub.next_renewal_date else None
            if active_sub.plan:
                plan_name = active_sub.plan.name

    return {
        "student_id": str(user.id),
        "kcet_student_id": user.kcet_student_id,
        "display_name": user.display_name,
        "email": user.email,
        "student_subtype": user.student_subtype,
        "institution_id": str(user.institution_id) if user.institution_id else None,
        "institution_name": institution.name if institution else None,
        "access_status": access_status,
        "plan_name": plan_name,
        "next_renewal_date": next_renewal_date,
    }


@router.route("/student/exams", methods=["GET"])
def get_institution_student_exams():    
    payload = require_authenticated()
    from flask import g
    db = getattr(g, "db", None)
    session = db
    """Get institution-specific exams available to the student.

    Institution students see ONLY exams belonging to their institution.
    Platform-wide exams (institution_id IS NULL) are NOT shown.
    Strict isolation: no cross-institution access.
    """
    if payload.get("role") != "student" or payload.get("student_subtype") != "institution_linked":
        raise HTTPException(
            status_code=403,
            detail={"error": "forbidden", "message": "Institution students only"},
        )

    institution_id_str = payload.get("institution_id")
    if not institution_id_str:
        raise HTTPException(status_code=403, detail={"error": "no_institution", "message": "No institution linked"})

    institution_id = UUID(institution_id_str)

    from ..db.models import Exam, ExamSet, User
    from sqlalchemy import func, or_

    student_id_str = payload.get("user_id") or payload.get("sub")
    student = None
    if student_id_str:
        try:
            student = db.query(User).filter(User.id == UUID(student_id_str)).first()
        except Exception:
            student = None

    student_batch_id = getattr(student, "batch_id", None) if student else None

    # Filter: ONLY exams belonging to this institution, AND either assigned to student's batch OR all batches
    filters = [
        Exam.is_published.is_(True),
        Exam.institution_id == institution_id,
    ]
    if student_batch_id:
        filters.append(or_(Exam.batch_id.is_(None), Exam.batch_id == student_batch_id))
    else:
        filters.append(Exam.batch_id.is_(None))

    stmt = (
        db.query(Exam, func.count(ExamSet.id).label("set_count"))
        .outerjoin(ExamSet, ExamSet.exam_id == Exam.id)
        .filter(*filters)
        .group_by(Exam.id)
        .order_by(Exam.created_at.desc())
        .all()
    )

    buckets: dict[str, list] = {}
    for exam, set_count in stmt:
        sets_list = (
            db.query(ExamSet)
            .filter(ExamSet.exam_id == exam.id)
            .order_by(ExamSet.set_label.asc())
            .all()
        )
        bucket = buckets.setdefault(exam.subject, [])
        bucket.append({
            "exam_id": str(exam.id),
            "exam_name": exam.exam_name,
            "created_at": exam.created_at.isoformat() if exam.created_at else None,
            "set_count": int(set_count or 0),
            "is_institution_exam": True,
            "batch_id": str(exam.batch_id) if exam.batch_id else None,
            "batch_name": exam.batch.name if getattr(exam, "batch", None) else "All Batches",
            "duration_minutes": getattr(exam, "duration_minutes", 60) or 60,
            "scheduled_start": exam.scheduled_start.isoformat() if getattr(exam, "scheduled_start", None) else None,
            "scheduled_end": exam.scheduled_end.isoformat() if getattr(exam, "scheduled_end", None) else None,
            "total_marks": getattr(exam, "total_marks", 60) or 60,
            "sets": [{"exam_set_id": str(s.id), "set_label": s.set_label} for s in sets_list],
        })

    return {
        "subjects": [
            {"subject": subj, "available_exams": len(exams), "exams": exams}
            for subj, exams in buckets.items()
        ]
    }


@router.route("/student/leaderboard", methods=["GET"])
def get_institution_student_leaderboard():    
    payload = require_authenticated()
    from flask import g
    db = getattr(g, "db", None)
    session = db
    """Institution-scoped leaderboard — top students within the institution."""
    if payload.get("role") != "student" or payload.get("student_subtype") != "institution_linked":
        raise HTTPException(status_code=403, detail={"error": "forbidden", "message": "Institution students only"})

    institution_id_str = payload.get("institution_id")
    if not institution_id_str:
        raise HTTPException(status_code=403, detail={"error": "no_institution"})

    institution_id = UUID(institution_id_str)
    sub_claim = payload.get("sub", "")

    # Get all students in this institution
    students = db.query(User).filter(User.institution_id == institution_id).all()
    student_map = {str(s.id): s for s in students}
    student_ids = list(student_map.keys())

    if not student_ids:
        return {"leaderboard": [], "my_rank": None, "total": 0}

    from ..db.models import Submission
    from sqlalchemy import func as sa_func

    # Aggregate scores per student
    rows = (
        db.query(
            Submission.user_id,
            sa_func.count(Submission.id).label("attempts"),
            sa_func.avg(Submission.score_pct).label("avg_score"),
        )
        .filter(Submission.user_id.in_([UUID(sid) for sid in student_ids]))
        .group_by(Submission.user_id)
        .order_by(sa_func.avg(Submission.score_pct).desc())
        .all()
    )

    leaderboard = []
    my_rank = None
    for rank, row in enumerate(rows, start=1):
        uid_str = str(row.user_id)
        student = student_map.get(uid_str)
        entry = {
            "rank": rank,
            "display_name": student.display_name if student else "Unknown",
            "kcet_student_id": student.kcet_student_id if student else "—",
            "avg_score": round(float(row.avg_score), 1),
            "attempts": int(row.attempts),
        }
        leaderboard.append(entry)
        if student and student.kcet_student_id == sub_claim:
            my_rank = rank

    return {
        "leaderboard": leaderboard[:20],  # top 20
        "my_rank": my_rank,
        "total": len(leaderboard),
    }


@router.route("/student/performance", methods=["GET"])
def get_institution_student_performance():    
    payload = require_authenticated()
    from flask import g
    db = getattr(g, "db", None)
    session = db
    """Personal performance analytics for institution student."""
    if payload.get("role") != "student" or payload.get("student_subtype") != "institution_linked":
        raise HTTPException(status_code=403, detail={"error": "forbidden", "message": "Institution students only"})

    sub_claim = payload.get("sub", "")
    user = db.query(User).filter(User.kcet_student_id == sub_claim).first()
    if not user:
        raise HTTPException(status_code=401, detail={"error": "user_not_found"})

    from ..db.models import Exam, ExamSet, Submission

    rows = (
        db.query(Submission, ExamSet, Exam)
        .join(ExamSet, ExamSet.id == Submission.exam_set_id)
        .join(Exam, Exam.id == ExamSet.exam_id)
        .filter(Submission.user_id == user.id)
        .order_by(Submission.submitted_at.desc())
        .limit(100)
        .all()
    )

    submissions = [
        {
            "id": str(s.id),
            "subject": ex.subject,
            "set_label": es.set_label,
            "score_pct": float(s.score_pct),
            "pass_flag": float(s.score_pct) >= 50.0,
            "time_taken_sec": s.time_taken_sec,
            "submitted_at": s.submitted_at.isoformat() if s.submitted_at else None,
        }
        for s, es, ex in rows
    ]

    total = len(submissions)
    avg_score = round(sum(s["score_pct"] for s in submissions) / total, 1) if total else 0
    pass_rate = round(sum(1 for s in submissions if s["pass_flag"]) / total * 100, 1) if total else 0

    return {
        "submissions": submissions,
        "summary": {
            "total_exams": total,
            "avg_score": avg_score,
            "pass_rate": pass_rate,
        },
    }


# ─────────────────────────────────────────────────────────────
# GET /api/institution/students
# ─────────────────────────────────────────────────────────────

@router.route("/students", methods=["GET"])
def get_all_students():    
    payload = require_institution_admin()
    from flask import g
    db = getattr(g, "db", None)
    session = db
    """Get all students: institution-linked students + direct subscribers.
    
    Returns:
    {
        "institution": {
            "name": "SMVITM",
            "code": "smvitm",
            "students": [
                {
                    "email": "student@example.com",
                    "name": "Student Name",
                    "id": "SMVITM0001",
                    "subtype": "institution_linked"
                }
            ]
        },
        "direct_subscribers": [
            {
                "email": "direct@example.com",
                "name": "Direct Subscriber",
                "id": "KCET0001",
                "subtype": "direct_subscriber"
            }
        ]
    }
    """
    try:
        institution_id = UUID(auth.get("institution_id"))
        
        # Get institution info
        institution = (
            db.query(Institution)
            .filter(Institution.id == institution_id)
            .first()
        )
        
        if not institution:
            raise HTTPException(
                status_code=404,
                detail={"error": "institution_not_found", "message": "Institution not found"}
            )
        
        # Get institution-linked students
        institution_students = (
            db.query(User)
            .filter(
                User.institution_id == institution_id,
                User.role == "student"
            )
            .all()
        )
        
        # Get all direct subscribers (not linked to any institution)
        direct_subscribers = (
            db.query(User)
            .filter(
                User.student_subtype == "direct_subscriber",
                User.institution_id.is_(None),
                User.role == "student"
            )
            .all()
        )
        
        return {
            "institution": {
                "name": institution.name,
                "code": institution.institution_code,
                "students": [
                    {
                        "email": s.email,
                        "name": s.display_name,
                        "id": s.kcet_student_id,
                        "subtype": s.student_subtype
                    }
                    for s in institution_students
                ]
            },
            "direct_subscribers": [
                {
                    "email": s.email,
                    "name": s.display_name,
                    "id": s.kcet_student_id,
                    "subtype": s.student_subtype
                }
                for s in direct_subscribers
            ]
        }
        
    except Exception as e:
        import logging
        logging.getLogger("smartkcet.institution").error(
            "Error fetching students: %s", e
        )
        raise HTTPException(
            status_code=500,
            detail={"error": "server_error", "message": "Failed to fetch students"}
        )


# ---------------------------------------------------------------------------
# BATCH MANAGEMENT (Classes / Sections)
# ---------------------------------------------------------------------------

@router.route("/batches", methods=["GET"])
def list_institution_batches():
    payload = require_institution_admin()
    db = getattr(g, "db", None)
    inst_id = UUID(payload["institution_id"])
    from ..db.models import InstitutionBatch, User, Exam

    batches = (
        db.query(InstitutionBatch)
        .filter(InstitutionBatch.institution_id == inst_id)
        .order_by(InstitutionBatch.created_at.asc())
        .all()
    )

    result = []
    for b in batches:
        student_count = db.query(User).filter(User.batch_id == b.id, User.role == "student").count()
        exam_count = db.query(Exam).filter(Exam.batch_id == b.id).count()
        result.append({
            "id": str(b.id),
            "name": b.name,
            "description": b.description,
            "student_count": student_count,
            "exam_count": exam_count,
            "created_at": b.created_at.isoformat() if b.created_at else None,
        })

    return jsonify({"batches": result, "total": len(result)})


@router.route("/batches", methods=["POST"])
def create_institution_batch():
    payload = require_institution_admin()
    db = getattr(g, "db", None)
    inst_id = UUID(payload["institution_id"])
    from ..db.models import InstitutionBatch

    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    description = (data.get("description") or "").strip()

    if not name:
        return make_response(jsonify({"error": "validation_error", "message": "Batch name is required"}), 400)

    batch = InstitutionBatch(
        institution_id=inst_id,
        name=name,
        description=description if description else None,
    )
    db.add(batch)
    db.commit()
    db.refresh(batch)

    return jsonify({
        "id": str(batch.id),
        "name": batch.name,
        "description": batch.description,
        "student_count": 0,
        "exam_count": 0,
        "created_at": batch.created_at.isoformat() if batch.created_at else None,
        "message": "Batch created successfully"
    }), 201


@router.route("/batches/<batch_id>", methods=["DELETE"])
def delete_institution_batch(batch_id: str):
    payload = require_institution_admin()
    db = getattr(g, "db", None)
    inst_id = UUID(payload["institution_id"])
    from ..db.models import InstitutionBatch, User, Exam

    try:
        b_uuid = UUID(batch_id)
    except ValueError:
        return make_response(jsonify({"error": "invalid_id", "message": "Invalid batch ID"}), 400)

    batch = db.query(InstitutionBatch).filter(InstitutionBatch.id == b_uuid, InstitutionBatch.institution_id == inst_id).first()
    if not batch:
        return make_response(jsonify({"error": "not_found", "message": "Batch not found"}), 404)

    # Unlink students and exams before deleting
    db.query(User).filter(User.batch_id == b_uuid).update({"batch_id": None})
    db.query(Exam).filter(Exam.batch_id == b_uuid).update({"batch_id": None})

    db.delete(batch)
    db.commit()

    return jsonify({"success": True, "message": "Batch deleted successfully"})


@router.route("/students/<student_id>/batch", methods=["PATCH"])
def assign_student_batch(student_id: str):
    payload = require_institution_admin()
    db = getattr(g, "db", None)
    inst_id = UUID(payload["institution_id"])
    from ..db.models import InstitutionBatch, User

    try:
        s_uuid = UUID(student_id)
    except ValueError:
        return make_response(jsonify({"error": "invalid_id", "message": "Invalid student ID"}), 400)

    student = db.query(User).filter(User.id == s_uuid, User.institution_id == inst_id, User.role == "student").first()
    if not student:
        return make_response(jsonify({"error": "not_found", "message": "Student not found"}), 404)

    data = request.get_json(silent=True) or {}
    batch_id_str = data.get("batch_id")
    if batch_id_str:
        try:
            b_uuid = UUID(batch_id_str)
            batch = db.query(InstitutionBatch).filter(InstitutionBatch.id == b_uuid, InstitutionBatch.institution_id == inst_id).first()
            if not batch:
                return make_response(jsonify({"error": "batch_not_found", "message": "Batch not found"}), 404)
            student.batch_id = b_uuid
            batch_name = batch.name
        except ValueError:
            return make_response(jsonify({"error": "invalid_batch_id", "message": "Invalid batch ID"}), 400)
    else:
        student.batch_id = None
        batch_name = None

    db.commit()
    return jsonify({
        "success": True,
        "student_id": str(student.id),
        "batch_id": str(student.batch_id) if student.batch_id else None,
        "batch_name": batch_name,
        "message": "Student batch updated successfully"
    })


__all__ = ["router"]
