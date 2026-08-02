"""Student college recommendations endpoint.

Provides GET /api/student/college-recommendations.
Analyzes user's exam submissions, projects their KCET rank range, and dynamically 
recommends colleges categorized as Target, Reach, and Safe.
Direct students on a Free Trial receive a redacted preview of the recommendations,
while Pro and Institutional students get full access.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List
from uuid import UUID

from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..db.models import Submission, User, Exam, ExamSet
from ..db.session import get_async_session as get_session
from ..db.subscription_models import Subscription, SubscriptionPlan
from ..middleware.rbac import require_student, current_user
from ..subscription.dependencies import get_access_control

router = APIRouter()
logger = logging.getLogger("smartkcet.student.recommendations")

# A realistic catalog of 19 major Karnataka engineering colleges.
COLLEGES = [
    # Tier 1
    {
        "name": "RV College of Engineering (RVCE)",
        "location": "Bangalore",
        "tier": 1,
        "cutoff_rank": 1200,
        "description": "Preeminent engineering college in Karnataka, known for exceptional placements and academic rigor.",
    },
    {
        "name": "PES University (PESU)",
        "location": "Bangalore",
        "tier": 1,
        "cutoff_rank": 2000,
        "description": "Top-tier private university with highly competitive computer science and engineering programs.",
    },
    {
        "name": "BMS College of Engineering (BMSCE)",
        "location": "Bangalore",
        "tier": 1,
        "cutoff_rank": 3200,
        "description": "One of India's oldest and most prestigious private-aided colleges, offering excellent infrastructure.",
    },
    {
        "name": "M.S. Ramaiah Institute of Technology (MSRIT)",
        "location": "Bangalore",
        "tier": 1,
        "cutoff_rank": 4000,
        "description": "Highly reputed institution offering robust research centers and stellar placements.",
    },
    {
        "name": "Bangalore Institute of Technology (BIT)",
        "location": "Bangalore",
        "tier": 1,
        "cutoff_rank": 6000,
        "description": "Pioneered computer science education in Karnataka with a strong central campus and alumni network.",
    },
    # Tier 2
    {
        "name": "Dayananda Sagar College of Engineering (DSCE)",
        "location": "Bangalore",
        "tier": 2,
        "cutoff_rank": 12000,
        "description": "Autonomous college with a massive campus, active technical clubs, and diverse specializations.",
    },
    {
        "name": "Nitte Meenakshi Institute of Technology (NMIT)",
        "location": "Bangalore",
        "tier": 2,
        "cutoff_rank": 18000,
        "description": "Autonomous institute with multi-disciplinary research funding, design projects, and global tie-ups.",
    },
    {
        "name": "Sir M. Visvesvaraya Institute of Technology (Sir MVIT)",
        "location": "Bangalore",
        "tier": 2,
        "cutoff_rank": 20000,
        "description": "Renowned for its spacious campus, sports facilities, and strong core engineering departments.",
    },
    {
        "name": "R.N.S. Institute of Technology (RNSIT)",
        "location": "Bangalore",
        "tier": 2,
        "cutoff_rank": 22000,
        "description": "Disciplined academic environment producing excellent VTU ranks and consistent placement metrics.",
    },
    {
        "name": "JSS Science and Technology University (SJCE)",
        "location": "Mysore",
        "tier": 2,
        "cutoff_rank": 15000,
        "description": "One of Mysore's premium technical campuses with deep research focus and legacy.",
    },
    # Tier 3
    {
        "name": "CMR Institute of Technology (CMRIT)",
        "location": "Bangalore",
        "tier": 3,
        "cutoff_rank": 30000,
        "description": "Vibrant campus culture with decent IT and core engineering placement opportunities.",
    },
    {
        "name": "MVJ College of Engineering (MVJCE)",
        "location": "Bangalore",
        "tier": 3,
        "cutoff_rank": 35000,
        "description": "Offers diverse engineering disciplines with well-equipped laboratories and workshop blocks.",
    },
    {
        "name": "The Oxford College of Engineering (TOCE)",
        "location": "Bangalore",
        "tier": 3,
        "cutoff_rank": 40000,
        "description": "Centrally located in HSR Layout, convenient for industrial training and startup interactions.",
    },
    {
        "name": "Don Bosco Institute of Technology (DBIT)",
        "location": "Bangalore",
        "tier": 3,
        "cutoff_rank": 45000,
        "description": "Offers solid curriculum frameworks aligned with VTU guidelines and structured training cells.",
    },
    {
        "name": "Acharya Institute of Technology (AIT)",
        "location": "Bangalore",
        "tier": 3,
        "cutoff_rank": 32000,
        "description": "Large international student cohort with outstanding sports infrastructure and design labs.",
    },
    # Tier 4
    {
        "name": "East West Institute of Technology (EWIT)",
        "location": "Bangalore",
        "tier": 4,
        "cutoff_rank": 60000,
        "description": "Affordable technical programs offering standard undergraduate paths in west Bangalore.",
    },
    {
        "name": "HKBK College of Engineering",
        "location": "Bangalore",
        "tier": 4,
        "cutoff_rank": 55000,
        "description": "Modern infrastructure with growing placement associations and technical hackathons.",
    },
    {
        "name": "Rajiv Gandhi Institute of Technology (RGIT)",
        "location": "Bangalore",
        "tier": 4,
        "cutoff_rank": 70000,
        "description": "Offers undergraduate programs with focused guidance and basic lab modules.",
    },
    {
        "name": "Cambridge Institute of Technology (CIT)",
        "location": "Bangalore",
        "tier": 4,
        "cutoff_rank": 50000,
        "description": "Autonomous college showing rapid growth in VTU results, placements, and innovation centers.",
    },
]


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


def map_score_to_rank_and_tier(score: float) -> tuple[int, str, str]:
    """Map average score percentage (0-100) to projected rank and display values.
    
    Returns:
        (projected_rank, rank_range_string, student_tier_string)
    """
    if score >= 90:
        # 90-100% maps to rank 100-2500
        projected_rank = int(100 + (100 - score) * 240)
        rank_range = f"{max(1, projected_rank - 200):,} - {projected_rank + 200:,}"
        student_tier = "Tier 1"
    elif score >= 75:
        # 75-90% maps to rank 2500-8000
        projected_rank = int(2500 + (90 - score) * 366.6)
        rank_range = f"{projected_rank - 1000:,} - {projected_rank + 1000:,}"
        student_tier = "Tier 2"
    elif score >= 60:
        # 60-75% maps to rank 8000-20000
        projected_rank = int(8000 + (75 - score) * 800)
        rank_range = f"{projected_rank - 2500:,} - {projected_rank + 2500:,}"
        student_tier = "Tier 2"
    elif score >= 45:
        # 45-60% maps to rank 20000-45000
        projected_rank = int(20000 + (60 - score) * 1666.6)
        rank_range = f"{projected_rank - 4000:,} - {projected_rank + 4000:,}"
        student_tier = "Tier 3"
    else:
        # < 45% maps to rank 45000-100000
        projected_rank = int(45000 + (45 - score) * 1222.2)
        rank_range = f"{projected_rank - 8000:,} - {min(100000, projected_rank + 8000):,}"
        student_tier = "Tier 4"
        
    return projected_rank, rank_range, student_tier


def calculate_match_type(projected_rank: int, cutoff_rank: int) -> str:
    """Categorize college match type based on projected rank and cutoff rank.
    
    Match logic:
    - Safe: Student's rank is significantly better (numerically lower) than the cutoff (projected_rank < 0.8 * cutoff_rank)
    - Target: Student's rank is close to the cutoff (0.8 * cutoff_rank <= projected_rank <= 1.2 * cutoff_rank)
    - Reach: Student's rank is worse than the cutoff (projected_rank > 1.2 * cutoff_rank)
    """
    if projected_rank < 0.8 * cutoff_rank:
        return "safe"
    elif projected_rank <= 1.2 * cutoff_rank:
        return "target"
    else:
        return "reach"


@router.get("/college-recommendations")
async def get_college_recommendations(
    request: Request,
    payload: Dict[str, Any] = Depends(require_student),
    db: Session = Depends(get_session),
) -> Dict[str, Any]:
    """Retrieve college recommendations based on student's average exam scores.
    
    Supports lock-state preview for Free Trial subscribers and full access
    for Pro and Institutional subscribers.
    """
    user = current_user(request, db)
    if not user:
        raise HTTPException(
            status_code=401,
            detail={"error": "user_not_found", "message": "Authenticated user not found"},
        )

    # 1. Fetch completed submissions for user to calculate average score
    submissions = (
        db.query(Submission.score_pct)
        .filter(Submission.user_id == user.id, Submission.status == "completed")
        .all()
    )

    if not submissions:
        return {
            "no_data": True,
            "message": "Complete at least one exam to generate college recommendations.",
        }

    # 2. Compute average score percentage
    total_score = sum(float(sub.score_pct) for sub in submissions)
    avg_score = round(total_score / len(submissions), 2)

    # 3. Determine projected rank and student tier
    projected_rank, rank_range, student_tier = map_score_to_rank_and_tier(avg_score)

    # 4. Determine subscription/locked state
    # Institution students always get full access
    if user.student_subtype == "institution_linked":
        is_locked = False
    else:
        # Check active non-trial subscriptions
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
        # If student has active subscription, unlocked. Otherwise locked.
        is_locked = active_sub is None

    # 5. Build match lists
    targets = []
    reaches = []
    safes = []

    for col in COLLEGES:
        match_type = calculate_match_type(projected_rank, col["cutoff_rank"])
        
        name = col["name"]
        location = col["location"]
        description = col["description"]
        
        # Redact strings if the tier is locked
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

    return {
        "no_data": False,
        "is_locked": is_locked,
        "average_score": avg_score,
        "projected_rank_range": rank_range,
        "student_tier": student_tier,
        "lock_message": (
            "Upgrade to the Pro Plan to unlock the full names, locations, "
            "and details of your recommended colleges."
            if is_locked
            else None
        ),
        "matches": {
            "target": targets,
            "reach": reaches,
            "safe": safes,
        },
        "counts": {
            "target": len(targets),
            "reach": len(reaches),
            "safe": len(safes),
        }
    }


@router.get("/rank-booster-suggestions")
async def get_rank_booster_suggestions(
    request: Request,
    target_rank: int = 5000,
    payload: Dict[str, Any] = Depends(require_student),
    db: Session = Depends(get_session),
) -> Dict[str, Any]:
    """Provide personalized study guide and action items to improve KCET rank."""
    user = current_user(request, db)
    if not user:
        raise HTTPException(
            status_code=401,
            detail={"error": "user_not_found", "message": "Authenticated user not found"},
        )

    # 1. Fetch overall average and number of attempts
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
        return {
            "no_data": True,
            "message": "Complete at least one exam to receive personalized study suggestions.",
        }

    attempts = int(submissions_query.attempts)
    current_avg = round(float(submissions_query.avg_score), 2)
    avg_time = round(float(submissions_query.avg_time), 1)

    # 2. Determine target score based on requested target_rank
    if target_rank <= 1000:
        target_score = 90.0
        target_label = "Top 1,000 (Tier 1)"
    elif target_rank <= 5000:
        target_score = 80.0
        target_label = "Top 5,000 (Tier 1)"
    elif target_rank <= 15000:
        target_score = 65.0
        target_label = "Top 15,000 (Tier 2)"
    else:
        target_score = 50.0
        target_label = "Top 30,000 (Tier 3)"

    score_gap = round(max(0.0, target_score - current_avg), 2)

    # 3. Fetch subject-wise average scores
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

    # 4. Identify weakest subject from the ones they have attempted
    weakest_subject = None
    weakest_score = 101.0
    for subj, score in subject_scores.items():
        if score < weakest_score:
            weakest_score = score
            weakest_subject = subj

    # 5. Check subscription status (gating)
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

    # 6. Generate action items
    action_items = []
    
    if score_gap == 0:
        action_items.append(
            f"🎉 Keep it up! Your current average of {current_avg}% is already on track to achieve {target_label}."
        )
        action_items.append("Take more exams periodically to maintain consistency and keep your sharp edges.")
    else:
        # Focus on weakest subject
        if weakest_subject:
            action_items.append(
                f"Target your weakest subject: **{weakest_subject}** (currently average {weakest_score}%). "
                f"Focus on raising this to at least {target_score}% to close your overall score gap."
            )
        
        # Consistent practice
        if attempts < 3:
            action_items.append(
                f"Increase attempt count: You have taken {attempts} exam(s). "
                f"We recommend completing at least {3 - attempts} more sets to establish a stable average."
            )
            
        # Timing checks
        if avg_time > 45 * 60: # greater than 45 minutes
            m = int(avg_time // 60)
            action_items.append(
                f"Increase speed: Your average time per exam is {m} minutes. "
                "Aim for under 40 minutes per set to build timing buffers for difficult questions."
            )
        else:
            action_items.append(
                "Maintain timing: Your average pace is excellent. Continue simulating real-time constraints."
            )

    # Redact action items if locked (Free Trial user)
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

    return {
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
    }


__all__ = ["router"]
