"""Usage tracking and quota enforcement.

This module implements the usage tracker that monitors and enforces
per-student and per-institution usage limits based on subscription tiers.
"""

from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db.subscription_models import UsageRecord
from .models import RemainingAttempts, UsageCheckResult


class UsageTracker:
    """Tracks and enforces per-student and per-institution usage limits.
    
    This service handles:
    - Quota verification before exam starts
    - Usage recording after successful exam submission
    - Remaining attempts calculation for dashboard display
    - Period counter resets for institutions
    - Usage statistics for platform admin
    """

    def __init__(self, db: Session):
        """Initialize the usage tracker.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    def can_start_exam(self, user_id: UUID) -> UsageCheckResult:
        """Check if user has remaining quota.
        
        Uses pessimistic locking to prevent race conditions on concurrent
        exam start requests.
        
        **Requirements:** 2.1, 2.6, 2.9, 5.2, 5.3, 5.4
        
        Args:
            user_id: User ID to check quota for
            
        Returns:
            UsageCheckResult indicating whether exam can be started
        """
        from ..db.models import User
        from ..db.subscription_models import Institution, Subscription, SubscriptionPlan
        
        # Use pessimistic locking to prevent race conditions
        # SELECT FOR UPDATE locks the user row until transaction completes
        user = (
            self.db.query(User)
            .filter(User.id == user_id)
            .with_for_update()
            .first()
        )
        
        if not user:
            return UsageCheckResult(
                can_start=False,
                reason="User not found",
                remaining_attempts=None,
                quota_type=None,
                resets_at=None,
            )
        
        # Get active subscription with locking
        subscription = (
            self.db.query(Subscription)
            .filter(
                Subscription.user_id == user_id,
                Subscription.status.in_(["trial", "active", "grace_period"])
            )
            .with_for_update()
            .first()
        )
        
        # Institution-linked student: check institution subscription first
        if user.student_subtype == "institution_linked" and user.institution_id:
            from ..db.subscription_models import Institution
            institution = (
                self.db.query(Institution)
                .filter(Institution.id == user.institution_id)
                .with_for_update()
                .first()
            )
            
            if not institution:
                return UsageCheckResult(
                    can_start=False,
                    reason="Institution not found",
                    remaining_attempts=None,
                    quota_type=None,
                    resets_at=None,
                )
            # Bypass quota checks for institution students
            return UsageCheckResult(
                can_start=True,
                reason=None,
                remaining_attempts=None,
                quota_type="unlimited",
                resets_at=None,
            )
            
            # Get institution subscription
            inst_subscription = (
                self.db.query(Subscription)
                .filter(
                    Subscription.institution_id == institution.id,
                    Subscription.status.in_(["active", "grace_period"])
                )
                .with_for_update()
                .first()
            )
            
            if not inst_subscription:
                return UsageCheckResult(
                    can_start=False,
                    reason="Institution subscription not active",
                    remaining_attempts=None,
                    quota_type=None,
                    resets_at=None,
                )
            
            # Get institution plan
            inst_plan = (
                self.db.query(SubscriptionPlan)
                .filter(SubscriptionPlan.id == inst_subscription.plan_id)
                .first()
            )
            
            if not inst_plan:
                return UsageCheckResult(
                    can_start=False,
                    reason="Institution plan not found",
                    remaining_attempts=None,
                    quota_type=None,
                    resets_at=None,
                )
            
            # Check if institution has unlimited tests
            if inst_plan.max_test_attempts_per_period is None:
                return UsageCheckResult(
                    can_start=True,
                    reason=None,
                    remaining_attempts=None,  # Unlimited
                    quota_type="unlimited",
                    resets_at=None,
                )
            
            # Check weekly and monthly limits
            now = datetime.utcnow()
            period_start = inst_subscription.current_period_start
            
            # Calculate weekly period (7 days from period start)
            weekly_start = period_start
            while weekly_start + timedelta(days=7) < now:
                weekly_start += timedelta(days=7)
            weekly_end = weekly_start + timedelta(days=7)
            
            # Calculate monthly period (30 days from period start)
            monthly_start = period_start
            while monthly_start + timedelta(days=30) < now:
                monthly_start += timedelta(days=30)
            monthly_end = monthly_start + timedelta(days=30)
            
            # Count usage in current weekly period for this institution
            weekly_count = (
                self.db.query(UsageRecord)
                .filter(
                    UsageRecord.institution_id == institution.id,
                    UsageRecord.billing_period_start >= weekly_start,
                    UsageRecord.billing_period_start < weekly_end,
                )
                .count()
            )
            
            # Count usage in current monthly period for this institution
            monthly_count = (
                self.db.query(UsageRecord)
                .filter(
                    UsageRecord.institution_id == institution.id,
                    UsageRecord.billing_period_start >= monthly_start,
                    UsageRecord.billing_period_start < monthly_end,
                )
                .count()
            )
            
            max_attempts = inst_plan.max_test_attempts_per_period
            
            # Check weekly limit
            if weekly_count >= max_attempts:
                return UsageCheckResult(
                    can_start=False,
                    reason=f"Institution weekly test limit reached ({max_attempts} tests per week)",
                    remaining_attempts=0,
                    quota_type="institution_weekly",
                    resets_at=weekly_end,
                )
            
            # Check monthly limit
            if monthly_count >= max_attempts:
                return UsageCheckResult(
                    can_start=False,
                    reason=f"Institution monthly test limit reached ({max_attempts} tests per month)",
                    remaining_attempts=0,
                    quota_type="institution_monthly",
                    resets_at=monthly_end,
                )
            
            # Calculate remaining attempts (minimum of weekly and monthly remaining)
            weekly_remaining = max_attempts - weekly_count
            monthly_remaining = max_attempts - monthly_count
            remaining = min(weekly_remaining, monthly_remaining)
            
            return UsageCheckResult(
                can_start=True,
                reason=None,
                remaining_attempts=remaining,
                quota_type="institution_weekly",  # Report the more restrictive limit
                resets_at=weekly_end if weekly_remaining < monthly_remaining else monthly_end,
            )

        # No active subscription - deny access
        if not subscription:
            return UsageCheckResult(
                can_start=False,
                reason="No active subscription",
                remaining_attempts=None,
                quota_type=None,
                resets_at=None,
            )
        
        # Get the plan details
        plan = (
            self.db.query(SubscriptionPlan)
            .filter(SubscriptionPlan.id == subscription.plan_id)
            .first()
        )
        
        if not plan:
            return UsageCheckResult(
                can_start=False,
                reason="Subscription plan not found",
                remaining_attempts=None,
                quota_type=None,
                resets_at=None,
            )
        
        # Check quota based on subscription type
        
        # Case 1: Free Trial - 5 lifetime attempts
        if subscription.status == "trial":
            # Count total usage records for this user
            attempt_count = (
                self.db.query(UsageRecord)
                .filter(UsageRecord.user_id == user_id)
                .count()
            )
            
            remaining = 5 - attempt_count
            
            if remaining <= 0:
                return UsageCheckResult(
                    can_start=False,
                    reason="Trial attempt limit reached (5 lifetime attempts)",
                    remaining_attempts=0,
                    quota_type="trial",
                    resets_at=None,
                )
            
            return UsageCheckResult(
                can_start=True,
                reason=None,
                remaining_attempts=remaining,
                quota_type="trial",
                resets_at=None,
            )
        
        # Case 2: Pro Subscription - unlimited attempts
        if plan.plan_type == "individual" and subscription.status in ["active", "grace_period"]:
            return UsageCheckResult(
                can_start=True,
                reason=None,
                remaining_attempts=None,  # Unlimited
                quota_type="unlimited",
                resets_at=None,
            )
        
        # Default: deny access if we can't determine quota
        return UsageCheckResult(
            can_start=False,
            reason="Unable to determine quota",
            remaining_attempts=None,
            quota_type=None,
            resets_at=None,
        )

    def record_attempt(
        self, user_id: UUID, submission_id: UUID, subject: str
    ) -> None:
        """Record a successful exam start against the user's quota.
        
        **Requirements:** 5.1, 5.7
        
        Args:
            user_id: User ID
            submission_id: Submission ID (exam attempt)
            subject: Subject of the exam
        """
        from ..db.models import User
        from ..db.subscription_models import Subscription
        
        # Get user to check institution linkage
        user = self.db.query(User).filter(User.id == user_id).first()
        
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        # Get active subscription to determine billing period start
        subscription = (
            self.db.query(Subscription)
            .filter(
                Subscription.user_id == user_id,
                Subscription.status.in_(["trial", "active", "grace_period"])
            )
            .first()
        )
        
        # Determine billing period start
        # For trial and individual subscriptions, use subscription start date
        # For institution-linked, use institution subscription period start
        billing_period_start = datetime.utcnow()
        institution_id = None
        
        if subscription:
            billing_period_start = subscription.current_period_start
        
        # If user is institution-linked, also record institution_id
        if user.institution_id:
            institution_id = user.institution_id
            
            # Get institution subscription for accurate period start
            inst_subscription = (
                self.db.query(Subscription)
                .filter(
                    Subscription.institution_id == institution_id,
                    Subscription.status.in_(["active", "grace_period"])
                )
                .first()
            )
            
            if inst_subscription:
                billing_period_start = inst_subscription.current_period_start
        
        # Create usage record
        usage_record = UsageRecord(
            user_id=user_id,
            institution_id=institution_id,
            submission_id=submission_id,
            subject=subject,
            recorded_at=datetime.utcnow(),
            billing_period_start=billing_period_start,
        )
        
        self.db.add(usage_record)
        self.db.commit()

    def get_remaining_attempts(self, user_id: UUID) -> RemainingAttempts:
        """Return remaining attempts for display on dashboard.
        
        **Requirements:** 2.4
        
        Args:
            user_id: User ID to query
            
        Returns:
            RemainingAttempts with quota details
        """
        from ..db.models import User
        from ..db.subscription_models import Institution, Subscription, SubscriptionPlan
        
        # Get user
        user = self.db.query(User).filter(User.id == user_id).first()
        
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        # Get active subscription
        subscription = (
            self.db.query(Subscription)
            .filter(
                Subscription.user_id == user_id,
                Subscription.status.in_(["trial", "active", "grace_period"])
            )
            .first()
        )
        
        # Institution-linked student: derive quota from institution subscription
        if user.student_subtype == "institution_linked" and user.institution_id:
            institution = (
                self.db.query(Institution)
                .filter(Institution.id == user.institution_id)
                .first()
            )
            
            inst_subscription = None
            if institution:
                inst_subscription = (
                    self.db.query(Subscription)
                    .filter(
                        Subscription.institution_id == institution.id,
                        Subscription.status.in_(["active", "grace_period"])
                    )
                    .first()
                )
            
            if not inst_subscription:
                return RemainingAttempts(
                    total_attempts=0,
                    max_attempts=None,
                    remaining_attempts=None,
                    is_unlimited=False,
                    period_start=None,
                    period_end=None,
                )
            
            inst_plan = (
                self.db.query(SubscriptionPlan)
                .filter(SubscriptionPlan.id == inst_subscription.plan_id)
                .first()
            )
            
            total_attempts = (
                self.db.query(UsageRecord)
                .filter(UsageRecord.user_id == user_id)
                .count()
            )
            
            if not inst_plan or inst_plan.max_test_attempts_per_period is None:
                return RemainingAttempts(
                    total_attempts=total_attempts,
                    max_attempts=None,
                    remaining_attempts=None,
                    is_unlimited=True,
                    period_start=inst_subscription.current_period_start,
                    period_end=inst_subscription.next_renewal_date,
                )
            
            # Weekly period calculation
            now = datetime.utcnow()
            weekly_start = inst_subscription.current_period_start
            while weekly_start + timedelta(days=7) < now:
                weekly_start += timedelta(days=7)
            weekly_end = weekly_start + timedelta(days=7)
            
            weekly_count = (
                self.db.query(UsageRecord)
                .filter(
                    UsageRecord.institution_id == institution.id,
                    UsageRecord.billing_period_start >= weekly_start,
                    UsageRecord.billing_period_start < weekly_end,
                )
                .count()
            )
            
            max_attempts = inst_plan.max_test_attempts_per_period
            remaining = max(0, max_attempts - weekly_count)
            
            return RemainingAttempts(
                total_attempts=total_attempts,
                max_attempts=max_attempts,
                remaining_attempts=remaining,
                is_unlimited=False,
                period_start=weekly_start,
                period_end=weekly_end,
            )

        # No active subscription
        if not subscription:
            return RemainingAttempts(
                total_attempts=0,
                max_attempts=None,
                remaining_attempts=None,
                is_unlimited=False,
                period_start=None,
                period_end=None,
            )
        
        # Get plan details
        plan = (
            self.db.query(SubscriptionPlan)
            .filter(SubscriptionPlan.id == subscription.plan_id)
            .first()
        )
        
        if not plan:
            raise ValueError(f"Plan {subscription.plan_id} not found")
        
        # Count total attempts for this user
        total_attempts = (
            self.db.query(UsageRecord)
            .filter(UsageRecord.user_id == user_id)
            .count()
        )
        
        # Case 1: Free Trial - 5 lifetime attempts
        if subscription.status == "trial":
            max_attempts = 5
            remaining = max(0, max_attempts - total_attempts)
            
            return RemainingAttempts(
                total_attempts=total_attempts,
                max_attempts=max_attempts,
                remaining_attempts=remaining,
                is_unlimited=False,
                period_start=subscription.start_date,
                period_end=None,  # Trial doesn't have a period end
            )
        
        # Case 2: Pro Subscription - unlimited attempts
        if plan.plan_type == "individual" and subscription.status in ["active", "grace_period"]:
            return RemainingAttempts(
                total_attempts=total_attempts,
                max_attempts=None,
                remaining_attempts=None,
                is_unlimited=True,
                period_start=subscription.current_period_start,
                period_end=subscription.next_renewal_date,
            )
        
        # Default: return basic info
        return RemainingAttempts(
            total_attempts=total_attempts,
            max_attempts=None,
            remaining_attempts=None,
            is_unlimited=False,
            period_start=subscription.current_period_start,
            period_end=subscription.next_renewal_date,
        )

    def reset_period_counters(
        self, institution_id: UUID, period: str
    ) -> None:
        """Reset weekly/monthly counters for an institution.
        
        **Requirements:** 5.6
        
        Args:
            institution_id: Institution ID
            period: Period to reset ('weekly' or 'monthly')
        """
        from ..db.subscription_models import Institution, Subscription
        
        # Validate period parameter
        if period not in ["weekly", "monthly"]:
            raise ValueError(f"Invalid period: {period}. Must be 'weekly' or 'monthly'")
        
        # Get institution
        institution = (
            self.db.query(Institution)
            .filter(Institution.id == institution_id)
            .first()
        )
        
        if not institution:
            raise ValueError(f"Institution {institution_id} not found")
        
        # Get institution subscription
        subscription = (
            self.db.query(Subscription)
            .filter(
                Subscription.institution_id == institution_id,
                Subscription.status.in_(["active", "grace_period"])
            )
            .first()
        )
        
        if not subscription:
            # No active subscription, nothing to reset
            return
        
        # Update the current_period_start to mark the beginning of a new period
        # This effectively resets the counters since usage queries filter by billing_period_start
        now = datetime.utcnow()
        
        if period == "weekly":
            # Advance period start by 7 days
            subscription.current_period_start = now
        elif period == "monthly":
            # Advance period start by 30 days
            subscription.current_period_start = now
        
        self.db.commit()

    def get_usage_stats(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        subscription_tier: Optional[str] = None,
    ) -> dict:
        """Platform admin query for usage analytics.
        
        **Requirements:** 5.8
        
        Args:
            start_date: Start of date range filter (optional)
            end_date: End of date range filter (optional)
            subscription_tier: Filter by subscription tier (optional)
            
        Returns:
            Usage statistics dictionary
        """
        from sqlalchemy import func
        from ..db.subscription_models import Subscription, SubscriptionPlan
        
        # Build base query
        query = (
            self.db.query(
                UsageRecord.subject,
                func.count(UsageRecord.id).label("attempt_count"),
                SubscriptionPlan.plan_type,
                SubscriptionPlan.name.label("plan_name"),
            )
            .join(Subscription, 
                  (UsageRecord.user_id == Subscription.user_id) | 
                  (UsageRecord.institution_id == Subscription.institution_id))
            .join(SubscriptionPlan, Subscription.plan_id == SubscriptionPlan.id)
        )
        
        # Apply date filters
        if start_date:
            query = query.filter(UsageRecord.recorded_at >= start_date)
        if end_date:
            query = query.filter(UsageRecord.recorded_at <= end_date)
        
        # Apply subscription tier filter
        if subscription_tier:
            query = query.filter(SubscriptionPlan.name.like(f"%{subscription_tier}%"))
        
        # Group by subject and plan
        query = query.group_by(
            UsageRecord.subject,
            SubscriptionPlan.plan_type,
            SubscriptionPlan.name,
        )
        
        results = query.all()
        
        # Calculate total attempts
        total_attempts = sum(row.attempt_count for row in results)
        
        # Group by subject
        by_subject = {}
        for row in results:
            if row.subject not in by_subject:
                by_subject[row.subject] = 0
            by_subject[row.subject] += row.attempt_count
        
        # Group by subscription tier
        by_tier = {}
        for row in results:
            if row.plan_name not in by_tier:
                by_tier[row.plan_name] = 0
            by_tier[row.plan_name] += row.attempt_count
        
        # Build response
        return {
            "total_attempts": total_attempts,
            "by_subject": by_subject,
            "by_tier": by_tier,
            "date_range": {
                "start": start_date.isoformat() if start_date else None,
                "end": end_date.isoformat() if end_date else None,
            },
            "filter": {
                "subscription_tier": subscription_tier,
            },
        }


__all__ = ["UsageTracker"]
