"""Institution Admin content management endpoints.

Mirrors the Admin upload/questions flow but scoped to the institution's
namespace.  Every question, indexed file, and exam created here is tagged
with the institution's UUID so there is **zero overlap** with the platform-
wide (admin) data.

Endpoints
---------
POST   /content/upload              – batch file upload + MCQ extraction
POST   /content/upload/single       – single-file upload with progress info
GET    /content/upload/files        – list institution's indexed files
GET    /content/questions           – paginated institution question bank
GET    /content/questions/counts    – per-subject question counts
DELETE /content/questions/{id}      – delete institution question
POST   /content/exams               – create institution-scoped exam
GET    /content/exams               – list institution-scoped exams
PATCH  /content/exams/{id}          – publish / unpublish institution exam
GET    /content/analytics           – institution student analytics
"""

from __future__ import annotations
import os

import hashlib
import logging
import random
import uuid
from typing import Annotated, Any, List, Optional
from pydantic import BaseModel

import os
from flask import Blueprint, request, g, make_response, jsonify, Response
from fastapi.responses import JSONResponse
from sqlalchemy import delete, func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from ..db.models import (
    Exam, ExamSet, ExamSetQuestion, IndexedFile, Question, Subject, Submission, User,
)
from ..db.session import get_async_session as get_session
from ..db.subscription_models import Institution, Subscription, SubscriptionPlan
from ..middleware.rbac import require_authenticated
from ..rag.mcq_extractor import extract_or_generate_mcqs

# Graceful degradation for Python 3.14 compatibility
# pytesseract is not available in Python 3.14 (pkgutil.find_loader removed)
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
    logger.warning(
        "RAG parsing module not available (Python 3.14 compatibility): %s. "
        "File upload functionality will be limited.",
        e,
    )
    PARSING_AVAILABLE = False
    # Provide stub functions so the module can still be imported
    chunk_text = None
    extract_text_from_docx = None
    extract_text_from_pdf = None
    extract_text_from_txt = None

from ..rag.store import stores

logger = logging.getLogger("smartkcet.institution.content")

router = Blueprint("institution_content", __name__)

# Limits (supports large textbooks and papers without restriction)
MAX_FILE_SIZE_MB = 1000
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
MAX_FILES_PER_BATCH = 10
PAGE_SIZE = 50


# ---------------------------------------------------------------------------
# Feature flag helpers
# ---------------------------------------------------------------------------

FEATURE_ADMIN_QBANK = "admin_question_bank"
FEATURE_UNLIMITED_UPLOADS = "unlimited_uploads"
FEATURE_AI_ANALYTICS = "ai_analytics"
FEATURE_ADVANCED_ANALYTICS = "advanced_analytics"


def _get_active_plan(db: Session, institution_id: uuid.UUID)-> Optional[SubscriptionPlan]:
    """Return the active SubscriptionPlan for the institution, or None."""
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


def _has_feature(plan: Optional[SubscriptionPlan], feature: str)-> bool:
    """Check if a plan's feature_flags grants access to a specific feature.

    If the plan is None (no subscription) → all features denied.
    If feature_flags is empty or feature key is absent → feature is allowed
    (default-open so existing plans without explicit flags work).
    """
    if plan is None:
        return False
    flags = plan.feature_flags or {}
    if not flags:
        return True  # Legacy plan with no flags — allow all
    return bool(flags.get(feature, True))  # Missing key → allowed


def _require_feature(db: Session, institution_id: uuid.UUID, feature: str, feature_label: str = "This feature")-> None:
    """Raise 403 if institution's plan does not include the given feature flag."""
    plan = _get_active_plan(db, institution_id)
    if not _has_feature(plan, feature):
        raise HTTPException(
            status_code=403,
            detail={
                "error": "feature_not_included",
                "feature": feature,
                "message": (
                    f"{feature_label} is not included in your current plan. "
                    "Upgrade to Premium to access this feature."
                ),
                "upgrade_url": "/institution/pricing",
            },
        )

# Exam creation constants (mirrors admin: 4 sets × 60 = 240)
SET_LABELS = ("A", "B", "C", "D")
QUESTIONS_PER_SET = 60
QUESTIONS_PER_EXAM = QUESTIONS_PER_SET * len(SET_LABELS)  # 240


# ---------------------------------------------------------------------------
# Auth dependency
# ---------------------------------------------------------------------------

def require_institution_admin()-> dict:    
    payload = require_authenticated()
    
    payload = require_authenticated()
    if payload.get("role") != "institution_admin":
        raise HTTPException(
            status_code=403,
            detail={"error": "forbidden", "message": "Institution admin access required"},
        )
    if "institution_id" not in payload:
        raise HTTPException(
            status_code=403,
            detail={"error": "forbidden", "message": "Institution ID not found in token"},
        )
    return payload


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _institution_id(payload: dict)-> uuid.UUID:
    return uuid.UUID(payload["institution_id"])


def check_subscription_active(db: Session, institution_id: uuid.UUID)-> bool:
    # Bypass subscription check globally for institution uploads
    return True


def _validation_error(message: str, field: Optional[str] = None)-> JSONResponse:
    body: dict[str, Any] = {"error": "validation_error", "message": message}
    if field is not None:
        body["field"] = field
    return JSONResponse(status_code=400, content=body)


