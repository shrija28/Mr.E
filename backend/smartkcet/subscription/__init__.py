"""Subscription service module for SmartKCET platform.

This module manages subscription lifecycle for individuals and institutions,
including plan selection, billing, renewal, expiry, grace periods, and
trial conversion.

It also provides access control for subscription-based features:
- Free Trial restrictions (5 exam attempts, basic analytics, hidden leaderboard)
- Pro subscription permissions (unlimited exams, full analytics, leaderboard rank)
"""

from .access_control import (
    AccessCheckResult,
    AccessLevel,
    FeatureAccess,
    SubscriptionAccessControl,
)
from .dependencies import (
    get_access_control,
    require_exam_access,
    require_full_analytics_access,
    require_leaderboard_access,
)
from .models import (
    BillingPeriod,
    EffectiveSubscriptionStatus,
    RemainingAttempts,
    SubscriptionCreate,
    SubscriptionResponse,
    UsageCheckResult,
)
from .routes import router
from .service import SubscriptionService

__all__ = [
    "AccessCheckResult",
    "AccessLevel",
    "BillingPeriod",
    "EffectiveSubscriptionStatus",
    "FeatureAccess",
    "RemainingAttempts",
    "SubscriptionAccessControl",
    "SubscriptionCreate",
    "SubscriptionResponse",
    "SubscriptionService",
    "UsageCheckResult",
    "get_access_control",
    "require_exam_access",
    "require_full_analytics_access",
    "require_leaderboard_access",
    "router",
]

