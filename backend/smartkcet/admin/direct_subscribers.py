"""Admin API endpoints for managing direct subscriber students using Flask Blueprint."""

from __future__ import annotations

import logging
from flask import Blueprint, jsonify, request
from sqlalchemy.orm import Session

from ..db.models import User
from ..db.session import get_db
from ..middleware.rbac import require_admin

logger = logging.getLogger("smartkcet.admin.direct_subscribers")

router = Blueprint("admin_direct_subscribers", __name__, url_prefix="/api/admin")


@router.route("/direct-subscribers", methods=["GET"])
@require_admin
def get_direct_subscribers():
    db: Session = get_db()
    try:
        direct_subscribers = (
            db.query(User)
            .filter(User.student_subtype == "direct_subscriber")
            .all()
        )
        
        if not direct_subscribers:
            return jsonify({
                "count": 0,
                "students": [],
                "message": "No direct subscriber students found"
            }), 200

        students_data = []
        for user in direct_subscribers:
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
        
        return jsonify({
            "count": len(students_data),
            "students": students_data,
            "message": f"Found {len(students_data)} direct subscriber student(s)"
        }), 200
        
    except Exception as e:
        logger.error("Error fetching direct subscribers: %s", e)
        return jsonify({"error": "server_error", "message": f"Error fetching direct subscribers: {str(e)}"}), 500


@router.route("/direct-subscribers/unsubscribed", methods=["GET"])
@require_admin
def get_unsubscribed_direct_subscribers():
    db: Session = get_db()
    try:
        from ..db.subscription_models import Subscription
        active_sub_users = (
            db.query(Subscription.user_id)
            .filter(Subscription.status.in_(["trial", "active", "overdue", "grace_period"]))
            .distinct()
        )
        
        unsubscribed = (
            db.query(User)
            .filter(
                User.student_subtype == "direct_subscriber",
                ~User.id.in_(active_sub_users)
            )
            .all()
        )
        
        if not unsubscribed:
            return jsonify({
                "count": 0,
                "students": [],
                "message": "No unsubscribed direct subscriber students found"
            }), 200

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
        
        return jsonify({
            "count": len(students_data),
            "students": students_data,
            "message": f"Found {len(students_data)} unsubscribed direct subscriber student(s)"
        }), 200
        
    except Exception as e:
        logger.error("Error fetching unsubscribed direct subscribers: %s", e)
        return jsonify({"error": "server_error", "message": f"Error fetching unsubscribed students: {str(e)}"}), 500


@router.route("/direct-subscribers/statistics", methods=["GET"])
@require_admin
def get_direct_subscribers_statistics():
    db: Session = get_db()
    try:
        from ..db.subscription_models import Subscription
        total = db.query(User).filter(User.student_subtype == "direct_subscriber").count()
        active_sub_users = (
            db.query(Subscription.user_id)
            .filter(Subscription.status.in_(["trial", "active", "overdue", "grace_period"]))
            .distinct()
        )
        with_subscription = db.query(User).filter(
            User.student_subtype == "direct_subscriber",
            User.id.in_(active_sub_users)
        ).count()

        without_subscription = total - with_subscription

        return jsonify({
            "total_direct_subscribers": total,
            "with_active_subscription": with_subscription,
            "without_subscription": without_subscription,
            "percentage_subscribed": (with_subscription / total * 100) if total > 0 else 0,
            "percentage_needs_popup": (without_subscription / total * 100) if total > 0 else 0,
        }), 200
        
    except Exception as e:
        logger.error("Error fetching statistics: %s", e)
        return jsonify({"error": "server_error", "message": f"Error fetching statistics: {str(e)}"}), 500


__all__ = ["router"]