def _normalise_subject(value: Optional[str])-> Optional[Subject]:
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    if not stripped:
        return None
    try:
        return Subject(stripped)
    except ValueError:
        return None


def _extract_text(filename: str, content: bytes)-> Optional[str]:
    lowered = filename.lower()
    if lowered.endswith(".pdf"):
        return extract_text_from_pdf(content)
    if lowered.endswith(".docx"):
        return extract_text_from_docx(content)
    if lowered.endswith(".txt"):
        return extract_text_from_txt(content)
    return None


def _compute_file_hash(content: bytes)-> str:
    return hashlib.sha256(content).hexdigest()


def _check_duplicate(db: Session, subject: str, file_hash: str, institution_id: uuid.UUID)-> Optional[IndexedFile]:
    """Check if this institution already indexed this exact file for the subject."""
    stmt = select(IndexedFile).where(
        IndexedFile.subject == subject,
        IndexedFile.file_hash == file_hash,
        IndexedFile.institution_id == institution_id,
    )
    return db.execute(stmt).scalar_one_or_none()


def _record_indexed_file(db: Session, subject: str, filename: str, file_hash: str, file_size: int, chunk_count: int, institution_id: uuid.UUID, file_type: str = "question_paper")-> IndexedFile:
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


def _store_mcqs_in_db(db: Session, mcqs: List[dict], subject: str, batch_id: uuid.UUID, institution_id: uuid.UUID)-> int:
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


def _serialise_question(row: Question)-> dict[str, Any]:
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


def _counts_by_subject(session: Session, institution_id: uuid.UUID)-> dict[str, int]:
    rows = session.execute(
        select(Question.subject, func.count(Question.id))
        .where(Question.institution_id == institution_id)
        .group_by(Question.subject)
    ).all()
    found = {s: int(c) for s, c in rows}
    return {s.value: int(found.get(s.value, 0)) for s in Subject}


# ---------------------------------------------------------------------------
# POST /content/upload/single  (per-file progress, mirrors admin)
# ---------------------------------------------------------------------------

@router.route("/content/upload/single", methods=["POST"])
def upload_single_file(subject: Optional[str] = None, file_type: str = "question_paper", file: Any = None)-> Any:    
    payload = require_institution_admin()
    from flask import g, request
    db = getattr(g, "db", None)
    session = db
    """Upload a single file and return per-file status for progress tracking."""
    inst_id = _institution_id(payload)

    if subject is None:
        subject = request.form.get("subject") or request.args.get("subject")
    if file_type is None or file_type == "question_paper":
        file_type = request.form.get("file_type") or request.args.get("file_type") or "question_paper"
    if file is None:
        file = request.files.get("file")
    if file is None:
        return _validation_error("file is required", field="file")

    if not check_subscription_active(db, inst_id):
        raise HTTPException(
            status_code=403,
            detail={
                "error": "subscription_inactive",
                "message": "Institution subscription must be active to upload content.",
            },
        )

    selected = _normalise_subject(subject)
    if selected is None:
        return _validation_error(
            f"subject is required and must be one of {[s.value for s in Subject]}",
            field="subject",
        )

    filename = file.filename or ""
    content = file.read()
    file_size = len(content)

    if file_size > MAX_FILE_SIZE_BYTES:
        return _validation_error(
            f"File exceeds {MAX_FILE_SIZE_MB}MB limit",
            field="file",
        )

    file_hash = _compute_file_hash(content)

    # Duplicate check (scoped to this institution)
    existing = _check_duplicate(db, selected.value, file_hash, inst_id)
    if existing is not None:
        return {
            "status": "duplicate",
            "filename": filename,
            "file_hash": file_hash,
            "file_size": file_size,
            "chunk_count": existing.chunk_count,
            "message": f"Already indexed as '{existing.filename}' with {existing.chunk_count} chunks",
        }

    text = _extract_text(filename, content)
    if text is None:
        return {
            "status": "unsupported",
            "filename": filename,
            "file_hash": file_hash,
            "file_size": file_size,
            "chunk_count": 0,
            "message": f"Unsupported file type: {filename}",
        }

    if not text.strip():
        return {
            "status": "empty",
            "filename": filename,
            "chunk_count": 0,
            "message": "No text could be extracted from this file",
        }

    chunks = chunk_text(text)
    if not chunks:
        return {
            "status": "empty",
            "filename": filename,
            "chunk_count": 0,
            "message": "Text too short to produce meaningful chunks",
        }

    stores.add(selected, chunks)

    _record_indexed_file(
        db,
        subject=selected.value,
        filename=filename,
        file_hash=file_hash,
        file_size=file_size,
        chunk_count=len(chunks),
        institution_id=inst_id,
        file_type=file_type,
    )

    mcq_batch_id = uuid.uuid4()
    mcqs = extract_or_generate_mcqs(text, topic=selected.value, min_questions=5)
    questions_extracted = _store_mcqs_in_db(
        db, mcqs, selected.value, mcq_batch_id, inst_id
    )
    logger.info(
        "Institution %s: '%s' → %d chunks, %d MCQs for %s",
        inst_id, filename, len(chunks), questions_extracted, selected.value,
    )

    return {
        "status": "indexed",
        "filename": filename,
        "file_hash": file_hash,
        "file_size": file_size,
        "chunk_count": len(chunks),
        "questions_extracted": questions_extracted,
        "message": f"Successfully indexed {len(chunks)} chunks, extracted {questions_extracted} questions",
    }


