"""Student-facing operations Blueprint aggregator."""

from __future__ import annotations

from typing import Any
from flask import Blueprint, jsonify, request

from ..middleware.rbac import require_student
from .exams import router as exams_router
from .leaderboard import router as leaderboard_router
from .submissions import router as submissions_router
from .submit import router as submit_router
from .recommendations import router as recommendations_router
from .rank_suggestions import router as rank_suggestions_router

router = Blueprint("student", __name__, url_prefix="/api/student")


@router.route("/ping", methods=["GET"])
@require_student
def student_ping():
    token_payload = getattr(request, "token_payload", {}) or {}
    return jsonify({"status": "ok", "role": token_payload.get("role"), "sub": token_payload.get("sub")}), 200


sub_blueprints = [
    exams_router,
    submit_router,
    submissions_router,
    leaderboard_router,
    recommendations_router,
    rank_suggestions_router,
]

__all__ = ["router", "sub_blueprints"]
