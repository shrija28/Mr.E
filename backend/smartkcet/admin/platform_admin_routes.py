"""Platform Admin API routes using Flask Blueprint.

Mounted under /api/admin/platform from smartkcet.admin.__init__.
"""

import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from flask import Blueprint, jsonify, request
from sqlalchemy import func, outerjoin
from sqlalchemy.orm import Session

from ..db.models import Exam, Question, User
from ..db.session import get_db
from ..db.subscription_models import Institution, Subscription, SubscriptionEvent, SubscriptionPlan
from ..middleware.rbac import require_platform_admin
from .platform_admin_service import PlatformAdminService

logger = logging.getLogger("smartkcet.admin.platform")

router = Blueprint("platform_admin", __name__, url_prefix="/api/admin/platform")


@router.route("/check-config", methods=["POST"])
def check_admin_config():
    db: Session = get_db()
    service = PlatformAdminService(db)
    is_configured = service.is_admin_configured()
    
    if is_configured:
        return jsonify({
            "success": True,
            "message": "Platform Admin is configured",
            "admin_configured": True,
        }), 200
    else:
        return jsonify({
            "success": False,
            "message": "Platform Admin is not configured.",
            "admin_configured": False,
        }), 200


@router.route("/subscription-plans", methods=["POST"])
@require_platform_admin
def create_subscription_plan():
    db: Session = get_db()
    data = request.get_json(silent=True) or {}
    service = PlatformAdminService(db)
    
    try:
        plan = service.create_subscription_plan(
            name=data.get("name"),
            plan_type=data.get("plan_type"),
            billing_period=data.get("billing_period"),
            price=Decimal(str(data.get("price", 0))),
            max_test_attempts_per_period=data.get("max_test_attempts_per_period"),
            max_student_seats=data.get("max_student_seats"),
            feature_flags=data.get("feature_flags"),
        )
        return jsonify({
            "id": str(plan.id),
            "name": plan.name,
            "plan_type": plan.plan_type,
            "billing_period": plan.billing_period,
            "price": float(plan.price),
            "max_test_attempts_per_period": plan.max_test_attempts_per_period,
            "max_student_seats": plan.max_student_seats,
            "feature_flags": plan.feature_flags,
            "is_active": plan.is_active,
        }), 201
    except ValueError as e:
        return jsonify({"error": "validation_error", "message": str(e)}), 400


@router.route("/subscription-plans/<plan_id>", methods=["GET"])
@require_platform_admin
def get_subscription_plan(plan_id: str):
    db: Session = get_db()
    try:
        pid = UUID(plan_id)
    except (ValueError, TypeError):
        return jsonify({"error": "validation_error", "message": "Invalid plan_id"}), 400

    service = PlatformAdminService(db)
    plan = service.get_subscription_plan(pid)
    
    if not plan:
        return jsonify({"error": "not_found", "message": f"Subscription plan {plan_id} not found"}), 404
    
    return jsonify({
        "id": str(plan.id),
        "name": plan.name,
        "plan_type": plan.plan_type,
        "billing_period": plan.billing_period,
        "price": float(plan.price),
        "max_test_attempts_per_period": plan.max_test_attempts_per_period,
        "max_student_seats": plan.max_student_seats,
        "feature_flags": plan.feature_flags,
        "is_active": plan.is_active,
    }), 200