# ---------------------------------------------------------------------------
# POST /content/upload  (batch upload, mirrors admin)
# ---------------------------------------------------------------------------

@router.route("/content/upload", methods=["POST"])
def upload_institution_content(subject: Optional[str] = None, file_type: str = "question_paper", files: Optional[List[Any]] = None)-> Any:    
    payload = require_institution_admin()
    from flask import g, request
    db = getattr(g, "db", None)
    session = db
    """Batch upload question papers to the institution's question bank."""
    inst_id = _institution_id(payload)

    if subject is None:
        subject = request.form.get("subject") or request.args.get("subject")
    if file_type is None or file_type == "question_paper":
        file_type = request.form.get("file_type") or request.args.get("file_type") or "question_paper"
    if not files:
        files = request.files.getlist("files") or request.files.getlist("file")

    if not files:
        return _validation_error("At least one file is required", field="files")

    if not check_subscription_active(db, inst_id):
        raise HTTPException(
            status_code=403,
            detail={
                "error": "subscription_inactive",
                "message": "Institution subscription must be active to upload content.",
            },
        )

    selected = _normalise_subject(subject)
    if selected is None:
        return _validation_error(
            f"subject is required and must be one of {[s.value for s in Subject]}",
            field="subject",
        )

    if len(files) > MAX_FILES_PER_BATCH:
        return _validation_error(
            f"Maximum {MAX_FILES_PER_BATCH} files per upload batch",
            field="files",
        )

    warnings: List[str] = []
    already_indexed: List[dict] = []
    indexed_files = 0
    total_chunks = 0
    total_questions_extracted = 0

    for upload_file in files:
        filename = upload_file.filename or ""
        content = upload_file.read()
        file_size = len(content)

        if file_size > MAX_FILE_SIZE_BYTES:
            warnings.append(f"{filename}: exceeds {MAX_FILE_SIZE_MB}MB size limit")
            continue

        file_hash = _compute_file_hash(content)

        # Institution-scoped duplicate check
        existing = _check_duplicate(db, selected.value, file_hash, inst_id)
        if existing is not None:
            already_indexed.append({
                "filename": filename,
                "existing_filename": existing.filename,
                "chunk_count": existing.chunk_count,
            })
            continue

        text = _extract_text(filename, content)
        if text is None:
            warnings.append(f"{filename}: unsupported file type (only PDF, DOCX, TXT allowed)")
            continue

        if not text.strip():
            warnings.append(f"{filename}: no text could be extracted")
            continue

        chunks = chunk_text(text)
        if not chunks:
            warnings.append(f"{filename}: text too short to produce meaningful chunks")
            continue

        stores.add(selected, chunks)

        _record_indexed_file(
            db,
            subject=selected.value,
            filename=filename,
            file_hash=file_hash,
            file_size=file_size,
            chunk_count=len(chunks),
            institution_id=inst_id,
            file_type=file_type,
        )

        mcq_batch_id = uuid.uuid4()
        mcqs = extract_or_generate_mcqs(text, topic=selected.value, min_questions=5)
        questions_extracted = _store_mcqs_in_db(
            db, mcqs, selected.value, mcq_batch_id, inst_id
        )
        logger.info(
            "Institution %s: '%s' → %d chunks, %d MCQs for %s",
            inst_id, filename, len(chunks), questions_extracted, selected.value,
        )

        indexed_files += 1
        total_chunks += len(chunks)
        total_questions_extracted += questions_extracted

    return {
        "success": True,
        "institution_id": str(inst_id),
        "subject": selected.value,
        "indexed_files": indexed_files,
        "total_chunks": total_chunks,
        "questions_extracted": total_questions_extracted,
        "warnings": warnings,
        "already_indexed": already_indexed,
    }


# ---------------------------------------------------------------------------
# GET /content/upload/files  (mirrors admin, scoped to institution)
# ---------------------------------------------------------------------------

@router.route("/content/upload/files", methods=["GET"])
def list_institution_indexed_files()-> Any:    
    payload = require_institution_admin()
    from flask import g
    db = getattr(g, "db", None)
    session = db
    from flask import request
    subject = request.args.get("subject", None)
    """Return files previously indexed by this institution for a subject."""
    inst_id = _institution_id(payload)

    selected = _normalise_subject(subject)
    if selected is None:
        return _validation_error(
            f"subject must be one of {[s.value for s in Subject]}",
            field="subject",
        )

    stmt = (
        select(IndexedFile)
        .where(
            IndexedFile.subject == selected.value,
            IndexedFile.institution_id == inst_id,
        )
        .order_by(IndexedFile.indexed_at.desc())
    )
    files = db.execute(stmt).scalars().all()

    return {
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
    }


# ---------------------------------------------------------------------------
# GET /content/questions/counts  (institution question bank counts)
# ---------------------------------------------------------------------------

