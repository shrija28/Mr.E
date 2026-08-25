"""Admin leaderboard endpoint — full ranked list with optional subject filter.

Implements GET /api/admin/leaderboard?subject=... (REQ-11.4, REQ-11.5, REQ-11.7).

Returns:
- The full ranked list with names, KCET IDs, composite scores, subject-wise averages
- Optional subject filter parameter
- Total count of ranked students
"""

from __future__ import annotations
import os

from typing import Any, Dict, List, Optional

import os
from flask import Blueprint, request, g, make_response, jsonify, Response
from sqlalchemy.orm import Session

from ..db.session import get_async_session as get_session
from ..leaderboard.service import get_leaderboard
from ..middleware.rbac import require_admin

router = Blueprint("admin_leaderboard", __name__)


@router.route("/leaderboard", methods=["GET"])
def admin_leaderboard()-> Dict[str, Any]:    
    _admin = require_admin()
    from flask import g
    db = getattr(g, "db", None)
    session = db
    from flask import request
    subject = request.args.get("subject", None)
    """Return the full ranked leaderboard with optional subject filter.

    When *subject* is provided, only submissions for that subject are
    considered and students with zero submissions in that subject are
    excluded (REQ-11.7).
    """
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

    return {
        "total_ranked": len(ranked),
        "subject": subject,
        "entries": entries,
    }


__all__ = ["router"]
