"""Pydantic schemas for subscription service API request/response.

This module defines the data transfer objects (DTOs) used by the subscription
service for API interactions, validation, and serialization.
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class BillingPeriod(str, Enum):
    """Billing period for subscriptions."""

    WEEKLY = "weekly"
    MONTHLY = "monthly"


class SubscriptionStatus(str, Enum):
    """Subscription status values."""

    TRIAL = "trial"
    ACTIVE = "active"
    OVERDUE = "overdue"
    GRACE_PERIOD = "grace_period"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class PlanType(str, Enum):
    """Subscription plan type."""

    INDIVIDUAL = "individual"
    INSTITUTION = "institution"


# ---------------------------------------------------------------------------
# Request Schemas
# ---------------------------------------------------------------------------


class SubscriptionCreate(BaseModel):
    """Request schema for creating a new subscription.
    
    Used when a student selects a subscription plan (Free Trial or Pro).
    """

    plan_type: str = Field(
        ...,
        description="Type of subscription: 'trial' or 'pro'",
        pattern="^(trial|pro)$",
    )
    billing_period: Optional[BillingPeriod] = Field(
        None,
        description="Billing period (required for Pro subscriptions)",
    )
    trial_duration_days: Optional[int] = Field(
        None,
        ge=1,
        le=90,
        description="Trial duration in days (1-90, default 7 for trial subscriptions)",
    )

    @field_validator("billing_period")
    @classmethod
    def validate_billing_period_for_pro(cls, v, info):
        """Ensure billing_period is provided for Pro subscriptions."""
        if info.data.get("plan_type") == "pro" and v is None:
            raise ValueError("billing_period is required for Pro subscriptions")
        if info.data.get("plan_type") == "trial" and v is not None:
            raise ValueError("billing_period should not be provided for trial subscriptions")
        return v

    @field_validator("trial_duration_days")
    @classmethod
    def validate_trial_duration(cls, v, info):
        """Ensure trial_duration_days is only provided for trial subscriptions."""
        if info.data.get("plan_type") != "trial" and v is not None:
            raise ValueError("trial_duration_days should only be provided for trial subscriptions")
        return v


class SubscriptionUpgrade(BaseModel):
    """Request schema for upgrading from trial to Pro."""

    billing_period: BillingPeriod = Field(
        ...,
        description="Billing period for the Pro subscription",
    )


class SubscriptionReactivate(BaseModel):
    """Request schema for reactivating an expired/cancelled subscription."""

    billing_period: BillingPeriod = Field(
        ...,
        description="Billing period for the reactivated subscription",
    )


# ---------------------------------------------------------------------------
# Response Schemas
# ---------------------------------------------------------------------------


class SubscriptionResponse(BaseModel):
    """Response schema for subscription details.
    
    Returned when querying or creating a subscription.
    """

    id: UUID
    user_id: Optional[UUID] = None
    institution_id: Optional[UUID] = None
    plan_id: UUID
    status: SubscriptionStatus
    start_date: datetime
    current_period_start: datetime
    next_renewal_date: Optional[datetime] = None
    cancellation_date: Optional[datetime] = None
    grace_period_end: Optional[datetime] = None
    trial_duration_days: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EffectiveSubscriptionStatus(BaseModel):
    """Effective subscription status for a user.
    
    Provides a single-query result containing all subscription-related
    information needed for access control decisions.
    """

    has_subscription: bool = Field(
        ...,
        description="Whether the user has any subscription record",
    )
    status: Optional[SubscriptionStatus] = Field(
        None,
        description="Current subscription status (null if no subscription)",
    )
    plan_type: Optional[PlanType] = Field(
        None,
        description="Type of subscription plan (individual or institution)",
    )
    plan_name: Optional[str] = Field(
        None,
        description="Name of the subscription plan (e.g., '7-Day Premium Trial', 'Pro Monthly')",
    )
    billing_period: Optional[BillingPeriod] = Field(
        None,
        description="Billing period (weekly or monthly)",
    )
    is_trial: bool = Field(
        default=False,
        description="Whether this is a trial subscription",
    )
    is_active: bool = Field(
        default=False,
        description="Whether the subscription grants active access (trial, active, or grace_period)",
    )
    trial_attempts_remaining: Optional[int] = Field(
        None,
        description="Remaining exam attempts for trial users (null for non-trial)",
    )
    start_date: Optional[datetime] = Field(
        None,
        description="Subscription start date",
    )
    current_period_start: Optional[datetime] = Field(
        None,
        description="Current billing period start date",
    )
    next_renewal_date: Optional[datetime] = Field(
        None,
        description="Next renewal date (null for trial or expired)",
    )
    grace_period_end: Optional[datetime] = Field(
        None,
        description="Grace period end date (null if not in grace period)",
    )
    institution_id: Optional[UUID] = Field(
        None,
        description="Institution ID for institution-linked subscriptions",
    )
    institution_name: Optional[str] = Field(
        None,
        description="Institution name for institution-linked subscriptions",
    )


class RemainingAttempts(BaseModel):
    """Remaining exam attempts for a user.
    
    Used for dashboard display and quota enforcement.
    """

    total_attempts: int = Field(
        ...,
        description="Total exam attempts made by the user",
    )
    max_attempts: Optional[int] = Field(
        None,
        description="Maximum allowed attempts (null for unlimited)",
    )
    remaining_attempts: Optional[int] = Field(
        None,
        description="Remaining attempts (null for unlimited)",
    )
    is_unlimited: bool = Field(
        default=False,
        description="Whether the user has unlimited attempts",
    )
    period_start: Optional[datetime] = Field(
        None,
        description="Start of the current billing period (for institution plans)",
    )
    period_end: Optional[datetime] = Field(
        None,
        description="End of the current billing period (for institution plans)",
    )


class UsageCheckResult(BaseModel):
    """Result of a usage quota check.
    
    Returned by the usage tracker when checking if a user can start an exam.
    """

    can_start: bool = Field(
        ...,
        description="Whether the user can start an exam",
    )
    reason: Optional[str] = Field(
        None,
        description="Reason for denial (if can_start is False)",
    )
    remaining_attempts: Optional[int] = Field(
        None,
        description="Remaining attempts (null for unlimited)",
    )
    quota_type: Optional[str] = Field(
        None,
        description="Type of quota enforced: 'trial', 'institution_weekly', 'institution_monthly', 'unlimited'",
    )
    resets_at: Optional[datetime] = Field(
        None,
        description="When the quota resets (for institution plans)",
    )


# ---------------------------------------------------------------------------
# Plan Schemas
# ---------------------------------------------------------------------------


class SubscriptionPlanResponse(BaseModel):
    """Response schema for subscription plan details."""

    id: UUID
    name: str
    plan_type: PlanType
    billing_period: BillingPeriod
    price: float
    max_test_attempts_per_period: Optional[int] = Field(
        None,
        description="Maximum test attempts per period (null for unlimited)",
    )
    max_student_seats: Optional[int] = Field(
        None,
        description="Maximum student seats (for institution plans)",
    )
    feature_flags: dict = Field(
        default_factory=dict,
        description="Feature flags for the plan",
    )
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


__all__ = [
    "BillingPeriod",
    "EffectiveSubscriptionStatus",
    "PlanType",
    "RemainingAttempts",
    "SubscriptionCreate",
    "SubscriptionPlanResponse",
    "SubscriptionReactivate",
    "SubscriptionResponse",
    "SubscriptionStatus",
    "SubscriptionUpgrade",
    "UsageCheckResult",
]