@router.route("/subscription-plans", methods=["GET"])
@require_platform_admin
def list_subscription_plans():
    db: Session = get_db()
    plan_type = request.args.get("plan_type")
    raw_is_active = request.args.get("is_active")

    query = db.query(SubscriptionPlan)
    if plan_type is not None:
        query = query.filter(SubscriptionPlan.plan_type == plan_type)
    if raw_is_active is not None:
        query = query.filter(SubscriptionPlan.is_active == (raw_is_active.lower() == "true"))

    plans = query.all()

    if len(plans) == 0:
        default_plans = [
            {
                'name': 'Free',
                'plan_type': 'individual',
                'billing_period': 'monthly',
                'price': Decimal('0'),
                'max_test_attempts_per_period': 5,
                'max_student_seats': None,
                'feature_flags': {'mock_tests_5': True, 'practice_exams_3': True, 'ai_analytics': False, 'kcet_question_bank': False, 'leaderboard': False, 'performance_reports': 'Basic', 'ai_recommendations': False},
                'is_active': True,
            },
            {
                'name': '7-Day Premium Trial',
                'plan_type': 'individual',
                'billing_period': 'weekly',
                'price': Decimal('99'),
                'max_test_attempts_per_period': 999,
                'max_student_seats': None,
                'feature_flags': {'mock_tests_unlimited': True, 'practice_exams_unlimited': True, 'ai_analytics': True, 'kcet_question_bank': True, 'leaderboard': True, 'performance_reports': True, 'ai_recommendations': True},
                'is_active': True,
            },
            {
                'name': 'Pro Monthly',
                'plan_type': 'individual',
                'billing_period': 'monthly',
                'price': Decimal('349'),
                'max_test_attempts_per_period': 999,
                'max_student_seats': None,
                'feature_flags': {'mock_tests_unlimited': True, 'practice_exams_unlimited': True, 'ai_analytics': True, 'kcet_question_bank': True, 'leaderboard': True, 'performance_reports': 'Advanced', 'ai_recommendations': True},
                'is_active': True,
            },
            {
                'name': 'Pro Yearly',
                'plan_type': 'individual',
                'billing_period': 'monthly',
                'price': Decimal('2999'),
                'max_test_attempts_per_period': 999,
                'max_student_seats': None,
                'feature_flags': {'mock_tests_unlimited': True, 'practice_exams_unlimited': True, 'ai_analytics': True, 'kcet_question_bank': True, 'leaderboard': True, 'performance_reports': 'Advanced', 'ai_recommendations': True, 'priority_access': True},
                'is_active': True,
            },
            {
                'name': 'Starter',
                'plan_type': 'institution',
                'billing_period': 'monthly',
                'price': Decimal('1499'),
                'max_test_attempts_per_period': None,
                'max_student_seats': 50,
                'feature_flags': {'institution_uploads': True, 'institution_question_bank': False, 'chapter_tests': True, 'analytics': 'Basic', 'ai_analytics': False, 'performance_reports': 'Basic', 'branding': False, 'priority_support': False},
                'is_active': True,
            },
            {
                'name': 'Basic',
                'plan_type': 'institution',
                'billing_period': 'monthly',
                'price': Decimal('2999'),
                'max_test_attempts_per_period': None,
                'max_student_seats': 100,
                'feature_flags': {'institution_uploads': True, 'institution_question_bank': True, 'chapter_tests': True, 'analytics': 'Advanced', 'ai_analytics': False, 'performance_reports': 'Advanced', 'branding': False, 'priority_support': False},
                'is_active': True,
            },
            {
                'name': 'Premium',
                'plan_type': 'institution',
                'billing_period': 'monthly',
                'price': Decimal('7999'),
                'max_test_attempts_per_period': None,
                'max_student_seats': None,
                'feature_flags': {'institution_uploads': True, 'institution_question_bank': 'Full', 'chapter_tests': True, 'analytics': 'Advanced', 'ai_analytics': True, 'performance_reports': 'Advanced', 'branding': True, 'priority_support': True},
                'is_active': True,
            },
            {
                'name': 'Enterprise',
                'plan_type': 'institution',
                'billing_period': 'monthly',
                'price': Decimal('0'),
                'max_test_attempts_per_period': None,
                'max_student_seats': None,
                'feature_flags': {'institution_uploads': True, 'institution_question_bank': 'Full', 'chapter_tests': True, 'analytics': 'Advanced', 'ai_analytics': True, 'performance_reports': 'Custom', 'branding': True, 'priority_support': 'Dedicated Support'},
                'is_active': True,
            },
        ]
        for plan_data in default_plans:
            plan = SubscriptionPlan(
                name=plan_data['name'],
                plan_type=plan_data['plan_type'],
                billing_period=plan_data['billing_period'],
                price=plan_data['price'],
                max_test_attempts_per_period=plan_data['max_test_attempts_per_period'],
                max_student_seats=plan_data['max_student_seats'],
                feature_flags=plan_data['feature_flags'],
                is_active=plan_data['is_active'],
            )
            db.add(plan)
        db.commit()
        plans = db.query(SubscriptionPlan).all()

    res = [
        {
            "id": str(p.id),
            "name": p.name,
            "plan_type": p.plan_type,
            "billing_period": p.billing_period,
            "price": float(p.price),
            "max_test_attempts_per_period": p.max_test_attempts_per_period,
            "max_student_seats": p.max_student_seats,
            "feature_flags": p.feature_flags,
            "is_active": p.is_active,
        }
        for p in plans
    ]
    return jsonify(res), 200


