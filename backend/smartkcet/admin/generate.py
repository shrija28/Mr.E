"""Admin question-generation endpoint — DB-driven question bank.

Generates 4 paper sets (A/B/C/D) by querying the questions table for the
selected subject and randomly partitioning available questions into
non-overlapping sets.

No external API calls are made. Questions come entirely from the DB,
populated during the upload phase via the MCQ extractor.

NOTE: Groq can be re-enabled as an optional enhancement later if needed.
The import is kept but not used in the current flow.

Response shape on success::

    {
        "success": True,
        "added": 80,
        "batch_id": "<uuid>",
        "subject": "Biology",
        "sets": [
            [{"id": "A-0", "q": "...", "type": "MCQ", "topic": "...", "opts": [...], "ans": 0, "marks": 1}, ...],
            [...],
            [...],
            [...]
        ]
    }
"""

from __future__ import annotations
import os

import random
import uuid
import logging
from typing import Any, Optional

import os
from flask import Blueprint, request, g, make_response, jsonify, Response
from fastapi.responses import JSONResponse
from sqlalchemy import select, func as sa_func
from sqlalchemy.orm import Session

from ..db.models import Question, Subject
from ..db.session import get_async_session as get_session
from ..middleware.rbac import require_admin
from ..rag.store import stores

# NOTE: Groq import kept for potential future re-enablement as an optional
# enhancement (e.g., AI-powered question generation when DB is empty).
# Currently NOT used in the generation flow.
# from ..rag import groq_client as groq_module
# from ..rag.groq_client import GroqAPIKeyError

logger = logging.getLogger("smartkcet.admin.generate")

router = Blueprint("admin_generate", __name__)


# Generation contract: 4 sets, up to 60 questions each = up to 240 total.
SET_LABELS = ("A", "B", "C", "D")
QUESTIONS_PER_SET = 60
MIN_TOTAL_QUESTIONS = 20  # Minimum to generate any sets at all


def _validation_error(message: str, field: Optional[str] = None):
    """Return a 400 JSON envelope identical in shape to the upload endpoint."""

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


def _read_subject(req=None)-> Optional[str]:
    """Extract the subject field from JSON, form-data, or query parameters in Flask."""
    from flask import request as flask_req
    r = req or flask_req

    try:
        data = r.get_json(silent=True)
        if isinstance(data, dict) and data.get("subject"):
            return str(data["subject"]).strip()
    except Exception:
        pass

    try:
        if r.form and "subject" in r.form:
            return str(r.form.get("subject")).strip()
    except Exception:
        pass

    try:
        if r.args and "subject" in r.args:
            return str(r.args.get("subject")).strip()
    except Exception:
        pass

    return None


def _question_row_to_dict(row: Question, set_label: str, index: int)-> dict:
    """Convert a Question ORM row to the frontend-expected dict format."""
    opts = row.options
    if isinstance(opts, str):
        try:
            import json
            opts = json.loads(opts)
        except Exception:
            opts = []
    if not isinstance(opts, list):
        opts = []

    return {
        "id": f"{set_label}-{index}",
        "q": row.question_text,
        "type": "MCQ",
        "topic": row.topic or "General",
        "opts": opts,
        "ans": int(row.correct_option) if str(row.correct_option).isdigit() else 0,
        "marks": 1,
        "exp": row.explanation or "",
    }


