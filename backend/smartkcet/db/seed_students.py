"""Seed script — provisions test student accounts for development/testing.

This script creates multiple test students with different configurations:
- Direct subscribers (no institution)
- Institution-linked students (with institution)

Usage::

    python -m smartkcet.db.seed_students

Environment variables:
- COUNT (optional): Number of students to create per type (default: 5)
- CREATE_INSTITUTIONS (optional): Whether to create test institutions (default: True)

Exit codes:
- 0 — students created successfully
- 1 — error during creation
"""

from __future__ import annotations

import logging
import os
import sys
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session

from .models import User
from .session import SessionLocal
from .subscription_models import Institution, Subscription, SubscriptionPlan
from ..auth.identity import next_kcet_id, next_institution_student_id

logger = logging.getLogger("smartkcet.seed_students")


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    import bcrypt

    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def get_next_kcet_id(session: Session, counter: int = None) -> str:
    """Generate the next KCET student ID (KCET001, KCET002, etc.).
    
    Args:
        session: Database session
        counter: If provided, use this counter value. Otherwise query max from DB.
    """
    from sqlalchemy import func

    if counter is not None:
        return f"KCET{counter:03d}"

    # Get max ID from database
    max_result = session.query(func.max(User.kcet_student_id)).filter(
        User.kcet_student_id.like("KCET%")
    ).scalar()

    if max_result is None:
        return "KCET001"

    try:
        max_num = int(max_result.replace("KCET", ""))
        return f"KCET{max_num + 1:03d}"
    except (ValueError, AttributeError):
        return "KCET001"


def seed_test_institutions(session: Session, count: int = 3) -> list[Institution]:
    """Create test institutions."""
    institutions = []

    institution_names = [
        # institution_code must be lowercase letters only so the
        # institution-specific student ID format ({code}####) parses
        # correctly per smartkcet.auth.identity.INSTITUTION_ID_RE.
        ("KCET Academy", "kcetacademy"),
        ("Engineering Coaching Centre", "engcoaching"),
        ("NEET Plus Institute", "neetplus"),
    ]

    for i, (name, code) in enumerate(institution_names[:count]):
        # Check if institution already exists
        existing = session.query(Institution).filter(
            Institution.institution_code == code
        ).first()

        if existing is None:
            institution = Institution(
                id=uuid.uuid4(),
                name=name,
                institution_code=code,
                contact_phone=f"+91-90000-{i:05d}",
                subscription_status="active",
                registered_at=datetime.utcnow(),
            )
            session.add(institution)
            institutions.append(institution)
            logger.info(f"Created test institution: {name} ({code})")

    session.commit()
    return institutions


def seed_test_direct_subscribers(session: Session, count: int = 5) -> list[User]:
    """Create test direct subscriber accounts (individual students).

    Direct subscribers get the global ``KCET####`` ID format via
    :func:`smartkcet.auth.identity.next_kcet_id` — the same generator the
    real registration endpoint uses.
    """
    students = []

    for i in range(1, count + 1):
        email = f"student{i}@smartkcet.test"

        # Check if student already exists
        existing = session.query(User).filter(User.email == email).first()

        if existing is None:
            # next_kcet_id scans existing IDs; autoflush makes students
            # added earlier in this loop visible so the counter advances.
            student_id = next_kcet_id(session)
            student = User(
                id=uuid.uuid4(),
                email=email,
                kcet_student_id=student_id,
                display_name=f"Direct Student {i}",
                password_hash=hash_password(f"TestPass{i}@123"),
                role="student",
                student_subtype="direct_subscriber",
                institution_id=None,
                created_at=datetime.utcnow(),
            )
            session.add(student)
            session.flush()  # make this ID visible to the next next_kcet_id()
            students.append(student)
            logger.info(f"Created direct subscriber: {email} ({student_id})")

    session.commit()
    return students


def seed_test_institution_students(
    session: Session, institutions: list[Institution], count_per_institution: int = 5
) -> list[User]:
    """Create test institution-linked student accounts.

    Institution students get institution-specific IDs in the
    ``{institution_code}####`` format (e.g. ``kcetacademy0001``) via
    :func:`smartkcet.auth.identity.next_institution_student_id`, matching
    the real registration flow. Each institution keeps its own counter.
    """
    students = []

    for inst_idx, institution in enumerate(institutions):
        for i in range(1, count_per_institution + 1):
            email = f"inst{inst_idx + 1}_student{i}@smartkcet.test"

            # Check if student already exists
            existing = session.query(User).filter(User.email == email).first()

            if existing is None:
                # Institution-specific ID ({code}####); per-institution counter.
                student_id = next_institution_student_id(session, str(institution.id))
                student = User(
                    id=uuid.uuid4(),
                    email=email,
                    kcet_student_id=student_id,
                    display_name=f"{institution.name} - Student {i}",
                    password_hash=hash_password(f"TestPass{i}@123"),
                    role="student",
                    student_subtype="institution_linked",
                    institution_id=institution.id,
                    created_at=datetime.utcnow(),
                )
                session.add(student)
                session.flush()  # make this ID visible to the next generator call
                students.append(student)
                logger.info(
                    f"Created institution student: {email} ({student_id}) for {institution.name}"
                )

    session.commit()
    return students


