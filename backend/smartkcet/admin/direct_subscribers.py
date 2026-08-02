"""Admin API endpoints for managing direct subscriber students."""

from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..db.models import User
from ..db.session import get_async_session as get_session
from ..middleware.rbac import require_admin

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/direct-subscribers")
async def get_direct_subscribers(
    db: Session = Depends(get_session),
    _: Annotated[dict, Depends(require_admin)] = None,
):
    """Get all direct subscriber students (admin only).
    
    Returns list of students registered as personal/direct subscribers
    with their subscription status.
    """
    try:
        # Query all direct subscriber students
        direct_subscribers = (
            db.query(User)
            .filter(User.student_subtype == "direct_subscriber")
            .all()
        )
        
        if not direct_subscribers:
            return {
                "count": 0,
                "students": [],
                "message": "No direct subscriber students found"
            }
        
        # Build response with subscription info
        students_data = []
        for user in direct_subscribers:
            # Get subscription info
            from ..db.subscription_models import Subscription
            subscription = (
                db.query(Subscription)
                .filter(
                    Subscription.user_id == user.id,
                    Subscription.status.in_(["trial", "active", "overdue", "grace_period"])
                )
                .first()
            )
            
            students_data.append({
                "id": str(user.id),
                "kcet_student_id": user.kcet_student_id,
                "name": user.display_name,
                "email": user.email,
                "student_subtype": user.student_subtype,
                "has_active_subscription": subscription is not None,
                "subscription_status": subscription.status if subscription else "no_subscription",
                "created_at": user.created_at.isoformat() if user.created_at else None,
            })
        
        return {
            "count": len(students_data),
            "students": students_data,
            "message": f"Found {len(students_data)} direct subscriber student(s)"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching direct subscribers: {str(e)}"
        )


@router.get("/direct-subscribers/unsubscribed")
async def get_unsubscribed_direct_subscribers(
    db: Session = Depends(get_session),
    _: Annotated[dict, Depends(require_admin)] = None,
):
    """Get direct subscriber students WITHOUT active subscriptions (admin only).
    
    These students will see the subscription popup on next login.
    """
    try:
        # Query direct subscribers without active subscriptions
        from ..db.subscription_models import Subscription
        
        # Subquery for users with active subscriptions
        active_sub_users = (
            db.query(Subscription.user_id)
            .filter(Subscription.status.in_(["trial", "active", "overdue", "grace_period"]))
            .distinct()
        )
        
        # Get direct subscribers without active subscriptions
        unsubscribed = (
            db.query(User)
            .filter(
                User.student_subtype == "direct_subscriber",
                ~User.id.in_(active_sub_users)
            )
            .all()
        )
        
        if not unsubscribed:
            return {
                "count": 0,
                "students": [],
                "message": "No unsubscribed direct subscriber students found"
            }
        
        students_data = []
        for user in unsubscribed:
            students_data.append({
                "id": str(user.id),
                "kcet_student_id": user.kcet_student_id,
                "name": user.display_name,
                "email": user.email,
                "student_subtype": user.student_subtype,
                "status": "needs_subscription",
                "created_at": user.created_at.isoformat() if user.created_at else None,
            })
        
        return {
            "count": len(students_data),
            "students": students_data,
            "message": f"Found {len(students_data)} unsubscribed direct subscriber student(s) - they will see popup on next login"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching unsubscribed students: {str(e)}"
        )


@router.get("/direct-subscribers/statistics")
async def get_direct_subscribers_statistics(
    db: Session = Depends(get_session),
    _: Annotated[dict, Depends(require_admin)] = None,
):
    """Get statistics about direct subscriber students (admin only)."""
    try:
        from ..db.subscription_models import Subscription
        
        # Total direct subscribers
        total = db.query(User).filter(User.student_subtype == "direct_subscriber").count()
        
        # With active subscriptions
        active_sub_users = (
            db.query(Subscription.user_id)
            .filter(Subscription.status.in_(["trial", "active", "overdue", "grace_period"]))
            .distinct()
        )
        with_subscription = db.query(User).filter(
            User.student_subtype == "direct_subscriber",
            User.id.in_(active_sub_users)
        ).count()
        
        # Without subscriptions (will see popup)
        without_subscription = total - with_subscription
        
        return {
            "total_direct_subscribers": total,
            "with_active_subscription": with_subscription,
            "without_subscription": without_subscription,
            "percentage_subscribed": (with_subscription / total * 100) if total > 0 else 0,
            "percentage_needs_popup": (without_subscription / total * 100) if total > 0 else 0,
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching statistics: {str(e)}"
        )
