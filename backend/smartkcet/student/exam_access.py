"""POST /api/exam/check-access using Flask Blueprint."""

from __future__ import annotations

import logging
from typing import Any

from flask import Blueprint, jsonify, request
from sqlalchemy.orm import Session

from ..db.session import get_db
from ..middleware.rbac import current_user, require_student

logger = logging.getLogger("smartkcet.exam.check_access")

router = Blueprint("exam_access", __name__, url_prefix="/api/exam")


@router.route("/check-access", methods=["POST"])
@require_student
def check_exam_access():
    session: Session = get_db()
    user = current_user(request, session)
    if user is None:
        return jsonify({"error": "auth_required", "message": "Authentication required."}), 401

    from ..subscription.service import SubscriptionService

    service = SubscriptionService(session)
    try:
        effective = service.get_effective_status(user.id)
    except Exception as exc:
        logger.warning("check_exam_access: get_effective_status failed for user %s: %s", user.kcet_student_id, exc)
        return jsonify({
            "error": "subscription_verification_failed",
            "message": "Unable to verify subscription status. Please try again.",
            "retry_after_sec": 5,
        }), 503

    if not effective.has_subscription or not effective.is_active:
        return jsonify({
            "error_code": "subscription_required",
            "error": "subscription_required",
            "message": "No active subscription. Please activate a plan to start exams.",
        }), 403

    if user.student_subtype == "institution_linked":
        from ..subscription.usage import UsageTracker

        tracker = UsageTracker(session)
        try:
            result = tracker.can_start_exam(user.id)
        except Exception as exc:
            logger.warning("check_exam_access: UsageTracker failed: %s", exc)
            return jsonify({
                "access": "granted",
                "quota_type": "institution",
                "remaining_attempts": None,
            }), 200

        if not result.can_start:
            return jsonify({
                "error_code": "institution_quota_exhausted",
                "error": "institution_quota_exhausted",
                "message": result.reason or "Institution quota reached.",
                "remaining": result.remaining_attempts or 0,
                "reset_date": result.resets_at.isoformat() if result.resets_at else None,
            }), 403

        return jsonify({
            "access": "granted",
            "quota_type": "institution",
            "remaining_attempts": result.remaining_attempts,
        }), 200

    if effective.is_trial:
        from ..subscription.usage import UsageTracker

        tracker = UsageTracker(session)
        try:
            result = tracker.can_start_exam(user.id)
        except Exception as exc:
            logger.warning("check_exam_access: UsageTracker trial failed: %s", exc)
            return jsonify({
                "access": "granted",
                "quota_type": "trial",
                "remaining_attempts": None,
            }), 200

        if not result.can_start:
            return jsonify({
                "error_code": "quota_exhausted",
                "error": "quota_exhausted",
                "message": result.reason or "Free Trial limit reached (5 lifetime attempts).",
                "remaining": 0,
                "upgrade_url": "/subscription",
            }), 403

        return jsonify({
            "access": "granted",
            "quota_type": "trial",
            "remaining_attempts": result.remaining_attempts,
        }), 200

    return jsonify({
        "access": "granted",
        "quota_type": "unlimited",
        "remaining_attempts": None,
    }), 200


__all__ = ["router"]
