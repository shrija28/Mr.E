"""Admin exam-authoring endpoints using Flask Blueprint."""

from __future__ import annotations

import logging
import random
import time
import uuid
from typing import Any, Optional
from pathlib import Path as PPath

from flask import Blueprint, jsonify, request
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from ..db.models import Exam, ExamSet, ExamSetQuestion, Question, Subject, SyllabusTopic
from ..db.session import get_db
from ..middleware.rbac import require_admin

logger = logging.getLogger("smartkcet.admin.exams")

router = Blueprint("admin_exams", __name__, url_prefix="/api/admin")

SET_LABELS = ("A", "B", "C", "D")
QUESTIONS_PER_SET = 20
QUESTIONS_PER_EXAM = QUESTIONS_PER_SET * len(SET_LABELS)


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


def _get_clean_unique_questions(session: Session, subject_val: str, source_filter: Optional[str] = None) -> list[Question]:
    from ..rag.mcq_extractor import is_valid_question
    import json

    stmt = select(Question).where(Question.subject == subject_val)
    if source_filter:
        try:
            filtered_stmt = stmt.where(Question.source_type == source_filter)
            rows = list(session.execute(filtered_stmt).scalars().all())
            if len(rows) < QUESTIONS_PER_EXAM:
                rows = list(session.execute(stmt).scalars().all())
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


def _create_exam_from_db(
    subject_str: str,
    exam_name: Optional[str],
    selected: Subject,
    session: Session,
    source_filter: Optional[str],
):
    subject_val = selected.value
    clean_questions = _get_clean_unique_questions(session, subject_val, source_filter)

    if len(clean_questions) < QUESTIONS_PER_EXAM:
        needed = QUESTIONS_PER_EXAM - len(clean_questions)
        logger.info("Question bank for %s has %d clean questions; auto-generating %d top-up questions...", subject_val, len(clean_questions), needed)
        try:
            from ..rag.mcq_extractor import extract_or_generate_mcqs
            additional_mcqs = extract_or_generate_mcqs("", topic=subject_val, min_questions=needed)
            mcq_batch_id = uuid.uuid4()
            for mcq in additional_mcqs:
                q_row = Question(
                    subject=subject_val,
                    question_text=mcq["q"],
                    options=mcq["opts"],
                    correct_option=str(mcq["ans"]),
                    topic=mcq.get("topic", "General"),
                    explanation=mcq.get("exp", ""),
                    generation_batch_id=mcq_batch_id,
                    source_type="generated_kcet",
                    institution_id=None,
                )
                session.add(q_row)
            session.commit()
            clean_questions = _get_clean_unique_questions(session, subject_val, source_filter)
        except Exception as exc:
            logger.warning("Failed to auto top-up questions for %s: %s", subject_val, exc)
            session.rollback()

    all_ids = [q.id for q in clean_questions]
    sample_size = min(len(all_ids), QUESTIONS_PER_EXAM)
    drawn: list[uuid.UUID] = random.sample(all_ids, sample_size)

    num_sets = len(SET_LABELS)
    questions_per_set = max(1, sample_size // num_sets)

    partitions: list[list[uuid.UUID]] = [
        drawn[i * questions_per_set : (i + 1) * questions_per_set]
        for i in range(num_sets)
    ]

    exam = Exam(subject=selected.value, exam_name=exam_name)
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
                "question_count": len(qids),
            })
        session.commit()
    except (SQLAlchemyError, Exception) as exc:
        session.rollback()
        logger.warning("POST /api/admin/exams (DB path) failed: %s", exc)
        return jsonify({"error": "exam_creation_failed", "message": str(exc)}), 500

    return jsonify({
        "exam_id": str(exam.id),
        "subject": selected.value,
        "exam_name": exam.exam_name,
        "source": source_filter or "all",
        "set_ids": sets_payload,
        "created_at": exam.created_at.isoformat() if exam.created_at else None,
    }), 201


