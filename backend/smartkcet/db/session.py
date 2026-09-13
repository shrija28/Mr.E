"""Database engine + session factory.

The project defaults to PostgreSQL for local/production work and reads the
connection string from ``DATABASE_URL``.  A SQLite fallback remains available
for quick local troubleshooting, but the standard project configuration now
points at PostgreSQL so the app matches the requested production database.

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


# PostgreSQL is the default project database.  If no ``DATABASE_URL`` is
# provided explicitly, the app uses the local PostgreSQL service configured for
# this project.
_DEFAULT_POSTGRES_URL = "postgresql+psycopg2://postgres:postgres@127.0.0.1:5432/smartkcet"
_DEFAULT_SQLITE_PATH = Path(__file__).resolve().parents[2] / "smartkcet.db"
_DEFAULT_DATABASE_URL = _DEFAULT_POSTGRES_URL


def _resolve_database_url()-> str:
    """Read ``DATABASE_URL`` from the environment, falling back to PostgreSQL."""

    return os.getenv("DATABASE_URL", _DEFAULT_DATABASE_URL)


def _build_engine(database_url: str)-> Engine:
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


def _create_tables()-> None:
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


def _add_missing_columns()-> None:
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


def get_session()-> Iterator[Session]:
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


def get_async_session()-> AsyncGenerator[Session, None]:
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


def get_db() -> Session:
    """Return a request-scoped database session attached to Flask g context."""
    from flask import g
    if "db" not in g:
        g.db = SessionLocal()
    return g.db


def teardown_db(exception=None) -> None:
    """Close the request-scoped database session on Flask app teardown."""
    from flask import g
    db = g.pop("db", None)
    if db is not None:
        if exception is not None:
            db.rollback()
        db.close()


__all__ = [
    "DATABASE_URL",
    "engine",
    "SessionLocal",
    "get_session",
    "get_async_session",
    "get_db",
    "teardown_db",
]
