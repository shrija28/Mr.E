"""Student exam-selection endpoint.

Implements task 7.5 / REQ-8.1, REQ-8.2, REQ-8.3 and the read side of the
contract documented in design.md §4.2 ("Student Exam-Selection
Visibility").

* Mounted under ``/api/student/exams`` from :mod:`smartkcet.student`.
* Student-only — guarded by
  :func:`smartkcet.middleware.rbac.require_student`.
* Subjects with **no published exam** are omitted from the response per
  REQ-8.2 / design.md §4.2.  When no subject has any published exam the
  response shape collapses to ``{"subjects": []}`` and the UI renders
  the "no exams currently available" empty state.
* Optional ``?subject=Biology`` query parameter scopes the response to
  one subject; mismatched subjects yield ``{"subjects": []}`` rather
  than a 400 (the spec lists no validation error for this case — the
  filter is purely additive).
"""

from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Depends, Query, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session
import uuid

from ..db.models import Exam, ExamSet, ExamSetQuestion, Question, Subject
from ..db.session import get_async_session as get_session
from ..middleware.rbac import require_student
from ..subscription.dependencies import get_access_control, require_exam_access

router = APIRouter()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _validation_error(message: str, field: Optional[str] = None) -> JSONResponse:
    """Return a 400 envelope identical in shape to the admin endpoints."""

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
# GET /api/student/exams  (REQ-8.1, REQ-8.2, REQ-8.3 / design.md §4.2)
# ---------------------------------------------------------------------------


@router.get("/exams")
def list_published_exams(
    request: Request,
    subject: Optional[str] = Query(default=None),
    session: Session = Depends(get_session),
    _student: dict = Depends(require_student),
    access_control = Depends(get_access_control),
) -> Any:
    """Return per-subject groupings of published exams visible to students.

    Response shape::

        {
          "subjects": [
            {
              "subject": "Biology",
              "available_exams": 2,
              "exams": [
                {"exam_id": "...", "created_at": "...", "set_count": 4},
                ...
              ]
            },
            ...
          ],
          "remaining_attempts": {
            "total_attempts": 2,
            "max_attempts": 5,
            "remaining_attempts": 3,
            "is_unlimited": false,
            "period_start": "2024-01-01T00:00:00",
            "period_end": "2024-01-08T00:00:00"
          }
        }

    Subjects without at least one published exam are omitted.  When the
    optional ``?subject=`` filter narrows the scope to a single subject
    that has no published exam, the response is ``{"subjects": []}``.
    
    **Institution Integration (REQ-7.3, 9.7):**
    Students linked to institutions see both platform-wide exams (institution_id IS NULL)
    and institution-specific exams (institution_id matches their institution).
    
    **Subscription Integration (REQ-1.5, 2.4):**
    Response includes remaining exam attempts for display on exam selection screen.
    """

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

    # Get student's institution_id and subtype from token payload
    student_institution_id = _student.get("institution_id")
    student_subtype = _student.get("student_subtype", "direct_subscriber")

    stmt = (
        select(Exam, func.count(ExamSet.id).label("set_count"))
        .outerjoin(ExamSet, ExamSet.exam_id == Exam.id)
        .where(Exam.is_published.is_(True))
        .group_by(Exam.id)
        .order_by(Exam.created_at.desc(), Exam.id.asc())
    )

    # ── Strict exam isolation ────────────────────────────────────────────────
    # Access matrix:
    #   direct_subscriber  → platform-wide exams only (institution_id IS NULL)
    #   institution_linked → their institution's exams only (institution_id == theirs)
    #                        NOT platform-wide, NOT other institutions
    if student_subtype == "institution_linked" and student_institution_id is not None:
        # Institution student: ONLY see exams belonging to their institution
        try:
            inst_uuid = uuid.UUID(student_institution_id)
        except ValueError:
            inst_uuid = student_institution_id
        stmt = stmt.where(Exam.institution_id == inst_uuid)
    else:
        # Personal student (direct_subscriber or no subtype): platform-wide only
        stmt = stmt.where(Exam.institution_id.is_(None))

    if selected is not None:
        stmt = stmt.where(Exam.subject == selected.value)

    rows = session.execute(stmt).all()

    # Group rows by subject.  ``buckets`` preserves insertion order so a
    # subject's first-seen ``created_at`` decides where it appears in
    # the response — combined with the SQL ``ORDER BY created_at DESC``
    # this mirrors the admin-list ordering.
    buckets: dict[str, list[dict[str, Any]]] = {}
    for exam, set_count in rows:
        created_at = exam.created_at

        # Fetch the actual exam sets for this exam so the UI can link directly
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

    # Get remaining attempts for display (REQ-1.5, 2.4)
    from ..middleware.rbac import current_user
    user = current_user(request, session)
    remaining_attempts_data = None
    if user:
        try:
            remaining_attempts_data = access_control.get_remaining_attempts(user.id)
        except Exception as exc:
            # If we can't get remaining attempts, log but don't fail the request
            import logging
            logger = logging.getLogger("smartkcet.student.exams")
            logger.warning("Failed to get remaining attempts for user %s: %s", user.id, exc)

    return {
        "subjects": subjects_payload,
        "remaining_attempts": remaining_attempts_data,
    }


# ---------------------------------------------------------------------------
# GET /api/student/exams/{exam_set_id}  (REQ-9.1 / task 14.3)
# ---------------------------------------------------------------------------


@router.get("/exams/{exam_set_id}")
def get_exam_set_questions(
    exam_set_id: str,
    session: Session = Depends(get_session),
    _student: dict = Depends(require_student),
    _exam_access: dict = Depends(require_exam_access),
) -> Any:
    """Return the questions for a specific exam set so the student can take the exam.

    Response shape::

        {
          "exam_set_id": "uuid",
          "set_label": "A",
          "subject": "Biology",
          "difficulty": "medium",
          "questions": [
            {"q": "...", "type": "MCQ", "opts": [...], "topic": "...", "marks": 1},
            ...
          ]
        }

    Questions are ordered by ``ExamSetQuestion.order_index`` so the
    student's answer map keys (``"0"`` ... ``"19"``) align with positions.
    """
    import uuid as _uuid

    try:
        set_id = _uuid.UUID(exam_set_id)
    except (ValueError, TypeError):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "validation_error", "message": "exam_set_id must be a valid UUID"},
        )

    exam_set = session.get(ExamSet, set_id)
    if exam_set is None:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"error": "not_found", "resource": "exam_set", "value": str(set_id)},
        )

    # Verify the parent exam is published
    exam = session.get(Exam, exam_set.exam_id)
    if exam is None or not exam.is_published:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"error": "not_found", "message": "Exam is not available"},
        )

    # ── Ownership check: enforce strict exam isolation ───────────────────────
    # Institution student → can only access their institution's exams
    # Personal student   → can only access platform-wide exams (institution_id IS NULL)
    student_subtype = _student.get("student_subtype", "direct_subscriber")
    student_institution_id = _student.get("institution_id")

    if student_subtype == "institution_linked":
        # Must belong to their institution
        if str(exam.institution_id) != str(student_institution_id):
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"error": "not_found", "message": "Exam is not available"},
            )
    else:
        # Personal student: must be platform-wide (institution_id IS NULL)
        if exam.institution_id is not None:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"error": "not_found", "message": "Exam is not available"},
            )

    # Load questions ordered by position
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

    return {
        "exam_set_id": str(set_id),
        "set_label": exam_set.set_label,
        "subject": exam.subject,
        "difficulty": "medium",
        "questions": questions,
    }


__all__ = ["router"]
