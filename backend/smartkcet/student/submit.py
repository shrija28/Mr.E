"""Student exam-submission and exam-status endpoints using Flask Blueprint."""

from __future__ import annotations

import logging
import uuid
from typing import Any, Optional

from flask import Blueprint, jsonify, request
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from .. import leaderboard
from ..db.models import (
    Exam,
    ExamSet,
    ExamSetQuestion,
    Question,
    Submission,
    User,
)
from ..db.session import get_db
from ..middleware.rbac import current_user, require_student
from ..submissions.scoring import score_submission

logger = logging.getLogger("smartkcet.student.submit")

router = Blueprint("student_submit", __name__, url_prefix="/api/student")
_MAX_IDEMPOTENCY_KEY_LEN = 64


def _validation_error(message: str, field: Optional[str] = None):
    body: dict[str, Any] = {"error": "validation_error", "message": message}
    if field is not None:
        body["field"] = field
    return jsonify(body), 400


def _not_found(resource: str, value: Any):
    return jsonify({"error": "not_found", "resource": resource, "value": str(value)}), 404


def _serialise_submission(sub: Submission) -> dict[str, Any]:
    submitted_at = sub.submitted_at
    return {
        "id": str(sub.id),
        "user_id": str(sub.user_id),
        "exam_set_id": str(sub.exam_set_id),
        "answers": sub.answers,
        "score_pct": float(sub.score_pct),
        "topic_breakdown": sub.topic_breakdown,
        "time_taken_sec": int(sub.time_taken_sec),
        "submitted_at": (
            submitted_at.isoformat() if submitted_at is not None else None
        ),
        "status": sub.status,
        "pass_flag": float(sub.score_pct) >= 50.0,
        "idempotency_key": sub.idempotency_key,
    }


def _load_exam_set_questions(
    session: Session, exam_set_id: uuid.UUID
) -> list[dict[str, Any]]:
    stmt = (
        select(Question, ExamSetQuestion.order_index)
        .join(ExamSetQuestion, ExamSetQuestion.question_id == Question.id)
        .where(ExamSetQuestion.exam_set_id == exam_set_id)
        .order_by(ExamSetQuestion.order_index.asc())
    )
    rows = session.execute(stmt).all()
    questions: list[dict[str, Any]] = []
    for question, _order in rows:
        questions.append(
            {
                "q": question.question_text,
                "opts": question.options,
                "ans": question.correct_option,
                "topic": question.topic or "General",
                "marks": 1,
            }
        )
    return questions