@router.route("/content/questions/counts", methods=["GET"])
def get_question_counts()-> Any:    
    payload = require_institution_admin()
    from flask import g
    db = getattr(g, "db", None)
    session = db
    """Return per-subject question counts for this institution's bank."""
    inst_id = _institution_id(payload)
    counts = _counts_by_subject(session, inst_id)
    insufficient = {s: c < QUESTIONS_PER_EXAM for s, c in counts.items()}
    return {
        "institution_id": str(inst_id),
        "counts": counts,
        "insufficient": insufficient,
        "threshold": QUESTIONS_PER_EXAM,
    }


# ---------------------------------------------------------------------------
# GET /content/questions  (paginated institution question bank)
# ---------------------------------------------------------------------------

@router.route("/content/questions", methods=["GET"])
def list_institution_questions()-> Any:    
    payload = require_institution_admin()
    from flask import g
    db = getattr(g, "db", None)
    session = db
    from flask import request
    subject = request.args.get("subject", None)
    from flask import request
    page = int(request.args.get("page", 1))
    
    payload = require_institution_admin()
    from flask import g
    db = getattr(g, "db", None)
    session = db
    from flask import request
    subject = request.args.get("subject", None)
    from flask import request
    page = int(request.args.get("page", 1))
    """Paginated list of questions in this institution's bank."""
    inst_id = _institution_id(payload)

    base_filter = [Question.institution_id == inst_id]
    selected = _normalise_subject(subject)
    if subject is not None:
        if selected is None:
            return _validation_error(
                f"subject must be one of {[s.value for s in Subject]}",
                field="subject",
            )
        base_filter.append(Question.subject == selected.value)

    total = int(session.execute(
        select(func.count(Question.id)).where(*base_filter)
    ).scalar_one())

    rows = session.execute(
        select(Question)
        .where(*base_filter)
        .order_by(Question.created_at.desc(), Question.id.asc())
        .offset((page - 1) * PAGE_SIZE)
        .limit(PAGE_SIZE)
    ).scalars().all()

    return {
        "institution_id": str(inst_id),
        "questions": [_serialise_question(r) for r in rows],
        "total": total,
        "page": page,
        "page_size": PAGE_SIZE,
        "subject": selected.value if selected else None,
        "counts_by_subject": _counts_by_subject(session, inst_id),
    }


# ---------------------------------------------------------------------------
# DELETE /content/questions/{question_id}
# ---------------------------------------------------------------------------

@router.route("/content/questions/<question_id>", methods=["DELETE"])
def delete_institution_question(question_id: uuid.UUID)-> Any:    
    payload = require_institution_admin()
    from flask import g
    db = getattr(g, "db", None)
    session = db
    """Delete a question from this institution's bank."""
    inst_id = _institution_id(payload)
    qid_str = str(question_id)

    try:
        result = session.execute(
            delete(Question).where(
                Question.id == question_id,
                Question.institution_id == inst_id,
            )
        )
        rows_affected = int(result.rowcount or 0)
        if rows_affected <= 0:
            session.rollback()
            return make_response(jsonify({"deleted": False, "error": "not_found", "id": qid_str}), 404)
        session.commit()
    except SQLAlchemyError as exc:
        session.rollback()
        logger.warning("DELETE /content/questions/%s failed: %s", qid_str, exc)
        return make_response(jsonify({"deleted": False, "error": type(exc).__name__, "id": qid_str}), 500)
    return {"deleted": True, "id": qid_str}


# ---------------------------------------------------------------------------
# POST /content/exams  (institution-scoped exam creation)
# ---------------------------------------------------------------------------

