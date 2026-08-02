"""FastAPI dependencies for subscription-based access control.

This module provides dependency functions that can be used in route handlers
to enforce subscription-based access restrictions.
"""

from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from ..db.session import get_async_session as get_session
from ..middleware.rbac import current_user
from .access_control import AccessLevel, SubscriptionAccessControl


def require_exam_access(
    request: Request,
    db: Session = Depends(get_session),
) -> dict:
    """Dependency to require exam access using effective subscription status.

    Correctly handles both personal and institution students:
    - Personal students: check their own subscription (trial/pro)
    - Institution students: check their institution's subscription

    Uses ``SubscriptionService.get_effective_status()`` which delegates
    to the institution subscription for institution-linked students.

    Raises HTTPException if access is denied.
    """
    user = current_user(request, db)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "auth_required",
                "message": "Authentication required",
            },
        )

    # Use effective status — works for both personal and institution students
    from ..subscription.service import SubscriptionService

    service = SubscriptionService(db)
    try:
        effective = service.get_effective_status(user.id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "subscription_verification_failed",
                "message": "Unable to verify subscription status. Please retry.",
                "retry_after_sec": 5,
            },
        )

    if not effective.has_subscription or not effective.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "subscription_required",
                "message": "No active subscription.",
            },
        )

    # For institution students and pro users just pass through.
    # Trial quota is enforced at /api/exam/check-access before exam starts.
    return {
        "user_id": user.id,
        "quota_type": "institution" if user.student_subtype == "institution_linked"
                       else ("trial" if effective.is_trial else "unlimited"),
    }


def require_full_analytics_access(
    request: Request,
    db: Session = Depends(get_session),
) -> dict:
    """Dependency to require full analytics access (Pro only).
    
    Checks if the authenticated user has permission to view full analytics:
    - Free Trial: Denied (basic analytics only)
    - Pro: Granted (full analytics with topic breakdowns, AI recommendations, trends)
    
    Raises HTTPException if access is denied.
    
    **Requirements:** 2.2, 3.2
    
    Args:
        request: FastAPI request object
        db: Database session
        
    Returns:
        Dictionary with access information
        
    Raises:
        HTTPException: 403 if access denied (upgrade required)
    """
    user = current_user(request, db)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "auth_required",
                "message": "Authentication required",
            },
        )
    
    access_control = SubscriptionAccessControl(db)
    access_result = access_control.check_analytics_access(user.id)
    
    if not access_result.is_granted:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "forbidden",
                "message": access_result.reason,
                "required_tier": "pro",
                "upgrade_url": access_result.upgrade_url,
            },
        )
    
    return {
        "user_id": user.id,
    }


def require_leaderboard_access(
    request: Request,
    db: Session = Depends(get_session),
) -> dict:
    """Dependency to require leaderboard rank access (Pro only).
    
    Checks if the authenticated user has permission to view leaderboard rank:
    - Free Trial: Denied (rank hidden, upgrade prompt shown)
    - Pro: Granted (rank and medal indicators shown)
    
    Raises HTTPException if access is denied.
    
    **Requirements:** 2.3, 3.3
    
    Args:
        request: FastAPI request object
        db: Database session
        
    Returns:
        Dictionary with access information
        
    Raises:
        HTTPException: 403 if access denied (upgrade required)
    """
    user = current_user(request, db)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "auth_required",
                "message": "Authentication required",
            },
        )
    
    access_control = SubscriptionAccessControl(db)
    access_result = access_control.check_leaderboard_access(user.id)
    
    if not access_result.is_granted:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "forbidden",
                "message": access_result.reason,
                "required_tier": "pro",
                "upgrade_url": access_result.upgrade_url,
            },
        )
    
    return {
        "user_id": user.id,
    }


def get_access_control(db: Session = Depends(get_session)) -> SubscriptionAccessControl:
    """Dependency to get SubscriptionAccessControl instance.
    
    Provides access to the access control service for manual checks in route handlers.
    
    Args:
        db: Database session
        
    Returns:
        SubscriptionAccessControl instance
    """
    return SubscriptionAccessControl(db)


__all__ = [
    "get_access_control",
    "require_exam_access",
    "require_full_analytics_access",
    "require_leaderboard_access",
]
