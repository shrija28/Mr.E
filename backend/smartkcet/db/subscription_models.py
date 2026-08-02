"""SQLAlchemy ORM models for subscription platform upgrade.

This module defines the new tables introduced by the subscription platform
upgrade: institutions, subscription_plans, subscriptions, billing_records,
usage_records, subscription_events, and invitations.

All tables use UUID primary keys and TIMESTAMP columns with server-side
defaults. CHECK constraints are used instead of native ENUMs for portability
between SQLite (development) and PostgreSQL (production).
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    Uuid,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .models import Submission, User


# ---------------------------------------------------------------------------
# INSTITUTIONS
# ---------------------------------------------------------------------------


class Institution(Base):
    """An organizational entity (school, coaching centre, college) that
    purchases a subscription plan to provide platform access to students.
    """

    __tablename__ = "institutions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    institution_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, unique=True)
    contact_phone: Mapped[str] = mapped_column(String(15), nullable=False)
    subscription_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="inactive",
        server_default="inactive",
    )
    registered_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    __table_args__ = (
        CheckConstraint(
            "subscription_status IN ('inactive', 'active', 'overdue', 'grace_period', 'expired')",
            name="ck_institutions_subscription_status",
        ),
    )

    # Relationships
    subscriptions: Mapped[list["Subscription"]] = relationship(
        back_populates="institution",
        foreign_keys="Subscription.institution_id",
    )
    invitations: Mapped[list["Invitation"]] = relationship(
        back_populates="institution",
        cascade="all, delete-orphan",
    )
    usage_records: Mapped[list["UsageRecord"]] = relationship(
        back_populates="institution",
    )


# ---------------------------------------------------------------------------
# SUBSCRIPTION_PLANS
# ---------------------------------------------------------------------------


class SubscriptionPlan(Base):
    """A defined tier of access with specific limits on features, test counts,
    analytics access, and billing period.
    """

    __tablename__ = "subscription_plans"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    plan_type: Mapped[str] = mapped_column(String(20), nullable=False)
    billing_period: Mapped[str] = mapped_column(String(20), nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    max_test_attempts_per_period: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )  # NULL = unlimited
    max_student_seats: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )  # Required for institution plans
    feature_flags: Mapped[Any] = mapped_column(JSON, nullable=False, default=dict)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="1"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    __table_args__ = (
        CheckConstraint(
            "plan_type IN ('individual', 'institution')",
            name="ck_subscription_plans_plan_type",
        ),
        CheckConstraint(
            "billing_period IN ('weekly', 'monthly')",
            name="ck_subscription_plans_billing_period",
        ),
    )

    # Relationships
    subscriptions: Mapped[list["Subscription"]] = relationship(
        back_populates="plan",
    )


# ---------------------------------------------------------------------------
# SUBSCRIPTIONS
# ---------------------------------------------------------------------------


class Subscription(Base):
    """A subscription record for either an individual user or an institution.
    Exactly one of user_id or institution_id must be non-null.
    """

    __tablename__ = "subscriptions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=True
    )
    institution_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid, ForeignKey("institutions.id", ondelete="CASCADE"), nullable=True
    )
    plan_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("subscription_plans.id", ondelete="RESTRICT"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    start_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    current_period_start: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    next_renewal_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )
    cancellation_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )
    grace_period_end: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )
    trial_duration_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('trial', 'active', 'overdue', 'grace_period', 'expired', 'cancelled')",
            name="ck_subscriptions_status",
        ),
        CheckConstraint(
            "(user_id IS NOT NULL AND institution_id IS NULL) OR "
            "(user_id IS NULL AND institution_id IS NOT NULL)",
            name="ck_subscriptions_exactly_one_owner",
        ),
        # Partial unique index: prevent multiple active subscriptions per user
        Index(
            "idx_subscriptions_active_user",
            "user_id",
            unique=True,
            postgresql_where=text(
                "status IN ('trial', 'active', 'overdue', 'grace_period')"
            ),
            sqlite_where=text("status IN ('trial', 'active', 'overdue', 'grace_period')"),
        ),
        # Partial unique index: prevent multiple active subscriptions per institution
        Index(
            "idx_subscriptions_active_institution",
            "institution_id",
            unique=True,
            postgresql_where=text(
                "status IN ('trial', 'active', 'overdue', 'grace_period')"
            ),
            sqlite_where=text("status IN ('trial', 'active', 'overdue', 'grace_period')"),
        ),
    )

    # Relationships
    user: Mapped[Optional["User"]] = relationship(
        back_populates="subscriptions",
        foreign_keys=[user_id],
    )
    institution: Mapped[Optional["Institution"]] = relationship(
        back_populates="subscriptions",
        foreign_keys=[institution_id],
    )
    plan: Mapped["SubscriptionPlan"] = relationship(
        back_populates="subscriptions",
    )
    billing_records: Mapped[list["BillingRecord"]] = relationship(
        back_populates="subscription",
        cascade="all, delete-orphan",
    )
    subscription_events: Mapped[list["SubscriptionEvent"]] = relationship(
        back_populates="subscription",
        cascade="all, delete-orphan",
    )


# ---------------------------------------------------------------------------
# BILLING_RECORDS
# ---------------------------------------------------------------------------


class BillingRecord(Base):
    """A billing transaction record for a subscription, enriched with Razorpay IDs."""

    __tablename__ = "billing_records"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    subscription_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("subscriptions.id", ondelete="CASCADE"), nullable=False
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    # Amount in paise (100 paise = ₹1) — used for Razorpay API calls
    amount_paise: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="INR", server_default="INR")
    billing_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    payment_status: Mapped[str] = mapped_column(String(20), nullable=False)
    payment_method_ref: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    payment_method_type: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    transaction_ref: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    # Razorpay identifiers (set after payment gateway interaction)
    razorpay_order_id:   Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    razorpay_payment_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    razorpay_signature:  Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    plan_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, nullable=True)

    __table_args__ = (
        CheckConstraint(
            "payment_status IN ('paid', 'pending', 'failed', 'created', 'refunded')",
            name="ck_billing_records_payment_status",
        ),
    )

    # Relationships
    subscription: Mapped["Subscription"] = relationship(
        back_populates="billing_records",
    )


# ---------------------------------------------------------------------------
# USAGE_RECORDS
# ---------------------------------------------------------------------------


class UsageRecord(Base):
    """Tracks exam attempts for quota enforcement and analytics."""

    __tablename__ = "usage_records"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    institution_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid, ForeignKey("institutions.id", ondelete="SET NULL"), nullable=True
    )
    submission_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("submissions.id", ondelete="CASCADE"), nullable=False
    )
    subject: Mapped[str] = mapped_column(String(32), nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    billing_period_start: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship(
        back_populates="usage_records",
        foreign_keys=[user_id],
    )
    institution: Mapped[Optional["Institution"]] = relationship(
        back_populates="usage_records",
        foreign_keys=[institution_id],
    )
    submission: Mapped["Submission"] = relationship(
        back_populates="usage_records",
    )


# ---------------------------------------------------------------------------
# SUBSCRIPTION_EVENTS
# ---------------------------------------------------------------------------


class SubscriptionEvent(Base):
    """Audit log of all subscription state transitions."""

    __tablename__ = "subscription_events"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    subscription_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("subscriptions.id", ondelete="CASCADE"), nullable=False
    )
    event_type: Mapped[str] = mapped_column(String(20), nullable=False)
    previous_status: Mapped[str] = mapped_column(String(20), nullable=False)
    new_status: Mapped[str] = mapped_column(String(20), nullable=False)
    event_metadata: Mapped[Any] = mapped_column("metadata", JSON, nullable=False, default=dict)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    __table_args__ = (
        CheckConstraint(
            "event_type IN ('activated', 'renewed', 'overdue', 'grace_period', 'expired', 'cancelled', 'reactivated', 'upgraded')",
            name="ck_subscription_events_event_type",
        ),
    )

    # Relationships
    subscription: Mapped["Subscription"] = relationship(
        back_populates="subscription_events",
    )


# ---------------------------------------------------------------------------
# INVITATIONS
# ---------------------------------------------------------------------------


class Invitation(Base):
    """Institution invitation codes for student onboarding."""

    __tablename__ = "invitations"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    institution_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False
    )
    code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    sequence_number: Mapped[int] = mapped_column(Integer, nullable=False, default=0)  # NEW: Sequential number
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending", server_default="pending"
    )
    consumed_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    consumed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    __table_args__ = (
        UniqueConstraint("code", name="uq_invitations_code"),
        CheckConstraint(
            "status IN ('pending', 'consumed', 'expired')",
            name="ck_invitations_status",
        ),
    )

    # Relationships
    institution: Mapped["Institution"] = relationship(
        back_populates="invitations",
    )
    consumer: Mapped[Optional["User"]] = relationship(
        foreign_keys=[consumed_by],
    )


__all__ = [
    "Institution",
    "SubscriptionPlan",
    "Subscription",
    "BillingRecord",
    "UsageRecord",
    "SubscriptionEvent",
    "Invitation",
    "PaymentLog",
]


# ---------------------------------------------------------------------------
# PAYMENT_LOGS — raw Razorpay event audit trail
# ---------------------------------------------------------------------------


class PaymentLog(Base):
    """Raw Razorpay event log — every order creation, payment, and webhook stored here.

    This is the source-of-truth for payment disputes and reconciliation.
    Subscriptions are only activated AFTER a verified webhook, never from
    frontend-only success callbacks.
    """

    __tablename__ = "payment_logs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    razorpay_order_id:   Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    razorpay_payment_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    entity_type: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # 'institution' | 'user'
    entity_id:   Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, nullable=True)
    subscription_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, nullable=True)
    amount_paise: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="INR", server_default="INR")
    status: Mapped[str] = mapped_column(String(20), nullable=False)  # created|paid|failed|refunded
    raw_payload: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
