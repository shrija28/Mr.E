"""Admin KCET Syllabus management API using Flask Blueprint."""

from __future__ import annotations

import logging
import os
import shutil
import uuid
from pathlib import Path as PathlibPath
from typing import Any, Optional

from flask import Blueprint, jsonify, request, send_from_directory
from sqlalchemy import delete, func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from ..db.models import Subject, SyllabusTopic
from ..db.session import get_db
from ..middleware.rbac import require_admin

logger = logging.getLogger("smartkcet.admin.syllabus")

router = Blueprint("admin_syllabus", __name__, url_prefix="/api/admin")
public_router = Blueprint("public_syllabus", __name__, url_prefix="/api")

TEXTBOOKS_DIR = PathlibPath(__file__).resolve().parent.parent.parent / "data" / "textbooks"
VALID_PUC = {"1st PUC", "2nd PUC"}
VALID_SUBJECTS = {s.value for s in Subject}


def _serialise(t: SyllabusTopic) -> dict[str, Any]:
    return {
        "id": t.id,
        "subject": t.subject,
        "puc_year": t.puc_year,
        "chapter_number": t.chapter_number,
        "chapter_name": t.chapter_name,
        "display_order": t.display_order,
        "description": t.description,
        "is_active": t.is_active,
        "textbook_filename": t.textbook_filename,
        "textbook_path": t.textbook_path,
        "created_at": t.created_at.isoformat() if t.created_at else None,
        "updated_at": t.updated_at.isoformat() if t.updated_at else None,
    }


def _validation_error(msg: str, field: Optional[str] = None):
    body: dict[str, Any] = {"error": "validation_error", "message": msg}
    if field:
        body["field"] = field
    return jsonify(body), 400


@public_router.route("/syllabus/textbook/<filename>", methods=["GET"])
def download_textbook(filename: str):
    file_path = TEXTBOOKS_DIR / filename
    if not file_path.exists() or not file_path.is_file():
        return jsonify({"error": "not_found", "message": "Textbook file not found"}), 404
    return send_from_directory(TEXTBOOKS_DIR, filename)


@public_router.route("/syllabus", methods=["GET"])
def list_syllabus_public():
    session: Session = get_db()
    subject = request.args.get("subject")
    puc_year = request.args.get("puc_year")

    stmt = (
        select(SyllabusTopic)
        .where(SyllabusTopic.is_active.is_(True))
        .order_by(
            SyllabusTopic.subject,
            SyllabusTopic.puc_year,
            SyllabusTopic.display_order,
            SyllabusTopic.chapter_number,
        )
    )
    if subject:
        if subject not in VALID_SUBJECTS:
            return _validation_error(f"subject must be one of {sorted(VALID_SUBJECTS)}")
        stmt = stmt.where(SyllabusTopic.subject == subject)
    if puc_year:
        if puc_year not in VALID_PUC:
            return _validation_error("puc_year must be '1st PUC' or '2nd PUC'")
        stmt = stmt.where(SyllabusTopic.puc_year == puc_year)

    rows = session.execute(stmt).scalars().all()

    grouped: dict[str, dict[str, list]] = {}
    for t in rows:
        grouped.setdefault(t.subject, {}).setdefault(t.puc_year, []).append(_serialise(t))

    result = []
    for subj, puc_map in grouped.items():
        puc_list = []
        for puc, chapters in sorted(puc_map.items()):
            puc_list.append({
                "puc_year": puc,
                "chapters": chapters,
                "total_chapters": len(chapters),
            })
        result.append({
            "subject": subj,
            "puc_years": puc_list,
            "total_chapters": sum(len(v) for v in puc_map.values()),
        })

    return jsonify({
        "subjects": result,
        "total_topics": len(rows),
    }), 200


@public_router.route("/syllabus/<subject>", methods=["GET"])
def get_syllabus_by_subject(subject: str):
    session: Session = get_db()
    if subject not in VALID_SUBJECTS:
        return jsonify({"error": "not_found", "message": f"Subject '{subject}' not found"}), 404

    stmt = (
        select(SyllabusTopic)
        .where(SyllabusTopic.subject == subject, SyllabusTopic.is_active.is_(True))
        .order_by(SyllabusTopic.puc_year, SyllabusTopic.display_order, SyllabusTopic.chapter_number)
    )
    rows = session.execute(stmt).scalars().all()

    puc_map: dict[str, list] = {}
    for t in rows:
        puc_map.setdefault(t.puc_year, []).append(_serialise(t))

    return jsonify({
        "subject": subject,
        "puc_years": [
            {"puc_year": p, "chapters": chs, "total_chapters": len(chs)}
            for p, chs in sorted(puc_map.items())
        ],
        "total_chapters": len(rows),
    }), 200


