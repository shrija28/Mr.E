"""Payment gateway API routes using Flask Blueprint."""

from __future__ import annotations

import json
import logging
import time
import uuid
from collections import defaultdict
from typing import Any

from flask import Blueprint, jsonify, request
from sqlalchemy.orm import Session

from ..db.session import get_db
from ..db.subscription_models import SubscriptionPlan
from ..middleware.rbac import current_user, require_authenticated
from . import gateway
from .service import (
    create_institution_order,
    create_student_order,
    get_institution_payment_history,
    get_student_payment_history,
    handle_refund_webhook,
)

logger = logging.getLogger("smartkcet.payments.routes")

router = Blueprint("payments", __name__, url_prefix="/api/payments")

_rate_store: dict[str, list[float]] = defaultdict(list)
_RATE_WINDOW = 60
_RATE_MAX_REQ = 5


def _check_rate_limit():
    ip = request.remote_addr or "unknown"
    now = time.monotonic()
    _rate_store[ip] = [t for t in _rate_store[ip] if now - t < _RATE_WINDOW]
    if len(_rate_store[ip]) >= _RATE_MAX_REQ:
        res = jsonify({
            "error": "rate_limited",
            "message": f"Too many order creation requests. Please wait {_RATE_WINDOW}s.",
            "retry_after": _RATE_WINDOW,
        })
        res.headers["Retry-After"] = str(_RATE_WINDOW)
        return res, 429
    _rate_store[ip].append(now)
    return None


def _serialize_plan(p: SubscriptionPlan) -> dict:
    return {
        "id": str(p.id),
        "name": p.name,
        "plan_type": p.plan_type,
        "billing_period": p.billing_period,
        "price": float(p.price),
        "price_paise": int(float(p.price) * 100),
        "max_student_seats": p.max_student_seats,
        "max_test_attempts_per_period": p.max_test_attempts_per_period,
        "feature_flags": p.feature_flags or {},
        "is_active": p.is_active,
    }


@router.route("/plans", methods=["GET"])
def list_plans():
    db: Session = get_db()
    plans = (
        db.query(SubscriptionPlan)
        .filter(SubscriptionPlan.is_active.is_(True))
        .order_by(SubscriptionPlan.plan_type, SubscriptionPlan.price.asc())
        .all()
    )
    return jsonify({
        "plans": [_serialize_plan(p) for p in plans],
        "key_id": gateway.get_public_key(),
        "gateway_configured": gateway.is_configured(),
    }), 200


@router.route("/plans/student", methods=["GET"])
def list_student_plans():
    db: Session = get_db()
    plans = (
        db.query(SubscriptionPlan)
        .filter(
            SubscriptionPlan.plan_type == "individual",
            SubscriptionPlan.is_active.is_(True),
        )
        .order_by(SubscriptionPlan.price.asc())
        .all()
    )
    return jsonify({
        "plans": [_serialize_plan(p) for p in plans],
        "key_id": gateway.get_public_key(),
        "gateway_configured": gateway.is_configured(),
    }), 200


@router.route("/plans/institution", methods=["GET"])
def list_institution_plans():
    db: Session = get_db()
    plans = (
        db.query(SubscriptionPlan)
        .filter(
            SubscriptionPlan.plan_type == "institution",
            SubscriptionPlan.is_active.is_(True),
        )
        .order_by(SubscriptionPlan.price.asc())
        .all()
    )
    return jsonify({
        "plans": [_serialize_plan(p) for p in plans],
        "key_id": gateway.get_public_key(),
        "gateway_configured": gateway.is_configured(),
    }), 200


@router.route("/create-order", methods=["POST"])
@require_authenticated
def create_order():
    rate_res = _check_rate_limit()
    if rate_res:
        return rate_res

    db: Session = get_db()
    user = current_user(request, db)
    if user is None:
        return jsonify({"error": "auth_required", "message": "User not found"}), 401

    data = request.get_json(silent=True) or {}
    raw_plan_id = data.get("plan_id")
    if not raw_plan_id:
        return jsonify({"error": "validation_error", "message": "plan_id is required"}), 400

    try:
        if isinstance(raw_plan_id, uuid.UUID):
            plan_id = raw_plan_id
        else:
            plan_id = uuid.UUID(str(raw_plan_id))
    except (ValueError, AttributeError) as e:
        return jsonify({"error": "validation_error", "message": f"Invalid plan_id: {e}"}), 400

    role = user.role

    try:
        if role == "institution_admin":
            if not user.institution_id:
                return jsonify({"error": "validation_error", "message": "institution_id missing"}), 400
            result = create_institution_order(db, user.institution_id, plan_id)
        elif role == "student":
            result = create_student_order(db, user.id, plan_id)
        else:
            return jsonify({"error": "forbidden", "message": "Only students and institution admins can create orders"}), 403
        return jsonify(result), 200
    except ValueError as exc:
        return jsonify({"error": "invalid_plan", "message": str(exc)}), 400
    except Exception as exc:
        logger.exception("create-order failed: %s", exc)
        return jsonify({"error": "order_creation_failed", "message": str(exc)}), 500


