"""Legacy ExamForge routes preserved during the structural refactor.

The behaviour is unchanged from ``backend/app.py`` - the endpoints are
simply moved onto an :class:`fastapi.APIRouter` so ``smartkcet.main`` can
mount them.  Renaming, RBAC gating, per-subject scoping, and DB-backed
persistence land in later tasks (3.x, 4.x, 5.x, 7.x, 8.x).
"""

from __future__ import annotations

import uuid
from typing import List

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

# Graceful degradation for Python 3.14 compatibility
# Both groq and pytesseract hang on import on Python 3.14
try:
    from ..rag import groq_client as groq_module
    GROQ_AVAILABLE = True
except (ImportError, TimeoutError):
    GROQ_AVAILABLE = False
    groq_module = None

# pytesseract is not available on Python 3.14 (pkgutil.find_loader removed)
try:
    from ..rag.parsing import (
        chunk_text,
        extract_text_from_docx,
        extract_text_from_pdf,
        extract_text_from_txt,
    )
    PARSING_AVAILABLE = True
except (ImportError, TimeoutError):
    PARSING_AVAILABLE = False
    # Provide stub functions so the module can still be imported
    chunk_text = None
    extract_text_from_docx = None
    extract_text_from_pdf = None
    extract_text_from_txt = None

from ..rag.store import store
from ..submissions.scoring import score_submission

router = APIRouter()


@router.get("/health")
def health() -> dict:
    return {"status": "ok", "chunks_indexed": len(store.chunks)}


@router.get("/debug")
def debug() -> dict:
    return {"chunks_indexed": len(store.chunks), "sample": store.chunks[:2]}


@router.post("/upload")
async def upload(files: List[UploadFile] = File(...)) -> dict:
    if len(files) > 10:
        raise HTTPException(400, "Maximum 10 files allowed")
    store.reset()
    doc_ids: List[str] = []
    total_chunks = 0
    for f in files:
        content = await f.read()
        name = (f.filename or "").lower()
        if name.endswith(".pdf"):
            text = extract_text_from_pdf(content)
        elif name.endswith(".docx"):
            text = extract_text_from_docx(content)
        elif name.endswith((".txt", ".doc")):
            text = extract_text_from_txt(content)
        else:
            continue
        chunks = chunk_text(text)
        store.add(chunks)
        total_chunks += len(chunks)
        doc_ids.append(str(uuid.uuid4()))
        print(f"\u2713 Indexed {f.filename}: {len(chunks)} chunks")
    return {
        "success": True,
        "doc_ids": doc_ids,
        "total_chunks": total_chunks,
        "message": f"{len(doc_ids)} files indexed with {total_chunks} chunks",
    }


class GenerateRequest(BaseModel):
    difficulty: str = "medium"
    count: int = 20
    types: list = ["MCQ"]
    subject: str = "General Subject"
    num_sets: int = 4


@router.post("/generate")
def generate(req: GenerateRequest) -> dict:
    if not store.chunks:
        raise HTTPException(400, "No documents uploaded yet.")
    subject = req.subject
    if subject == "General Subject":
        sample = " ".join(store.chunks[:5])
        detected = groq_module.detect_subject(sample)
        if detected:
            subject = detected
    print(f"Generating for subject: {subject}")
    used_questions: set = set()
    sets: list = []
    for label in ["A", "B", "C", "D"]:
        chunks = store.search(f"{subject} multiple choice questions", k=20)
        questions = groq_module.generate_mcq_set(chunks, subject, label, used_questions)
        sets.append(questions)
        print(f"\u2713 Set {label}: {len(questions)} questions")
    return {"sets": sets}


class AnalyzeRequest(BaseModel):
    questions: list
    answers: dict
    student: dict = {}


@router.post("/analyze")
def analyze(req: AnalyzeRequest) -> dict:
    """Score a submission via the shared :func:`score_submission` helper.

    The legacy ``/analyze`` route is now a thin wrapper around
    :mod:`smartkcet.submissions.scoring` so the new role-scoped
    ``POST /api/student/submit`` endpoint (task 8.1) and this legacy path
    share a single source of scoring truth.
    """

    return score_submission(req.questions, req.answers)
