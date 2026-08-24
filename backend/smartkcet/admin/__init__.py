"""Admin-facing operations Blueprint aggregator."""

from __future__ import annotations

from typing import Any
from flask import Blueprint, jsonify, request

from ..middleware.rbac import require_admin
from .analytics import router as analytics_router
from .dashboard import router as dashboard_router
from .direct_subscribers import router as direct_subscribers_router
from .exams import router as exams_router
from .generate import router as generate_router
from .leaderboard import router as leaderboard_router
from .platform_admin_routes import router as platform_admin_router
from .questions import router as questions_router
from .syllabus import public_router as public_syllabus_router, router as syllabus_router
from .upload import router as upload_router

router = Blueprint("admin", __name__, url_prefix="/api/admin")


@router.route("/ping", methods=["GET"])
@require_admin
def admin_ping():
    token_payload = getattr(request, "token_payload", {}) or {}
    return jsonify({"status": "ok", "role": token_payload.get("role"), "sub": token_payload.get("sub")}), 200


sub_blueprints = [
    analytics_router,
    dashboard_router,
    direct_subscribers_router,
    exams_router,
    generate_router,
    leaderboard_router,
    platform_admin_router,
    questions_router,
    syllabus_router,
    upload_router,
]

__all__ = ["router", "public_syllabus_router", "sub_blueprints"]
