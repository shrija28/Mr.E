import os
"""Platform Admin API routes.

This module defines FastAPI routes for Platform Admin operations including:
- Admin authentication
- Subscription plan CRUD
- Institution management
- Aggregate analytics
"""

import logging
from datetime import datetime
from typing import List, Optional
from uuid import UUID

import os
from flask import Blueprint, request, g, make_response, jsonify, Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..db.session import get_async_session as get_session
from ..middleware.rbac import require_platform_admin
from .platform_admin_models import (
    AdminLoginRequest,
    AdminLoginResponse,
    AggregateAnalyticsResponse,
    CreateSubscriptionPlanRequest,
    InstitutionListResponse,
    InstitutionResponse,
    SubscriptionPlanResponse,
    SuccessResponse,
    UpdateSubscriptionPlanRequest,
)
from .platform_admin_service import PlatformAdminService

logger = logging.getLogger(__name__)

router = Blueprint("admin_platform_admin_routes", __name__)


# -----------------------------------------------------------------------------
# Admin Authentication
# -----------------------------------------------------------------------------


@router.route("/check-config", methods=["POST"])
def check_admin_config()-> AdminLoginResponse:    
    from flask import g
    db = getattr(g, "db", None)
    session = db
    
    from flask import g
    db = getattr(g, "db", None)
    session = db
    """Check if Platform Admin is configured.
    
    This endpoint checks if ADMIN_EMAIL and ADMIN_PASSWORD_HASH environment
    variables are set. It does not require authentication.
    """
    service = PlatformAdminService(db)
    is_configured = service.is_admin_configured()
    
    if is_configured:
        return AdminLoginResponse(
            success=True,
            message="Platform Admin is configured",
            admin_configured=True,
        )
    else:
        return AdminLoginResponse(
            success=False,
            message="Platform Admin is not configured. Set ADMIN_EMAIL and ADMIN_PASSWORD_HASH environment variables.",
            admin_configured=False,
        )


# -----------------------------------------------------------------------------
# Subscription Plan CRUD
# -----------------------------------------------------------------------------


@router.route("/subscription-plans", methods=["POST"])
def create_subscription_plan()-> SubscriptionPlanResponse:    
    from flask import g
    db = getattr(g, "db", None)
    session = db
    
    from flask import g
    db = getattr(g, "db", None)
    session = db
    """Create a new subscription plan.
    
    Requires Platform Admin authentication.
    """
    service = PlatformAdminService(db)
    
    try:
        plan = service.create_subscription_plan(
            name=request.name,
            plan_type=request.plan_type,
            billing_period=request.billing_period,
            price=request.price,
            max_test_attempts_per_period=request.max_test_attempts_per_period,
            max_student_seats=request.max_student_seats,
            feature_flags=request.feature_flags,
        )
        return SubscriptionPlanResponse.model_validate(plan)
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )


@router.route("/subscription-plans/<plan_id>", methods=["GET"])
def get_subscription_plan(plan_id: UUID)-> SubscriptionPlanResponse:    
    from flask import g
    db = getattr(g, "db", None)
    session = db
    
    from flask import g
    db = getattr(g, "db", None)
    session = db
    """Get a subscription plan by ID.
    
    Requires Platform Admin authentication.
    """
    service = PlatformAdminService(db)
    plan = service.get_subscription_plan(plan_id)
    
    if not plan:
        raise HTTPException(
            status_code=404,
            detail=f"Subscription plan {plan_id} not found",
        )
    
    return SubscriptionPlanResponse.model_validate(plan)


