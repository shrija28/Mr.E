"""Admin exam-authoring endpoints.

Implements task 7.1, 7.3 / REQ-7.1 ... REQ-7.6 and the admin-side
contract documented in design.md §4 (atomic exam creation), §4.1
(publish/unpublish) and §4.2 (student exam-selection visibility — the
read side that this module powers via ``GET /api/admin/exams``).

* Mounted under ``/api/admin/exams`` from :mod:`smartkcet.admin`.
* Every endpoint is admin-only — guarded by
  :func:`smartkcet.middleware.rbac.require_admin`.
* The 400 envelope shape (``{error, message[, field]}``) mirrors
  :mod:`.upload`, :mod:`.generate`, and :mod:`.questions` so the admin
  UI can handle validation failures uniformly.

Endpoints
---------

``POST /api/admin/exams``
    Atomic exam creation (REQ-7.1, REQ-7.2, REQ-7.3 / design.md §4).
    Counts the requested subject's questions; aborts with 422 when the
    bank holds fewer than :data:`QUESTIONS_PER_EXAM` (80) rows.  On
    sufficient stock it draws 80 random questions, partitions them into
    4 disjoint sets of 20 labelled A/B/C/D, and inserts the exam + 4
    sets + 80 set-question rows in a single SQL transaction.  Any
    failure at any of those three steps triggers ``ROLLBACK`` so no
    partial exam record persists.

``PATCH /api/admin/exams/{exam_id}``
    Idempotent publish/unpublish toggle (REQ-7.4, REQ-7.5 / design.md
    §4.1).  The ``exams.is_published`` column is the single source of
    truth for new student attempts; in-progress submissions on a
    now-unpublished exam are left untouched per design.md §4.1.

``GET /api/admin/exams``
    List all exams with subject, creation date, published status, and
    set count (REQ-7.6).  Optional ``?subject=Biology`` filter.  Sorted
    by ``created_at DESC`` so the freshly created exam shows first.
"""

from __future__ import annotations

import logging
import random
import time
import uuid
from typing import Any, Optional

from fastapi import APIRouter, Depends, Path, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from ..db.models import Exam, ExamSet, ExamSetQuestion, Question, Subject
from ..db.session import get_async_session as get_session
from ..middleware.rbac import require_admin

logger = logging.getLogger("smartkcet.admin.exams")

router = APIRouter()


# REQ-7.1 — exam contract: 4 sets × 20 questions = 80 total.  Defined as
# module-level constants so the smoke test (and any future admin UI)
# imports the same values rather than duplicating the magic numbers.
SET_LABELS = ("A", "B", "C", "D")
QUESTIONS_PER_SET = 20
QUESTIONS_PER_EXAM = QUESTIONS_PER_SET * len(SET_LABELS)  # 80


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _validation_error(message: str, field: Optional[str] = None) -> JSONResponse:
    """Return a 400 envelope identical in shape to other admin endpoints."""

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
# Request schemas
# ---------------------------------------------------------------------------


class CreateExamRequest(BaseModel):
    """Body for ``POST /api/admin/exams``."""

    subject: Optional[str] = None
    exam_name: Optional[str] = None
    source: Optional[str] = None  # 'question_paper' | 'textbook' | None (both)


class PublishExamRequest(BaseModel):
    """Body for ``PATCH /api/admin/exams/{exam_id}``."""

    is_published: Optional[bool] = None


# ---------------------------------------------------------------------------
# POST /api/admin/exams  (REQ-7.1, REQ-7.2, REQ-7.3 / design.md §4)
# ---------------------------------------------------------------------------


