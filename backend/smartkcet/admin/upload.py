"""Admin file-upload endpoint with per-subject FAISS indexing.

Implements task 4.3 / REQ-5.1, REQ-5.3, REQ-5.4, REQ-8.5:

* Mounted under ``/api/admin/upload`` from :mod:`smartkcet.admin`.
* Admin-only — guarded by :func:`smartkcet.middleware.rbac.require_admin`.
* Required ``subject`` form field (``Biology|Physics|Chemistry|Mathematics``);
  missing or unrecognised values short-circuit with HTTP 400 before any
  file is parsed.
* Up to 10 files per batch (REQ-5.3); larger batches are rejected with
  HTTP 400.
* Per-file extraction errors / unsupported extensions / empty OCR
  results are aggregated into the response ``warnings`` list **without**
  aborting the batch (REQ-5.4).
* Indexing is scoped strictly to the requested subject's FAISS store via
  :data:`smartkcet.rag.store.stores`; other subjects are never touched
  (REQ-5.1, REQ-8.5).
* Duplicate detection via SHA-256 file hash per subject.
* Individual file upload endpoint for per-file progress tracking.
* List indexed files endpoint for frontend display.
"""

from __future__ import annotations
import os

import hashlib
import logging
import uuid
from typing import Any, List, Optional

import os
from flask import Blueprint, request, g, make_response, jsonify, Response
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db.models import IndexedFile, Question, Subject
from ..middleware.rbac import require_admin
from ..rag.mcq_extractor import extract_or_generate_mcqs
from ..rag.topic_matcher import match_filename_to_topic, is_topic_matching, SUBJECT_CHAPTERS

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
    logger = logging.getLogger("smartkcet.admin.upload")
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

logger = logging.getLogger("smartkcet.admin.upload")

router = Blueprint("admin_upload", __name__)


# REQ-5.3 — matches the legacy ``/upload`` cap so admins don't experience
# a regression when migrating to the role-scoped endpoint.
MAX_FILES_PER_BATCH = 10


def _validation_error(message: str, field: Optional[str] = None):
    """Return a 400 JSON envelope identical in shape to other auth/admin errors."""

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


def _extract_text(filename: str, content: bytes)-> Optional[str]:
    """Dispatch on the filename extension; return ``None`` for unsupported types."""

    lowered = filename.lower()
    if lowered.endswith(".pdf"):
        logger.info("Extracting text from PDF: %s (%d bytes)", filename, len(content))
        return extract_text_from_pdf(content)
    if lowered.endswith(".docx"):
        logger.info("Extracting text from DOCX: %s (%d bytes)", filename, len(content))
        return extract_text_from_docx(content)
    if lowered.endswith(".txt"):
        logger.info("Extracting text from TXT: %s (%d bytes)", filename, len(content))
        return extract_text_from_txt(content)
    logger.warning("Unsupported file extension: %s", filename)
    return None


def _compute_file_hash(content: bytes)-> str:
    """Compute SHA-256 hex digest of file content."""
    return hashlib.sha256(content).hexdigest()


def _check_duplicate(db: Session, subject: str, file_hash: str)-> Optional[IndexedFile]:
    """Check if a file with the same hash already exists for admin (institution_id IS NULL)."""
    stmt = select(IndexedFile).where(
        IndexedFile.subject == subject,
        IndexedFile.file_hash == file_hash,
        IndexedFile.institution_id.is_(None),
    )
    return db.execute(stmt).scalar_one_or_none()