@router.route("/content/exams", methods=["POST"])
def create_institution_exam()-> Any:    
    payload = require_institution_admin()
    from flask import g, request, jsonify, make_response
    db = getattr(g, "db", None)
    session = db
    
    inst_id = _institution_id(payload)

    if not check_subscription_active(session, inst_id):
        raise HTTPException(
            status_code=403,
            detail={
                "error": "subscription_inactive",
                "message": "Institution subscription must be active to create exams.",
            },
        )

    body = request.get_json(silent=True) or {}
    subject_raw = body.get("subject") or request.args.get("subject")
    exam_name = body.get("exam_name") or request.args.get("exam_name") or "Weekly Test"
    batch_id_raw = body.get("batch_id")
    duration_minutes = int(body.get("duration_minutes") or 60)
    total_marks = int(body.get("total_marks") or 60)
    scheduled_start_str = body.get("scheduled_start")
    scheduled_end_str = body.get("scheduled_end")
    is_published = body.get("is_published", True)
    question_count = int(body.get("question_count") or 40)

    selected = _normalise_subject(subject_raw)
    if selected is None:
        return _validation_error(
            f"subject is required and must be one of {[s.value for s in Subject]}",
            field="subject",
        )

    # Parse batch_id
    batch_id = None
    if batch_id_raw and str(batch_id_raw).strip() not in ("", "all", "null"):
        try:
            batch_id = uuid.UUID(str(batch_id_raw))
        except Exception:
            batch_id = None

    # Parse dates
    from datetime import datetime
    scheduled_start = None
    if scheduled_start_str:
        try:
            scheduled_start = datetime.fromisoformat(scheduled_start_str.replace("Z", "+00:00"))
        except Exception:
            scheduled_start = None
            
    scheduled_end = None
    if scheduled_end_str:
        try:
            scheduled_end = datetime.fromisoformat(scheduled_end_str.replace("Z", "+00:00"))
        except Exception:
            scheduled_end = None

    # STRICT NO-REPEAT RULE: Query questions ALREADY used in previous exams for this subject & institution
    from ..rag.mcq_extractor import normalize_question_fingerprint, apply_subject_subtype_breakdown, interleave_by_subtype, infer_question_subtype, shuffle_question_options

    used_q_rows = session.execute(
        select(Question.id, Question.question_text)
        .join(ExamSetQuestion, Question.id == ExamSetQuestion.question_id)
        .join(ExamSet, ExamSetQuestion.exam_set_id == ExamSet.id)
        .join(Exam, ExamSet.exam_id == Exam.id)
        .where(Exam.subject == selected.value, Exam.institution_id == inst_id)
    ).all()
    used_qids = {r[0] for r in used_q_rows}
    used_q_fingerprints = {normalize_question_fingerprint(r[1]) for r in used_q_rows if r[1]}

    # Count institution-scoped extracted questions (strictly from user uploads for this institution)
    query_filters = [
        Question.subject == selected.value,
        Question.institution_id == inst_id,
        func.length(Question.question_text) <= 220,
    ]
    if batch_id:
        query_filters.append(Question.generation_batch_id == batch_id)

    id_rows = session.execute(
        select(Question.id, Question.question_text).where(*query_filters)
    ).all()

    # Exclude any questions that were already assigned to previous exams or duplicated by fingerprint
    unused_ids = []
    seen_fingerprints = set(used_q_fingerprints)
    for qid, qtext in id_rows:
        fp = normalize_question_fingerprint(qtext)
        if qid not in used_qids and fp and fp not in seen_fingerprints:
            unused_ids.append(qid)
            seen_fingerprints.add(fp)

    num_sets = len(SET_LABELS)
    target_per_set = max(1, question_count)
    total_needed = target_per_set

    # If available unused questions are less than total_needed, generate fresh non-repeating questions
    if len(unused_ids) < total_needed:
        needed = total_needed - len(unused_ids)
        context_text = ""
        try:
            matched_chunks = stores.search(selected, selected.value, k=40)
            if matched_chunks:
                context_text = "\n\n".join(matched_chunks)
        except Exception:
            pass

        fresh_mcqs = extract_or_generate_mcqs(context_text, topic=selected.value, min_questions=needed + 15, used_questions=seen_fingerprints)
        gen_batch_id = uuid.uuid4()
        for mcq in fresh_mcqs:
            q_text = mcq.get("q", "").strip()
            fp = normalize_question_fingerprint(q_text)
            if not q_text or not fp or fp in seen_fingerprints:
                continue
            opts = mcq.get("opts", [])
            ans = mcq.get("ans", 0)
            if not isinstance(opts, list) or len(opts) != 4:
                continue
            shuffled_opts, new_ans = shuffle_question_options(opts, ans)
            row = Question(
                subject=selected.value,
                question_text=q_text,
                options=shuffled_opts,
                correct_option=str(new_ans),
                topic=mcq.get("topic", selected.value),
                generation_batch_id=gen_batch_id,
                institution_id=inst_id,
                source_type="textbook",
                explanation=mcq.get("exp", f"Solution derived from uploaded {selected.value} material."),
            )
            session.add(row)
            session.flush()
            unused_ids.append(row.id)
            used_qids.add(row.id)
            seen_fingerprints.add(fp)

    if len(unused_ids) < total_needed:
        return make_response(jsonify({
            "error": "insufficient_questions",
            "subject": selected.value,
            "count": len(unused_ids),
            "required": total_needed,
            "message": f"Not enough unused questions available for {selected.value}. Please upload more question papers or textbooks first."
        }), 422)

    # Load candidate Question objects
    candidate_objects = session.execute(
        select(Question).where(Question.id.in_(unused_ids))
    ).scalars().all()

    # Convert to dicts with subtype inference
    candidate_dicts = [
        {
            "id": q.id,
            "q": q.question_text,
            "opts": q.options,
            "subtype": infer_question_subtype(q.question_text, q.options or [], selected.value),
            "topic": q.topic or "General"
        }
        for q in candidate_objects
    ]

    # Enforce KCET Blueprint Subtype Variety Breakdown (e.g. Physics: 35% Formula, 18% Multi-step, 47% Theory)
    balanced_pool = apply_subject_subtype_breakdown(candidate_dicts, selected.value, target_per_set)
    if len(balanced_pool) < target_per_set:
        balanced_pool = candidate_dicts[:target_per_set]

    # Interleave by subtype so adjacent questions alternate in structure
    base_interleaved = interleave_by_subtype(balanced_pool)
    base_qids = [item["id"] for item in base_interleaved]

    # Standard KCET Model: All sets (Set A, B, C, D) contain the EXACT SAME pool of questions,
    # but shuffled into different order sequences across sets so same question number contains different questions.
    partitions = []
    for s_i in range(num_sets):
        set_qids = list(base_qids)
        if s_i > 0:
            random.shuffle(set_qids)
            if set_qids == base_qids and len(set_qids) > 1:
                set_qids.reverse()
        partitions.append(set_qids)

    exam = Exam(
        subject=selected.value,
        exam_name=exam_name,
        institution_id=inst_id,
        batch_id=batch_id,
        duration_minutes=duration_minutes,
        total_marks=total_marks,
        scheduled_start=scheduled_start,
        scheduled_end=scheduled_end,
        is_published=is_published,
    )
    session.add(exam)

    try:
        session.flush()
        sets_payload = []
        for label, qids in zip(SET_LABELS, partitions):
            exam_set = ExamSet(exam_id=exam.id, set_label=label)
            session.add(exam_set)
            session.flush()
            session.add_all([
                ExamSetQuestion(exam_set_id=exam_set.id, question_id=qid, order_index=i)
                for i, qid in enumerate(qids)
            ])
            sets_payload.append({
                "label": label,
                "exam_set_id": str(exam_set.id),
                "question_count": len(qids),
            })
        session.commit()
    except (SQLAlchemyError, Exception) as exc:
        session.rollback()
        logger.warning("POST /institution/content/exams failed: %s", exc)
        return make_response(jsonify({"error": "exam_creation_failed", "message": str(exc)}), 500)

    created_at = exam.created_at
    batch_name = exam.batch.name if getattr(exam, "batch", None) else "All Batches"
    return jsonify({
        "exam_id": str(exam.id),
        "institution_id": str(inst_id),
        "subject": selected.value,
        "exam_name": exam.exam_name,
        "batch_id": str(batch_id) if batch_id else None,
        "batch_name": batch_name,
        "duration_minutes": exam.duration_minutes,
        "total_marks": exam.total_marks,
        "is_published": exam.is_published,
        "set_ids": sets_payload,
        "created_at": created_at.isoformat() if created_at else None,
    }), 201


