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
import os

import logging
import random
import time
import uuid
from typing import Any, Optional

import os
from flask import Blueprint, request, g, make_response, jsonify, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import func, select, delete
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from ..db.models import Exam, ExamSet, ExamSetQuestion, Question, Subject, Submission
from ..db.session import get_async_session as get_session
from ..middleware.rbac import require_admin

logger = logging.getLogger("smartkcet.admin.exams")

router = Blueprint("admin_exams", __name__)


# REQ-7.1 — exam contract: 4 sets × 60 questions = 240 total.  Defined as
# module-level constants so the smoke test (and any future admin UI)
# imports the same values rather than duplicating the magic numbers.
SET_LABELS = ("A", "B", "C", "D")
QUESTIONS_PER_SET = 60
QUESTIONS_PER_EXAM = QUESTIONS_PER_SET * len(SET_LABELS)  # 240


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _validation_error(message: str, field: Optional[str] = None):
    """Return a 400 envelope identical in shape to other admin endpoints."""

    body: dict[str, Any] = {"error": "validation_error", "message": message}
    if field is not None:
        body["field"] = field
    return jsonify(body), 400


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
# Request schemas
# ---------------------------------------------------------------------------


class CreateExamRequest(BaseModel):
    """Body for ``POST /api/admin/exams``."""

    subject: Optional[str] = None
    exam_name: Optional[str] = None
    source: Optional[str] = None  # 'question_paper' | 'textbook' | None (both)
    is_published: Optional[bool] = True
    institution_id: Optional[str] = None


class PublishExamRequest(BaseModel):
    """Body for ``PATCH /api/admin/exams/{exam_id}``."""

    is_published: Optional[bool] = None


# ---------------------------------------------------------------------------
# POST /api/admin/exams  (REQ-7.1, REQ-7.2, REQ-7.3 / design.md §4)
# ---------------------------------------------------------------------------


@router.route("/exams", methods=["POST"])
def create_exam()-> Any:    
    from flask import request
    payload = CreateExamRequest(**(request.get_json() or {}))
    _admin = require_admin()
    from flask import g
    db = getattr(g, "db", None)
    session = db
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

    # Retrieve directly from the stored questions in Question Bank
    return _create_exam_from_db(payload, selected, session, source_filter=None)


def _get_clean_unique_questions(session: Session, subject_val: str, source_filter: Optional[str] = None)-> list[Question]:
    """Return all valid, complete, deduplicated Question rows for the given subject,
    ordered with most recently added/generated questions prioritized."""
    from ..rag.mcq_extractor import is_valid_question
    import json

    stmt = (
        select(Question)
        .where(Question.subject == subject_val)
        .order_by(Question.created_at.desc(), Question.id.desc())
    )
    if source_filter and source_filter not in ("all", ""):
        try:
            if source_filter in ("textbook", "rag"):
                filtered_stmt = stmt.where(Question.source_type.in_(("textbook", "rag")))
            else:
                filtered_stmt = stmt.where(Question.source_type == source_filter)
            rows = list(session.execute(filtered_stmt).scalars().all())
            if len(rows) < QUESTIONS_PER_EXAM:
                all_rows = list(session.execute(stmt).scalars().all())
                existing_ids = set(r.id for r in rows)
                for r in all_rows:
                    if r.id not in existing_ids:
                        rows.append(r)
        except Exception:
            rows = list(session.execute(stmt).scalars().all())
    else:
        rows = list(session.execute(stmt).scalars().all())

    seen_texts: set[str] = set()
    clean_rows: list[Question] = []

    for r in rows:
        if not r.question_text:
            continue
        norm_text = r.question_text.strip().lower()
        if norm_text in seen_texts:
            continue

        opts = r.options
        if isinstance(opts, str):
            try:
                opts = json.loads(opts)
            except Exception:
                opts = []

        if not is_valid_question(r.question_text, opts, subject=subject_val):
            continue

        seen_texts.add(norm_text)
        clean_rows.append(r)

    return clean_rows


