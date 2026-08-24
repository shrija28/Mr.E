"""Flask routes for subscription management.

Mounted under /api/subscription from smartkcet.main.
"""

import logging
import os
from typing import Any
from flask import Blueprint, jsonify, request
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from sqlalchemy import cast, String
from datetime import datetime as dt

from ..db.session import get_db
from ..middleware.rbac import current_user, require_authenticated
from .service import SubscriptionService

logger = logging.getLogger(__name__)

router = Blueprint("subscription", __name__, url_prefix="/api/subscription")


@router.route("/user/subscription-status", methods=["GET"])
@require_authenticated
def check_subscription_status():
    db: Session = get_db()
    user = current_user(request, db)
    if user is None:
        return jsonify({"error": "auth_required", "message": "User not found"}), 401
    
    service = SubscriptionService(db)
    try:
        needs_popup = service.needs_subscription_selection(user.id)
        available_plans = service.get_available_plans_for_selection()
        
        from ..db.subscription_models import Subscription as SubscriptionModel, SubscriptionPlan
        
        current_subscription = (
            db.query(SubscriptionModel)
            .filter(
                SubscriptionModel.user_id == user.id,
                SubscriptionModel.status.in_(["trial", "active", "overdue", "grace_period"])
            )
            .first()
        )
        
        current_status = current_subscription.status if current_subscription else None
        has_active_subscription = current_subscription is not None
        current_plan_name = None
        days_remaining = None
        
        if current_subscription:
            try:
                plan = (
                    db.query(SubscriptionPlan)
                    .filter(cast(SubscriptionPlan.id, String) == str(current_subscription.plan_id))
                    .first()
                )
                if plan:
                    current_plan_name = plan.name
                if current_subscription.next_renewal_date:
                    remaining = (current_subscription.next_renewal_date - dt.utcnow()).days
                    days_remaining = max(0, remaining)
            except Exception as e:
                logger.warning("Could not get plan details: %s", e)
        
        return jsonify({
            "needs_subscription_selection": needs_popup,
            "student_subtype": user.student_subtype,
            "has_active_subscription": has_active_subscription,
            "current_status": current_status,
            "current_plan_name": current_plan_name,
            "days_remaining": days_remaining,
            "available_plans": available_plans,
        }), 200
    
    except SQLAlchemyError as e:
        logger.error("Database error checking subscription status: %s", e)
        db.rollback()
        return jsonify({
            "error": "service_unavailable",
            "message": "Could not retrieve subscription status. Please retry.",
            "retry_after_sec": 5,
        }), 503


@router.route("/subscription-plans", methods=["GET"])
@require_authenticated
def get_available_plans():
    db: Session = get_db()
    user = current_user(request, db)
    if user is None:
        return jsonify({"error": "auth_required", "message": "User not found"}), 401
    
    service = SubscriptionService(db)
    try:
        plans = service.get_available_plans_for_selection()
        return jsonify(plans), 200
    except SQLAlchemyError as e:
        logger.error("Database error retrieving subscription plans: %s", e)
        db.rollback()
        return jsonify({
            "error": "service_unavailable",
            "message": "Could not retrieve subscription plans. Please retry.",
            "retry_after_sec": 5,
        }), 503


@router.route("/user/subscribe", methods=["POST"])
@require_authenticated
def activate_subscription_plan():
    db: Session = get_db()
    user = current_user(request, db)
    if user is None:
        return jsonify({"error": "auth_required", "message": "User not found"}), 401
    
    data = request.get_json(silent=True) or {}
    plan_type = data.get("plan_type", "free")
    billing_period = data.get("billing_period")

    service = SubscriptionService(db)
    try:
        if not service.needs_subscription_selection(user.id):
            return jsonify({
                "error": "forbidden",
                "message": "User does not require subscription selection",
            }), 403
        
        if plan_type == "trial":
            subscription = service.activate_trial(user.id)
        elif plan_type == "pro":
            if not billing_period:
                return jsonify({
                    "error": "validation_error",
                    "field": "billing_period",
                    "message": "billing_period is required for Pro subscriptions",
                }), 400
            from .models import BillingPeriod
            subscription = service.activate_pro(user.id, BillingPeriod(billing_period))
        else:
            subscription = service.activate_free(user.id)
        
        from .models import SubscriptionResponse
        resp = SubscriptionResponse.model_validate(subscription)
        return jsonify(resp.model_dump(mode="json")), 201
    
    except ValueError as e:
        msg = str(e)
        if "once per account" in msg or "already" in msg.lower():
            return jsonify({"error": "trial_already_used", "message": msg}), 409
        return jsonify({"error": "validation_error", "message": msg}), 400
    except SQLAlchemyError as e:
        db.rollback()
        return jsonify({
            "error": "service_unavailable",
            "message": "Could not complete subscription activation.",
            "retry_after_sec": 5,
        }), 503


