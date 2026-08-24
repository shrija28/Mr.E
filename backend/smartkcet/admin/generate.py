"""Admin question-generation endpoint using Flask Blueprint."""

from __future__ import annotations

import logging
import random
import uuid
from typing import Any, Optional

from flask import Blueprint, jsonify, request
from sqlalchemy import select, func as sa_func
from sqlalchemy.orm import Session

from ..db.models import Question, Subject
from ..db.session import get_db
from ..middleware.rbac import require_admin

logger = logging.getLogger("smartkcet.admin.generate")

router = Blueprint("admin_generate", __name__, url_prefix="/api/admin")

SET_LABELS = ("A", "B", "C", "D")
QUESTIONS_PER_SET = 20
MIN_TOTAL_QUESTIONS = 20


def _validation_error(message: str, field: Optional[str] = None):
    body: dict[str, Any] = {"error": "validation_error", "message": message}
    if field is not None:
        body["field"] = field
    return jsonify(body), 400


def _normalise_subject(value: Optional[str]) -> Optional[Subject]:
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    if not stripped:
        return None
    try:
        return Subject(stripped)
    except ValueError:
        return None


def _question_row_to_dict(row: Question, set_label: str, index: int) -> dict:
    return {
        "id": f"{set_label}-{index}",
        "q": row.question_text,
        "type": "MCQ",
        "topic": row.topic or "General",
        "opts": row.options if isinstance(row.options, list) else [],
        "ans": int(row.correct_option) if str(row.correct_option).isdigit() else 0,
        "marks": 1,
        "exp": row.explanation or "",
    }


@router.route("/generate", methods=["POST"])
@require_admin
def generate():
    session: Session = get_db()
    data = request.get_json(silent=True) or request.form or {}
    raw_subject = data.get("subject")

    selected = _normalise_subject(raw_subject)
    if selected is None:
        allowed = [s.value for s in Subject]
        return _validation_error(f"subject is required and must be one of {allowed}", field="subject")

    subject_name = selected.value

    stmt = (
        select(Question)
        .where(Question.subject == subject_name)
        .order_by(sa_func.random())
    )
    all_questions = list(session.execute(stmt).scalars().all())
    total_available = len(all_questions)

    if total_available < MIN_TOTAL_QUESTIONS:
        return _validation_error(
            f"Not enough questions in the database for {subject_name}. Found {total_available}, need at least {MIN_TOTAL_QUESTIONS}.",
            field="subject",
        )

    random.shuffle(all_questions)

    num_sets = len(SET_LABELS)
    questions_per_set = min(QUESTIONS_PER_SET, total_available // num_sets)

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

    return jsonify({
        "success": True,
        "added": total_added,
        "batch_id": str(batch_id),
        "subject": subject_name,
        "sets": sets,
    }), 200


__all__ = ["router", "SET_LABELS", "QUESTIONS_PER_SET"]
