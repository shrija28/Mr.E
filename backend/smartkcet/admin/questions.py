"""Admin Question_Bank management endpoints.

Implements task 6.1, 6.3, 6.4 / REQ-6.1, REQ-6.2, REQ-6.3, REQ-6.4, REQ-6.5
and the admin-side contract documented in design.md §2.x for the
Question_Bank surface.

* Mounted under ``/api/admin/questions`` from :mod:`smartkcet.admin`.
* Every endpoint is admin-only — guarded by
  :func:`smartkcet.middleware.rbac.require_admin`.
* The 400 envelope shape (``{error, message[, field]}``) mirrors
  :mod:`.upload` and :mod:`.generate` so the admin UI can handle
  validation failures uniformly.

Endpoints
---------

``GET /api/admin/questions``
    Paginated list with optional ``subject`` filter.  Page size is fixed
    at :data:`PAGE_SIZE` (50) per REQ-6.1; any client-supplied
    ``page_size`` query parameter is silently capped at this maximum so
    no caller can pull more than 50 rows in one request.  Response
    embeds ``counts_by_subject`` for the four KCET subjects so the
    frontend can render the per-subject totals (REQ-6.3) without a
    second request.

``DELETE /api/admin/questions/{question_id}``
    Reported-status delete (REQ-6.2 / REQ-6.5).  The frontend trusts the
    JSON envelope, not the HTTP layer, so a DB-level failure rolls back
    the transaction and returns ``{deleted: false, error: ...}`` even if
    the row was technically removed before the error.  Missing rows
    return 404 with the same shape.

``GET /api/admin/questions/counts``
    Per-subject totals plus an ``insufficient`` flag (REQ-6.4) so the
    admin UI can render the "fewer than 20 questions" warning without
    duplicating the threshold logic on the client.  The threshold is
    exposed in the response so a future change to the constant only
    needs to touch this module.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any, Optional

from fastapi import APIRouter, Depends, Path, Query, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy import delete, func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from ..db.models import Question, Subject
from ..db.session import get_async_session as get_session
from ..middleware.rbac import require_admin

logger = logging.getLogger("smartkcet.admin.questions")

router = APIRouter()


# REQ-6.1 — fixed page size.  Defined as a module-level constant so the
# smoke test and any future admin UI can import the same value rather
# than duplicating the magic number.
PAGE_SIZE = 50

# REQ-6.4 — "insufficient questions" threshold.  Exposed in the counts
# response so the frontend never has to hardcode this number.
INSUFFICIENT_THRESHOLD = 20


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


def _serialise_question(row: Question) -> dict[str, Any]:
    """Map a :class:`Question` ORM row to the admin-list JSON shape."""

    created_at = row.created_at
    return {
        "id": str(row.id),
        "subject": row.subject,
        "question": row.question_text,
        "question_text": row.question_text,
        "options": row.options,
        "correct_option": row.correct_option,
        "topic": row.topic,
        "generation_batch_id": str(row.generation_batch_id),
        # ISO-8601 with naive UTC timestamps (matches what the ORM stores).
        "created_at": created_at.isoformat() if created_at is not None else None,
    }


def _counts_by_subject(session: Session) -> dict[str, int]:
    """Return a ``{subject_value: count}`` map for platform-wide (admin) questions only.

    Only counts questions with ``institution_id IS NULL`` so institution-uploaded
    questions never appear in the admin question bank.
    """

    rows = session.execute(
        select(Question.subject, func.count(Question.id))
        .where(Question.institution_id.is_(None))
        .group_by(Question.subject)
    ).all()
    found = {subject: int(count) for subject, count in rows}
    return {s.value: int(found.get(s.value, 0)) for s in Subject}


# ---------------------------------------------------------------------------
# GET /api/admin/questions/counts  (must be declared BEFORE the {question_id}
#                                   route so FastAPI's path matcher does not
#                                   try to coerce "counts" into a UUID).
# ---------------------------------------------------------------------------


@router.get("/questions/counts")
def list_counts(
    session: Session = Depends(get_session),
    _admin: dict = Depends(require_admin),
) -> Any:
    """Return per-subject totals + ``insufficient`` flags + the threshold.

    REQ-6.4: a subject is "insufficient" when its total question count
    is strictly less than :data:`INSUFFICIENT_THRESHOLD`.  The frontend
    uses this to decide whether to show the "fewer than 20" warning.
    """

    counts = _counts_by_subject(session)
    insufficient = {
        subject_value: total < INSUFFICIENT_THRESHOLD
        for subject_value, total in counts.items()
    }
    return {
        "counts": counts,
        "insufficient": insufficient,
        "threshold": INSUFFICIENT_THRESHOLD,
    }


# ---------------------------------------------------------------------------
# GET /api/admin/questions
# ---------------------------------------------------------------------------


@router.get("/questions")
def list_questions(
    request: Request,
    subject: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    session: Session = Depends(get_session),
    _admin: dict = Depends(require_admin),
) -> Any:
    """List questions with optional subject filter and stable pagination.

    Query parameters
    ----------------
    subject
        Optional KCET subject (one of ``Biology``, ``Physics``,
        ``Chemistry``, ``Mathematics``).  Anything else short-circuits
        to a 400 envelope before any DB call is made.
    page
        1-indexed page number.  Values < 1 are rejected by FastAPI's
        ``Query(ge=1)`` and surface as a standard 422.
    page_size
        Accepted for forward compatibility but **always capped** at
        :data:`PAGE_SIZE` (REQ-6.1: "at most 50 questions per page").
        Reading the raw query string lets us cap silently rather than
        introducing a hard-coded ``page_size`` parameter that would
        misleadingly suggest the cap is negotiable.
    """

    # Validate the subject filter up-front so we never run a SELECT with
    # a bogus filter value.
    selected: Optional[Subject] = None
    if subject is not None:
        normalised = _normalise_subject(subject)
        if normalised is None:
            allowed = [s.value for s in Subject]
            return _validation_error(
                f"subject must be one of {allowed}",
                field="subject",
            )
        selected = normalised

    # ``page_size`` is intentionally not exposed as a typed parameter:
    # the spec pins the page size at 50 and the cap should hold even
    # when callers try to override it.
    requested_size = request.query_params.get("page_size")
    page_size = PAGE_SIZE
    if requested_size is not None:
        try:
            parsed = int(requested_size)
        except ValueError:
            return _validation_error(
                "page_size must be an integer",
                field="page_size",
            )
        if parsed < 1:
            return _validation_error(
                "page_size must be >= 1",
                field="page_size",
            )
        page_size = min(parsed, PAGE_SIZE)

    # Build the base SELECT — platform-wide questions only (institution_id IS NULL).
    # Institution-uploaded questions are scoped to their institution and must
    # never appear in the admin question bank view.
    base_filter = [Question.institution_id.is_(None)]
    if selected is not None:
        base_filter.append(Question.subject == selected.value)

    total_stmt = select(func.count(Question.id))
    if base_filter:
        total_stmt = total_stmt.where(*base_filter)
    total = int(session.execute(total_stmt).scalar_one())

    page_stmt = (
        select(Question)
        .order_by(Question.created_at.desc(), Question.id.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    if base_filter:
        page_stmt = page_stmt.where(*base_filter)
    rows = session.execute(page_stmt).scalars().all()

    return {
        "questions": [_serialise_question(r) for r in rows],
        "total": total,
        "page": page,
        "page_size": page_size,
        "subject": selected.value if selected is not None else None,
        "counts_by_subject": _counts_by_subject(session),
    }


# ---------------------------------------------------------------------------
# DELETE /api/admin/questions/{question_id}
# ---------------------------------------------------------------------------


@router.delete("/questions/{question_id}")
def delete_question(
    question_id: uuid.UUID = Path(...),
    session: Session = Depends(get_session),
    _admin: dict = Depends(require_admin),
) -> Any:
    """Delete a single question, reporting DB-level success or failure.

    REQ-6.2 / REQ-6.5 — the response's ``deleted`` flag mirrors the
    DB report:

    * ``rows_affected > 0``  → 200 ``{deleted: true, id}``
    * ``rows_affected == 0`` → 404 ``{deleted: false, error: "not_found"}``
    * any :class:`SQLAlchemyError` → rollback, 500 ``{deleted: false,
      error: "<error class name>"}``

    The frontend follows this report verbatim (REQ-6.5: "treat the
    operation as failed and SHALL keep the question visible") so we
    never auto-retry — a user-visible error is the contract.
    """

    qid_str = str(question_id)

    try:
        result = session.execute(
            delete(Question).where(Question.id == question_id)
        )
        rows_affected = int(result.rowcount or 0)
        if rows_affected <= 0:
            # Nothing to commit — release the transactional state so the
            # session is reusable.
            session.rollback()
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"deleted": False, "error": "not_found", "id": qid_str},
            )
        session.commit()
    except SQLAlchemyError as exc:
        session.rollback()
        # Surface the SQLAlchemy error class name (e.g. ``IntegrityError``,
        # ``OperationalError``) so the admin UI can display a meaningful
        # diagnostic without leaking the raw SQL message.
        error_name = type(exc).__name__ or "database_error"
        logger.warning("DELETE /api/admin/questions/%s failed: %s", qid_str, exc)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"deleted": False, "error": error_name, "id": qid_str},
        )

    return {"deleted": True, "id": qid_str}


__all__ = [
    "router",
    "PAGE_SIZE",
    "INSUFFICIENT_THRESHOLD",
]
