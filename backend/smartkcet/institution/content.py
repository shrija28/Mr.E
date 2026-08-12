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

import hashlib
import logging
import random
import uuid
from typing import Annotated, Any, List, Optional
from pydantic import BaseModel

from fastapi import APIRouter, Depends, File, Form, HTTPException, Path, Query, UploadFile, status
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

router = APIRouter()

# Limits (mirrors admin limits)
MAX_FILE_SIZE_MB = 20
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


def _get_active_plan(db: Session, institution_id: uuid.UUID) -> Optional[SubscriptionPlan]:
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


def _has_feature(plan: Optional[SubscriptionPlan], feature: str) -> bool:
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


def _require_feature(
    db: Session,
    institution_id: uuid.UUID,
    feature: str,
    feature_label: str = "This feature",
) -> None:
    """Raise 403 if institution's plan does not include the given feature flag."""
    plan = _get_active_plan(db, institution_id)
    if not _has_feature(plan, feature):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
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

# Exam creation constants (mirrors admin: 4 sets × 20 = 80)
SET_LABELS = ("A", "B", "C", "D")
QUESTIONS_PER_SET = 20
QUESTIONS_PER_EXAM = QUESTIONS_PER_SET * len(SET_LABELS)  # 80


# ---------------------------------------------------------------------------
# Auth dependency
# ---------------------------------------------------------------------------

def require_institution_admin(
    payload: Annotated[dict, Depends(require_authenticated)],
) -> dict:
    if payload.get("role") != "institution_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "forbidden", "message": "Institution admin access required"},
        )
    if "institution_id" not in payload:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "forbidden", "message": "Institution ID not found in token"},
        )
    return payload


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _institution_id(payload: dict) -> uuid.UUID:
    return uuid.UUID(payload["institution_id"])


def check_subscription_active(db: Session, institution_id: uuid.UUID) -> bool:
    # Bypass subscription check globally for institution uploads
    return True


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


def _extract_text(filename: str, content: bytes) -> Optional[str]:
    lowered = filename.lower()
    if lowered.endswith(".pdf"):
        return extract_text_from_pdf(content)
    if lowered.endswith(".docx"):
        return extract_text_from_docx(content)
    if lowered.endswith(".txt"):
        return extract_text_from_txt(content)
    return None


def _compute_file_hash(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _check_duplicate(
    db: Session, subject: str, file_hash: str, institution_id: uuid.UUID
) -> Optional[IndexedFile]:
    """Check if this institution already indexed this exact file for the subject."""
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


# ---------------------------------------------------------------------------
# POST /content/upload/single  (per-file progress, mirrors admin)
# ---------------------------------------------------------------------------

@router.post("/content/upload/single")
async def upload_single_file(
    subject: Optional[str] = Form(default=None),
    file_type: str = Form(default="question_paper"),
    file: UploadFile = File(...),
    payload: Annotated[dict, Depends(require_institution_admin)] = None,
    db: Session = Depends(get_session),
) -> Any:
    """Upload a single file and return per-file status for progress tracking."""
    inst_id = _institution_id(payload)

    if not check_subscription_active(db, inst_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
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
    content = await file.read()
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

@router.post("/content/upload")
async def upload_institution_content(
    subject: Optional[str] = Form(default=None),
    file_type: str = Form(default="question_paper"),
    files: List[UploadFile] = File(default_factory=list),
    payload: Annotated[dict, Depends(require_institution_admin)] = None,
    db: Session = Depends(get_session),
) -> Any:
    """Batch upload question papers to the institution's question bank."""
    inst_id = _institution_id(payload)

    if not check_subscription_active(db, inst_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
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
        content = await upload_file.read()
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

@router.get("/content/upload/files")
async def list_institution_indexed_files(
    subject: str = Query(...),
    payload: Annotated[dict, Depends(require_institution_admin)] = None,
    db: Session = Depends(get_session),
) -> Any:
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

@router.get("/content/questions/counts")
def get_question_counts(
    payload: Annotated[dict, Depends(require_institution_admin)] = None,
    session: Session = Depends(get_session),
) -> Any:
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

@router.get("/content/questions")
def list_institution_questions(
    subject: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    payload: Annotated[dict, Depends(require_institution_admin)] = None,
    session: Session = Depends(get_session),
) -> Any:
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

@router.delete("/content/questions/{question_id}")
def delete_institution_question(
    question_id: uuid.UUID = Path(...),
    payload: Annotated[dict, Depends(require_institution_admin)] = None,
    session: Session = Depends(get_session),
) -> Any:
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
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"deleted": False, "error": "not_found", "id": qid_str},
            )
        session.commit()
    except SQLAlchemyError as exc:
        session.rollback()
        logger.warning("DELETE /content/questions/%s failed: %s", qid_str, exc)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"deleted": False, "error": type(exc).__name__, "id": qid_str},
        )
    return {"deleted": True, "id": qid_str}


# ---------------------------------------------------------------------------
# POST /content/exams  (institution-scoped exam creation)
# ---------------------------------------------------------------------------

