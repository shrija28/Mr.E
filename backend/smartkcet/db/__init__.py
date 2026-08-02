"""Database package — declarative base, ORM models, and session factory.

Re-exports the most commonly used names so callers can write::

    from smartkcet.db import Base, User, Subject, get_session

instead of reaching into individual submodules.
"""

from .base import Base
from .models import (
    Exam,
    ExamSet,
    ExamSetQuestion,
    IndexedFile,
    LeaderboardScore,
    Question,
    RevokedToken,
    Subject,
    Submission,
    User,
)
from .session import DATABASE_URL, SessionLocal, engine, get_session
from .subscription_models import (
    BillingRecord,
    Institution,
    Invitation,
    Subscription,
    SubscriptionEvent,
    SubscriptionPlan,
    UsageRecord,
)

__all__ = [
    "Base",
    "DATABASE_URL",
    "Exam",
    "ExamSet",
    "ExamSetQuestion",
    "IndexedFile",
    "LeaderboardScore",
    "Question",
    "RevokedToken",
    "SessionLocal",
    "Subject",
    "Submission",
    "User",
    "engine",
    "get_session",
    "Institution",
    "SubscriptionPlan",
    "Subscription",
    "BillingRecord",
    "UsageRecord",
    "SubscriptionEvent",
    "Invitation",
]
