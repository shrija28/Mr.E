"""Student-facing operations (exam selection, submission, dashboard).

This module hosts the ``/api/student`` router that is mounted in
:mod:`smartkcet.main`.

Mounted endpoints:

* ``GET  /api/student/ping``                       — RBAC smoke-test.
* ``GET  /api/student/exams``                      — task 7.5 published-exam listing.
* ``POST /api/student/submit``                     — task 8.1 score + persist.
* ``GET  /api/student/exams/{exam_set_id}/status`` — task 8.3 already-completed check.
* ``GET  /api/student/submissions``                — task 8.5 history list.
* ``GET  /api/student/submissions/{id}``           — task 8.5 detail drawer.
* ``GET  /api/student/leaderboard/me``             — task 10.9 personal rank + top-3.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends

from ..middleware.rbac import require_student
from .exams import router as exams_router
from .leaderboard import router as leaderboard_router
from .submissions import router as submissions_router
from .submit import router as submit_router
from .recommendations import router as recommendations_router
from .rank_suggestions import router as rank_suggestions_router

router = APIRouter(prefix="/api/student", tags=["student"])


@router.get("/ping")
def student_ping(
    payload: dict[str, Any] = Depends(require_student),
) -> dict[str, Any]:
    """Smoke-test endpoint — confirms the student RBAC dependency is wired."""

    return {"status": "ok", "role": payload.get("role"), "sub": payload.get("sub")}


# Mount the sub-routers under the same ``/api/student`` prefix.  Each
# sub-router declares relative paths (``/exams``, ``/submit``,
# ``/submissions``) and applies its own ``Depends(require_student)`` per
# endpoint so the RBAC contract from design.md §1.6 is enforced at the
# endpoint level.
router.include_router(exams_router)
router.include_router(submit_router)
router.include_router(submissions_router)
router.include_router(leaderboard_router)
router.include_router(recommendations_router)
router.include_router(rank_suggestions_router)


__all__ = ["router"]
