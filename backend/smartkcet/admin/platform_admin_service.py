"""Platform Admin service implementation.

This module implements Platform Admin functionality including:
- CRUD operations for subscription plans
- Institution management (activate, suspend, remove)
- Aggregate analytics (active users, subscription distribution, exam attempts, revenue)
- Admin authentication via environment variables
- Audit logging for all write operations
"""

import logging
import os
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..db.models import Submission, User
from ..db.subscription_models import (
    BillingRecord,
    Institution,
    Subscription,
    SubscriptionPlan,
    UsageRecord,
)

logger = logging.getLogger(__name__)


class PlatformAdminService:
    """Service for Platform Admin operations.
    
    Platform Admin has unrestricted access to all features and can:
    - Manage subscription plans (CRUD)
    - Manage institutions (activate, suspend, remove)
    - View aggregate analytics
    - Access all platform data without restrictions
    """

    def __init__(self, db: Session):
        """Initialize the platform admin service.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    # -------------------------------------------------------------------------
    # Admin Authentication
    # -------------------------------------------------------------------------

    @staticmethod
    def get_admin_credentials() -> Optional[tuple[str, str]]:
        """Get admin credentials from environment variables.
        
        Returns:
            Tuple of (email, password_hash) if both env vars are set, None otherwise
        """
        admin_email = os.getenv("ADMIN_EMAIL")
        admin_password_hash = os.getenv("ADMIN_PASSWORD_HASH")
        
        if not admin_email or not admin_password_hash:
            logger.warning(
                "Platform Admin credentials not configured. "
                "Set ADMIN_EMAIL and ADMIN_PASSWORD_HASH environment variables."
            )
            return None
        
        return (admin_email, admin_password_hash)

    @staticmethod
    def is_admin_configured() -> bool:
        """Check if Platform Admin credentials are configured.
        
        Returns:
            True if both ADMIN_EMAIL and ADMIN_PASSWORD_HASH are set
        """
        return PlatformAdminService.get_admin_credentials() is not None

    def verify_admin_credentials(self, email: str, password_hash: str) -> bool:
        """Verify admin credentials against environment variables.
        
        Args:
            email: Admin email to verify
            password_hash: Password hash to verify
            
        Returns:
            True if credentials match environment variables
        """
        credentials = self.get_admin_credentials()
        if not credentials:
            logger.warning("Admin login attempted but credentials not configured")
            return False
        
        admin_email, admin_password_hash = credentials
        return email == admin_email and password_hash == admin_password_hash

    # -------------------------------------------------------------------------
    # Subscription Plan CRUD
    # -------------------------------------------------------------------------

    def create_subscription_plan(
        self,
        name: str,
        plan_type: str,
        billing_period: str,
        price: Decimal,
        max_test_attempts_per_period: Optional[int] = None,
        max_student_seats: Optional[int] = None,
        feature_flags: Optional[Dict[str, Any]] = None,
    ) -> SubscriptionPlan:
        """Create a new subscription plan.
        
        Args:
            name: Plan name
            plan_type: 'individual' or 'institution'
            billing_period: 'weekly' or 'monthly'
            price: Plan price
            max_test_attempts_per_period: Max test attempts per period (None = unlimited)
            max_student_seats: Max student seats (required for institution plans)
            feature_flags: Additional feature flags
            
        Returns:
            Created subscription plan
            
        Raises:
            ValueError: If validation fails
        """
        # Validate plan_type
        if plan_type not in ["individual", "institution"]:
            raise ValueError(f"Invalid plan_type: {plan_type}")
        
        # Validate billing_period
        if billing_period not in ["weekly", "monthly"]:
            raise ValueError(f"Invalid billing_period: {billing_period}")
        
        # Validate institution plan requirements
        if plan_type == "institution" and max_student_seats is None:
            raise ValueError("max_student_seats is required for institution plans")
        
        # Create plan
        plan = SubscriptionPlan(
            name=name,
            plan_type=plan_type,
            billing_period=billing_period,
            price=price,
            max_test_attempts_per_period=max_test_attempts_per_period,
            max_student_seats=max_student_seats,
            feature_flags=feature_flags or {},
            is_active=True,
        )
        
        self.db.add(plan)
        self.db.commit()
        self.db.refresh(plan)
        
        # Log the operation
        self._log_write_operation(
            operation_type="create_subscription_plan",
            target_id=str(plan.id),
            details={
                "name": name,
                "plan_type": plan_type,
                "billing_period": billing_period,
                "price": str(price),
            }
        )
        
        return plan

    def get_subscription_plan(self, plan_id: UUID) -> Optional[SubscriptionPlan]:
        """Get a subscription plan by ID.
        
        Args:
            plan_id: Plan ID
            
        Returns:
            Subscription plan or None if not found
        """
        return self.db.query(SubscriptionPlan).filter(
            SubscriptionPlan.id == plan_id
        ).first()

    def list_subscription_plans(
        self,
        plan_type: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> List[SubscriptionPlan]:
        """List all subscription plans with optional filters.
        
        Args:
            plan_type: Filter by plan type ('individual' or 'institution')
            is_active: Filter by active status
            
        Returns:
            List of subscription plans
        """
        query = self.db.query(SubscriptionPlan)
        
        if plan_type is not None:
            query = query.filter(SubscriptionPlan.plan_type == plan_type)
        
        if is_active is not None:
            query = query.filter(SubscriptionPlan.is_active == is_active)
        
        return query.all()

    def update_subscription_plan(
        self,
        plan_id: UUID,
        name: Optional[str] = None,
        price: Optional[Decimal] = None,
        max_test_attempts_per_period: Optional[int] = None,
        max_student_seats: Optional[int] = None,
        feature_flags: Optional[Dict[str, Any]] = None,
        is_active: Optional[bool] = None,
    ) -> SubscriptionPlan:
        """Update a subscription plan.
        
        Args:
            plan_id: Plan ID to update
            name: New plan name
            price: New price
            max_test_attempts_per_period: New max test attempts
            max_student_seats: New max student seats
            feature_flags: New feature flags
            is_active: New active status
            
        Returns:
            Updated subscription plan
            
        Raises:
            ValueError: If plan not found
        """
        plan = self.get_subscription_plan(plan_id)
        if not plan:
            raise ValueError(f"Subscription plan {plan_id} not found")
        
        # Update fields
        if name is not None:
            plan.name = name
        if price is not None:
            plan.price = price
        if max_test_attempts_per_period is not None:
            plan.max_test_attempts_per_period = max_test_attempts_per_period
        if max_student_seats is not None:
            plan.max_student_seats = max_student_seats
        if feature_flags is not None:
            plan.feature_flags = feature_flags
        if is_active is not None:
            plan.is_active = is_active
        
        self.db.commit()
        self.db.refresh(plan)
        
        # Log the operation
        self._log_write_operation(
            operation_type="update_subscription_plan",
            target_id=str(plan_id),
            details={
                "updated_fields": {
                    k: v for k, v in {
                        "name": name,
                        "price": str(price) if price else None,
                        "max_test_attempts_per_period": max_test_attempts_per_period,
                        "max_student_seats": max_student_seats,
                        "is_active": is_active,
                    }.items() if v is not None
                }
            }
        )
        
        return plan

    def delete_subscription_plan(self, plan_id: UUID) -> None:
        """Delete a subscription plan.
        
        Rejects deletion if the plan has active subscribers.
        
        Args:
            plan_id: Plan ID to delete
            
        Raises:
            ValueError: If plan not found or has active subscribers
        """
        plan = self.get_subscription_plan(plan_id)
        if not plan:
            raise ValueError(f"Subscription plan {plan_id} not found")
        
        # Check for active subscribers
        active_subscriptions = self.db.query(Subscription).filter(
            Subscription.plan_id == plan_id,
            Subscription.status.in_(["trial", "active", "overdue", "grace_period"])
        ).count()
        
        if active_subscriptions > 0:
            raise ValueError(
                f"Cannot delete plan {plan_id}: {active_subscriptions} active subscribers"
            )
        
        self.db.delete(plan)
        self.db.commit()
        
        # Log the operation
        self._log_write_operation(
            operation_type="delete_subscription_plan",
            target_id=str(plan_id),
            details={"plan_name": plan.name}
        )

    # -------------------------------------------------------------------------
    # Institution Management
    # -------------------------------------------------------------------------

    def activate_institution(self, institution_id: UUID) -> Institution:
        """Activate an institution.
        
        Args:
            institution_id: Institution ID to activate
            
        Returns:
            Updated institution
            
        Raises:
            ValueError: If institution not found
        """
        institution = self.db.query(Institution).filter(
            Institution.id == institution_id
        ).first()
        
        if not institution:
            raise ValueError(f"Institution {institution_id} not found")
        
        previous_status = institution.subscription_status
        institution.subscription_status = "active"
        
        self.db.commit()
        self.db.refresh(institution)
        
        # Log the operation
        self._log_write_operation(
            operation_type="activate_institution",
            target_id=str(institution_id),
            details={
                "institution_name": institution.name,
                "previous_status": previous_status,
                "new_status": "active",
            }
        )
        
        return institution

    def suspend_institution(self, institution_id: UUID) -> Institution:
        """Suspend an institution.
        
        Args:
            institution_id: Institution ID to suspend
            
        Returns:
            Updated institution
            
        Raises:
            ValueError: If institution not found
        """
        institution = self.db.query(Institution).filter(
            Institution.id == institution_id
        ).first()
        
        if not institution:
            raise ValueError(f"Institution {institution_id} not found")
        
        previous_status = institution.subscription_status
        institution.subscription_status = "inactive"
        
        self.db.commit()
        self.db.refresh(institution)
        
        # Log the operation
        self._log_write_operation(
            operation_type="suspend_institution",
            target_id=str(institution_id),
            details={
                "institution_name": institution.name,
                "previous_status": previous_status,
                "new_status": "inactive",
            }
        )
        
        return institution

    def remove_institution(self, institution_id: UUID) -> None:
        """Remove an institution.
        
        This will cascade delete all related data (subscriptions, invitations, etc.)
        
        Args:
            institution_id: Institution ID to remove
            
        Raises:
            ValueError: If institution not found
        """
        institution = self.db.query(Institution).filter(
            Institution.id == institution_id
        ).first()
        
        if not institution:
            raise ValueError(f"Institution {institution_id} not found")
        
        institution_name = institution.name
        
        self.db.delete(institution)
        self.db.commit()
        
        # Log the operation
        self._log_write_operation(
            operation_type="remove_institution",
            target_id=str(institution_id),
            details={"institution_name": institution_name}
        )

    def list_institutions(
        self,
        subscription_status: Optional[str] = None,
    ) -> List[Institution]:
        """List all institutions with optional filters.
        
        Args:
            subscription_status: Filter by subscription status
            
        Returns:
            List of institutions
        """
        query = self.db.query(Institution)
        
        if subscription_status is not None:
            query = query.filter(Institution.subscription_status == subscription_status)
        
        return query.all()

    # -------------------------------------------------------------------------
    # Aggregate Analytics
    # -------------------------------------------------------------------------

    def get_active_users_count(self) -> Dict[str, int]:
        """Get count of active users by role and subscription status.
        
        Returns:
            Dictionary with user counts by category
        """
        # Total users by role
        total_platform_admins = self.db.query(User).filter(
            User.role == "platform_admin"
        ).count()
        
        total_institution_admins = self.db.query(User).filter(
            User.role == "institution_admin"
        ).count()
        
        total_students = self.db.query(User).filter(
            User.role == "student"
        ).count()
        
        # Students with active subscriptions
        active_subscribers = self.db.query(User).join(
            Subscription, User.id == Subscription.user_id
        ).filter(
            User.role == "student",
            Subscription.status.in_(["trial", "active", "grace_period"])
        ).count()
        
        # Students by subtype
        direct_subscribers = self.db.query(User).filter(
            User.role == "student",
            User.student_subtype == "direct_subscriber"
        ).count()
        
        institution_linked = self.db.query(User).filter(
            User.role == "student",
            User.student_subtype == "institution_linked"
        ).count()
        
        dual_subscribers = self.db.query(User).filter(
            User.role == "student",
            User.student_subtype == "dual"
        ).count()
        
        return {
            "total_users": total_platform_admins + total_institution_admins + total_students,
            "platform_admins": total_platform_admins,
            "institution_admins": total_institution_admins,
            "total_students": total_students,
            "active_subscribers": active_subscribers,
            "direct_subscribers": direct_subscribers,
            "institution_linked": institution_linked,
            "dual_subscribers": dual_subscribers,
        }

    def get_subscription_distribution(self) -> Dict[str, Any]:
        """Get subscription distribution statistics.
        
        Returns:
            Dictionary with subscription counts by status and type
        """
        # Subscriptions by status
        subscription_counts = {}
        for status in ["trial", "active", "overdue", "grace_period", "expired", "cancelled"]:
            count = self.db.query(Subscription).filter(
                Subscription.status == status
            ).count()
            subscription_counts[status] = count
        
        # Individual vs institution subscriptions
        individual_subscriptions = self.db.query(Subscription).filter(
            Subscription.user_id.isnot(None)
        ).count()
        
        institution_subscriptions = self.db.query(Subscription).filter(
            Subscription.institution_id.isnot(None)
        ).count()
        
        # Subscriptions by plan
        plan_distribution = self.db.query(
            SubscriptionPlan.name,
            func.count(Subscription.id).label("count")
        ).join(
            Subscription, SubscriptionPlan.id == Subscription.plan_id
        ).group_by(
            SubscriptionPlan.name
        ).all()
        
        return {
            "by_status": subscription_counts,
            "individual_subscriptions": individual_subscriptions,
            "institution_subscriptions": institution_subscriptions,
            "by_plan": {plan_name: count for plan_name, count in plan_distribution},
        }

    def get_exam_attempts_statistics(self) -> Dict[str, Any]:
        """Get exam attempt statistics.
        
        Returns:
            Dictionary with exam attempt counts and averages
        """
        # Total exam attempts
        total_attempts = self.db.query(Submission).count()
        
        # Attempts by subject
        attempts_by_subject = self.db.query(
            UsageRecord.subject,
            func.count(UsageRecord.id).label("count")
        ).group_by(
            UsageRecord.subject
        ).all()
        
        # Average attempts per user
        user_attempt_counts = self.db.query(
            Submission.user_id,
            func.count(Submission.id).label("count")
        ).group_by(
            Submission.user_id
        ).subquery()
        
        avg_attempts_per_user = self.db.query(
            func.avg(user_attempt_counts.c.count)
        ).scalar() or 0
        
        # Attempts by subscription type
        trial_attempts = self.db.query(UsageRecord).join(
            User, UsageRecord.user_id == User.id
        ).join(
            Subscription, User.id == Subscription.user_id
        ).filter(
            Subscription.status == "trial"
        ).count()
        
        pro_attempts = self.db.query(UsageRecord).join(
            User, UsageRecord.user_id == User.id
        ).join(
            Subscription, User.id == Subscription.user_id
        ).filter(
            Subscription.status == "active"
        ).count()
        
        return {
            "total_attempts": total_attempts,
            "by_subject": {subject: count for subject, count in attempts_by_subject},
            "avg_attempts_per_user": float(avg_attempts_per_user),
            "trial_attempts": trial_attempts,
            "pro_attempts": pro_attempts,
        }

    def get_revenue_statistics(self) -> Dict[str, Any]:
        """Get revenue statistics.
        
        Returns:
            Dictionary with revenue totals and breakdowns
        """
        # Total revenue (all paid billing records)
        total_revenue = self.db.query(
            func.sum(BillingRecord.amount)
        ).filter(
            BillingRecord.payment_status == "paid"
        ).scalar() or Decimal("0.00")
        
        # Revenue by plan type
        revenue_by_plan = self.db.query(
            SubscriptionPlan.name,
            func.sum(BillingRecord.amount).label("revenue")
        ).join(
            Subscription, SubscriptionPlan.id == Subscription.plan_id
        ).join(
            BillingRecord, Subscription.id == BillingRecord.subscription_id
        ).filter(
            BillingRecord.payment_status == "paid"
        ).group_by(
            SubscriptionPlan.name
        ).all()
        
        # Pending revenue (pending payments)
        pending_revenue = self.db.query(
            func.sum(BillingRecord.amount)
        ).filter(
            BillingRecord.payment_status == "pending"
        ).scalar() or Decimal("0.00")
        
        # Failed revenue (failed payments)
        failed_revenue = self.db.query(
            func.sum(BillingRecord.amount)
        ).filter(
            BillingRecord.payment_status == "failed"
        ).scalar() or Decimal("0.00")
        
        return {
            "total_revenue": str(total_revenue),
            "by_plan": {plan_name: str(revenue) for plan_name, revenue in revenue_by_plan},
            "pending_revenue": str(pending_revenue),
            "failed_revenue": str(failed_revenue),
        }

    def get_aggregate_analytics(self) -> Dict[str, Any]:
        """Get all aggregate analytics in a single call.
        
        Returns:
            Dictionary with all analytics data
        """
        return {
            "active_users": self.get_active_users_count(),
            "subscription_distribution": self.get_subscription_distribution(),
            "exam_attempts": self.get_exam_attempts_statistics(),
            "revenue": self.get_revenue_statistics(),
            "generated_at": datetime.utcnow().isoformat(),
        }

    # -------------------------------------------------------------------------
    # Audit Logging
    # -------------------------------------------------------------------------

    def _log_write_operation(
        self,
        operation_type: str,
        target_id: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log a write operation for audit purposes.
        
        Args:
            operation_type: Type of operation (e.g., 'create_subscription_plan')
            target_id: ID of the target entity
            details: Additional operation details
        """
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "operation_type": operation_type,
            "target_id": target_id,
            "details": details or {},
        }
        
        logger.info(
            f"Platform Admin write operation: {operation_type}",
            extra=log_entry
        )


__all__ = ["PlatformAdminService"]
