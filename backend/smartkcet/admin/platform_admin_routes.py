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

from fastapi import APIRouter, Depends, HTTPException, status
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

router = APIRouter(prefix="/platform", tags=["Platform Admin"])


# -----------------------------------------------------------------------------
# Admin Authentication
# -----------------------------------------------------------------------------


@router.post("/check-config", response_model=AdminLoginResponse)
def check_admin_config(db: Session = Depends(get_session)) -> AdminLoginResponse:
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


@router.post("/subscription-plans", response_model=SubscriptionPlanResponse, status_code=status.HTTP_201_CREATED)
def create_subscription_plan(
    request: CreateSubscriptionPlanRequest,
    db: Session = Depends(get_session),
    _: dict = Depends(require_platform_admin),
) -> SubscriptionPlanResponse:
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
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/subscription-plans/{plan_id}", response_model=SubscriptionPlanResponse)
def get_subscription_plan(
    plan_id: UUID,
    db: Session = Depends(get_session),
    _: dict = Depends(require_platform_admin),
) -> SubscriptionPlanResponse:
    """Get a subscription plan by ID.
    
    Requires Platform Admin authentication.
    """
    service = PlatformAdminService(db)
    plan = service.get_subscription_plan(plan_id)
    
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subscription plan {plan_id} not found",
        )
    
    return SubscriptionPlanResponse.model_validate(plan)


@router.get("/subscription-plans", response_model=List[SubscriptionPlanResponse])
def list_subscription_plans(
    plan_type: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_session),
    _: dict = Depends(require_platform_admin),
) -> List[SubscriptionPlanResponse]:
    """List all subscription plans with optional filters.
    
    Requires Platform Admin authentication.
    """
    from ..db.subscription_models import SubscriptionPlan
    from decimal import Decimal
    
    query = db.query(SubscriptionPlan)
    
    if plan_type is not None:
        query = query.filter(SubscriptionPlan.plan_type == plan_type)
    
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


@router.patch("/subscription-plans/{plan_id}", response_model=SubscriptionPlanResponse)
def update_subscription_plan(
    plan_id: UUID,
    request: UpdateSubscriptionPlanRequest,
    db: Session = Depends(get_session),
    _: dict = Depends(require_platform_admin),
) -> SubscriptionPlanResponse:
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
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.delete("/subscription-plans/{plan_id}", response_model=SuccessResponse)
def delete_subscription_plan(
    plan_id: UUID,
    db: Session = Depends(get_session),
    _: dict = Depends(require_platform_admin),
) -> SuccessResponse:
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
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# -----------------------------------------------------------------------------
# Institution Management
# -----------------------------------------------------------------------------


@router.post("/institutions/{institution_id}/activate", response_model=InstitutionResponse)
def activate_institution(
    institution_id: UUID,
    db: Session = Depends(get_session),
    _: dict = Depends(require_platform_admin),
) -> InstitutionResponse:
    """Activate an institution.
    
    Requires Platform Admin authentication.
    """
    service = PlatformAdminService(db)
    
    try:
        institution = service.activate_institution(institution_id)
        return InstitutionResponse.model_validate(institution)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.post("/institutions/{institution_id}/suspend", response_model=InstitutionResponse)
def suspend_institution(
    institution_id: UUID,
    db: Session = Depends(get_session),
    _: dict = Depends(require_platform_admin),
) -> InstitutionResponse:
    """Suspend an institution.
    
    Requires Platform Admin authentication.
    """
    service = PlatformAdminService(db)
    
    try:
        institution = service.suspend_institution(institution_id)
        return InstitutionResponse.model_validate(institution)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.delete("/institutions/{institution_id}", response_model=SuccessResponse)
