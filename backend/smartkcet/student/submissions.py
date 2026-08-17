"""Student submission history endpoints.

Implements task 8.5 / REQ-4.5, REQ-10.1, REQ-10.4, REQ-14.3.

Access Control (Tasks 5.3, 5.4):
- Free Trial: Basic analytics only (total score, pass/fail)
- Pro: Full analytics (topic breakdowns, AI recommendations, trends)

Endpoints
---------

``GET /api/student/submissions``
    Return the authenticated student's submissions.  Default sort is
    ``submitted_at DESC`` (REQ-10.4).  Optional filters: ``subject``
    (joins through exam_sets → exams), ``limit`` (default 50, capped at
    200), ``offset`` (default 0).  Response items are summary records —
    detailed answer data lives on the ``GET .../{id}`` endpoint.

``GET /api/student/submissions/{submission_id}``
    Return the full submission record for a single attempt, including
    the answers, scoring envelope, and per-question correctness review.
    Enforces ownership: a 403 is returned when the submission does not
    belong to the authenticated student.  The 403 body is intentionally
    bare so no information about the submission leaks (REQ-4.5).
"""

from __future__ import annotations

import uuid
from typing import Any, Optional

from fastapi import APIRouter, Depends, Path, Query, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from ..db.models import Exam, ExamSet, ExamSetQuestion, Question, Submission, Subject
from ..db.session import get_async_session as get_session
from ..middleware.rbac import current_user, require_student
from ..subscription.dependencies import get_access_control

router = APIRouter()


_DEFAULT_LIMIT = 50
_MAX_LIMIT = 200


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _validation_error(message: str, field: Optional[str] = None) -> JSONResponse:
    body: dict[str, Any] = {"error": "validation_error", "message": message}
    if field is not None:
        body["field"] = field
    return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=body)


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


def _summary_row(
    submission: Submission, exam_set: ExamSet, exam: Exam
) -> dict[str, Any]:
    """Map a join row to the dashboard summary shape."""

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


# ---------------------------------------------------------------------------
# GET /api/student/submissions  (REQ-10.1, REQ-10.4)
# ---------------------------------------------------------------------------


@router.get("/submissions")
def list_submissions(
    request: Request,
    subject: Optional[str] = Query(default=None),
    limit: int = Query(default=_DEFAULT_LIMIT, ge=1),
    offset: int = Query(default=0, ge=0),
    session: Session = Depends(get_session),
    _student: dict = Depends(require_student),
    access_control = Depends(get_access_control),
) -> Any:
    """List the authenticated student's submissions, newest first.
    
    **Subscription Integration (REQ-2.4):**
    Response includes subscription status and remaining attempts for dashboard display.
    """

    user = current_user(request, session)
    if user is None or user.role != "student":
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "error": "auth_required",
                "message": "Authenticated student account not found.",
            },
        )

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

    capped_limit = min(int(limit), _MAX_LIMIT)

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

    # Get subscription status and remaining attempts for dashboard display (REQ-2.4)
    subscription_status = None
    remaining_attempts_data = None
    try:
        # Get effective subscription status
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
        
        # Get remaining attempts
        remaining_attempts_data = access_control.get_remaining_attempts(user.id)
    except Exception as exc:
        # If we can't get subscription info, log but don't fail the request
        import logging
        logger = logging.getLogger("smartkcet.student.submissions")
        logger.warning("Failed to get subscription info for user %s: %s", user.id, exc)

    return {
        "submissions": summaries,
        "limit": capped_limit,
        "offset": int(offset),
        "subject": selected_subject.value if selected_subject is not None else None,
        "subscription_status": subscription_status,
        "remaining_attempts": remaining_attempts_data,
    }


# ---------------------------------------------------------------------------
# GET /api/student/submissions/{submission_id}  (REQ-4.5, REQ-14.3)
# ---------------------------------------------------------------------------


@router.get("/submissions/{submission_id}")
def get_submission(
    request: Request,
    submission_id: uuid.UUID = Path(...),
    session: Session = Depends(get_session),
    _student: dict = Depends(require_student),
    access_control = Depends(get_access_control),
) -> Any:
    """Return the full submission record (with question review).

    A 403 is returned when the submission belongs to a different
    student, with no body data leaked (REQ-4.5).
    """

    user = current_user(request, session)
    if user is None or user.role != "student":
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "error": "auth_required",
                "message": "Authenticated student account not found.",
            },
        )

    submission = session.execute(
        select(Submission)
        .where(Submission.id == submission_id)
        .options(joinedload(Submission.exam_set).joinedload(ExamSet.exam))
    ).scalar_one_or_none()

    if submission is None:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "error": "not_found",
                "resource": "submission",
                "value": str(submission_id),
            },
        )

    if submission.user_id != user.id:
        # REQ-4.5: forbidden, with no submission data in the body.
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"error": "forbidden", "message": "Access denied."},
        )

    exam_set = submission.exam_set
    exam = exam_set.exam if exam_set is not None else None

    # Pull the question rows so the detail drawer can render the answer
    # review (correct option, topic, etc.) without a second request.
    question_rows = session.execute(
        select(Question, ExamSetQuestion.order_index)
        .join(ExamSetQuestion, ExamSetQuestion.question_id == Question.id)
        .where(ExamSetQuestion.exam_set_id == submission.exam_set_id)
        .order_by(ExamSetQuestion.order_index.asc())
    ).all()
    questions: list[dict[str, Any]] = []
    answers = submission.answers if isinstance(submission.answers, dict) else {}
    from ..submissions.scoring import _is_correct_answer
    for question, order_index in question_rows:
        index_str = str(order_index)
        given = answers.get(index_str)
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
                "correctAns": question.correct_option,
                "topic": question.topic or "General",
                "given": given,
                "status": given_status,
                "exp": question.explanation or "",
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
        "answers": submission.answers,
        "questions": questions,
    }
    
    # Filter analytics data based on subscription tier
    filtered_data = access_control.filter_analytics_data(analytics_data, user.id)
    
    return filtered_data


__all__ = ["router"]