@router.route("/subscription-plans", methods=["GET"])
def list_subscription_plans(plan_type: Optional[str] = None, is_active: Optional[bool] = None)-> List[SubscriptionPlanResponse]:    
    from flask import g
    db = getattr(g, "db", None)
    session = db
    
    from flask import g
    db = getattr(g, "db", None)
    session = db
    """List all subscription plans with optional filters.
    
    Requires Platform Admin authentication.
    """
    from ..db.subscription_models import SubscriptionPlan
    from decimal import Decimal
    from flask import request
    
    pt = request.args.get("plan_type") or plan_type
    ia = request.args.get("is_active")
    if ia is not None:
        is_active = ia.lower() in ("true", "1")
    
    query = db.query(SubscriptionPlan)
    
    if pt is not None and pt != "":
        query = query.filter(SubscriptionPlan.plan_type == pt)
    
    if is_active is not None:
        query = query.filter(SubscriptionPlan.is_active == is_active)
    
    plans = query.all()
    
    # If no plans exist, seed with default plans
    if len(plans) == 0:
        default_plans = [
            # Individual Plans
            {
                'name': 'Free',
                'plan_type': 'individual',
                'billing_period': 'monthly',
                'price': Decimal('0'),
                'max_test_attempts_per_period': 5,  # 5 mock tests
                'max_student_seats': None,
                'feature_flags': {
                    'mock_tests_5': True,
                    'practice_exams_3': True,
                    'ai_analytics': False,
                    'kcet_question_bank': False,
                    'leaderboard': False,
                    'performance_reports': 'Basic',
                    'ai_recommendations': False,
                },
                'is_active': True,
            },
            {
                'name': '7-Day Premium Trial',
                'plan_type': 'individual',
                'billing_period': 'weekly',
                'price': Decimal('99'),
                'max_test_attempts_per_period': 999,  # Unlimited
                'max_student_seats': None,
                'feature_flags': {
                    'mock_tests_unlimited': True,
                    'practice_exams_unlimited': True,
                    'ai_analytics': True,
                    'kcet_question_bank': True,
                    'leaderboard': True,
                    'performance_reports': True,
                    'ai_recommendations': True,
                },
                'is_active': True,
            },
            {
                'name': 'Pro Monthly',
                'plan_type': 'individual',
                'billing_period': 'monthly',
                'price': Decimal('349'),
                'max_test_attempts_per_period': 999,  # Unlimited
                'max_student_seats': None,
                'feature_flags': {
                    'mock_tests_unlimited': True,
                    'practice_exams_unlimited': True,
                    'ai_analytics': True,
                    'kcet_question_bank': True,
                    'leaderboard': True,
                    'performance_reports': 'Advanced',
                    'ai_recommendations': True,
                },
                'is_active': True,
            },
            {
                'name': 'Pro Yearly',
                'plan_type': 'individual',
                'billing_period': 'monthly',
                'price': Decimal('2999'),
                'max_test_attempts_per_period': 999,  # Unlimited
                'max_student_seats': None,
                'feature_flags': {
                    'mock_tests_unlimited': True,
                    'practice_exams_unlimited': True,
                    'ai_analytics': True,
                    'kcet_question_bank': True,
                    'leaderboard': True,
                    'performance_reports': 'Advanced',
                    'ai_recommendations': True,
                    'priority_access': True,
                },
                'is_active': True,
            },
            # Institution Plans
            {
                'name': 'Starter',
                'plan_type': 'institution',
                'billing_period': 'monthly',
                'price': Decimal('1499'),
                'max_test_attempts_per_period': None,
                'max_student_seats': 50,
                'feature_flags': {
                    'institution_uploads': True,
                    'institution_question_bank': False,
                    'chapter_tests': True,
                    'analytics': 'Basic',
                    'ai_analytics': False,
                    'performance_reports': 'Basic',
                    'branding': False,
                    'priority_support': False,
                },
                'is_active': True,
            },
            {
                'name': 'Basic',
                'plan_type': 'institution',
                'billing_period': 'monthly',
                'price': Decimal('2999'),
                'max_test_attempts_per_period': None,
                'max_student_seats': 100,
                'feature_flags': {
                    'institution_uploads': True,
                    'institution_question_bank': True,
                    'chapter_tests': True,
                    'analytics': 'Advanced',
                    'ai_analytics': False,
                    'performance_reports': 'Advanced',
                    'branding': False,
                    'priority_support': False,
                },
                'is_active': True,
            },
            {
                'name': 'Premium',
                'plan_type': 'institution',
                'billing_period': 'monthly',
                'price': Decimal('7999'),
                'max_test_attempts_per_period': None,
                'max_student_seats': None,  # Unlimited
                'feature_flags': {
                    'institution_uploads': True,
                    'institution_question_bank': 'Full',
                    'chapter_tests': True,
                    'analytics': 'Advanced',
                    'ai_analytics': True,
                    'performance_reports': 'Advanced',
                    'branding': True,
                    'priority_support': True,
                },
                'is_active': True,
            },
            {
                'name': 'Enterprise',
                'plan_type': 'institution',
                'billing_period': 'monthly',
                'price': Decimal('0'),  # Contact for pricing
                'max_test_attempts_per_period': None,
                'max_student_seats': None,  # Unlimited
                'feature_flags': {
                    'institution_uploads': True,
                    'institution_question_bank': 'Full',
                    'chapter_tests': True,
                    'analytics': 'Advanced',
                    'ai_analytics': True,
                    'performance_reports': 'Custom',
                    'branding': True,
                    'priority_support': 'Dedicated Support',
                },
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
    
    return [SubscriptionPlanResponse.model_validate(plan) for plan in plans]


@router.route("/subscription-plans/<plan_id>", methods=["PATCH"])
def update_subscription_plan(plan_id: UUID)-> SubscriptionPlanResponse:    
    from flask import g
    db = getattr(g, "db", None)
    session = db
    
    from flask import g
    db = getattr(g, "db", None)
    session = db
    """Update a subscription plan.
    
    Requires Platform Admin authentication.
    """
    service = PlatformAdminService(db)
    
    try:
        plan = service.update_subscription_plan(
            plan_id=plan_id,
            name=request.name,
            price=request.price,
            max_test_attempts_per_period=request.max_test_attempts_per_period,
            max_student_seats=request.max_student_seats,
            feature_flags=request.feature_flags,
            is_active=request.is_active,
        )
        return SubscriptionPlanResponse.model_validate(plan)
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )


@router.route("/subscription-plans/<plan_id>", methods=["DELETE"])
def delete_subscription_plan(plan_id: UUID)-> SuccessResponse:    
    from flask import g
    db = getattr(g, "db", None)
    session = db
    
    from flask import g
    db = getattr(g, "db", None)
    session = db
    """Delete a subscription plan.
    
    Rejects deletion if the plan has active subscribers.
    Requires Platform Admin authentication.
    """
    service = PlatformAdminService(db)
    
    try:
        service.delete_subscription_plan(plan_id)
        return SuccessResponse(
            success=True,
            message=f"Subscription plan {plan_id} deleted successfully",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )


# -----------------------------------------------------------------------------
# Institution Management
# -----------------------------------------------------------------------------


@router.route("/institutions/<institution_id>/activate", methods=["POST"])
def activate_institution(institution_id: UUID)-> InstitutionResponse:    
    from flask import g
    db = getattr(g, "db", None)
    session = db
    
    from flask import g
    db = getattr(g, "db", None)
    session = db
    """Activate an institution.
    
    Requires Platform Admin authentication.
    """
    service = PlatformAdminService(db)
    
    try:
        institution = service.activate_institution(institution_id)
        return InstitutionResponse.model_validate(institution)
    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e),
        )


