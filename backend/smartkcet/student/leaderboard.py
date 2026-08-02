"""Student leaderboard endpoint — personal rank + top-3 medals.

Implements GET /api/student/leaderboard/me (REQ-11.4, REQ-11.5, REQ-11.7).

Returns:
- The authenticated student's rank (or "—" if ineligible or Free Trial)
- Total ranked count (number of students on the leaderboard)
- Top-3 medal entries (rank 1, 2, 3 with display_name, kcet_student_id, composite_score)
- The student's own composite_score and average_score if eligible
- Medal tier for Pro subscribers (Gold top 10%, Silver top 25%, Bronze top 50%)

Access Control (Tasks 5.3, 5.4):
- Free Trial: Rank hidden, upgrade prompt shown
- Pro: Rank and medal indicators shown
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from ..db.session import get_async_session as get_session
from ..leaderboard.service import get_leaderboard
from ..middleware.rbac import current_user, require_student
from ..subscription.dependencies import get_access_control

router = APIRouter()


@router.get("/leaderboard/me")
def student_leaderboard_me(
    request: Request,
    payload: Dict[str, Any] = Depends(require_student),
    session: Session = Depends(get_session),
    access_control = Depends(get_access_control),
) -> Dict[str, Any]:
    """Return the student's rank, top-3 medals, and total ranked count.

    The student is identified by the ``sub`` claim in the JWT payload,
    which corresponds to their ``kcet_student_id``.
    
    Access control (Tasks 5.3, 5.4):
    - Free Trial: Rank hidden, upgrade prompt shown
    - Pro: Rank and medal indicators shown
    """
    # Get the authenticated user
    user = current_user(request, session)
    if not user:
        return {
            "error": "auth_required",
            "message": "User not found",
        }
    
    student_kcet_id: str = payload.get("sub", "")

    ranked = get_leaderboard(session)

    total_ranked = len(ranked)

    # Top-3 medal entries
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

    # Find the authenticated student's entry
    my_entry: Optional[Dict[str, Any]] = None
    my_rank: Any = "\u2014"  # em-dash for ineligible

    for entry in ranked:
        if entry.kcet_student_id == student_kcet_id:
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
    
    # Filter leaderboard data based on subscription tier
    filtered_data = access_control.filter_leaderboard_data(leaderboard_data, user.id)
    
    return filtered_data


__all__ = ["router"]
