"""Student exam-submission and exam-status endpoints.

Implements task 8.1, 8.3 / REQ-9.3, REQ-9.7 and the submission contract
from design.md §4A.1, §4A.3, §5.1.

Endpoints
---------

``POST /api/student/submit``
    The student-side replacement for the legacy ``POST /analyze``.  The
    handler:

    1. Validates the JSON body shape.
    2. Looks up the exam set + its 20 questions.
    3. Checks the idempotency token against existing submissions by the
       authenticated student; returns the existing record on a hit.
    4. Scores via :func:`smartkcet.submissions.scoring.score_submission`.
    5. Persists a ``Submission`` row inside a single transaction.  The
       student id comes from the Session_Token — the request body's
       student id (if any) is **never** trusted.
    6. After the transaction commits, dispatches
       :func:`smartkcet.leaderboard.recompute_async` exactly once
       (REQ-11.6 / design.md §6.3).  The leaderboard service is a stub
       until task 10.

``GET /api/student/exams/{exam_set_id}/status``
    Returns ``{completed: True, submission: {...}}`` when the
    authenticated student already has a completed submission for the
    set, else ``{completed: False}``.  The frontend (task 14.3) calls
    this before serving the exam UI to render the previous-result view
    instead of a fresh attempt.
"""

from __future__ import annotations
import os

import logging
import uuid
from typing import Any, Optional

import os
from flask import Blueprint, request, g, make_response, jsonify, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel
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
from ..db.session import get_async_session as get_session
from ..middleware.rbac import current_user, require_student
from ..submissions.scoring import score_submission
from ..rag.ai_analyzer import analyze_student_submission

logger = logging.getLogger("smartkcet.student.submit")

router = Blueprint("student_submit", __name__)


# Idempotency tokens are stored in a VARCHAR(64) column — see the
# migration in ``backend/migrations/versions/0002_add_submission_idempotency_key.py``.
_MAX_IDEMPOTENCY_KEY_LEN = 64


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _validation_error(message: str, field: Optional[str] = None)-> Any:
    """Return a 400 envelope identical in shape to the admin endpoints."""

    body: dict[str, Any] = {"error": "validation_error", "message": message}
    if field is not None:
        body["field"] = field
    return make_response(jsonify(body), 400)


def _not_found(resource: str, value: Any)-> JSONResponse:
    return make_response(jsonify({"error": "not_found", "resource": resource, "value": str(value)}), 404)


def _serialise_submission(sub: Submission)-> dict[str, Any]:
    """Map a :class:`Submission` ORM row to the JSON shape the dashboard expects."""

    submitted_at = sub.submitted_at
    answers_dict = sub.answers if isinstance(sub.answers, dict) else {}
    ai_data = answers_dict.get("__ai_analysis__") if isinstance(answers_dict, dict) else None
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
        "ai_analysis": ai_data,
        "detailed_reviews": ai_data.get("detailed_reviews", []) if isinstance(ai_data, dict) else [],
    }



def _load_exam_set_questions(session: Session, exam_set_id: uuid.UUID)-> list[dict[str, Any]]:
    """Return the question rows for ``exam_set_id`` as scoring-helper dicts.

    Ordered by ``ExamSetQuestion.order_index`` so the keys in the
    student's answer map (``"0"`` ... ``"19"``) line up with the
    question positions.
    """

    stmt = (
        select(Question, ExamSetQuestion.order_index)
        .join(ExamSetQuestion, ExamSetQuestion.question_id == Question.id)
        .where(ExamSetQuestion.exam_set_id == exam_set_id)
        .order_by(ExamSetQuestion.order_index.asc())
    )
    rows = session.execute(stmt).all()
    from ..rag.mcq_extractor import infer_question_subtype

    questions: list[dict[str, Any]] = []
    for question, _order in rows:
        st = infer_question_subtype(question.question_text, question.options or [], question.subject)
        questions.append(
            {
                "q": question.question_text,
                "opts": question.options,
                "ans": question.correct_option,
                "topic": question.topic or "General",
                "exp": question.explanation or "",
                "subtype": st,
                "marks": 1,
            }
        )
    return questions



# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------


class SubmitRequest(BaseModel):
    exam_set_id: Optional[str] = None
    answers: Optional[dict[str, Any]] = None
    time_taken_sec: Optional[int] = None
    idempotency_key: Optional[str] = None
    question_times: Optional[dict[str, Any]] = None


# ---------------------------------------------------------------------------
# POST /api/student/submit  (REQ-9.3 / design.md §4A.3, §5.1)
# ---------------------------------------------------------------------------


