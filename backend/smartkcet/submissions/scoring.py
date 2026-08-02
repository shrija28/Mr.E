"""Pure scoring helper for student submissions.

Implements the scoring contract that previously lived inline in
``backend/app.py``'s ``/analyze`` endpoint and is now also wired into
:mod:`smartkcet.routes.legacy`.  Both call sites use this single
function so behaviour stays identical between the legacy ``/analyze``
endpoint and the new role-scoped ``POST /api/student/submit`` endpoint
(task 8.1, REQ-9.3).

The function is intentionally pure: no DB, no side effects, no
network.  Persistence and idempotency are handled by the caller.

Input shape
-----------

``questions`` is a list of dicts with the following keys (extras are
ignored)::

    {
        "q":     str,                # question text
        "opts":  list[str],          # 4 MCQ options
        "ans":   int | str,          # canonical correct option (index or label)
        "topic": str,                # optional, defaults to "General"
        "marks": int,                # optional, defaults to 1
    }

``answers`` is a mapping from the question's stringified index to the
student's selected option (``"0"|"1"|"2"|"3"`` for MCQs, or ``""`` for
unanswered).  This matches the legacy ``ES.answers`` map produced by
``frontend/js/exam.js``.

Output shape
------------

The return value matches the legacy ``/analyze`` body verbatim, plus an
explicit ``topic_breakdown`` alias used by ``Submission.topic_breakdown``
so the persistence call site does not have to remember which of the
two equivalent keys to write::

    {
        "percentage":      int,
        "earned":          int,
        "total":           int,
        "topicScores":     dict[str, {"earned": int, "total": int}],
        "topic_breakdown": dict[str, {"earned": int, "total": int}],   # alias
        "typeScores":      dict[str, {"earned": int, "total": int}],
        "strong":          list[{"topic": str, "pct": int}],
        "canImprove":      list[{"topic": str, "pct": int}],
        "weak":            list[{"topic": str, "pct": int}],
        "questionResults": list[ ... per-question record ... ],
        "pass":            bool,
        "recommendation":  str,
    }

The 70 / 40 thresholds (strong vs. improve vs. weak) and the "Excellent /
Good / Needs improvement" recommendation prefixes mirror the legacy
behaviour and the contract documented in REQ-10.5.
"""

from __future__ import annotations

from typing import Any, Iterable, Mapping


# Bucket thresholds (REQ-10.5).
_STRONG_THRESHOLD = 70
_IMPROVE_THRESHOLD = 40

# Legacy /analyze pass mark.  Unchanged from app.py so the dashboard
# treats existing and new submissions identically.
_PASS_THRESHOLD = 40


def _pct(earned: int, total: int) -> int:
    """Round earned/total to a percentage, returning 0 when total is 0."""

    if total <= 0:
        return 0
    return round((earned / total) * 100)


def _normalised_marks(value: Any) -> int:
    """Coerce a question's ``marks`` field to a positive int (default 1)."""

    if isinstance(value, bool):  # bool is a subclass of int — exclude.
        return 1
    if isinstance(value, int) and value > 0:
        return value
    if isinstance(value, float) and value > 0:
        return int(value)
    return 1


def score_submission(
    questions: Iterable[Mapping[str, Any]],
    answers: Mapping[str, Any],
) -> dict[str, Any]:
    """Score one submission and return the full result envelope.

    See module docstring for input/output shape.
    """

    questions_list = list(questions)
    total = 0
    earned = 0
    topic_scores: dict[str, dict[str, int]] = {}
    type_scores: dict[str, dict[str, int]] = {}
    question_results: list[dict[str, Any]] = []

    for i, q in enumerate(questions_list):
        marks = _normalised_marks(q.get("marks"))
        total += marks

        topic = q.get("topic")
        if not isinstance(topic, str) or not topic.strip():
            topic = "General"

        topic_scores.setdefault(topic, {"earned": 0, "total": 0})["total"] += marks
        type_scores.setdefault("MCQ", {"earned": 0, "total": 0})["total"] += marks

        given = answers.get(str(i))

        # Classification rules carried over from legacy /analyze:
        #   - given is None / "" → unanswered (0 marks)
        #   - str(given) == str(q.ans) → correct (full marks)
        #   - else → wrong (0 marks)
        question_earned = 0
        if given is None or given == "":
            status = "unanswered"
        elif str(given) == str(q.get("ans")):
            question_earned = marks
            status = "correct"
        else:
            status = "wrong"

        earned += question_earned
        topic_scores[topic]["earned"] += question_earned
        type_scores["MCQ"]["earned"] += question_earned

        question_results.append(
            {
                "q": q.get("q"),
                "type": "MCQ",
                "topic": topic,
                "given": given,
                "correctAns": q.get("ans"),
                "earned": question_earned,
                "marks": marks,
                "status": status,
            }
        )

    percentage = _pct(earned, total)

    strong: list[dict[str, Any]] = []
    can_improve: list[dict[str, Any]] = []
    weak: list[dict[str, Any]] = []
    for topic_name, scores in topic_scores.items():
        topic_pct = _pct(scores["earned"], scores["total"])
        bucket = (
            strong
            if topic_pct >= _STRONG_THRESHOLD
            else can_improve
            if topic_pct >= _IMPROVE_THRESHOLD
            else weak
        )
        bucket.append({"topic": topic_name, "pct": topic_pct})

    if percentage >= 75:
        recommendation = "Excellent! "
    elif percentage >= 50:
        recommendation = "Good effort. "
    else:
        recommendation = "Needs improvement. "
    if weak:
        recommendation += f"Focus on: {', '.join(w['topic'] for w in weak)}."

    return {
        "percentage": percentage,
        "earned": earned,
        "total": total,
        "topicScores": topic_scores,
        # Alias for callers (notably ``Submission.topic_breakdown``) that
        # want a name aligned with the DB column.  The two keys point at
        # the same dict so updates stay in sync — but because the dict is
        # produced fresh per call, persistence callers can safely pass
        # either one to ``json.dumps`` without aliasing concerns.
        "topic_breakdown": topic_scores,
        "typeScores": type_scores,
        "strong": strong,
        "canImprove": can_improve,
        "weak": weak,
        "questionResults": question_results,
        "pass": percentage >= _PASS_THRESHOLD,
        "recommendation": recommendation,
    }


__all__ = ["score_submission"]
