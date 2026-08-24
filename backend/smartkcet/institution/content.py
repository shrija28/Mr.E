"""Institution Admin content management endpoints using Flask Blueprint."""

from __future__ import annotations

import hashlib
import logging
import random
import uuid
from typing import Any, List, Optional

from flask import Blueprint, jsonify, request
from sqlalchemy import delete, func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from ..db.models import (
    Exam, ExamSet, ExamSetQuestion, IndexedFile, Question, Subject, Submission, User,
)
from ..db.session import get_db
from ..db.subscription_models import Institution, Subscription, SubscriptionPlan
from ..middleware.rbac import require_institution_admin, current_user

try:
    from ..rag.parsing import (
        chunk_text,
        extract_text_from_docx,
        extract_text_from_pdf,
        extract_text_from_txt,
    )
    PARSING_AVAILABLE = True
except ImportError as e:
    logger = logging.getLogger("smartkcet.institution.content")
    logger.warning("RAG parsing module not available: %s", e)
    PARSING_AVAILABLE = False
    chunk_text = None
    extract_text_from_docx = None
    extract_text_from_pdf = None
    extract_text_from_txt = None

from ..rag.store import stores

logger = logging.getLogger("smartkcet.institution.content")

router = Blueprint("institution_content", __name__, url_prefix="/api/institution/content")

MAX_FILE_SIZE_MB = 20
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
MAX_FILES_PER_BATCH = 10
PAGE_SIZE = 50

FEATURE_ADMIN_QBANK = "admin_question_bank"
FEATURE_UNLIMITED_UPLOADS = "unlimited_uploads"
FEATURE_AI_ANALYTICS = "ai_analytics"
FEATURE_ADVANCED_ANALYTICS = "advanced_analytics"
SET_LABELS = ("A", "B", "C", "D")
QUESTIONS_PER_SET = 20
QUESTIONS_PER_EXAM = QUESTIONS_PER_SET * len(SET_LABELS)


def _get_active_plan(db: Session, institution_id: uuid.UUID) -> Optional[SubscriptionPlan]:
    sub = (
        db.query(Subscription)
        .filter(
            Subscription.institution_id == institution_id,
            Subscription.status.in_(["trial", "active", "overdue", "grace_period"]),
        )
        .first()
    )
    if not sub:
        return None
    return db.query(SubscriptionPlan).filter(SubscriptionPlan.id == sub.plan_id).first()


def _has_feature(plan: Optional[SubscriptionPlan], feature: str) -> bool:
    if plan is None:
        return False
    flags = plan.feature_flags or {}
    if not flags:
        return True
    return bool(flags.get(feature, True))


def _require_feature_check(db: Session, institution_id: uuid.UUID, feature: str, feature_label: str = "This feature"):
    plan = _get_active_plan(db, institution_id)
    if not _has_feature(plan, feature):
        return jsonify({
            "error": "feature_not_included",
            "feature": feature,
            "message": f"{feature_label} is not included in your current plan. Upgrade to Premium to access this feature.",
            "upgrade_url": "/institution/pricing",
        }), 403
    return None


def _institution_id_from_req() -> Optional[uuid.UUID]:
    user = getattr(request, "token_payload", {}) or {}
    inst_id_str = user.get("institution_id")
    if not inst_id_str:
        return None
    try:
        return uuid.UUID(inst_id_str)
    except (ValueError, TypeError):
        return None


def check_subscription_active(db: Session, institution_id: uuid.UUID) -> bool:
    return True


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


def _extract_text(filename: str, content: bytes) -> Optional[str]:
    lowered = filename.lower()
    if lowered.endswith(".pdf"):
        return extract_text_from_pdf(content) if extract_text_from_pdf else None
    if lowered.endswith(".docx"):
        return extract_text_from_docx(content) if extract_text_from_docx else None
    if lowered.endswith(".txt"):
        return extract_text_from_txt(content) if extract_text_from_txt else None
    return None