def create_trial_subscriptions(session: Session, students: list[User]) -> int:
    """Create trial subscriptions for students."""
    count = 0

    # Get or create Free Trial plan
    free_trial_plan = session.query(SubscriptionPlan).filter(
        SubscriptionPlan.name == "Free",
        SubscriptionPlan.plan_type == "individual",
    ).first()

    if free_trial_plan is None:
        logger.warning("Free Trial plan not found. Skipping subscription creation.")
        return 0

    for student in students:
        # Check if student already has a subscription
        existing_sub = session.query(Subscription).filter(
            Subscription.user_id == student.id
        ).first()

        if existing_sub is None:
            subscription = Subscription(
                id=uuid.uuid4(),
                user_id=student.id,
                institution_id=None,
                plan_id=free_trial_plan.id,
                status="trial",
                start_date=datetime.utcnow(),
                current_period_start=datetime.utcnow(),
                next_renewal_date=datetime.utcnow() + timedelta(days=7),
                trial_duration_days=7,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            session.add(subscription)
            count += 1

    session.commit()
    logger.info(f"Created {count} trial subscriptions")
    return count


def create_institution_subscriptions(session: Session, institutions: list[Institution]) -> int:
    """Create subscriptions for institutions."""
    count = 0

    # Get the institution plan (use "Basic" by default)
    inst_plan = session.query(SubscriptionPlan).filter(
        SubscriptionPlan.plan_type == "institution",
        SubscriptionPlan.name == "Basic"
    ).first()

    if inst_plan is None:
        # Try any institution plan
        inst_plan = session.query(SubscriptionPlan).filter(
            SubscriptionPlan.plan_type == "institution"
        ).first()

    if inst_plan is None:
        logger.warning("No institution subscription plans found. Skipping institution subscription creation.")
        return 0

    for institution in institutions:
        # Check if institution already has a subscription
        existing_sub = session.query(Subscription).filter(
            Subscription.institution_id == institution.id
        ).first()

        if existing_sub is None:
            now = datetime.utcnow()
            subscription = Subscription(
                id=uuid.uuid4(),
                user_id=None,
                institution_id=institution.id,
                plan_id=inst_plan.id,
                status="active",
                start_date=now,
                current_period_start=now,
                next_renewal_date=now + timedelta(days=30),
                created_at=now,
                updated_at=now,
            )
            session.add(subscription)
            count += 1
            logger.info(f"Created subscription for institution: {institution.name}")

    session.commit()
    logger.info(f"Created {count} institution subscriptions")
    return count


def seed_students(
    session: Optional[Session] = None,
    direct_subscriber_count: int = 5,
    institution_count: int = 3,
    institution_student_count: int = 5,
) -> dict:
    """Create all test students and subscriptions.

    Returns a dictionary with summary of created entities.
    """
    owns_session = session is None
    if session is None:
        session = SessionLocal()

    try:
        logger.info("Starting student seed...")

        # Step 1: Create test institutions
        institutions = seed_test_institutions(session, institution_count)
        logger.info(f"Created {len(institutions)} test institutions")

        # Step 2: Create direct subscriber students
        direct_students = seed_test_direct_subscribers(session, direct_subscriber_count)
        logger.info(f"Created {len(direct_students)} direct subscriber students")

        # Step 3: Create institution-linked students
        institution_students = seed_test_institution_students(
            session, institutions, institution_student_count
        )
        logger.info(
            f"Created {len(institution_students)} institution-linked students"
        )

        # Step 4: Create trial subscriptions for direct subscribers
        trial_subs = create_trial_subscriptions(session, direct_students)

        return {
            "status": "success",
            "institutions_created": len(institutions),
            "direct_subscribers_created": len(direct_students),
            "institution_students_created": len(institution_students),
            "trial_subscriptions_created": trial_subs,
            "total_students": len(direct_students) + len(institution_students),
            "message": f"Successfully seeded {len(direct_students) + len(institution_students)} students",
        }

    except Exception as e:
        logger.error(f"Error during student seed: {e}", exc_info=True)
        session.rollback()
        return {
            "status": "error",
            "error": str(e),
        }

    finally:
        if owns_session:
            session.close()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Read environment variables
    direct_count = int(os.getenv("DIRECT_STUDENTS", "5"))
    institution_count = int(os.getenv("INSTITUTIONS", "3"))
    students_per_inst = int(os.getenv("INST_STUDENTS", "5"))

    result = seed_students(
        direct_subscriber_count=direct_count,
        institution_count=institution_count,
        institution_student_count=students_per_inst,
    )

    print("\n" + "=" * 60)
    print("SEED RESULTS")
    print("=" * 60)
    for key, value in result.items():
        print(f"{key}: {value}")
    print("=" * 60)

    sys.exit(0 if result["status"] == "success" else 1)