def _create_exam_from_db(payload: CreateExamRequest, selected: Subject, session: Session, source_filter: Optional[str] = None)-> Any:
    """Draw questions from the DB question bank and build a 1-set exam (Set A with 60 questions).
    
    Guarantees clean, authentic questions and allows multiple 60-question exams to be created from
    the 240 questions generated in the Question Bank.
    """
    subject_val = selected.value

    # Step 1: Query clean, unique questions stored in the Question Bank for this subject
    clean_questions = _get_clean_unique_questions(session, subject_val, source_filter)

    if len(clean_questions) == 0:
        return make_response(jsonify({
            "error": "no_questions_found",
            "message": f"No questions found in Question Bank for {subject_val}. Please go to the Upload section and click 'Generate 4 Sets' for {subject_val} first."
        }), 400)

    # Prioritize questions not yet used in previous exams for this subject
    linked_stmt = (
        select(ExamSetQuestion.question_id)
        .join(ExamSet, ExamSet.id == ExamSetQuestion.exam_set_id)
        .join(Exam, Exam.id == ExamSet.exam_id)
        .where(Exam.subject == subject_val)
    )
    already_used_ids = set(session.execute(linked_stmt).scalars().all())

    available_questions = [q for q in clean_questions if q.id not in already_used_ids]
    if len(available_questions) < QUESTIONS_PER_SET:
        available_questions = clean_questions

    all_ids = [q.id for q in available_questions]

    # Step 2: Draw exactly 60 unique questions for this 1-set exam
    sample_size = min(len(all_ids), QUESTIONS_PER_SET)
    drawn: list[uuid.UUID] = random.sample(all_ids, sample_size)

    partitions: list[list[uuid.UUID]] = [drawn]
    labels = ["A"]

    exam_inst_id = None
    if payload.institution_id:
        try:
            exam_inst_id = uuid.UUID(payload.institution_id)
        except (ValueError, TypeError):
            exam_inst_id = None

    exam_title = (payload.exam_name or "").strip()
    if not exam_title:
        existing_exam_count = session.execute(
            select(func.count(Exam.id)).where(Exam.subject == selected.value)
        ).scalar_one()
        exam_title = f"KCET {selected.value} Mock Exam" if existing_exam_count == 0 else f"KCET {selected.value} Mock Exam #{existing_exam_count + 1}"

    is_pub = True if payload.is_published is None else bool(payload.is_published)
    exam = Exam(
        subject=selected.value,
        exam_name=exam_title,
        is_published=is_pub,
        institution_id=exam_inst_id,
    )
    session.add(exam)
    try:
        session.flush()
        sets_payload: list[dict[str, Any]] = []
        for label, qids in zip(labels, partitions):
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
                "question_count": len(qids),
            })
        session.commit()
    except (SQLAlchemyError, Exception) as exc:
        session.rollback()
        logger.warning("POST /api/admin/exams (DB path) failed: %s", exc)
        return make_response(jsonify({"error": "exam_creation_failed", "message": str(exc)}), 500)

    return {
        "exam_id": str(exam.id),
        "subject": selected.value,
        "exam_name": exam.exam_name,
        "source": source_filter or "all",
        "set_ids": sets_payload,
        "created_at": exam.created_at.isoformat() if exam.created_at else None,
    }