@router.route("/institutions/<institution_id>/suspend", methods=["POST"])
def suspend_institution(institution_id: UUID)-> InstitutionResponse:    
    from flask import g
    db = getattr(g, "db", None)
    session = db
    
    from flask import g
    db = getattr(g, "db", None)
    session = db
    """Suspend an institution.
    
    Requires Platform Admin authentication.
    """
    service = PlatformAdminService(db)
    
    try:
        institution = service.suspend_institution(institution_id)
        return InstitutionResponse.model_validate(institution)
    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e),
        )


@router.route("/institutions/<institution_id>", methods=["DELETE"])
def remove_institution(institution_id: UUID)-> SuccessResponse:    
    from flask import g
    db = getattr(g, "db", None)
    session = db
    
    from flask import g
    db = getattr(g, "db", None)
    session = db
    """Remove an institution.
    
    This will cascade delete all related data (subscriptions, invitations, etc.)
    Requires Platform Admin authentication.
    """
    service = PlatformAdminService(db)
    
    try:
        service.remove_institution(institution_id)
        return SuccessResponse(
            success=True,
            message=f"Institution {institution_id} removed successfully",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e),
        )


@router.route("/institutions", methods=["GET"])
def list_institutions(subscription_status: Optional[str] = None)-> InstitutionListResponse:    
    from flask import g
    db = getattr(g, "db", None)
    session = db
    
    from flask import g
    db = getattr(g, "db", None)
    session = db
    """List all institutions with optional filters.
    
    Requires Platform Admin authentication.
    """
    from ..db.models import User, Question, Exam
    from ..db.subscription_models import Subscription, Institution
    from sqlalchemy import func
    
    query = db.query(Institution)
    
    status = request.args.get("subscription_status") or subscription_status
    if status is not None and status != "":
        query = query.filter(Institution.subscription_status == status)
    
    institutions = query.all()
    
    # Build response with additional data
    inst_responses = []
    for inst in institutions:
        # Get subscription info
        subscription = (
            db.query(Subscription)
            .filter(Subscription.institution_id == inst.id)
            .first()
        )
        
        # Get plan name from subscription
        plan_name = None
        if subscription and subscription.plan_id:
            from ..db.subscription_models import SubscriptionPlan
            plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.id == subscription.plan_id).first()
            if plan:
                plan_name = plan.name
        
        # Get student count
        student_count = db.query(func.count(User.id)).filter(
            User.institution_id == inst.id,
            User.role == 'student'
        ).scalar() or 0
        
        # Get question count
        question_count = db.query(func.count(Question.id)).filter(
            Question.institution_id == inst.id
        ).scalar() or 0
        
        # Get exam count
        exam_count = db.query(func.count(Exam.id)).filter(
            Exam.institution_id == inst.id
        ).scalar() or 0
        
        inst_responses.append(InstitutionResponse(
            id=str(inst.id),
            name=inst.name,
            institution_code=inst.institution_code,
            contact_phone=inst.contact_phone,
            subscription_status=inst.subscription_status,
            registered_at=inst.registered_at.isoformat() if inst.registered_at else None,
            student_count=int(student_count),
            question_count=int(question_count),
            exam_count=int(exam_count),
            plan_name=plan_name,
            next_renewal_date=subscription.next_renewal_date.isoformat() if subscription and subscription.next_renewal_date else None,
        ))
    
    return InstitutionListResponse(
        institutions=inst_responses,
        total=len(inst_responses),
    )