@router.post("/exams", status_code=status.HTTP_201_CREATED)
def create_exam(
    payload: CreateExamRequest,
    session: Session = Depends(get_session),
    _admin: dict = Depends(require_admin),
) -> Any:
    """Create one exam (1 row + 4 sets + 80 set-question links) atomically.

    Supports two question sources:
    - ``source='question_paper'``: draws from DB questions extracted from PYQ uploads
    - ``source='textbook'``: generates fresh KCET-level MCQs live from textbook
      chunks stored in the FAISS index via Groq LLM
    - ``source=None``: draws from all questions in DB regardless of source

    For 'textbook' source the flow is:
    1. Pull all FAISS chunks for the subject (textbook content)
    2. Call Groq 4 times (once per set A/B/C/D) with 20 questions each
    3. Store the 80 generated questions in the DB as source_type='textbook'
    4. Create the exam + sets + links pointing at the newly stored questions
    """

    selected = _normalise_subject(payload.subject)
    if selected is None:
        allowed = [s.value for s in Subject]
        return _validation_error(
            f"subject is required and must be one of {allowed}",
            field="subject",
        )

    source = payload.source  # 'question_paper' | 'textbook' | None

    # ── Textbook path: generate fresh questions from FAISS + Groq ──────────
    if source == "textbook":
        return _create_exam_from_textbook(payload, selected, session)

    # ── PYQ / DB path: draw from existing question bank ─────────────────────
    return _create_exam_from_db(payload, selected, session, source_filter=source)


def _create_exam_from_db(
    payload: CreateExamRequest,
    selected: Subject,
    session: Session,
    source_filter: Optional[str],
) -> Any:
    """Draw 80 random questions from the DB question bank and build an exam."""

    # Step 1: count available questions
    # Note: source_type filter is applied only when explicitly requested.
    # If source_type column doesn't exist yet on some rows, fall back gracefully.
    count_stmt = select(func.count(Question.id)).where(
        Question.subject == selected.value
    )
    if source_filter:
        try:
            count_stmt = count_stmt.where(Question.source_type == source_filter)
        except Exception:
            pass  # Column may not exist on older DB — ignore filter

    available = int(session.execute(count_stmt).scalar_one())
    if available < QUESTIONS_PER_EXAM:
        source_label = "previous year papers" if source_filter == "question_paper" else "question bank"
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": "insufficient_questions",
                "subject": selected.value,
                "count": available,
                "required": QUESTIONS_PER_EXAM,
                "source": source_filter or "all",
                "message": (
                    f"Not enough questions from {source_label} for {selected.value}. "
                    f"Found {available}, need {QUESTIONS_PER_EXAM}. "
                    f"Please upload more {'question papers' if source_filter == 'question_paper' else 'files'} first."
                ),
            },
        )

    # Step 2: random draw of 80 question IDs
    id_stmt = select(Question.id).where(Question.subject == selected.value)
    if source_filter:
        try:
            id_stmt = id_stmt.where(Question.source_type == source_filter)
        except Exception:
            pass

    id_rows = session.execute(id_stmt).all()
    all_ids: list[uuid.UUID] = [row[0] for row in id_rows]

    if len(all_ids) < QUESTIONS_PER_EXAM:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": "insufficient_questions",
                "subject": selected.value,
                "count": len(all_ids),
                "required": QUESTIONS_PER_EXAM,
                "source": source_filter or "all",
            },
        )

    drawn: list[uuid.UUID] = random.sample(all_ids, QUESTIONS_PER_EXAM)

    # Step 3: partition into 4 sets and insert atomically
    partitions: list[list[uuid.UUID]] = [
        drawn[i * QUESTIONS_PER_SET : (i + 1) * QUESTIONS_PER_SET]
        for i in range(len(SET_LABELS))
    ]

    exam = Exam(subject=selected.value, exam_name=payload.exam_name)
    session.add(exam)
    try:
        session.flush()
        sets_payload: list[dict[str, Any]] = []
        for label, qids in zip(SET_LABELS, partitions):
            exam_set = ExamSet(exam_id=exam.id, set_label=label)
            session.add(exam_set)
            session.flush()
            link_rows = [
                ExamSetQuestion(
                    exam_set_id=exam_set.id,
                    question_id=qid,
                    order_index=oi,
                )
                for oi, qid in enumerate(qids)
            ]
            session.add_all(link_rows)
            sets_payload.append({
                "label": label,
                "exam_set_id": str(exam_set.id),
                "question_count": QUESTIONS_PER_SET,
            })
        session.commit()
    except (SQLAlchemyError, Exception) as exc:
        session.rollback()
        logger.warning("POST /api/admin/exams (DB path) failed: %s", exc)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": "exam_creation_failed", "message": str(exc)},
        )

    return {
        "exam_id": str(exam.id),
        "subject": selected.value,
        "exam_name": exam.exam_name,
        "source": source_filter or "all",
        "set_ids": sets_payload,
        "created_at": exam.created_at.isoformat() if exam.created_at else None,
    }