@router.route("/subscription-plans/<plan_id>", methods=["PATCH"])
@require_platform_admin
def update_subscription_plan(plan_id: str):
    db: Session = get_db()
    try:
        pid = UUID(plan_id)
    except (ValueError, TypeError):
        return jsonify({"error": "validation_error", "message": "Invalid plan_id"}), 400

    data = request.get_json(silent=True) or {}
    service = PlatformAdminService(db)
    
    price_val = Decimal(str(data["price"])) if "price" in data and data["price"] is not None else None

    try:
        plan = service.update_subscription_plan(
            plan_id=pid,
            name=data.get("name"),
            price=price_val,
            max_test_attempts_per_period=data.get("max_test_attempts_per_period"),
            max_student_seats=data.get("max_student_seats"),
            feature_flags=data.get("feature_flags"),
            is_active=data.get("is_active"),
        )
        return jsonify({
            "id": str(plan.id),
            "name": plan.name,
            "plan_type": plan.plan_type,
            "billing_period": plan.billing_period,
            "price": float(plan.price),
            "max_test_attempts_per_period": plan.max_test_attempts_per_period,
            "max_student_seats": plan.max_student_seats,
            "feature_flags": plan.feature_flags,
            "is_active": plan.is_active,
        }), 200
    except ValueError as e:
        return jsonify({"error": "validation_error", "message": str(e)}), 400


@router.route("/subscription-plans/<plan_id>", methods=["DELETE"])
@require_platform_admin
def delete_subscription_plan(plan_id: str):
    db: Session = get_db()
    try:
        pid = UUID(plan_id)
    except (ValueError, TypeError):
        return jsonify({"error": "validation_error", "message": "Invalid plan_id"}), 400

    service = PlatformAdminService(db)
    try:
        service.delete_subscription_plan(pid)
        return jsonify({"success": True, "message": f"Subscription plan {plan_id} deleted successfully"}), 200
    except ValueError as e:
        return jsonify({"error": "validation_error", "message": str(e)}), 400


@router.route("/institutions/<institution_id>/activate", methods=["POST"])
@require_platform_admin
def activate_institution(institution_id: str):
    db: Session = get_db()
    try:
        iid = UUID(institution_id)
    except (ValueError, TypeError):
        return jsonify({"error": "validation_error", "message": "Invalid institution_id"}), 400

    service = PlatformAdminService(db)
    try:
        institution = service.activate_institution(iid)
        return jsonify({
            "id": str(institution.id),
            "name": institution.name,
            "institution_code": institution.institution_code,
            "subscription_status": institution.subscription_status,
        }), 200
    except ValueError as e:
        return jsonify({"error": "not_found", "message": str(e)}), 404


