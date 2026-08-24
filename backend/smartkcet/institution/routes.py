"""Flask routes for institution management.

Mounted under /api/institution from smartkcet.main.
"""

from datetime import datetime, timedelta
import logging
from typing import Any
from uuid import UUID

from flask import Blueprint, jsonify, request
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from ..db.models import Exam, ExamSet, Submission, User
from ..db.session import get_db
from ..db.subscription_models import Institution, Subscription, SubscriptionPlan
from ..middleware.rbac import current_user, require_authenticated, require_institution_admin
from .service import (
    DatabaseUnavailableError,
    DuplicateEmailError,
    InstitutionService,
    InstitutionServiceError,
    ValidationError,
)

logger = logging.getLogger("smartkcet.institution.routes")

router = Blueprint("institution", __name__, url_prefix="/api/institution")


@router.route("/register", methods=["POST"])
def register_institution():
    db: Session = get_db()
    data = request.get_json(silent=True) or {}
    name = data.get("name")
    admin_email = data.get("admin_email")
    admin_password = data.get("admin_password")
    admin_display_name = data.get("admin_display_name")
    institution_code = data.get("institution_code")

    service = InstitutionService(db)
    try:
        institution, admin_user = service.register_institution(
            name=name,
            admin_email=admin_email,
            admin_password=admin_password,
            admin_display_name=admin_display_name,
            institution_code=institution_code,
        )
        return jsonify({
            "institution_id": str(institution.id),
            "name": institution.name,
            "institution_code": institution.institution_code,
            "admin_user_id": str(admin_user.id),
            "admin_email": admin_user.email,
            "created_at": institution.created_at.isoformat() if institution.created_at else None,
        }), 201
    except ValidationError as e:
        return jsonify({"error": "validation_error", "message": str(e)}), 400
    except DuplicateEmailError as e:
        return jsonify({"error": "email_already_registered", "message": str(e)}), 409
    except DatabaseUnavailableError as e:
        db.rollback()
        return jsonify({"error": "service_unavailable", "message": str(e)}), 503
    except Exception as e:
        db.rollback()
        logger.error("Institution registration error: %s", e)
        return jsonify({"error": "registration_failed", "message": str(e)}), 500


@router.route("/invitations", methods=["POST"])
@require_institution_admin
def create_invitations():
    db: Session = get_db()
    user = getattr(request, "token_payload", {}) or {}
    inst_id_str = user.get("institution_id")
    if not inst_id_str:
        return jsonify({"error": "forbidden", "message": "Institution ID not found"}), 403

    try:
        institution_id = UUID(inst_id_str)
    except (ValueError, TypeError):
        return jsonify({"error": "validation_error", "message": "Invalid institution_id"}), 400

    data = request.get_json(silent=True) or {}
    count = data.get("count", 1)
    expires_in_days = data.get("expires_in_days", 7)

    service = InstitutionService(db)
    try:
        invitations = service.create_invitations(
            institution_id=institution_id,
            count=count,
            expires_in_days=expires_in_days,
        )

        institution = db.query(Institution).filter(Institution.id == institution_id).first()
        base_url = request.host_url.rstrip("/")

        invite_responses = []
        for inv in invitations:
            invite_link = f"{base_url}/html/student-register.html?invite={inv.code}"
            invite_responses.append({
                "id": str(inv.id),
                "code": inv.code,
                "invite_link": invite_link,
                "status": inv.status,
                "created_at": inv.created_at.isoformat() if inv.created_at else None,
                "expires_at": inv.expires_at.isoformat() if inv.expires_at else None,
            })

        return jsonify({
            "institution_id": str(institution_id),
            "count": len(invitations),
            "invitations": invite_responses,
        }), 201
    except ValidationError as e:
        return jsonify({"error": "validation_error", "message": str(e)}), 400
    except DatabaseUnavailableError as e:
        db.rollback()
        return jsonify({"error": "service_unavailable", "message": str(e)}), 503


@router.route("/invitations/<invitation_code>", methods=["GET"])
def get_invitation_details(invitation_code: str):
    db: Session = get_db()
    service = InstitutionService(db)
    try:
        invitation, institution = service.get_invitation_details(invitation_code)
        return jsonify({
            "code": invitation.code,
            "institution_name": institution.name,
            "status": invitation.status,
            "expires_at": invitation.expires_at.isoformat() if invitation.expires_at else None,
            "is_valid": invitation.status == "pending" and (invitation.expires_at is None or invitation.expires_at > datetime.utcnow()),
        }), 200
    except ValidationError as e:
        return jsonify({"error": "invalid_invitation", "message": str(e)}), 404
    except DatabaseUnavailableError as e:
        db.rollback()
        return jsonify({"error": "service_unavailable", "message": str(e)}), 503


