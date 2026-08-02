"""POST /api/exam/check-access — subscription gate for exam start.

Called by ``exam.js`` (via ``SubscriptionAPI.checkExamAccess``) before the
student clicks "Begin Exam".  Returns HTTP 200 when access is granted and
HTTP 403 with a structured error_code when denied.

Supports:
- Personal students (direct_subscriber) — personal subscription / trial
- Institution students (institution_linked)  — inherits institution plan

The endpoint uses ``SubscriptionService.get_effective_status()`` which
already delegates to the institution subscription for institution-linked
students, so no special-casing of the subtype is needed beyond routing
through that helper.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..db.session import get_async_session as get_session
from ..middleware.rbac import current_user, require_student

logger = logging.getLogger("smartkcet.exam.check_access")

router = APIRouter(prefix="/api/exam", tags=["exam"])


class CheckAccessRequest(BaseModel):
    subject: Optional[str] = None
    set: Optional[str] = None


@router.post("/check-access")
def check_exam_access(
    body: CheckAccessRequest,
    request: Request,
    session: Session = Depends(get_session),
    _student: dict = Depends(require_student),
) -> Any:
    """Subscription gate: return 200 if the student may start an exam, 403 otherwise.

    Uses ``SubscriptionService.get_effective_status()`` which correctly
    resolves institution-linked students through their institution's
    subscription — no personal subscription is required for them.
    """

    user = current_user(request, session)
    if user is None:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"error": "auth_required", "message": "Authentication required."},
        )

    # ── Resolve effective subscription ───────────────────────────────────────
    from ..subscription.service import SubscriptionService

    service = SubscriptionService(session)
    try:
        effective = service.get_effective_status(user.id)
    except Exception as exc:
        logger.warning(
            "check_exam_access: get_effective_status failed for user %s: %s",
            user.kcet_student_id, exc,
        )
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "error": "subscription_verification_failed",
                "message": "Unable to verify subscription status. Please try again.",
                "retry_after_sec": 5,
            },
        )

    logger.info(
        "check_exam_access: user=%s subtype=%s eff_status=%s is_active=%s",
        user.kcet_student_id,
        user.student_subtype,
        effective.status,
        effective.is_active,
    )

    # ── No active subscription at all ────────────────────────────────────────
    if not effective.has_subscription or not effective.is_active:
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={
                "error_code": "subscription_required",
                "error": "subscription_required",
                "message": (
                    "No active subscription. Please activate a plan to start exams."
                ),
            },
        )

    # ── Institution student — check institution quota ─────────────────────────
    if user.student_subtype == "institution_linked":
        from ..subscription.usage import UsageTracker

        tracker = UsageTracker(session)
        try:
            result = tracker.can_start_exam(user.id)
        except Exception as exc:
            logger.warning(
                "check_exam_access: UsageTracker.can_start_exam failed for user %s: %s",
                user.kcet_student_id, exc,
            )
            # Fail open — the submit endpoint re-validates
            return {
                "access": "granted",
                "quota_type": "institution",
                "remaining_attempts": None,
            }

        if not result.can_start:
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={
                    "error_code": "institution_quota_exhausted",
                    "error": "institution_quota_exhausted",
                    "message": result.reason or "Institution quota reached.",
                    "remaining": result.remaining_attempts or 0,
                    "reset_date": (
                        result.resets_at.isoformat() if result.resets_at else None
                    ),
                },
            )

        return {
            "access": "granted",
            "quota_type": "institution",
            "remaining_attempts": result.remaining_attempts,
        }

    # ── Personal trial — check 5-attempt cap ─────────────────────────────────
    if effective.is_trial:
        from ..subscription.usage import UsageTracker

        tracker = UsageTracker(session)
        try:
            result = tracker.can_start_exam(user.id)
        except Exception as exc:
            logger.warning(
                "check_exam_access: UsageTracker.can_start_exam (trial) failed for user %s: %s",
                user.kcet_student_id, exc,
            )
            return {
                "access": "granted",
                "quota_type": "trial",
                "remaining_attempts": None,
            }

        if not result.can_start:
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={
                    "error_code": "quota_exhausted",
                    "error": "quota_exhausted",
                    "message": (
                        result.reason
                        or "Free Trial limit reached (5 lifetime attempts)."
                    ),
                    "remaining": 0,
                    "upgrade_url": "/subscription",
                },
            )

        return {
            "access": "granted",
            "quota_type": "trial",
            "remaining_attempts": result.remaining_attempts,
        }

    # ── Personal Pro / grace_period — unlimited ───────────────────────────────
    return {
        "access": "granted",
        "quota_type": "unlimited",
        "remaining_attempts": None,
    }


__all__ = ["router"]