@router.route("/syllabus/counts", methods=["GET"])
@require_admin
def get_topic_counts():
    session: Session = get_db()
    from sqlalchemy import case
    rows = session.execute(
        select(
            SyllabusTopic.subject,
            SyllabusTopic.puc_year,
            func.count(SyllabusTopic.id).label("total"),
            func.sum(
                case((SyllabusTopic.is_active == True, 1), else_=0)
            ).label("active"),
        )
        .group_by(SyllabusTopic.subject, SyllabusTopic.puc_year)
        .order_by(SyllabusTopic.subject, SyllabusTopic.puc_year)
    ).all()

    counts = [
        {"subject": r.subject, "puc_year": r.puc_year, "total": r.total, "active": r.active or 0}
        for r in rows
    ]
    return jsonify({"counts": counts}), 200


@router.route("/syllabus", methods=["GET"])
@require_admin
def list_topics():
    session: Session = get_db()
    subject = request.args.get("subject")
    puc_year = request.args.get("puc_year")
    include_inactive_str = request.args.get("include_inactive", "true")
    include_inactive = include_inactive_str.lower() == "true"

    stmt = select(SyllabusTopic).order_by(
        SyllabusTopic.subject,
        SyllabusTopic.puc_year,
        SyllabusTopic.display_order,
        SyllabusTopic.chapter_number,
    )
    if subject:
        if subject not in VALID_SUBJECTS:
            return _validation_error(f"subject must be one of {sorted(VALID_SUBJECTS)}")
        stmt = stmt.where(SyllabusTopic.subject == subject)
    if puc_year:
        if puc_year not in VALID_PUC:
            return _validation_error("puc_year must be '1st PUC' or '2nd PUC'")
        stmt = stmt.where(SyllabusTopic.puc_year == puc_year)
    if not include_inactive:
        stmt = stmt.where(SyllabusTopic.is_active.is_(True))

    rows = session.execute(stmt).scalars().all()
    return jsonify({"topics": [_serialise(t) for t in rows], "total": len(rows)}), 200


@router.route("/syllabus", methods=["POST"])
@require_admin
def create_topic():
    session: Session = get_db()
    subject = request.form.get("subject")
    puc_year = request.form.get("puc_year")
    raw_chapter_number = request.form.get("chapter_number")
    chapter_name = request.form.get("chapter_name")
    raw_display_order = request.form.get("display_order", 0)
    description = request.form.get("description")
    raw_is_active = request.form.get("is_active", "true")
    textbook = request.files.get("textbook")

    if not subject or subject not in VALID_SUBJECTS:
        return _validation_error(f"subject must be one of {sorted(VALID_SUBJECTS)}", "subject")
    if not puc_year or puc_year not in VALID_PUC:
        return _validation_error("puc_year must be '1st PUC' or '2nd PUC'", "puc_year")
    if not chapter_name or not chapter_name.strip():
        return _validation_error("chapter_name is required", "chapter_name")

    try:
        chapter_number = int(raw_chapter_number)
    except (ValueError, TypeError):
        return _validation_error("chapter_number must be an integer", "chapter_number")

    if chapter_number < 1:
        return _validation_error("chapter_number must be >= 1", "chapter_number")

    display_order = int(raw_display_order) if str(raw_display_order).isdigit() else 0
    is_active = raw_is_active.lower() in ("true", "1")

    topic = SyllabusTopic(
        subject=subject,
        puc_year=puc_year,
        chapter_number=chapter_number,
        chapter_name=chapter_name.strip(),
        display_order=display_order,
        description=description,
        is_active=is_active,
    )
    session.add(topic)
    try:
        session.flush()
        if textbook and textbook.filename:
            os.makedirs(TEXTBOOKS_DIR, exist_ok=True)
            unique_prefix = f"topic_{topic.id}"
            safe_filename = f"{unique_prefix}_{textbook.filename}"
            dest_path = TEXTBOOKS_DIR / safe_filename
            textbook.save(dest_path)
            topic.textbook_filename = textbook.filename
            topic.textbook_path = f"/api/syllabus/textbook/{safe_filename}"

            try:
                from .upload import _extract_text, chunk_text, stores
                textbook.seek(0)
                content = textbook.read()
                text = _extract_text(textbook.filename, content)
                if text and text.strip():
                    chunks = chunk_text(text)
                    if chunks and stores:
                        stores.add(Subject(subject), chunks)
            except Exception as index_err:
                logger.warning("Textbook indexing failed (non-fatal): %s", index_err)

        session.commit()
        session.refresh(topic)
    except SQLAlchemyError as exc:
        session.rollback()
        if "UNIQUE" in str(exc).upper():
            return jsonify({
                "error": "duplicate_chapter",
                "message": f"Chapter {chapter_number} already exists for {subject} {puc_year}",
            }), 409
        return jsonify({"error": "db_error", "message": str(exc)}), 500

    return jsonify(_serialise(topic)), 201