@router.route("/institutions/<institution_id>/suspend", methods=["POST"])
@require_platform_admin
def suspend_institution(institution_id: str):
    db: Session = get_db()
    try:
        iid = UUID(institution_id)
    except (ValueError, TypeError):
        return jsonify({"error": "validation_error", "message": "Invalid institution_id"}), 400

    service = PlatformAdminService(db)
    try:
        institution = service.suspend_institution(iid)
        return jsonify({
            "id": str(institution.id),
            "name": institution.name,
            "institution_code": institution.institution_code,
            "subscription_status": institution.subscription_status,
        }), 200
    except ValueError as e:
        return jsonify({"error": "not_found", "message": str(e)}), 404


@router.route("/institutions/<institution_id>", methods=["DELETE"])
@require_platform_admin
def remove_institution(institution_id: str):
    db: Session = get_db()
    try:
        iid = UUID(institution_id)
    except (ValueError, TypeError):
        return jsonify({"error": "validation_error", "message": "Invalid institution_id"}), 400

    service = PlatformAdminService(db)
    try:
        service.remove_institution(iid)
        return jsonify({"success": True, "message": f"Institution {institution_id} removed successfully"}), 200
    except ValueError as e:
        return jsonify({"error": "not_found", "message": str(e)}), 404


@router.route("/institutions", methods=["GET"])
@require_platform_admin
def list_institutions():
    db: Session = get_db()
    subscription_status = request.args.get("subscription_status")

    query = db.query(Institution)
    if subscription_status is not None:
        query = query.filter(Institution.subscription_status == subscription_status)
    
    institutions = query.all()
    inst_responses = []

    for inst in institutions:
        subscription = (
            db.query(Subscription)
            .filter(Subscription.institution_id == inst.id)
            .first()
        )
        plan_name = None
        if subscription and subscription.plan_id:
            plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.id == subscription.plan_id).first()
            if plan:
                plan_name = plan.name
        
        student_count = db.query(func.count(User.id)).filter(User.institution_id == inst.id, User.role == 'student').scalar() or 0
        question_count = db.query(func.count(Question.id)).filter(Question.institution_id == inst.id).scalar() or 0
        exam_count = db.query(func.count(Exam.id)).filter(Exam.institution_id == inst.id).scalar() or 0
        
        inst_responses.append({
            "id": str(inst.id),
            "name": inst.name,
            "institution_code": inst.institution_code,
            "contact_phone": inst.contact_phone,
            "subscription_status": inst.subscription_status,
            "registered_at": inst.registered_at.isoformat() if inst.registered_at else None,
            "student_count": int(student_count),
            "question_count": int(question_count),
            "exam_count": int(exam_count),
            "plan_name": plan_name,
            "next_renewal_date": subscription.next_renewal_date.isoformat() if subscription and subscription.next_renewal_date else None,
        })
    
    return jsonify({
        "institutions": inst_responses,
        "total": len(inst_responses),
    }), 200


@router.route("/students", methods=["GET"])
@require_platform_admin
def list_students():
    db: Session = get_db()
    student_type = request.args.get("student_type")
    raw_inst_id = request.args.get("institution_id")

    inst_id: Optional[UUID] = None
    if raw_inst_id:
        try:
            inst_id = UUID(raw_inst_id)
        except (ValueError, TypeError):
            pass

    query = db.query(User).filter(User.role == 'student')

    if student_type == 'direct':
        query = query.filter(User.student_subtype.in_(['direct_subscriber', 'dual']))
    elif student_type == 'institution':
        query = query.filter(User.student_subtype.in_(['institution_linked', 'dual']))
        if inst_id:
            query = query.filter(User.institution_id == inst_id)
    elif inst_id:
        query = query.filter(User.institution_id == inst_id)

    students = query.all()
    students_data = []

    for user in students:
        subscription = (
            db.query(Subscription)
            .filter(User.id == user.id, Subscription.status.in_(["trial", "active", "overdue", "grace_period"]))
            .first()
        )
        institution_name = None
        if user.institution_id:
            institution = db.query(Institution).filter(Institution.id == user.institution_id).first()
            institution_name = institution.name if institution else None

        students_data.append({
            "id": str(user.id),
            "kcet_student_id": user.kcet_student_id,
            "name": user.display_name,
            "email": user.email,
            "student_subtype": user.student_subtype or "unknown",
            "institution_id": str(user.institution_id) if user.institution_id else None,
            "institution_name": institution_name,
            "subscription_status": subscription.status if subscription else "no_subscription",
            "has_active_subscription": subscription is not None,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        })

    return jsonify({
        "count": len(students_data),
        "students": students_data,
    }), 200


