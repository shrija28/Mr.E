"""Extract MCQ questions from text using pattern matching.

Looks for patterns like:
- "1. Question text\n  a) option1\n  b) option2\n  c) option3\n  d) option4"
- "Q1: Question text\n  A. option1\n  B. option2\n  C. option3\n  D. option4"
- Numbered questions with lettered options (A/B/C/D or a/b/c/d or 1/2/3/4)

Also handles KCET-style formats where answer keys may be at the end.

This module does NOT use any external AI/LLM APIs — it is purely
regex/pattern-based extraction.
"""

from __future__ import annotations

import logging
import re
from typing import List, Optional

logger = logging.getLogger("smartkcet.rag.mcq_extractor")


# ---------------------------------------------------------------------------
# Pattern-based MCQ extraction
# ---------------------------------------------------------------------------

# Matches question numbers like: "1.", "1)", "Q1.", "Q1:", "Q.1", "Q 1."
_Q_NUM_RE = re.compile(
    r"^(?:Q\.?\s*)?(\d{1,3})\s*[.):\-]\s*",
    re.IGNORECASE,
)

# Matches option lines like: "a)", "A.", "(A)", "(a)", "a.", "A)"
_OPT_RE = re.compile(
    r"^\s*(?:\(?([A-Da-d])\)?[.):\-]\s*|([A-Da-d])\s*[.):\-]\s*)",
)

# Matches numbered option lines like: "1)", "1.", "(1)"
_OPT_NUM_RE = re.compile(
    r"^\s*(?:\(?([1-4])\)?[.):\-]\s*|([1-4])\s*[.):\-]\s*)",
)

# Answer key patterns: "1-A", "1. A", "1) A", "Ans: A"
_ANS_KEY_RE = re.compile(
    r"(?:^|\n)\s*(\d{1,3})\s*[.):\-]\s*([A-Da-d1-4])\b",
)

# Single-line answer pattern: "Answer: A" or "Ans: B" or "Correct: C"
_INLINE_ANS_RE = re.compile(
    r"(?:answer|ans|correct)\s*[:=]\s*([A-Da-d1-4])\b",
    re.IGNORECASE,
)


def _option_index(letter: str) -> int:
    """Convert A/B/C/D or 1/2/3/4 to 0-based index."""
    letter = letter.upper()
    if letter in "ABCD":
        return ord(letter) - ord("A")
    if letter in "1234":
        return int(letter) - 1
    return 0


def _extract_answer_keys(text: str) -> dict[int, int]:
    """Try to find an answer key section at the end of the text.

    Returns a mapping of question_number → correct_option_index (0-based).
    """
    # Look for answer key sections (often at the end)
    answer_section_markers = [
        r"answer\s*key",
        r"answers?\s*:",
        r"key\s*:",
        r"solution",
    ]
    marker_pattern = re.compile(
        "|".join(answer_section_markers), re.IGNORECASE
    )

    keys: dict[int, int] = {}

    # Find the answer key section
    match = marker_pattern.search(text)
    if match:
        answer_text = text[match.start():]
        for m in _ANS_KEY_RE.finditer(answer_text):
            q_num = int(m.group(1))
            ans_letter = m.group(2)
            keys[q_num] = _option_index(ans_letter)

    return keys


def extract_mcqs_from_text(text: str, topic: str = "General") -> List[dict]:
    """Extract structured MCQ questions from raw text.

    Returns a list of dicts:
        [{"q": "...", "opts": ["A", "B", "C", "D"], "ans": 0, "topic": "General"}]

    The extractor handles various numbering and option styles commonly
    found in KCET and other competitive exam papers.
    """
    if not text or not text.strip():
        return []

    questions: List[dict] = []
    lines = text.split("\n")

    # First pass: try to find answer keys
    answer_keys = _extract_answer_keys(text)

    # Second pass: extract questions and options
    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Try to match a question number
        q_match = _Q_NUM_RE.match(line)
        if not q_match:
            i += 1
            continue

        q_num = int(q_match.group(1))
        # Extract question text (everything after the number on this line)
        q_text = line[q_match.end():].strip()

        # Question text might span multiple lines until we hit an option
        i += 1
        while i < len(lines):
            next_line = lines[i].strip()
            if not next_line:
                i += 1
                continue
            # Check if this line is an option
            if _OPT_RE.match(next_line) or _OPT_NUM_RE.match(next_line):
                break
            # Check if this is a new question
            if _Q_NUM_RE.match(next_line):
                break
            # Otherwise it's continuation of the question text
            q_text += " " + next_line
            i += 1

        if not q_text.strip():
            continue

        # Now try to collect 4 options
        options: List[str] = []
        inline_answer: Optional[int] = None

        while i < len(lines) and len(options) < 4:
            opt_line = lines[i].strip()
            if not opt_line:
                i += 1
                continue

            opt_match = _OPT_RE.match(opt_line)
            if opt_match:
                letter = opt_match.group(1) or opt_match.group(2)
                opt_text = opt_line[opt_match.end():].strip()
                options.append(opt_text)
                i += 1
                continue

            opt_num_match = _OPT_NUM_RE.match(opt_line)
            if opt_num_match:
                opt_text = opt_line[opt_num_match.end():].strip()
                options.append(opt_text)
                i += 1
                continue

            # Check for inline answer on this line
            ans_match = _INLINE_ANS_RE.search(opt_line)
            if ans_match and len(options) == 4:
                inline_answer = _option_index(ans_match.group(1))
                i += 1
                break

            # Not an option line — stop collecting
            break

        # We need exactly 4 options for a valid MCQ
        if len(options) != 4:
            continue

        # Check for inline answer in the lines immediately after options
        if inline_answer is None:
            # Check next few lines for an answer indicator
            lookahead = min(i + 3, len(lines))
            for j in range(i, lookahead):
                ans_match = _INLINE_ANS_RE.search(lines[j])
                if ans_match:
                    inline_answer = _option_index(ans_match.group(1))
                    break

        # Determine the correct answer
        correct_ans = 0  # Default to first option if unknown
        if inline_answer is not None:
            correct_ans = inline_answer
        elif q_num in answer_keys:
            correct_ans = answer_keys[q_num]

        questions.append({
            "q": q_text.strip(),
            "opts": options,
            "ans": correct_ans,
            "topic": topic,
            "exp": "",
        })

    logger.info(
        "Pattern extraction found %d MCQs from text (%d chars)",
        len(questions),
        len(text),
    )
    return questions


