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
import os

from typing import Any

import os
from flask import Blueprint, request, g, make_response, jsonify, Response

from ..middleware.rbac import require_student
from .exams import router as exams_router
from .leaderboard import router as leaderboard_router
from .submissions import router as submissions_router
from .submit import router as submit_router
from .recommendations import router as recommendations_router
from .rank_suggestions import router as rank_suggestions_router

router = Blueprint("student___init__", __name__)


@router.route("/ping", methods=["GET"])
def student_ping()-> dict[str, Any]:    
    _student = require_student()
    
    _student = require_student()
    """Smoke-test endpoint — confirms the student RBAC dependency is wired."""

    return {"status": "ok", "role": payload.get("role"), "sub": payload.get("sub")}


# Mount the sub-routers under the same ``/api/student`` prefix.  Each
# sub-router declares relative paths (``/exams``, ``/submit``,
# ``/submissions``) and applies its own ``Depends(require_student)`` per
# endpoint so the RBAC contract from design.md §1.6 is enforced at the
# endpoint level.
router.register_blueprint(exams_router)
router.register_blueprint(submit_router)
router.register_blueprint(submissions_router)
router.register_blueprint(leaderboard_router)
router.register_blueprint(recommendations_router)
router.register_blueprint(rank_suggestions_router)


__all__ = ["router"]