# -----------------------------------------------------------------------------
# Students Management
# -----------------------------------------------------------------------------


@router.route("/students", methods=["GET"])
def list_students(student_type: Optional[str] = None,
    institution_id: Optional[UUID] = None):    
    from flask import g, request
    db = getattr(g, "db", None)

    st = request.args.get("student_type") or student_type
    inst_id = request.args.get("institution_id") or institution_id

    from ..db.models import User
    from ..db.subscription_models import Subscription, Institution
    
    query = db.query(User).filter(User.role == 'student')
    
    if st == 'direct':
        query = query.filter(User.student_subtype.in_(['direct_subscriber', 'dual']))
    elif st == 'institution':
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
            .filter(
                Subscription.user_id == user.id,
                Subscription.status.in_(["trial", "active", "overdue", "grace_period"])
            )
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
    
    return {
        "count": len(students_data),
        "students": students_data,
    }


@router.route("/students/<user_id>", methods=["GET"])
def get_student_by_id(user_id):
    from flask import g, jsonify
    from uuid import UUID
    from ..db.models import User
    from ..db.subscription_models import Subscription, SubscriptionPlan, Institution

    db = getattr(g, "db", None)
    try:
        u_uuid = UUID(str(user_id)) if not isinstance(user_id, UUID) else user_id
    except Exception:
        return jsonify({"detail": "Invalid student user ID"}), 400

    user = db.query(User).filter(User.id == u_uuid, User.role == "student").first()
    if not user:
        return jsonify({"detail": "Student not found"}), 404

    subscription = (
        db.query(Subscription)
        .filter(
            Subscription.user_id == user.id,
            Subscription.status.in_(["trial", "active", "overdue", "grace_period"])
        )
        .first()
    )

    plan_name = None
    if subscription and subscription.plan_id:
        plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.id == subscription.plan_id).first()
        if plan:
            plan_name = plan.name

    institution_name = None
    if user.institution_id:
        inst = db.query(Institution).filter(Institution.id == user.institution_id).first()
        if inst:
            institution_name = inst.name

    return jsonify({
        "id": str(user.id),
        "kcet_student_id": user.kcet_student_id,
        "name": user.display_name,
        "email": user.email,
        "student_subtype": user.student_subtype or "direct_subscriber",
        "institution_id": str(user.institution_id) if user.institution_id else None,
        "institution_name": institution_name,
        "subscription_status": subscription.status if subscription else "no_subscription",
        "plan_name": plan_name,
        "plan_id": str(subscription.plan_id) if subscription and subscription.plan_id else None,
        "next_renewal_date": subscription.next_renewal_date.isoformat() if subscription and subscription.next_renewal_date else None,
        "price": float(subscription.price) if subscription and subscription.price else None,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }), 200


