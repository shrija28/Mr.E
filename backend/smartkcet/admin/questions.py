"""Admin Question_Bank management endpoints using Flask Blueprint."""

from __future__ import annotations

import logging
import uuid
from typing import Any, Optional

from flask import Blueprint, jsonify, request
from sqlalchemy import delete, func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from ..db.models import Question, Subject
from ..db.session import get_db
from ..middleware.rbac import require_admin

logger = logging.getLogger("smartkcet.admin.questions")

router = Blueprint("admin_questions", __name__, url_prefix="/api/admin")

PAGE_SIZE = 100
MAX_PAGE_SIZE = 200
INSUFFICIENT_THRESHOLD = 20


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


def _serialise_question(row: Question) -> dict[str, Any]:
    created_at = row.created_at
    return {
        "id": str(row.id),
        "subject": row.subject,
        "question": row.question_text,
        "question_text": row.question_text,
        "options": row.options,
        "correct_option": row.correct_option,
        "topic": row.topic,
        "explanation": row.explanation,
        "source_type": row.source_type,
        "generation_batch_id": str(row.generation_batch_id) if row.generation_batch_id else None,
        "created_at": created_at.isoformat() if created_at is not None else None,
    }


def _counts_by_subject(session: Session) -> dict[str, int]:
    rows = session.execute(
        select(Question.subject, func.count(Question.id))
        .where(Question.institution_id.is_(None))
        .group_by(Question.subject)
    ).all()
    found = {subject: int(count) for subject, count in rows}
    return {s.value: int(found.get(s.value, 0)) for s in Subject}


@router.route("/questions/counts", methods=["GET"])
@require_admin
def list_counts():
    session: Session = get_db()
    counts = _counts_by_subject(session)
    insufficient = {
        subject_value: total < INSUFFICIENT_THRESHOLD
        for subject_value, total in counts.items()
    }
    return jsonify({
        "counts": counts,
        "insufficient": insufficient,
        "threshold": INSUFFICIENT_THRESHOLD,
    }), 200


@router.route("/questions", methods=["GET"])
@require_admin
def list_questions():
    session: Session = get_db()
    subject = request.args.get("subject")
    raw_page = request.args.get("page", 1)
    raw_page_size = request.args.get("page_size")

    try:
        page = max(1, int(raw_page))
    except (ValueError, TypeError):
        page = 1

    selected: Optional[Subject] = None
    if subject is not None:
        normalised = _normalise_subject(subject)
        if normalised is None:
            allowed = [s.value for s in Subject]
            return _validation_error(f"subject must be one of {allowed}", field="subject")
        selected = normalised

    page_size = PAGE_SIZE
    if raw_page_size is not None:
        try:
            parsed = int(raw_page_size)
            if parsed < 1:
                return _validation_error("page_size must be >= 1", field="page_size")
            page_size = min(parsed, MAX_PAGE_SIZE)
        except ValueError:
            return _validation_error("page_size must be an integer", field="page_size")

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

    return jsonify({
        "questions": [_serialise_question(r) for r in rows],
        "total": total,
        "page": page,
        "page_size": page_size,
        "subject": selected.value if selected is not None else None,
        "counts_by_subject": _counts_by_subject(session),
    }), 200


@router.route("/questions/<question_id>", methods=["DELETE"])
@require_admin
def delete_question(question_id: str):
    session: Session = get_db()
    try:
        qid = uuid.UUID(question_id)
    except (ValueError, TypeError):
        return jsonify({"deleted": False, "error": "validation_error", "id": question_id}), 400

    try:
        result = session.execute(
            delete(Question).where(Question.id == qid)
        )
        rows_affected = int(result.rowcount or 0)
        if rows_affected <= 0:
            session.rollback()
            return jsonify({"deleted": False, "error": "not_found", "id": question_id}), 404
        session.commit()
    except SQLAlchemyError as exc:
        session.rollback()
        error_name = type(exc).__name__ or "database_error"
        logger.warning("DELETE /api/admin/questions/%s failed: %s", question_id, exc)
        return jsonify({"deleted": False, "error": error_name, "id": question_id}), 500

    return jsonify({"deleted": True, "id": question_id}), 200


__all__ = ["router", "PAGE_SIZE", "INSUFFICIENT_THRESHOLD"]
