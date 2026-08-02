"""Razorpay client wrapper.

Reads RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET from environment.
In SMARTKCET_DEV_MODE=1 with placeholder keys, payment creation is
mocked so the app starts and the flow can be tested without real keys.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import uuid
from typing import Any, Optional

logger = logging.getLogger("smartkcet.payments.gateway")

_RAZORPAY_KEY_ID     = os.getenv("RAZORPAY_KEY_ID", "")
_RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "")
_WEBHOOK_SECRET      = os.getenv("RAZORPAY_WEBHOOK_SECRET", "")
_DEV_MODE            = os.getenv("SMARTKCET_DEV_MODE", "0") == "1"
_KEYS_CONFIGURED     = (
    bool(_RAZORPAY_KEY_ID)
    and not _RAZORPAY_KEY_ID.endswith("YourKeyIdHere")
    and bool(_RAZORPAY_KEY_SECRET)
    and not _RAZORPAY_KEY_SECRET.endswith("YourKeySecretHere")
)

# Lazy-load the Razorpay client so import never fails even without the package
_razorpay_client: Any = None


def _get_client() -> Any:
    global _razorpay_client
    if _razorpay_client is not None:
        return _razorpay_client
    try:
        import razorpay  # type: ignore
        _razorpay_client = razorpay.Client(
            auth=(_RAZORPAY_KEY_ID, _RAZORPAY_KEY_SECRET)
        )
        return _razorpay_client
    except Exception as exc:
        logger.warning("Razorpay client init failed: %s", exc)
        return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def create_order(
    amount_paise: int,
    receipt: str,
    notes: Optional[dict] = None,
) -> dict[str, Any]:
    """Create a Razorpay order.

    Returns dict with at minimum: id, amount, currency, receipt, status.

    In dev mode or when keys are not configured, returns a mock order so
    developers can test the full UI flow without real Razorpay credentials.
    """
    if not _KEYS_CONFIGURED or _DEV_MODE:
        mock_id = "order_mock_" + uuid.uuid4().hex[:16]
        logger.info("DEV MODE — returning mock Razorpay order %s", mock_id)
        return {
            "id": mock_id,
            "amount": amount_paise,
            "currency": "INR",
            "receipt": receipt,
            "status": "created",
            "_mock": True,
        }

    client = _get_client()
    if client is None:
        raise RuntimeError("Razorpay client unavailable")

    data = {
        "amount":   amount_paise,
        "currency": "INR",
        "receipt":  receipt,
        "notes":    notes or {},
    }
    order = client.order.create(data=data)
    logger.info("Created Razorpay order %s for ₹%.2f", order["id"], amount_paise / 100)
    return order


def verify_payment_signature(
    order_id: str,
    payment_id: str,
    signature: str,
) -> bool:
    """Verify the Razorpay payment signature (client-side success).

    This is the lightweight verification for the /verify endpoint hit
    AFTER the user pays. The authoritative activation comes from the
    webhook (verify_webhook_signature below).
    """
    if not _KEYS_CONFIGURED:
        logger.warning("DEV MODE — skipping signature verification")
        return True

    key_secret = _RAZORPAY_KEY_SECRET.encode()
    message = f"{order_id}|{payment_id}".encode()
    expected = hmac.new(key_secret, message, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


def verify_webhook_signature(body: bytes, header_signature: str) -> bool:
    """Verify Razorpay webhook HMAC-SHA256 signature.

    body             — raw request body bytes
    header_signature — value of X-Razorpay-Signature header

    Returns True if the webhook is authentic.
    """
    if not _WEBHOOK_SECRET or _WEBHOOK_SECRET.endswith("YourWebhookSecretHere"):
        # No webhook secret configured — in dev mode allow all, in prod reject all
        if _DEV_MODE:
            logger.warning("DEV MODE — webhook secret not configured, accepting webhook")
            return True
        logger.error("PROD — webhook secret not configured, rejecting webhook")
        return False

    expected = hmac.new(
        _WEBHOOK_SECRET.encode(), body, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, header_signature)


def get_public_key() -> str:
    """Return the Razorpay key_id for the frontend (safe to expose)."""
    return _RAZORPAY_KEY_ID


def is_configured() -> bool:
    return _KEYS_CONFIGURED