@router.route("/students", methods=["POST"])
def create_student():
    """Create a new student with an authentic password for real platform use."""
    from flask import g, request, jsonify
    from uuid import UUID, uuid4
    from datetime import datetime, timezone, timedelta
    from ..db.models import User
    from ..db.subscription_models import Subscription, SubscriptionPlan
    from ..auth.passwords import hash_password
    from ..auth.identity import next_kcet_id
    from ..middleware.rbac import require_admin

    require_admin()
    db = getattr(g, "db", None)

    data = request.get_json() or {}
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = (data.get("password") or "").strip()
    custom_kcet_id = (data.get("kcet_student_id") or "").strip()
    plan_id = data.get("plan_id")

    if not name:
        return jsonify({"detail": "Student name is required"}), 400
    if not email or "@" not in email:
        return jsonify({"detail": "Valid email address is required"}), 400
    if not password or len(password) < 6:
        return jsonify({"detail": "Password must be at least 6 characters"}), 400

    existing = db.query(User).filter(User.email == email).first()
    if existing:
        return jsonify({"detail": f"An account with email '{email}' already exists"}), 400

    if custom_kcet_id:
        student_id = custom_kcet_id
    else:
        student_id = next_kcet_id(db)

    pwd_hash = hash_password(password)

    new_user = User(
        id=uuid4(),
        email=email,
        password_hash=pwd_hash,
        display_name=name,
        role="student",
        student_subtype="direct_subscriber",
        kcet_student_id=student_id,
        created_at=datetime.now(timezone.utc).replace(tzinfo=None),
    )
    db.add(new_user)
    db.flush()

    if plan_id:
        try:
            p_uuid = UUID(str(plan_id))
            plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.id == p_uuid).first()
            if plan:
                sub = Subscription(
                    id=uuid4(),
                    user_id=new_user.id,
                    plan_id=plan.id,
                    status="active",
                    billing_period=plan.billing_period,
                    price=plan.price,
                    current_period_start=datetime.now(timezone.utc).replace(tzinfo=None),
                    next_renewal_date=datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=30),
                )
                db.add(sub)
        except Exception as e:
            logger.warning(f"Could not attach initial plan {plan_id}: {e}")

    db.commit()

    return jsonify({
        "success": True,
        "message": "Student account created successfully with active credentials",
        "student": {
            "id": str(new_user.id),
            "email": new_user.email,
            "name": new_user.display_name,
            "kcet_student_id": new_user.kcet_student_id,
            "role": new_user.role,
        }
    }), 201


# ─────────────────────────────────────────────────────────────────────────────
# Test Data Seeding (Development)
# ─────────────────────────────────────────────────────────────────────────────


@router.route("/seed/students", methods=["POST"])
def seed_test_students(direct_count: int = 5, institution_count: int = 3, students_per_institution: int = 5):    
    from flask import g
    db = getattr(g, "db", None)
    session = db
    
    from flask import g
    db = getattr(g, "db", None)
    session = db
    """Seed test student accounts for development/testing.
    
    Creates:
    - Direct subscriber students (individual users)
    - Test institutions
    - Institution-linked students
    - Trial subscriptions
    
    Query params:
    - direct_count: Number of direct subscribers to create (default: 5)
    - institution_count: Number of test institutions to create (default: 3)
    - students_per_institution: Students per institution (default: 5)
    
    Requires Platform Admin authentication.
    """
    try:
        from ..db.seed_students import seed_students
        
        result = seed_students(
            session=db,
            direct_subscriber_count=direct_count,
            institution_count=institution_count,
            institution_student_count=students_per_institution,
        )
        
        return result
    except Exception as e:
        logger.error(f"Error seeding students: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error seeding students: {str(e)}",
        )


# ─────────────────────────────────────────────────────────────────────────────
# Direct Subscriber Subscriptions
# ─────────────────────────────────────────────────────────────────────────────


