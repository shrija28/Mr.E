"""Student submission history endpoints.

Implements task 8.5 / REQ-4.5, REQ-10.1, REQ-10.4, REQ-14.3.

Access Control (Tasks 5.3, 5.4):
- Free Trial: Basic analytics only (total score, pass/fail)
- Pro: Full analytics (topic breakdowns, AI recommendations, trends)

Endpoints
---------

``GET /api/student/submissions``
    Return the authenticated student's submissions.  Default sort is
    ``submitted_at DESC`` (REQ-10.4).  Optional filters: ``subject``
    (joins through exam_sets → exams), ``limit`` (default 50, capped at
    200), ``offset`` (default 0).  Response items are summary records —
    detailed answer data lives on the ``GET .../{id}`` endpoint.

``GET /api/student/submissions/{submission_id}``
    Return the full submission record for a single attempt, including
    the answers, scoring envelope, and per-question correctness review.
    Enforces ownership: a 403 is returned when the submission does not
    belong to the authenticated student.  The 403 body is intentionally
    bare so no information about the submission leaks (REQ-4.5).
"""

from __future__ import annotations
import os

import uuid
from typing import Any, Optional

import os
from flask import Blueprint, request, g, make_response, jsonify, Response
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from ..db.models import Exam, ExamSet, ExamSetQuestion, Question, Submission, Subject
from ..db.session import get_async_session as get_session
from ..middleware.rbac import current_user, require_student
from ..subscription.dependencies import get_access_control

router = Blueprint("student_submissions", __name__)


_DEFAULT_LIMIT = 50
_MAX_LIMIT = 200


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _validation_error(message: str, field: Optional[str] = None) -> Any:
    body: dict[str, Any] = {"error": "validation_error", "message": message}
    if field is not None:
        body["field"] = field
    return make_response(jsonify(body), 400)


def _normalise_subject(value: Optional[str])-> Optional[Subject]:
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    if not stripped:
        return None
    try:
        return Subject(stripped)
    except ValueError:
        return None


def _summary_row(submission: Submission, exam_set: ExamSet, exam: Exam)-> dict[str, Any]:
    """Map a join row to the dashboard summary shape."""

    submitted_at = submission.submitted_at
    return {
        "id": str(submission.id),
        "exam_set_id": str(submission.exam_set_id),
        "exam_id": str(exam.id),
        "set_label": exam_set.set_label,
        "subject": exam.subject,
        "score_pct": float(submission.score_pct),
        "time_taken_sec": int(submission.time_taken_sec),
        "submitted_at": (
            submitted_at.isoformat() if submitted_at is not None else None
        ),
        "status": submission.status,
        "pass_flag": float(submission.score_pct) >= 50.0,
    }


# ---------------------------------------------------------------------------
# GET /api/student/submissions  (REQ-10.1, REQ-10.4)
# ---------------------------------------------------------------------------