def remove_institution(
    institution_id: UUID,
    db: Session = Depends(get_session),
    _: dict = Depends(require_platform_admin),
) -> SuccessResponse:
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
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.get("/institutions", response_model=InstitutionListResponse)
async def list_institutions(
    subscription_status: Optional[str] = None,
    db: Session = Depends(get_session),
    _: dict = Depends(require_platform_admin),
) -> InstitutionListResponse:
    """List all institutions with optional filters.
    
    Requires Platform Admin authentication.
    """
    from ..db.models import User, Question, Exam
    from ..db.subscription_models import Subscription, Institution
    from sqlalchemy import func
    
    query = db.query(Institution)
    
    if subscription_status is not None:
        query = query.filter(Institution.subscription_status == subscription_status)
    
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


@router.get("/students")
async def list_students(
    student_type: Optional[str] = None,  # 'direct' or 'institution' or None for all
    institution_id: Optional[UUID] = None,
    db: Session = Depends(get_session),
    _: dict = Depends(require_platform_admin),
):
    """List all students with optional filters.
    
    Requires Platform Admin authentication.
    
    Query params:
    - student_type: 'direct' for direct subscribers, 'institution' for institution-linked
    - institution_id: filter by specific institution
    """
    from ..db.models import User
    from ..db.subscription_models import Subscription, Institution
    
    query = db.query(User).filter(User.role == 'student')
    
    # Filter by student type
    if student_type == 'direct':
        query = query.filter(User.student_subtype.in_(['direct_subscriber', 'dual']))
    elif student_type == 'institution':
        query = query.filter(User.student_subtype.in_(['institution_linked', 'dual']))
        if institution_id:
            query = query.filter(User.institution_id == institution_id)
    elif institution_id:
        query = query.filter(User.institution_id == institution_id)
    
    students = query.all()
    
    # Build response with subscription info
    students_data = []
    for user in students:
        # Get subscription info
        subscription = (
            db.query(Subscription)
            .filter(
                Subscription.user_id == user.id,
                Subscription.status.in_(["trial", "active", "overdue", "grace_period"])
            )
            .first()
        )
        
        # Get institution name if linked
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


# ─────────────────────────────────────────────────────────────────────────────
# Test Data Seeding (Development)
# ─────────────────────────────────────────────────────────────────────────────


@router.post("/seed/students")
def seed_test_students(
    direct_count: int = 5,
    institution_count: int = 3,
    students_per_institution: int = 5,
    db: Session = Depends(get_session),
    _: dict = Depends(require_platform_admin),
):
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
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error seeding students: {str(e)}",
        )


# ─────────────────────────────────────────────────────────────────────────────
# Direct Subscriber Subscriptions
# ─────────────────────────────────────────────────────────────────────────────


@router.get("/direct-subscriptions")
def list_direct_subscriptions(
    subscription_status: Optional[str] = None,
    db: Session = Depends(get_session),
    _: dict = Depends(require_platform_admin),
):
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


@router.get("/analytics", response_model=AggregateAnalyticsResponse)
def get_aggregate_analytics(
    db: Session = Depends(get_session),
    _: dict = Depends(require_platform_admin),
) -> AggregateAnalyticsResponse:
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


@router.post("/subscriptions/{subscription_id}/renew")
def renew_subscription(
    subscription_id: UUID,
    db: Session = Depends(get_session),
    _: dict = Depends(require_platform_admin),
):
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
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subscription {subscription_id} not found",
        )
    
    if subscription.status == 'cancelled':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
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
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error renewing subscription: {str(e)}",
        )


@router.post("/subscriptions/{subscription_id}/cancel")
def cancel_subscription(
    subscription_id: UUID,
    db: Session = Depends(get_session),
    _: dict = Depends(require_platform_admin),
):
    """Cancel a subscription.
    
    Requires Platform Admin authentication.
    """
    from ..db.subscription_models import Subscription
    
    subscription = db.query(Subscription).filter(
        Subscription.id == subscription_id
    ).first()
    
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subscription {subscription_id} not found",
        )
    
    if subscription.status == 'cancelled':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
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
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error cancelling subscription: {str(e)}",
        )


