"""Access control helpers for Free Trial and Pro subscription features.

This module implements the access restrictions and permission checks for
different subscription tiers as specified in tasks 5.3 and 5.4.

Free Trial restrictions (Task 5.3):
- 5 exam attempt lifetime cap (count only persisted submissions)
- Analytics restricted to basic score display only (total score, pass/fail)
- Leaderboard rank hidden, show upgrade prompt
- Display remaining attempts on dashboard and exam selection
- Allow in-progress exam completion on expiry

Pro subscription permissions (Task 5.4):
- Unlimited exam attempts across all 4 subjects
- Full analytics (topic breakdowns, AI recommendations, trends, comparative analysis)
- Display leaderboard rank with medal indicators (Gold top 10%, Silver top 25%, Bronze top 50%)
- Handle subscription status verification failure (deny exam start with retry prompt)
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from ..db.models import User
from ..db.subscription_models import Subscription, SubscriptionPlan
from .models import EffectiveSubscriptionStatus, SubscriptionStatus
from .usage import UsageTracker


class FeatureAccess(str, Enum):
    """Feature access levels for different subscription tiers."""
    
    EXAM_START = "exam_start"
    BASIC_ANALYTICS = "basic_analytics"
    FULL_ANALYTICS = "full_analytics"
    LEADERBOARD_RANK = "leaderboard_rank"
    LEADERBOARD_MEDALS = "leaderboard_medals"


class AccessLevel(str, Enum):
    """Access level for a feature."""
    
    GRANTED = "granted"
    DENIED = "denied"
    UPGRADE_REQUIRED = "upgrade_required"


class AccessCheckResult:
    """Result of an access control check."""
    
    def __init__(
        self,
        access: AccessLevel,
        reason: Optional[str] = None,
        remaining_attempts: Optional[int] = None,
        upgrade_url: Optional[str] = None,
    ):
        self.access = access
        self.reason = reason
        self.remaining_attempts = remaining_attempts
        self.upgrade_url = upgrade_url
    
    @property
    def is_granted(self) -> bool:
        """Check if access is granted."""
        return self.access == AccessLevel.GRANTED
    
    @property
    def requires_upgrade(self) -> bool:
        """Check if upgrade is required."""
        return self.access == AccessLevel.UPGRADE_REQUIRED


class SubscriptionAccessControl:
    """Access control service for subscription-based features.
    
    This service implements the access control matrix defined in the design
    document, enforcing Free Trial restrictions and Pro subscription permissions.
    
    **Requirements:** 2.1, 2.2, 2.3, 2.4, 2.6, 2.9, 3.1, 3.2, 3.3, 3.8
    """
    
    def __init__(self, db: Session):
        """Initialize the access control service.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self.usage_tracker = UsageTracker(db)
    
    def check_exam_access(self, user_id: UUID) -> AccessCheckResult:
        """Check if user can start an exam.
        
        Implements Task 5.3 (Free Trial restrictions) and Task 5.4 (Pro permissions).
        
        Free Trial:
        - Enforce 5 exam attempt lifetime cap
        - Count only persisted submissions
        - Display remaining attempts
        
        Pro:
        - Grant unlimited exam attempts
        - Handle subscription verification failure
        
        **Requirements:** 2.1, 2.6, 2.9, 3.1, 3.8
        
        Args:
            user_id: User ID to check access for
            
        Returns:
            AccessCheckResult indicating whether exam access is granted
        """
        # Use the usage tracker to check quota
        usage_result = self.usage_tracker.can_start_exam(user_id)
        
        if not usage_result.can_start:
            # Determine if this is a quota issue or subscription issue
            if "subscription" in usage_result.reason.lower():
                # Subscription verification failure
                return AccessCheckResult(
                    access=AccessLevel.DENIED,
                    reason="Unable to verify subscription status. Please retry.",
                    upgrade_url=None,
                )
            elif "trial" in usage_result.reason.lower() or "limit" in usage_result.reason.lower():
                # Trial limit reached - upgrade required
                return AccessCheckResult(
                    access=AccessLevel.UPGRADE_REQUIRED,
                    reason=usage_result.reason,
                    remaining_attempts=0,
                    upgrade_url="/api/subscription/upgrade",
                )
            else:
                # Other denial reason (institution quota, etc.)
                return AccessCheckResult(
                    access=AccessLevel.DENIED,
                    reason=usage_result.reason,
                    remaining_attempts=usage_result.remaining_attempts,
                )
        
        # Access granted
        return AccessCheckResult(
            access=AccessLevel.GRANTED,
            reason=None,
            remaining_attempts=usage_result.remaining_attempts,
        )
    
    def check_analytics_access(self, user_id: UUID) -> AccessCheckResult:
        """Check analytics access level for user.
        
        Implements Task 5.3 (Free Trial restrictions) and Task 5.4 (Pro permissions).
        
        Free Trial:
        - Restrict to basic score display only (total score, pass/fail)
        - Hide detailed topic breakdowns, AI recommendations, trends
        
        Pro:
        - Grant full analytics access
        - Include topic breakdowns, AI recommendations, trends, comparative analysis
        
        **Requirements:** 2.2, 3.2
        
        Args:
            user_id: User ID to check access for
            
        Returns:
            AccessCheckResult indicating analytics access level
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        
        if not user:
            return AccessCheckResult(
                access=AccessLevel.DENIED,
                reason="User not found",
            )
        
        # Get active subscription
        subscription = (
            self.db.query(Subscription)
            .filter(
                Subscription.user_id == user_id,
                Subscription.status.in_(["trial", "active", "grace_period"])
            )
            .first()
        )
        
        if not subscription:
            return AccessCheckResult(
                access=AccessLevel.DENIED,
                reason="No active subscription",
                upgrade_url="/api/subscription/select",
            )
        
        # Free Trial: basic analytics only
        if subscription.status == "trial":
            return AccessCheckResult(
                access=AccessLevel.UPGRADE_REQUIRED,
                reason="Full analytics require Pro subscription. Upgrade to access topic breakdowns, AI recommendations, and performance trends.",
                upgrade_url="/api/subscription/upgrade",
            )
        
        # Pro subscription: full analytics
        plan = (
            self.db.query(SubscriptionPlan)
            .filter(SubscriptionPlan.id == subscription.plan_id)
            .first()
        )
        
        if plan and plan.plan_type == "individual" and subscription.status in ["active", "grace_period"]:
            return AccessCheckResult(
                access=AccessLevel.GRANTED,
                reason=None,
            )
        
        # Default: basic analytics only
        return AccessCheckResult(
            access=AccessLevel.UPGRADE_REQUIRED,
            reason="Full analytics require Pro subscription",
            upgrade_url="/api/subscription/upgrade",
        )
    
    def check_leaderboard_access(self, user_id: UUID) -> AccessCheckResult:
        """Check leaderboard access level for user.
        
        Implements Task 5.3 (Free Trial restrictions) and Task 5.4 (Pro permissions).
        
        Free Trial:
        - Hide leaderboard rank
        - Show upgrade prompt
        
        Pro:
        - Display leaderboard rank
        - Show medal indicators (Gold top 10%, Silver top 25%, Bronze top 50%)
        
        **Requirements:** 2.3, 3.3
        
        Args:
            user_id: User ID to check access for
            
        Returns:
            AccessCheckResult indicating leaderboard access level
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        
        if not user:
            return AccessCheckResult(
                access=AccessLevel.DENIED,
                reason="User not found",
            )
        
        # Get active subscription
        subscription = (
            self.db.query(Subscription)
            .filter(
                Subscription.user_id == user_id,
                Subscription.status.in_(["trial", "active", "grace_period"])
            )
            .first()
        )
        
        if not subscription:
            return AccessCheckResult(
                access=AccessLevel.DENIED,
                reason="No active subscription",
                upgrade_url="/api/subscription/select",
            )
        
        # Free Trial: hide rank, show upgrade prompt
        if subscription.status == "trial":
            return AccessCheckResult(
                access=AccessLevel.UPGRADE_REQUIRED,
                reason="Leaderboard rank requires Pro subscription. Upgrade to see your ranking and compete for medals.",
                upgrade_url="/api/subscription/upgrade",
            )
        
        # Pro subscription: show rank and medals
        plan = (
            self.db.query(SubscriptionPlan)
            .filter(SubscriptionPlan.id == subscription.plan_id)
            .first()
        )
        
        if plan and plan.plan_type == "individual" and subscription.status in ["active", "grace_period"]:
            return AccessCheckResult(
                access=AccessLevel.GRANTED,
                reason=None,
            )
        
        # Default: hide rank
        return AccessCheckResult(
            access=AccessLevel.UPGRADE_REQUIRED,
            reason="Leaderboard rank requires Pro subscription",
            upgrade_url="/api/subscription/upgrade",
        )
    
    def get_remaining_attempts(self, user_id: UUID) -> dict:
        """Get remaining exam attempts for display on dashboard.
        
        Implements Task 5.3 requirement to display remaining attempts.
        
        **Requirements:** 2.4
        
        Args:
            user_id: User ID to query
            
        Returns:
            Dictionary with remaining attempts information
        """
        remaining = self.usage_tracker.get_remaining_attempts(user_id)
        
        return {
            "total_attempts": remaining.total_attempts,
            "max_attempts": remaining.max_attempts,
            "remaining_attempts": remaining.remaining_attempts,
            "is_unlimited": remaining.is_unlimited,
            "period_start": remaining.period_start.isoformat() if remaining.period_start else None,
            "period_end": remaining.period_end.isoformat() if remaining.period_end else None,
        }
    
    def calculate_medal_tier(self, rank: int, total_ranked: int) -> Optional[str]:
        """Calculate medal tier based on rank percentile.
        
        Implements Task 5.4 medal indicators for Pro subscribers.
        
        Medal tiers:
        - Gold: Top 10%
        - Silver: Top 25%
        - Bronze: Top 50%
        - None: Below top 50%
        
        **Requirements:** 3.3
        
        Args:
            rank: User's rank (1-indexed)
            total_ranked: Total number of ranked users
            
        Returns:
            Medal tier string or None
        """
        if total_ranked == 0:
            return None
        
        percentile = (rank / total_ranked) * 100
        
        if percentile <= 10:
            return "gold"
        elif percentile <= 25:
            return "silver"
        elif percentile <= 50:
            return "bronze"
        else:
            return None
    
    def filter_analytics_data(self, analytics_data: dict, user_id: UUID) -> dict:
        """Filter analytics data based on subscription tier.
        
        Implements Task 5.3 analytics restrictions for Free Trial users.
        
        Free Trial: Return only basic score display (total score, pass/fail)
        Pro: Return full analytics data unchanged
        
        **Requirements:** 2.2, 3.2
        
        Args:
            analytics_data: Full analytics data dictionary
            user_id: User ID to check subscription for
            
        Returns:
            Filtered analytics data based on subscription tier
        """
        access_result = self.check_analytics_access(user_id)
        
        if access_result.is_granted:
            # Pro subscription: return full analytics
            return analytics_data
        
        # Free Trial: return only basic score display
        return {
            "score_pct": analytics_data.get("score_pct"),
            "pass_flag": analytics_data.get("pass_flag"),
            "submitted_at": analytics_data.get("submitted_at"),
            "subject": analytics_data.get("subject"),
            "upgrade_required": True,
            "upgrade_url": access_result.upgrade_url,
            "upgrade_message": access_result.reason,
        }
    
    def filter_leaderboard_data(self, leaderboard_data: dict, user_id: UUID) -> dict:
        """Filter leaderboard data based on subscription tier.
        
        Implements Task 5.3 leaderboard restrictions for Free Trial users.
        
        Free Trial: Hide rank, show upgrade prompt
        Pro: Show rank and medal indicators
        
        **Requirements:** 2.3, 3.3
        
        Args:
            leaderboard_data: Full leaderboard data dictionary
            user_id: User ID to check subscription for
            
        Returns:
            Filtered leaderboard data based on subscription tier
        """
        access_result = self.check_leaderboard_access(user_id)
        
        if access_result.is_granted:
            # Pro subscription: return full leaderboard with medals
            my_rank = leaderboard_data.get("my_rank")
            total_ranked = leaderboard_data.get("total_ranked", 0)
            
            # Add medal tier if applicable
            if isinstance(my_rank, int):
                medal = self.calculate_medal_tier(my_rank, total_ranked)
                leaderboard_data["medal"] = medal
            
            return leaderboard_data
        
        # Free Trial: hide rank, show upgrade prompt
        return {
            "my_rank": "—",  # em-dash for hidden
            "total_ranked": leaderboard_data.get("total_ranked", 0),
            "top_3": leaderboard_data.get("top_3", []),
            "me": None,
            "upgrade_required": True,
            "upgrade_url": access_result.upgrade_url,
            "upgrade_message": access_result.reason,
        }


__all__ = [
    "AccessCheckResult",
    "AccessLevel",
    "FeatureAccess",
    "SubscriptionAccessControl",
]
