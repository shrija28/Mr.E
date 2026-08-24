"""Legacy ExamForge routes using Flask Blueprint."""

from __future__ import annotations

import uuid
from typing import List
from flask import Blueprint, jsonify, request

try:
    from ..rag import groq_client as groq_module
    GROQ_AVAILABLE = True
except (ImportError, TimeoutError):
    GROQ_AVAILABLE = False
    groq_module = None

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
    chunk_text = None
    extract_text_from_docx = None
    extract_text_from_pdf = None
    extract_text_from_txt = None

from ..rag.store import store
from ..submissions.scoring import score_submission

router = Blueprint("legacy", __name__)


@router.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "chunks_indexed": len(store.chunks)}), 200


@router.route("/debug", methods=["GET"])
def debug():
    return jsonify({"chunks_indexed": len(store.chunks), "sample": store.chunks[:2]}), 200


@router.route("/upload", methods=["POST"])
def upload():
    uploaded_files = request.files.getlist("files")
    if len(uploaded_files) > 10:
        return jsonify({"error": "validation_error", "message": "Maximum 10 files allowed"}), 400
    store.reset()
    doc_ids: List[str] = []
    total_chunks = 0
    for f in uploaded_files:
        content = f.read()
        name = (f.filename or "").lower()
        if name.endswith(".pdf"):
            text = extract_text_from_pdf(content) if extract_text_from_pdf else ""
        elif name.endswith(".docx"):
            text = extract_text_from_docx(content) if extract_text_from_docx else ""
        elif name.endswith((".txt", ".doc")):
            text = extract_text_from_txt(content) if extract_text_from_txt else ""
        else:
            continue
        chunks = chunk_text(text) if chunk_text else []
        store.add(chunks)
        total_chunks += len(chunks)
        doc_ids.append(str(uuid.uuid4()))
    return jsonify({
        "success": True,
        "doc_ids": doc_ids,
        "total_chunks": total_chunks,
        "message": f"{len(doc_ids)} files indexed with {total_chunks} chunks",
    }), 200


@router.route("/generate", methods=["POST"])
def generate():
    if not store.chunks:
        return jsonify({"error": "validation_error", "message": "No documents uploaded yet."}), 400
    data = request.get_json(silent=True) or {}
    subject = data.get("subject", "General Subject")
    if subject == "General Subject" and GROQ_AVAILABLE and groq_module:
        sample = " ".join(store.chunks[:5])
        detected = groq_module.detect_subject(sample)
        if detected:
            subject = detected
    used_questions: set = set()
    sets: list = []
    for label in ["A", "B", "C", "D"]:
        chunks = store.search(f"{subject} multiple choice questions", k=20)
        if GROQ_AVAILABLE and groq_module:
            questions = groq_module.generate_mcq_set(chunks, subject, label, used_questions)
        else:
            questions = []
        sets.append(questions)
    return jsonify({"sets": sets}), 200


@router.route("/analyze", methods=["POST"])
def analyze():
    data = request.get_json(silent=True) or {}
    questions = data.get("questions", [])
    answers = data.get("answers", {})
    return jsonify(score_submission(questions, answers)), 200


__all__ = ["router"]
