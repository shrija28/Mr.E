"""Student college recommendations endpoint using Flask Blueprint."""

from __future__ import annotations

import logging
from typing import Any, Dict
from flask import Blueprint, jsonify, request
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..db.models import Submission, User, Exam, ExamSet
from ..db.session import get_db
from ..db.subscription_models import Subscription, SubscriptionPlan
from ..middleware.rbac import require_student, current_user

router = Blueprint("student_recommendations", __name__, url_prefix="/api/student")
logger = logging.getLogger("smartkcet.student.recommendations")

COLLEGES = [
    {"name": "RV College of Engineering (RVCE)", "location": "Bangalore", "tier": 1, "cutoff_rank": 1200, "description": "Preeminent engineering college in Karnataka, known for exceptional placements and academic rigor."},
    {"name": "PES University (PESU)", "location": "Bangalore", "tier": 1, "cutoff_rank": 2000, "description": "Top-tier private university with highly competitive computer science and engineering programs."},
    {"name": "BMS College of Engineering (BMSCE)", "location": "Bangalore", "tier": 1, "cutoff_rank": 3200, "description": "One of India's oldest and most prestigious private-aided colleges, offering excellent infrastructure."},
    {"name": "M.S. Ramaiah Institute of Technology (MSRIT)", "location": "Bangalore", "tier": 1, "cutoff_rank": 4000, "description": "Highly reputed institution offering robust research centers and stellar placements."},
    {"name": "Bangalore Institute of Technology (BIT)", "location": "Bangalore", "tier": 1, "cutoff_rank": 6000, "description": "Pioneered computer science education in Karnataka with a strong central campus and alumni network."},
    {"name": "Dayananda Sagar College of Engineering (DSCE)", "location": "Bangalore", "tier": 2, "cutoff_rank": 12000, "description": "Autonomous college with a massive campus, active technical clubs, and diverse specializations."},
    {"name": "Nitte Meenakshi Institute of Technology (NMIT)", "location": "Bangalore", "tier": 2, "cutoff_rank": 18000, "description": "Autonomous institute with multi-disciplinary research funding, design projects, and global tie-ups."},
    {"name": "Sir M. Visvesvaraya Institute of Technology (Sir MVIT)", "location": "Bangalore", "tier": 2, "cutoff_rank": 20000, "description": "Renowned for its spacious campus, sports facilities, and strong core engineering departments."},
    {"name": "R.N.S. Institute of Technology (RNSIT)", "location": "Bangalore", "tier": 2, "cutoff_rank": 22000, "description": "Disciplined academic environment producing excellent VTU ranks and consistent placement metrics."},
    {"name": "JSS Science and Technology University (SJCE)", "location": "Mysore", "tier": 2, "cutoff_rank": 15000, "description": "Premier university in Mysore with a legacy of engineering excellence."},
]


def redact_string(val: str) -> str:
    if not val:
        return val
    words = val.split()
    redacted_words = ["█" * max(len(w), 3) for w in words]
    return " ".join(redacted_words)


def map_score_to_rank_and_tier(avg_score: float):
    if avg_score >= 85.0:
        return 1000, "1 - 1,500", "Tier 1"
    elif avg_score >= 70.0:
        return 4500, "1,500 - 8,000", "Tier 1/2"
    elif avg_score >= 55.0:
        return 14000, "8,000 - 20,000", "Tier 2"
    elif avg_score >= 40.0:
        return 28000, "20,000 - 45,000", "Tier 3"
    else:
        return 55000, "45,000+", "Tier 3"


def calculate_match_type(projected_rank: int, cutoff_rank: int) -> str:
    if projected_rank <= cutoff_rank:
        return "target"
    elif projected_rank <= cutoff_rank * 1.3:
        return "safe"
    else:
        return "reach"


