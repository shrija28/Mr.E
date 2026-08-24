"""Admin leaderboard endpoint using Flask Blueprint."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from flask import Blueprint, jsonify, request
from sqlalchemy.orm import Session

from ..db.session import get_db
from ..leaderboard.service import get_leaderboard
from ..middleware.rbac import require_admin

router = Blueprint("admin_leaderboard", __name__, url_prefix="/api/admin")


@router.route("/leaderboard", methods=["GET"])
@require_admin
def admin_leaderboard():
    session: Session = get_db()
    subject = request.args.get("subject")

    ranked = get_leaderboard(session, subject=subject)

    entries: List[Dict[str, Any]] = []
    for entry in ranked:
        entries.append(
            {
                "rank": entry.rank,
                "display_name": entry.display_name,
                "kcet_student_id": entry.kcet_student_id,
                "composite_score": round(entry.composite_score, 4),
                "average_score": round(entry.average_score, 4),
                "attempt_count": entry.attempt_count,
            }
        )

    return jsonify({
        "total_ranked": len(ranked),
        "subject": subject,
        "entries": entries,
    }), 200


__all__ = ["router"]
