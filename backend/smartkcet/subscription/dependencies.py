"""Flask helpers and decorators for subscription-based access control."""

from typing import Any, Callable, Optional
from flask import jsonify, request, g
from sqlalchemy.orm import Session

from ..db.session import get_db
from ..middleware.rbac import current_user
from .access_control import AccessLevel, SubscriptionAccessControl


def get_access_control(db: Session | None = None) -> SubscriptionAccessControl:
    """Get SubscriptionAccessControl instance."""
    db_sess = db if db is not None else get_db()
    return SubscriptionAccessControl(db_sess)


def require_exam_access(req: Any = None, db: Session | None = None) -> Any:
    """Require exam access using effective subscription status."""
    db_sess = db if db is not None else get_db()
    user = current_user(req or request, db_sess)

    if not user:
        return jsonify({"error": "auth_required", "message": "Authentication required"}), 401

    from ..subscription.service import SubscriptionService

    service = SubscriptionService(db_sess)
    try:
        effective = service.get_effective_status(user.id)
    except Exception:
        return jsonify({
            "error": "subscription_verification_failed",
            "message": "Unable to verify subscription status. Please retry.",
            "retry_after_sec": 5,
        }), 503

    if not effective.has_subscription or not effective.is_active:
        return jsonify({"error": "subscription_required", "message": "No active subscription."}), 403

    return {
        "user_id": user.id,
        "quota_type": "institution" if user.student_subtype == "institution_linked"
                       else ("trial" if effective.is_trial else "unlimited"),
    }


def require_full_analytics_access(req: Any = None, db: Session | None = None) -> Any:
    """Require full analytics access (Pro only)."""
    db_sess = db if db is not None else get_db()
    user = current_user(req or request, db_sess)
    
    if not user:
        return jsonify({"error": "auth_required", "message": "Authentication required"}), 401
    
    access_control = SubscriptionAccessControl(db_sess)
    access_result = access_control.check_analytics_access(user.id)
    
    if not access_result.is_granted:
        return jsonify({
            "error": "forbidden",
            "message": access_result.reason,
            "required_tier": "pro",
            "upgrade_url": access_result.upgrade_url,
        }), 403
    
    return {"user_id": user.id}


def require_leaderboard_access(req: Any = None, db: Session | None = None) -> Any:
    """Require leaderboard rank access (Pro only)."""
    db_sess = db if db is not None else get_db()
    user = current_user(req or request, db_sess)
    
    if not user:
        return jsonify({"error": "auth_required", "message": "Authentication required"}), 401
    
    access_control = SubscriptionAccessControl(db_sess)
    access_result = access_control.check_leaderboard_access(user.id)
    
    if not access_result.is_granted:
        return jsonify({
            "error": "forbidden",
            "message": access_result.reason,
            "required_tier": "pro",
            "upgrade_url": access_result.upgrade_url,
        }), 403
    
    return {"user_id": user.id}


__all__ = [
    "get_access_control",
    "require_exam_access",
    "require_full_analytics_access",
    "require_leaderboard_access",
]