@router.route("/submissions", methods=["GET"])
def list_submissions()-> Any:    
    _student = require_student()
    from flask import g
    db = getattr(g, "db", None)
    session = db
    from flask import g
    access_control = getattr(g, "access_control", None)
    from flask import request
    subject = request.args.get("subject", None)
    from flask import request
    limit = int(request.args.get("limit", _DEFAULT_LIMIT))
    from flask import request
    offset = int(request.args.get("offset", 0))
    
    _student = require_student()
    from flask import g
    db = getattr(g, "db", None)
    session = db
    from flask import g
    access_control = getattr(g, "access_control", None)
    from flask import request
    subject = request.args.get("subject", None)
    from flask import request
    limit = int(request.args.get("limit", _DEFAULT_LIMIT))
    from flask import request
    offset = int(request.args.get("offset", 0))
    """List the authenticated student's submissions, newest first.
    
    **Subscription Integration (REQ-2.4):**
    Response includes subscription status and remaining attempts for dashboard display.
    """

    user = current_user(request, session)
    if user is None or user.role != "student":
        return make_response(jsonify({
                "error": "auth_required",
                "message": "Authenticated student account not found.",
            }), 401)

    selected_subject: Optional[Subject] = None
    if subject is not None:
        normalised = _normalise_subject(subject)
        if normalised is None:
            allowed = [s.value for s in Subject]
            return _validation_error(
                f"subject must be one of {allowed}",
                field="subject",
            )
        selected_subject = normalised

    capped_limit = min(int(limit), _MAX_LIMIT)

    stmt = (
        select(Submission, ExamSet, Exam)
        .join(ExamSet, ExamSet.id == Submission.exam_set_id)
        .join(Exam, Exam.id == ExamSet.exam_id)
        .where(Submission.user_id == user.id)
        .order_by(Submission.submitted_at.desc(), Submission.id.asc())
        .offset(offset)
        .limit(capped_limit)
    )
    if selected_subject is not None:
        stmt = stmt.where(Exam.subject == selected_subject.value)

    rows = session.execute(stmt).all()
    summaries = [_summary_row(sub, exam_set, exam) for sub, exam_set, exam in rows]

    # Get subscription status and remaining attempts for dashboard display (REQ-2.4)
    subscription_status = None
    remaining_attempts_data = None
    try:
        # Get effective subscription status
        from ..subscription.service import SubscriptionService
        subscription_service = SubscriptionService(session)
        effective_status = subscription_service.get_effective_status(user.id)
        
        subscription_status = {
            "has_subscription": effective_status.has_subscription,
            "status": effective_status.status,
            "plan_type": effective_status.plan_type,
            "billing_period": effective_status.billing_period,
            "is_trial": effective_status.is_trial,
            "is_active": effective_status.is_active,
            "trial_attempts_remaining": effective_status.trial_attempts_remaining,
            "next_renewal_date": effective_status.next_renewal_date.isoformat() if effective_status.next_renewal_date else None,
            "grace_period_end": effective_status.grace_period_end.isoformat() if effective_status.grace_period_end else None,
            "institution_id": str(effective_status.institution_id) if effective_status.institution_id else None,
            "institution_name": effective_status.institution_name,
        }
        
        # Get remaining attempts
        from ..subscription.access_control import SubscriptionAccessControl
        ac = access_control or SubscriptionAccessControl(session)
        remaining_attempts_data = ac.get_remaining_attempts(user.id)
    except Exception as exc:
        # If we can't get subscription info, log but don't fail the request
        import logging
        logger = logging.getLogger("smartkcet.student.submissions")
        logger.warning("Failed to get subscription info for user %s: %s", user.id, exc)

    return {
        "submissions": summaries,
        "limit": capped_limit,
        "offset": int(offset),
        "subject": selected_subject.value if selected_subject is not None else None,
        "subscription_status": subscription_status,
        "remaining_attempts": remaining_attempts_data,
    }


# ---------------------------------------------------------------------------
# GET /api/student/submissions/{submission_id}  (REQ-4.5, REQ-14.3)
# ---------------------------------------------------------------------------


