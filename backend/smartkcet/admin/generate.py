"""Admin question-generation endpoint — DB-driven question bank.

Generates 4 paper sets (A/B/C/D) by querying the questions table for the
selected subject and randomly partitioning available questions into
non-overlapping sets.

No external API calls are made. Questions come entirely from the DB,
populated during the upload phase via the MCQ extractor.

NOTE: Groq can be re-enabled as an optional enhancement later if needed.
The import is kept but not used in the current flow.

Response shape on success::

    {
        "success": True,
        "added": 80,
        "batch_id": "<uuid>",
        "subject": "Biology",
        "sets": [
            [{"id": "A-0", "q": "...", "type": "MCQ", "topic": "...", "opts": [...], "ans": 0, "marks": 1}, ...],
            [...],
            [...],
            [...]
        ]
    }
"""

from __future__ import annotations

import random
import uuid
import logging
from typing import Any, Optional

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy import select, func as sa_func
from sqlalchemy.orm import Session

from ..db.models import Question, Subject
from ..db.session import get_async_session as get_session
from ..middleware.rbac import require_admin
from ..rag.store import stores

# NOTE: Groq import kept for potential future re-enablement as an optional
# enhancement (e.g., AI-powered question generation when DB is empty).
# Currently NOT used in the generation flow.
# from ..rag import groq_client as groq_module
# from ..rag.groq_client import GroqAPIKeyError

logger = logging.getLogger("smartkcet.admin.generate")

router = APIRouter()


# Generation contract: 4 sets, up to 20 questions each = up to 80 total.
SET_LABELS = ("A", "B", "C", "D")
QUESTIONS_PER_SET = 20
MIN_TOTAL_QUESTIONS = 20  # Minimum to generate any sets at all


def _validation_error(message: str, field: Optional[str] = None) -> JSONResponse:
    """Return a 400 JSON envelope identical in shape to the upload endpoint."""

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


async def _read_subject(request: Request) -> Optional[str]:
    """Extract the ``subject`` field from form-data or a JSON body.

    Mirrors the dual-input behaviour an admin UI would use: either an
    ``application/x-www-form-urlencoded`` / ``multipart/form-data`` POST
    or an ``application/json`` POST with a ``{"subject": ...}`` body.
    Returns ``None`` when the field is absent or not parseable.
    """

    content_type = (request.headers.get("content-type") or "").lower()

    # Form-data path (mirrors the upload endpoint).
    if "multipart/form-data" in content_type or "application/x-www-form-urlencoded" in content_type:
        try:
            form = await request.form()
        except Exception:
            return None
        value = form.get("subject")
        return value if isinstance(value, str) else None

    # JSON path.
    if "application/json" in content_type:
        try:
            body = await request.json()
        except Exception:
            return None
        if isinstance(body, dict):
            value = body.get("subject")
            return value if isinstance(value, str) else None
        return None

    # No content-type or an unsupported one — try JSON as a best-effort
    # fallback so callers using raw bodies still work, otherwise None.
    try:
        body = await request.json()
    except Exception:
        return None
    if isinstance(body, dict):
        value = body.get("subject")
        return value if isinstance(value, str) else None
    return None


def _question_row_to_dict(row: Question, set_label: str, index: int) -> dict:
    """Convert a Question ORM row to the frontend-expected dict format."""
    return {
        "id": f"{set_label}-{index}",
        "q": row.question_text,
        "type": "MCQ",
        "topic": row.topic or "General",
        "opts": row.options if isinstance(row.options, list) else [],
        "ans": int(row.correct_option) if row.correct_option.isdigit() else 0,
        "marks": 1,
        "exp": row.explanation or "",
    }


@router.post("/generate")
async def generate(
    request: Request,
    session: Session = Depends(get_session),
    _admin: dict = Depends(require_admin),
) -> Any:
    """Generate 4 paper sets from the DB question bank for the chosen subject.

    No external API calls are made. Questions are pulled from the DB
    (populated during upload via MCQ extraction) and randomly partitioned
    into 4 non-overlapping sets.
    """

    raw_subject = await _read_subject(request)
    selected = _normalise_subject(raw_subject)
    if selected is None:
        allowed = [s.value for s in Subject]
        return _validation_error(
            f"subject is required and must be one of {allowed}",
            field="subject",
        )

    subject_name = selected.value

    # Query all questions for this subject from the DB
    stmt = (
        select(Question)
        .where(Question.subject == subject_name)
        .order_by(sa_func.random())
    )
    all_questions = list(session.execute(stmt).scalars().all())
    total_available = len(all_questions)

    logger.info(
        "Generate request for %s: %d questions available in DB",
        subject_name,
        total_available,
    )

    # Need at least MIN_TOTAL_QUESTIONS to generate any sets
    if total_available < MIN_TOTAL_QUESTIONS:
        return _validation_error(
            f"Not enough questions in the database for {subject_name}. "
            f"Found {total_available}, need at least {MIN_TOTAL_QUESTIONS}. "
            f"Please upload more question papers first.",
            field="subject",
        )

    # Shuffle questions randomly
    random.shuffle(all_questions)

    # Determine questions per set based on available count
    # If 80+ available: 4 sets of 20
    # If fewer: distribute evenly across 4 sets
    num_sets = len(SET_LABELS)
    questions_per_set = min(QUESTIONS_PER_SET, total_available // num_sets)

    # Partition questions into 4 non-overlapping sets
    batch_id = uuid.uuid4()
    sets: list[list[dict]] = []

    for i, label in enumerate(SET_LABELS):
        start = i * questions_per_set
        end = start + questions_per_set
        set_rows = all_questions[start:end]

        set_questions = [
            _question_row_to_dict(row, label, idx)
            for idx, row in enumerate(set_rows)
        ]
        sets.append(set_questions)

    total_added = sum(len(s) for s in sets)

    logger.info(
        "Generated %d questions across 4 sets (batch %s) for %s",
        total_added,
        batch_id,
        subject_name,
    )

    return {
        "success": True,
        "added": total_added,
        "batch_id": str(batch_id),
        "subject": subject_name,
        "sets": sets,
    }


__all__ = ["router", "SET_LABELS", "QUESTIONS_PER_SET"]