def _create_exam_from_textbook(
    payload: CreateExamRequest,
    selected: Subject,
    session: Session,
) -> Any:
    """Generate 80 KCET-level MCQs by reading the actual textbook PDFs
    uploaded via the Syllabus page, extracting their text, and calling
    Groq 4 times (once per set A/B/C/D × 20 questions each).
    """
    from pathlib import Path as PPath
    from ..db.models import SyllabusTopic
    from ..rag.groq_client import generate_kcet_mcqs_from_textbook, GroqAPIKeyError
    from ..rag.parsing import extract_text_from_pdf, extract_text_from_docx, extract_text_from_txt
    from ..rag.store import stores as faiss_stores

    subject_name = selected.value

    TEXTBOOKS_DIR = PPath(__file__).resolve().parent.parent.parent / "data" / "textbooks"

    # ── Step 1: find all syllabus chapters for this subject that have a textbook
    stmt = (
        select(SyllabusTopic)
        .where(
            SyllabusTopic.subject == subject_name,
            SyllabusTopic.textbook_filename.isnot(None),
            SyllabusTopic.is_active.is_(True),
        )
        .order_by(SyllabusTopic.puc_year, SyllabusTopic.chapter_number)
    )
    chapters_with_textbooks = session.execute(stmt).scalars().all()

    if not chapters_with_textbooks:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": "no_textbook_content",
                "subject": subject_name,
                "message": (
                    f"No textbooks uploaded for {subject_name} chapters. "
                    "Go to Syllabus → Upload Textbooks and upload PDFs for each chapter first."
                ),
            },
        )

    logger.info(
        "Textbook exam: found %d chapters with textbooks for %s",
        len(chapters_with_textbooks), subject_name,
    )

    # ── Step 2: extract text from every textbook file
    # Group chapters into 4 even buckets (one per set A/B/C/D)
    chapter_texts: list[tuple[str, str]] = []  # (chapter_name, text)

    for topic in chapters_with_textbooks:
        # Build the on-disk filename: topic_{id}_{original_filename}
        safe_filename = f"topic_{topic.id}_{topic.textbook_filename}"
        file_path = TEXTBOOKS_DIR / safe_filename

        if not file_path.exists():
            logger.warning(
                "Textbook file not found on disk: %s (chapter: %s)",
                file_path, topic.chapter_name,
            )
            continue

        try:
            raw = file_path.read_bytes()
            fn = topic.textbook_filename.lower()
            if fn.endswith(".pdf"):
                text = extract_text_from_pdf(raw)
            elif fn.endswith(".docx") or fn.endswith(".doc"):
                text = extract_text_from_docx(raw)
            elif fn.endswith(".txt"):
                text = extract_text_from_txt(raw)
            else:
                logger.warning("Unsupported textbook format: %s", topic.textbook_filename)
                continue

            if text and text.strip():
                chapter_texts.append((topic.chapter_name, text.strip()))
                logger.info(
                    "Extracted %d chars from '%s' (chapter: %s)",
                    len(text), topic.textbook_filename, topic.chapter_name,
                )
        except Exception as exc:
            logger.warning(
                "Failed to extract text from %s: %s", topic.textbook_filename, exc
            )

    if not chapter_texts:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": "text_extraction_failed",
                "subject": subject_name,
                "message": (
                    f"Could not extract text from any {subject_name} textbook files. "
                    "Make sure the uploaded files are readable PDFs/DOCX/TXT."
                ),
            },
        )

    logger.info(
        "Textbook exam: extracted text from %d/%d chapter textbooks for %s",
        len(chapter_texts), len(chapters_with_textbooks), subject_name,
    )

    # ── Step 4: generate 20 KCET MCQs per set via Groq
    generated_questions: list[dict] = []
    used_questions: set[str] = set()
    batch_id = uuid.uuid4()
    generation_errors: list[str] = []

    # Calculate equal chunks for all chapters to build fair context
    context_parts = []
    if chapter_texts:
        chars_per_chapter = 3500 // len(chapter_texts)
        for ch_name, ch_text in chapter_texts:
            chunk = ch_text[:chars_per_chapter] if len(ch_text) > chars_per_chapter else ch_text
            context_parts.append(f"=== Chapter: {ch_name} ===\n{chunk}")

    context_str = "\n\n".join(context_parts)
    chapter_names = [c[0] for c in chapter_texts]

    for label in SET_LABELS:
        try:
            set_qs = generate_kcet_mcqs_from_textbook(
                context_chunks=[context_str],
                subject=subject_name,
                set_label=label,
                used_questions=used_questions,
                questions_needed=QUESTIONS_PER_SET,
                chapter_names=chapter_names,
            )
            generated_questions.extend(set_qs)
            logger.info(
                "Set %s: generated %d KCET questions from %d chapters",
                label, len(set_qs), len(chapter_texts),
            )
            
        except GroqAPIKeyError as e:
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={"error": "groq_api_key_error", "message": str(e)},
            )
        except Exception as e:
            logger.error("Textbook generation set %s failed: %s", label, e)
            generation_errors.append(f"Set {label}: {e}")

    if len(generated_questions) < QUESTIONS_PER_EXAM:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "generation_incomplete",
                "generated": len(generated_questions),
                "required": QUESTIONS_PER_EXAM,
                "errors": generation_errors,
                "message": (
                    f"Only generated {len(generated_questions)}/{QUESTIONS_PER_EXAM} questions. "
                    + (f"Errors: {'; '.join(generation_errors)}" if generation_errors else "")
                ),
            },
        )

    # ── Step 5: store the 80 generated questions in DB as source_type='textbook'
    stored_ids: list[uuid.UUID] = []
    for q_dict in generated_questions[:QUESTIONS_PER_EXAM]:
        opts = q_dict.get("opts", [])
        if not isinstance(opts, list) or len(opts) != 4:
            continue
        q_row = Question(
            subject=subject_name,
            question_text=q_dict.get("q", "").strip(),
            options=opts,
            correct_option=str(q_dict.get("ans", 0)),
            explanation=q_dict.get("exp", ""),
            topic=q_dict.get("topic", "General"),
            generation_batch_id=batch_id,
            institution_id=None,
            source_type="textbook",
        )
        session.add(q_row)
        try:
            session.flush()
            stored_ids.append(q_row.id)
        except Exception as exc:
            session.rollback()
            logger.warning("Failed to flush question: %s", exc)

    if len(stored_ids) < QUESTIONS_PER_EXAM:
        session.rollback()
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "question_storage_failed",
                "stored": len(stored_ids),
                "required": QUESTIONS_PER_EXAM,
                "message": "Failed to store enough generated questions in the database.",
            },
        )

    # ── Step 6: create Exam + 4 ExamSets + 80 ExamSetQuestion links atomically
    exam = Exam(subject=subject_name, exam_name=payload.exam_name)
    session.add(exam)
    try:
        session.flush()
        drawn = stored_ids[:QUESTIONS_PER_EXAM]
        partitions = [
            drawn[i * QUESTIONS_PER_SET : (i + 1) * QUESTIONS_PER_SET]
            for i in range(len(SET_LABELS))
        ]
        sets_payload: list[dict[str, Any]] = []
        for label, qids in zip(SET_LABELS, partitions):
            exam_set = ExamSet(exam_id=exam.id, set_label=label)
            session.add(exam_set)
            session.flush()
            session.add_all([
                ExamSetQuestion(exam_set_id=exam_set.id, question_id=qid, order_index=oi)
                for oi, qid in enumerate(qids)
            ])
            sets_payload.append({
                "label": label,
                "exam_set_id": str(exam_set.id),
                "question_count": QUESTIONS_PER_SET,
            })
        session.commit()
    except (SQLAlchemyError, Exception) as exc:
        session.rollback()
        logger.warning("POST /api/admin/exams (textbook) commit failed: %s", exc)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": "exam_creation_failed", "message": str(exc)},
        )

    logger.info(
        "Textbook exam created: id=%s subject=%s chapters_used=%d questions=%d",
        exam.id, subject_name, len(chapter_texts), len(stored_ids),
    )

    return {
        "exam_id": str(exam.id),
        "subject": subject_name,
        "exam_name": exam.exam_name,
        "source": "textbook",
        "chapters_used": len(chapter_texts),
        "questions_generated": len(stored_ids),
        "set_ids": sets_payload,
        "created_at": exam.created_at.isoformat() if exam.created_at else None,
    }