@router.route("/submit", methods=["POST"])
def submit()-> Any:    
    from flask import request
    payload = SubmitRequest(**(request.get_json() or {}))
    _student = require_student()
    from flask import g
    db = getattr(g, "db", None)
    session = db
    """Score and persist one student submission.

    The flow follows design.md §5.1:

    1. Validate input shape (no DB call yet).
    2. Resolve the authenticated student via the cookie token — the
       request body's user id is **never** trusted.
    3. Idempotency lookup keyed by ``(user_id, idempotency_key)`` —
       returns the existing submission record on a hit.
    4. Load exam-set questions, score, persist, commit.
    5. After commit, dispatch the leaderboard recompute (stubbed).
    """

    # ---- Step 1: shape validation -------------------------------------
    if not isinstance(payload.exam_set_id, str) or not payload.exam_set_id.strip():
        return _validation_error("exam_set_id is required", field="exam_set_id")
    try:
        exam_set_id = uuid.UUID(payload.exam_set_id)
    except (ValueError, TypeError):
        return _validation_error("exam_set_id must be a UUID", field="exam_set_id")

    if not isinstance(payload.answers, dict):
        return _validation_error(
            "answers must be an object mapping question index to choice",
            field="answers",
        )

    if (
        not isinstance(payload.time_taken_sec, int)
        or isinstance(payload.time_taken_sec, bool)
        or payload.time_taken_sec < 0
    ):
        return _validation_error(
            "time_taken_sec must be a non-negative integer",
            field="time_taken_sec",
        )

    if isinstance(payload.idempotency_key, str) and payload.idempotency_key.strip():
        idempotency_key = payload.idempotency_key.strip()
        if len(idempotency_key) > _MAX_IDEMPOTENCY_KEY_LEN:
            return _validation_error(
                f"idempotency_key must be {_MAX_IDEMPOTENCY_KEY_LEN} characters or fewer",
                field="idempotency_key",
            )
    else:
        idempotency_key = uuid.uuid4().hex

    # ---- Step 2: resolve authenticated student -----------------------
    user = current_user(request, session)
    if user is None or user.role != "student":
        # ``require_student`` already enforced the role check, but a
        # token whose ``sub`` no longer matches a row in ``users`` would
        # slip through — surface that as 401 here rather than handing
        # the submission to a phantom user.
        return make_response(jsonify({
                "error": "auth_required",
                "message": "Authenticated student account not found.",
            }), 401)

    # ---- Step 3: idempotency lookup ----------------------------------
    existing = session.execute(
        select(Submission).where(
            Submission.user_id == user.id,
            Submission.idempotency_key == idempotency_key,
        )
    ).scalar_one_or_none()
    if existing is not None:
        rep_answers = existing.answers or {}
        replay_body = {
            "submission_id": str(existing.id),
            "submission": _serialise_submission(existing),
            "idempotent_replay": True,
            "percentage": float(existing.score_pct or 0.0),
            "time_taken_sec": int(existing.time_taken_sec or 0),
        }
        if isinstance(rep_answers, dict) and "__ai_analysis__" in rep_answers:
            ai_data = rep_answers["__ai_analysis__"]
            replay_body["ai_analysis"] = ai_data
            replay_body["detailed_reviews"] = ai_data.get("detailed_reviews", []) if isinstance(ai_data, dict) else []
            summ = ai_data.get("summary", {}) if isinstance(ai_data, dict) else {}
            replay_body["score"] = summ.get("score", summ.get("correct_count", 0))
            replay_body["total_marks"] = summ.get("total", 60)
            replay_body["percentage"] = summ.get("percentage", 0.0)
            replay_body["correct_count"] = summ.get("correct_count", summ.get("score", 0))
            replay_body["incorrect_count"] = summ.get("incorrect_count", 0)
            replay_body["unanswered_count"] = summ.get("unanswered_count", 0)
        return make_response(jsonify(replay_body), 200)

    # ---- Step 4: load questions + score + persist --------------------
    exam_set = session.get(ExamSet, exam_set_id)
    if exam_set is None:
        return _not_found("exam_set", exam_set_id)

    questions = _load_exam_set_questions(session, exam_set_id)
    if not questions:
        return make_response(jsonify({
                "error": "exam_set_empty",
                "message": "exam set has no questions",
                "exam_set_id": str(exam_set_id),
            }), 422)

    exam = session.get(Exam, exam_set.exam_id) if exam_set else None
    subject_name = exam.subject if exam is not None else "General"

    score = score_submission(questions, payload.answers)
    ai_analysis = analyze_student_submission(
        questions=questions,
        answers=payload.answers or {},
        score_data=score,
        time_taken_sec=int(payload.time_taken_sec),
        subject=subject_name,
    )

    answers_data = dict(payload.answers) if payload.answers else {}
    if payload.question_times:
        answers_data["__question_times__"] = payload.question_times
    answers_data["__ai_analysis__"] = ai_analysis

    submission = Submission(
        user_id=user.id,
        exam_set_id=exam_set_id,
        answers=answers_data,
        score_pct=float(score["percentage"]),
        topic_breakdown=score["topic_breakdown"],
        time_taken_sec=int(payload.time_taken_sec),
        status="completed",
        idempotency_key=idempotency_key,
    )
    session.add(submission)
    try:
        session.commit()
    except IntegrityError:
        # A concurrent retry hit the unique constraint after our
        # idempotency lookup.  Re-read and return the persisted row so
        # the caller still gets a 200 with the final state.
        session.rollback()
        replay = session.execute(
            select(Submission).where(
                Submission.user_id == user.id,
                Submission.idempotency_key == idempotency_key,
            )
        ).scalar_one_or_none()
        if replay is not None:
            return {
                "submission_id": str(replay.id),
                "submission": _serialise_submission(replay),
                "idempotent_replay": True,
            }
        return make_response(jsonify({
                "error": "persistence_failed",
                "message": "failed to persist submission",
            }), 500)
    except SQLAlchemyError as exc:
        session.rollback()
        logger.warning("POST /api/student/submit failed: %s", exc)
        return make_response(jsonify({
                "error": "persistence_failed",
                "message": f"failed to persist submission: {exc}",
            }), 500)

    # ---- Step 5: leaderboard recompute (REQ-11.6) --------------------
    # Fired only after the transaction has committed.  The current
    # implementation in :mod:`smartkcet.leaderboard` is a no-op stub
    # that logs the trigger; task 10 fills in the body.
    try:
        leaderboard.recompute_async(user.id)
    except Exception as exc:  # pragma: no cover - defensive belt
        # The leaderboard recompute is fire-and-forget and must NEVER
        # fail the submission response.  Log and continue.
        logger.warning("leaderboard recompute_async raised: %s", exc)

    # ---- Step 6: record usage for subscription tracking (REQ-5.1, 5.7) ----
    # Record the exam attempt for usage tracking and quota enforcement
    try:
        from ..subscription.usage import UsageTracker
        usage_tracker = UsageTracker(session)
        
        # Get the exam to determine subject
        exam = session.get(Exam, exam_set.exam_id) if exam_set else None
        
        usage_tracker.record_attempt(
            user_id=user.id,
            submission_id=submission.id,
            subject=exam.subject if exam is not None else "Unknown"
        )
    except Exception as exc:  # pragma: no cover - defensive belt
        # Usage tracking is important but should not fail the submission
        logger.warning("usage tracking record_attempt raised: %s", exc)

    summ = ai_analysis.get("summary", {}) if isinstance(ai_analysis, dict) else {}
    earned = int(summ.get("score", score.get("earned", 0)))
    total = int(summ.get("total", score.get("total", len(questions))))
    pct = float(summ.get("percentage", score.get("percentage", 0.0)))
    correct = int(summ.get("correct_count", earned))
    incorrect = int(summ.get("incorrect_count", max(0, total - correct)))
    unans = int(summ.get("unanswered_count", max(0, total - correct - incorrect)))

    response_body: dict[str, Any] = {
        "submission_id": str(submission.id),
        "submission": _serialise_submission(submission),
        "idempotent_replay": False,
        "ai_analysis": ai_analysis,
        "detailed_reviews": ai_analysis.get("detailed_reviews", []),
        "score": earned,
        "total_marks": total,
        "percentage": pct,
        "correct_count": correct,
        "incorrect_count": incorrect,
        "unanswered_count": unans,
        "time_taken_sec": int(payload.time_taken_sec),
    }
    score_envelope = {k: v for k, v in score.items() if k != "topic_breakdown"}
    response_body["result"] = score_envelope
    return make_response(jsonify(response_body), 200)


