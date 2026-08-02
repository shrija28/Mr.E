"""Admin aggregate analytics endpoint.

Implements task 11.1 / REQ-12.1, REQ-12.2, REQ-12.3, REQ-12.6.

Provides ``GET /api/admin/analytics`` — an admin-only endpoint that
returns submission data across all students, reshaped to match the
``submissions`` array consumed by ``dashboard.js`` so the existing chart
code (radar, bar, doughnut) can be reused unchanged on the admin
analytics page.

Filters
-------

All filters are optional and combinable:

* ``subject`` — one of Biology / Physics / Chemistry / Mathematics.
* ``student`` — a KCET Student ID (e.g. ``KCET0001``).
* ``set``     — an ``exam_set_id`` (UUID).
* ``status``  — ``completed`` or ``in_progress``.

Pagination
----------

* ``limit``  — default 100, max 500.
* ``offset`` — default 0.

Empty-state
-----------

When the filtered subset is empty the response carries
``{empty: true, submissions: [], total: 0, filters: {...}}`` so the
frontend can render the empty-state message instead of empty charts
(REQ-12.6).
"""

from __future__ import annotations

import uuid
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..db.models import Exam, ExamSet, Submission, Subject, User
from ..db.session import get_async_session as get_session
from ..middleware.rbac import require_admin, require_authenticated

router = APIRouter()

_DEFAULT_LIMIT = 100
_MAX_LIMIT = 500


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _validation_error(message: str, field: Optional[str] = None) -> JSONResponse:
    """Return a 400 envelope identical in shape to other admin endpoints."""

    body: dict[str, Any] = {"error": "validation_error", "message": message}
    if field is not None:
        body["field"] = field
    return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=body)


def _normalise_subject(value: Optional[str]) -> Optional[Subject]:
    """Return the matching :class:`Subject` enum or ``None`` for invalid input."""

    if not isinstance(value, str):
        return None
    stripped = value.strip()
    if not stripped:
        return None
    try:
        return Subject(stripped)
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# GET /api/admin/analytics  (REQ-12.1, REQ-12.2, REQ-12.3, REQ-12.6)
# ---------------------------------------------------------------------------


@router.get("/analytics")
def get_analytics(
    subject: Optional[str] = Query(default=None),
    student: Optional[str] = Query(default=None),
    set: Optional[str] = Query(default=None, alias="set"),
    status_filter: Optional[str] = Query(default=None, alias="status"),
    limit: int = Query(default=_DEFAULT_LIMIT, ge=1),
    offset: int = Query(default=0, ge=0),
    session: Session = Depends(get_session),
    _admin: dict = Depends(require_authenticated),
) -> Any:
    """Return aggregate analytics across all students with optional filters.

    The response shape matches the ``submissions`` array that
    ``dashboard.js`` already consumes, augmented with ``student_name``
    and ``kcet_student_id`` fields for the admin results table.

    Default sort: ``submitted_at DESC`` (REQ-12.3).
    
    **Institution Integration (REQ-7.4, 9.7):**
    - Platform admins see all submissions across all students
    - Institution admins see only submissions from students linked to their institution
    """
    
    # Require admin role (platform_admin or institution_admin)
    admin_role = _admin.get("role")
    if admin_role not in ("platform_admin", "institution_admin"):
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={
                "error": "forbidden",
                "message": "Admin access required",
            },
        )

    # --- Validate filters ---------------------------------------------------

    selected_subject: Optional[Subject] = None
    if subject is not None:
        normalised = _normalise_subject(subject)
        if normalised is None:
            allowed = [s.value for s in Subject]
            return _validation_error(
                f"subject must be one of {allowed}",
                field="subject",
            )
        selected_subject = normalised

    # Validate status filter
    valid_statuses = ("completed", "in_progress")
    if status_filter is not None and status_filter not in valid_statuses:
        return _validation_error(
            f"status must be one of {list(valid_statuses)}",
            field="status",
        )

    # Validate set filter (must be a valid UUID)
    set_uuid: Optional[uuid.UUID] = None
    if set is not None:
        try:
            set_uuid = uuid.UUID(set)
        except (ValueError, AttributeError):
            return _validation_error(
                "set must be a valid UUID (exam_set_id)",
                field="set",
            )

    # --- Build query ---------------------------------------------------------

    capped_limit = min(int(limit), _MAX_LIMIT)

    # Build the active filters dict for the response envelope.
    filters_response: dict[str, Any] = {
        "subject": selected_subject.value if selected_subject is not None else None,
        "student": student if student else None,
        "set": set if set else None,
        "status": status_filter if status_filter else None,
    }

    # Core query: submissions joined with exam_sets, exams, and users.
    stmt = (
        select(Submission, ExamSet, Exam, User)
        .join(ExamSet, ExamSet.id == Submission.exam_set_id)
        .join(Exam, Exam.id == ExamSet.exam_id)
        .join(User, User.id == Submission.user_id)
    )

    # Institution scoping (REQ-7.4, 7.7, 9.7):
    # - Platform admins see all submissions
    # - Institution admins see only submissions from their institution's students
    admin_role = _admin.get("role")
    admin_institution_id = _admin.get("institution_id")
    
    if admin_role == "institution_admin" and admin_institution_id is not None:
        # Scope to institution's students only (REQ-7.7)
        stmt = stmt.where(User.institution_id == admin_institution_id)

    # Apply filters
    if selected_subject is not None:
        stmt = stmt.where(Exam.subject == selected_subject.value)

    if student:
        # Filter by KCET Student ID
        stmt = stmt.where(User.kcet_student_id == student.strip())

    if set_uuid is not None:
        stmt = stmt.where(Submission.exam_set_id == set_uuid)

    if status_filter is not None:
        stmt = stmt.where(Submission.status == status_filter)

    # Default sort: submitted_at DESC (REQ-12.3), tie-break on id
    stmt = stmt.order_by(
        Submission.submitted_at.desc(), Submission.id.asc()
    )

    # Get total count before pagination
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = int(session.execute(count_stmt).scalar_one())

    # Apply pagination
    stmt = stmt.offset(offset).limit(capped_limit)

    rows = session.execute(stmt).all()

    # --- Build response ------------------------------------------------------

    submissions: list[dict[str, Any]] = []
    for submission, exam_set, exam, user in rows:
        submitted_at = submission.submitted_at
        submissions.append(
            {
                "id": str(submission.id),
                "student_name": user.display_name,
                "kcet_student_id": user.kcet_student_id or "",
                "exam_set_id": str(submission.exam_set_id),
                "set_label": exam_set.set_label,
                "subject": exam.subject,
                "score_pct": float(submission.score_pct),
                "time_taken_sec": int(submission.time_taken_sec),
                "submitted_at": (
                    submitted_at.isoformat()
                    if submitted_at is not None
                    else None
                ),
                "status": submission.status,
                "pass_flag": float(submission.score_pct) >= 50.0,
            }
        )

    # REQ-12.6: empty filtered subset → empty: true so the frontend
    # renders the empty-state message instead of empty charts.
    is_empty = total == 0

    return {
        "submissions": submissions,
        "total": total,
        "empty": is_empty,
        "filters": filters_response,
        "limit": capped_limit,
        "offset": int(offset),
    }


__all__ = ["router"]
