"""Admin-facing operations (question bank, exam authoring, analytics).

This module hosts the ``/api/admin`` router that is mounted in
:mod:`smartkcet.main`.  Sub-routers are composed here so each functional
area (upload, generate, question bank, exam authoring, analytics) can
own its own module without leaking implementation details to the
application factory.

Currently mounted:

* ``GET  /api/admin/ping``      — task 3.5 RBAC smoke endpoint.
* ``POST /api/admin/upload``    — task 4.3 file upload + per-subject
                                   FAISS indexing (see :mod:`.upload`).
* ``POST /api/admin/generate``  — task 4.5 transactional 80-question
                                   generation batch (see :mod:`.generate`).
* ``GET  /api/admin/questions`` — task 6.1 paginated listing with
                                   subject filter (see :mod:`.questions`).
* ``DELETE /api/admin/questions/{id}`` — task 6.3 reported-status
                                   delete (see :mod:`.questions`).
* ``GET  /api/admin/questions/counts`` — task 6.4 per-subject totals
                                   plus REQ-6.4 insufficient flags.
* ``POST /api/admin/exams``, ``PATCH /api/admin/exams/{id}``,
  ``GET /api/admin/exams``        — task 7.1 / 7.3 atomic exam
                                   creation, publish toggle, and exam
                                   list (see :mod:`.exams`).

Future tasks (7.x exam authoring, 11.x analytics) follow the same
pattern: define a sub-router in its own module and call
``router.include_router(...)`` here.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends

from ..middleware.rbac import require_admin
from .analytics import router as analytics_router
from .dashboard import router as dashboard_router
from .exams import router as exams_router
from .generate import router as generate_router
from .leaderboard import router as leaderboard_router
from .platform_admin_routes import router as platform_admin_router
from .questions import router as questions_router
from .upload import router as upload_router
from .syllabus import router as syllabus_router

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/ping")
def admin_ping(payload: dict[str, Any] = Depends(require_admin)) -> dict[str, Any]:
    """Smoke-test endpoint — confirms the admin RBAC dependency is wired."""

    return {"status": "ok", "role": payload.get("role"), "sub": payload.get("sub")}


# Mount the upload sub-router under the same ``/api/admin`` prefix.  The
# sub-router declares relative paths (``/upload``) and applies its own
# ``Depends(require_admin)`` per endpoint so the RBAC contract from
# design.md §1.6 is enforced at the endpoint level.
router.include_router(upload_router)
router.include_router(generate_router)
router.include_router(questions_router)
router.include_router(exams_router)
router.include_router(leaderboard_router)
router.include_router(analytics_router)
router.include_router(dashboard_router)
router.include_router(dashboard_router)
router.include_router(platform_admin_router)
router.include_router(syllabus_router)


__all__ = ["router"]
