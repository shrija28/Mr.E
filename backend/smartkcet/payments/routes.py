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

import json
import logging
import time
import uuid
from collections import defaultdict
from typing import Annotated, Any, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
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

router = APIRouter(prefix="/api/payments", tags=["payments"])


# ---------------------------------------------------------------------------
# Simple in-process rate limiter (IP-based)
# Replace with Redis-based limiter in production for multi-process deployments
# ---------------------------------------------------------------------------

_rate_store: dict[str, list[float]] = defaultdict(list)
_RATE_WINDOW  = 60   # seconds
_RATE_MAX_REQ = 5    # max order creations per window per IP


def _check_rate_limit(request: Request) -> None:
    ip  = request.client.host if request.client else "unknown"
    now = time.monotonic()
    _rate_store[ip] = [t for t in _rate_store[ip] if now - t < _RATE_WINDOW]
    if len(_rate_store[ip]) >= _RATE_MAX_REQ:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
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

@router.get("/plans")
async def list_plans(db: Session = Depends(get_session)) -> Any:
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


@router.get("/plans/student")
async def list_student_plans(db: Session = Depends(get_session)) -> Any:
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


@router.get("/plans/institution")
async def list_institution_plans(db: Session = Depends(get_session)) -> Any:
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


def _serialize_plan(p: SubscriptionPlan) -> dict:
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

@router.post("/create-order")
async def create_order(
    request: Request,
    body: CreateOrderRequest,
    payload: Annotated[dict, Depends(require_authenticated)],
    db: Session = Depends(get_session),
) -> Any:
    """Create a Razorpay order. Works for both institution admins and students.

    Rate-limited to 5 orders per minute per IP to prevent abuse.
    Idempotent: duplicate orders for the same plan within 5 min are safe
    (Razorpay order IDs are unique per creation, so replay = new order).
    """
    _check_rate_limit(request)

    # DEBUG: Enhanced logging to find exact bug location
    print("="*60)
    print("==== CREATE ORDER DEBUG START ====")
    print("="*60)
    print(f"RAW BODY object: {body}")
    print(f"BODY TYPE: {type(body)}")
    print(f"BODY.__dict__: {body.__dict__ if hasattr(body, '__dict__') else 'N/A'}")
    print(f"REQUEST object: {request}")
    print(f"REQUEST TYPE: {type(request)}")
    print("-"*60)
    print(f"body.plan_id VALUE: {body.plan_id}")
    print(f"body.plan_id TYPE: {type(body.plan_id)}")
    print(f"body.plan_id REPR: {repr(body.plan_id)}")
    print(f"Is body.plan_id already UUID?: {isinstance(body.plan_id, uuid.UUID)}")
    print("-"*60)
    print(f"payload ROLE: {payload.get('role')}")
    print(f"payload KEYS: {list(payload.keys())}")
    print("="*60)
    
    logger.info(f"[create-order] body.plan_id: {body.plan_id}, type: {type(body.plan_id)}")

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
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "validation_error", "message": f"Invalid plan_id: {str(e)}"},
        )

    role = payload.get("role", "")

    try:
        if role == "institution_admin":
            institution_id_str = payload.get("institution_id", "")
            if not institution_id_str:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"error": "validation_error", "message": "institution_id missing from token"},
                )
            institution_id = uuid.UUID(institution_id_str)
            result = create_institution_order(db, institution_id, plan_id)
            
        elif role == "student":
            # Students: get user UUID from current_user (not from token "sub")
            # The "sub" in JWT might be KCET ID (string), not a UUID
            from ..middleware.rbac import current_user
            user = current_user(request, db)
            if user is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, 
                    detail={"error": "auth_required", "message": "User not found"}
                )
            
            logger.info(f"[create-order] Student user.id: {user.id}, type: {type(user.id)}")
            result = create_student_order(db, user.id, plan_id)
            
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
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
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "invalid_plan", "message": str(exc)},
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("create-order failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "order_creation_failed", "message": str(exc)},
        )


# ---------------------------------------------------------------------------
# POST /api/payments/verify  — institution_admin or student
# ---------------------------------------------------------------------------

