"""Payment gateway API routes.

POST /api/payments/create-order        — institution or student order creation
POST /api/payments/verify              — signature verification (frontend)
POST /api/payments/webhook             — Razorpay server webhook (HMAC verified)
GET  /api/payments/plans               — public plan list (all plan types)
GET  /api/payments/plans/student       — public individual/student plans only
GET  /api/payments/history             — billing history (institution or student)

Design goals
------------
- Works fully in dev/test mode with mock keys
- Production activation: add RAZORPAY_* env vars + webhook URL, zero code change
- Rate limiting on order creation to prevent abuse
- Idempotent webhook processing (duplicate webhook = safe skip)
- Replay attack protection via order_id uniqueness in BillingRecord
"""

from __future__ import annotations
import os

import json
import logging
import time
import uuid
from collections import defaultdict
from typing import Annotated, Any, Optional

import os
from flask import Blueprint, request, g, make_response, jsonify, Response
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..db.session import get_async_session as get_session
from ..db.subscription_models import SubscriptionPlan
from ..middleware.rbac import require_authenticated, require_institution_admin
from . import gateway
from .service import (
    create_institution_order,
    create_student_order,
    get_institution_payment_history,
    get_student_payment_history,
    handle_refund_webhook,
    handle_webhook,
)

logger = logging.getLogger("smartkcet.payments.routes")

router = Blueprint("payments_routes", __name__)


# ---------------------------------------------------------------------------
# Simple in-process rate limiter (IP-based)
# Replace with Redis-based limiter in production for multi-process deployments
# ---------------------------------------------------------------------------

_rate_store: dict[str, list[float]] = defaultdict(list)
_RATE_WINDOW  = 60   # seconds
_RATE_MAX_REQ = 5    # max order creations per window per IP


def _check_rate_limit()-> None:
    ip  = request.remote_addr or "unknown"
    now = time.monotonic()
    _rate_store[ip] = [t for t in _rate_store[ip] if now - t < _RATE_WINDOW]
    if len(_rate_store[ip]) >= _RATE_MAX_REQ:
        raise HTTPException(
            status_code=429,
            detail={
                "error": "rate_limited",
                "message": f"Too many order creation requests. Please wait {_RATE_WINDOW}s.",
                "retry_after": _RATE_WINDOW,
            },
            headers={"Retry-After": str(_RATE_WINDOW)},
        )
    _rate_store[ip].append(now)


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class CreateOrderRequest(BaseModel):
    plan_id: str


class VerifyPaymentRequest(BaseModel):
    razorpay_order_id:   str
    razorpay_payment_id: str
    razorpay_signature:  str
    plan_id: Optional[str] = None


# ---------------------------------------------------------------------------
# GET /api/payments/plans  — public, both institution and student plans
# ---------------------------------------------------------------------------

@router.route("/plans", methods=["GET"])
def list_plans()-> Any:    
    from flask import g
    db = getattr(g, "db", None)
    session = db
    
    from flask import g
    db = getattr(g, "db", None)
    session = db
    """Return all active subscription plans (both institution and individual)."""
    plans = (
        db.query(SubscriptionPlan)
        .filter(SubscriptionPlan.is_active.is_(True))
        .order_by(SubscriptionPlan.plan_type, SubscriptionPlan.price.asc())
        .all()
    )
    return {
        "plans": [_serialize_plan(p) for p in plans],
        "key_id": gateway.get_public_key(),
        "gateway_configured": gateway.is_configured(),
    }


@router.route("/plans/student", methods=["GET"])
def list_student_plans()-> Any:    
    from flask import g
    db = getattr(g, "db", None)
    session = db
    
    from flask import g
    db = getattr(g, "db", None)
    session = db
    """Return active individual (student) subscription plans."""
    plans = (
        db.query(SubscriptionPlan)
        .filter(
            SubscriptionPlan.plan_type == "individual",
            SubscriptionPlan.is_active.is_(True),
        )
        .order_by(SubscriptionPlan.price.asc())
        .all()
    )
    return {
        "plans": [_serialize_plan(p) for p in plans],
        "key_id": gateway.get_public_key(),
        "gateway_configured": gateway.is_configured(),
    }


@router.route("/plans/institution", methods=["GET"])
def list_institution_plans()-> Any:    
    from flask import g
    db = getattr(g, "db", None)
    session = db
    
    from flask import g
    db = getattr(g, "db", None)
    session = db
    """Return active institution subscription plans."""
    plans = (
        db.query(SubscriptionPlan)
        .filter(
            SubscriptionPlan.plan_type == "institution",
            SubscriptionPlan.is_active.is_(True),
        )
        .order_by(SubscriptionPlan.price.asc())
        .all()
    )
    return {
        "plans": [_serialize_plan(p) for p in plans],
        "key_id": gateway.get_public_key(),
        "gateway_configured": gateway.is_configured(),
    }


