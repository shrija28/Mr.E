"""Payment service — creates orders, verifies payments, activates subscriptions.

Security contract
-----------------
1. POST /api/payments/create-order
   - Authenticated institution_admin or student
   - Creates Razorpay order, saves a BillingRecord with status='created'
   - Returns {order_id, amount, key_id, receipt} to frontend

2. POST /api/payments/verify   (frontend calls after Razorpay success)
   - Verifies HMAC-SHA256 signature (razorpay_order_id|razorpay_payment_id)
   - Does NOT activate — only marks record as pending-webhook
   - Returns 200 so frontend can show "payment received" UI

3. POST /api/payments/webhook  (Razorpay server calls)
   - Verifies X-Razorpay-Signature over raw body
   - Only after successful webhook verification:
     • Updates BillingRecord to status='paid'
     • Activates / renews the Subscription
     • Creates SubscriptionEvent
   - Returns 200 immediately (Razorpay retries on non-200)
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Optional

from sqlalchemy.orm import Session

from ..db.subscription_models import (
    BillingRecord,
    Institution,
    PaymentLog,
    Subscription,
    SubscriptionEvent,
    SubscriptionPlan,
)
from . import gateway

logger = logging.getLogger("smartkcet.payments.service")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _paise(rupees: Decimal | float) -> int:
    """Convert rupees (Decimal or float) to paise (integer)."""
    return int(Decimal(str(rupees)) * 100)


def _plan_duration(billing_period: str) -> timedelta:
    return timedelta(days=7) if billing_period == "weekly" else timedelta(days=30)


# ---------------------------------------------------------------------------
# Order creation
# ---------------------------------------------------------------------------

def create_institution_order(
    db: Session,
    institution_id: uuid.UUID,
    plan_id: uuid.UUID,
) -> dict[str, Any]:
    """Create a Razorpay order for an institution plan purchase.

    Returns the data the frontend needs to open the Razorpay checkout modal.
    """
    logger.info(f"[create_institution_order] institution_id: {institution_id}, plan_id: {plan_id}")

    # Compare via the ORM's native UUID handling. The id column stores a
    # 32-char hex string (no hyphens), so casting to String and comparing
    # against str(uuid) (36-char, hyphenated) never matches.
    plan = db.query(SubscriptionPlan).filter(
        SubscriptionPlan.id == plan_id,
        SubscriptionPlan.is_active.is_(True),
    ).first()
    if not plan:
        raise ValueError(f"Plan {plan_id} not found or inactive")

    amount_paise = _paise(plan.price)
    receipt = f"inst_{str(institution_id)[:8]}_{uuid.uuid4().hex[:8]}"

    order = gateway.create_order(
        amount_paise=amount_paise,
        receipt=receipt,
        notes={
            "entity_type":    "institution",
            "institution_id": str(institution_id),
            "plan_id":        str(plan_id),
            "plan_name":      plan.name,
        },
    )

    # Create a pending BillingRecord so we can track this order
    now = datetime.utcnow()

    # Check if there is an existing active subscription to attach to
    existing_sub = db.query(Subscription).filter(
        Subscription.institution_id == institution_id,
        Subscription.status.in_(["trial", "active", "overdue", "grace_period"]),
    ).first()

    billing = BillingRecord(
        subscription_id=existing_sub.id if existing_sub else _get_or_create_pending_sub(db, institution_id, plan),
        amount=plan.price,
        amount_paise=amount_paise,
        currency="INR",
        billing_date=now,
        payment_status="created",
        razorpay_order_id=order["id"],
        plan_id=plan_id,
    )
    db.add(billing)

    # Log the order creation
    log = PaymentLog(
        id=uuid.uuid4(),
        event_type="order.created",
        razorpay_order_id=order["id"],
        entity_type="institution",
        entity_id=institution_id,
        amount_paise=amount_paise,
        currency="INR",
        status="created",
        raw_payload=json.dumps(order),
    )
    db.add(log)
    db.commit()

    return {
        "order_id":     order["id"],
        "amount":       amount_paise,
        "currency":     "INR",
        "receipt":      receipt,
        "key_id":       gateway.get_public_key(),
        "plan_name":    plan.name,
        "plan_id":      str(plan_id),
        "description":  f"SmartKCET — {plan.name} ({plan.billing_period})",
        "_mock":        order.get("_mock", False),
    }


def _get_or_create_pending_sub(
    db: Session,
    institution_id: uuid.UUID,
    plan: SubscriptionPlan,
) -> uuid.UUID:
    """Return a stub subscription ID for the billing record when no active sub exists."""
    # In real flow, subscription is created/updated only after payment webhook
    # We create a minimal pending record to link billing
    now = datetime.utcnow()
    # Ensure plan_id is a UUID, not a string (SQLite may return strings)
    plan_id = plan.id if isinstance(plan.id, uuid.UUID) else uuid.UUID(str(plan.id))
    sub = Subscription(
        institution_id=institution_id,
        plan_id=plan_id,
        status="expired",          # stays expired until webhook activates
        start_date=now,
        current_period_start=now,
    )
    db.add(sub)
    db.flush()
    return sub.id


# ---------------------------------------------------------------------------
# Webhook handler — THE authoritative activation path
# ---------------------------------------------------------------------------

def handle_webhook(
    db: Session,
    raw_body: bytes,
    signature_header: str,
) -> dict[str, Any]:
    """Process a Razorpay webhook.

    Verifies signature, then handles:
      - payment.captured  → activate / renew subscription
      - payment.failed    → mark billing record failed
      - order.paid        → same as payment.captured (belt-and-suspenders)

    Always returns {"status": "ok"} on success so Razorpay stops retrying.
    """
    # 1. Verify signature FIRST — reject anything that doesn't match
    if not gateway.verify_webhook_signature(raw_body, signature_header):
        logger.warning("Webhook signature verification FAILED — rejecting")
        raise PermissionError("Invalid webhook signature")

    payload = json.loads(raw_body)
    event   = payload.get("event", "")
    entity  = payload.get("payload", {}).get("payment", {}).get("entity", {})

    order_id    = entity.get("order_id", "")
    payment_id  = entity.get("id", "")
    amount_paise = entity.get("amount", 0)
    method      = entity.get("method", "")
    status      = entity.get("status", "")

    logger.info("Webhook event=%s order=%s payment=%s", event, order_id, payment_id)

    # Log every webhook for audit
    _log_webhook(db, event, order_id, payment_id, amount_paise, status, raw_body)

    if event in ("payment.captured", "order.paid") and status in ("captured", "paid", ""):
        _activate_on_payment(db, order_id, payment_id, amount_paise, method)
    elif event == "payment.failed":
        _fail_billing_record(db, order_id, payment_id)

    return {"status": "ok"}




# DEPRECATED: Old _activate_on_payment with debug prints - kept for reference
# Now using dispatcher function below


def _fail_billing_record(
    db: Session,
    order_id: str,
    payment_id: str,
) -> None:
    billing = db.query(BillingRecord).filter(
        BillingRecord.razorpay_order_id == order_id
    ).first()
    if billing:
        billing.payment_status     = "failed"
        billing.razorpay_payment_id = payment_id
        db.commit()
        logger.info("BillingRecord marked failed for order %s", order_id)


def _log_webhook(
    db: Session,
    event: str,
    order_id: str,
    payment_id: str,
    amount_paise: int,
    status: str,
    raw_body: bytes,
) -> None:
    log = PaymentLog(
        id=uuid.uuid4(),
        event_type=event,
        razorpay_order_id=order_id or None,
        razorpay_payment_id=payment_id or None,
        amount_paise=amount_paise or None,
        status=status or "received",
        raw_payload=raw_body.decode("utf-8", errors="replace")[:10000],
    )
    db.add(log)
    # Don't commit here — caller commits after activation


# ---------------------------------------------------------------------------
# Payment history for billing dashboard
# ---------------------------------------------------------------------------

def get_institution_payment_history(
    db: Session,
    institution_id: uuid.UUID,
    limit: int = 50,
) -> list[dict]:
    """Return billing records for an institution, newest first."""
    records = (
        db.query(BillingRecord, SubscriptionPlan)
        .join(Subscription, BillingRecord.subscription_id == Subscription.id)
        .outerjoin(SubscriptionPlan, SubscriptionPlan.id == BillingRecord.plan_id)
        .filter(Subscription.institution_id == institution_id)
        .order_by(BillingRecord.billing_date.desc())
        .limit(limit)
        .all()
    )

    result = []
    for br, plan in records:
        result.append({
            "id":                   str(br.id),
            "date":                 br.billing_date.isoformat() if br.billing_date else None,
            "amount":               float(br.amount),
            "currency":             br.currency or "INR",
            "plan_name":            plan.name if plan else "—",
            "billing_period":       plan.billing_period if plan else "—",
            "payment_status":       br.payment_status,
            "payment_method":       br.payment_method_ref or "—",
            "transaction_ref":      br.razorpay_payment_id or br.transaction_ref or "—",
            "razorpay_order_id":    br.razorpay_order_id or "—",
        })
    return result


# ---------------------------------------------------------------------------
# Student order creation — mirrors institution flow
# ---------------------------------------------------------------------------

def create_student_order(
    db: Session,
    user_id: uuid.UUID,
    plan_id: uuid.UUID,
) -> dict[str, Any]:
    """Create a Razorpay order for a student plan purchase (Pro subscription).

    Returns the data the frontend needs to open the Razorpay checkout modal.
    Works with test keys in dev mode — no code change needed for production.
    
    **IMPORTANT**: Only allows order creation for paid plans if user has NO active subscription.
    Users with active subscriptions must wait for expiry before upgrading to paid plans.
    FREE plan purchases are always allowed (student can downgrade anytime).
    """
    from ..db.models import User as UserModel
    from ..subscription.service import SubscriptionService

    logger.info(f"[create_student_order] user_id: {user_id}, plan_id: {plan_id}")

    try:
        # Compare via the ORM's native UUID handling. The id column stores a
        # 32-char hex string (no hyphens); casting to String and comparing
        # against str(uuid) (36-char, hyphenated) never matches.
        plan = db.query(SubscriptionPlan).filter(
            SubscriptionPlan.id == plan_id,
            SubscriptionPlan.is_active.is_(True),
        ).first()
    except Exception as e:
        logger.error(f"[create_student_order] DB query failed: {e}")
        raise
    
    if not plan:
        logger.error(f"[create_student_order] Plan {plan_id} not found or inactive")
        raise ValueError(f"Plan {plan_id} not found or inactive")
    
    logger.info(f"[create_student_order] Plan found: {plan.name} at ₹{plan.price}")

    if plan.plan_type != "individual":
        raise ValueError("Students can only subscribe to individual plans")

    # Check if user has active subscription - ONLY block for PAID plans
    # FREE plan can always be purchased (downgrade allowed)
    if plan.price > 0:  # Paid plan (not Free)
        subscription_service = SubscriptionService(db)
        can_change, error_msg = subscription_service.can_change_subscription(user_id)
        
        if not can_change:
            logger.warning(f"[create_student_order] User {user_id} has active subscription: {error_msg}")
            raise ValueError(error_msg)

    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise ValueError(f"User {user_id} not found")

    amount_paise = _paise(plan.price)
    receipt = f"stu_{str(user_id)[:8]}_{uuid.uuid4().hex[:8]}"

    order = gateway.create_order(
        amount_paise=amount_paise,
        receipt=receipt,
        notes={
            "entity_type": "student",
            "user_id":     str(user_id),
            "plan_id":     str(plan_id),
            "plan_name":   plan.name,
            "user_email":  user.email,
        },
    )

    now = datetime.utcnow()

    # Check for existing subscription to attach billing to
    existing_sub = db.query(Subscription).filter(
        Subscription.user_id == user_id,
        Subscription.status.in_(["trial", "active", "overdue", "grace_period"]),
    ).first()

    sub_id = existing_sub.id if existing_sub else _get_or_create_pending_student_sub(db, user_id, plan)

    billing = BillingRecord(
        subscription_id=sub_id,
        amount=plan.price,
        amount_paise=amount_paise,
        currency="INR",
        billing_date=now,
        payment_status="created",
        razorpay_order_id=order["id"],
        plan_id=plan_id,
    )
    db.add(billing)

    log = PaymentLog(
        id=uuid.uuid4(),
        event_type="order.created",
        razorpay_order_id=order["id"],
        entity_type="student",
        entity_id=user_id,
        subscription_id=sub_id,
        amount_paise=amount_paise,
        currency="INR",
        status="created",
        raw_payload=json.dumps(order),
    )
    db.add(log)
    db.commit()

    return {
        "order_id":    order["id"],
        "amount":      amount_paise,
        "currency":    "INR",
        "receipt":     receipt,
        "key_id":      gateway.get_public_key(),
        "plan_name":   plan.name,
        "plan_id":     str(plan_id),
        "description": f"SmartKCET Pro — {plan.billing_period}",
        "prefill": {
            "name":  user.display_name or "",
            "email": user.email or "",
        },
        "_mock": order.get("_mock", False),
    }


def _get_or_create_pending_student_sub(
    db: Session,
    user_id: uuid.UUID,
    plan: SubscriptionPlan,
) -> uuid.UUID:
    """Create a minimal pending subscription stub for billing linkage."""
    now = datetime.utcnow()
    # Ensure plan_id is a UUID, not a string (SQLite may return strings)
    plan_id = plan.id if isinstance(plan.id, uuid.UUID) else uuid.UUID(str(plan.id))
    sub = Subscription(
        user_id=user_id,
        plan_id=plan_id,
        status="expired",
        start_date=now,
        current_period_start=now,
    )
    db.add(sub)
    db.flush()
    return sub.id


# ---------------------------------------------------------------------------
# Activate student subscription after payment
# ---------------------------------------------------------------------------

def _activate_student_on_payment(
    db: Session,
    billing: BillingRecord,
    payment_id: str,
    method: str,
    amount_paise: int,
    order_id: str,
) -> None:
    """Activate / upgrade a student subscription after verified webhook."""
    from ..db.models import User as UserModel
    from datetime import timedelta

    sub  = db.query(Subscription).filter(Subscription.id == billing.subscription_id).first()

    # Use billing.plan_id if available (user's selection), fallback to sub.plan_id
    plan_id_to_use = billing.plan_id or sub.plan_id
    # Normalise to a UUID and compare natively (id is stored as 32-char hex).
    plan = None
    if plan_id_to_use:
        try:
            _pid = plan_id_to_use if isinstance(plan_id_to_use, uuid.UUID) else uuid.UUID(str(plan_id_to_use))
            plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.id == _pid).first()
        except (ValueError, TypeError):
            plan = None

    if not sub or not plan:
        logger.error("Cannot activate student sub: sub or plan missing for order %s", order_id)
        return

    now         = datetime.utcnow()
    prev_status = sub.status
    duration    = _plan_duration(plan.billing_period)

    # Keep plan_id as a UUID — the column is a UUID type, so assigning a
    # string raises "'str' object has no attribute 'hex'" on flush.
    _raw_plan = billing.plan_id or sub.plan_id
    if _raw_plan is None:
        plan_id_to_assign = None
    elif isinstance(_raw_plan, uuid.UUID):
        plan_id_to_assign = _raw_plan
    else:
        plan_id_to_assign = uuid.UUID(str(_raw_plan))
    sub.plan_id               = plan_id_to_assign
    sub.status                = "active"
    sub.start_date            = sub.start_date if prev_status not in ("expired", "cancelled") else now
    sub.current_period_start  = now
    sub.next_renewal_date     = now + duration
    sub.cancellation_date     = None
    sub.grace_period_end      = None

    evt = SubscriptionEvent(
        subscription_id=sub.id,
        event_type="activated" if prev_status in ("expired", "cancelled") else "renewed",
        previous_status=prev_status,
        new_status="active",
        event_metadata={
            "razorpay_order_id":   order_id,
            "razorpay_payment_id": payment_id,
            "payment_method":      method,
            "amount_paise":        amount_paise,
            "activated_at":        now.isoformat(),
            "entity_type":         "student",
        },
    )
    db.add(evt)
    db.commit()

    logger.info("Student subscription %s activated via webhook (order=%s)", sub.id, order_id)


# ---------------------------------------------------------------------------
# Extend webhook handler to support student subscriptions
# ---------------------------------------------------------------------------

def _activate_on_payment(
    db: Session,
    order_id: str,
    payment_id: str,
    amount_paise: int,
    method: str,
) -> None:
    """Activate subscription (institution or student) after successful payment."""
    billing = db.query(BillingRecord).filter(
        BillingRecord.razorpay_order_id == order_id
    ).first()

    if billing is None:
        logger.warning("No BillingRecord found for order_id=%s — cannot activate", order_id)
        return

    if billing.payment_status == "paid":
        logger.info("Order %s already processed — idempotent skip", order_id)
        return

    # Mark billing as paid
    billing.payment_status      = "paid"
    billing.razorpay_payment_id = payment_id
    billing.payment_method_ref  = method
    billing.transaction_ref     = payment_id

    # Determine if this is an institution or student subscription
    sub = db.query(Subscription).filter(Subscription.id == billing.subscription_id).first()
    if not sub:
        logger.error("Subscription not found for billing %s", billing.id)
        return

    if sub.institution_id:
        # Institution payment
        _activate_institution_sub(db, sub, billing, payment_id, method, amount_paise, order_id)
    elif sub.user_id:
        # Student payment
        _activate_student_on_payment(db, billing, payment_id, method, amount_paise, order_id)
    else:
        logger.error("Subscription %s has neither user_id nor institution_id", sub.id)


def _activate_institution_sub(
    db: Session,
    sub: Subscription,
    billing: BillingRecord,
    payment_id: str,
    method: str,
    amount_paise: int,
    order_id: str,
) -> None:
    """Activate institution subscription (extracted for clarity)."""
    # Use billing.plan_id if available (user's selection), fallback to sub.plan_id
    plan_id_to_use = billing.plan_id or sub.plan_id
    # Normalise to a UUID and compare natively (id is stored as 32-char hex).
    plan = None
    if plan_id_to_use:
        try:
            _pid = plan_id_to_use if isinstance(plan_id_to_use, uuid.UUID) else uuid.UUID(str(plan_id_to_use))
            plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.id == _pid).first()
        except (ValueError, TypeError):
            plan = None

    if not plan:
        logger.error("Plan not found for order %s (plan_id=%s)", order_id, plan_id_to_use)
        return

    now         = datetime.utcnow()
    prev_status = sub.status
    duration    = _plan_duration(plan.billing_period)

    # Keep plan_id as a UUID — the column is a UUID type, so assigning a
    # string raises "'str' object has no attribute 'hex'" on flush.
    _raw_plan = billing.plan_id or sub.plan_id
    if _raw_plan is None:
        plan_id_to_assign = None
    elif isinstance(_raw_plan, uuid.UUID):
        plan_id_to_assign = _raw_plan
    else:
        plan_id_to_assign = uuid.UUID(str(_raw_plan))
    sub.plan_id               = plan_id_to_assign
    sub.status                = "active"
    sub.start_date            = sub.start_date if prev_status not in ("expired", "cancelled") else now
    sub.current_period_start  = now
    sub.next_renewal_date     = now + duration
    sub.cancellation_date     = None
    sub.grace_period_end      = None

    if sub.institution_id:
        inst = db.query(Institution).filter(Institution.id == sub.institution_id).first()
        if inst:
            inst.subscription_status = "active"

    evt = SubscriptionEvent(
        subscription_id=sub.id,
        event_type="activated" if prev_status in ("expired", "cancelled") else "renewed",
        previous_status=prev_status,
        new_status="active",
        event_metadata={
            "razorpay_order_id":   order_id,
            "razorpay_payment_id": payment_id,
            "payment_method":      method,
            "amount_paise":        amount_paise,
            "activated_at":        now.isoformat(),
        },
    )
    db.add(evt)
    db.commit()

    logger.info("Institution subscription %s activated via webhook (order=%s)", sub.id, order_id)


# ---------------------------------------------------------------------------
# Refund hook (records the refund; refunds initiated via Razorpay dashboard)
# ---------------------------------------------------------------------------

def handle_refund_webhook(
    db: Session,
    order_id: str,
    payment_id: str,
    refund_id: str,
    amount_paise: int,
) -> None:
    """Mark billing record as refunded and suspend subscription access.

    Refunds are initiated via the Razorpay dashboard or admin API.
    This webhook records the refund and revokes subscription access.
    """
    billing = db.query(BillingRecord).filter(
        BillingRecord.razorpay_payment_id == payment_id
    ).first()

    if not billing:
        logger.warning("Refund webhook: no billing record for payment %s", payment_id)
        return

    billing.payment_status = "refunded"

    sub = db.query(Subscription).filter(Subscription.id == billing.subscription_id).first()
    if sub and sub.status == "active":
        prev = sub.status
        sub.status = "cancelled"

        evt = SubscriptionEvent(
            subscription_id=sub.id,
            event_type="cancelled",
            previous_status=prev,
            new_status="cancelled",
            event_metadata={
                "reason":           "refund_issued",
                "refund_id":        refund_id,
                "razorpay_payment_id": payment_id,
                "amount_refunded_paise": amount_paise,
                "refunded_at":      datetime.utcnow().isoformat(),
            },
        )
        db.add(evt)

        # Update institution status if applicable
        if sub.institution_id:
            inst = db.query(Institution).filter(Institution.id == sub.institution_id).first()
            if inst:
                inst.subscription_status = "inactive"

    db.commit()
    logger.info("Refund processed for payment %s, refund_id=%s", payment_id, refund_id)


# ---------------------------------------------------------------------------
# Student payment history
# ---------------------------------------------------------------------------

def get_student_payment_history(
    db: Session,
    user_id: uuid.UUID,
    limit: int = 50,
) -> list[dict]:
    """Return billing records for a student, newest first."""
    records = (
        db.query(BillingRecord, SubscriptionPlan)
        .join(Subscription, BillingRecord.subscription_id == Subscription.id)
        .outerjoin(SubscriptionPlan, SubscriptionPlan.id == BillingRecord.plan_id)
        .filter(Subscription.user_id == user_id)
        .order_by(BillingRecord.billing_date.desc())
        .limit(limit)
        .all()
    )
    result = []
    for br, plan in records:
        result.append({
            "id":              str(br.id),
            "date":            br.billing_date.isoformat() if br.billing_date else None,
            "amount":          float(br.amount),
            "currency":        br.currency or "INR",
            "plan_name":       plan.name if plan else "—",
            "billing_period":  plan.billing_period if plan else "—",
            "payment_status":  br.payment_status,
            "payment_method":  br.payment_method_ref or "—",
            "transaction_ref": br.razorpay_payment_id or br.transaction_ref or "—",
            "razorpay_order_id": br.razorpay_order_id or "—",
        })
    return result


# keep old _fail_billing_record for the original webhook path
def _fail_billing_record(db: Session, order_id: str, payment_id: str) -> None:
    billing = db.query(BillingRecord).filter(
        BillingRecord.razorpay_order_id == order_id
    ).first()
    if billing:
        billing.payment_status      = "failed"
        billing.razorpay_payment_id = payment_id
        db.commit()
        logger.info("BillingRecord marked failed for order %s", order_id)