@router.route("/select", methods=["POST"])
@require_authenticated
def select_subscription_plan():
    db: Session = get_db()
    user = current_user(request, db)
    if user is None:
        return jsonify({"error": "auth_required", "message": "User not found"}), 401
    
    data = request.get_json(silent=True) or {}
    plan_type = data.get("plan_type", "trial")
    billing_period = data.get("billing_period")
    trial_duration_days = data.get("trial_duration_days", 7)

    service = SubscriptionService(db)
    try:
        if plan_type in ["trial", "pro"]:
            can_change, error_msg = service.can_change_subscription(user.id)
            if not can_change:
                return jsonify({
                    "error": "active_subscription_exists",
                    "message": error_msg,
                }), 409
        
        if plan_type == "trial":
            subscription = service.activate_trial(user.id, trial_duration_days)
        elif plan_type == "pro":
            if not billing_period:
                return jsonify({
                    "error": "validation_error",
                    "field": "billing_period",
                    "message": "billing_period is required for Pro subscriptions",
                }), 400
            from .models import BillingPeriod
            subscription = service.activate_pro(user.id, BillingPeriod(billing_period))
        else:
            return jsonify({
                "error": "validation_error",
                "field": "plan_type",
                "message": f"Invalid plan_type: {plan_type}. Must be 'trial' or 'pro'",
            }), 400
        
        from .models import SubscriptionResponse
        resp = SubscriptionResponse.model_validate(subscription)
        return jsonify(resp.model_dump(mode="json")), 201
    
    except ValueError as e:
        msg = str(e)
        if "once per account" in msg or "already" in msg.lower():
            return jsonify({"error": "trial_already_used", "message": msg}), 409
        return jsonify({"error": "validation_error", "message": msg}), 400
    except SQLAlchemyError as e:
        db.rollback()
        return jsonify({
            "error": "service_unavailable",
            "message": "Could not complete subscription activation.",
            "retry_after_sec": 5,
        }), 503


@router.route("/activate-free", methods=["POST"])
@require_authenticated
def activate_free_plan():
    db: Session = get_db()
    user = current_user(request, db)
    if user is None:
        return jsonify({"error": "auth_required", "message": "User not found"}), 401

    from ..db.subscription_models import Subscription as SubscriptionModel
    ACTIVE_STATUSES = ["trial", "active", "trialing", "grace_period"]

    existing_active = (
        db.query(SubscriptionModel)
        .filter(
            SubscriptionModel.user_id == user.id,
            SubscriptionModel.status.in_(ACTIVE_STATUSES),
        )
        .first()
    )

    if existing_active:
        return jsonify({
            "error": "subscription_active",
            "message": "Current subscription active. Free plan available after expiry.",
        }), 400

    service = SubscriptionService(db)
    try:
        subscription = service.activate_free(user.id)
        from .models import SubscriptionResponse
        resp = SubscriptionResponse.model_validate(subscription)
        return jsonify(resp.model_dump(mode="json")), 201
    except ValueError as e:
        return jsonify({"error": "plan_not_found", "message": str(e)}), 404
    except SQLAlchemyError as e:
        db.rollback()
        return jsonify({"error": "service_unavailable", "message": str(e)}), 503


@router.route("/status", methods=["GET"])
@require_authenticated
def get_subscription_status():
    db: Session = get_db()
    user = current_user(request, db)
    if user is None:
        return jsonify({"error": "auth_required", "message": "User not found"}), 401
    
    service = SubscriptionService(db)
    try:
        effective_status = service.get_effective_status(user.id)
        return jsonify(effective_status.model_dump(mode="json")), 200
    except SQLAlchemyError as e:
        db.rollback()
        return jsonify({"error": "service_unavailable", "message": str(e)}), 503


