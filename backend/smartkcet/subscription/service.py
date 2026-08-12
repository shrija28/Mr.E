"""Subscription service implementation.

This module implements the core subscription lifecycle management logic,
including activation, renewal, expiry, cancellation, and reactivation.
"""

from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db.subscription_models import Subscription, SubscriptionPlan
from .models import BillingPeriod, EffectiveSubscriptionStatus


class SubscriptionService:
    """Manages subscription lifecycle for individuals and institutions.
    
    This service handles:
    - Subscription activation (trial and pro)
    - Subscription upgrades (trial to pro)
    - Subscription renewal and expiry
    - Subscription cancellation and reactivation
    - Effective subscription status queries
    """

    def __init__(self, db: Session):
        """Initialize the subscription service.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    def activate_free(self, user_id: UUID) -> Subscription:
        """Activate Free plan (₹0) for a student.
        
        Only allowed when no active subscription exists (all are expired/cancelled).
        Returns existing active Free subscription if already on it.
        
        Args:
            user_id: User ID to activate free plan for
            
        Returns:
            Subscription record
            
        Raises:
            ValueError: If an active paid/trial subscription already exists
        """
        # Check for existing active subscription
        existing_active = (
            self.db.query(Subscription)
            .filter(
                Subscription.user_id == user_id,
                Subscription.status.in_(["trial", "active", "overdue", "grace_period"])
            )
            .first()
        )
        
        if existing_active:
            # If already on Free plan, return it
            from sqlalchemy import cast, String
            existing_plan = self.db.query(SubscriptionPlan).filter(
                cast(SubscriptionPlan.id, String) == str(existing_active.plan_id)
            ).first()
            
            if existing_plan and existing_plan.name == "Free" and existing_plan.price == 0:
                return existing_active  # Already on Free
            
            # Otherwise, block if they're on a paid/trial plan
            raise ValueError(
                "Cannot activate Free plan while an active paid or trial subscription exists. "
                "Please wait for your subscription to expire."
            )
        
        # Get Free plan (₹0)
        free_plan = (
            self.db.query(SubscriptionPlan)
            .filter(
                SubscriptionPlan.name == "Free",
                SubscriptionPlan.plan_type == "individual",
                SubscriptionPlan.price == 0,
                SubscriptionPlan.is_active == True
            )
            .first()
        )
        
        if not free_plan:
            raise ValueError("Free plan not found in database")
        
        # Create new free subscription
        now = datetime.utcnow()
        
        subscription = Subscription(
            user_id=user_id,
            plan_id=free_plan.id,  # Use UUID directly
            status="active",
            start_date=now,
            current_period_start=now,
            next_renewal_date=None,  # Free plan doesn't renew
        )
        
        self.db.add(subscription)
        self.db.flush()
        
        # Create subscription event for audit trail
        from ..db.subscription_models import SubscriptionEvent
        event = SubscriptionEvent(
            subscription_id=subscription.id,
            event_type="activated",
            previous_status="none",
            new_status="active",
            event_metadata={
                "plan_name": "Free",
                "activation_timestamp": now.isoformat()
            }
        )
        self.db.add(event)
        
        self.db.commit()
        self.db.refresh(subscription)
        
        return subscription

    def activate_trial(
        self, user_id: UUID, duration_days: int = 7
    ) -> Subscription:
        """Create a Free Trial subscription.
        
        If user already has an active Free subscription, deactivate it first.
        One trial per account lifetime — raises ValueError if a prior trial exists
        in any state (expired, cancelled, or active).
        
        Args:
            user_id: User ID to activate trial for
            duration_days: Trial duration in days (default 7)
            
        Returns:
            Subscription record
            
        Raises:
            ValueError: If duration_days is outside valid range or trial already used
        """
        # Validate duration_days
        if not (1 <= duration_days <= 90):
            raise ValueError(
                f"Trial duration must be between 1 and 90 days, got {duration_days}"
            )
        
        # Check for existing active subscription and DEACTIVATE if it's Free
        existing_active = (
            self.db.query(Subscription)
            .filter(
                Subscription.user_id == user_id,
                Subscription.status.in_(["trial", "active", "overdue", "grace_period"])
            )
            .first()
        )
        
        if existing_active:
            # If it's the same trial, return it (idempotent)
            from sqlalchemy import cast, String
            existing_plan = self.db.query(SubscriptionPlan).filter(
                cast(SubscriptionPlan.id, String) == str(existing_active.plan_id)
            ).first()
            
            if existing_plan and existing_plan.name == "Free Trial":
                return existing_active  # Already on trial, return it
            
            # Otherwise deactivate the previous subscription (Free/Pro/etc)
            existing_active.status = "expired"
            self.db.flush()
        
        # Prevent trial abuse: one trial per account lifetime
        prior_trial = (
            self.db.query(Subscription)
            .join(SubscriptionPlan, Subscription.plan_id == SubscriptionPlan.id)
            .filter(
                Subscription.user_id == user_id,
                SubscriptionPlan.plan_type == "individual",
                SubscriptionPlan.name == "Free Trial",
            )
            .first()
        )
        
        if prior_trial:
            raise ValueError(
                "Free Trial can only be used once per account. "
                "Please subscribe to a Pro plan to continue."
            )
        
        # Get Free Trial plan
        free_trial_plan = (
            self.db.query(SubscriptionPlan)
            .filter(
                SubscriptionPlan.name == "Free Trial",
                SubscriptionPlan.plan_type == "individual",
                SubscriptionPlan.is_active == True
            )
            .first()
        )
        
        if not free_trial_plan:
            raise ValueError("Free Trial plan not found in database")
        
        # Create new trial subscription
        now = datetime.utcnow()
        
        subscription = Subscription(
            user_id=user_id,
            plan_id=free_trial_plan.id,  # Use UUID directly
            status="trial",
            start_date=now,
            current_period_start=now,
            trial_duration_days=duration_days,
            next_renewal_date=None,  # Trials don't renew
        )
        
        self.db.add(subscription)
        self.db.flush()  # Flush to get the subscription ID
        
        # Create subscription event for audit trail
        from ..db.subscription_models import SubscriptionEvent
        event = SubscriptionEvent(
            subscription_id=subscription.id,
            event_type="activated",
            previous_status="none",
            new_status="trial",
            event_metadata={
                "trial_duration_days": duration_days,
                "activation_timestamp": now.isoformat()
            }
        )
        self.db.add(event)
        
        self.db.commit()
        self.db.refresh(subscription)
        
        return subscription

    def activate_pro(
        self, user_id: UUID, billing_period: BillingPeriod
    ) -> Subscription:
        """Create a Pro subscription with the given billing period.
        
        If user already has an active Free/Trial subscription, deactivate it first.
        
        Args:
            user_id: User ID to activate Pro subscription for
            billing_period: Billing period (weekly or monthly)
            
        Returns:
            Subscription record
        """
        # Check for existing active subscription
        existing_active = (
            self.db.query(Subscription)
            .filter(
                Subscription.user_id == user_id,
                Subscription.status.in_(["trial", "active", "overdue", "grace_period"])
            )
            .first()
        )
        
        if existing_active:
            # If it's already the same Pro plan, return it (idempotent)
            from sqlalchemy import cast, String
            existing_plan = self.db.query(SubscriptionPlan).filter(
                cast(SubscriptionPlan.id, String) == str(existing_active.plan_id)
            ).first()
            
            if (existing_plan and 
                existing_plan.name.startswith("Pro") and
                existing_plan.billing_period == billing_period.value):
                return existing_active  # Already on this plan
            
            # Otherwise deactivate the previous subscription (Free/Trial/different Pro)
            existing_active.status = "expired"
            self.db.flush()
        
        # Get Pro plan for the specified billing period
        pro_plan = (
            self.db.query(SubscriptionPlan)
            .filter(
                SubscriptionPlan.name.like("Pro%"),
                SubscriptionPlan.plan_type == "individual",
                SubscriptionPlan.billing_period == billing_period.value,
                SubscriptionPlan.is_active == True
            )
            .first()
        )
        
        if not pro_plan:
            raise ValueError(
                f"Pro plan with billing period '{billing_period.value}' not found in database"
            )
        
        # Calculate next renewal date based on billing period
        now = datetime.utcnow()
        if billing_period == BillingPeriod.WEEKLY:
            next_renewal = now + timedelta(days=7)
        else:  # MONTHLY
            next_renewal = now + timedelta(days=30)
        
        # Create new Pro subscription
        subscription = Subscription(
            user_id=user_id,
            plan_id=pro_plan.id,  # Use UUID directly, not as string
            status="active",
            start_date=now,
            current_period_start=now,
            next_renewal_date=next_renewal,
            trial_duration_days=None,
        )
        
        self.db.add(subscription)
        self.db.flush()  # Flush to get the subscription ID
        
        # Create subscription event for audit trail
        from ..db.subscription_models import SubscriptionEvent
        event = SubscriptionEvent(
            subscription_id=subscription.id,
            event_type="activated",
            previous_status="none",
            new_status="active",
            event_metadata={
                "billing_period": billing_period.value,
                "next_renewal_date": next_renewal.isoformat(),
                "activation_timestamp": now.isoformat()
            }
        )
        self.db.add(event)
        
        self.db.commit()
        self.db.refresh(subscription)
        
        return subscription

    def activate_institution_plan(
        self, institution_id: UUID, plan_id: UUID
    ) -> Subscription:
        """Activate an institution subscription plan.

        Creates a new Subscription if none exists, or upgrades/renews an
        existing one. Called by the payment webhook and manual admin activation.

        Args:
            institution_id: Institution ID
            plan_id: Subscription plan ID to activate

        Returns:
            Subscription record (new or updated)
        """
        from ..db.subscription_models import Institution, SubscriptionEvent

        plan = (
            self.db.query(SubscriptionPlan)
            .filter(SubscriptionPlan.id == plan_id, SubscriptionPlan.is_active.is_(True))
            .first()
        )
        if not plan:
            raise ValueError(f"Plan {plan_id} not found or inactive")

        existing = (
            self.db.query(Subscription)
            .filter(
                Subscription.institution_id == institution_id,
                Subscription.status.in_(["trial", "active", "overdue", "grace_period"]),
            )
            .first()
        )

        now = datetime.utcnow()
        duration = timedelta(days=7 if plan.billing_period == "weekly" else 30)

        if existing:
            prev_status = existing.status
            existing.plan_id              = plan_id
            existing.status               = "active"
            existing.current_period_start = now
            existing.next_renewal_date    = now + duration
            existing.cancellation_date    = None
            existing.grace_period_end     = None

            evt = SubscriptionEvent(
                subscription_id=existing.id,
                event_type="upgraded",
                previous_status=prev_status,
                new_status="active",
                event_metadata={"plan_id": str(plan_id), "activated_at": now.isoformat()},
            )
            self.db.add(evt)
            self.db.commit()
            self.db.refresh(existing)
            return existing

        subscription = Subscription(
            institution_id=institution_id,
            plan_id=plan_id,
            status="active",
            start_date=now,
            current_period_start=now,
            next_renewal_date=now + duration,
        )
        self.db.add(subscription)
        self.db.flush()

        evt = SubscriptionEvent(
            subscription_id=subscription.id,
            event_type="activated",
            previous_status="none",
            new_status="active",
            event_metadata={"plan_id": str(plan_id), "activated_at": now.isoformat()},
        )
        self.db.add(evt)

        inst = self.db.query(Institution).filter(Institution.id == institution_id).first()
        if inst:
            inst.subscription_status = "active"

        self.db.commit()
        self.db.refresh(subscription)
        return subscription

    def get_effective_status(self, user_id: UUID) -> EffectiveSubscriptionStatus:
        """Single round-trip query for a user's current subscription state.
        
        For institution-linked students (student_subtype == 'institution_linked'),
        returns the institution's subscription status as their effective access.
        
        Args:
            user_id: User ID to query
            
        Returns:
            EffectiveSubscriptionStatus with all subscription details
        """
        from ..db.models import User
        from ..db.subscription_models import Institution

        # Fetch user to check subtype
        user = self.db.query(User).filter(User.id == user_id).first()

        # Institution-linked students: derive status from institution subscription
        if user and user.student_subtype == "institution_linked" and user.institution_id:
            institution = self.db.query(Institution).filter(
                Institution.id == user.institution_id
            ).first()

            inst_sub = (
                self.db.query(Subscription)
                .filter(
                    Subscription.institution_id == user.institution_id,
                    Subscription.status.in_(["trial", "active", "overdue", "grace_period"]),
                )
                .first()
            )

            inst_plan = None
            if inst_sub:
                inst_plan = (
                    self.db.query(SubscriptionPlan)
                    .filter(SubscriptionPlan.id == inst_sub.plan_id)
                    .first()
                )

            return EffectiveSubscriptionStatus(
                has_subscription=True,
                status="active",
                plan_type=inst_plan.plan_type if inst_plan else "institution",
                plan_name=inst_plan.name if inst_plan else "Institution Pro",
                billing_period=inst_plan.billing_period if inst_plan else "monthly",
                is_trial=False,
                is_active=True,
                trial_attempts_remaining=None,
                start_date=inst_sub.start_date if inst_sub else None,
                current_period_start=inst_sub.current_period_start if inst_sub else None,
                next_renewal_date=inst_sub.next_renewal_date if inst_sub else None,
                grace_period_end=inst_sub.grace_period_end if inst_sub else None,
                institution_id=user.institution_id,
                institution_name=institution.name if institution else None,
            )
        
        # Single query with all necessary joins
        result = (
            self.db.query(
                Subscription,
                SubscriptionPlan,
                User,
                Institution
            )
            .outerjoin(SubscriptionPlan, Subscription.plan_id == SubscriptionPlan.id)
            .outerjoin(User, Subscription.user_id == User.id)
            .outerjoin(Institution, User.institution_id == Institution.id)
            .filter(
                Subscription.user_id == user_id,
                Subscription.status.in_(["trial", "active", "overdue", "grace_period"])
            )
            .first()
        )
        
        # No active subscription found
        if not result:
            return EffectiveSubscriptionStatus(
                has_subscription=False,
                status=None,
                plan_type=None,
                plan_name=None,
                billing_period=None,
                is_trial=False,
                is_active=False,
                trial_attempts_remaining=None,
                start_date=None,
                current_period_start=None,
                next_renewal_date=None,
                grace_period_end=None,
                institution_id=None,
                institution_name=None,
            )
        
        subscription, plan, user, institution = result
        
        # Determine if subscription is active (grants access)
        is_active = subscription.status in ["trial", "active", "grace_period"]
        
        # Determine if this is a trial subscription
        is_trial = subscription.status == "trial"
        
        # Calculate remaining trial attempts if applicable
        trial_attempts_remaining = None
        if is_trial:
            from ..db.models import Submission
            attempt_count = (
                self.db.query(Submission)
                .filter(Submission.user_id == user_id)
                .count()
            )
            trial_attempts_remaining = max(0, 5 - attempt_count)
        
        # Build response
        return EffectiveSubscriptionStatus(
            has_subscription=True,
            status=subscription.status,
            plan_type=plan.plan_type if plan else None,
            plan_name=plan.name if plan else None,
            billing_period=plan.billing_period if plan else None,
            is_trial=is_trial,
            is_active=is_active,
            trial_attempts_remaining=trial_attempts_remaining,
            start_date=subscription.start_date,
            current_period_start=subscription.current_period_start,
            next_renewal_date=subscription.next_renewal_date,
            grace_period_end=subscription.grace_period_end,
            institution_id=institution.id if institution else None,
            institution_name=institution.name if institution else None,
        )

    def process_renewal(
        self, subscription_id: UUID, payment_confirmed: bool
    ) -> Subscription:
        """Handle renewal: extend on payment, enter grace period otherwise.
        
        Args:
            subscription_id: Subscription ID to renew
            payment_confirmed: Whether payment was confirmed
            
        Returns:
            Updated subscription record
        """
        from ..db.subscription_models import SubscriptionEvent
        
        # Get the subscription
        subscription = (
            self.db.query(Subscription)
            .filter(Subscription.id == subscription_id)
            .first()
        )
        
        if not subscription:
            raise ValueError(f"Subscription {subscription_id} not found")
        
        # Get the plan to determine billing period
        plan = (
            self.db.query(SubscriptionPlan)
            .filter(SubscriptionPlan.id == subscription.plan_id)
            .first()
        )
        
        if not plan:
            raise ValueError(f"Plan {subscription.plan_id} not found")
        
        now = datetime.utcnow()
        previous_status = subscription.status
        
        if payment_confirmed:
            # Extend subscription by one billing period
            if plan.billing_period == "weekly":
                new_renewal_date = subscription.next_renewal_date + timedelta(days=7)
            else:  # monthly
                new_renewal_date = subscription.next_renewal_date + timedelta(days=30)
            
            subscription.next_renewal_date = new_renewal_date
            subscription.current_period_start = subscription.next_renewal_date - timedelta(
                days=7 if plan.billing_period == "weekly" else 30
            )
            subscription.status = "active"
            subscription.grace_period_end = None
            
            # Create renewal event
            event = SubscriptionEvent(
                subscription_id=subscription.id,
                event_type="renewed",
                previous_status=previous_status,
                new_status="active",
                event_metadata={
                    "payment_confirmed": True,
                    "new_renewal_date": new_renewal_date.isoformat(),
                    "renewal_timestamp": now.isoformat()
                }
            )
        else:
            # Enter grace period (3 days from renewal date)
            grace_period_end = subscription.next_renewal_date + timedelta(days=3)
            subscription.status = "grace_period"
            subscription.grace_period_end = grace_period_end
            
            # Create grace period event
            event = SubscriptionEvent(
                subscription_id=subscription.id,
                event_type="grace_period",
                previous_status=previous_status,
                new_status="grace_period",
                event_metadata={
                    "payment_confirmed": False,
                    "grace_period_end": grace_period_end.isoformat(),
                    "entered_grace_period_at": now.isoformat()
                }
            )
        
        self.db.add(event)
        self.db.commit()
        self.db.refresh(subscription)
        
        return subscription

    def cancel_subscription(self, subscription_id: UUID) -> Subscription:
        """Mark subscription for cancellation at end of current billing period.
        
        Args:
            subscription_id: Subscription ID to cancel
            
        Returns:
            Updated subscription record
        """
        from ..db.subscription_models import SubscriptionEvent
        
        # Get the subscription
        subscription = (
            self.db.query(Subscription)
            .filter(Subscription.id == subscription_id)
            .first()
        )
        
        if not subscription:
            raise ValueError(f"Subscription {subscription_id} not found")
        
        now = datetime.utcnow()
        previous_status = subscription.status
        
        # Mark for cancellation at end of billing period
        subscription.cancellation_date = now
        # Status remains active until current period ends
        # (The scheduler will transition to 'cancelled' at next_renewal_date)
        
        # Create cancellation event
        event = SubscriptionEvent(
            subscription_id=subscription.id,
            event_type="cancelled",
            previous_status=previous_status,
            new_status=subscription.status,  # Status doesn't change yet
            event_metadata={
                "cancellation_requested_at": now.isoformat(),
                "will_cancel_at": subscription.next_renewal_date.isoformat() if subscription.next_renewal_date else None,
            }
        )
        
        self.db.add(event)
        self.db.commit()
        self.db.refresh(subscription)
        
        return subscription

    def reactivate(
        self, user_id: UUID, billing_period: BillingPeriod
    ) -> Subscription:
        """Create new active subscription for a previously expired user.
        
        Args:
            user_id: User ID to reactivate
            billing_period: Billing period for new subscription
            
        Returns:
            New subscription record
        """
        from ..db.subscription_models import SubscriptionEvent
        
        # Check for existing active subscription
        existing_active = (
            self.db.query(Subscription)
            .filter(
                Subscription.user_id == user_id,
                Subscription.status.in_(["trial", "active", "overdue", "grace_period"])
            )
            .first()
        )
        
        if existing_active:
            raise ValueError(
                f"User {user_id} already has an active subscription. Cannot reactivate."
            )
        
        # Get Pro plan for the specified billing period
        pro_plan = (
            self.db.query(SubscriptionPlan)
            .filter(
                SubscriptionPlan.name.like("Pro%"),
                SubscriptionPlan.plan_type == "individual",
                SubscriptionPlan.billing_period == billing_period.value,
                SubscriptionPlan.is_active == True
            )
            .first()
        )
        
        if not pro_plan:
            raise ValueError(
                f"Pro plan with billing period '{billing_period.value}' not found in database"
            )
        
        # Calculate next renewal date based on billing period
        now = datetime.utcnow()
        if billing_period == BillingPeriod.WEEKLY:
            next_renewal = now + timedelta(days=7)
        else:  # MONTHLY
            next_renewal = now + timedelta(days=30)
        
        # Create new Pro subscription (preserves history - all exam records remain)
        subscription = Subscription(
            user_id=user_id,
            plan_id=pro_plan.id,
            status="active",
            start_date=now,
            current_period_start=now,
            next_renewal_date=next_renewal,
            trial_duration_days=None,
        )
        
        self.db.add(subscription)
        self.db.flush()  # Flush to get the subscription ID
        
        # Create reactivation event
        event = SubscriptionEvent(
            subscription_id=subscription.id,
            event_type="reactivated",
            previous_status="expired",  # Assuming reactivation from expired state
            new_status="active",
            event_metadata={
                "billing_period": billing_period.value,
                "next_renewal_date": next_renewal.isoformat(),
                "reactivation_timestamp": now.isoformat()
            }
        )
        self.db.add(event)
        
        self.db.commit()
        self.db.refresh(subscription)
        
        return subscription

    def upgrade_trial_to_pro(
        self, user_id: UUID, billing_period: BillingPeriod
    ) -> Subscription:
        """Convert trial to Pro, preserving history.
        
        Args:
            user_id: User ID with trial subscription
            billing_period: Billing period for Pro subscription
            
        Returns:
            Updated subscription record
        """
        from ..db.subscription_models import SubscriptionEvent
        
        # Get the current trial subscription
        trial_subscription = (
            self.db.query(Subscription)
            .filter(
                Subscription.user_id == user_id,
                Subscription.status == "trial"
            )
            .first()
        )
        
        if not trial_subscription:
            raise ValueError(f"No active trial subscription found for user {user_id}")
        
        # Get Pro plan for the specified billing period
        pro_plan = (
            self.db.query(SubscriptionPlan)
            .filter(
                SubscriptionPlan.name.like("Pro%"),
                SubscriptionPlan.plan_type == "individual",
                SubscriptionPlan.billing_period == billing_period.value,
                SubscriptionPlan.is_active == True
            )
            .first()
        )
        
        if not pro_plan:
            raise ValueError(
                f"Pro plan with billing period '{billing_period.value}' not found in database"
            )
        
        # Calculate next renewal date based on billing period
        now = datetime.utcnow()
        if billing_period == BillingPeriod.WEEKLY:
            next_renewal = now + timedelta(days=7)
        else:  # MONTHLY
            next_renewal = now + timedelta(days=30)
        
        previous_status = trial_subscription.status
        
        # Update the trial subscription to Pro
        trial_subscription.plan_id = pro_plan.id
        trial_subscription.status = "active"
        trial_subscription.current_period_start = now
        trial_subscription.next_renewal_date = next_renewal
        trial_subscription.trial_duration_days = None  # No longer a trial
        
        # Create upgrade event
        event = SubscriptionEvent(
            subscription_id=trial_subscription.id,
            event_type="upgraded",
            previous_status=previous_status,
            new_status="active",
            event_metadata={
                "upgraded_from": "trial",
                "upgraded_to": "pro",
                "billing_period": billing_period.value,
                "next_renewal_date": next_renewal.isoformat(),
                "upgrade_timestamp": now.isoformat()
            }
        )
        self.db.add(event)
        
        self.db.commit()
        self.db.refresh(trial_subscription)
        
        return trial_subscription

    def check_pending_renewals(self) -> int:
        """Batch job: process all subscriptions past their renewal date.
        
        Returns:
            Count of subscriptions processed
        """
        # Implementation will be added in subsequent tasks
        raise NotImplementedError(
            "check_pending_renewals will be implemented in Task 3.4"
        )

    def can_change_subscription(self, user_id: UUID) -> tuple[bool, str | None]:
        """Check if user is allowed to change/upgrade their subscription plan.
        
        Business Rules:
        - Free plan users can upgrade to any paid plan (Trial, Monthly, Yearly)
        - Paid plan users (Trial, Monthly, Yearly) CANNOT change until expiry
        - Expired subscriptions can be re-selected
        
        Args:
            user_id: UUID of the user to check
            
        Returns:
            Tuple of (can_change: bool, error_message: str or None)
            - (True, None) if user can change plan
            - (False, error_message) if user has an active PAID subscription
            
        Raises:
            ValueError: If user does not exist
        """
        from ..db.models import User
        
        # Fetch user
        user = self.db.query(User).filter(User.id == user_id).first()
        
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        # Check for active subscription (trial, active, overdue, grace_period)
        active_subscription = (
            self.db.query(Subscription)
            .filter(
                Subscription.user_id == user_id,
                Subscription.status.in_(["trial", "active", "overdue", "grace_period"])
            )
            .first()
        )
        
        if not active_subscription:
            # No active subscription - user can change
            return (True, None)
        
        # Get the plan details to check if it's free or paid
        plan = (
            self.db.query(SubscriptionPlan)
            .filter(SubscriptionPlan.id == active_subscription.plan_id)
            .first()
        )
        
        plan_name = plan.name if plan else "your current plan"
        
        # KEY BUSINESS RULE: Free plan users can upgrade to any paid plan
        if plan and plan.price == 0:
            # Free plan - allow upgrade to paid plans
            return (True, None)
        
        # For PAID plans (Trial, Monthly, Yearly), block until expiry
        # Calculate days remaining
        if active_subscription.next_renewal_date:
            from datetime import datetime as dt
            remaining_days = (active_subscription.next_renewal_date - dt.utcnow()).days
            remaining_days = max(0, remaining_days)
            
            error_msg = (
                f"You have an active {plan_name} subscription. "
                f"Your current subscription expires in {remaining_days} days. "
                f"Please wait for it to expire before selecting a new plan."
            )
        else:
            error_msg = (
                f"You have an active {plan_name} subscription. "
                f"Please wait for it to expire before selecting a new plan."
            )
        
        return (False, error_msg)

    def needs_subscription_selection(self, user_id: UUID) -> bool:
        """Check if user must select a subscription plan via popup.
        
        Returns True ONLY if:
        - user.student_subtype == 'direct_subscriber' AND
        - user has NO active subscription (status NOT IN ['trial', 'active', 'overdue', 'grace_period'])
        
        Returns False for:
        - Institution-linked students (ALWAYS)
        - Any user with an active subscription
        - Non-student users
        
        Args:
            user_id: UUID of the user to check
            
        Returns:
            bool: True if popup should be shown, False otherwise
            
        Raises:
            ValueError: If user does not exist
        """
        from ..db.models import User
        
        # Fetch user
        user = self.db.query(User).filter(User.id == user_id).first()
        
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        # Institution-linked students NEVER see popup
        if user.student_subtype == "institution_linked":
            return False
        
        # Non-direct-subscribers don't see popup (only direct_subscriber)
        if user.student_subtype != "direct_subscriber":
            return False
        
        # Check if user has an active subscription
        active_subscription = (
            self.db.query(Subscription)
            .filter(
                Subscription.user_id == user_id,
                Subscription.status.in_(["trial", "active", "overdue", "grace_period"])
            )
            .first()
        )
        
        # Return True if NO active subscription exists
        return active_subscription is None

    def get_available_plans_for_selection(self) -> list[dict]:
        """Get the 4 subscription plans available for popup selection.
        
        Returns plans in this order:
        1. Free (₹0)
        2. 7-Day Premium Trial (₹99)
        3. Pro Monthly (₹349)
        4. Pro Yearly (₹2,999)
        
        Returns:
            List of plan dicts with id, name, price, and other details
            
        Raises:
            ValueError: If any required plan is not found or inactive
        """
        # Define the expected plans for the popup
        plan_names = [
            "Free",
            "7-Day Premium Trial",
            "Pro Monthly",
            "Pro Yearly"
        ]
        
        # Query all required plans at once
        plans = (
            self.db.query(SubscriptionPlan)
            .filter(
                SubscriptionPlan.name.in_(plan_names),
                SubscriptionPlan.is_active == True
            )
            .all()
        )
        
        # Verify all plans were found
        found_names = {plan.name for plan in plans}
        missing_names = set(plan_names) - found_names
        
        if missing_names:
            raise ValueError(
                f"Required subscription plans not found or inactive: {', '.join(sorted(missing_names))}"
            )
        
        # Sort plans by price to ensure consistent ordering (Free, Trial, Monthly, Yearly)
        plans_sorted = sorted(plans, key=lambda p: (float(p.price), p.name))
        
        # Convert to dict format for API response
        return [
            {
                "id": str(plan.id),
                "name": plan.name,
                "price": float(plan.price),
                "plan_type": plan.plan_type,
                "billing_period": plan.billing_period,
                "max_test_attempts_per_period": plan.max_test_attempts_per_period,
                "is_active": plan.is_active,
            }
            for plan in plans_sorted
        ]


    # ─────────────────────────────────────────────────────────────────────
    # PHASE 2: Subscription Management - Button State Logic
    # ─────────────────────────────────────────────────────────────────────

    def get_subscription_management_status(self, user_id: UUID) -> dict:
        """Get subscription status and button states for plan management page.
        
        Returns current subscription info and the state of each plan button
        (enabled, disabled, or current) based on subscription status.
        
        Used by: GET /api/user/subscription-management
        
        Args:
            user_id: UUID of the user
            
        Returns:
            dict with keys:
            - has_active_subscription: bool
            - current_plan: dict or None (id, name, price, billing_period, is_expired)
            - subscription_status: str or None ('active', 'trial', 'expired', etc.)
            - next_renewal_date: ISO8601 str or None
            - available_plans: list of dicts with button states
            
        Raises:
            ValueError: If user not found
        """
        from ..db.models import User
        
        # Fetch user
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        # Query active subscription
        active_sub = (
            self.db.query(Subscription)
            .filter(
                Subscription.user_id == user_id,
                Subscription.status.in_(["trial", "active", "overdue", "grace_period"])
            )
            .first()
        )
        
        # No subscription → all plans available
        if not active_sub:
            all_plans = self._get_all_individual_plans()
            return {
                "has_active_subscription": False,
                "current_plan": None,
                "subscription_status": None,
                "next_renewal_date": None,
                "available_plans": [
                    self._plan_to_response_dict(plan, "enabled", "Select Plan")
                    for plan in all_plans
                ]
            }
        
        # Get current plan details
        current_plan = (
            self.db.query(SubscriptionPlan)
            .filter(SubscriptionPlan.id == active_sub.plan_id)
            .first()
        )
        
        if not current_plan:
            raise ValueError(f"Plan {active_sub.plan_id} not found")
        
        # Get all plans and calculate button states
        all_plans = self._get_all_individual_plans()
        
        available_plans = []
        for plan in all_plans:
            button_state = self._get_button_state(
                current_plan_name=current_plan.name,
                target_plan_name=plan.name,
                subscription_status=active_sub.status
            )
            button_label = self._get_button_label(button_state)
            
            available_plans.append(
                self._plan_to_response_dict(plan, button_state, button_label)
            )
        
        return {
            "has_active_subscription": True,
            "current_plan": {
                "id": str(current_plan.id),
                "name": current_plan.name,
                "price": float(current_plan.price),
                "billing_period": current_plan.billing_period,
                "is_expired": active_sub.status == "expired"
            },
            "subscription_status": active_sub.status,
            "next_renewal_date": active_sub.next_renewal_date.isoformat() if active_sub.next_renewal_date else None,
            "available_plans": available_plans
        }

    def _get_button_state(
        self,
        current_plan_name: str,
        target_plan_name: str,
        subscription_status: str
    ) -> str:
        """Calculate button state for a plan given current subscription status.
        
        Returns: "enabled", "disabled", or "current"
        
        Logic:
        - Expired/Cancelled: all plans "enabled" (can select fresh)
        - Current plan: always "current" (locked)
        - Trial users: all others "disabled" (cannot switch)
        - Monthly users: all others "disabled" (cannot switch)
        - Yearly users: all others "disabled" (highest tier, locked)
        - Free users: others "enabled" (can upgrade)
        
        Args:
            current_plan_name: Name of user's current plan
            target_plan_name: Name of plan to check
            subscription_status: Status of current subscription
            
        Returns:
            "enabled", "disabled", or "current"
        """
        # Expired/cancelled subscriptions: all plans available
        if subscription_status in ["expired", "cancelled"]:
            return "current" if current_plan_name == target_plan_name else "enabled"
        
        # Current plan: always locked
        if current_plan_name == target_plan_name:
            return "current"
        
        # Trial users: locked to trial (all others disabled)
        if current_plan_name == "7-Day Premium Trial":
            return "disabled"
        
        # Monthly users: locked to monthly (all others disabled)
        if current_plan_name == "Pro Monthly":
            return "disabled"
        
        # Yearly users: locked to yearly (highest tier, all others disabled)
        if current_plan_name == "Pro Yearly":
            return "disabled"
        
        # Free users: others can be selected (enabled)
        if current_plan_name == "Free":
            return "enabled"
        
        # Default: disabled (safety)
        return "disabled"

    def _get_button_label(self, button_state: str) -> str:
        """Get user-facing button label for a button state.
        
        Args:
            button_state: "enabled", "disabled", or "current"
            
        Returns:
            User-friendly label string
        """
        if button_state == "current":
            return "🔒 Current Plan"
        elif button_state == "disabled":
            return "🚫 Locked"
        else:
            return "✅ Select Plan"

    def _get_all_individual_plans(self) -> list[SubscriptionPlan]:
        """Get all 4 individual subscription plans in standard order.
        
        Order: Free, 7-Day Trial, Pro Monthly, Pro Yearly (by price ascending)
        
        Returns:
            List of SubscriptionPlan objects
            
        Raises:
            ValueError: If any required plan not found or not active
        """
        # Define expected plans
        plan_names = [
            "Free",
            "7-Day Premium Trial",
            "Pro Monthly",
            "Pro Yearly"
        ]
        
        # Query all required plans
        plans = (
            self.db.query(SubscriptionPlan)
            .filter(
                SubscriptionPlan.plan_type == "individual",
                SubscriptionPlan.is_active == True,
                SubscriptionPlan.name.in_(plan_names)
            )
            .all()
        )
        
        # Verify all plans were found
        found_names = {plan.name for plan in plans}
        missing_names = set(plan_names) - found_names
        
        if missing_names:
            import logging
            logging.getLogger("smartkcet.subscription").warning(
                f"Some subscription plans not found or inactive: {missing_names}"
            )
        
        # Sort by price to ensure consistent ordering
        return sorted(plans, key=lambda p: (float(p.price), p.name))

    def _plan_to_response_dict(
        self,
        plan: SubscriptionPlan,
        button_state: str,
        button_label: str
    ) -> dict:
        """Convert SubscriptionPlan to API response dict with button state.
        
        Args:
            plan: SubscriptionPlan object
            button_state: "enabled", "disabled", or "current"
            button_label: User-facing label
            
        Returns:
            dict with plan info and button state
        """
        return {
            "id": str(plan.id),
            "name": plan.name,
            "price": float(plan.price),
            "plan_type": plan.plan_type,
            "billing_period": plan.billing_period,
            "button_state": button_state,
            "button_label": button_label,
        }


__all__ = ["SubscriptionService"]