# ---------------------------------------------------------------------------
# GET /content/exams  (list institution exams)
# ---------------------------------------------------------------------------

@router.route("/content/exams", methods=["GET"])
def list_institution_exams()-> Any:    
    payload = require_institution_admin()
    from flask import g, request, jsonify
    db = getattr(g, "db", None)
    session = db
    subject = request.args.get("subject", None)
    inst_id = _institution_id(payload)

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
            return _validation_error(
                f"subject must be one of {[s.value for s in Subject]}",
                field="subject",
            )
        stmt = stmt.where(Exam.subject == selected.value)

    rows = session.execute(stmt).all()
    exams_payload = []
    for exam, set_count in rows:
        sub_count = (
            session.query(func.count(Submission.id))
            .join(ExamSet, Submission.exam_set_id == ExamSet.id)
            .filter(ExamSet.exam_id == exam.id)
            .scalar() or 0
        )
        exams_payload.append({
            "exam_id": str(exam.id),
            "subject": exam.subject,
            "exam_name": exam.exam_name,
            "batch_id": str(exam.batch_id) if exam.batch_id else None,
            "batch_name": exam.batch.name if getattr(exam, "batch", None) else "All Batches",
            "duration_minutes": getattr(exam, "duration_minutes", 60) or 60,
            "total_marks": getattr(exam, "total_marks", 60) or 60,
            "scheduled_start": exam.scheduled_start.isoformat() if getattr(exam, "scheduled_start", None) else None,
            "scheduled_end": exam.scheduled_end.isoformat() if getattr(exam, "scheduled_end", None) else None,
            "created_at": exam.created_at.isoformat() if exam.created_at else None,
            "is_published": bool(exam.is_published),
            "set_count": int(set_count or 0),
            "completion_count": int(sub_count),
        })

    return {
        "institution_id": str(inst_id),
        "exams": exams_payload,
        "subject": selected.value if selected else None,
        "total": len(exams_payload),
    }


# ---------------------------------------------------------------------------
# PATCH /content/exams/{exam_id}  (publish / unpublish / update)
# ---------------------------------------------------------------------------

@router.route("/content/exams/<exam_id>", methods=["PATCH"])
def patch_institution_exam(exam_id: str)-> Any:    
    payload = require_institution_admin()
    from flask import g, request, jsonify, make_response
    db = getattr(g, "db", None)
    session = db
    inst_id = _institution_id(payload)

    body = request.get_json(silent=True) or {}
    try:
        e_uuid = uuid.UUID(exam_id)
    except ValueError:
        return make_response(jsonify({"error": "invalid_id", "message": "Invalid exam ID"}), 400)

    exam = session.get(Exam, e_uuid)
    if exam is None or exam.institution_id != inst_id:
        return make_response(jsonify({"error": "not_found", "exam_id": str(exam_id)}), 404)

    if "is_published" in body:
        exam.is_published = bool(body["is_published"])
    if "batch_id" in body:
        b_raw = body["batch_id"]
        exam.batch_id = uuid.UUID(b_raw) if b_raw and str(b_raw).strip() not in ("", "all", "null") else None
    if "exam_name" in body and body["exam_name"]:
        exam.exam_name = str(body["exam_name"]).strip()

    try:
        session.commit()
    except SQLAlchemyError as exc:
        session.rollback()
        return make_response(jsonify({"error": "update_failed", "message": str(exc)}), 500)

    return jsonify({"exam_id": str(exam.id), "is_published": exam.is_published, "message": "Exam updated"})


# ---------------------------------------------------------------------------
# DELETE /content/exams/{exam_id}
# ---------------------------------------------------------------------------