@router.route("/submissions/<submission_id>", methods=["GET"])
def get_submission(submission_id: uuid.UUID)-> Any:    
    _student = require_student()
    from flask import g
    db = getattr(g, "db", None)
    session = db
    from flask import g
    access_control = getattr(g, "access_control", None)
    """Return the full submission record (with question review).

    A 403 is returned when the submission belongs to a different
    student, with no body data leaked (REQ-4.5).
    """

    user = current_user(request, session)
    if user is None or user.role != "student":
        return make_response(jsonify({
                "error": "auth_required",
                "message": "Authenticated student account not found.",
            }), 401)

    submission = session.execute(
        select(Submission)
        .where(Submission.id == submission_id)
        .options(joinedload(Submission.exam_set).joinedload(ExamSet.exam))
    ).scalar_one_or_none()

    if submission is None:
        return make_response(jsonify({
                "error": "not_found",
                "resource": "submission",
                "value": str(submission_id),
            }), 404)

    if submission.user_id != user.id:
        # REQ-4.5: forbidden, with no submission data in the body.
        return make_response(jsonify({"error": "forbidden", "message": "Access denied."}), 403)

    exam_set = submission.exam_set
    exam = exam_set.exam if exam_set is not None else None

    # Pull the question rows so the detail drawer can render the answer
    # review (correct option, topic, etc.) without a second request.
    question_rows = session.execute(
        select(Question, ExamSetQuestion.order_index)
        .join(ExamSetQuestion, ExamSetQuestion.question_id == Question.id)
        .where(ExamSetQuestion.exam_set_id == submission.exam_set_id)
        .order_by(ExamSetQuestion.order_index.asc())
    ).all()
    questions: list[dict[str, Any]] = []
    answers = submission.answers if isinstance(submission.answers, dict) else {}
    from ..db.subscription_models import Subscription
    from ..submissions.scoring import _is_correct_answer

    sub = session.query(Subscription).options(joinedload(Subscription.plan)).filter(
        Subscription.user_id == user.id,
        Subscription.status.in_(["active", "trial", "grace_period"])
    ).first()
    is_institution = (getattr(user, "student_subtype", "") == "institution_linked") or (getattr(user, "institution_id", None) is not None)
    is_premium = is_institution or (sub is not None and sub.plan is not None and sub.plan.name.lower() != "free")

    q_times = answers.get("__question_times__", {}) if isinstance(answers, dict) else {}

    for question, order_index in question_rows:
        index_str = str(order_index)
        given = answers.get(index_str)
        q_time = q_times.get(index_str) if isinstance(q_times, dict) else None
        if q_time is None and isinstance(q_times, dict):
            q_time = q_times.get(int(order_index))

        if given is None or str(given).strip() == "":
            given_status = "unanswered"
        elif _is_correct_answer(given, question.correct_option, question.options):
            given_status = "correct"
        else:
            given_status = "wrong"
        questions.append(
            {
                "order_index": int(order_index),
                "id": str(question.id),
                "q": question.question_text,
                "opts": question.options,
                "correctAns": question.correct_option if is_premium else None,
                "topic": question.topic or "General",
                "given": given,
                "status": given_status,
                "exp": (question.explanation or "") if is_premium else None,
                "time_taken_sec": q_time,
            }
        )

    submitted_at = submission.submitted_at
    
    analytics_data = {
        "id": str(submission.id),
        "exam_set_id": str(submission.exam_set_id),
        "exam_id": str(exam.id) if exam is not None else None,
        "set_label": exam_set.set_label if exam_set is not None else None,
        "subject": exam.subject if exam is not None else None,
        "score_pct": float(submission.score_pct),
        "topic_breakdown": submission.topic_breakdown,
        "time_taken_sec": int(submission.time_taken_sec),
        "submitted_at": (
            submitted_at.isoformat() if submitted_at is not None else None
        ),
        "status": submission.status,
        "pass_flag": float(submission.score_pct) >= 50.0,
        "is_premium_subscriber": is_premium,
        "answers": submission.answers,
        "questions": questions,
    }
    
    # Filter analytics data based on subscription tier
    filtered_data = access_control.filter_analytics_data(analytics_data, user.id)
    
    return filtered_data


# ---------------------------------------------------------------------------
# GET /api/student/dashboard-stats
# ---------------------------------------------------------------------------