# ---------------------------------------------------------------------------
# PATCH /api/admin/exams/{exam_id}  (REQ-7.4, REQ-7.5 / design.md §4.1)
# ---------------------------------------------------------------------------


@router.patch("/exams/{exam_id}")
def patch_exam(
    payload: PublishExamRequest,
    exam_id: uuid.UUID = Path(...),
    session: Session = Depends(get_session),
    _admin: dict = Depends(require_admin),
) -> Any:
    """Toggle publish/unpublish on an existing exam (idempotent).

    REQ-7.4 / REQ-7.5 / design.md §4.1: ``exams.is_published`` is the
    single source of truth for student visibility of new attempts.
    Repeated publishes or unpublishes leave the column at the requested
    value without side effects on ``exam_sets`` or ``submissions``.

    In-progress submissions on a now-unpublished exam continue and
    persist normally — the column gates only new attempts.
    """

    if payload.is_published is None or not isinstance(payload.is_published, bool):
        return _validation_error(
            "is_published is required and must be a boolean",
            field="is_published",
        )

    exam = session.get(Exam, exam_id)
    if exam is None:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"error": "not_found", "exam_id": str(exam_id)},
        )

    # Idempotent assignment — if the column already holds the requested
    # value the UPDATE is a no-op but the response shape is unchanged.
    if exam.is_published != payload.is_published:
        exam.is_published = payload.is_published
        try:
            session.commit()
        except SQLAlchemyError as exc:
            session.rollback()
            logger.warning(
                "PATCH /api/admin/exams/%s failed: %s", exam_id, exc
            )
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": "publish_update_failed",
                    "message": f"failed to update publish state: {exc}",
                },
            )

    return {"exam_id": str(exam.id), "is_published": exam.is_published}