@router.route("/upgrade", methods=["POST"])
@require_authenticated
def upgrade_subscription():
    db: Session = get_db()
    user = current_user(request, db)
    if user is None:
        return jsonify({"error": "auth_required", "message": "User not found"}), 401
    
    data = request.get_json(silent=True) or {}
    period_str = data.get("billing_period", "monthly")

    service = SubscriptionService(db)
    try:
        dev_mode = os.getenv("SMARTKCET_DEV_MODE", "0") == "1"
        if dev_mode:
            from .models import BillingPeriod
            subscription = service.upgrade_trial_to_pro(user.id, BillingPeriod(period_str))
            from .models import SubscriptionResponse
            resp = SubscriptionResponse.model_validate(subscription)
            return jsonify(resp.model_dump(mode="json")), 200
        else:
            return jsonify({
                "error": "payment_required",
                "message": "Please use the subscription pricing page to upgrade your plan.",
                "redirect": "/subscription",
            }), 402
    except ValueError as e:
        return jsonify({"error": "upgrade_failed", "message": str(e)}), 400
    except SQLAlchemyError as e:
        db.rollback()
        return jsonify({"error": "service_unavailable", "message": str(e)}), 503


@router.route("/cancel", methods=["POST"])
@require_authenticated
def cancel_subscription():
    db: Session = get_db()
    user = current_user(request, db)
    if user is None:
        return jsonify({"error": "auth_required", "message": "User not found"}), 401
    
    service = SubscriptionService(db)
    try:
        from ..db.subscription_models import Subscription
        active_subscription = (
            db.query(Subscription)
            .filter(
                Subscription.user_id == user.id,
                Subscription.status.in_(["trial", "active", "overdue", "grace_period"])
            )
            .first()
        )
        if not active_subscription:
            return jsonify({"error": "subscription_not_found", "message": "No active subscription found to cancel"}), 404
        
        subscription = service.cancel_subscription(active_subscription.id)
        from .models import SubscriptionResponse
        resp = SubscriptionResponse.model_validate(subscription)
        return jsonify(resp.model_dump(mode="json")), 200
    except ValueError as e:
        return jsonify({"error": "cancellation_failed", "message": str(e)}), 400
    except SQLAlchemyError as e:
        db.rollback()
        return jsonify({"error": "service_unavailable", "message": str(e)}), 503


@router.route("/reactivate", methods=["POST"])
@require_authenticated
def reactivate_subscription():
    db: Session = get_db()
    user = current_user(request, db)
    if user is None:
        return jsonify({"error": "auth_required", "message": "User not found"}), 401
    
    data = request.get_json(silent=True) or {}
    period_str = data.get("billing_period", "monthly")

    service = SubscriptionService(db)
    try:
        dev_mode = os.getenv("SMARTKCET_DEV_MODE", "0") == "1"
        if dev_mode:
            from .models import BillingPeriod
            subscription = service.reactivate(user.id, BillingPeriod(period_str))
            from .models import SubscriptionResponse
            resp = SubscriptionResponse.model_validate(subscription)
            return jsonify(resp.model_dump(mode="json")), 201
        else:
            return jsonify({
                "error": "payment_required",
                "message": "Please use the subscription pricing page to reactivate your plan.",
                "redirect": "/subscription",
            }), 402
    except ValueError as e:
        return jsonify({"error": "reactivation_failed", "message": str(e)}), 400
    except SQLAlchemyError as e:
        db.rollback()
        return jsonify({"error": "service_unavailable", "message": str(e)}), 503


@router.route("/user/subscription-management", methods=["GET"])
@require_authenticated
def get_subscription_management_status():
    db: Session = get_db()
    user = current_user(request, db)
    if user is None:
        return jsonify({"error": "auth_required", "message": "User not found"}), 401
    
    service = SubscriptionService(db)
    try:
        management_status = service.get_subscription_management_status(user.id)
        return jsonify(management_status), 200
    except ValueError as e:
        return jsonify({"error": "validation_error", "message": str(e)}), 400
    except SQLAlchemyError as e:
        db.rollback()
        return jsonify({"error": "service_unavailable", "message": str(e)}), 503


@router.route("/remaining-attempts", methods=["GET"])
@require_authenticated
def get_remaining_attempts():
    db: Session = get_db()
    user = current_user(request, db)
    if user is None:
        return jsonify({"error": "auth_required", "message": "User not found"}), 401
    
    from .access_control import SubscriptionAccessControl
    access_control = SubscriptionAccessControl(db)
    try:
        remaining = access_control.get_remaining_attempts(user.id)
        return jsonify(remaining.model_dump(mode="json")), 200
    except SQLAlchemyError as e:
        db.rollback()
        return jsonify({"error": "service_unavailable", "message": str(e)}), 503


__all__ = ["router"]
