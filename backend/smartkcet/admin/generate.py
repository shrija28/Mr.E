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

    body_data = request.get_json(silent=True) or {}
    req_filenames = body_data.get("filenames")
    req_topics = body_data.get("topics")

    from ..rag.topic_matcher import get_uploaded_topics_for_subject, is_topic_matching, match_filename_to_topic, SUBJECT_CHAPTERS
    official_chapters = SUBJECT_CHAPTERS.get(subject_name, [])

    if req_topics and isinstance(req_topics, list) and len(req_topics) > 0:
        uploaded_topics = [t for t in req_topics if any(is_topic_matching(t, [ch]) for ch in official_chapters)]
    elif req_filenames and isinstance(req_filenames, list) and len(req_filenames) > 0:
        mapped = [match_filename_to_topic(fn, subject_name) for fn in req_filenames]
        uploaded_topics = [t for t in set(mapped) if any(is_topic_matching(t, [ch]) for ch in official_chapters)]
    else:
        uploaded_topics = get_uploaded_topics_for_subject(session, subject_name)
    logger.info("Subject %s has active uploaded topics: %s", subject_name, uploaded_topics)

    # Query all questions for this subject from the DB
    stmt = (
        select(Question)
        .where(Question.subject == subject_name)
    )
    db_questions = list(session.execute(stmt).scalars().all())

    # If uploaded topics exist, filter strictly to questions matching uploaded topics
    if uploaded_topics:
        all_questions = [q for q in db_questions if is_topic_matching(q.topic, uploaded_topics)]
        logger.info(
            "Filtered %d DB questions to %d matching uploaded topics for %s",
            len(db_questions),
            len(all_questions),
            subject_name,
        )
    else:
        all_questions = db_questions

    existing_texts = set(q.question_text for q in all_questions if q.question_text)

    # If fewer than 240 questions in DB, generate strictly from uploaded material & syllabus
    if len(all_questions) < required_total:
        needed = required_total - len(all_questions)
        from ..rag.mcq_extractor import extract_or_generate_mcqs, is_valid_question

        batch_id = uuid.uuid4()
        topup_mcqs = []

        if uploaded_topics:
            # Top up strictly across each uploaded topic so no topic is missed and zero unuploaded topics leak
            target_per_topic = (required_total + len(uploaded_topics) - 1) // len(uploaded_topics)
            for top in uploaded_topics:
                curr_topic_qs = sum(1 for q in all_questions if is_topic_matching(q.topic, [top]))
                shortfall = max(0, target_per_topic - curr_topic_qs)
                if shortfall > 0:
                    topic_mcqs = extract_or_generate_mcqs(
                        "",
                        topic=subject_name,
                        min_questions=shortfall,
                        used_questions=existing_texts,
                        allowed_topics=[top],
                    )
                    for mcq in topic_mcqs:
                        mcq["topic"] = top
                    topup_mcqs.extend(topic_mcqs)
                    for mcq in topic_mcqs:
                        existing_texts.add(mcq.get("q", "").strip())
        else:
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

            topup_mcqs = extract_or_generate_mcqs(
                context_text,
                topic=subject_name,
                min_questions=needed + 10,
                used_questions=existing_texts,
            )

        for mcq in topup_mcqs:
            q_text = mcq.get("q", "").strip()
            if not q_text:
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

    from ..rag.blueprint import calculate_chapter_quotas
    blueprint_quotas = calculate_chapter_quotas(
        subject_name,
        uploaded_topics if uploaded_topics else None,
        QUESTIONS_PER_SET,
    )

    # Partition questions into 4 non-overlapping sets of 60 questions each adhering to blueprint quotas
    sets_rows: list[list[Question]] = [[] for _ in range(len(SET_LABELS))]
    by_topic: dict[str, list[Question]] = {}
    topic_pool = uploaded_topics if uploaded_topics else list(blueprint_quotas.keys())

    for q in all_questions:
        assigned = None
        for ut in topic_pool:
            if is_topic_matching(q.topic, [ut]):
                assigned = ut
                break
        if not assigned:
            assigned = q.topic or "General"
        by_topic.setdefault(assigned, []).append(q)

    # Shuffle questions within each topic pool
    for top_name, top_qs in by_topic.items():
        random.shuffle(top_qs)

    # Allocate questions into each of the 4 sets strictly following official chapter quotas
    for s_idx in range(len(SET_LABELS)):
        for top_name, target_q in blueprint_quotas.items():
            t_list = by_topic.get(top_name, [])
            for _ in range(target_q):
                if t_list and len(sets_rows[s_idx]) < QUESTIONS_PER_SET:
                    sets_rows[s_idx].append(t_list.pop(0))

    # Fill any minor shortfalls from remaining questions
    placed_ids = set(id(q) for s in sets_rows for q in s)
    remaining = [q for q in all_questions if id(q) not in placed_ids]
    random.shuffle(remaining)
    for s in sets_rows:
        while len(s) < QUESTIONS_PER_SET and remaining:
            s.append(remaining.pop())

    batch_id = uuid.uuid4()
    sets: list[list[dict]] = []

    for i, label in enumerate(SET_LABELS):
        set_rows = sets_rows[i]
        random.shuffle(set_rows)  # Shuffle so topics interleave naturally
        set_questions = [
            _question_row_to_dict(row, label, idx)
            for idx, row in enumerate(set_rows)
        ]
        if uploaded_topics:
            set_questions = [q for q in set_questions if is_topic_matching(q.get("topic"), uploaded_topics)]
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