@router.route("/content/exams/<exam_id>", methods=["DELETE"])
def delete_institution_exam(exam_id: str)-> Any:    
    payload = require_institution_admin()
    from flask import g, jsonify, make_response
    db = getattr(g, "db", None)
    session = db
    inst_id = _institution_id(payload)

    try:
        e_uuid = uuid.UUID(exam_id)
    except ValueError:
        return make_response(jsonify({"error": "invalid_id", "message": "Invalid exam ID"}), 400)

    exam = session.get(Exam, e_uuid)
    if exam is None or exam.institution_id != inst_id:
        return make_response(jsonify({"error": "not_found", "exam_id": str(exam_id)}), 404)

    try:
        session.delete(exam)
        session.commit()
    except SQLAlchemyError as exc:
        session.rollback()
        return make_response(jsonify({"error": "delete_failed", "message": str(exc)}), 500)

    return jsonify({"success": True, "exam_id": str(e_uuid), "message": "Exam deleted successfully"})


# ---------------------------------------------------------------------------
# GET /content/exams/{exam_id}/questions  (view questions put in specific exam)
# ---------------------------------------------------------------------------

@router.route("/content/exams/<exam_id>/questions", methods=["GET"])
def get_institution_exam_questions(exam_id: str) -> Any:
    payload = require_institution_admin()
    from flask import g, jsonify, make_response
    session = getattr(g, "db", None)
    inst_id = _institution_id(payload)

    try:
        e_uuid = uuid.UUID(exam_id)
    except ValueError:
        return make_response(jsonify({"error": "invalid_id", "message": "Invalid exam ID"}), 400)

    exam = session.get(Exam, e_uuid)
    if exam is None or (exam.institution_id and exam.institution_id != inst_id):
        return make_response(jsonify({"error": "not_found", "message": "Exam not found"}), 404)

    sets = session.execute(
        select(ExamSet).where(ExamSet.exam_id == exam.id).order_by(ExamSet.set_label.asc())
    ).scalars().all()

    # Auto-heal / synchronize: Ensure Sets B, C, D contain the EXACT SAME pool of questions in shuffled order sequence
    if sets and len(sets) > 1:
        set_a = sets[0]
        set_a_qids = session.execute(
            select(ExamSetQuestion.question_id)
            .where(ExamSetQuestion.exam_set_id == set_a.id)
            .order_by(ExamSetQuestion.order_index.asc())
        ).scalars().all()

        if set_a_qids:
            from sqlalchemy import delete
            base_set = set(set_a_qids)
            base_list = list(set_a_qids)
            need_commit = False
            for es in sets[1:]:
                es_qids = session.execute(
                    select(ExamSetQuestion.question_id)
                    .where(ExamSetQuestion.exam_set_id == es.id)
                    .order_by(ExamSetQuestion.order_index.asc())
                ).scalars().all()

                if set(es_qids) != base_set or list(es_qids) == base_list:
                    session.execute(
                        delete(ExamSetQuestion).where(ExamSetQuestion.exam_set_id == es.id)
                    )
                    shuffled_qids = list(base_list)
                    random.shuffle(shuffled_qids)
                    if shuffled_qids == base_list and len(shuffled_qids) > 1:
                        shuffled_qids.reverse()
                    session.add_all([
                        ExamSetQuestion(exam_set_id=es.id, question_id=qid, order_index=idx)
                        for idx, qid in enumerate(shuffled_qids)
                    ])
                    need_commit = True
            if need_commit:
                session.commit()

    from ..rag.mcq_extractor import shuffle_options_for_set_label
    sets_data = []
    for es in sets:
        q_rows = session.execute(
            select(Question, ExamSetQuestion.order_index)
            .join(ExamSetQuestion, Question.id == ExamSetQuestion.question_id)
            .where(ExamSetQuestion.exam_set_id == es.id)
            .order_by(ExamSetQuestion.order_index.asc())
        ).all()

        questions = []
        for q, order in q_rows:
            shuffled_opts, new_ans = shuffle_options_for_set_label(q.options or [], q.correct_option, es.set_label)
            questions.append({
                "id": str(q.id),
                "order_index": order,
                "question_text": q.question_text,
                "options": shuffled_opts,
                "correct_option": str(new_ans),
                "topic": q.topic or "General",
                "explanation": q.explanation or ""
            })

        sets_data.append({
            "exam_set_id": str(es.id),
            "set_label": es.set_label,
            "question_count": len(questions),
            "questions": questions
        })

    return jsonify({
        "exam_id": str(exam.id),
        "exam_name": exam.exam_name,
        "subject": exam.subject,
        "duration_minutes": exam.duration_minutes,
        "total_marks": exam.total_marks,
        "sets": sets_data
    })


# ---------------------------------------------------------------------------
# GET /content/analytics  (institution student analytics)
# ---------------------------------------------------------------------------