@router.post("/content/exams", status_code=status.HTTP_201_CREATED)
def create_institution_exam(
    subject: Optional[str] = Query(default=None),
    exam_name: Optional[str] = Query(default=None),
    payload: Annotated[dict, Depends(require_institution_admin)] = None,
    session: Session = Depends(get_session),
) -> Any:
    """Create an exam from this institution's question bank."""
    inst_id = _institution_id(payload)

    if not check_subscription_active(session, inst_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "subscription_inactive",
                "message": "Institution subscription must be active to create exams.",
            },
        )

    # Feature gate: Advanced exam creation requires Premium plan
    # Basic plan can create exams from institution's own question bank
    # Premium plan additionally allows using admin KCET question bank
    # (No explicit gate here since we always use institution's own bank)

    selected = _normalise_subject(subject)
    if selected is None:
        return _validation_error(
            f"subject is required and must be one of {[s.value for s in Subject]}",
            field="subject",
        )

    # Count institution-scoped questions
    available = int(session.execute(
        select(func.count(Question.id)).where(
            Question.subject == selected.value,
            Question.institution_id == inst_id,
        )
    ).scalar_one())

    # We need at least 4 questions to create 4 sets (A, B, C, D)
    if available < 4:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": "insufficient_questions",
                "subject": selected.value,
                "count": available,
                "required": 4,
                "message": (
                    f"Not enough questions in institution's {selected.value} bank. "
                    f"Found {available}, need at least 4. "
                    f"Please upload more question papers first."
                ),
            },
        )

    id_rows = session.execute(
        select(Question.id).where(
            Question.subject == selected.value,
            Question.institution_id == inst_id,
        )
    ).all()
    all_ids: list[uuid.UUID] = [row[0] for row in id_rows]

    # Dynamic scaling based on availability (up to QUESTIONS_PER_EXAM)
    exam_size = min(len(all_ids), QUESTIONS_PER_EXAM)
    
    # Ensure the exam size is perfectly divisible by the number of sets (4)
    num_sets = len(SET_LABELS)
    exam_size = exam_size - (exam_size % num_sets)
    questions_per_set = exam_size // num_sets

    if exam_size < 4:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": "insufficient_questions",
                "subject": selected.value,
                "count": len(all_ids),
                "required": 4,
                "message": "Not enough unique questions to form 4 sets."
            },
        )

    drawn = random.sample(all_ids, exam_size)
    partitions = [
        drawn[i * questions_per_set : (i + 1) * questions_per_set]
        for i in range(num_sets)
    ]

    exam = Exam(
        subject=selected.value,
        exam_name=exam_name,
        institution_id=inst_id,
    )
    session.add(exam)

    try:
        session.flush()
        sets_payload: list[dict[str, Any]] = []
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
                "question_count": QUESTIONS_PER_SET,
            })
        session.commit()
    except (SQLAlchemyError, Exception) as exc:
        session.rollback()
        logger.warning("POST /institution/content/exams failed: %s", exc)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": "exam_creation_failed", "message": str(exc)},
        )

    created_at = exam.created_at
    return {
        "exam_id": str(exam.id),
        "institution_id": str(inst_id),
        "subject": selected.value,
        "exam_name": exam.exam_name,
        "set_ids": sets_payload,
        "created_at": created_at.isoformat() if created_at else None,
    }


# ---------------------------------------------------------------------------
# GET /content/exams  (list institution exams)
# ---------------------------------------------------------------------------

@router.get("/content/exams")
def list_institution_exams(
    subject: Optional[str] = Query(default=None),
    payload: Annotated[dict, Depends(require_institution_admin)] = None,
    session: Session = Depends(get_session),
) -> Any:
    """List all exams created by this institution."""
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

    return {
        "institution_id": str(inst_id),
        "exams": exams_payload,
        "subject": selected.value if selected else None,
        "total": len(exams_payload),
    }


# ---------------------------------------------------------------------------
# PATCH /content/exams/{exam_id}  (publish / unpublish)
# ---------------------------------------------------------------------------

class PublishExamRequest(BaseModel):
    is_published: bool

@router.patch("/content/exams/{exam_id}")
def patch_institution_exam(
    payload_body: PublishExamRequest,
    exam_id: uuid.UUID = Path(...),
    payload: Annotated[dict, Depends(require_institution_admin)] = None,
    session: Session = Depends(get_session),
) -> Any:
    """Publish or unpublish an institution exam."""
    inst_id = _institution_id(payload)

    if payload_body.is_published is None:
        return _validation_error("is_published is required", field="is_published")

    exam = session.get(Exam, exam_id)
    if exam is None or exam.institution_id != inst_id:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"error": "not_found", "exam_id": str(exam_id)},
        )

    if exam.is_published != payload_body.is_published:
        exam.is_published = payload_body.is_published
        try:
            session.commit()
        except SQLAlchemyError as exc:
            session.rollback()
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"error": "update_failed", "message": str(exc)},
            )

    return {"exam_id": str(exam.id), "is_published": exam.is_published}


# ---------------------------------------------------------------------------
# GET /content/analytics  (institution student analytics)
# ---------------------------------------------------------------------------

@router.get("/content/analytics")
async def get_institution_content_analytics(
    payload: Annotated[dict, Depends(require_institution_admin)] = None,
    db: Session = Depends(get_session),
) -> Any:
    """Analytics for institution students on institution exams."""
    inst_id = _institution_id(payload)

    students = db.query(User).filter(User.institution_id == inst_id, User.role == "student").all()
    student_ids = [s.id for s in students]

    if not student_ids:
        return {
            "institution_id": str(inst_id),
            "total_students": 0,
            "total_submissions": 0,
            "average_score": 0.0,
            "students": [],
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
    }


__all__ = ["router"]


# ---------------------------------------------------------------------------
# GET /content/admin-questions — access admin KCET question bank (Premium gate)
# ---------------------------------------------------------------------------

@router.get("/content/admin-questions")
def get_admin_questions_for_institution(
    subject: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    payload: Annotated[dict, Depends(require_institution_admin)] = None,
    session: Session = Depends(get_session),
) -> Any:
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

@router.get("/content/feature-access")
def get_feature_access(
    payload: Annotated[dict, Depends(require_institution_admin)] = None,
    session: Session = Depends(get_session),
) -> Any:
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