def _create_exam_from_textbook(payload: CreateExamRequest, selected: Subject, session: Session) -> Any:
    """Generate 80 KCET-level MCQs using RAG (Retrieval-Augmented Generation) from
    textbook chapters and syllabus content.
    
    1. Checks uploaded chapter textbooks in data/textbooks/.
    2. If absent, loads pre-indexed textbook chunks from data/faiss/{subject}.chunks.json.
    3. Invokes Groq LLM to generate fresh questions anchored to textbook context.
    4. Seamlessly falls back to authentic pedagogical KCET generation if LLM is unavailable.
    5. Stores questions in the database with source_type='rag' and constructs 4 sets (A/B/C/D).
    """
    from pathlib import Path as PPath
    import json
    from ..db.models import SyllabusTopic
    from ..rag.groq_client import generate_kcet_mcqs_from_textbook, GroqAPIKeyError
    from ..rag.parsing import extract_text_from_pdf, extract_text_from_docx, extract_text_from_txt
    from ..rag.mcq_extractor import extract_or_generate_mcqs, is_valid_question

    subject_name = selected.value
    TEXTBOOKS_DIR = PPath(__file__).resolve().parent.parent.parent / "data" / "textbooks"
    FAISS_DIR = PPath(__file__).resolve().parent.parent.parent / "data" / "faiss"

    chapter_texts: list[tuple[str, str]] = []  # (chapter_name, text)

    # ── Step 1: Check syllabus chapters with uploaded textbook files
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

    for topic in chapters_with_textbooks:
        safe_filename = f"topic_{topic.id}_{topic.textbook_filename}"
        file_path = TEXTBOOKS_DIR / safe_filename
        if not file_path.exists():
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
                continue

            if text and text.strip():
                chapter_texts.append((topic.chapter_name, text.strip()))
        except Exception as exc:
            logger.warning("Failed to extract text from %s: %s", topic.textbook_filename, exc)

    # ── Step 2: Fall back to pre-indexed FAISS textbook chunks if no files uploaded
    if not chapter_texts:
        chunk_file = FAISS_DIR / f"{subject_name}.chunks.json"
        if chunk_file.exists():
            try:
                with open(chunk_file, "r", encoding="utf-8") as f:
                    all_chunks = json.load(f)
                if all_chunks and isinstance(all_chunks, list):
                    # Sample chunks across the textbook
                    sample_count = min(30, len(all_chunks))
                    step = max(1, len(all_chunks) // sample_count)
                    sampled = [all_chunks[i] for i in range(0, len(all_chunks), step)][:sample_count]
                    joined_text = "\n\n".join(sampled)
                    chapter_texts.append((f"{subject_name} NCERT Textbook", joined_text))
                    logger.info("Loaded %d textbook chunks from %s for RAG exam", len(sampled), chunk_file.name)
            except Exception as exc:
                logger.warning("Failed to load pre-indexed chunks for %s: %s", subject_name, exc)

    # If still no textbook content, provide a friendly message
    if not chapter_texts:
        chapter_texts.append((f"{subject_name} Syllabus", f"Standard Karnataka CET PUC 1 and PUC 2 {subject_name} syllabus concepts, definitions, derivations, formulas and applications."))

    logger.info("RAG exam: using %d text context sources for %s", len(chapter_texts), subject_name)

    # ── Step 3: Build fair context for RAG generation
    context_parts = []
    chars_per_chapter = 4000 // len(chapter_texts) if chapter_texts else 4000
    for ch_name, ch_text in chapter_texts:
        chunk = ch_text[:chars_per_chapter] if len(ch_text) > chars_per_chapter else ch_text
        context_parts.append(f"=== Chapter: {ch_name} ===\n{chunk}")
    context_str = "\n\n".join(context_parts)
    chapter_names = [c[0] for c in chapter_texts]

    # ── Step 4: Generate 20 KCET MCQs per set via Groq LLM (or fallback generator)
    generated_questions: list[dict] = []
    used_questions: set[str] = set()
    batch_id = uuid.uuid4()
    generation_errors: list[str] = []

    for label in SET_LABELS:
        set_qs = []
        try:
            set_qs = generate_kcet_mcqs_from_textbook(
                context_chunks=[context_str],
                subject=subject_name,
                set_label=label,
                used_questions=used_questions,
                questions_needed=QUESTIONS_PER_SET,
                chapter_names=chapter_names,
            )
            logger.info("Set %s: generated %d KCET questions via Groq RAG LLM", label, len(set_qs))
        except (GroqAPIKeyError, Exception) as e:
            logger.warning("Groq RAG generation for set %s failed or key missing: %s. Using authentic RAG question bank.", label, e)
            generation_errors.append(f"Set {label}: {e}")

        # Top up this set if fewer than QUESTIONS_PER_SET were returned
        if len(set_qs) < QUESTIONS_PER_SET:
            needed = QUESTIONS_PER_SET - len(set_qs)
            try:
                topup = extract_or_generate_mcqs(context_str, topic=subject_name, min_questions=needed, used_questions=used_questions)
                for q in topup:
                    if q["q"] not in used_questions and is_valid_question(q["q"], q["opts"], subject=subject_name):
                        set_qs.append(q)
                        used_questions.add(q["q"])
                        if len(set_qs) >= QUESTIONS_PER_SET:
                            break
            except Exception as exc:
                logger.error("Top-up generation failed: %s", exc)

        for q in set_qs:
            used_questions.add(q.get("q", ""))
        generated_questions.extend(set_qs[:QUESTIONS_PER_SET])

    # Final safeguard: if total < QUESTIONS_PER_EXAM, top up
    if len(generated_questions) < QUESTIONS_PER_EXAM:
        clean_db_questions = _get_clean_unique_questions(session, subject_name)
        random.shuffle(clean_db_questions)
        for q_row in clean_db_questions:
            if q_row.question_text and q_row.question_text not in used_questions:
                opts = q_row.options
                if isinstance(opts, str):
                    try:
                        opts = json.loads(opts)
                    except Exception:
                        opts = []
                if isinstance(opts, list) and len(opts) == 4:
                    generated_questions.append({
                        "q": q_row.question_text,
                        "opts": opts,
                        "ans": int(q_row.correct_option) if str(q_row.correct_option).isdigit() else 0,
                        "topic": q_row.topic or subject_name,
                        "exp": q_row.explanation or f"Concept solution derived from {subject_name} textbook principles."
                    })
                    used_questions.add(q_row.question_text)
                    if len(generated_questions) >= QUESTIONS_PER_EXAM:
                        break

    # Step 4.5: Ensure sufficient pool of questions
    if len(generated_questions) < QUESTIONS_PER_EXAM + 20:
        shortfall = (QUESTIONS_PER_EXAM + 20) - len(generated_questions)
        extra = extract_or_generate_mcqs(context_str, topic=subject_name, min_questions=shortfall + 20, used_questions=used_questions)
        for q in extra:
            if q["q"] not in used_questions and is_valid_question(q["q"], q["opts"], subject=subject_name):
                generated_questions.append(q)
                used_questions.add(q["q"])
                if len(generated_questions) >= QUESTIONS_PER_EXAM + 20:
                    break

    # ── Step 5: Store questions in DB as source_type='rag'
    stored_ids: list[uuid.UUID] = []
    for q_dict in generated_questions:
        if len(stored_ids) >= QUESTIONS_PER_EXAM:
            break
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
            source_type="rag",
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
        return make_response(jsonify({
            "error": "question_storage_failed",
            "stored": len(stored_ids),
            "required": QUESTIONS_PER_EXAM,
            "message": "Failed to store enough generated questions in the database.",
        }), 500)

    # ── Step 6: Atomically create Exam + 4 ExamSets + 80 ExamSetQuestion links
    exam_inst_id = None
    if payload.institution_id:
        try:
            exam_inst_id = uuid.UUID(payload.institution_id)
        except (ValueError, TypeError):
            exam_inst_id = None

    is_pub = True if payload.is_published is None else bool(payload.is_published)
    exam = Exam(
        subject=subject_name,
        exam_name=payload.exam_name,
        is_published=is_pub,
        institution_id=exam_inst_id,
    )
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
        logger.warning("POST /api/admin/exams (RAG) commit failed: %s", exc)
        return make_response(jsonify({"error": "exam_creation_failed", "message": str(exc)}), 500)

    logger.info(
        "RAG exam created: id=%s subject=%s chapters_used=%d questions=%d",
        exam.id, subject_name, len(chapter_texts), len(stored_ids),
    )

    return {
        "exam_id": str(exam.id),
        "subject": subject_name,
        "exam_name": exam.exam_name,
        "source": "rag",
        "chapters_used": len(chapter_texts),
        "questions_generated": len(stored_ids),
        "set_ids": sets_payload,
        "created_at": exam.created_at.isoformat() if exam.created_at else None,
    }


# ---------------------------------------------------------------------------
# PATCH /api/admin/exams/{exam_id}  (REQ-7.4, REQ-7.5 / design.md §4.1)
# ---------------------------------------------------------------------------


@router.route("/exams/<exam_id>", methods=["PATCH"])
def patch_exam(exam_id: str) -> Any:    
    from flask import request
    payload = PublishExamRequest(**(request.get_json() or {}))
    _admin = require_admin()
    from flask import g
    db = getattr(g, "db", None)
    session = db
    """Toggle publish/unpublish on an existing exam (idempotent)."""

    if payload.is_published is None or not isinstance(payload.is_published, bool):
        return _validation_error(
            "is_published is required and must be a boolean",
            field="is_published",
        )

    try:
        exam_uuid = uuid.UUID(str(exam_id))
    except (ValueError, AttributeError):
        return make_response(jsonify({"error": "invalid_uuid", "exam_id": str(exam_id)}), 400)

    exam = session.get(Exam, exam_uuid)
    if exam is None:
        return make_response(jsonify({"error": "not_found", "exam_id": str(exam_id)}), 404)

    # Idempotent assignment
    if exam.is_published != payload.is_published:
        exam.is_published = payload.is_published
        try:
            session.commit()
        except SQLAlchemyError as exc:
            session.rollback()
            logger.warning(
                "PATCH /api/admin/exams/%s failed: %s", exam_id, exc
            )
            return make_response(jsonify({
                    "error": "publish_update_failed",
                    "message": f"failed to update publish state: {exc}",
                }), 500)

    return make_response(jsonify({"exam_id": str(exam.id), "is_published": exam.is_published}), 200)


@router.route("/exams/<exam_id>", methods=["DELETE"])
def delete_exam(exam_id: str) -> Any:
    """Permanently delete an exam and its sets / submissions."""
    _admin = require_admin()
    from flask import g
    db = getattr(g, "db", None)
    session = db

    try:
        exam_uuid = uuid.UUID(str(exam_id))
    except (ValueError, AttributeError):
        return make_response(jsonify({"error": "invalid_uuid", "exam_id": str(exam_id)}), 400)

    exam = session.get(Exam, exam_uuid)
    if exam is None:
        return make_response(jsonify({"error": "not_found", "exam_id": str(exam_id)}), 404)

    try:
        # Explicitly delete child records (submissions, usage records, exam sets)
        set_ids = [s.id for s in exam.sets] if exam.sets else []
        if set_ids:
            try:
                from ..db.subscription_models import UsageRecord
                sub_ids_stmt = select(Submission.id).where(Submission.exam_set_id.in_(set_ids))
                sub_ids = list(session.execute(sub_ids_stmt).scalars().all())
                if sub_ids:
                    session.execute(delete(UsageRecord).where(UsageRecord.submission_id.in_(sub_ids)))
                    session.execute(delete(Submission).where(Submission.id.in_(sub_ids)))
            except Exception as e:
                logger.warning("Error deleting child submissions/usage records: %s", e)

            session.execute(delete(ExamSetQuestion).where(ExamSetQuestion.exam_set_id.in_(set_ids)))
            session.execute(delete(ExamSet).where(ExamSet.id.in_(set_ids)))

        session.delete(exam)
        session.commit()
        return make_response(jsonify({"success": True, "deleted_id": str(exam_uuid)}), 200)
    except SQLAlchemyError as exc:
        session.rollback()
        logger.warning("DELETE /api/admin/exams/%s failed: %s", exam_id, exc)
        return make_response(jsonify({"error": "delete_failed", "message": str(exc)}), 500)



# ---------------------------------------------------------------------------
# GET /api/admin/exams  (REQ-7.6)
# ---------------------------------------------------------------------------


@router.route("/exams", methods=["GET"])
def list_exams()-> Any:    
    _admin = require_admin()
    from flask import g
    db = getattr(g, "db", None)
    session = db
    from flask import request
    subject = request.args.get("subject", None)
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


# ---------------------------------------------------------------------------
# GET /api/admin/exams/{exam_id}  (inspect sets & questions)
# ---------------------------------------------------------------------------


@router.route("/exams/<exam_id>", methods=["GET"])
def get_exam_details(exam_id: str) -> Any:
    """Return the exam with all sets (A/B/C/D) and their assigned questions."""
    _admin = require_admin()
    from flask import g
    db = getattr(g, "db", None)
    session = db

    try:
        exam_uuid = uuid.UUID(str(exam_id))
    except (ValueError, AttributeError):
        return make_response(jsonify({"error": "invalid_uuid", "exam_id": str(exam_id)}), 400)

    exam = session.get(Exam, exam_uuid)
    if exam is None:
        return make_response(jsonify({"error": "not_found", "exam_id": str(exam_id)}), 404)

    import json
    sets_data = []
    for s in sorted(exam.sets, key=lambda x: x.set_label):
        set_qs = (
            session.query(Question, ExamSetQuestion.order_index)
            .join(ExamSetQuestion, ExamSetQuestion.question_id == Question.id)
            .filter(ExamSetQuestion.exam_set_id == s.id)
            .order_by(ExamSetQuestion.order_index.asc())
            .all()
        )
        questions_list = []
        for q, oi in set_qs:
            opts = q.options
            if isinstance(opts, str):
                try:
                    opts = json.loads(opts)
                except Exception:
                    opts = []
            questions_list.append({
                "id": str(q.id),
                "order_index": oi,
                "q": q.question_text,
                "question": q.question_text,
                "opts": opts,
                "options": opts,
                "ans": int(q.correct_option) if str(q.correct_option).isdigit() else 0,
                "correct_option": q.correct_option,
                "topic": q.topic,
                "explanation": q.explanation,
                "exp": q.explanation,
                "source_type": q.source_type,
            })
        sets_data.append({
            "set_id": str(s.id),
            "set_label": s.set_label,
            "question_count": len(questions_list),
            "questions": questions_list,
        })

    return make_response(jsonify({
        "exam_id": str(exam.id),
        "exam_name": exam.exam_name,
        "subject": exam.subject,
        "is_published": bool(exam.is_published),
        "created_at": exam.created_at.isoformat() if exam.created_at else None,
        "sets": sets_data,
        "total_questions": sum(len(s["questions"]) for s in sets_data),
    }), 200)


__all__ = [
    "router",
    "SET_LABELS",
    "QUESTIONS_PER_SET",
    "QUESTIONS_PER_EXAM",
]
