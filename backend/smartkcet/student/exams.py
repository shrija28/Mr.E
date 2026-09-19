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
import os

from typing import Any, Optional

import os
from flask import Blueprint, request, g, make_response, jsonify, Response
from fastapi.responses import JSONResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session
import uuid

from ..db.models import Exam, ExamSet, ExamSetQuestion, Question, Subject
from ..db.session import get_async_session as get_session
from ..middleware.rbac import require_student
from ..subscription.dependencies import get_access_control, require_exam_access

router = Blueprint("student_exams", __name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _validation_error(message: str, field: Optional[str] = None)-> JSONResponse:
    """Return a 400 envelope identical in shape to the admin endpoints."""

    body: dict[str, Any] = {"error": "validation_error", "message": message}
    if field is not None:
        body["field"] = field
    return JSONResponse(status_code=400, content=body)


def _normalise_subject(value: Optional[str])-> Optional[Subject]:
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


@router.route("/exams", methods=["GET"])
def list_published_exams()-> Any:    
    _student = require_student()
    from flask import g
    db = getattr(g, "db", None)
    session = db
    from flask import g
    access_control = getattr(g, "access_control", None)
    from flask import request
    subject = request.args.get("subject", None)
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
    #   institution_linked → their institution's exams AND platform-wide exams (created by admin)
    if student_subtype == "institution_linked" and student_institution_id is not None:
        # Institution student: see their institution's exams AND platform-wide admin exams
        try:
            inst_uuid = uuid.UUID(student_institution_id)
        except ValueError:
            inst_uuid = student_institution_id
        from sqlalchemy import or_
        stmt = stmt.where(or_(Exam.institution_id == inst_uuid, Exam.institution_id.is_(None)))
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

        # Deterministically assign set based on student ID (e.g. KCET0001 -> Set A, KCET0002 -> Set B, etc.)
        student_id_str = ""
        if user:
            student_id_str = user.kcet_student_id or str(user.id)
        else:
            student_id_str = _student.get("kcet_student_id") or _student.get("sub") or ""

        import re as _re
        digits = _re.findall(r'\d+', student_id_str)
        assigned_idx = 0
        if sets_payload:
            if digits:
                try:
                    val = int(digits[-1])
                    assigned_idx = (val - 1) % len(sets_payload)
                except (ValueError, IndexError):
                    assigned_idx = 0
            else:
                num_hash = 0
                for char in str(student_id_str):
                    num_hash = (num_hash * 31 + ord(char)) & 0xFFFFFFFF
                assigned_idx = num_hash % len(sets_payload)

        assigned_set = sets_payload[assigned_idx] if sets_payload else {}

        bucket = buckets.setdefault(exam.subject, [])
        bucket.append(
            {
                "exam_id": str(exam.id),
                "exam_name": exam.exam_name,
                "created_at": (
                    created_at.isoformat() if created_at is not None else None
                ),
                "set_count": len(sets_payload) or int(set_count or 0),
                "question_count": questions_per_set,
                "duration_minutes": exam.duration_minutes or 60,
                "total_marks": exam.total_marks or (questions_per_set * 1 if questions_per_set else 60),
                "scheduled_start": exam.scheduled_start.isoformat() if exam.scheduled_start else None,
                "scheduled_end": exam.scheduled_end.isoformat() if exam.scheduled_end else None,
                "institution_id": str(exam.institution_id) if exam.institution_id else None,
                "assigned_set_id": assigned_set.get("exam_set_id"),
                "assigned_set_label": assigned_set.get("set_label"),
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
    from ..subscription.access_control import SubscriptionAccessControl
    user = current_user(request, session)
    remaining_attempts_data = None
    if user:
        try:
            ac = access_control or SubscriptionAccessControl(session)
            remaining_attempts_data = ac.get_remaining_attempts(user.id)
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


@router.route("/exams/<exam_set_id>", methods=["GET"])
def get_exam_set_questions(exam_set_id: str)-> Any:    
    _student = require_student()
    from flask import g
    db = getattr(g, "db", None)
    session = db
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
        return make_response(jsonify({"error": "validation_error", "message": "exam_set_id must be a valid UUID"}), 400)

    exam_set = session.get(ExamSet, set_id)
    if exam_set is None:
        return make_response(jsonify({"error": "not_found", "resource": "exam_set", "value": str(set_id)}), 404)

    # Verify the parent exam is published
    exam = session.get(Exam, exam_set.exam_id)
    if exam is None or not exam.is_published:
        return make_response(jsonify({"error": "not_found", "message": "Exam is not available"}), 404)

    # ── Ownership check: enforce strict exam isolation ───────────────────────
    # Institution student → can only access their institution's exams
    # Personal student   → can only access platform-wide exams (institution_id IS NULL)
    student_subtype = _student.get("student_subtype", "direct_subscriber")
    student_institution_id = _student.get("institution_id")

    if student_subtype == "institution_linked":
        # Must belong to their institution OR be platform-wide (created by admin)
        if exam.institution_id is not None and str(exam.institution_id) != str(student_institution_id):
            return make_response(jsonify({"error": "not_found", "message": "Exam is not available"}), 404)
    else:
        # Personal student: must be platform-wide (institution_id IS NULL)
        if exam.institution_id is not None:
            return make_response(jsonify({"error": "not_found", "message": "Exam is not available"}), 404)

    # Ensure set questions are synchronized with Set A's question pool in shuffled order sequence
    sets = session.execute(
        select(ExamSet).where(ExamSet.exam_id == exam.id).order_by(ExamSet.set_label.asc())
    ).scalars().all()
    if sets and len(sets) > 1 and exam_set.id != sets[0].id:
        set_a_qids = session.execute(
            select(ExamSetQuestion.question_id)
            .where(ExamSetQuestion.exam_set_id == sets[0].id)
            .order_by(ExamSetQuestion.order_index.asc())
        ).scalars().all()
        cur_qids = session.execute(
            select(ExamSetQuestion.question_id)
            .where(ExamSetQuestion.exam_set_id == set_id)
            .order_by(ExamSetQuestion.order_index.asc())
        ).scalars().all()
        base_set = set(set_a_qids)
        base_list = list(set_a_qids)
        if set_a_qids and (set(cur_qids) != base_set or list(cur_qids) == base_list):
            from sqlalchemy import delete
            import random
            session.execute(delete(ExamSetQuestion).where(ExamSetQuestion.exam_set_id == set_id))
            shuffled_qids = list(base_list)
            random.shuffle(shuffled_qids)
            if shuffled_qids == base_list and len(shuffled_qids) > 1:
                shuffled_qids.reverse()
            session.add_all([
                ExamSetQuestion(exam_set_id=set_id, question_id=qid, order_index=idx)
                for idx, qid in enumerate(shuffled_qids)
            ])
            session.commit()

    # Load questions ordered by position
    stmt = (
        select(Question, ExamSetQuestion.order_index)
        .join(ExamSetQuestion, ExamSetQuestion.question_id == Question.id)
        .where(ExamSetQuestion.exam_set_id == set_id)
        .order_by(ExamSetQuestion.order_index.asc())
    )
    rows = session.execute(stmt).all()
    from ..rag.mcq_extractor import infer_question_subtype, shuffle_options_for_set_label

    questions = []
    for question, _order in rows:
        st = infer_question_subtype(question.question_text, question.options or [], exam.subject)
        shuffled_opts, new_ans = shuffle_options_for_set_label(question.options or [], question.correct_option, exam_set.set_label)
        questions.append({
            "q": question.question_text,
            "type": "MCQ",
            "opts": shuffled_opts,
            "topic": question.topic or "General",
            "ans": str(new_ans),
            "subtype": st,
            "exp": question.explanation or "",
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
