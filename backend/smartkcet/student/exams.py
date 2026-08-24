"""Student exam-selection endpoints using Flask Blueprint."""

from __future__ import annotations

import logging
import uuid
from typing import Any, Optional

from flask import Blueprint, jsonify, request
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..db.models import Exam, ExamSet, ExamSetQuestion, Question, Subject
from ..db.session import get_db
from ..middleware.rbac import current_user, require_student
from ..subscription.dependencies import get_access_control, require_exam_access

logger = logging.getLogger("smartkcet.student.exams")

router = Blueprint("student_exams", __name__, url_prefix="/api/student")


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


@router.route("/exams", methods=["GET"])
@require_student
def list_published_exams():
    session: Session = get_db()
    subject = request.args.get("subject")
    
    selected: Optional[Subject] = None
    if subject is not None:
        normalised = _normalise_subject(subject)
        if normalised is None:
            allowed = [s.value for s in Subject]
            return _validation_error(f"subject must be one of {allowed}", field="subject")
        selected = normalised

    token_payload = getattr(request, "token_payload", {}) or {}
    student_institution_id = token_payload.get("institution_id")
    student_subtype = token_payload.get("student_subtype", "direct_subscriber")

    stmt = (
        select(Exam, func.count(ExamSet.id).label("set_count"))
        .outerjoin(ExamSet, ExamSet.exam_id == Exam.id)
        .where(Exam.is_published.is_(True))
        .group_by(Exam.id)
        .order_by(Exam.created_at.desc(), Exam.id.asc())
    )

    if student_subtype == "institution_linked" and student_institution_id is not None:
        try:
            inst_uuid = uuid.UUID(student_institution_id)
        except ValueError:
            inst_uuid = student_institution_id
        stmt = stmt.where(Exam.institution_id == inst_uuid)
    else:
        stmt = stmt.where(Exam.institution_id.is_(None))

    if selected is not None:
        stmt = stmt.where(Exam.subject == selected.value)

    rows = session.execute(stmt).all()

    buckets: dict[str, list[dict[str, Any]]] = {}
    for exam, set_count in rows:
        created_at = exam.created_at

        sets_stmt = (
            select(ExamSet)
            .where(ExamSet.exam_id == exam.id)
            .order_by(ExamSet.set_label.asc())
        )
        exam_sets = session.execute(sets_stmt).scalars().all()
        sets_payload = [
            {"exam_set_id": str(es.id), "set_label": es.set_label}
            for es in exam_sets
        ]

        bucket = buckets.setdefault(exam.subject, [])
        bucket.append(
            {
                "exam_id": str(exam.id),
                "exam_name": exam.exam_name,
                "created_at": (
                    created_at.isoformat() if created_at is not None else None
                ),
                "set_count": int(set_count or 0),
                "sets": sets_payload,
            }
        )

    subjects_payload: list[dict[str, Any]] = [
        {
            "subject": subject_value,
            "available_exams": len(exams),
            "exams": exams,
        }
        for subject_value, exams in buckets.items()
    ]

    user = current_user(request, session)
    remaining_attempts_data = None
    if user:
        try:
            access_control = get_access_control(session)
            remaining_attempts_obj = access_control.get_remaining_attempts(user.id)
            if hasattr(remaining_attempts_obj, "model_dump"):
                remaining_attempts_data = remaining_attempts_obj.model_dump(mode="json")
            else:
                remaining_attempts_data = remaining_attempts_obj
        except Exception as exc:
            logger.warning("Failed to get remaining attempts for user %s: %s", user.id, exc)

    return jsonify({
        "subjects": subjects_payload,
        "remaining_attempts": remaining_attempts_data,
    }), 200


@router.route("/exams/<exam_set_id>", methods=["GET"])
@require_student
def get_exam_set_questions(exam_set_id: str):
    session: Session = get_db()
    
    exam_access_res = require_exam_access(request, session)
    if isinstance(exam_access_res, tuple):
        return exam_access_res

    try:
        set_id = uuid.UUID(exam_set_id)
    except (ValueError, TypeError):
        return jsonify({"error": "validation_error", "message": "exam_set_id must be a valid UUID"}), 400

    exam_set = session.get(ExamSet, set_id)
    if exam_set is None:
        return jsonify({"error": "not_found", "resource": "exam_set", "value": str(set_id)}), 404

    exam = session.get(Exam, exam_set.exam_id)
    if exam is None or not exam.is_published:
        return jsonify({"error": "not_found", "message": "Exam is not available"}), 404

    token_payload = getattr(request, "token_payload", {}) or {}
    student_subtype = token_payload.get("student_subtype", "direct_subscriber")
    student_institution_id = token_payload.get("institution_id")

    if student_subtype == "institution_linked":
        if str(exam.institution_id) != str(student_institution_id):
            return jsonify({"error": "not_found", "message": "Exam is not available"}), 404
    else:
        if exam.institution_id is not None:
            return jsonify({"error": "not_found", "message": "Exam is not available"}), 404

    stmt = (
        select(Question, ExamSetQuestion.order_index)
        .join(ExamSetQuestion, ExamSetQuestion.question_id == Question.id)
        .where(ExamSetQuestion.exam_set_id == set_id)
        .order_by(ExamSetQuestion.order_index.asc())
    )
    rows = session.execute(stmt).all()

    questions = []
    for question, _order in rows:
        questions.append({
            "q": question.question_text,
            "type": "MCQ",
            "opts": question.options,
            "topic": question.topic or "General",
            "ans": question.correct_option,
            "marks": 1,
        })

    return jsonify({
        "exam_set_id": str(set_id),
        "set_label": exam_set.set_label,
        "subject": exam.subject,
        "difficulty": "medium",
        "questions": questions,
    }), 200


__all__ = ["router"]