@router.route("/dashboard-stats", methods=["GET"])
def get_dashboard_stats() -> Any:
    """Return real-time aggregated dashboard analytics for the authenticated student.

    Calculates real KPIs, subject performance, chronological score trend,
    pass vs fail ratio, AI strength/weakness areas, leaderboard standing,
    and recent exam history from the student's actual database submissions.
    """
    _student = require_student()
    session = getattr(g, "db", None)
    if session is None:
        from ..db.session import SessionLocal
        session = SessionLocal()

    user = current_user(request, session)
    if user is None or user.role != "student":
        return make_response(
            jsonify({
                "error": "auth_required",
                "message": "Authenticated student account not found.",
            }),
            401,
        )

    # 1. Fetch leaderboard to determine student's rank and top peers
    from ..leaderboard.service import get_leaderboard
    ranked = get_leaderboard(session)

    top_students = []
    for entry in ranked[:5]:
        top_students.append({
            "rank": entry.rank,
            "name": entry.display_name or f"Student {str(entry.kcet_student_id)[-4:]}",
            "id": entry.kcet_student_id,
            "score": round(float(entry.composite_score), 1),
            "progress": "+Top",
        })

    # 2. Query all completed submissions for the student, sorted newest first
    stmt = (
        select(Submission, ExamSet, Exam)
        .join(ExamSet, ExamSet.id == Submission.exam_set_id)
        .join(Exam, Exam.id == ExamSet.exam_id)
        .where(Submission.user_id == user.id, Submission.status == "completed")
        .order_by(Submission.submitted_at.desc(), Submission.id.asc())
    )
    rows = session.execute(stmt).all()

    # Starter state when student has 0 submissions
    if not rows:
        return jsonify({
            "kpis": {
                "examsTaken": 0,
                "submissions": 0,
                "avgScore": 0,
                "passRate": 0,
                "avgTime": 0,
                "rank": "—",
                "rankHint": "Complete at least one mock exam to generate your score and rank analytics",
            },
            "topicData": {
                "labels": ["Physics", "Chemistry", "Mathematics", "Biology"],
                "scores": [0, 0, 0, 0],
            },
            "setData": {
                "labels": [],
                "scores": [],
            },
            "passFailData": {
                "labels": ["Pass", "Fail"],
                "counts": [0, 0],
            },
            "aiAnalysis": {
                "strong_areas": [],
                "can_improve_areas": [],
                "weak_areas": [],
                "recommendation": "You have not completed any mock exams yet. Select a published exam above and submit your first attempt to generate personalized AI performance insights.",
                "rank_booster": {
                    "current_score": 0,
                    "current_rank": 55000,
                    "boosted_score": 75.0,
                    "boosted_rank": 8000,
                    "rank_leap": 47000,
                    "potential_marks_gain": 15.0,
                    "weakest_subject": "General",
                    "top_weak_topic": "Foundational Concepts",
                    "has_data": False,
                },
                "action_plan": [
                    {
                        "id": "step-1",
                        "title": "Complete Your First KCET Diagnostic Exam",
                        "desc": "Take any published subject mock test above (Physics, Chemistry, or Mathematics) to calibrate your starting score.",
                        "category": "Diagnostic",
                        "badge": "Step 1",
                    },
                    {
                        "id": "step-2",
                        "title": "Inspect Personalized AI Topic Breakdown",
                        "desc": "Identify high-weightage chapters where you can convert gaps into rapid marks.",
                        "category": "Analysis",
                        "badge": "Step 2",
                    },
                    {
                        "id": "step-3",
                        "title": "Execute Targeted Revision & PYQs",
                        "desc": "Solve 15-20 timed KCET previous year questions on your lowest-scoring topic.",
                        "category": "Practice",
                        "badge": "Step 3",
                    },
                ],
            },
            "topStudents": top_students,
            "examHistory": [],
            "has_data": False,
        })

    # 3. Calculate real KPIs
    submissions_count = len(rows)
    distinct_exam_ids = len(set(exam.id for _, _, exam in rows))
    scores = [float(sub.score_pct) for sub, _, _ in rows]
    avg_score = round(sum(scores) / submissions_count, 1)
    pass_count = sum(1 for s in scores if s >= 50.0)
    fail_count = submissions_count - pass_count
    pass_rate = round((pass_count / submissions_count) * 100, 1)
    total_time = sum(int(sub.time_taken_sec or 0) for sub, _, _ in rows)
    avg_time = round(total_time / (submissions_count * 60)) if submissions_count > 0 else 0

    # Determine user's rank
    my_rank: Any = "—"
    rank_hint = "Score at least 30% on average to qualify on statewide leaderboard"
    for entry in ranked:
        if entry.student_id == str(user.id) or entry.kcet_student_id == user.kcet_student_id:
            my_rank = entry.rank
            rank_hint = f"Ranked #{my_rank} out of {len(ranked)} on statewide leaderboard"
            break

    if my_rank == "—" and avg_score >= 30.0:
        rank_hint = "Take exams across more subjects to appear on statewide leaderboard"

    # 4. Subject / Topic scores
    subject_scores_dict: dict[str, list[float]] = {
        "Physics": [],
        "Chemistry": [],
        "Mathematics": [],
        "Biology": [],
    }
    for sub, _, exam in rows:
        subj = exam.subject
        if subj in subject_scores_dict:
            subject_scores_dict[subj].append(float(sub.score_pct))
        else:
            subject_scores_dict[subj] = [float(sub.score_pct)]

    topic_labels = ["Physics", "Chemistry", "Mathematics", "Biology"]
    topic_scores = []
    for label in topic_labels:
        scores_list = subject_scores_dict.get(label, [])
        if scores_list:
            topic_scores.append(round(sum(scores_list) / len(scores_list), 1))
        else:
            topic_scores.append(0)

    # 5. Chronological score progression trend
    chronological_rows = list(reversed(rows))
    trend_labels = []
    trend_scores = []
    for i, (sub, exam_set, exam) in enumerate(chronological_rows):
        label = f"#{i+1} {exam.subject}"
        trend_labels.append(label)
        trend_scores.append(round(float(sub.score_pct), 1))

    # 6. Aggregate AI Analysis (strengths, weak topics, and personalized recommendation)
    topic_aggregates: dict[str, dict[str, int]] = {}
    for sub, _, _ in rows:
        breakdown = sub.topic_breakdown
        if isinstance(breakdown, dict):
            for topic, stats in breakdown.items():
                if isinstance(stats, dict) and "earned" in stats and "total" in stats:
                    if topic not in topic_aggregates:
                        topic_aggregates[topic] = {"earned": 0, "total": 0}
                    topic_aggregates[topic]["earned"] += int(stats["earned"])
                    topic_aggregates[topic]["total"] += int(stats["total"])

    strong_areas = []
    can_improve_areas = []
    weak_areas = []

    for topic, stats in sorted(topic_aggregates.items(), key=lambda x: x[0]):
        if stats["total"] > 0:
            pct = round((stats["earned"] / stats["total"]) * 100, 1)
            display_str = f"{topic} ({pct}%)"
            if pct >= 75.0:
                strong_areas.append(display_str)
            elif pct >= 50.0:
                can_improve_areas.append(display_str)
            else:
                weak_areas.append(display_str)

    # Recommendation text
    recommendation_text = ""
    latest_sub = rows[0][0] if rows else None
    if latest_sub and isinstance(latest_sub.answers, dict):
        ai_meta = latest_sub.answers.get("__ai_analysis__")
        if isinstance(ai_meta, dict) and ai_meta.get("recommendation"):
            recommendation_text = ai_meta["recommendation"]

    if not recommendation_text:
        if weak_areas:
            recommendation_text = f"Priority Focus: Strengthen foundational concepts in {weak_areas[0].split(' (')[0]}. Regular practice with standard KCET numericals will boost your score significantly."
        elif can_improve_areas:
            recommendation_text = f"Good progress! To push your score into the top percentile, refine speed and accuracy in {can_improve_areas[0].split(' (')[0]}."
        else:
            recommendation_text = "Outstanding performance across all topics! Maintain your daily practice routine and focus on mock exam time-management."

    # 7. Rank Booster & 3-Step Action Plan calculations
    def _calc_kcet_rank(score: float) -> int:
        s = max(0.0, min(100.0, float(score)))
        if s >= 90.0:
            return int(100 + (100.0 - s) * 240.0)
        elif s >= 75.0:
            return int(2500 + (90.0 - s) * 366.6)
        elif s >= 60.0:
            return int(8000 + (75.0 - s) * 800.0)
        elif s >= 45.0:
            return int(20000 + (60.0 - s) * 1666.6)
        else:
            return int(45000 + (45.0 - s) * 1222.2)

    # Identify student's weakest subject
    weakest_subject = "Physics"
    lowest_subj_score = 101.0
    for subj, sc_list in subject_scores_dict.items():
        if sc_list:
            subj_avg = sum(sc_list) / len(sc_list)
            if subj_avg < lowest_subj_score:
                lowest_subj_score = subj_avg
                weakest_subject = subj

    # Top weak topic (from weak_areas, or can_improve_areas, or fallback)
    top_weak_topic = None
    if weak_areas:
        top_weak_topic = weak_areas[0].split(" (")[0]
    elif can_improve_areas:
        top_weak_topic = can_improve_areas[0].split(" (")[0]
    else:
        top_weak_topic = f"{weakest_subject} Core Concepts"

    current_rank = _calc_kcet_rank(avg_score)
    est_gain = 14.0 if avg_score < 70.0 else (10.0 if avg_score < 85.0 else 5.0)
    boosted_score = min(98.0, round(avg_score + est_gain, 1))
    boosted_rank = _calc_kcet_rank(boosted_score)
    rank_leap = max(50, current_rank - boosted_rank)
    potential_marks = round(est_gain * 0.6, 1)

    rank_booster = {
        "current_score": avg_score,
        "current_rank": current_rank,
        "boosted_score": boosted_score,
        "boosted_rank": boosted_rank,
        "rank_leap": rank_leap,
        "potential_marks_gain": potential_marks,
        "est_gain_pct": est_gain,
        "weakest_subject": weakest_subject,
        "top_weak_topic": top_weak_topic,
        "has_data": True,
    }

    action_plan = [
        {
            "id": "step-1",
            "title": f"Revise Core Formulas & NCERT Theory in {top_weak_topic}",
            "desc": f"Review key formulas, standard definitions, and exception cases for {top_weak_topic} in {weakest_subject}.",
            "category": "Formulas & Theory",
            "badge": "Step 1",
        },
        {
            "id": "step-2",
            "title": f"Solve 15-20 Timed PYQs in {top_weak_topic}",
            "desc": f"Work through past 5 years KCET questions under timed conditions (< 75s per numerical).",
            "category": "Targeted Practice",
            "badge": "Step 2",
        },
        {
            "id": "step-3",
            "title": f"Validate with a {weakest_subject} Mock Exam",
            "desc": f"Retake a {weakest_subject} exam aiming for >= 75% accuracy to lock in your score and rank gains.",
            "category": "Mock Validation",
            "badge": "Step 3",
        },
    ]

    # 8. Exam history list
    exam_history = []
    for sub, exam_set, exam in rows:
        submitted_at_str = sub.submitted_at.strftime("%b %d, %Y") if sub.submitted_at else "—"
        exam_history.append({
            "id": str(sub.id),
            "subject": exam.subject,
            "exam_name": exam.exam_name or f"{exam.subject} Exam",
            "set": f"Set {exam_set.set_label}",
            "score": f"{float(sub.score_pct):.1f}%",
            "score_pct": float(sub.score_pct),
            "time": f"{round(sub.time_taken_sec / 60)}m",
            "time_taken_sec": int(sub.time_taken_sec),
            "status": "Pass" if float(sub.score_pct) >= 50.0 else "Fail",
            "date": submitted_at_str,
        })

    return jsonify({
        "kpis": {
            "examsTaken": distinct_exam_ids,
            "submissions": submissions_count,
            "avgScore": avg_score,
            "passRate": pass_rate,
            "avgTime": avg_time,
            "rank": my_rank,
            "rankHint": rank_hint,
        },
        "topicData": {
            "labels": topic_labels,
            "scores": topic_scores,
        },
        "setData": {
            "labels": trend_labels,
            "scores": trend_scores,
        },
        "passFailData": {
            "labels": ["Pass", "Fail"],
            "counts": [pass_count, fail_count],
        },
        "aiAnalysis": {
            "strong_areas": strong_areas,
            "can_improve_areas": can_improve_areas,
            "weak_areas": weak_areas,
            "recommendation": recommendation_text,
            "rank_booster": rank_booster,
            "action_plan": action_plan,
        },
        "topStudents": top_students,
        "examHistory": exam_history,
        "has_data": True,
    })


__all__ = ["router"]