@router.route("/syllabus/<topic_id>", methods=["PATCH"])
@require_admin
def patch_topic(topic_id: str):
    session: Session = get_db()
    try:
        tid = int(topic_id)
    except ValueError:
        return jsonify({"error": "validation_error", "message": "Invalid topic_id"}), 400

    topic = session.get(SyllabusTopic, tid)
    if topic is None:
        return jsonify({"error": "not_found", "id": topic_id}), 404

    chapter_name = request.form.get("chapter_name")
    raw_display_order = request.form.get("display_order")
    description = request.form.get("description")
    raw_is_active = request.form.get("is_active")
    textbook = request.files.get("textbook")
    clear_textbook = request.form.get("clear_textbook", "false").lower() == "true"

    if chapter_name is not None:
        if not chapter_name.strip():
            return _validation_error("chapter_name cannot be empty", "chapter_name")
        topic.chapter_name = chapter_name.strip()
    if raw_display_order is not None:
        try:
            topic.display_order = int(raw_display_order)
        except ValueError:
            pass
    if description is not None:
        topic.description = description
    if raw_is_active is not None:
        topic.is_active = raw_is_active.lower() in ("true", "1")

    if clear_textbook:
        topic.textbook_filename = None
        topic.textbook_path = None
    elif textbook and textbook.filename:
        os.makedirs(TEXTBOOKS_DIR, exist_ok=True)
        unique_prefix = f"topic_{topic.id}"
        safe_filename = f"{unique_prefix}_{textbook.filename}"
        dest_path = TEXTBOOKS_DIR / safe_filename
        textbook.save(dest_path)
        topic.textbook_filename = textbook.filename
        topic.textbook_path = f"/api/syllabus/textbook/{safe_filename}"

        try:
            from .upload import _extract_text, chunk_text, stores
            textbook.seek(0)
            content = textbook.read()
            text = _extract_text(textbook.filename, content)
            if text and text.strip():
                chunks = chunk_text(text)
                if chunks and stores:
                    stores.add(Subject(topic.subject), chunks)
        except Exception as index_err:
            logger.warning("Textbook indexing failed (non-fatal): %s", index_err)

    try:
        session.commit()
        session.refresh(topic)
    except SQLAlchemyError as exc:
        session.rollback()
        return jsonify({"error": "db_error", "message": str(exc)}), 500

    return jsonify(_serialise(topic)), 200


@router.route("/syllabus/<topic_id>", methods=["DELETE"])
@require_admin
def delete_topic(topic_id: str):
    session: Session = get_db()
    try:
        tid = int(topic_id)
    except ValueError:
        return jsonify({"error": "validation_error", "message": "Invalid topic_id"}), 400

    topic = session.get(SyllabusTopic, tid)
    if topic is None:
        return jsonify({"error": "not_found", "id": topic_id}), 404

    try:
        session.execute(delete(SyllabusTopic).where(SyllabusTopic.id == tid))
        session.commit()
    except SQLAlchemyError as exc:
        session.rollback()
        return jsonify({"error": "db_error", "message": str(exc)}), 500

    return jsonify({"deleted": True, "id": topic_id}), 200


@router.route("/syllabus/bulk-textbook", methods=["POST"])
@require_admin
def bulk_upload_textbooks():
    session: Session = get_db()
    results = []
    errors = []

    os.makedirs(TEXTBOOKS_DIR, exist_ok=True)

    for field_name, upload_file in request.files.items():
        if not field_name.startswith("textbook_"):
            continue
        try:
            topic_id = int(field_name[len("textbook_"):])
        except ValueError:
            continue

        if not upload_file.filename:
            continue

        topic = session.get(SyllabusTopic, topic_id)
        if topic is None:
            errors.append({"topic_id": topic_id, "error": "Chapter not found"})
            continue

        try:
            content = upload_file.read()
            safe_filename = f"topic_{topic_id}_{upload_file.filename}"
            dest_path = TEXTBOOKS_DIR / safe_filename

            with open(dest_path, "wb") as f:
                f.write(content)

            topic.textbook_filename = upload_file.filename
            topic.textbook_path = f"/api/syllabus/textbook/{safe_filename}"

            try:
                from .upload import _extract_text, chunk_text, stores
                text = _extract_text(upload_file.filename, content)
                if text and text.strip():
                    chunks = chunk_text(text)
                    if chunks and stores:
                        stores.add(Subject(topic.subject), chunks)
            except Exception as index_err:
                logger.warning("Bulk textbook indexing failed: %s", index_err)

            session.flush()
            results.append({
                "topic_id": topic_id,
                "chapter_name": topic.chapter_name,
                "subject": topic.subject,
                "filename": upload_file.filename,
                "status": "ok",
            })
        except Exception as exc:
            errors.append({"topic_id": topic_id, "error": str(exc)})

    try:
        session.commit()
    except SQLAlchemyError as exc:
        session.rollback()
        return jsonify({"error": "db_error", "message": str(exc)}), 500

    return jsonify({
        "uploaded": len(results),
        "errors": len(errors),
        "results": results,
        "error_details": errors,
    }), 200


__all__ = ["router", "public_router"]