@router.route("/submit", methods=["POST"])
@require_student
def submit():
    session: Session = get_db()
    data = request.get_json(silent=True) or {}
    raw_exam_set_id = data.get("exam_set_id")
    answers = data.get("answers")
    time_taken_sec = data.get("time_taken_sec")
    raw_idempotency_key = data.get("idempotency_key")
    question_times = data.get("question_times")

    if not isinstance(raw_exam_set_id, str) or not raw_exam_set_id.strip():
        return _validation_error("exam_set_id is required", field="exam_set_id")
    try:
        exam_set_id = uuid.UUID(raw_exam_set_id)
    except (ValueError, TypeError):
        return _validation_error("exam_set_id must be a UUID", field="exam_set_id")

    if not isinstance(answers, dict):
        return _validation_error(
            "answers must be an object mapping question index to choice",
            field="answers",
        )

    if (
        not isinstance(time_taken_sec, int)
        or isinstance(time_taken_sec, bool)
        or time_taken_sec < 0
    ):
        return _validation_error(
            "time_taken_sec must be a non-negative integer",
            field="time_taken_sec",
        )

    if not isinstance(raw_idempotency_key, str) or not raw_idempotency_key.strip():
        return _validation_error(
            "idempotency_key is required and must be a non-empty string",
            field="idempotency_key",
        )

    idempotency_key = raw_idempotency_key.strip()
    if len(idempotency_key) > _MAX_IDEMPOTENCY_KEY_LEN:
        return _validation_error(
            f"idempotency_key must be {_MAX_IDEMPOTENCY_KEY_LEN} characters or fewer",
            field="idempotency_key",
        )

    user = current_user(request, session)
    if user is None or user.role != "student":
        return jsonify({"error": "auth_required", "message": "Authenticated student account not found."}), 401

    existing = session.execute(
        select(Submission).where(
            Submission.user_id == user.id,
            Submission.idempotency_key == idempotency_key,
        )
    ).scalar_one_or_none()
    if existing is not None:
        return jsonify({
            "submission_id": str(existing.id),
            "submission": _serialise_submission(existing),
            "idempotent_replay": True,
        }), 200

    exam_set = session.get(ExamSet, exam_set_id)
    if exam_set is None:
        return _not_found("exam_set", exam_set_id)

    questions = _load_exam_set_questions(session, exam_set_id)
    if not questions:
        return jsonify({
            "error": "exam_set_empty",
            "message": "exam set has no questions",
            "exam_set_id": str(exam_set_id),
        }), 422

    score = score_submission(questions, answers)
    answers_data = dict(answers) if answers else {}
    if question_times:
        answers_data["__question_times__"] = question_times

    submission = Submission(
        user_id=user.id,
        exam_set_id=exam_set_id,
        answers=answers_data,
        score_pct=float(score["percentage"]),
        topic_breakdown=score["topic_breakdown"],
        time_taken_sec=int(time_taken_sec),
        status="completed",
        idempotency_key=idempotency_key,
    )
    session.add(submission)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        replay = session.execute(
            select(Submission).where(
                Submission.user_id == user.id,
                Submission.idempotency_key == idempotency_key,
            )
        ).scalar_one_or_none()
        if replay is not None:
            return jsonify({
                "submission_id": str(replay.id),
                "submission": _serialise_submission(replay),
                "idempotent_replay": True,
            }), 200
        return jsonify({"error": "persistence_failed", "message": "failed to persist submission"}), 500
    except SQLAlchemyError as exc:
        session.rollback()
        logger.warning("POST /api/student/submit failed: %s", exc)
        return jsonify({"error": "persistence_failed", "message": f"failed to persist submission: {exc}"}), 500

    try:
        leaderboard.recompute_async(user.id)
    except Exception as exc:
        logger.warning("leaderboard recompute_async raised: %s", exc)

    try:
        from ..subscription.usage import UsageTracker
        usage_tracker = UsageTracker(session)
        exam = session.get(Exam, exam_set.exam_id) if exam_set else None
        usage_tracker.record_attempt(
            user_id=user.id,
            submission_id=submission.id,
            subject=exam.subject if exam is not None else "Unknown"
        )
    except Exception as exc:
        logger.warning("usage tracking record_attempt raised: %s", exc)

    score_envelope = {k: v for k, v in score.items() if k != "topic_breakdown"}
    response_body: dict[str, Any] = {
        "submission_id": str(submission.id),
        "submission": _serialise_submission(submission),
        "idempotent_replay": False,
        "result": score_envelope,
    }
    return jsonify(response_body), 200


@router.route("/exams/<exam_set_id>/status", methods=["GET"])
@require_student
def exam_set_status(exam_set_id: str):
    session: Session = get_db()
    user = current_user(request, session)
    if user is None or user.role != "student":
        return jsonify({"error": "auth_required", "message": "Authenticated student account not found."}), 401

    try:
        set_id = uuid.UUID(exam_set_id)
    except (ValueError, TypeError):
        return jsonify({"error": "validation_error", "message": "exam_set_id must be a UUID"}), 400

    exam_set = session.get(ExamSet, set_id)
    if exam_set is None:
        return _not_found("exam_set", exam_set_id)

    stmt = (
        select(Submission)
        .where(
            Submission.user_id == user.id,
            Submission.exam_set_id == set_id,
            Submission.status == "completed",
        )
        .order_by(Submission.submitted_at.desc())
        .limit(1)
    )
    submission = session.execute(stmt).scalar_one_or_none()
    if submission is None:
        return jsonify({"completed": False}), 200
    return jsonify({
        "completed": True,
        "submission": _serialise_submission(submission),
    }), 200


__all__ = ["router"]