@router.route("/seed/students", methods=["POST"])
@require_platform_admin
def seed_test_students():
    db: Session = get_db()
    data = request.get_json(silent=True) or {}
    direct_count = int(data.get("direct_count", 5))
    institution_count = int(data.get("institution_count", 3))
    students_per_institution = int(data.get("students_per_institution", 5))

    try:
        from ..db.seed_students import seed_students
        result = seed_students(
            session=db,
            direct_subscriber_count=direct_count,
            institution_count=institution_count,
            institution_student_count=students_per_institution,
        )
        return jsonify(result), 200
    except Exception as e:
        db.rollback()
        logger.error(f"Error seeding students: {e}", exc_info=True)
        return jsonify({"error": "seed_failed", "message": str(e)}), 500


@router.route("/direct-subscriptions", methods=["GET"])
@require_platform_admin
def list_direct_subscriptions():
    db: Session = get_db()
    subscription_status = request.args.get("subscription_status")

    query = db.query(
        User.id,
        User.display_name,
        User.email,
        User.kcet_student_id,
        Subscription.id.label('subscription_id'),
        Subscription.status,
        Subscription.start_date,
        Subscription.current_period_start,
        Subscription.next_renewal_date,
        SubscriptionPlan.name.label('plan_name'),
        SubscriptionPlan.price,
    ).outerjoin(
        Subscription, Subscription.user_id == User.id
    ).outerjoin(
        SubscriptionPlan, SubscriptionPlan.id == Subscription.plan_id
    ).filter(
        User.role == 'student',
        User.student_subtype.in_(['direct_subscriber', 'dual']),
    )

    if subscription_status:
        query = query.filter(Subscription.status == subscription_status)
    else:
        query = query.filter(
            (Subscription.status.in_(['trial', 'active', 'overdue', 'grace_period'])) |
            (Subscription.id.is_(None))
        )

    results = query.all()
    subscriptions_data = []

    for row in results:
        subscriptions_data.append({
            "id": str(row.subscription_id) if row.subscription_id else None,
            "user_id": str(row.id),
            "student_name": row.display_name,
            "email": row.email,
            "kcet_student_id": row.kcet_student_id,
            "plan_name": row.plan_name or "—",
            "status": row.status or "no_subscription",
            "start_date": row.start_date.isoformat() if row.start_date else None,
            "current_period_start": row.current_period_start.isoformat() if row.current_period_start else None,
            "next_renewal_date": row.next_renewal_date.isoformat() if row.next_renewal_date else None,
            "price": float(row.price) if row.price else None,
        })

    return jsonify({
        "count": len(subscriptions_data),
        "subscriptions": subscriptions_data,
    }), 200


@router.route("/analytics", methods=["GET"])
@require_platform_admin
def get_aggregate_analytics():
    db: Session = get_db()
    service = PlatformAdminService(db)
    analytics = service.get_aggregate_analytics()
    return jsonify(analytics), 200