@router.route("/content/analytics", methods=["GET"])
def get_institution_content_analytics()-> Any:    
    payload = require_institution_admin()
    from flask import g, request
    db = getattr(g, "db", None)
    session = db
    inst_id = _institution_id(payload)
    from ..db.models import InstitutionBatch

    batch_id_str = request.args.get("batch_id")
    batch_filter_id = None
    if batch_id_str and str(batch_id_str).lower() not in ("all", ""):
        try:
            batch_filter_id = uuid.UUID(batch_id_str)
        except Exception:
            batch_filter_id = None

    # Query students
    students_query = db.query(User).filter(User.institution_id == inst_id, User.role == "student")
    if batch_filter_id:
        students_query = students_query.filter(User.batch_id == batch_filter_id)
    students = students_query.all()
    student_ids = [s.id for s in students]

    all_batches = db.query(InstitutionBatch).filter(InstitutionBatch.institution_id == inst_id).order_by(InstitutionBatch.name.asc()).all()
    batches_data = [{"id": str(b.id), "name": b.name} for b in all_batches]

    if not student_ids:
        return {
            "institution_id": str(inst_id),
            "total_students": 0,
            "total_submissions": 0,
            "average_score": 0.0,
            "students": [],
            "batches": batches_data,
        }

    submissions = (
        db.query(Submission)
        .join(ExamSet, Submission.exam_set_id == ExamSet.id)
        .join(Exam, ExamSet.exam_id == Exam.id)
        .filter(
            Submission.user_id.in_(student_ids),
            Exam.institution_id == inst_id,
        )
        .all()
    )

    total_submissions = len(submissions)
    average_score = (
        sum(s.score_pct for s in submissions) / total_submissions
        if total_submissions > 0
        else 0.0
    )

    student_analytics = []
    for student in students:
        student_subs = [s for s in submissions if s.user_id == student.id]
        avg = (
            sum(s.score_pct for s in student_subs) / len(student_subs)
            if student_subs
            else 0.0
        )
        student_analytics.append({
            "student_id": str(student.id),
            "display_name": student.display_name,
            "email": student.email,
            "batch_name": student.batch.name if getattr(student, "batch", None) else "Unassigned",
            "total_attempts": len(student_subs),
            "average_score": round(avg, 2),
        })

    student_analytics.sort(key=lambda x: x["average_score"], reverse=True)

    return {
        "institution_id": str(inst_id),
        "total_students": len(students),
        "total_submissions": total_submissions,
        "average_score": round(average_score, 2),
        "students": student_analytics,
        "batches": batches_data,
    }


__all__ = ["router"]


# ---------------------------------------------------------------------------
# GET /content/admin-questions — access admin KCET question bank (Premium gate)
# ---------------------------------------------------------------------------

@router.route("/content/admin-questions", methods=["GET"])
def get_admin_questions_for_institution()-> Any:    
    payload = require_institution_admin()
    from flask import g
    db = getattr(g, "db", None)
    session = db
    from flask import request
    subject = request.args.get("subject", None)
    from flask import request
    page = int(request.args.get("page", 1))
    
    payload = require_institution_admin()
    from flask import g
    db = getattr(g, "db", None)
    session = db
    from flask import request
    subject = request.args.get("subject", None)
    from flask import request
    page = int(request.args.get("page", 1))
    """Return platform-wide (admin) KCET questions for use in institution exams.

    This endpoint is gated by the 'admin_question_bank' feature flag.
    Only Premium-tier institutions can access the admin KCET question bank.
    Basic-tier institutions can only use their own uploaded questions.
    """
    inst_id = _institution_id(payload)

    # Feature gate — requires admin_question_bank flag in plan
    _require_feature(
        session, inst_id,
        FEATURE_ADMIN_QBANK,
        "Access to the admin KCET question bank",
    )

    base_filter = [Question.institution_id.is_(None)]  # platform-wide questions only
    if subject:
        selected = _normalise_subject(subject)
        if selected is None:
            return _validation_error(
                f"subject must be one of {[s.value for s in Subject]}", field="subject"
            )
        base_filter.append(Question.subject == selected.value)

    total = int(session.execute(
        select(func.count(Question.id)).where(*base_filter)
    ).scalar_one())

    rows = session.execute(
        select(Question)
        .where(*base_filter)
        .order_by(Question.created_at.desc(), Question.id.asc())
        .offset((page - 1) * PAGE_SIZE)
        .limit(PAGE_SIZE)
    ).scalars().all()

    return {
        "institution_id": str(inst_id),
        "source": "admin_kcet_bank",
        "questions": [_serialise_question(r) for r in rows],
        "total": total,
        "page": page,
        "page_size": PAGE_SIZE,
    }


# ---------------------------------------------------------------------------
# GET /content/feature-access — check which features this institution has
# ---------------------------------------------------------------------------

@router.route("/content/feature-access", methods=["GET"])
def get_feature_access()-> Any:    
    payload = require_institution_admin()
    from flask import g
    db = getattr(g, "db", None)
    session = db
    """Return the feature access matrix for this institution's current plan.

    Frontend uses this to show/hide UI elements (e.g., Admin Question Bank tab).
    """
    inst_id = _institution_id(payload)
    plan    = _get_active_plan(session, inst_id)
    flags   = plan.feature_flags if plan else {}

    features = [
        FEATURE_ADMIN_QBANK,
        FEATURE_UNLIMITED_UPLOADS,
        FEATURE_AI_ANALYTICS,
        FEATURE_ADVANCED_ANALYTICS,
    ]

    return {
        "institution_id": str(inst_id),
        "plan_name": plan.name if plan else "No plan",
        "has_active_subscription": plan is not None,
        "features": {f: _has_feature(plan, f) for f in features},
    }