@router.route("/direct-subscriptions", methods=["GET"])
def list_direct_subscriptions(subscription_status: Optional[str] = None):    
    from flask import g
    db = getattr(g, "db", None)
    session = db
    
    from flask import g
    db = getattr(g, "db", None)
    session = db
    """List all direct subscriber students with their subscriptions (if any).
    
    Shows ALL direct subscriber students, including those without active subscriptions.
    Uses LEFT JOIN to include students regardless of subscription status.
    
    Requires Platform Admin authentication.
    """
    from ..db.models import User
    from ..db.subscription_models import Subscription, SubscriptionPlan
    from sqlalchemy import outerjoin
    
    # Query ALL direct subscribers with LEFT JOIN to include those without subscriptions
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
    
    # Filter by active subscriptions only if status filter is applied
    if subscription_status:
        query = query.filter(Subscription.status == subscription_status)
    else:
        # Show only active/trial subscriptions, or students with no subscription
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
    
    return {
        "count": len(subscriptions_data),
        "subscriptions": subscriptions_data,
    }


# -----------------------------------------------------------------------------
# Aggregate Analytics
# -----------------------------------------------------------------------------


@router.route("/analytics", methods=["GET"])
def get_aggregate_analytics()-> AggregateAnalyticsResponse:    
    from flask import g
    db = getattr(g, "db", None)
    session = db
    
    from flask import g
    db = getattr(g, "db", None)
    session = db
    """Get aggregate analytics for the entire platform.
    
    Includes:
    - Active users count by role and subscription status
    - Subscription distribution by status and type
    - Exam attempt statistics
    - Revenue statistics
    
    Requires Platform Admin authentication.
    """
    service = PlatformAdminService(db)
    analytics = service.get_aggregate_analytics()
    
    return AggregateAnalyticsResponse(**analytics)


__all__ = ["router"]


# ─────────────────────────────────────────────────────────────────────────────
# Subscription Management - Direct Subscribers
# ─────────────────────────────────────────────────────────────────────────────


@router.route("/subscriptions/<subscription_id>/renew", methods=["POST"])
def renew_subscription(subscription_id: UUID):    
    from flask import g
    db = getattr(g, "db", None)
    session = db
    
    from flask import g
    db = getattr(g, "db", None)
    session = db
    """Renew a subscription (extend for another billing period).
    
    Requires Platform Admin authentication.
    """
    from ..db.subscription_models import Subscription
    from datetime import timedelta
    
    subscription = db.query(Subscription).filter(
        Subscription.id == subscription_id
    ).first()
    
    if not subscription:
        raise HTTPException(
            status_code=404,
            detail=f"Subscription {subscription_id} not found",
        )
    
    if subscription.status == 'cancelled':
        raise HTTPException(
            status_code=400,
            detail="Cannot renew a cancelled subscription",
        )
    
    try:
        # Extend renewal date by one billing period
        if subscription.next_renewal_date:
            if 'monthly' in subscription.plan.billing_period.lower():
                subscription.next_renewal_date = subscription.next_renewal_date + timedelta(days=30)
            else:  # weekly
                subscription.next_renewal_date = subscription.next_renewal_date + timedelta(days=7)
        
        # Set status to active
        subscription.status = 'active'
        subscription.updated_at = datetime.utcnow()
        
        db.commit()
        
        return {
            "success": True,
            "message": f"Subscription renewed successfully until {subscription.next_renewal_date.isoformat()}",
            "subscription_id": str(subscription.id),
            "next_renewal_date": subscription.next_renewal_date.isoformat(),
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Error renewing subscription: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error renewing subscription: {str(e)}",
        )


@router.route("/subscriptions/<subscription_id>/cancel", methods=["POST"])
def cancel_subscription(subscription_id: UUID):    
    from flask import g
    db = getattr(g, "db", None)
    session = db
    
    from flask import g
    db = getattr(g, "db", None)
    session = db
    """Cancel a subscription.
    
    Requires Platform Admin authentication.
    """
    from ..db.subscription_models import Subscription
    
    subscription = db.query(Subscription).filter(
        Subscription.id == subscription_id
    ).first()
    
    if not subscription:
        raise HTTPException(
            status_code=404,
            detail=f"Subscription {subscription_id} not found",
        )
    
    if subscription.status == 'cancelled':
        raise HTTPException(
            status_code=400,
            detail="Subscription is already cancelled",
        )
    
    try:
        subscription.status = 'cancelled'
        subscription.cancellation_date = datetime.utcnow()
        subscription.updated_at = datetime.utcnow()
        
        db.commit()
        
        return {
            "success": True,
            "message": "Subscription cancelled successfully",
            "subscription_id": str(subscription.id),
            "cancellation_date": subscription.cancellation_date.isoformat(),
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Error cancelling subscription: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error cancelling subscription: {str(e)}",
        )


