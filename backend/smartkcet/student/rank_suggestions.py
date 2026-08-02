"""APIs for student rank suggestions."""

from __future__ import annotations

import math
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query, Request, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..db.session import get_session
from ..middleware.rbac import require_student, current_user
from ..db.models import User, Submission, Exam, ExamSet
from ..db.subscription_models import Subscription, SubscriptionPlan
from ..leaderboard.service import get_leaderboard

router = APIRouter()


def redact_string(s: str) -> str:
    """Obscure/redact words in a string, preserving first and last characters."""
    words = s.split()
    redacted_words = []
    for word in words:
        if len(word) <= 2:
            redacted_words.append(word[0] + "*" * (len(word) - 1) if word else "")
        else:
            redacted_words.append(word[0] + "*" * (len(word) - 2) + word[-1])
    return " ".join(redacted_words)


def calculate_std_dev(scores: list[float]) -> float:
    """Compute the population standard deviation of scores."""
    if len(scores) < 2:
        return 0.0
    mean = sum(scores) / len(scores)
    variance = sum((s - mean) ** 2 for s in scores) / len(scores)
    return math.sqrt(variance)


def generate_personalized_suggestions(
    current_rank: Optional[int],
    desired_rank: int,
    avg_score: float,
    attempts: int,
    scores: list[float],
    std_dev: float,
    subject_scores: dict[str, float],
    weak_topics: list[tuple[str, float]],
    max_attempts_in_cohort: int,
    current_composite: float,
    target_composite: float,
    is_locked: bool
) -> list[str]:
    suggestions = []

    if attempts == 0:
        suggestions.append("No exam history found. Complete at least one mock exam to generate rank suggestions.")
        if is_locked:
            suggestions.append("🔒 Upgrade to Pro to unlock detailed analytics and personalized weak-topic breakdowns.")
        return suggestions

    if current_rank is None:
        suggestions.append(f"Your current average score of {avg_score:.1f}% is below the leaderboard eligibility threshold of 30.0%.")
        suggestions.append("Complete another exam and aim for at least 30% to appear on the leaderboard.")
        if is_locked:
            redacted = []
            for item in suggestions:
                redacted_words = []
                for word in item.split():
                    if word.startswith("**") and word.endswith("**"):
                        clean_word = word[2:-2]
                        redacted_words.append("**" + redact_string(clean_word) + "**")
                    elif "%" in word or any(char.isdigit() for char in word):
                        redacted_words.append(word)
                    else:
                        redacted_words.append(redact_string(word))
                redacted.append(" ".join(redacted_words))
            suggestions = redacted
            suggestions.append("🔒 Upgrade to Pro to unlock detailed analytics and personalized weak-topic breakdowns.")
        return suggestions

    if current_rank <= desired_rank:
        suggestions.append(f"🎉 Great job! Your current rank ({current_rank}) is already better than or equal to your desired rank ({desired_rank}).")
        suggestions.append("To maintain this rank, continue taking exams regularly and keep your consistency score high.")
        suggestions.append("Focus on weak areas to challenge for an even higher rank!")
    else:
        composite_gap = target_composite - current_composite
        suggestions.append(
            f"To improve your rank from {current_rank} to {desired_rank}, you need to close a composite score gap of {composite_gap:.2f} points."
        )

        # Average score gap
        score_pct_increase = composite_gap / 0.6
        if avg_score + score_pct_increase <= 100.0:
            suggestions.append(
                f"Assuming your attempt count and consistency remain constant, you need to increase your average score by approximately {score_pct_increase:.1f}% (raising your average from {avg_score:.1f}% to {avg_score + score_pct_increase:.1f}%)."
            )
        else:
            suggestions.append(
                "To close this gap, you will need to improve both your average score and your attempt frequency, as a score-only improvement is not mathematically sufficient."
            )

        # Normalized attempts improvement
        if attempts < max_attempts_in_cohort:
            attempt_boost = (1.0 / max_attempts_in_cohort) * 100.0 * 0.2
            suggestions.append(
                f"Increase your exam attempts: Each new exam attempt will increase your composite score by approximately {attempt_boost:.2f} points (by improving your normalized attempt score)."
            )

        # Consistency improvement
        if attempts > 1 and std_dev > 15.0:
            suggestions.append(
                f"Work on consistency: Your standard deviation of scores is {std_dev:.1f}%. Stabilizing your exam scores will improve your consistency score and boost your rank."
            )

        # Weakest subject focus
        weakest_subject = None
        weakest_score = 101.0
        for subj, score in subject_scores.items():
            if score < weakest_score:
                weakest_score = score
                weakest_subject = subj

        if weakest_subject:
            suggestions.append(
                f"Focus on your weakest subject: **{weakest_subject}** (currently averaging {weakest_score:.1f}%). Aim to bring this subject's score closer to {max(30.0, avg_score + 10.0):.1f}%."
            )

        # Weak topics focus
        if weak_topics:
            top_weak = [f"'{t[0]}' ({t[1]:.1f}%)" for t in weak_topics[:2]]
            suggestions.append(
                f"Focus on improving your scores in these weak topics: {', '.join(top_weak)}."
            )
        else:
            if weakest_subject:
                suggestions.append(
                    f"We recommend taking at least 3 more mock tests focusing on **{weakest_subject}**."
                )

    if is_locked:
        redacted = []
        for item in suggestions:
            redacted_words = []
            for word in item.split():
                if word.startswith("**") and word.endswith("**"):
                    clean_word = word[2:-2]
                    redacted_words.append("**" + redact_string(clean_word) + "**")
                elif "%" in word or any(char.isdigit() for char in word):
                    redacted_words.append(word)
                else:
                    redacted_words.append(redact_string(word))
            redacted.append(" ".join(redacted_words))
        suggestions = redacted
        suggestions.append("🔒 Upgrade to Pro to unlock detailed analytics and personalized weak-topic breakdowns.")

    return suggestions