@router.route("/subscriptions/<subscription_id>/renew", methods=["POST"])
@require_platform_admin
def renew_subscription(subscription_id: str):
    db: Session = get_db()
    try:
        sid = UUID(subscription_id)
    except (ValueError, TypeError):
        return jsonify({"error": "validation_error", "message": "Invalid subscription_id"}), 400

    subscription = db.query(Subscription).filter(Subscription.id == sid).first()
    if not subscription:
        return jsonify({"error": "not_found", "message": f"Subscription {subscription_id} not found"}), 404

    if subscription.status == 'cancelled':
        return jsonify({"error": "invalid_operation", "message": "Cannot renew a cancelled subscription"}), 400

    try:
        if subscription.next_renewal_date:
            if 'monthly' in (subscription.plan.billing_period.lower() if subscription.plan else 'monthly'):
                subscription.next_renewal_date = subscription.next_renewal_date + timedelta(days=30)
            else:
                subscription.next_renewal_date = subscription.next_renewal_date + timedelta(days=7)
        subscription.status = 'active'
        subscription.updated_at = datetime.utcnow()
        db.commit()

        return jsonify({
            "success": True,
            "message": f"Subscription renewed successfully until {subscription.next_renewal_date.isoformat()}",
            "subscription_id": str(subscription.id),
            "next_renewal_date": subscription.next_renewal_date.isoformat(),
        }), 200
    except Exception as e:
        db.rollback()
        return jsonify({"error": "renewal_failed", "message": str(e)}), 500


@router.route("/subscriptions/<subscription_id>/cancel", methods=["POST"])
@require_platform_admin
def cancel_subscription(subscription_id: str):
    db: Session = get_db()
    try:
        sid = UUID(subscription_id)
    except (ValueError, TypeError):
        return jsonify({"error": "validation_error", "message": "Invalid subscription_id"}), 400

    subscription = db.query(Subscription).filter(Subscription.id == sid).first()
    if not subscription:
        return jsonify({"error": "not_found", "message": f"Subscription {subscription_id} not found"}), 404

    if subscription.status == 'cancelled':
        return jsonify({"error": "invalid_operation", "message": "Subscription is already cancelled"}), 400

    try:
        subscription.status = 'cancelled'
        subscription.cancellation_date = datetime.utcnow()
        subscription.updated_at = datetime.utcnow()
        db.commit()

        return jsonify({
            "success": True,
            "message": "Subscription cancelled successfully",
            "subscription_id": str(subscription.id),
            "cancellation_date": subscription.cancellation_date.isoformat(),
        }), 200
    except Exception as e:
        db.rollback()
        return jsonify({"error": "cancellation_failed", "message": str(e)}), 500


