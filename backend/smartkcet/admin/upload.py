"""Admin file-upload endpoint with per-subject FAISS indexing using Flask Blueprint."""

from __future__ import annotations

import hashlib
import logging
import uuid
from typing import Any, List, Optional

from flask import Blueprint, jsonify, request
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db.models import IndexedFile, Question, Subject
from ..db.session import get_db
from ..middleware.rbac import require_admin
from ..rag.mcq_extractor import extract_or_generate_mcqs

try:
    from ..rag.parsing import (
        chunk_text,
        extract_text_from_docx,
        extract_text_from_pdf,
        extract_text_from_txt,
    )
    PARSING_AVAILABLE = True
except ImportError as e:
    logger = logging.getLogger("smartkcet.admin.upload")
    logger.warning("RAG parsing module not available: %s", e)
    PARSING_AVAILABLE = False
    chunk_text = None
    extract_text_from_docx = None
    extract_text_from_pdf = None
    extract_text_from_txt = None

from ..rag.store import stores

logger = logging.getLogger("smartkcet.admin.upload")

router = Blueprint("admin_upload", __name__, url_prefix="/api/admin")

MAX_FILES_PER_BATCH = 10


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


def _check_duplicate(db: Session, subject: str, file_hash: str) -> Optional[IndexedFile]:
    stmt = select(IndexedFile).where(
        IndexedFile.subject == subject,
        IndexedFile.file_hash == file_hash,
        IndexedFile.institution_id.is_(None),
    )
    return db.execute(stmt).scalar_one_or_none()


def _record_indexed_file(
    db: Session,
    subject: str,
    filename: str,
    file_hash: str,
    file_size: int,
    chunk_count: int,
    file_type: str = "question_paper",
) -> IndexedFile:
    record = IndexedFile(
        subject=subject,
        filename=filename,
        file_hash=file_hash,
        file_size=file_size,
        chunk_count=chunk_count,
        file_type=file_type,
        institution_id=None,
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
    source_type: str = "question_paper",
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
            institution_id=None,
            source_type=source_type,
            explanation=mcq.get("exp", ""),
        )
        db.add(row)
        stored += 1

    if stored > 0:
        try:
            db.commit()
        except Exception as exc:
            logger.warning("Failed to commit MCQs to DB: %s", exc)
            db.rollback()
            return 0

    return stored


@router.route("/upload/files", methods=["GET"])
@require_admin
def list_indexed_files():
    db: Session = get_db()
    subject = request.args.get("subject")
    selected = _normalise_subject(subject)
    if selected is None:
        allowed = [s.value for s in Subject]
        return _validation_error(f"subject is required and must be one of {allowed}", field="subject")

    stmt = (
        select(IndexedFile)
        .where(IndexedFile.subject == selected.value, IndexedFile.institution_id.is_(None))
        .order_by(IndexedFile.indexed_at.desc())
    )
    files = db.execute(stmt).scalars().all()

    return jsonify({
        "subject": selected.value,
        "files": [
            {
                "id": str(f.id),
                "filename": f.filename,
                "file_hash": f.file_hash,
                "file_size": f.file_size,
                "chunk_count": f.chunk_count,
                "file_type": f.file_type,
                "indexed_at": f.indexed_at.isoformat() if f.indexed_at else None,
            }
            for f in files
        ],
    }), 200


@router.route("/upload/single", methods=["POST"])
@require_admin
def upload_single():
    db: Session = get_db()
    subject = request.form.get("subject")
    file_type = request.form.get("file_type", "question_paper")
    file = request.files.get("file")

    if not file:
        return _validation_error("file is required", field="file")

    selected = _normalise_subject(subject)
    if selected is None:
        allowed = [s.value for s in Subject]
        return _validation_error(f"subject is required and must be one of {allowed}", field="subject")

    filename = file.filename or ""
    content = file.read()
    file_size = len(content)
    file_hash = _compute_file_hash(content)

    existing = _check_duplicate(db, selected.value, file_hash)
    if existing is not None:
        return jsonify({
            "status": "duplicate",
            "filename": filename,
            "file_hash": file_hash,
            "file_size": file_size,
            "chunk_count": existing.chunk_count,
            "message": f"File already indexed as '{existing.filename}' with {existing.chunk_count} chunks",
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
        return jsonify({
            "status": "empty",
            "filename": filename,
            "file_hash": file_hash,
            "file_size": file_size,
            "chunk_count": 0,
            "message": "No text could be extracted from this file",
        }), 200

    chunks = chunk_text(text) if chunk_text else [text]
    if not chunks:
        return jsonify({
            "status": "empty",
            "filename": filename,
            "file_hash": file_hash,
            "file_size": file_size,
            "chunk_count": 0,
            "message": "Text too short to produce meaningful chunks",
        }), 200

    if stores:
        stores.add(selected, chunks)

    _record_indexed_file(
        db,
        subject=selected.value,
        filename=filename,
        file_hash=file_hash,
        file_size=file_size,
        chunk_count=len(chunks),
        file_type=file_type,
    )

    mcq_batch_id = uuid.uuid4()
    mcqs = extract_or_generate_mcqs(text, topic=selected.value, min_questions=5)
    questions_extracted = _store_mcqs_in_db(db, mcqs, selected.value, mcq_batch_id, source_type=file_type)

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
@require_admin
def upload():
    db: Session = get_db()
    subject = request.form.get("subject")
    file_type = request.form.get("file_type", "question_paper")
    files = request.files.getlist("files")

    selected = _normalise_subject(subject)
    if selected is None:
        allowed = [s.value for s in Subject]
        return _validation_error(f"subject is required and must be one of {allowed}", field="subject")

    if len(files) > MAX_FILES_PER_BATCH:
        return _validation_error(f"Maximum {MAX_FILES_PER_BATCH} files per upload batch", field="files")

    warnings: List[str] = []
    already_indexed: List[dict[str, Any]] = []
    indexed_files = 0
    total_chunks = 0
    total_questions_extracted = 0

    for upload_file in files:
        filename = upload_file.filename or ""
        content = upload_file.read()
        file_size = len(content)
        file_hash = _compute_file_hash(content)

        existing = _check_duplicate(db, selected.value, file_hash)
        if existing is not None:
            already_indexed.append({
                "filename": filename,
                "existing_filename": existing.filename,
                "file_hash": file_hash,
                "chunk_count": existing.chunk_count,
                "indexed_at": existing.indexed_at.isoformat() if existing.indexed_at else None,
            })
            continue

        text = _extract_text(filename, content)
        if text is None or not text.strip():
            warnings.append(filename)
            continue

        chunks = chunk_text(text) if chunk_text else [text]
        if not chunks:
            warnings.append(filename)
            continue

        if stores:
            stores.add(selected, chunks)

        _record_indexed_file(
            db,
            subject=selected.value,
            filename=filename,
            file_hash=file_hash,
            file_size=file_size,
            chunk_count=len(chunks),
            file_type=file_type,
        )

        mcq_batch_id = uuid.uuid4()
        mcqs = extract_or_generate_mcqs(text, topic=selected.value, min_questions=5)
        questions_extracted = _store_mcqs_in_db(db, mcqs, selected.value, mcq_batch_id, source_type=file_type)

        indexed_files += 1
        total_chunks += len(chunks)
        total_questions_extracted += questions_extracted

    return jsonify({
        "success": True,
        "subject": selected.value,
        "indexed_files": indexed_files,
        "total_chunks": total_chunks,
        "questions_extracted": total_questions_extracted,
        "warnings": warnings,
        "already_indexed": already_indexed,
    }), 200


__all__ = ["router", "MAX_FILES_PER_BATCH"]
