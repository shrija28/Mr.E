"""Student leaderboard endpoint using Flask Blueprint."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from flask import Blueprint, jsonify, request
from sqlalchemy.orm import Session

from ..db.session import get_db
from ..leaderboard.service import get_leaderboard
from ..middleware.rbac import current_user, require_student
from ..subscription.dependencies import get_access_control

router = Blueprint("student_leaderboard", __name__, url_prefix="/api/student")


@router.route("/leaderboard/me", methods=["GET"])
@require_student
def student_leaderboard_me():
    session: Session = get_db()
    user = current_user(request, session)
    if not user:
        return jsonify({"error": "auth_required", "message": "User not found"}), 401
    
    token_payload = getattr(request, "token_payload", {}) or {}
    student_kcet_id: str = token_payload.get("sub", "")

    ranked = get_leaderboard(session)
    total_ranked = len(ranked)

    top_3: List[Dict[str, Any]] = []
    for entry in ranked[:3]:
        top_3.append(
            {
                "rank": entry.rank,
                "display_name": entry.display_name,
                "kcet_student_id": entry.kcet_student_id,
                "composite_score": round(entry.composite_score, 4),
            }
        )

    my_entry: Optional[Dict[str, Any]] = None
    my_rank: Any = "—"

    for entry in ranked:
        if entry.kcet_student_id == student_kcet_id or entry.student_id == str(user.id):
            my_rank = entry.rank
            my_entry = {
                "rank": entry.rank,
                "composite_score": round(entry.composite_score, 4),
                "average_score": round(entry.average_score, 4),
            }
            break

    leaderboard_data = {
        "my_rank": my_rank,
        "total_ranked": total_ranked,
        "top_3": top_3,
        "me": my_entry,
    }
    
    access_control = get_access_control(session)
    filtered_data = access_control.filter_leaderboard_data(leaderboard_data, user.id)
    
    return jsonify(filtered_data), 200


__all__ = ["router"]