@router.route("/students/<user_id>/subscription/manage", methods=["POST"])
@require_platform_admin
def manage_student_subscription(user_id: str):
    db: Session = get_db()
    try:
        uid = UUID(user_id)
    except (ValueError, TypeError):
        return jsonify({"error": "validation_error", "message": "Invalid user_id"}), 400

    data = request.get_json(silent=True) or {}
    action = data.get("action")
    plan_id_raw = data.get("plan_id")

    plan_id: Optional[UUID] = None
    if plan_id_raw:
        try:
            plan_id = UUID(str(plan_id_raw))
        except (ValueError, TypeError):
            pass

    user = db.query(User).filter(User.id == uid, User.role == 'student').first()
    if not user:
        return jsonify({"error": "not_found", "message": f"Student {user_id} not found"}), 404

    try:
        now = datetime.utcnow()
        active_subs = db.query(Subscription).filter(
            Subscription.user_id == user.id,
            Subscription.status.in_(["trial", "active", "overdue", "grace_period"])
        ).all()

        if action in ("remove", "cancel") or not plan_id:
            if not active_subs:
                return jsonify({
                    "success": True,
                    "message": "Student already has no active subscription",
                    "user_id": str(user.id),
                    "subscription_status": "cancelled",
                }), 200

            for sub in active_subs:
                prev_status = sub.status
                sub.status = "cancelled"
                sub.cancellation_date = now
                sub.updated_at = now

                event = SubscriptionEvent(
                    subscription_id=sub.id,
                    event_type="cancelled",
                    previous_status=prev_status,
                    new_status="cancelled",
                    event_metadata={"admin_action": "remove_subscription", "timestamp": now.isoformat()}
                )
                db.add(event)

            db.commit()
            return jsonify({
                "success": True,
                "message": "Subscription removed successfully. Student status set to INACTIVE.",
                "user_id": str(user.id),
                "subscription_status": "cancelled",
            }), 200

        plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.id == plan_id).first()
        if not plan:
            return jsonify({"error": "not_found", "message": f"Plan {plan_id} not found"}), 404

        months = int(data.get("duration_months", 1) or 1)
        start_from = now
        renew_from_str = data.get("renew_from")
        if renew_from_str:
            try:
                start_from = datetime.fromisoformat(renew_from_str)
            except Exception:
                start_from = now

        next_renewal = start_from + timedelta(days=30 * months)

        if active_subs:
            sub = active_subs[0]
            prev_status = sub.status
            sub.plan_id = plan.id
            sub.status = "active"
            sub.current_period_start = start_from
            sub.next_renewal_date = next_renewal
            sub.updated_at = now

            event = SubscriptionEvent(
                subscription_id=sub.id,
                event_type="upgraded",
                previous_status=prev_status,
                new_status="active",
                event_metadata={"admin_action": "update_subscription", "plan_name": plan.name, "timestamp": now.isoformat()}
            )
            db.add(event)
        else:
            sub = Subscription(
                user_id=user.id,
                plan_id=plan.id,
                status="active",
                start_date=start_from,
                current_period_start=start_from,
                next_renewal_date=next_renewal,
                created_at=now,
                updated_at=now,
            )
            db.add(sub)
            db.flush()

            event = SubscriptionEvent(
                subscription_id=sub.id,
                event_type="activated",
                previous_status="none",
                new_status="active",
                event_metadata={"admin_action": "create_subscription", "plan_name": plan.name, "timestamp": now.isoformat()}
            )
            db.add(event)

        db.commit()
        return jsonify({
            "success": True,
            "message": f"Subscription updated to {plan.name} until {next_renewal.strftime('%d %b %Y')}",
            "user_id": str(user.id),
            "subscription_id": str(sub.id),
            "plan_name": plan.name,
            "subscription_status": "active",
        }), 200
    except Exception as e:
        db.rollback()
        logger.error(f"Error managing student subscription: {e}", exc_info=True)
        return jsonify({"error": "manage_failed", "message": str(e)}), 500


@router.route("/students/<user_id>/reset-password", methods=["POST"])
@require_platform_admin
def reset_student_password(user_id: str):
    db: Session = get_db()
    try:
        uid = UUID(user_id)
    except (ValueError, TypeError):
        return jsonify({"error": "validation_error", "message": "Invalid user_id"}), 400

    data = request.get_json(silent=True) or {}
    new_password = data.get("password")

    from ..db.models import User
    from ..auth.passwords import hash_password

    try:
        user = db.query(User).filter(
            User.id == uid,
            User.role == 'student',
            User.student_subtype.in_(['direct_subscriber', 'dual'])
        ).first()

        if not user:
            return jsonify({"error": "not_found", "message": "Student not found or is not a direct subscriber"}), 404

        if not new_password or len(new_password) < 8:
            return jsonify({"error": "validation_error", "message": "Password must be at least 8 characters"}), 400

        user.password_hash = hash_password(new_password)
        user.updated_at = datetime.utcnow()
        db.commit()

        return jsonify({
            "success": True,
            "message": "Password reset successfully",
            "user_id": str(user.id),
            "email": user.email,
        }), 200
    except Exception as e:
        db.rollback()
        logger.error(f"Error resetting password: {e}", exc_info=True)
        return jsonify({"error": "reset_failed", "message": str(e)}), 500


__all__ = ["router"]