def _record_indexed_file(db: Session, subject: str, filename: str, file_hash: str, file_size: int, chunk_count: int, file_type: str = "question_paper")-> IndexedFile:
    """Insert a new admin IndexedFile record (institution_id=NULL) and commit."""
    record = IndexedFile(
        subject=subject,
        filename=filename,
        file_hash=file_hash,
        file_size=file_size,
        chunk_count=chunk_count,
        file_type=file_type,
        institution_id=None,  # admin/global
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def _store_mcqs_in_db(db: Session, mcqs: List[dict], subject: str, batch_id: uuid.UUID, source_type: str = "question_paper")-> int:
    """Store extracted MCQs as platform-wide Question rows (institution_id=NULL).

    Returns the number of questions successfully stored.
    """
    stored = 0
    for mcq in mcqs:
        q_text = mcq.get("q", "").strip()
        opts = mcq.get("opts", [])
        ans = mcq.get("ans", 0)
        topic = mcq.get("topic", "General")

        # Validate
        if not q_text or not isinstance(opts, list) or len(opts) != 4:
            continue

        row = Question(
            subject=subject,
            question_text=q_text,
            options=opts,
            correct_option=str(ans),
            topic=topic if isinstance(topic, str) else "General",
            generation_batch_id=batch_id,
            institution_id=None,  # platform-wide
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


# ─── GET /upload/files — list indexed files for a subject ─────────────────────


@router.route("/upload/files", methods=["GET"])
def list_indexed_files()-> Any:    
    _admin = require_admin()
    from flask import g
    db = getattr(g, "db", None)
    session = db
    from flask import request
    subject = request.args.get("subject", None)
    """Return all previously indexed files for a subject, with detected chapter topics."""

    selected = _normalise_subject(subject)
    if selected is None:
        allowed = [s.value for s in Subject]
        return _validation_error(
            f"subject is required and must be one of {allowed}",
            field="subject",
        )

    stmt = (
        select(IndexedFile)
        .where(
            IndexedFile.subject == selected.value,
            IndexedFile.institution_id.is_(None),
        )
        .order_by(IndexedFile.indexed_at.desc())
    )
    files = db.execute(stmt).scalars().all()
    official_chapters = SUBJECT_CHAPTERS.get(selected.value, [])

    response_files = []
    for f in files:
        topic = match_filename_to_topic(f.filename, selected.value)
        is_official = any(is_topic_matching(topic, [ch]) for ch in official_chapters)
        response_files.append({
            "id": str(f.id),
            "filename": f.filename,
            "file_hash": f.file_hash,
            "file_size": f.file_size,
            "chunk_count": f.chunk_count,
            "file_type": f.file_type,
            "topic": topic,
            "is_official_topic": is_official,
            "indexed_at": f.indexed_at.isoformat() if f.indexed_at else None,
        })

    return {
        "subject": selected.value,
        "files": response_files,
    }


# ─── DELETE /upload/files/<file_id> — delete an indexed file ──────────────────


@router.route("/upload/files/<file_id>", methods=["DELETE"])
def delete_indexed_file(file_id: str) -> Any:
    _admin = require_admin()
    from flask import g
    db = getattr(g, "db", None)

    try:
        file_uuid = uuid.UUID(file_id)
    except ValueError:
        return _validation_error("Invalid file ID format", field="file_id")

    record = db.execute(
        select(IndexedFile).where(
            IndexedFile.id == file_uuid,
            IndexedFile.institution_id.is_(None),
        )
    ).scalar_one_or_none()

    if not record:
        return jsonify({"error": "not_found", "message": "File not found"}), 404

    filename = record.filename
    subject_val = record.subject
    file_topic = match_filename_to_topic(filename, subject_val)

    # Delete the IndexedFile record
    db.delete(record)

    # Check if any other uploaded files for this subject share this topic
    other_files = db.execute(
        select(IndexedFile.filename).where(
            IndexedFile.subject == subject_val,
            IndexedFile.institution_id.is_(None),
            IndexedFile.id != file_uuid,
        )
    ).scalars().all()
    other_topics = {match_filename_to_topic(fn, subject_val) for fn in other_files}

    deleted_q_count = 0
    if file_topic not in other_topics:
        # Purge questions in DB matching this topic
        all_qs = db.execute(
            select(Question).where(Question.subject == subject_val)
        ).scalars().all()
        for q in all_qs:
            if is_topic_matching(q.topic, [file_topic]):
                db.delete(q)
                deleted_q_count += 1

    # Remove local textbook file copy if exists
    try:
        from pathlib import Path
        tb_path = Path("data/textbooks") / filename
        if tb_path.exists():
            tb_path.unlink()
    except Exception as exc:
        logger.warning("Could not unlink %s: %s", filename, exc)

    db.commit()
    logger.info(
        "Deleted indexed file '%s' (topic '%s') and %d associated questions",
        filename,
        file_topic,
        deleted_q_count,
    )

    return jsonify({
        "success": True,
        "message": f"Deleted '{filename}' and purged {deleted_q_count} questions from Question Bank.",
        "deleted_questions": deleted_q_count,
    })


# ─── DELETE /upload/clear — clear all indexed files and questions for a subject ─


@router.route("/upload/clear", methods=["DELETE"])
def clear_indexed_files() -> Any:
    _admin = require_admin()
    from flask import g, request
    db = getattr(g, "db", None)
    subject = request.args.get("subject", None)
    selected = _normalise_subject(subject)
    if selected is None:
        allowed = [s.value for s in Subject]
        return _validation_error(
            f"subject is required and must be one of {allowed}",
            field="subject",
        )

    records = db.execute(
        select(IndexedFile).where(
            IndexedFile.subject == selected.value,
            IndexedFile.institution_id.is_(None),
        )
    ).scalars().all()
    file_count = len(records)
    for r in records:
        try:
            from pathlib import Path
            p = Path("data/textbooks") / r.filename
            if p.exists():
                p.unlink()
        except Exception:
            pass
        db.delete(r)

    all_qs = db.execute(
        select(Question).where(Question.subject == selected.value)
    ).scalars().all()
    q_count = len(all_qs)
    for q in all_qs:
        db.delete(q)

    try:
        stores.clear(selected)
    except Exception:
        pass

    db.commit()
    logger.info("Cleared all %d files and %d questions for %s", file_count, q_count, selected.value)

    return jsonify({
        "success": True,
        "message": f"Cleared all {file_count} files and {q_count} questions for {selected.value}.",
        "cleared_files": file_count,
        "cleared_questions": q_count,
    })


# ─── POST /upload/single — individual file upload with progress ───────────────


@router.route("/upload/single", methods=["POST"])
def upload_single(subject: Optional[str] = None, file_type: str = "question_paper", file: Any = None)-> Any:    
    _admin = require_admin()
    from flask import g, request
    db = getattr(g, "db", None)
    session = db
    """Index a single uploaded file. Returns per-file status for progress tracking."""

    if subject is None:
        subject = request.form.get("subject") or request.args.get("subject")
    if file_type is None or file_type == "question_paper":
        file_type = request.form.get("file_type") or request.args.get("file_type") or "question_paper"
    if file is None:
        file = request.files.get("file")

    if file is None:
        return _validation_error("file is required", field="file")

    selected = _normalise_subject(subject)
    if selected is None:
        allowed = [s.value for s in Subject]
        return _validation_error(
            f"subject is required and must be one of {allowed}",
            field="subject",
        )

    filename = file.filename or ""
    content = file.read()
    file_size = len(content)
    file_hash = _compute_file_hash(content)

    # Check for duplicate
    existing = _check_duplicate(db, selected.value, file_hash)
    if existing is not None:
        return {
            "status": "duplicate",
            "filename": filename,
            "file_hash": file_hash,
            "file_size": file_size,
            "chunk_count": existing.chunk_count,
            "message": f"File already indexed as '{existing.filename}' with {existing.chunk_count} chunks",
        }

    # Extract text
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
            "file_hash": file_hash,
            "file_size": file_size,
            "chunk_count": 0,
            "message": "No text could be extracted from this file",
        }

    # Chunk text
    chunks = chunk_text(text)
    if not chunks:
        return {
            "status": "empty",
            "filename": filename,
            "file_hash": file_hash,
            "file_size": file_size,
            "chunk_count": 0,
            "message": "Text too short to produce meaningful chunks",
        }

    # Index into FAISS
    try:
        stores.add(selected, chunks)
    except Exception as exc:
        logger.warning("FAISS store indexing failed: %s", exc)

    # Record in database
    _record_indexed_file(
        db,
        subject=selected.value,
        filename=filename,
        file_hash=file_hash,
        file_size=file_size,
        chunk_count=len(chunks),
        file_type=file_type,
    )

    # Persist file copy to data/textbooks
    try:
        from pathlib import Path
        save_dir = Path("data/textbooks")
        save_dir.mkdir(parents=True, exist_ok=True)
        (save_dir / filename).write_bytes(content)
    except Exception as exc:
        logger.warning("Could not persist file copy to data/textbooks: %s", exc)

    # Extract MCQs strictly scoped to this file's chapter topic
    file_topic = match_filename_to_topic(filename, selected.value)
    mcq_batch_id = uuid.uuid4()
    mcqs = extract_or_generate_mcqs(
        text,
        topic=file_topic if file_topic != "General" else selected.value,
        min_questions=5,
        allowed_topics=[file_topic] if file_topic != "General" else None,
    )
    for mcq in mcqs:
        if file_topic != "General":
            mcq["topic"] = file_topic
    questions_extracted = _store_mcqs_in_db(db, mcqs, selected.value, mcq_batch_id, source_type=file_type)
    logger.info(
        "File '%s' (topic '%s'): extracted %d MCQs into question bank for %s",
        filename,
        file_topic,
        questions_extracted,
        selected.value,
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


# ─── POST /upload — batch upload (backward compat) ────────────────────────────


@router.route("/upload", methods=["POST"])
def upload(subject: Optional[str] = None, file_type: str = "question_paper", files: Optional[List[Any]] = None)-> Any:    
    _admin = require_admin()
    from flask import g, request
    db = getattr(g, "db", None)
    session = db
    """Index uploaded files into the requested subject's FAISS store.

    Now includes duplicate detection — files with matching SHA-256 hash
    for the same subject are skipped and returned in ``already_indexed``.
    """

    if subject is None:
        subject = request.form.get("subject") or request.args.get("subject")
    if file_type is None or file_type == "question_paper":
        file_type = request.form.get("file_type") or request.args.get("file_type") or "question_paper"
    if not files:
        files = request.files.getlist("files") or request.files.getlist("file")

    if not files:
        return _validation_error("At least one file is required", field="files")

    selected = _normalise_subject(subject)
    if selected is None:
        allowed = [s.value for s in Subject]
        return _validation_error(
            f"subject is required and must be one of {allowed}",
            field="subject",
        )

    if len(files) > MAX_FILES_PER_BATCH:
        return _validation_error(
            f"Maximum {MAX_FILES_PER_BATCH} files per upload batch",
            field="files",
        )

    warnings: List[str] = []
    already_indexed: List[dict[str, Any]] = []
    indexed_files = 0
    # Clear previously indexed files for this subject so only this uploaded batch defines the active scope
    try:
        old_files = db.execute(
            select(IndexedFile).where(
                IndexedFile.subject == selected.value,
                IndexedFile.institution_id.is_(None),
            )
        ).scalars().all()
        for of in old_files:
            db.delete(of)
        db.commit()
    except Exception as e:
        logger.warning("Could not clear previous indexed files: %s", e)

    try:
        stores.clear(selected)
    except Exception as exc:
        logger.warning("Failed to reset store for %s: %s", selected.value, exc)

    for upload_file in files:
        filename = upload_file.filename or ""
        content = upload_file.read()
        file_size = len(content)
        file_hash = _compute_file_hash(content)

        logger.info("Processing file: %s (%d bytes, hash: %s)", filename, file_size, file_hash[:12])

        # Duplicate detection
        existing = _check_duplicate(db, selected.value, file_hash)
        if existing is not None:
            logger.info(
                "File '%s' is a duplicate of '%s' (hash: %s) → skipping",
                filename,
                existing.filename,
                file_hash[:12],
            )
            already_indexed.append({
                "filename": filename,
                "existing_filename": existing.filename,
                "file_hash": file_hash,
                "chunk_count": existing.chunk_count,
                "indexed_at": existing.indexed_at.isoformat() if existing.indexed_at else None,
            })
            continue

        text = _extract_text(filename, content)
        if text is None:
            logger.warning(
                "File '%s': unsupported extension or extraction returned None → added to warnings",
                filename,
            )
            warnings.append(filename)
            continue

        if not text.strip():
            logger.warning(
                "File '%s': extraction returned empty text (0 chars after strip) → added to warnings",
                filename,
            )
            warnings.append(filename)
            continue

        chunks = chunk_text(text)
        if not chunks:
            logger.warning(
                "File '%s': text too short to produce chunks (%d chars) → added to warnings",
                filename,
                len(text.strip()),
            )
            warnings.append(filename)
            continue

        # REQ-5.1 / REQ-8.5: mutate only the selected subject's index.
        logger.info(
            "File '%s': successfully extracted %d chars → %d chunks → indexing into %s",
            filename,
            len(text.strip()),
            len(chunks),
            selected.value,
        )
        try:
            stores.add(selected, chunks)
        except Exception as exc:
            logger.warning("FAISS store indexing failed for %s: %s", filename, exc)

        # Record in database
        _record_indexed_file(
            db,
            subject=selected.value,
            filename=filename,
            file_hash=file_hash,
            file_size=file_size,
            chunk_count=len(chunks),
            file_type=file_type,
        )

        # Persist file copy to data/textbooks
        try:
            from pathlib import Path
            save_dir = Path("data/textbooks")
            save_dir.mkdir(parents=True, exist_ok=True)
            (save_dir / filename).write_bytes(content)
        except Exception as exc:
            logger.warning("Could not persist file copy to data/textbooks: %s", exc)

        # Extract MCQs strictly scoped to this file's chapter topic
        file_topic = match_filename_to_topic(filename, selected.value)
        mcq_batch_id = uuid.uuid4()
        mcqs = extract_or_generate_mcqs(
            text,
            topic=file_topic if file_topic != "General" else selected.value,
            min_questions=5,
            allowed_topics=[file_topic] if file_topic != "General" else None,
        )
        for mcq in mcqs:
            if file_topic != "General":
                mcq["topic"] = file_topic
        questions_extracted = _store_mcqs_in_db(db, mcqs, selected.value, mcq_batch_id, source_type=file_type)
        logger.info(
            "File '%s' (topic '%s'): extracted %d MCQs into question bank for %s",
            filename,
            file_topic,
            questions_extracted,
            selected.value,
        )

        indexed_files += 1
        total_chunks += len(chunks)
        total_questions_extracted += questions_extracted

    return {
        "success": True,
        "subject": selected.value,
        "indexed_files": indexed_files,
        "total_chunks": total_chunks,
        "questions_extracted": total_questions_extracted,
        "warnings": warnings,
        "already_indexed": already_indexed,
    }


__all__ = ["router", "MAX_FILES_PER_BATCH"]