def _compute_file_hash(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _check_duplicate(db: Session, subject: str, file_hash: str, institution_id: uuid.UUID) -> Optional[IndexedFile]:
    stmt = select(IndexedFile).where(
        IndexedFile.subject == subject,
        IndexedFile.file_hash == file_hash,
        IndexedFile.institution_id == institution_id,
    )
    return db.execute(stmt).scalar_one_or_none()


def _record_indexed_file(
    db: Session,
    subject: str,
    filename: str,
    file_hash: str,
    file_size: int,
    chunk_count: int,
    institution_id: uuid.UUID,
    file_type: str = "question_paper",
) -> IndexedFile:
    record = IndexedFile(
        subject=subject,
        filename=filename,
        file_hash=file_hash,
        file_size=file_size,
        chunk_count=chunk_count,
        file_type=file_type,
        institution_id=institution_id,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def _store_mcqs_in_db(
    db: Session,
    mcqs: List[dict],
    subject: str,
    batch_id: uuid.UUID,
    institution_id: uuid.UUID,
) -> int:
    stored = 0
    for mcq in mcqs:
        q_text = mcq.get("q", "").strip()
        opts = mcq.get("opts", [])
        ans = mcq.get("ans", 0)
        topic = mcq.get("topic", "General")
        if not q_text or not isinstance(opts, list) or len(opts) != 4:
            continue
        row = Question(
            subject=subject,
            question_text=q_text,
            options=opts,
            correct_option=str(ans),
            topic=topic if isinstance(topic, str) else "General",
            generation_batch_id=batch_id,
            institution_id=institution_id,
            explanation=mcq.get("exp", ""),
        )
        db.add(row)
        stored += 1
    if stored > 0:
        try:
            db.commit()
        except Exception as exc:
            logger.warning("Failed to commit MCQs: %s", exc)
            db.rollback()
            return 0
    return stored


def _serialise_question(row: Question) -> dict[str, Any]:
    return {
        "id": str(row.id),
        "subject": row.subject,
        "question_text": row.question_text,
        "options": row.options,
        "correct_option": row.correct_option,
        "topic": row.topic,
        "explanation": row.explanation,
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }


def _counts_by_subject(session: Session, institution_id: uuid.UUID) -> dict[str, int]:
    rows = session.execute(
        select(Question.subject, func.count(Question.id))
        .where(Question.institution_id == institution_id)
        .group_by(Question.subject)
    ).all()
    found = {s: int(c) for s, c in rows}
    return {s.value: int(found.get(s.value, 0)) for s in Subject}


@router.route("/upload/single", methods=["POST"])
@require_institution_admin
def upload_single_file():
    db: Session = get_db()
    inst_id = _institution_id_from_req()
    if not inst_id:
        return jsonify({"error": "forbidden", "message": "Institution ID not found"}), 403

    subject = request.form.get("subject")
    file_type = request.form.get("file_type", "question_paper")
    uploaded_file = request.files.get("file")

    if not uploaded_file:
        return _validation_error("file is required", field="file")

    selected = _normalise_subject(subject)
    if selected is None:
        return _validation_error(f"subject is required and must be one of {[s.value for s in Subject]}", field="subject")

    filename = uploaded_file.filename or ""
    content = uploaded_file.read()
    file_size = len(content)

    if file_size > MAX_FILE_SIZE_BYTES:
        return _validation_error(f"File exceeds {MAX_FILE_SIZE_MB}MB limit", field="file")

    file_hash = _compute_file_hash(content)
    existing = _check_duplicate(db, selected.value, file_hash, inst_id)
    if existing is not None:
        return jsonify({
            "status": "duplicate",
            "filename": filename,
            "file_hash": file_hash,
            "file_size": file_size,
            "chunk_count": existing.chunk_count,
            "message": f"Already indexed as '{existing.filename}' with {existing.chunk_count} chunks",
        }), 200

    text = _extract_text(filename, content)
    if text is None:
        return jsonify({
            "status": "unsupported",
            "filename": filename,
            "file_hash": file_hash,
            "file_size": file_size,
            "chunk_count": 0,
            "message": f"Unsupported file type: {filename}",
        }), 200

    if not text.strip():
        return jsonify({"status": "empty", "filename": filename, "chunk_count": 0, "message": "No text extracted"}), 200

    chunks = chunk_text(text) if chunk_text else [text]
    if not chunks:
        return jsonify({"status": "empty", "filename": filename, "chunk_count": 0, "message": "Text too short"}), 200

    if stores:
        stores.add(selected, chunks)

    _record_indexed_file(db, selected.value, filename, file_hash, file_size, len(chunks), inst_id, file_type)
    mcq_batch_id = uuid.uuid4()
    mcqs = extract_or_generate_mcqs(text, topic=selected.value, min_questions=5)
    questions_extracted = _store_mcqs_in_db(db, mcqs, selected.value, mcq_batch_id, inst_id)

    return jsonify({
        "status": "indexed",
        "filename": filename,
        "file_hash": file_hash,
        "file_size": file_size,
        "chunk_count": len(chunks),
        "questions_extracted": questions_extracted,
        "message": f"Successfully indexed {len(chunks)} chunks, extracted {questions_extracted} questions",
    }), 200


@router.route("/upload", methods=["POST"])
@require_institution_admin
def upload_institution_content():
    db: Session = get_db()
    inst_id = _institution_id_from_req()
    if not inst_id:
        return jsonify({"error": "forbidden", "message": "Institution ID not found"}), 403

    subject = request.form.get("subject")
    file_type = request.form.get("file_type", "question_paper")
    uploaded_files = request.files.getlist("files")

    selected = _normalise_subject(subject)
    if selected is None:
        return _validation_error(f"subject is required and must be one of {[s.value for s in Subject]}", field="subject")

    if len(uploaded_files) > MAX_FILES_PER_BATCH:
        return _validation_error(f"Maximum {MAX_FILES_PER_BATCH} files per upload batch", field="files")

    warnings, already_indexed = [], []
    indexed_files = total_chunks = total_questions_extracted = 0

    for upload_file in uploaded_files:
        filename = upload_file.filename or ""
        content = upload_file.read()
        file_size = len(content)

        if file_size > MAX_FILE_SIZE_BYTES:
            warnings.append(f"{filename}: exceeds size limit")
            continue

        file_hash = _compute_file_hash(content)
        existing = _check_duplicate(db, selected.value, file_hash, inst_id)
        if existing is not None:
            already_indexed.append({"filename": filename, "existing_filename": existing.filename, "chunk_count": existing.chunk_count})
            continue

        text = _extract_text(filename, content)
        if text is None or not text.strip():
            warnings.append(f"{filename}: unsupported or empty")
            continue

        chunks = chunk_text(text) if chunk_text else [text]
        if not chunks:
            warnings.append(f"{filename}: text too short")
            continue

        if stores:
            stores.add(selected, chunks)

        _record_indexed_file(db, selected.value, filename, file_hash, file_size, len(chunks), inst_id, file_type)
        mcq_batch_id = uuid.uuid4()
        mcqs = extract_or_generate_mcqs(text, topic=selected.value, min_questions=5)
        q_ext = _store_mcqs_in_db(db, mcqs, selected.value, mcq_batch_id, inst_id)

        indexed_files += 1
        total_chunks += len(chunks)
        total_questions_extracted += q_ext

    return jsonify({
        "success": True,
        "institution_id": str(inst_id),
        "subject": selected.value,
        "indexed_files": indexed_files,
        "total_chunks": total_chunks,
        "questions_extracted": total_questions_extracted,
        "warnings": warnings,
        "already_indexed": already_indexed,
    }), 200


@router.route("/upload/files", methods=["GET"])
@require_institution_admin
def list_institution_indexed_files():
    db: Session = get_db()
    inst_id = _institution_id_from_req()
    subject = request.args.get("subject")

    selected = _normalise_subject(subject)
    if selected is None:
        return _validation_error(f"subject must be one of {[s.value for s in Subject]}", field="subject")

    stmt = (
        select(IndexedFile)
        .where(IndexedFile.subject == selected.value, IndexedFile.institution_id == inst_id)
        .order_by(IndexedFile.indexed_at.desc())
    )
    files = db.execute(stmt).scalars().all()

    return jsonify({
        "institution_id": str(inst_id),
        "subject": selected.value,
        "files": [
            {
                "id": str(f.id),
                "filename": f.filename,
                "file_size": f.file_size,
                "chunk_count": f.chunk_count,
                "file_type": f.file_type,
                "indexed_at": f.indexed_at.isoformat() if f.indexed_at else None,
            }
            for f in files
        ],
    }), 200


@router.route("/questions/counts", methods=["GET"])
@require_institution_admin
def get_question_counts():
    session: Session = get_db()
    inst_id = _institution_id_from_req()
    counts = _counts_by_subject(session, inst_id)
    insufficient = {s: c < QUESTIONS_PER_EXAM for s, c in counts.items()}
    return jsonify({
        "institution_id": str(inst_id),
        "counts": counts,
        "insufficient": insufficient,
        "threshold": QUESTIONS_PER_EXAM,
    }), 200


@router.route("/questions", methods=["GET"])
@require_institution_admin
def list_institution_questions():
    session: Session = get_db()
    inst_id = _institution_id_from_req()
    subject = request.args.get("subject")
    raw_page = request.args.get("page", 1)
    try:
        page = max(1, int(raw_page))
    except (ValueError, TypeError):
        page = 1

    base_filter = [Question.institution_id == inst_id]
    selected = _normalise_subject(subject)
    if subject is not None:
        if selected is None:
            return _validation_error(f"subject must be one of {[s.value for s in Subject]}", field="subject")
        base_filter.append(Question.subject == selected.value)

    total = int(session.execute(select(func.count(Question.id)).where(*base_filter)).scalar_one())
    rows = session.execute(
        select(Question)
        .where(*base_filter)
        .order_by(Question.created_at.desc(), Question.id.asc())
        .offset((page - 1) * PAGE_SIZE)
        .limit(PAGE_SIZE)
    ).scalars().all()

    return jsonify({
        "institution_id": str(inst_id),
        "questions": [_serialise_question(r) for r in rows],
        "total": total,
        "page": page,
        "page_size": PAGE_SIZE,
        "subject": selected.value if selected else None,
        "counts_by_subject": _counts_by_subject(session, inst_id),
    }), 200


@router.route("/questions/<question_id>", methods=["DELETE"])
@require_institution_admin
def delete_institution_question(question_id: str):
    session: Session = get_db()
    inst_id = _institution_id_from_req()
    try:
        qid = uuid.UUID(question_id)
    except (ValueError, TypeError):
        return jsonify({"error": "validation_error", "message": "Invalid question_id"}), 400

    try:
        result = session.execute(
            delete(Question).where(Question.id == qid, Question.institution_id == inst_id)
        )
        if int(result.rowcount or 0) <= 0:
            session.rollback()
            return jsonify({"deleted": False, "error": "not_found", "id": question_id}), 404
        session.commit()
    except SQLAlchemyError as exc:
        session.rollback()
        return jsonify({"deleted": False, "error": type(exc).__name__, "id": question_id}), 500

    return jsonify({"deleted": True, "id": question_id}), 200


@router.route("/exams", methods=["POST"])
@require_institution_admin
def create_institution_exam():
    session: Session = get_db()
    inst_id = _institution_id_from_req()
    subject = request.args.get("subject")
    exam_name = request.args.get("exam_name")

    selected = _normalise_subject(subject)
    if selected is None:
        return _validation_error(f"subject is required and must be one of {[s.value for s in Subject]}", field="subject")

    available = int(session.execute(
        select(func.count(Question.id)).where(Question.subject == selected.value, Question.institution_id == inst_id)
    ).scalar_one())

    if available < 4:
        return jsonify({
            "error": "insufficient_questions",
            "subject": selected.value,
            "count": available,
            "required": 4,
            "message": f"Not enough questions in institution's {selected.value} bank.",
        }), 422

    id_rows = session.execute(
        select(Question.id).where(Question.subject == selected.value, Question.institution_id == inst_id)
    ).all()
    all_ids: list[uuid.UUID] = [row[0] for row in id_rows]

    exam_size = min(len(all_ids), QUESTIONS_PER_EXAM)
    num_sets = len(SET_LABELS)
    exam_size = exam_size - (exam_size % num_sets)
    questions_per_set = exam_size // num_sets

    if exam_size < 4:
        return jsonify({"error": "insufficient_questions", "subject": selected.value, "count": len(all_ids), "required": 4}), 422

    drawn = random.sample(all_ids, exam_size)
    partitions = [drawn[i * questions_per_set : (i + 1) * questions_per_set] for i in range(num_sets)]

    exam = Exam(subject=selected.value, exam_name=exam_name, institution_id=inst_id)
    session.add(exam)

    try:
        session.flush()
        sets_payload: list[dict[str, Any]] = []
        for label, qids in zip(SET_LABELS, partitions):
            exam_set = ExamSet(exam_id=exam.id, set_label=label)
            session.add(exam_set)
            session.flush()
            session.add_all([ExamSetQuestion(exam_set_id=exam_set.id, question_id=qid, order_index=i) for i, qid in enumerate(qids)])
            sets_payload.append({"label": label, "exam_set_id": str(exam_set.id), "question_count": len(qids)})
        session.commit()
    except Exception as exc:
        session.rollback()
        return jsonify({"error": "exam_creation_failed", "message": str(exc)}), 500

    return jsonify({
        "exam_id": str(exam.id),
        "institution_id": str(inst_id),
        "subject": selected.value,
        "exam_name": exam.exam_name,
        "set_ids": sets_payload,
        "created_at": exam.created_at.isoformat() if exam.created_at else None,
    }), 201


@router.route("/exams", methods=["GET"])
@require_institution_admin
def list_institution_exams():
    session: Session = get_db()
    inst_id = _institution_id_from_req()
    subject = request.args.get("subject")

    stmt = (
        select(Exam, func.count(ExamSet.id).label("set_count"))
        .outerjoin(ExamSet, ExamSet.exam_id == Exam.id)
        .where(Exam.institution_id == inst_id)
        .group_by(Exam.id)
        .order_by(Exam.created_at.desc(), Exam.id.asc())
    )

    selected = _normalise_subject(subject)
    if subject is not None:
        if selected is None:
            return _validation_error(f"subject must be one of {[s.value for s in Subject]}", field="subject")
        stmt = stmt.where(Exam.subject == selected.value)

    rows = session.execute(stmt).all()
    exams_payload = [
        {
            "exam_id": str(exam.id),
            "subject": exam.subject,
            "exam_name": exam.exam_name,
            "created_at": exam.created_at.isoformat() if exam.created_at else None,
            "is_published": bool(exam.is_published),
            "set_count": int(set_count or 0),
        }
        for exam, set_count in rows
    ]

    return jsonify({
        "institution_id": str(inst_id),
        "exams": exams_payload,
        "subject": selected.value if selected else None,
        "total": len(exams_payload),
    }), 200


@router.route("/exams/<exam_id>", methods=["PATCH"])
@require_institution_admin
def patch_institution_exam(exam_id: str):
    session: Session = get_db()
    inst_id = _institution_id_from_req()
    data = request.get_json(silent=True) or {}
    is_published = data.get("is_published")

    if is_published is None:
        return _validation_error("is_published is required", field="is_published")

    try:
        eid = uuid.UUID(exam_id)
    except (ValueError, TypeError):
        return jsonify({"error": "validation_error", "message": "Invalid exam_id"}), 400

    exam = session.get(Exam, eid)
    if exam is None or exam.institution_id != inst_id:
        return jsonify({"error": "not_found", "exam_id": exam_id}), 404

    exam.is_published = bool(is_published)
    try:
        session.commit()
    except SQLAlchemyError as exc:
        session.rollback()
        return jsonify({"error": "update_failed", "message": str(exc)}), 500

    return jsonify({"exam_id": str(exam.id), "is_published": exam.is_published}), 200


@router.route("/analytics", methods=["GET"])
@require_institution_admin
def get_institution_content_analytics():
    db: Session = get_db()
    inst_id = _institution_id_from_req()
    students = db.query(User).filter(User.institution_id == inst_id, User.role == "student").all()
    student_ids = [s.id for s in students]

    if not student_ids:
        return jsonify({
            "institution_id": str(inst_id),
            "total_students": 0,
            "total_submissions": 0,
            "average_score": 0.0,
            "students": [],
        }), 200

    submissions = (
        db.query(Submission)
        .join(ExamSet, Submission.exam_set_id == ExamSet.id)
        .join(Exam, ExamSet.exam_id == Exam.id)
        .filter(Submission.user_id.in_(student_ids), Exam.institution_id == inst_id)
        .all()
    )

    total_submissions = len(submissions)
    average_score = (sum(s.score_pct for s in submissions) / total_submissions) if total_submissions > 0 else 0.0

    student_analytics = []
    for student in students:
        student_subs = [s for s in submissions if s.user_id == student.id]
        avg = (sum(s.score_pct for s in student_subs) / len(student_subs)) if student_subs else 0.0
        student_analytics.append({
            "student_id": str(student.id),
            "display_name": student.display_name,
            "email": student.email,
            "total_attempts": len(student_subs),
            "average_score": round(avg, 2),
        })

    student_analytics.sort(key=lambda x: x["average_score"], reverse=True)

    return jsonify({
        "institution_id": str(inst_id),
        "total_students": len(students),
        "total_submissions": total_submissions,
        "average_score": round(average_score, 2),
        "students": student_analytics,
    }), 200


@router.route("/admin-questions", methods=["GET"])
@require_institution_admin
def get_admin_questions_for_institution():
    session: Session = get_db()
    inst_id = _institution_id_from_req()
    err_res = _require_feature_check(session, inst_id, FEATURE_ADMIN_QBANK, "Access to the admin KCET question bank")
    if err_res:
        return err_res

    subject = request.args.get("subject")
    raw_page = request.args.get("page", 1)
    try:
        page = max(1, int(raw_page))
    except (ValueError, TypeError):
        page = 1

    base_filter = [Question.institution_id.is_(None)]
    if subject:
        selected = _normalise_subject(subject)
        if selected is None:
            return _validation_error(f"subject must be one of {[s.value for s in Subject]}", field="subject")
        base_filter.append(Question.subject == selected.value)

    total = int(session.execute(select(func.count(Question.id)).where(*base_filter)).scalar_one())
    rows = session.execute(
        select(Question)
        .where(*base_filter)
        .order_by(Question.created_at.desc(), Question.id.asc())
        .offset((page - 1) * PAGE_SIZE)
        .limit(PAGE_SIZE)
    ).scalars().all()

    return jsonify({
        "institution_id": str(inst_id),
        "source": "admin_kcet_bank",
        "questions": [_serialise_question(r) for r in rows],
        "total": total,
        "page": page,
        "page_size": PAGE_SIZE,
    }), 200


@router.route("/feature-access", methods=["GET"])
@require_institution_admin
def get_feature_access():
    session: Session = get_db()
    inst_id = _institution_id_from_req()
    plan = _get_active_plan(session, inst_id)
    features = [FEATURE_ADMIN_QBANK, FEATURE_UNLIMITED_UPLOADS, FEATURE_AI_ANALYTICS, FEATURE_ADVANCED_ANALYTICS]

    return jsonify({
        "institution_id": str(inst_id),
        "plan_name": plan.name if plan else "No plan",
        "has_active_subscription": plan is not None,
        "features": {f: _has_feature(plan, f) for f in features},
    }), 200


__all__ = ["router"]
