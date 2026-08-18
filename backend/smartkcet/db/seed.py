"""Seed script — provisions the singleton admin account.

Implements REQ-3.5 (mirror of the startup config guard, on the seed-script
side).  Reads the admin credentials from environment variables and ensures
exactly one ``users`` row with ``role='admin'`` exists, idempotently.

Usage::

    python -m smartkcet.db.seed

Environment variables consumed:

* ``ADMIN_EMAIL`` — required.  RFC 5322 email.
* ``ADMIN_PASSWORD_HASH`` — required.  An already-hashed bcrypt string
  (e.g. produced by ``bcrypt.hashpw(b'...', bcrypt.gensalt()).decode()``).
  This script never re-hashes it; the env value is the canonical hash.
* ``ADMIN_DISPLAY_NAME`` — optional, defaults to ``"Administrator"``.

Exit codes:

* ``0`` — admin row was created or already up-to-date.
* ``1`` — required environment variable missing or malformed.
"""

from __future__ import annotations

import logging
import os
import re
import sys
from typing import Optional

from sqlalchemy.orm import Session

from .models import User
from .session import SessionLocal

logger = logging.getLogger("smartkcet.seed")


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------


# A bcrypt hash is 60 chars long and starts with one of the standard
# version prefixes ($2a$, $2b$, $2y$) followed by ``cost$22-char-salt +
# 31-char-hash``.  We do a structural check only — actual cryptographic
# verification happens on login.
_BCRYPT_HASH_RE = re.compile(
    r"^\$2[aby]\$\d{2}\$[./A-Za-z0-9]{53}$"
)

# Lightweight email shape check.  Full RFC 5322 validation happens in the
# auth service; here we only need to rule out obvious garbage so the seed
# doesn't insert junk.
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _is_valid_bcrypt_hash(value: str) -> bool:
    """Return True if ``value`` looks like a bcrypt hash."""

    return bool(_BCRYPT_HASH_RE.match(value))


def _is_valid_email(value: str) -> bool:
    """Return True if ``value`` looks like a syntactically valid email."""

    return bool(_EMAIL_RE.match(value)) and len(value) <= 254


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def _read_admin_config() -> tuple[str, str, str]:
    """Read and validate admin env vars; raise :class:`SystemExit` on error."""

    email = os.getenv("ADMIN_EMAIL")
    password_hash = os.getenv("ADMIN_PASSWORD_HASH")
    display_name = os.getenv("ADMIN_DISPLAY_NAME", "Administrator").strip()

    if not email:
        logger.error(
            "ADMIN_EMAIL environment variable is missing; cannot seed admin."
        )
        raise SystemExit(1)

    if not _is_valid_email(email):
        logger.error(
            "ADMIN_EMAIL %r is not a valid email address; refusing to seed.",
            email,
        )
        raise SystemExit(1)

    if not password_hash:
        logger.error(
            "ADMIN_PASSWORD_HASH environment variable is missing; "
            "cannot seed admin."
        )
        raise SystemExit(1)

    if not _is_valid_bcrypt_hash(password_hash):
        logger.error(
            "ADMIN_PASSWORD_HASH does not look like a bcrypt hash "
            "(must start with $2a$, $2b$, or $2y$ and be 60 chars). "
            "Refusing to seed."
        )
        raise SystemExit(1)

    if not display_name:
        display_name = "Administrator"

    return email, password_hash, display_name


def seed_admin(session: Optional[Session] = None) -> str:
    """Create or update the singleton admin row.

    Returns one of two human-readable status strings::

        "created"
        "updated"
        "unchanged"

    Idempotent: subsequent runs against the same DB and same env do not
    produce duplicate rows.
    """

    email, password_hash, display_name = _read_admin_config()

    owns_session = session is None
    if session is None:
        session = SessionLocal()

    try:
        existing = session.query(User).filter(User.email == email).one_or_none()

        if existing is None:
            admin = User(
                email=email,
                kcet_student_id=None,
                display_name=display_name,
                password_hash=password_hash,
                role="platform_admin",
            )
            session.add(admin)
            session.commit()
            print(f"Created admin {email}")
            return "created"

        # Update only the fields that should be admin-controlled.
        changed = False
        if existing.role != "platform_admin":
            existing.role = "platform_admin"
            changed = True
        if existing.password_hash != password_hash:
            existing.password_hash = password_hash
            changed = True
        if existing.kcet_student_id is not None:
            existing.kcet_student_id = None
            changed = True
        if existing.display_name != display_name:
            existing.display_name = display_name
            changed = True

        if changed:
            session.commit()
            print(f"Updated admin {email}")
            return "updated"

        print(f"Admin {email} already up-to-date")
        return "unchanged"
    finally:
        if owns_session:
            session.close()