@router.get("/rank-suggestions")
def get_rank_suggestions(
    request: Request,
    desired_rank: int = Query(..., description="The desired rank for suggestions."),
    payload: dict[str, Any] = Depends(require_student),
    db: Session = Depends(get_session),
):
    """
    Provide personalized suggestions to a student on how to achieve a desired rank.
    """
    user = current_user(request, db)
    if not user:
        raise HTTPException(
            status_code=401,
            detail={"error": "user_not_found", "message": "Authenticated user not found"},
        )

    # 1. Fetch user subscription gating state
    if user.student_subtype == "institution_linked":
        is_locked = False
    else:
        active_sub = (
            db.query(Subscription)
            .join(SubscriptionPlan, Subscription.plan_id == SubscriptionPlan.id)
            .filter(
                Subscription.user_id == user.id,
                Subscription.status.in_(["active", "grace_period"]),
                SubscriptionPlan.name != "Free",
            )
            .first()
        )
        is_locked = active_sub is None

    # 2. Fetch completed submissions for user to calculate stats
    submissions = (
        db.query(Submission)
        .filter(Submission.user_id == user.id, Submission.status == "completed")
        .all()
    )
    attempts = len(submissions)

    # 3. Handle 0 attempts early
    if attempts == 0:
        return {
            "current_rank": "—",
            "desired_rank": desired_rank,
            "suggestions": generate_personalized_suggestions(
                current_rank=None,
                desired_rank=desired_rank,
                avg_score=0.0,
                attempts=0,
                scores=[],
                std_dev=0.0,
                subject_scores={},
                weak_topics=[],
                max_attempts_in_cohort=1,
                current_composite=0.0,
                target_composite=0.0,
                is_locked=is_locked
            )
        }

    scores = [sub.score_pct for sub in submissions]
    avg_score = sum(scores) / attempts
    std_dev = calculate_std_dev(scores)

    # Subject averages
    subject_rows = (
        db.query(
            Exam.subject,
            func.avg(Submission.score_pct).label("avg_score")
        )
        .join(ExamSet, Submission.exam_set_id == ExamSet.id)
        .join(Exam, ExamSet.exam_id == Exam.id)
        .filter(Submission.user_id == user.id, Submission.status == "completed")
        .group_by(Exam.subject)
        .all()
    )
    subject_scores = {row.subject: float(row.avg_score) for row in subject_rows}

    # Weak topics calculation from aggregated breakdown
    topic_aggregates = {}
    for sub in submissions:
        breakdown = sub.topic_breakdown
        if isinstance(breakdown, dict):
            for topic, stats in breakdown.items():
                if isinstance(stats, dict) and "earned" in stats and "total" in stats:
                    if topic not in topic_aggregates:
                        topic_aggregates[topic] = {"earned": 0, "total": 0}
                    topic_aggregates[topic]["earned"] += stats["earned"]
                    topic_aggregates[topic]["total"] += stats["total"]

    weak_topics = []
    for topic, stats in topic_aggregates.items():
        if stats["total"] > 0:
            pct = (stats["earned"] / stats["total"]) * 100
            if pct < 60:
                weak_topics.append((topic, pct))
    weak_topics.sort(key=lambda x: x[1])

    # 4. Leaderboard positioning
    ranked = get_leaderboard(db)
    max_attempts_in_cohort = max((e.attempt_count for e in ranked), default=1)

    my_entry = None
    current_rank = None
    current_composite = 0.0

    for entry in ranked:
        if entry.student_id == str(user.id) or entry.kcet_student_id == user.kcet_student_id:
            my_entry = entry
            current_rank = entry.rank
            current_composite = entry.composite_score
            break

    # Determine target composite
    if not ranked:
        target_composite = 80.0
    elif desired_rank <= len(ranked):
        target_composite = ranked[desired_rank - 1].composite_score
    else:
        target_composite = ranked[-1].composite_score

    suggestions = generate_personalized_suggestions(
        current_rank=current_rank,
        desired_rank=desired_rank,
        avg_score=avg_score,
        attempts=attempts,
        scores=scores,
        std_dev=std_dev,
        subject_scores=subject_scores,
        weak_topics=weak_topics,
        max_attempts_in_cohort=max_attempts_in_cohort,
        current_composite=current_composite,
        target_composite=target_composite,
        is_locked=is_locked
    )

    return {
        "current_rank": current_rank if current_rank is not None else "—",
        "desired_rank": desired_rank,
        "suggestions": suggestions,
    }