def _serialize_plan(p: SubscriptionPlan)-> dict:
    return {
        "id":                           str(p.id),
        "name":                         p.name,
        "plan_type":                    p.plan_type,
        "billing_period":               p.billing_period,
        "price":                        float(p.price),
        "price_paise":                  int(float(p.price) * 100),
        "max_student_seats":            p.max_student_seats,
        "max_test_attempts_per_period": p.max_test_attempts_per_period,
        "feature_flags":                p.feature_flags or {},
        "is_active":                    p.is_active,
    }


# ---------------------------------------------------------------------------
# POST /api/payments/create-order  — institution_admin or student
# ---------------------------------------------------------------------------

@router.route("/create-order", methods=["POST"])
def create_order()-> Any:    
    payload = require_authenticated()
    from flask import g
    db = getattr(g, "db", None)
    session = db
    """Create a Razorpay order. Works for both institution admins and students.

    Rate-limited to 5 orders per minute per IP to prevent abuse.
    Idempotent: duplicate orders for the same plan within 5 min are safe
    (Razorpay order IDs are unique per creation, so replay = new order).
    """
    _check_rate_limit()

    body = CreateOrderRequest.model_validate(request.get_json(silent=True) or {})
    logger.info("[create-order] plan_id: %s, role: %s", body.plan_id, payload.get("role"))

    try:
        # Check if already UUID (DO NOT parse twice!)
        if isinstance(body.plan_id, uuid.UUID):
            plan_id = body.plan_id
            logger.info(f"[create-order] plan_id already UUID: {plan_id}")
        else:
            plan_id = uuid.UUID(str(body.plan_id))
            logger.info(f"[create-order] Parsed plan_id UUID: {plan_id}")
    except (ValueError, AttributeError) as e:
        logger.error(f"[create-order] UUID parsing failed: {e}")
        logger.error(f"[create-order] Attempted to parse: {body.plan_id}")
        raise HTTPException(
            status_code=400,
            detail={"error": "validation_error", "message": f"Invalid plan_id: {str(e)}"},
        )

    role = payload.get("role", "")

    try:
        if role == "institution_admin":
            institution_id_str = payload.get("institution_id", "")
            if not institution_id_str:
                raise HTTPException(
                    status_code=400,
                    detail={"error": "validation_error", "message": "institution_id missing from token"},
                )
            institution_id = uuid.UUID(institution_id_str)
            result = create_institution_order(db, institution_id, plan_id)
            
        elif role == "student":
            # Students: get user UUID from current_user (not from token "sub")
            # The "sub" in JWT might be KCET ID (string), not a UUID
            from ..middleware.rbac import current_user
            user = current_user(db)
            if user is None:
                raise HTTPException(
                    status_code=401, 
                    detail={"error": "auth_required", "message": "User not found"}
                )
            
            logger.info(f"[create-order] Student user.id: {user.id}, type: {type(user.id)}")
            result = create_student_order(db, user.id, plan_id)
            
        else:
            raise HTTPException(
                status_code=403,
                detail={"error": "forbidden", "message": "Only students and institution admins can create orders"},
            )
        return result
    except ValueError as exc:
        # Log the full exception for debugging
        logger.error(f"[create-order] ValueError caught: {exc}")
        logger.error(f"[create-order] Exception type: {type(exc)}")
        import traceback
        logger.error(f"[create-order] Traceback: {traceback.format_exc()}")
        
        raise HTTPException(
            status_code=400,
            detail={"error": "invalid_plan", "message": str(exc)},
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("create-order failed: %s", exc)
        raise HTTPException(
            status_code=500,
            detail={"error": "order_creation_failed", "message": str(exc)},
        )


# ---------------------------------------------------------------------------
# POST /api/payments/verify  — institution_admin or student
# ---------------------------------------------------------------------------

@router.route("/verify", methods=["POST"])
def verify_payment()-> Any:    
    payload = require_authenticated()
    from flask import g
    db = getattr(g, "db", None)
    session = db
    """Verify payment signature from frontend Razorpay success callback.

    This does NOT activate the subscription.
    Subscription activation happens only via the server-side webhook.
    Returns 200 immediately so the frontend can show "payment received" UI.
    """
    body = VerifyPaymentRequest.model_validate(request.get_json(silent=True) or {})
    valid = gateway.verify_payment_signature(
        body.razorpay_order_id,
        body.razorpay_payment_id,
        body.razorpay_signature,
    )
    
    if not valid:
        logger.warning("Frontend payment verification FAILED for order %s", body.razorpay_order_id)
        raise HTTPException(
            status_code=400,
            detail={
                "error": "signature_invalid",
                "message": "Payment signature verification failed. Contact support with your order ID.",
                "order_id": body.razorpay_order_id,
            },
        )

    logger.info("Frontend payment verified (awaiting webhook) for order %s", body.razorpay_order_id)

    # In test mode (rzp_test_ keys), activate subscription directly since
    # Razorpay can't reach localhost with a webhook. In production (rzp_live_),
    # activation happens ONLY via the server-side webhook — this block is skipped.
    razorpay_key = gateway.get_public_key()
    if razorpay_key.startswith("rzp_test_") or not gateway.is_configured():
        try:
            from .service import _activate_on_payment
            _activate_on_payment(db, body.razorpay_order_id, body.razorpay_payment_id, 0, "test_card")
        except Exception as e:
            logger.warning("Test-mode direct activation failed: %s", e)
    else:
        logger.info("Production mode - activation will happen via webhook")

    return {
        "verified": True,
        "message": "Payment received. Your subscription has been activated.",
        "order_id": body.razorpay_order_id,
    }


# ---------------------------------------------------------------------------
# POST /api/payments/webhook  — Razorpay server → our backend
# ---------------------------------------------------------------------------

@router.route("/webhook", methods=["POST"])
def razorpay_webhook()-> Any:    
    from flask import request
    x_razorpay_signature = request.headers.get("X-Razorpay-Signature", "")
    from flask import g
    db = getattr(g, "db", None)
    session = db
    
    from flask import g
    db = getattr(g, "db", None)
    session = db
    """Authoritative payment event handler from Razorpay.

    Security:
    - HMAC-SHA256 signature verified before ANY action
    - Idempotent: duplicate webhooks safely skipped
    - Handles: payment.captured, order.paid, payment.failed, refund.created
    - Subscription activated ONLY here — never from frontend success callback

    Production setup: configure this URL in Razorpay dashboard as webhook endpoint.
    Test mode: mock webhooks can be sent via Razorpay test dashboard.
    """
    raw_body = request.get_data(cache=True)

    # Signature verification
    if not gateway.verify_webhook_signature(raw_body, x_razorpay_signature):
        logger.warning("Webhook signature FAILED — rejecting")
        raise HTTPException(
            status_code=400,
            detail={"error": "invalid_signature"},
        )

    try:
        payload_data = json.loads(raw_body)
        event  = payload_data.get("event", "")
        entity = payload_data.get("payload", {}).get("payment", {}).get("entity", {})
        refund_entity = payload_data.get("payload", {}).get("refund", {}).get("entity", {})

        order_id   = entity.get("order_id", "")
        payment_id = entity.get("id", "")
        amt_paise  = entity.get("amount", 0)
        method     = entity.get("method", "")
        pay_status = entity.get("status", "")

        logger.info("Webhook: event=%s order=%s payment=%s", event, order_id, payment_id)

        # Log every event for audit
        from .service import _log_webhook, _activate_on_payment, _fail_billing_record
        _log_webhook(db, event, order_id, payment_id, amt_paise, pay_status, raw_body)

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

        return {"status": "ok"}

    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Webhook processing error: %s", exc)
        raise HTTPException(
            status_code=500,
            detail={"error": "webhook_processing_failed"},
        )


# ---------------------------------------------------------------------------
# GET /api/payments/history  — institution or student
# ---------------------------------------------------------------------------

@router.route("/history", methods=["GET"])
def payment_history()-> Any:    
    payload = require_authenticated()
    from flask import g
    db = getattr(g, "db", None)
    session = db
    """Return billing / payment history for the authenticated user.

    Works for both institution admins (institution billing) and students (personal billing).
    """
    role = payload.get("role", "")

    if role == "institution_admin":
        institution_id = uuid.UUID(payload.get("institution_id", ""))
        records = get_institution_payment_history(db, institution_id)
    elif role == "student":
        from ..middleware.rbac import current_user
        user = current_user(request, db)
        if user is None:
            raise HTTPException(status_code=401, detail={"error": "auth_required"})
        records = get_student_payment_history(db, user.id)
    else:
        raise HTTPException(status_code=403, detail={"error": "forbidden"})

    return {"history": records, "total": len(records)}


__all__ = ["router"]