def seed_subscription_plans(session: Optional[Session] = None) -> int:
    """Create default subscription plans for platform and institutions.
    
    Returns the number of plans inserted. Returns 0 if plans already exist
    (idempotent).
    """
    from .subscription_models import SubscriptionPlan
    from decimal import Decimal

    owns_session = session is None
    if session is None:
        session = SessionLocal()

    try:
        # Check if plans already exist (idempotent)
        existing_count = session.query(SubscriptionPlan).count()
        if existing_count > 0:
            return 0  # Already seeded

        plans = [
            # Individual plans
            SubscriptionPlan(
                name="Free",
                plan_type="individual",
                billing_period="monthly",
                price=Decimal("0.00"),
                max_test_attempts_per_period=5,
                feature_flags={
                    "leaderboard": False,
                    "analytics": "basic",
                    "topic_analysis": False,
                    "is_free": True,
                },
                is_active=True,
            ),
            SubscriptionPlan(
                name="7-Day Premium Trial",
                plan_type="individual",
                billing_period="weekly",
                price=Decimal("99.00"),
                max_test_attempts_per_period=999,  # Unlimited during trial
                feature_flags={
                    "leaderboard": True,
                    "analytics": "full",
                    "topic_analysis": True,
                    "trial_days": 7,
                },
                is_active=True,
            ),
            SubscriptionPlan(
                name="Pro Monthly",
                plan_type="individual",
                billing_period="monthly",
                price=Decimal("349.00"),
                max_test_attempts_per_period=999,  # Unlimited
                feature_flags={
                    "leaderboard": True,
                    "analytics": "full",
                    "topic_analysis": True,
                },
                is_active=True,
            ),
            SubscriptionPlan(
                name="Pro Yearly",
                plan_type="individual",
                billing_period="monthly",
                price=Decimal("2999.00"),
                max_test_attempts_per_period=999,  # Unlimited
                feature_flags={
                    "leaderboard": True,
                    "analytics": "full",
                    "topic_analysis": True,
                    "billing_period_display": "yearly",
                },
                is_active=True,
            ),
            # Institution plans — Updated pricing structure (REQ-Inst-1)
            SubscriptionPlan(
                name="Starter",
                plan_type="institution",
                billing_period="monthly",
                price=Decimal("1499.00"),
                max_test_attempts_per_period=None,  # Unlimited
                max_student_seats=50,
                feature_flags={
                    "student_limit": 50,
                    "institution_uploads": True,
                    "chapter_wise_tests": True,
                    "basic_analytics": True,
                    "kcet_question_bank": False,
                    "admin_kcet_bank_access": False,
                },
                is_active=True,
            ),
            SubscriptionPlan(
                name="Basic",
                plan_type="institution",
                billing_period="monthly",
                price=Decimal("2999.00"),
                max_test_attempts_per_period=None,  # Unlimited
                max_student_seats=100,
                feature_flags={
                    "student_limit": 100,
                    "institution_uploads": True,
                    "analytics": True,
                    "suggestions_and_guidance": True,
                },
                is_active=True,
            ),
            SubscriptionPlan(
                name="Premium",
                plan_type="institution",
                billing_period="monthly",
                price=Decimal("7999.00"),
                max_test_attempts_per_period=None,  # Unlimited
                max_student_seats=None,  # Unlimited students
                feature_flags={
                    "student_limit": "unlimited",
                    "institution_uploads": True,
                    "institution_question_bank": True,
                    "chapter_wise_exams": True,
                    "ai_analytics": True,
                    "advanced_reports": True,
                    "institution_branding": True,
                    "kcet_question_bank_access": "full",
                    "admin_kcet_bank_access": "full",
                    "priority_support": True,
                },
                is_active=True,
            ),
            SubscriptionPlan(
                name="Enterprise",
                plan_type="institution",
                billing_period="monthly",
                price=Decimal("0.00"),  # Custom pricing — contact sales
                max_test_attempts_per_period=None,  # Unlimited
                max_student_seats=None,  # Unlimited
                feature_flags={
                    "student_limit": "unlimited",
                    "multi_campus": True,
                    "custom_pricing": True,
                    "institution_uploads": True,
                    "institution_question_bank": True,
                    "chapter_wise_exams": True,
                    "ai_analytics": True,
                    "advanced_reports": True,
                    "institution_branding": True,
                    "kcet_question_bank_access": "full",
                    "admin_kcet_bank_access": "full",
                    "dedicated_account_manager": True,
                    "custom_integrations": True,
                    "sla_support": True,
                    "priority_support": True,
                },
                is_active=True,
            ),
        ]

        session.add_all(plans)
        session.commit()
        print(f"Seeded {len(plans)} subscription plans")
        return len(plans)
    except Exception as e:
        session.rollback()
        raise e
    finally:
        if owns_session:
            session.close()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    seed_admin()
    seed_subscription_plans()


if __name__ == "__main__":
    main()


__all__ = ["seed_admin", "seed_subscription_plans", "main"]
