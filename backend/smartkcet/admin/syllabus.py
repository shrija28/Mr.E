"""Admin KCET Syllabus management API.

Endpoints
---------
GET    /api/admin/syllabus             – list all topics (with filters)
GET    /api/admin/syllabus/counts      – chapter counts per subject/PUC
POST   /api/admin/syllabus             – add a new topic
PATCH  /api/admin/syllabus/{id}        – edit topic (name, order, active, description)
DELETE /api/admin/syllabus/{id}        – delete a topic

Public (no auth required)
GET    /api/syllabus                   – all active topics (for students/institutions)
GET    /api/syllabus/{subject}         – active topics for one subject
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from fastapi import APIRouter, Depends, Path, Query, Request, status, File, Form, UploadFile
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
import os
import uuid
import shutil
from pathlib import Path as PathlibPath
from sqlalchemy import delete, func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from ..db.models import SyllabusTopic, Subject
from ..db.session import get_async_session as get_session
from ..middleware.rbac import require_admin

logger = logging.getLogger("smartkcet.admin.syllabus")

router = APIRouter()
public_router = APIRouter()   # mounted separately — no auth


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

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


TEXTBOOKS_DIR = PathlibPath(__file__).resolve().parent.parent.parent / "data" / "textbooks"

@public_router.get("/syllabus/textbook/{filename}")
def download_textbook(
    filename: str,
) -> FileResponse:
    """Download/view an associated textbook file."""
    file_path = TEXTBOOKS_DIR / filename
    if not file_path.exists() or not file_path.is_file():
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Textbook file not found")
    return FileResponse(file_path, filename=filename)


def _validation_error(msg: str, field: Optional[str] = None) -> JSONResponse:
    body: dict[str, Any] = {"error": "validation_error", "message": msg}
    if field:
        body["field"] = field
    return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=body)


VALID_PUC = {"1st PUC", "2nd PUC"}
VALID_SUBJECTS = {s.value for s in Subject}


# ---------------------------------------------------------------------------
# Request bodies
# ---------------------------------------------------------------------------

class CreateTopicRequest(BaseModel):
    subject: str
    puc_year: str
    chapter_number: int
    chapter_name: str
    display_order: int = 0
    description: Optional[str] = None
    is_active: bool = True


class PatchTopicRequest(BaseModel):
    chapter_name: Optional[str] = None
    display_order: Optional[int] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


# ---------------------------------------------------------------------------
# PUBLIC endpoints (no auth)
# ---------------------------------------------------------------------------

@public_router.get("/syllabus")
def list_syllabus_public(
    subject: Optional[str] = Query(default=None),
    puc_year: Optional[str] = Query(default=None),
    session: Session = Depends(get_session),
) -> Any:
    """Return all active KCET syllabus topics — accessible by students and institutions."""
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

    # Group into nested structure: subject → puc_year → chapters
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

    return {
        "subjects": result,
        "total_topics": len(rows),
    }


@public_router.get("/syllabus/{subject}")
def get_syllabus_by_subject(
    subject: str = Path(...),
    session: Session = Depends(get_session),
) -> Any:
    """Return active topics for one subject, grouped by PUC year."""
    if subject not in VALID_SUBJECTS:
        return JSONResponse(
            status_code=404,
            content={"error": "not_found", "message": f"Subject '{subject}' not found"},
        )
    stmt = (
        select(SyllabusTopic)
        .where(SyllabusTopic.subject == subject, SyllabusTopic.is_active.is_(True))
        .order_by(SyllabusTopic.puc_year, SyllabusTopic.display_order, SyllabusTopic.chapter_number)
    )
    rows = session.execute(stmt).scalars().all()

    puc_map: dict[str, list] = {}
    for t in rows:
        puc_map.setdefault(t.puc_year, []).append(_serialise(t))

    return {
        "subject": subject,
        "puc_years": [
            {"puc_year": p, "chapters": chs, "total_chapters": len(chs)}
            for p, chs in sorted(puc_map.items())
        ],
        "total_chapters": len(rows),
    }


# ---------------------------------------------------------------------------
# ADMIN endpoints
# ---------------------------------------------------------------------------

@router.get("/syllabus/counts")
def get_topic_counts(
    session: Session = Depends(get_session),
    _admin: dict = Depends(require_admin),
) -> Any:
    """Per-subject, per-PUC chapter counts (all + active)."""
    from sqlalchemy import Integer as SAInteger, case
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
    return {"counts": counts}


@router.get("/syllabus")
def list_topics(
    subject: Optional[str] = Query(default=None),
    puc_year: Optional[str] = Query(default=None),
    include_inactive: bool = Query(default=True),
    session: Session = Depends(get_session),
    _admin: dict = Depends(require_admin),
) -> Any:
    """Admin: list all syllabus topics with optional filters."""
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
    return {"topics": [_serialise(t) for t in rows], "total": len(rows)}


@router.post("/syllabus", status_code=status.HTTP_201_CREATED)
def create_topic(
    subject: str = Form(...),
    puc_year: str = Form(...),
    chapter_number: int = Form(...),
    chapter_name: str = Form(...),
    display_order: int = Form(default=0),
    description: Optional[str] = Form(default=None),
    is_active: bool = Form(default=True),
    textbook: Optional[UploadFile] = File(default=None),
    session: Session = Depends(get_session),
    _admin: dict = Depends(require_admin),
) -> Any:
    """Admin: add a new syllabus chapter."""
    if subject not in VALID_SUBJECTS:
        return _validation_error(f"subject must be one of {sorted(VALID_SUBJECTS)}", "subject")
    if puc_year not in VALID_PUC:
        return _validation_error("puc_year must be '1st PUC' or '2nd PUC'", "puc_year")
    if not chapter_name.strip():
        return _validation_error("chapter_name is required", "chapter_name")
    if chapter_number < 1:
        return _validation_error("chapter_number must be >= 1", "chapter_number")

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
            with open(dest_path, "wb") as buffer:
                shutil.copyfileobj(textbook.file, buffer)
            topic.textbook_filename = textbook.filename
            topic.textbook_path = f"/api/syllabus/textbook/{safe_filename}"

            try:
                from .upload import _extract_text, chunk_text, stores
                textbook.file.seek(0)
                content = textbook.file.read()
                text = _extract_text(textbook.filename, content)
                if text and text.strip():
                    chunks = chunk_text(text)
                    if chunks:
                        stores.add(Subject(subject), chunks)
                        logger.info("Indexed textbook '%s' for syllabus chapter %d", textbook.filename, topic.id)
            except Exception as index_err:
                logger.warning("Textbook indexing failed (non-fatal): %s", index_err)

        session.commit()
        session.refresh(topic)
    except SQLAlchemyError as exc:
        session.rollback()
        if "UNIQUE" in str(exc).upper():
            return JSONResponse(
                status_code=status.HTTP_409_CONFLICT,
                content={
                    "error": "duplicate_chapter",
                    "message": f"Chapter {chapter_number} already exists for {subject} {puc_year}",
                },
            )
        logger.warning("POST /admin/syllabus failed: %s", exc)
        return JSONResponse(
            status_code=500,
            content={"error": "db_error", "message": str(exc)},
        )
    return _serialise(topic)


@router.patch("/syllabus/{topic_id}")
def patch_topic(
    topic_id: int = Path(...),
    chapter_name: Optional[str] = Form(default=None),
    display_order: Optional[int] = Form(default=None),
    description: Optional[str] = Form(default=None),
    is_active: Optional[bool] = Form(default=None),
    textbook: Optional[UploadFile] = File(default=None),
    clear_textbook: bool = Form(default=False),
    session: Session = Depends(get_session),
    _admin: dict = Depends(require_admin),
) -> Any:
    """Admin: edit a syllabus topic (name, order, active status, description, textbook)."""
    topic = session.get(SyllabusTopic, topic_id)
    if topic is None:
        return JSONResponse(
            status_code=404,
            content={"error": "not_found", "id": topic_id},
        )

    if chapter_name is not None:
        if not chapter_name.strip():
            return _validation_error("chapter_name cannot be empty", "chapter_name")
        topic.chapter_name = chapter_name.strip()
    if display_order is not None:
        topic.display_order = display_order
    if description is not None:
        topic.description = description
    if is_active is not None:
        topic.is_active = is_active

    if clear_textbook:
        topic.textbook_filename = None
        topic.textbook_path = None
    elif textbook and textbook.filename:
        os.makedirs(TEXTBOOKS_DIR, exist_ok=True)
        unique_prefix = f"topic_{topic.id}"
        safe_filename = f"{unique_prefix}_{textbook.filename}"
        dest_path = TEXTBOOKS_DIR / safe_filename
        with open(dest_path, "wb") as buffer:
            shutil.copyfileobj(textbook.file, buffer)
        topic.textbook_filename = textbook.filename
        topic.textbook_path = f"/api/syllabus/textbook/{safe_filename}"

        try:
            from .upload import _extract_text, chunk_text, stores
            textbook.file.seek(0)
            content = textbook.file.read()
            text = _extract_text(textbook.filename, content)
            if text and text.strip():
                chunks = chunk_text(text)
                if chunks:
                    stores.add(Subject(topic.subject), chunks)
                    logger.info("Indexed textbook '%s' for syllabus chapter %d", textbook.filename, topic.id)
        except Exception as index_err:
            logger.warning("Textbook indexing failed (non-fatal): %s", index_err)

    try:
        session.commit()
        session.refresh(topic)
    except SQLAlchemyError as exc:
        session.rollback()
        return JSONResponse(
            status_code=500,
            content={"error": "db_error", "message": str(exc)},
        )
    return _serialise(topic)


@router.delete("/syllabus/{topic_id}")
def delete_topic(
    topic_id: int = Path(...),
    session: Session = Depends(get_session),
    _admin: dict = Depends(require_admin),
) -> Any:
    """Admin: permanently delete a syllabus topic."""
    topic = session.get(SyllabusTopic, topic_id)
    if topic is None:
        return JSONResponse(
            status_code=404,
            content={"error": "not_found", "id": topic_id},
        )
    try:
        session.execute(delete(SyllabusTopic).where(SyllabusTopic.id == topic_id))
        session.commit()
    except SQLAlchemyError as exc:
        session.rollback()
        return JSONResponse(
            status_code=500,
            content={"error": "db_error", "message": str(exc)},
        )
    return {"deleted": True, "id": topic_id}


# ---------------------------------------------------------------------------
# BULK TEXTBOOK UPLOAD
# ---------------------------------------------------------------------------

@router.post("/syllabus/bulk-textbook")
async def bulk_upload_textbooks(
    request: Request,
    session: Session = Depends(get_session),
    _admin: dict = Depends(require_admin),
) -> Any:
    """Admin: upload textbooks for multiple chapters at once.

    Accepts a multipart/form-data body where each field named ``textbook_{topic_id}``
    is a file upload for that chapter.  Returns per-chapter results.
    """
    form = await request.form()

    results = []
    errors = []

    os.makedirs(TEXTBOOKS_DIR, exist_ok=True)

    for field_name, field_value in form.multi_items():
        # Only process fields named textbook_<int>
        if not field_name.startswith("textbook_"):
            continue
        try:
            topic_id = int(field_name[len("textbook_"):])
        except ValueError:
            continue

        # Must be a file upload
        if not hasattr(field_value, "filename") or not field_value.filename:
            continue

        upload_file = field_value
        topic = session.get(SyllabusTopic, topic_id)
        if topic is None:
            errors.append({"topic_id": topic_id, "error": "Chapter not found"})
            continue

        try:
            content = await upload_file.read()
            safe_filename = f"topic_{topic_id}_{upload_file.filename}"
            dest_path = TEXTBOOKS_DIR / safe_filename

            with open(dest_path, "wb") as f:
                f.write(content)

            topic.textbook_filename = upload_file.filename
            topic.textbook_path = f"/api/syllabus/textbook/{safe_filename}"

            # Index into RAG (non-fatal)
            try:
                from .upload import _extract_text, chunk_text, stores
                text = _extract_text(upload_file.filename, content)
                if text and text.strip():
                    chunks = chunk_text(text)
                    if chunks:
                        stores.add(Subject(topic.subject), chunks)
                        logger.info(
                            "Bulk: indexed textbook '%s' for chapter %d (%s)",
                            upload_file.filename, topic_id, topic.subject,
                        )
            except Exception as index_err:
                logger.warning("Bulk textbook indexing failed (non-fatal): %s", index_err)

            session.flush()
            results.append({
                "topic_id": topic_id,
                "chapter_name": topic.chapter_name,
                "subject": topic.subject,
                "filename": upload_file.filename,
                "status": "ok",
            })

        except Exception as exc:
            logger.warning("Bulk textbook upload failed for topic %d: %s", topic_id, exc)
            errors.append({"topic_id": topic_id, "error": str(exc)})

    try:
        session.commit()
    except SQLAlchemyError as exc:
        session.rollback()
        return JSONResponse(
            status_code=500,
            content={"error": "db_error", "message": str(exc)},
        )

    return {
        "uploaded": len(results),
        "errors": len(errors),
        "results": results,
        "error_details": errors,
    }


__all__ = ["router", "public_router"]