def _create_exam_from_textbook(
    exam_name: Optional[str],
    selected: Subject,
    session: Session,
):
    from ..rag.groq_client import generate_kcet_mcqs_from_textbook, GroqAPIKeyError
    from ..rag.parsing import extract_text_from_pdf, extract_text_from_docx, extract_text_from_txt

    subject_name = selected.value
    TEXTBOOKS_DIR = PPath(__file__).resolve().parent.parent.parent / "data" / "textbooks"

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
        return jsonify({
            "error": "no_textbook_content",
            "subject": subject_name,
            "message": f"No textbooks uploaded for {subject_name} chapters.",
        }), 422

    chapter_texts: list[tuple[str, str]] = []

    for topic in chapters_with_textbooks:
        safe_filename = f"topic_{topic.id}_{topic.textbook_filename}"
        file_path = TEXTBOOKS_DIR / safe_filename

        if not file_path.exists():
            continue

        try:
            raw = file_path.read_bytes()
            fn = topic.textbook_filename.lower()
            text = None
            if fn.endswith(".pdf"):
                text = extract_text_from_pdf(raw)
            elif fn.endswith(".docx") or fn.endswith(".doc"):
                text = extract_text_from_docx(raw)
            elif fn.endswith(".txt"):
                text = extract_text_from_txt(raw)

            if text and text.strip():
                chapter_texts.append((topic.chapter_name, text.strip()))
        except Exception as exc:
            logger.warning("Failed to extract text from %s: %s", topic.textbook_filename, exc)

    if not chapter_texts:
        return jsonify({
            "error": "text_extraction_failed",
            "subject": subject_name,
            "message": f"Could not extract text from any {subject_name} textbook files.",
        }), 422

    generated_questions: list[dict] = []
    used_questions: set[str] = set()
    batch_id = uuid.uuid4()
    generation_errors: list[str] = []

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
        except GroqAPIKeyError as e:
            return jsonify({"error": "groq_api_key_error", "message": str(e)}), 503
        except Exception as e:
            logger.error("Textbook generation set %s failed: %s", label, e)
            generation_errors.append(f"Set {label}: {e}")

    if len(generated_questions) < QUESTIONS_PER_EXAM:
        return jsonify({
            "error": "generation_incomplete",
            "generated": len(generated_questions),
            "required": QUESTIONS_PER_EXAM,
            "errors": generation_errors,
            "message": f"Only generated {len(generated_questions)}/{QUESTIONS_PER_EXAM} questions.",
        }), 500

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
        return jsonify({
            "error": "question_storage_failed",
            "stored": len(stored_ids),
            "required": QUESTIONS_PER_EXAM,
            "message": "Failed to store enough generated questions in the database.",
        }), 500

    exam = Exam(subject=subject_name, exam_name=exam_name)
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
        return jsonify({"error": "exam_creation_failed", "message": str(exc)}), 500

    return jsonify({
        "exam_id": str(exam.id),
        "subject": subject_name,
        "exam_name": exam.exam_name,
        "source": "textbook",
        "chapters_used": len(chapter_texts),
        "questions_generated": len(stored_ids),
        "set_ids": sets_payload,
        "created_at": exam.created_at.isoformat() if exam.created_at else None,
    }), 201


@router.route("/exams", methods=["POST"])
@require_admin
def create_exam():
    session: Session = get_db()
    data = request.get_json(silent=True) or {}
    raw_subject = data.get("subject")
    exam_name = data.get("exam_name")
    source = data.get("source")

    selected = _normalise_subject(raw_subject)
    if selected is None:
        allowed = [s.value for s in Subject]
        return _validation_error(f"subject is required and must be one of {allowed}", field="subject")

    if source == "textbook":
        return _create_exam_from_textbook(exam_name, selected, session)

    return _create_exam_from_db(raw_subject, exam_name, selected, session, source_filter=source)


@router.route("/exams/<exam_id>", methods=["PATCH"])
@require_admin
def patch_exam(exam_id: str):
    session: Session = get_db()
    data = request.get_json(silent=True) or {}
    is_published = data.get("is_published")

    if is_published is None or not isinstance(is_published, bool):
        return _validation_error("is_published is required and must be a boolean", field="is_published")

    try:
        eid = uuid.UUID(exam_id)
    except (ValueError, TypeError):
        return jsonify({"error": "validation_error", "message": "Invalid exam_id"}), 400

    exam = session.get(Exam, eid)
    if exam is None:
        return jsonify({"error": "not_found", "exam_id": exam_id}), 404

    if exam.is_published != is_published:
        exam.is_published = is_published
        try:
            session.commit()
        except SQLAlchemyError as exc:
            session.rollback()
            return jsonify({"error": "publish_update_failed", "message": f"failed to update publish state: {exc}"}), 500

    return jsonify({"exam_id": str(exam.id), "is_published": exam.is_published}), 200


@router.route("/exams", methods=["GET"])
@require_admin
def list_exams():
    session: Session = get_db()
    subject = request.args.get("subject")

    selected: Optional[Subject] = None
    if subject is not None:
        normalised = _normalise_subject(subject)
        if normalised is None:
            allowed = [s.value for s in Subject]
            return _validation_error(f"subject must be one of {allowed}", field="subject")
        selected = normalised

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

    return jsonify({
        "exams": exams_payload,
        "subject": selected.value if selected is not None else None,
        "total": len(exams_payload),
    }), 200


__all__ = ["router", "SET_LABELS", "QUESTIONS_PER_SET", "QUESTIONS_PER_EXAM"]