# ---------------------------------------------------------------------------
# GET /api/admin/exams  (REQ-7.6)
# ---------------------------------------------------------------------------


@router.get("/exams")
def list_exams(
    subject: Optional[str] = Query(default=None),
    session: Session = Depends(get_session),
    _admin: dict = Depends(require_admin),
) -> Any:
    """List all exams with subject, creation date, published status, set_count.

    REQ-7.6: the admin panel shows every exam regardless of publish
    status.  Optional ``?subject=Biology`` filter scopes the list to a
    single subject.  Sort order is ``created_at DESC`` so the freshly
    created exam appears at the top.
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

    # Compute set_count via a left join + group_by so we get one row per
    # exam even when an exam has zero sets (which should not happen post
    # task 7.1, but the join is defensive).
    stmt = (
        select(Exam, func.count(ExamSet.id).label("set_count"))
        .outerjoin(ExamSet, ExamSet.exam_id == Exam.id)
        .group_by(Exam.id)
        .order_by(Exam.created_at.desc(), Exam.id.asc())
    )
    if selected is not None:
        stmt = stmt.where(Exam.subject == selected.value)

    rows = session.execute(stmt).all()
    exams_payload: list[dict[str, Any]] = []
    for exam, set_count in rows:
        created_at = exam.created_at
        exams_payload.append(
            {
                "exam_id": str(exam.id),
                "subject": exam.subject,
                "exam_name": exam.exam_name,
                "created_at": created_at.isoformat() if created_at is not None else None,
                "is_published": bool(exam.is_published),
                "set_count": int(set_count or 0),
            }
        )

    return {
        "exams": exams_payload,
        "subject": selected.value if selected is not None else None,
        "total": len(exams_payload),
    }


__all__ = [
    "router",
    "SET_LABELS",
    "QUESTIONS_PER_SET",
    "QUESTIONS_PER_EXAM",
]