@router.route("/college-recommendations", methods=["GET"])
@require_student
def get_college_recommendations():
    db: Session = get_db()
    user = current_user(request, db)
    if not user:
        return jsonify({"error": "user_not_found", "message": "Authenticated user not found"}), 401

    submissions = (
        db.query(Submission.score_pct)
        .filter(Submission.user_id == user.id, Submission.status == "completed")
        .all()
    )

    if not submissions:
        return jsonify({
            "no_data": True,
            "message": "Complete at least one exam to generate college recommendations.",
        }), 200

    total_score = sum(float(sub.score_pct) for sub in submissions)
    avg_score = round(total_score / len(submissions), 2)

    projected_rank, rank_range, student_tier = map_score_to_rank_and_tier(avg_score)

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

    targets, reaches, safes = [], [], []

    for col in COLLEGES:
        match_type = calculate_match_type(projected_rank, col["cutoff_rank"])
        name, location, description = col["name"], col["location"], col["description"]
        
        if is_locked:
            name = redact_string(name)
            location = redact_string(location)
            description = redact_string(description)

        col_data = {
            "name": name,
            "location": location,
            "tier": col["tier"],
            "cutoff_rank": col["cutoff_rank"],
            "description": description,
        }

        if match_type == "target":
            targets.append(col_data)
        elif match_type == "reach":
            reaches.append(col_data)
        else:
            safes.append(col_data)

    return jsonify({
        "no_data": False,
        "is_locked": is_locked,
        "average_score": avg_score,
        "projected_rank_range": rank_range,
        "student_tier": student_tier,
        "lock_message": (
            "Upgrade to the Pro Plan to unlock the full names, locations, and details of your recommended colleges."
            if is_locked else None
        ),
        "matches": {"target": targets, "reach": reaches, "safe": safes},
        "counts": {"target": len(targets), "reach": len(reaches), "safe": len(safes)}
    }), 200


@router.route("/rank-booster-suggestions", methods=["GET"])
@require_student
def get_rank_booster_suggestions():
    db: Session = get_db()
    user = current_user(request, db)
    if not user:
        return jsonify({"error": "user_not_found", "message": "Authenticated user not found"}), 401

    raw_target_rank = request.args.get("target_rank", 5000)
    try:
        target_rank = int(raw_target_rank)
    except (ValueError, TypeError):
        target_rank = 5000

    submissions_query = (
        db.query(
            func.count(Submission.id).label("attempts"),
            func.avg(Submission.score_pct).label("avg_score"),
            func.avg(Submission.time_taken_sec).label("avg_time")
        )
        .filter(Submission.user_id == user.id, Submission.status == "completed")
        .first()
    )

    if not submissions_query or submissions_query.attempts == 0:
        return jsonify({
            "no_data": True,
            "message": "Complete at least one exam to receive personalized study suggestions.",
        }), 200

    attempts = int(submissions_query.attempts)
    current_avg = round(float(submissions_query.avg_score), 2)
    avg_time = round(float(submissions_query.avg_time), 1)

    if target_rank <= 1000:
        target_score, target_label = 90.0, "Top 1,000 (Tier 1)"
    elif target_rank <= 5000:
        target_score, target_label = 80.0, "Top 5,000 (Tier 1)"
    elif target_rank <= 15000:
        target_score, target_label = 65.0, "Top 15,000 (Tier 2)"
    else:
        target_score, target_label = 50.0, "Top 30,000 (Tier 3)"

    score_gap = round(max(0.0, target_score - current_avg), 2)

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

    subject_scores = {row.subject: round(float(row.avg_score), 2) for row in subject_rows}
    weakest_subject, weakest_score = None, 101.0
    for subj, score in subject_scores.items():
        if score < weakest_score:
            weakest_score, weakest_subject = score, subj

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

    action_items = []
    if score_gap == 0:
        action_items.append(f"🎉 Keep it up! Your current average of {current_avg}% is already on track to achieve {target_label}.")
        action_items.append("Take more exams periodically to maintain consistency.")
    else:
        if weakest_subject:
            action_items.append(f"Target your weakest subject: **{weakest_subject}** (currently average {weakest_score}%). Focus on raising this to at least {target_score}%.")
        if attempts < 3:
            action_items.append(f"Increase attempt count: You have taken {attempts} exam(s). Complete at least {3 - attempts} more sets.")
        if avg_time > 45 * 60:
            m = int(avg_time // 60)
            action_items.append(f"Increase speed: Your average time per exam is {m} minutes. Aim for under 40 minutes per set.")
        else:
            action_items.append("Maintain timing: Your average pace is excellent.")

    if is_locked:
        redacted_items = []
        for item in action_items:
            redacted_words = []
            for word in item.split():
                if word.startswith("**") and word.endswith("**"):
                    clean_word = word[2:-2]
                    redacted_words.append("**" + redact_string(clean_word) + "**")
                elif "%" in word or any(char.isdigit() for char in word):
                    redacted_words.append(word)
                else:
                    redacted_words.append(redact_string(word))
            redacted_items.append(" ".join(redacted_words))
        action_items = redacted_items

    return jsonify({
        "no_data": False,
        "is_locked": is_locked,
        "current_average_score": current_avg,
        "required_average_score": target_score,
        "score_gap": score_gap,
        "target_label": target_label,
        "weakest_subject": weakest_subject,
        "weakest_subject_score": weakest_score if weakest_subject else None,
        "action_items": action_items,
        "lock_message": (
            "Upgrade to the Pro Plan to unlock personalized study strategies and rank booster action items."
            if is_locked else None
        )
    }), 200


__all__ = ["router"]