class StudentSubscriptionManageRequest(BaseModel):
    action: str  # 'update' or 'remove' / 'cancel'
    plan_id: Optional[UUID] = None
    duration_months: Optional[int] = 1
    renew_from: Optional[str] = None


@router.post("/students/{user_id}/subscription/manage")
def manage_student_subscription(
    user_id: UUID,
    data: StudentSubscriptionManageRequest,
    db: Session = Depends(get_session),
    _: dict = Depends(require_platform_admin),
):
    """Update or remove/cancel a student's subscription.
    
    Setting status to 'cancelled' sets the account's subscription status to INACTIVE.
    Requires Platform Admin authentication.
    """
    from ..db.models import User
    from ..db.subscription_models import Subscription, SubscriptionPlan, SubscriptionEvent
    from datetime import timedelta

    user = db.query(User).filter(User.id == user_id, User.role == 'student').first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student {user_id} not found",
        )

    try:
        now = datetime.utcnow()
        active_subs = db.query(Subscription).filter(
            Subscription.user_id == user.id,
            Subscription.status.in_(["trial", "active", "overdue", "grace_period"])
        ).all()

        if data.action in ("remove", "cancel") or not data.plan_id:
            # Set all active subscriptions to cancelled (INACTIVE)
            if not active_subs:
                return {
                    "success": True,
                    "message": "Student already has no active subscription",
                    "user_id": str(user.id),
                    "subscription_status": "cancelled",
                }

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
            return {
                "success": True,
                "message": "Subscription removed successfully. Student status set to INACTIVE.",
                "user_id": str(user.id),
                "subscription_status": "cancelled",
            }

        # Action: update to a new plan
        plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.id == data.plan_id).first()
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Plan {data.plan_id} not found",
            )

        months = data.duration_months or 1
        start_from = now
        if data.renew_from:
            try:
                start_from = datetime.fromisoformat(data.renew_from)
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
        return {
            "success": True,
            "message": f"Subscription updated to {plan.name} until {next_renewal.strftime('%d %b %Y')}",
            "user_id": str(user.id),
            "subscription_id": str(sub.id),
            "plan_name": plan.name,
            "subscription_status": "active",
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error managing student subscription: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error managing student subscription: {str(e)}",
        )



# ─────────────────────────────────────────────────────────────────────────────
# Password Reset for Direct Subscribers (Admin-initiated)
# ─────────────────────────────────────────────────────────────────────────────

class PasswordResetRequest(BaseModel):
    """Request to reset a student's password."""
    password: str = Field(
        ..., 
        min_length=8, 
        max_length=72,
        description="New password (8-72 characters)"
    )


@router.post("/students/{user_id}/reset-password")
def reset_student_password(
    user_id: UUID,
    data: PasswordResetRequest,
    db: Session = Depends(get_session),
    _: dict = Depends(require_platform_admin),
):
    """Reset a direct subscriber student's password.
    
    Allows platform admins to set a new password for students who forgot theirs.
    
    Requires Platform Admin authentication.
    
    Args:
        user_id: UUID of the student user
        data: New password
        db: Database session
        
    Returns:
        Success response with confirmation
    """
    from ..db.models import User
    from ..auth.passwords import hash_password
    
    try:
        # Find the user
        user = db.query(User).filter(
            User.id == user_id,
            User.role == 'student',
            User.student_subtype.in_(['direct_subscriber', 'dual'])
        ).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student not found or is not a direct subscriber"
            )
        
        # Validate password
        if len(data.password) < 8:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be at least 8 characters"
            )
        
        # Hash and update password
        user.password_hash = hash_password(data.password)
        user.updated_at = datetime.utcnow()
        
        db.add(user)
        db.commit()
        
        logger.info(f"Admin reset password for student {user.email} ({user.id})")
        
        return {
            "success": True,
            "message": "Password reset successfully",
            "user_id": str(user.id),
            "email": user.email,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error resetting password: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error resetting password"
        )
