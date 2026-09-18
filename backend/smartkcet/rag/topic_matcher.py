"""Topic and chapter matching utilities for uploaded textbooks and question files.

Maps user-uploaded filenames (e.g. "HUMAN REPRODUCTION.pdf", "general principal.pdf")
to official syllabus chapters and provides filtering to ensure that question generation
and question banks strictly restrict questions to only the uploaded chapters.
"""

from __future__ import annotations

import re
from typing import Optional, List, Set
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db.models import IndexedFile
from ..db.syllabus_seed import SYLLABUS_DATA

# Build subject -> list of chapter names mapping
SUBJECT_CHAPTERS: dict[str, list[str]] = {}
for entry in SYLLABUS_DATA:
    subj, _, _, ch_name = entry[0], entry[1], entry[2], entry[3]
    SUBJECT_CHAPTERS.setdefault(subj, []).append(ch_name)


def match_filename_to_topic(filename: str, subject: str, sample_text: Optional[str] = None) -> str:
    """Map a filename like 'HUMAN REPRODUCTION.pdf' or file text to its official syllabus chapter name."""
    if not filename and not sample_text:
        return "General"

    fn_clean = re.sub(r"\.[a-zA-Z0-9]+$", "", filename or "").replace("_", " ").replace("-", " ").strip()
    words = set(re.findall(r"[a-z]+", fn_clean.lower()))

    # Inspect sample text first if available
    if sample_text:
        st_lower = sample_text[:2000].lower()
        # Look for exact syllabus chapter matches in sample text
        chapters = SUBJECT_CHAPTERS.get(subject, [])
        for ch in chapters:
            if ch.lower() in st_lower:
                return ch
        # Detect Chemistry Metallurgy if subject is Chemistry
        if subject == "Chemistry" and ("general principles and processes of isolation" in st_lower or "metallurgy" in st_lower or "calcination" in st_lower):
            return "General Principles and Processes of Isolation of Elements"

    # Specific common textbook aliases
    if subject == "Biology":
        if ("biotech" in words or "biotechnology" in words) and ("principles" in words or "principals" in words or "processes" in words):
            return "Biotechnology : Principles and Processes" if "Biotechnology : Principles and Processes" in SUBJECT_CHAPTERS.get(subject, []) else "Biotechnology - Principles and Processes"
        if ("variation" in words) or ("principal" in words or "principles" in words) or (("inhertance" in words or "inheritance" in words) and not "molecular" in words):
            return "Principles of Inheritance and Variation"

    if subject == "Chemistry":
        if ("general" in words or "isolation" in words or "metallurgy" in words) and ("principal" in words or "principles" in words or "elements" in words):
            return "General Principles and Processes of Isolation of Elements"

    if ("inhertance" in words or "inheritance" in words) and "molecular" in words:
        return "Molecular Basis of Inheritance"
    if "reproduction" in words and ("flower" in words or "flowering" in words or "sexual" in words):
        return "Sexual Reproduction in Flowering Plants"
    if "reproduction" in words and "human" in words:
        return "Human Reproduction"
    if "chemical" in words and ("coordination" in words or "integration" in words):
        return "Chemical Coordination and Integration"
    if "biological" in words and "classification" in words:
        return "Biological Classification"
    if "animal" in words and "kingdom" in words:
        return "Animal Kingdom"
    if "plant" in words and "kingdom" in words:
        return "Plant Kingdom"

    # Search against official chapters for the given subject
    chapters = SUBJECT_CHAPTERS.get(subject, [])
    best_match = None
    best_score = 0
    for ch in chapters:
        ch_words = set(re.findall(r"[a-z]+", ch.lower()))
        common = words.intersection(ch_words)
        score = len(common)
        if score > best_score:
            best_score = score
            best_match = ch

    if best_match and best_score >= 1:
        return best_match

    # Fallback: clean title-cased filename
    return fn_clean.title()


def get_uploaded_topics_for_subject(session: Optional[Session] = None, subject: str = "Biology") -> list[str]:
    """Return all unique mapped chapter topics from files uploaded for this subject.
    If the user has uploaded files recorded in IndexedFile, strictly use ONLY those files
    and ensure topics belong to the subject's official syllabus.
    """
    filenames: list[str] = []
    if session is not None:
        try:
            stmt = (
                select(IndexedFile.filename)
                .where(
                    IndexedFile.subject == subject,
                    IndexedFile.institution_id.is_(None),
                )
            )
            filenames = list(session.execute(stmt).scalars().all())
        except Exception:
            filenames = []

    # Only if NO files were ever uploaded in DB for this subject, fallback to data/textbooks
    if not filenames:
        from pathlib import Path
        tb_dir = Path("data/textbooks")
        if tb_dir.exists():
            for p in tb_dir.iterdir():
                if p.is_file():
                    filenames.append(p.name)

    official_chapters = SUBJECT_CHAPTERS.get(subject, [])
    topics: list[str] = []
    seen: set[str] = set()

    for fn in filenames:
        topic = match_filename_to_topic(fn, subject)
        if not topic or topic.lower() in seen or topic.lower() == "general":
            continue
        # Verify the topic matches an official syllabus chapter for this subject
        matched_official = None
        for ch in official_chapters:
            if is_topic_matching(topic, [ch]):
                matched_official = ch
                break
        if matched_official and matched_official.lower() not in seen:
            seen.add(matched_official.lower())
            topics.append(matched_official)
        elif not matched_official and is_topic_matching(topic, official_chapters):
            seen.add(topic.lower())
            topics.append(topic)

    return topics


def is_topic_matching(question_topic: Optional[str], allowed_topics: List[str]) -> bool:
    """Check if question_topic accurately matches any of the allowed topics.
    Prevents cross-topic leakage (e.g. 'Morphology of Flowering Plants' will NOT match
    'Sexual Reproduction in Flowering Plants').
    """
    if not question_topic or not allowed_topics:
        return False

    q_clean = question_topic.strip().lower()
    q_norm = re.sub(r"[^a-z0-9]", "", q_clean)
    for allowed in allowed_topics:
        a_clean = allowed.strip().lower()
        a_norm = re.sub(r"[^a-z0-9]", "", a_clean)
        if q_norm == a_norm:
            return True
        # Match if one contains the other as a whole phrase
        if a_clean in q_clean or q_clean in a_clean:
            return True

    return False

