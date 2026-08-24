"""Student submission history endpoints using Flask Blueprint."""

from __future__ import annotations

import logging
import uuid
from typing import Any, Optional

from flask import Blueprint, jsonify, request
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from ..db.models import Exam, ExamSet, ExamSetQuestion, Question, Submission, Subject
from ..db.session import get_db
from ..middleware.rbac import current_user, require_student
from ..subscription.dependencies import get_access_control

logger = logging.getLogger("smartkcet.student.submissions")

router = Blueprint("student_submissions", __name__, url_prefix="/api/student")

_DEFAULT_LIMIT = 50
_MAX_LIMIT = 200


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


def _summary_row(submission: Submission, exam_set: ExamSet, exam: Exam) -> dict[str, Any]:
    submitted_at = submission.submitted_at
    return {
        "id": str(submission.id),
        "exam_set_id": str(submission.exam_set_id),
        "exam_id": str(exam.id),
        "set_label": exam_set.set_label,
        "subject": exam.subject,
        "score_pct": float(submission.score_pct),
        "time_taken_sec": int(submission.time_taken_sec),
        "submitted_at": (
            submitted_at.isoformat() if submitted_at is not None else None
        ),
        "status": submission.status,
        "pass_flag": float(submission.score_pct) >= 50.0,
    }


@router.route("/submissions", methods=["GET"])
@require_student
def list_submissions():
    session: Session = get_db()
    user = current_user(request, session)
    if user is None or user.role != "student":
        return jsonify({"error": "auth_required", "message": "Authenticated student account not found."}), 401

    subject = request.args.get("subject")
    raw_limit = request.args.get("limit", _DEFAULT_LIMIT)
    raw_offset = request.args.get("offset", 0)

    try:
        limit = int(raw_limit)
        offset = int(raw_offset)
    except (ValueError, TypeError):
        limit = _DEFAULT_LIMIT
        offset = 0

    selected_subject: Optional[Subject] = None
    if subject is not None:
        normalised = _normalise_subject(subject)
        if normalised is None:
            allowed = [s.value for s in Subject]
            return _validation_error(f"subject must be one of {allowed}", field="subject")
        selected_subject = normalised

    capped_limit = min(max(1, limit), _MAX_LIMIT)

    stmt = (
        select(Submission, ExamSet, Exam)
        .join(ExamSet, ExamSet.id == Submission.exam_set_id)
        .join(Exam, Exam.id == ExamSet.exam_id)
        .where(Submission.user_id == user.id)
        .order_by(Submission.submitted_at.desc(), Submission.id.asc())
        .offset(offset)
        .limit(capped_limit)
    )
    if selected_subject is not None:
        stmt = stmt.where(Exam.subject == selected_subject.value)

    rows = session.execute(stmt).all()
    summaries = [_summary_row(sub, exam_set, exam) for sub, exam_set, exam in rows]

    subscription_status = None
    remaining_attempts_data = None
    try:
        from ..subscription.service import SubscriptionService
        subscription_service = SubscriptionService(session)
        effective_status = subscription_service.get_effective_status(user.id)
        
        subscription_status = {
            "has_subscription": effective_status.has_subscription,
            "status": effective_status.status,
            "plan_type": effective_status.plan_type,
            "billing_period": effective_status.billing_period,
            "is_trial": effective_status.is_trial,
            "is_active": effective_status.is_active,
            "trial_attempts_remaining": effective_status.trial_attempts_remaining,
            "next_renewal_date": effective_status.next_renewal_date.isoformat() if effective_status.next_renewal_date else None,
            "grace_period_end": effective_status.grace_period_end.isoformat() if effective_status.grace_period_end else None,
            "institution_id": str(effective_status.institution_id) if effective_status.institution_id else None,
            "institution_name": effective_status.institution_name,
        }
        
        access_control = get_access_control(session)
        remaining_attempts_obj = access_control.get_remaining_attempts(user.id)
        if hasattr(remaining_attempts_obj, "model_dump"):
            remaining_attempts_data = remaining_attempts_obj.model_dump(mode="json")
        else:
            remaining_attempts_data = remaining_attempts_obj
    except Exception as exc:
        logger.warning("Failed to get subscription info for user %s: %s", user.id, exc)

    return jsonify({
        "submissions": summaries,
        "limit": capped_limit,
        "offset": offset,
        "subject": selected_subject.value if selected_subject is not None else None,
        "subscription_status": subscription_status,
        "remaining_attempts": remaining_attempts_data,
    }), 200