@router.route("/generate", methods=["POST"])
def generate()-> Any:    
    _admin = require_admin()
    from flask import g
    db = getattr(g, "db", None)
    session = db
    """Generate 4 paper sets (60 questions per set = 240 total unique questions)
    from the question bank for the chosen subject with zero overlap across sets.
    """

    raw_subject = _read_subject(request)
    selected = _normalise_subject(raw_subject)
    if selected is None:
        allowed = [s.value for s in Subject]
        return _validation_error(
            f"subject is required and must be one of {allowed}",
            field="subject",
        )

    subject_name = selected.value
    required_total = len(SET_LABELS) * QUESTIONS_PER_SET  # 4 * 60 = 240

    # Query all questions for this subject from the DB
    stmt = (
        select(Question)
        .where(Question.subject == subject_name)
    )
    all_questions = list(session.execute(stmt).scalars().all())
    existing_texts = set(q.question_text for q in all_questions if q.question_text)

    # If fewer than 240 questions in DB, generate from uploaded material & syllabus
    if len(all_questions) < required_total:
        needed = required_total - len(all_questions)
        from ..rag.mcq_extractor import extract_or_generate_mcqs, is_valid_question

        # Extract text context from uploaded textbook chunks for this subject
        context_text = ""
        try:
            chunks_path = stores._chunks_path(selected)
            if chunks_path.exists():
                import json
                with open(chunks_path, "r", encoding="utf-8") as cf:
                    chunks = json.load(cf)
                if chunks and isinstance(chunks, list) and len(chunks) > 0:
                    sample_size = min(30, len(chunks))
                    sample_chunks = chunks[:sample_size] if len(chunks) <= sample_size else random.sample(chunks, sample_size)
                    context_text = "\n\n".join(sample_chunks)
                    logger.info("Loaded %d uploaded chunks from %s for generation context", len(sample_chunks), chunks_path.name)
        except Exception as e:
            logger.warning("Could not read uploaded chunks for context: %s", e)

        topup_mcqs = extract_or_generate_mcqs(context_text, topic=subject_name, min_questions=needed + 10, used_questions=existing_texts)
        batch_id = uuid.uuid4()
        for mcq in topup_mcqs:
            q_text = mcq.get("q", "").strip()
            if not q_text or q_text in existing_texts:
                continue
            if not is_valid_question(q_text, mcq.get("opts", []), subject=subject_name):
                continue
            row = Question(
                subject=subject_name,
                question_text=q_text,
                options=mcq.get("opts", []),
                correct_option=str(mcq.get("ans", 0)),
                topic=mcq.get("topic", subject_name),
                generation_batch_id=batch_id,
                institution_id=None,
                source_type="textbook",
                explanation=mcq.get("exp", f"Solution based on {subject_name} NCERT syllabus."),
            )
            session.add(row)
            all_questions.append(row)
            existing_texts.add(q_text)

        try:
            session.commit()
            logger.info("Committed %d generated questions for %s into Question Bank", len(topup_mcqs), subject_name)
        except Exception as exc:
            session.rollback()
            logger.warning("Failed to commit generated questions in generate: %s", exc)

    total_available = len(all_questions)
    logger.info(
        "Generate request for %s: %d questions available",
        subject_name,
        total_available,
    )

    # Deduplicate strictly by question_text
    seen_texts = set()
    distinct_questions = []
    for q in all_questions:
        txt = (q.question_text or "").strip()
        if txt and txt not in seen_texts:
            seen_texts.add(txt)
            distinct_questions.append(q)
    all_questions = distinct_questions

    # Shuffle questions randomly
    random.shuffle(all_questions)

    # Partition questions into 4 non-overlapping sets of 60 questions each
    batch_id = uuid.uuid4()
    sets: list[list[dict]] = []

    for i, label in enumerate(SET_LABELS):
        start = i * QUESTIONS_PER_SET
        end = start + QUESTIONS_PER_SET
        set_rows = all_questions[start:end]

        set_questions = [
            _question_row_to_dict(row, label, idx)
            for idx, row in enumerate(set_rows)
        ]
        sets.append(set_questions)

    total_added = sum(len(s) for s in sets)

    logger.info(
        "Generated %d unique questions across 4 distinct sets for %s",
        total_added,
        subject_name,
    )

    return {
        "success": True,
        "added": total_added,
        "batch_id": str(batch_id),
        "subject": subject_name,
        "sets": sets,
    }


__all__ = ["router", "SET_LABELS", "QUESTIONS_PER_SET"]
