"""Database engine + session factory.

The default development backend is SQLite (``sqlite:///./smartkcet.db``,
resolved relative to the ``backend/`` directory).  Production deployments
override this by setting ``DATABASE_URL`` in the environment — the value is
already loaded for us by :mod:`smartkcet.config`, which calls
``dotenv.load_dotenv`` at import time.

For SQLite specifically we set ``check_same_thread=False`` so a session
created in FastAPI's request thread can be safely consumed by background
helpers spawned via the same dependency-injection scope.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import AsyncGenerator, Iterator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

# Importing config has the side-effect of running ``load_dotenv()`` so any
# ``DATABASE_URL`` defined in ``backend/.env`` is visible here.
from smartkcet import config as _config  # noqa: F401  (import for side-effects)


# The default DB lives next to ``backend/app.py`` regardless of the
# directory the process was launched from.
_DEFAULT_SQLITE_PATH = Path(__file__).resolve().parents[2] / "smartkcet.db"
_DEFAULT_DATABASE_URL = f"sqlite:///{_DEFAULT_SQLITE_PATH.as_posix()}"


def _resolve_database_url() -> str:
    """Read ``DATABASE_URL`` from the environment, falling back to SQLite."""

    return os.getenv("DATABASE_URL", _DEFAULT_DATABASE_URL)


def _build_engine(database_url: str) -> Engine:
    """Create an :class:`Engine` with backend-appropriate connect args."""

    connect_args: dict[str, object] = {}
    if database_url.startswith("sqlite"):
        # FastAPI dependency-injection may share a session across threads.
        connect_args["check_same_thread"] = False

    return create_engine(database_url, connect_args=connect_args, future=True)


DATABASE_URL: str = _resolve_database_url()
engine: Engine = _build_engine(DATABASE_URL)
SessionLocal: sessionmaker[Session] = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
    future=True,
)


def _create_tables() -> None:
    """Auto-create any missing tables (safe with checkfirst=True).

    Imports models to ensure they are registered with Base.metadata
    before calling create_all.
    """
    from .base import Base
    import smartkcet.db.models as _models  # noqa: F401 — register all models
    import smartkcet.db.subscription_models as _sub_models  # noqa: F401 — register subscription models

    Base.metadata.create_all(engine, checkfirst=True)

    # Add new columns to existing tables if they don't exist yet.
    # SQLAlchemy's create_all only creates new tables, not new columns.
    _add_missing_columns()


def _add_missing_columns() -> None:
    """Add columns introduced after initial schema creation (SQLite-safe)."""
    from sqlalchemy import inspect, text

    inspector = inspect(engine)

    # Add exam_name to exams table if missing
    if "exams" in inspector.get_table_names():
        columns = [col["name"] for col in inspector.get_columns("exams")]
        if "exam_name" not in columns:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE exams ADD COLUMN exam_name VARCHAR(200)"))


_create_tables()


def get_session() -> Iterator[Session]:
    """FastAPI dependency / direct call that yields a request-scoped :class:`Session`."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


async def get_async_session() -> AsyncGenerator[Session, None]:
    """Async FastAPI dependency for async route handlers.

    Use this in ``Depends(get_async_session)`` for async routes to avoid
    the anyio contextmanager_in_threadpool path that fails under Python 3.14.
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


__all__ = [
    "DATABASE_URL",
    "engine",
    "SessionLocal",
    "get_session",
    "get_async_session",
]