@router.route("/accept-invitation", methods=["POST"])
@require_authenticated
def accept_invitation():
    db: Session = get_db()
    current_u = current_user(request, db)
    if not current_u:
        return jsonify({"error": "auth_required", "message": "User not found"}), 401

    data = request.get_json(silent=True) or {}
    invitation_code = data.get("invitation_code")
    if not invitation_code:
        return jsonify({"error": "validation_error", "message": "invitation_code required"}), 400

    service = InstitutionService(db)
    try:
        invitation = service.accept_invitation(invitation_code=invitation_code, user_id=current_u.id)
        institution = db.query(Institution).filter(Institution.id == invitation.institution_id).first()
        return jsonify({
            "success": True,
            "message": f"Successfully joined {institution.name if institution else 'institution'}",
            "institution_id": str(invitation.institution_id),
            "institution_name": institution.name if institution else None,
        }), 200
    except ValidationError as e:
        return jsonify({"error": "validation_error", "message": str(e)}), 400
    except DatabaseUnavailableError as e:
        db.rollback()
        return jsonify({"error": "service_unavailable", "message": str(e)}), 503


@router.route("/students", methods=["GET"])
@require_institution_admin
def get_institution_students():
    db: Session = get_db()
    user = getattr(request, "token_payload", {}) or {}
    inst_id_str = user.get("institution_id")
    if not inst_id_str:
        return jsonify({"error": "forbidden", "message": "Institution ID not found"}), 403

    try:
        institution_id = UUID(inst_id_str)
    except (ValueError, TypeError):
        return jsonify({"error": "validation_error", "message": "Invalid institution_id"}), 400

    raw_page = request.args.get("page", 1)
    raw_page_size = request.args.get("page_size", 50)
    try:
        page = max(1, int(raw_page))
        page_size = min(max(1, int(raw_page_size)), 100)
    except (ValueError, TypeError):
        page, page_size = 1, 50

    service = InstitutionService(db)
    try:
        students, total_count = service.get_institution_students(
            institution_id=institution_id,
            page=page,
            page_size=page_size,
        )

        student_responses = []
        for student in students:
            student_responses.append({
                "id": str(student.id),
                "email": student.email,
                "display_name": student.display_name,
                "kcet_student_id": student.kcet_student_id,
                "joined_at": student.created_at.isoformat() if student.created_at else None,
            })

        return jsonify({
            "institution_id": str(institution_id),
            "students": student_responses,
            "total_count": total_count,
            "page": page,
            "page_size": page_size,
            "total_pages": (total_count + page_size - 1) // page_size if page_size > 0 else 0,
        }), 200
    except DatabaseUnavailableError as e:
        db.rollback()
        return jsonify({"error": "service_unavailable", "message": str(e)}), 503


@router.route("/students/<student_id>", methods=["DELETE"])
@require_institution_admin
def remove_student(student_id: str):
    db: Session = get_db()
    user = getattr(request, "token_payload", {}) or {}
    inst_id_str = user.get("institution_id")
    if not inst_id_str:
        return jsonify({"error": "forbidden", "message": "Institution ID not found"}), 403

    try:
        institution_id = UUID(inst_id_str)
        target_student_id = UUID(student_id)
    except (ValueError, TypeError):
        return jsonify({"error": "validation_error", "message": "Invalid UUID format"}), 400

    service = InstitutionService(db)
    try:
        service.remove_student(institution_id=institution_id, student_id=target_student_id)
        return jsonify({
            "success": True,
            "message": "Student successfully unlinked from institution",
            "student_id": str(target_student_id),
        }), 200
    except ValidationError as e:
        return jsonify({"error": "validation_error", "message": str(e)}), 400
    except DatabaseUnavailableError as e:
        db.rollback()
        return jsonify({"error": "service_unavailable", "message": str(e)}), 503


@router.route("/select-plan", methods=["POST"])
@require_institution_admin
def select_institution_plan():
    db: Session = get_db()
    user = getattr(request, "token_payload", {}) or {}
    inst_id_str = user.get("institution_id")
    if not inst_id_str:
        return jsonify({"error": "forbidden", "message": "Institution ID not found"}), 403

    try:
        institution_id = UUID(inst_id_str)
    except (ValueError, TypeError):
        return jsonify({"error": "validation_error", "message": "Invalid institution_id"}), 400

    data = request.get_json(silent=True) or {}
    plan_id_str = data.get("plan_id")
    if not plan_id_str:
        return jsonify({"error": "validation_error", "message": "plan_id required"}), 400

    try:
        plan_id = UUID(plan_id_str)
    except (ValueError, TypeError):
        return jsonify({"error": "validation_error", "message": "Invalid plan_id format"}), 400

    service = InstitutionService(db)
    try:
        subscription = service.select_institution_plan(institution_id=institution_id, plan_id=plan_id)
        from ..subscription.models import SubscriptionResponse
        resp = SubscriptionResponse.model_validate(subscription)
        return jsonify(resp.model_dump(mode="json")), 201
    except ValidationError as e:
        return jsonify({"error": "validation_error", "message": str(e)}), 400
    except DatabaseUnavailableError as e:
        db.rollback()
        return jsonify({"error": "service_unavailable", "message": str(e)}), 503