@router.route("/verify", methods=["POST"])
@require_authenticated
def verify_payment():
    data = request.get_json(silent=True) or {}
    razorpay_order_id = data.get("razorpay_order_id")
    razorpay_payment_id = data.get("razorpay_payment_id")
    razorpay_signature = data.get("razorpay_signature")

    if not razorpay_order_id or not razorpay_payment_id or not razorpay_signature:
        return jsonify({"error": "validation_error", "message": "Missing payment verification parameters"}), 400

    valid = gateway.verify_payment_signature(razorpay_order_id, razorpay_payment_id, razorpay_signature)
    if not valid:
        return jsonify({
            "error": "signature_invalid",
            "message": "Payment signature verification failed.",
            "order_id": razorpay_order_id,
        }), 400

    razorpay_key = gateway.get_public_key()
    if razorpay_key.startswith("rzp_test_") or not gateway.is_configured():
        try:
            from .service import _activate_on_payment
            db: Session = get_db()
            _activate_on_payment(db, razorpay_order_id, razorpay_payment_id, 0, "test_card")
        except Exception as e:
            logger.warning("Test-mode direct activation failed: %s", e)

    return jsonify({
        "verified": True,
        "message": "Payment received. Your subscription has been activated.",
        "order_id": razorpay_order_id,
    }), 200


@router.route("/webhook", methods=["POST"])
def razorpay_webhook():
    db: Session = get_db()
    raw_body = request.get_data()
    x_razorpay_signature = request.headers.get("X-Razorpay-Signature", "")

    if not gateway.verify_webhook_signature(raw_body, x_razorpay_signature):
        return jsonify({"error": "invalid_signature"}), 400

    try:
        payload_data = json.loads(raw_body)
        event = payload_data.get("event", "")
        entity = payload_data.get("payload", {}).get("payment", {}).get("entity", {})
        refund_entity = payload_data.get("payload", {}).get("refund", {}).get("entity", {})

        order_id = entity.get("order_id", "")
        payment_id = entity.get("id", "")
        amt_paise = entity.get("amount", 0)
        method = entity.get("method", "")
        pay_status = entity.get("status", "")

        from .service import _log_webhook, _activate_on_payment, _fail_billing_record
        _log_webhook(db, event, order_id, payment_id, amt_paise, pay_status, raw_body.decode("utf-8", errors="ignore"))

        if event in ("payment.captured", "order.paid"):
            _activate_on_payment(db, order_id, payment_id, amt_paise, method)
        elif event == "payment.failed":
            _fail_billing_record(db, order_id, payment_id)
        elif event == "refund.created":
            handle_refund_webhook(
                db,
                order_id=refund_entity.get("payment_id", payment_id),
                payment_id=refund_entity.get("payment_id", payment_id),
                refund_id=refund_entity.get("id", ""),
                amount_paise=refund_entity.get("amount", 0),
            )

        return jsonify({"status": "ok"}), 200
    except Exception as exc:
        logger.exception("Webhook processing error: %s", exc)
        return jsonify({"error": "webhook_processing_failed"}), 500


@router.route("/history", methods=["GET"])
@require_authenticated
def payment_history():
    db: Session = get_db()
    user = current_user(request, db)
    if user is None:
        return jsonify({"error": "auth_required"}), 401

    role = user.role
    if role == "institution_admin":
        if not user.institution_id:
            return jsonify({"error": "forbidden"}), 403
        records = get_institution_payment_history(db, user.institution_id)
    elif role == "student":
        records = get_student_payment_history(db, user.id)
    else:
        return jsonify({"error": "forbidden"}), 403

    return jsonify({"history": records, "total": len(records)}), 200


__all__ = ["router"]