class StudentSubscriptionManageRequest(BaseModel):
    action: str  # 'update' or 'remove' / 'cancel'
    plan_id: Optional[UUID] = None
    duration_months: Optional[int] = 1
    renew_from: Optional[str] = None


@router.route("/students/<user_id>/subscription/manage", methods=["POST"])
def manage_student_subscription(user_id):
    from flask import g, request, jsonify
    from uuid import UUID
    from ..db.models import User
    from ..db.subscription_models import Subscription, SubscriptionPlan
    from ..middleware.rbac import require_admin
    from datetime import datetime, timedelta

    require_admin()
    db = getattr(g, "db", None)

    try:
        u_uuid = UUID(str(user_id)) if not isinstance(user_id, UUID) else user_id
    except Exception:
        return jsonify({"detail": "Invalid student user ID"}), 400

    user = db.query(User).filter(User.id == u_uuid, User.role == 'student').first()
    if not user:
        return jsonify({"detail": "Student not found"}), 404

    data = request.get_json() or {}
    action = data.get("action")
    plan_id = data.get("plan_id")
    duration_months = int(data.get("duration_months") or 1)
    renew_from = data.get("renew_from")

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
            sub.status = "cancelled"
            sub.cancellation_date = now
            sub.updated_at = now

        db.commit()
        return jsonify({
            "success": True,
            "message": "Subscription removed successfully. Student status set to INACTIVE.",
            "user_id": str(user.id),
            "subscription_status": "cancelled",
        }), 200

    try:
        p_uuid = UUID(str(plan_id)) if not isinstance(plan_id, UUID) else plan_id
    except Exception:
        return jsonify({"detail": "Invalid plan ID"}), 400

    plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.id == p_uuid).first()
    if not plan:
        return jsonify({"detail": "Plan not found"}), 404

    start_from = now
    if renew_from:
        try:
            start_from = datetime.fromisoformat(renew_from)
        except Exception:
            start_from = now

    next_renewal = start_from + timedelta(days=30 * duration_months)

    if active_subs:
        sub = active_subs[0]
        sub.plan_id = plan.id
        sub.status = "active"
        sub.current_period_start = start_from
        sub.next_renewal_date = next_renewal
        sub.updated_at = now
    else:
        from uuid import uuid4
        sub = Subscription(
            id=uuid4(),
            user_id=user.id,
            plan_id=plan.id,
            status="active",
            billing_period=plan.billing_period,
            price=plan.price,
            current_period_start=start_from,
            next_renewal_date=next_renewal,
        )
        db.add(sub)

    db.commit()
    return jsonify({
        "success": True,
        "message": f"Subscription updated to {plan.name} successfully",
        "plan_name": plan.name,
        "next_renewal_date": next_renewal.isoformat(),
    }), 200



# ─────────────────────────────────────────────────────────────────────────────
# Password Reset for Direct Subscribers (Admin-initiated)
# ─────────────────────────────────────────────────────────────────────────────

@router.route("/students/<user_id>/reset-password", methods=["POST"])
def reset_student_password(user_id):
    from flask import g, request, jsonify
    from uuid import UUID
    from ..db.models import User
    from ..auth.passwords import hash_password
    from ..middleware.rbac import require_admin
    from datetime import datetime

    require_admin()
    db = getattr(g, "db", None)

    try:
        u_uuid = UUID(str(user_id)) if not isinstance(user_id, UUID) else user_id
    except Exception:
        return jsonify({"detail": "Invalid student user ID"}), 400

    user = db.query(User).filter(
        User.id == u_uuid,
        User.role == 'student'
    ).first()

    if not user:
        return jsonify({"detail": "Student not found"}), 404

    data = request.get_json() or {}
    new_password = (data.get("password") or data.get("new_password") or "").strip()
    if not new_password or len(new_password) < 6:
        return jsonify({"detail": "Password must be at least 6 characters"}), 400

    user.password_hash = hash_password(new_password)
    user.updated_at = datetime.utcnow()
    db.commit()

    logger.info(f"Admin reset password for student {user.email} ({user.id})")

    return jsonify({
        "success": True,
        "message": "Password reset successfully",
        "user_id": str(user.id),
        "email": user.email,
    }), 200