# ---------------------------------------------------------------------------
# GET /api/student/exams/{exam_set_id}/status  (REQ-9.7 / design.md §4A.1)
# ---------------------------------------------------------------------------


@router.route("/exams/<exam_set_id>/status", methods=["GET"])
def exam_set_status(exam_set_id: uuid.UUID)-> Any:    
    _student = require_student()
    from flask import g
    db = getattr(g, "db", None)
    session = db
    """Return the student's prior completed submission for ``exam_set_id``.

    Response shape::

        {"completed": true,  "submission": {...}}      # found
        {"completed": false}                            # none

    The query mirrors the SQL in design.md §4A.1: filter to the
    authenticated student, scope to ``status='completed'``, take the
    most recent row.
    """

    user = current_user(request, session)
    if user is None or user.role != "student":
        return make_response(jsonify({
                "error": "auth_required",
                "message": "Authenticated student account not found.",
            }), 401)

    # Confirm the exam_set actually exists so a 404 here is meaningful
    # (an unknown id should not collapse to "not completed").
    exam_set = session.get(ExamSet, exam_set_id)
    if exam_set is None:
        return _not_found("exam_set", exam_set_id)

    stmt = (
        select(Submission)
        .where(
            Submission.user_id == user.id,
            Submission.exam_set_id == exam_set_id,
            Submission.status == "completed",
        )
        .order_by(Submission.submitted_at.desc())
        .limit(1)
    )
    submission = session.execute(stmt).scalar_one_or_none()
    if submission is None:
        return {"completed": False}
    return {
        "completed": True,
        "submission": _serialise_submission(submission),
    }


__all__ = ["router"]
