"""Platform Admin Dashboard — aggregated metrics endpoint.

GET /api/admin/dashboard  (requires platform_admin)

Returns a single JSON object with every KPI tile the admin dashboard
needs:
  - Platform overview (institutions, students, questions, exams)
  - Question bank breakdown (admin vs institution, per subject)
  - Subscription summary (active, expired, trial, revenue)
  - Exam activity (total created, total attempted, recent)
  - Recent institutions (last 5 registered)
  - Alerts (expiring subscriptions, inactive institutions)
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..db.models import Exam, ExamSet, IndexedFile, Question, Submission, User
from ..db.session import get_session
from ..db.subscription_models import Institution, Subscription, SubscriptionPlan
from ..middleware.rbac import require_admin

logger = logging.getLogger("smartkcet.admin.dashboard")

router = APIRouter()


@router.get("/dashboard")
def get_admin_dashboard(
    session: Session = Depends(get_session),
    _admin: dict = Depends(require_admin),
) -> Any:
    """Return all KPI metrics for the platform admin dashboard."""

    now = datetime.utcnow()
    soon = now + timedelta(days=30)

    # ── Institutions ─────────────────────────────────────────────────────────
    total_institutions = session.execute(
        select(func.count(Institution.id))
    ).scalar_one()

    active_institutions = session.execute(
        select(func.count(Institution.id)).where(
            Institution.subscription_status.in_(["active", "trial", "overdue", "grace_period"])
        )
    ).scalar_one()

    # ── Users / Students ──────────────────────────────────────────────────────
    total_students = session.execute(
        select(func.count(User.id)).where(User.role == "student")
    ).scalar_one()

    institution_linked_students = session.execute(
        select(func.count(User.id)).where(
            User.role == "student",
            User.institution_id.isnot(None),
        )
    ).scalar_one()

    direct_students = total_students - institution_linked_students

    # ── Questions ─────────────────────────────────────────────────────────────
    # Admin (platform-wide) questions — institution_id IS NULL
    admin_questions_total = session.execute(
        select(func.count(Question.id)).where(Question.institution_id.is_(None))
    ).scalar_one()

    # Per-subject admin questions
    admin_q_by_subject = dict(
        session.execute(
            select(Question.subject, func.count(Question.id))
            .where(Question.institution_id.is_(None))
            .group_by(Question.subject)
        ).all()
    )

    # Institution questions — institution_id IS NOT NULL
    institution_questions_total = session.execute(
        select(func.count(Question.id)).where(Question.institution_id.isnot(None))
    ).scalar_one()

    # Per-institution question counts
    inst_q_rows = session.execute(
        select(Institution.name, func.count(Question.id))
        .join(Question, Question.institution_id == Institution.id)
        .group_by(Institution.id, Institution.name)
        .order_by(func.count(Question.id).desc())
        .limit(10)
    ).all()
    institution_question_counts = [{"name": r[0], "count": r[1]} for r in inst_q_rows]

    # ── Exams ─────────────────────────────────────────────────────────────────
    total_exams = session.execute(select(func.count(Exam.id))).scalar_one()
    published_exams = session.execute(
        select(func.count(Exam.id)).where(Exam.is_published.is_(True))
    ).scalar_one()

    # Total exam attempts (submissions)
    total_attempts = session.execute(select(func.count(Submission.id))).scalar_one()

    # Average score across all submissions
    avg_score_result = session.execute(
        select(func.avg(Submission.score_pct))
    ).scalar_one()
    avg_score = round(float(avg_score_result or 0), 1)

    # Exams by subject
    exams_by_subject = dict(
        session.execute(
            select(Exam.subject, func.count(Exam.id))
            .group_by(Exam.subject)
        ).all()
    )

    # ── Subscriptions ─────────────────────────────────────────────────────────
    active_subscriptions = session.execute(
        select(func.count(Subscription.id)).where(
            Subscription.status.in_(["active", "trial", "grace_period"])
        )
    ).scalar_one()

    expired_subscriptions = session.execute(
        select(func.count(Subscription.id)).where(
            Subscription.status.in_(["expired", "cancelled"])
        )
    ).scalar_one()

    overdue_subscriptions = session.execute(
        select(func.count(Subscription.id)).where(
            Subscription.status == "overdue"
        )
    ).scalar_one()

    # Institution subscriptions detail (for subscriptions page)
    inst_sub_rows = session.execute(
        select(
            Institution.id,
            Institution.name,
            Institution.subscription_status,
            Subscription.status,
            Subscription.next_renewal_date,
            SubscriptionPlan.name,
            SubscriptionPlan.price,
        )
        .outerjoin(
            Subscription,
            Subscription.institution_id == Institution.id,
        )
        .outerjoin(SubscriptionPlan, SubscriptionPlan.id == Subscription.plan_id)
        .order_by(Institution.registered_at.desc())
        .limit(100)
    ).all()

    institution_subscriptions = []
    seen_institutions = set()
    for row in inst_sub_rows:
        inst_id = str(row[0])
        if inst_id in seen_institutions:
            continue
        seen_institutions.add(inst_id)
        institution_subscriptions.append({
            "institution_id": inst_id,
            "institution_name": row[1],
            "institution_status": row[2],
            "subscription_status": row[3] or "none",
            "next_renewal_date": row[4].isoformat() if row[4] else None,
            "plan_name": row[5] or "—",
            "price": float(row[6]) if row[6] else None,
        })

    # Alerts: subscriptions expiring within 30 days
    expiring_soon = session.execute(
        select(
            Institution.name,
            Subscription.next_renewal_date,
            Subscription.status,
        )
        .join(Subscription, Subscription.institution_id == Institution.id)
        .where(
            Subscription.status.in_(["active", "trial", "overdue"]),
            Subscription.next_renewal_date.isnot(None),
            Subscription.next_renewal_date <= soon,
            Subscription.next_renewal_date >= now,
        )
        .order_by(Subscription.next_renewal_date)
        .limit(10)
    ).all()

    alerts = []
    for name, renewal, sub_status in expiring_soon:
        days_left = (renewal - now).days
        alerts.append({
            "type": "subscription_expiring",
            "severity": "warning" if days_left > 7 else "error",
            "message": f"{name}: subscription expires in {days_left} day{'s' if days_left != 1 else ''}",
            "days_left": days_left,
        })

    # Inactive institutions (no subscription at all)
    inactive_count = session.execute(
        select(func.count(Institution.id)).where(
            Institution.subscription_status == "inactive"
        )
    ).scalar_one()

    if inactive_count > 0:
        alerts.append({
            "type": "inactive_institutions",
            "severity": "info",
            "message": f"{inactive_count} institution{'s' if inactive_count != 1 else ''} with no active subscription",
            "count": int(inactive_count),
        })

    # ── Recent institutions (last 5) ──────────────────────────────────────────
    recent_inst_rows = session.execute(
        select(
            Institution.id,
            Institution.name,
            Institution.subscription_status,
            Institution.registered_at,
        )
        .order_by(Institution.registered_at.desc())
        .limit(5)
    ).all()

    recent_institutions = [
        {
            "id": str(r[0]),
            "name": r[1],
            "status": r[2],
            "registered_at": r[3].isoformat() if r[3] else None,
        }
        for r in recent_inst_rows
    ]

    # ── Indexed files ─────────────────────────────────────────────────────────
    admin_files = session.execute(
        select(func.count(IndexedFile.id)).where(IndexedFile.institution_id.is_(None))
    ).scalar_one()

    institution_files = session.execute(
        select(func.count(IndexedFile.id)).where(IndexedFile.institution_id.isnot(None))
    ).scalar_one()

    # ── Assemble response ─────────────────────────────────────────────────────
    return {
        "generated_at": now.isoformat(),

        # Overview KPIs
        "overview": {
            "total_institutions": int(total_institutions),
            "active_institutions": int(active_institutions),
            "total_students": int(total_students),
            "institution_linked_students": int(institution_linked_students),
            "direct_students": int(direct_students),
            "total_questions": int(admin_questions_total + institution_questions_total),
            "admin_questions": int(admin_questions_total),
            "institution_questions": int(institution_questions_total),
            "total_exams": int(total_exams),
            "published_exams": int(published_exams),
            "total_exam_attempts": int(total_attempts),
            "avg_score": avg_score,
            "active_subscriptions": int(active_subscriptions),
            "expired_subscriptions": int(expired_subscriptions),
            "overdue_subscriptions": int(overdue_subscriptions),
            "admin_indexed_files": int(admin_files),
            "institution_indexed_files": int(institution_files),
        },

        # Question bank breakdown
        "question_bank": {
            "admin_by_subject": {s: int(v) for s, v in admin_q_by_subject.items()},
            "institution_by_institution": institution_question_counts,
        },

        # Exams breakdown
        "exams": {
            "by_subject": {s: int(v) for s, v in exams_by_subject.items()},
        },

        # Institution subscriptions
        "institution_subscriptions": institution_subscriptions,

        # Recent institutions
        "recent_institutions": recent_institutions,

        # Alerts
        "alerts": alerts,
        "alert_count": len(alerts),
    }


__all__ = ["router"]