# ---------------------------------------------------------------------------
# Fallback: generate simple questions from text content
# ---------------------------------------------------------------------------


def _split_sentences(text: str) -> List[str]:
    """Split text into sentences, filtering out very short ones."""
    # Simple sentence splitter
    sentences = re.split(r"[.!?]+\s+", text)
    # Filter: keep sentences that are informative (not too short, not too long)
    return [
        s.strip()
        for s in sentences
        if 20 < len(s.strip()) < 300 and not s.strip().startswith(("http", "www"))
    ]


def _generate_distractors(correct: str, all_facts: List[str], idx: int) -> List[str]:
    """Generate 3 distractor options from other facts in the text."""
    distractors = []
    # Pick other sentences as distractors
    for j, fact in enumerate(all_facts):
        if j == idx:
            continue
        # Truncate long facts
        distractor = fact[:80] if len(fact) > 80 else fact
        distractors.append(distractor)
        if len(distractors) >= 3:
            break

    # If we don't have enough distractors, create generic ones
    generic = [
        "None of the above",
        "All of the above",
        "Cannot be determined",
        "Not applicable",
    ]
    while len(distractors) < 3:
        distractors.append(generic[len(distractors)])

    return distractors[:3]


def generate_fallback_mcqs(text: str, topic: str = "General", max_questions: int = 20) -> List[dict]:
    """Generate simple MCQ questions from text content when no structured MCQs are found.

    Creates "Which of the following statements is correct?" style questions
    using key sentences from the text as correct answers and other sentences
    as distractors.

    This is a best-effort fallback — questions won't be as polished as
    human-written or AI-generated ones, but they provide a usable question
    bank from any uploaded content.
    """
    if not text or not text.strip():
        return []

    sentences = _split_sentences(text)
    if len(sentences) < 4:
        logger.info("Not enough sentences for fallback MCQ generation (%d found)", len(sentences))
        return []

    questions: List[dict] = []
    used_sentences: set = set()

    for i, sentence in enumerate(sentences):
        if len(questions) >= max_questions:
            break

        # Skip if we've already used this sentence
        if sentence in used_sentences:
            continue
        used_sentences.add(sentence)

        # Create the correct answer (truncate if needed)
        correct = sentence[:100] if len(sentence) > 100 else sentence

        # Generate distractors from other sentences
        distractors = _generate_distractors(correct, sentences, i)

        # Build options with correct answer at a varying position
        correct_pos = i % 4  # Rotate correct answer position
        opts = list(distractors)  # Start with 3 distractors
        opts.insert(correct_pos, correct)

        # Create the question
        # Extract a key phrase for the question stem
        q_text = f"Which of the following is correct regarding the topic?"
        if len(sentence) > 50:
            # Try to create a more specific question from the sentence
            words = sentence.split()
            if len(words) > 5:
                # Use first few words as context
                context_words = " ".join(words[:4])
                q_text = f"Which statement about '{context_words}...' is correct?"

        questions.append({
            "q": q_text,
            "opts": opts,
            "ans": correct_pos,
            "topic": topic,
            "exp": "",
        })

    logger.info(
        "Fallback generation produced %d MCQs from %d sentences",
        len(questions),
        len(sentences),
    )
    return questions


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def extract_or_generate_mcqs(
    text: str,
    topic: str = "General",
    min_questions: int = 20,
) -> List[dict]:
    """Extract MCQs from text; fall back to generation if too few are found.

    1. First tries pattern-based extraction (for structured exam papers).
    2. If fewer than ``min_questions`` are found, supplements with
       fallback-generated questions from the text content.

    Returns a combined list of question dicts.
    """
    # Try structured extraction first
    extracted = extract_mcqs_from_text(text, topic=topic)

    if len(extracted) >= min_questions:
        logger.info(
            "Extracted %d MCQs (meets minimum of %d), no fallback needed",
            len(extracted),
            min_questions,
        )
        return extracted

    # Need more questions — generate from text content
    needed = min_questions - len(extracted)
    logger.info(
        "Only %d MCQs extracted (need %d), generating %d fallback questions",
        len(extracted),
        min_questions,
        needed,
    )
    fallback = generate_fallback_mcqs(text, topic=topic, max_questions=needed)

    combined = extracted + fallback
    logger.info("Total MCQs after fallback: %d", len(combined))
    return combined


__all__ = [
    "extract_mcqs_from_text",
    "generate_fallback_mcqs",
    "extract_or_generate_mcqs",
]
