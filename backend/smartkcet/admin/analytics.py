"""Admin aggregate analytics endpoint using Flask Blueprint."""

from __future__ import annotations

import uuid
from typing import Any, Optional

from flask import Blueprint, jsonify, request
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..db.models import Exam, ExamSet, Submission, Subject, User
from ..db.session import get_db
from ..middleware.rbac import require_admin, require_authenticated

router = Blueprint("admin_analytics", __name__, url_prefix="/api/admin")

_DEFAULT_LIMIT = 100
_MAX_LIMIT = 500


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


@router.route("/analytics", methods=["GET"])
@require_authenticated
def get_analytics():
    session: Session = get_db()
    token_payload = getattr(request, "token_payload", {}) or {}
    admin_role = token_payload.get("role")
    if admin_role not in ("platform_admin", "institution_admin"):
        return jsonify({"error": "forbidden", "message": "Admin access required"}), 403

    subject = request.args.get("subject")
    student = request.args.get("student")
    set_param = request.args.get("set")
    status_filter = request.args.get("status")
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

    valid_statuses = ("completed", "in_progress")
    if status_filter is not None and status_filter not in valid_statuses:
        return _validation_error(f"status must be one of {list(valid_statuses)}", field="status")

    set_uuid: Optional[uuid.UUID] = None
    if set_param is not None:
        try:
            set_uuid = uuid.UUID(set_param)
        except (ValueError, AttributeError):
            return _validation_error("set must be a valid UUID (exam_set_id)", field="set")

    capped_limit = min(max(1, limit), _MAX_LIMIT)

    filters_response: dict[str, Any] = {
        "subject": selected_subject.value if selected_subject is not None else None,
        "student": student if student else None,
        "set": set_param if set_param else None,
        "status": status_filter if status_filter else None,
    }

    stmt = (
        select(Submission, ExamSet, Exam, User)
        .join(ExamSet, ExamSet.id == Submission.exam_set_id)
        .join(Exam, Exam.id == ExamSet.exam_id)
        .join(User, User.id == Submission.user_id)
    )

    admin_institution_id = token_payload.get("institution_id")
    if admin_role == "institution_admin" and admin_institution_id is not None:
        stmt = stmt.where(User.institution_id == admin_institution_id)

    if selected_subject is not None:
        stmt = stmt.where(Exam.subject == selected_subject.value)

    if student:
        stmt = stmt.where(User.kcet_student_id == student.strip())

    if set_uuid is not None:
        stmt = stmt.where(Submission.exam_set_id == set_uuid)

    if status_filter is not None:
        stmt = stmt.where(Submission.status == status_filter)

    stmt = stmt.order_by(Submission.submitted_at.desc(), Submission.id.asc())

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = int(session.execute(count_stmt).scalar_one())

    stmt = stmt.offset(offset).limit(capped_limit)
    rows = session.execute(stmt).all()

    submissions: list[dict[str, Any]] = []
    for submission, exam_set, exam, user in rows:
        submitted_at = submission.submitted_at
        submissions.append(
            {
                "id": str(submission.id),
                "student_name": user.display_name,
                "kcet_student_id": user.kcet_student_id or "",
                "exam_set_id": str(submission.exam_set_id),
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
        )

    is_empty = total == 0

    return jsonify({
        "submissions": submissions,
        "total": total,
        "empty": is_empty,
        "filters": filters_response,
        "limit": capped_limit,
        "offset": offset,
    }), 200


__all__ = ["router"]
