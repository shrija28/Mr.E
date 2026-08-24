"""APIs for student rank suggestions using Flask Blueprint."""

from __future__ import annotations

import math
from typing import Any, Optional

from flask import Blueprint, jsonify, request
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..db.session import get_db
from ..middleware.rbac import require_student, current_user
from ..db.models import User, Submission, Exam, ExamSet
from ..db.subscription_models import Subscription, SubscriptionPlan
from ..leaderboard.service import get_leaderboard

router = Blueprint("student_rank_suggestions", __name__, url_prefix="/api/student")


def redact_string(s: str) -> str:
    words = s.split()
    redacted_words = []
    for word in words:
        if len(word) <= 2:
            redacted_words.append(word[0] + "*" * (len(word) - 1) if word else "")
        else:
            redacted_words.append(word[0] + "*" * (len(word) - 2) + word[-1])
    return " ".join(redacted_words)


def calculate_std_dev(scores: list[float]) -> float:
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

        score_pct_increase = composite_gap / 0.6
        if avg_score + score_pct_increase <= 100.0:
            suggestions.append(
                f"Assuming your attempt count and consistency remain constant, you need to increase your average score by approximately {score_pct_increase:.1f}% (raising your average from {avg_score:.1f}% to {avg_score + score_pct_increase:.1f}%)."
            )
        else:
            suggestions.append("In addition to improving accuracy, you should increase test volume to raise your consistency multiplier.")

    return suggestions


@router.route("/rank-suggestions", methods=["GET"])
@require_student
def get_rank_suggestions():
    db: Session = get_db()
    user = current_user(request, db)
    if not user:
        return jsonify({"error": "user_not_found", "message": "Authenticated user not found"}), 401

    raw_desired_rank = request.args.get("desired_rank")
    if not raw_desired_rank:
        return jsonify({"error": "validation_error", "message": "desired_rank query parameter is required"}), 400
    try:
        desired_rank = int(raw_desired_rank)
    except (ValueError, TypeError):
        return jsonify({"error": "validation_error", "message": "desired_rank must be an integer"}), 400

    if user.student_subtype == "institution_linked":
        is_locked = False
    else:
        active_sub = (
            db.query(Subscription)
            .join(SubscriptionPlan, Subscription.plan_id == SubscriptionPlan.id)
            .filter(
                Subscription.user_id == user.id,
                Subscription.status.in_(["active", "grace_period"]),
                ~SubscriptionPlan.name.in_(["Free", "Free Trial"]),
                SubscriptionPlan.price > 0,
            )
            .first()
        )
        is_locked = active_sub is None

    submissions = (
        db.query(Submission)
        .filter(Submission.user_id == user.id, Submission.status == "completed")
        .all()
    )
    attempts = len(submissions)

    if attempts == 0:
        return jsonify({
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
        }), 200

    scores = [sub.score_pct for sub in submissions]
    avg_score = sum(scores) / attempts
    std_dev = calculate_std_dev(scores)

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

    ranked = get_leaderboard(db)
    max_attempts_in_cohort = max((e.attempt_count for e in ranked), default=1)

    current_rank = None
    current_composite = 0.0

    for entry in ranked:
        if entry.student_id == str(user.id) or entry.kcet_student_id == user.kcet_student_id:
            current_rank = entry.rank
            current_composite = entry.composite_score
            break

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

    return jsonify({
        "current_rank": current_rank if current_rank is not None else "—",
        "desired_rank": desired_rank,
        "suggestions": suggestions,
    }), 200


__all__ = ["router"]