@router.route("/submissions/<submission_id>", methods=["GET"])
@require_student
def get_submission(submission_id: str):
    session: Session = get_db()
    user = current_user(request, session)
    if user is None or user.role != "student":
        return jsonify({"error": "auth_required", "message": "Authenticated student account not found."}), 401

    try:
        sub_uuid = uuid.UUID(submission_id)
    except (ValueError, TypeError):
        return jsonify({"error": "validation_error", "message": "submission_id must be a UUID"}), 400

    submission = session.execute(
        select(Submission)
        .where(Submission.id == sub_uuid)
        .options(joinedload(Submission.exam_set).joinedload(ExamSet.exam))
    ).scalar_one_or_none()

    if submission is None:
        return jsonify({
            "error": "not_found",
            "resource": "submission",
            "value": str(submission_id),
        }), 404

    if submission.user_id != user.id:
        return jsonify({"error": "forbidden", "message": "Access denied."}), 403

    exam_set = submission.exam_set
    exam = exam_set.exam if exam_set is not None else None

    question_rows = session.execute(
        select(Question, ExamSetQuestion.order_index)
        .join(ExamSetQuestion, ExamSetQuestion.question_id == Question.id)
        .where(ExamSetQuestion.exam_set_id == submission.exam_set_id)
        .order_by(ExamSetQuestion.order_index.asc())
    ).all()

    questions: list[dict[str, Any]] = []
    answers = submission.answers if isinstance(submission.answers, dict) else {}
    from ..db.subscription_models import Subscription
    from ..submissions.scoring import _is_correct_answer

    sub = session.query(Subscription).options(joinedload(Subscription.plan)).filter(
        Subscription.user_id == user.id,
        Subscription.status.in_(["active", "trial", "grace_period"])
    ).first()
    is_institution = (getattr(user, "student_subtype", "") == "institution_linked") or (getattr(user, "institution_id", None) is not None)
    is_premium = is_institution or (sub is not None and sub.plan is not None and sub.plan.name.lower() != "free")

    q_times = answers.get("__question_times__", {}) if isinstance(answers, dict) else {}

    for question, order_index in question_rows:
        index_str = str(order_index)
        given = answers.get(index_str)
        q_time = q_times.get(index_str) if isinstance(q_times, dict) else None
        if q_time is None and isinstance(q_times, dict):
            q_time = q_times.get(int(order_index))

        if given is None or str(given).strip() == "":
            given_status = "unanswered"
        elif _is_correct_answer(given, question.correct_option, question.options):
            given_status = "correct"
        else:
            given_status = "wrong"
        questions.append(
            {
                "order_index": int(order_index),
                "id": str(question.id),
                "q": question.question_text,
                "opts": question.options,
                "correctAns": question.correct_option if is_premium else None,
                "topic": question.topic or "General",
                "given": given,
                "status": given_status,
                "exp": (question.explanation or "") if is_premium else None,
                "time_taken_sec": q_time,
            }
        )

    submitted_at = submission.submitted_at
    analytics_data = {
        "id": str(submission.id),
        "exam_set_id": str(submission.exam_set_id),
        "exam_id": str(exam.id) if exam is not None else None,
        "set_label": exam_set.set_label if exam_set is not None else None,
        "subject": exam.subject if exam is not None else None,
        "score_pct": float(submission.score_pct),
        "topic_breakdown": submission.topic_breakdown,
        "time_taken_sec": int(submission.time_taken_sec),
        "submitted_at": (
            submitted_at.isoformat() if submitted_at is not None else None
        ),
        "status": submission.status,
        "pass_flag": float(submission.score_pct) >= 50.0,
        "is_premium_subscriber": is_premium,
        "answers": submission.answers,
        "questions": questions,
    }
    
    access_control = get_access_control(session)
    filtered_data = access_control.filter_analytics_data(analytics_data, user.id)
    
    return jsonify(filtered_data), 200


__all__ = ["router"]