@router.route("/dashboard", methods=["GET"])
@require_institution_admin
def get_institution_dashboard():
    db: Session = get_db()
    user = getattr(request, "token_payload", {}) or {}
    inst_id_str = user.get("institution_id")
    if not inst_id_str:
        return jsonify({"error": "forbidden", "message": "Institution ID not found"}), 403

    try:
        institution_id = UUID(inst_id_str)
    except (ValueError, TypeError):
        return jsonify({"error": "validation_error", "message": "Invalid institution_id"}), 400

    institution = db.query(Institution).filter(Institution.id == institution_id).first()
    if not institution:
        return jsonify({"error": "not_found", "message": "Institution not found"}), 404

    try:
        total_students = db.query(User).filter(
            User.institution_id == institution_id,
            User.role == "student",
        ).count()

        active_sub = (
            db.query(Subscription)
            .filter(
                Subscription.institution_id == institution_id,
                Subscription.status.in_(["trial", "active", "overdue", "grace_period"]),
            )
            .first()
        )

        subscription_status = active_sub.status if active_sub else "no_subscription"
        max_students = None
        weekly_test_limit = None
        monthly_test_limit = None
        next_renewal_date = None

        if active_sub and active_sub.plan:
            max_students = active_sub.plan.max_student_seats
            weekly_test_limit = active_sub.plan.max_test_attempts_per_period
            monthly_test_limit = active_sub.plan.max_test_attempts_per_period
            next_renewal_date = active_sub.next_renewal_date.isoformat() if active_sub.next_renewal_date else None

        all_user_ids = [
            row[0] for row in db.query(User.id).filter(User.institution_id == institution_id).all()
        ]

        recent_submissions = []
        now = datetime.utcnow()
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)

        exams_created_week = db.query(Exam).filter(
            Exam.institution_id == institution_id,
            Exam.created_at >= week_ago
        ).count()

        exams_created_month = db.query(Exam).filter(
            Exam.institution_id == institution_id,
            Exam.created_at >= month_ago
        ).count()

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
                logger.error("Error fetching dashboard submissions: %s", exc)

        tests_this_week = test_attempts_week + exams_created_week
        tests_this_month = test_attempts_month + exams_created_month

        return jsonify({
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
        }), 200
    except Exception as e:
        logger.error("Error generating institution dashboard: %s", e)
        return jsonify({"error": "dashboard_error", "message": str(e)}), 500


@router.route("/subscription", methods=["GET"])
@require_institution_admin
def get_institution_subscription():
    db: Session = get_db()
    user = getattr(request, "token_payload", {}) or {}
    inst_id_str = user.get("institution_id")
    if not inst_id_str:
        return jsonify({"error": "forbidden", "message": "Institution ID not found"}), 403

    try:
        institution_id = UUID(inst_id_str)
    except (ValueError, TypeError):
        return jsonify({"error": "validation_error", "message": "Invalid institution_id"}), 400

    active_sub = (
        db.query(Subscription)
        .filter(
            Subscription.institution_id == institution_id,
            Subscription.status.in_(["trial", "active", "overdue", "grace_period"]),
        )
        .first()
    )

    if not active_sub:
        return jsonify({
            "has_subscription": False,
            "status": "no_subscription",
            "message": "No active institution subscription found.",
        }), 200

    plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.id == active_sub.plan_id).first()

    return jsonify({
        "has_subscription": True,
        "subscription_id": str(active_sub.id),
        "status": active_sub.status,
        "plan_name": plan.name if plan else None,
        "plan_type": plan.plan_type if plan else None,
        "max_student_seats": plan.max_student_seats if plan else None,
        "max_test_attempts_per_period": plan.max_test_attempts_per_period if plan else None,
        "start_date": active_sub.start_date.isoformat() if active_sub.start_date else None,
        "next_renewal_date": active_sub.next_renewal_date.isoformat() if active_sub.next_renewal_date else None,
    }), 200


__all__ = ["router"]