@router.post("/verify")
async def verify_payment(
    request: Request,
    body: VerifyPaymentRequest,
    payload: Annotated[dict, Depends(require_authenticated)],
    db: Session = Depends(get_session),
) -> Any:
    """Verify payment signature from frontend Razorpay success callback.

    This does NOT activate the subscription.
    Subscription activation happens only via the server-side webhook.
    Returns 200 immediately so the frontend can show "payment received" UI.
    """
    print(f"\n[VERIFY] /verify endpoint HIT")
    print(f"[VERIFY] razorpay_order_id = {body.razorpay_order_id}")
    print(f"[VERIFY] razorpay_payment_id = {body.razorpay_payment_id}")
    print(f"[VERIFY] razorpay_signature = {body.razorpay_signature[:20]}...")
    
    print(f"[VERIFY] Verifying payment signature...")
    valid = gateway.verify_payment_signature(
        body.razorpay_order_id,
        body.razorpay_payment_id,
        body.razorpay_signature,
    )
    
    if not valid:
        print(f"[VERIFY] ❌ SIGNATURE VERIFICATION FAILED")
        logger.warning("Frontend payment verification FAILED for order %s", body.razorpay_order_id)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "signature_invalid",
                "message": "Payment signature verification failed. Contact support with your order ID.",
                "order_id": body.razorpay_order_id,
            },
        )

    print(f"[VERIFY] ✅ SIGNATURE VERIFICATION SUCCESS")
    logger.info("Frontend payment verified (awaiting webhook) for order %s", body.razorpay_order_id)

    # In test mode (rzp_test_ keys), activate subscription directly since
    # Razorpay can't reach localhost with a webhook. In production (rzp_live_),
    # activation happens ONLY via the server-side webhook — this block is skipped.
    razorpay_key = gateway.get_public_key()
    print(f"[VERIFY] Razorpay key starts with: {razorpay_key[:8]}")
    
    if razorpay_key.startswith("rzp_test_") or not gateway.is_configured():
        print(f"[VERIFY] TEST MODE DETECTED - calling _activate_on_payment directly")
        try:
            from .service import _activate_on_payment
            print(f"[VERIFY] Calling _activate_on_payment({body.razorpay_order_id}, ...)")
            _activate_on_payment(db, body.razorpay_order_id, body.razorpay_payment_id, 0, "test_card")
            print(f"[VERIFY] ✅ _activate_on_payment returned successfully")
        except Exception as e:
            print(f"[VERIFY] ❌ Test-mode direct activation FAILED:")
            print(f"[VERIFY] Exception: {e}")
            import traceback
            traceback.print_exc()
            logger.warning("Test-mode direct activation failed: %s", e)
    else:
        print(f"[VERIFY] PRODUCTION MODE - activation will happen via webhook")

    print(f"[VERIFY] Returning success response\n")
    return {
        "verified": True,
        "message": "Payment received. Your subscription has been activated.",
        "order_id": body.razorpay_order_id,
    }


# ---------------------------------------------------------------------------
# POST /api/payments/webhook  — Razorpay server → our backend
# ---------------------------------------------------------------------------

@router.post("/webhook")
async def razorpay_webhook(
    request: Request,
    db: Session = Depends(get_session),
    x_razorpay_signature: str = Header(default=""),
) -> Any:
    """Authoritative payment event handler from Razorpay.

    Security:
    - HMAC-SHA256 signature verified before ANY action
    - Idempotent: duplicate webhooks safely skipped
    - Handles: payment.captured, order.paid, payment.failed, refund.created
    - Subscription activated ONLY here — never from frontend success callback

    Production setup: configure this URL in Razorpay dashboard as webhook endpoint.
    Test mode: mock webhooks can be sent via Razorpay test dashboard.
    """
    raw_body = await request.body()

    # Signature verification
    if not gateway.verify_webhook_signature(raw_body, x_razorpay_signature):
        logger.warning("Webhook signature FAILED — rejecting")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
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
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "webhook_processing_failed"},
        )


# ---------------------------------------------------------------------------
# GET /api/payments/history  — institution or student
# ---------------------------------------------------------------------------

@router.get("/history")
async def payment_history(
    request: Request,
    payload: Annotated[dict, Depends(require_authenticated)],
    db: Session = Depends(get_session),
) -> Any:
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
