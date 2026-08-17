"""Alembic environment for the SmartKCET platform.

Customised for the SmartKCET Platform Upgrade — task 1.3:

* The ``backend/`` directory is prepended to ``sys.path`` so that ``import
  smartkcet`` works regardless of the current working directory the
  ``alembic`` CLI is invoked from.
* ``target_metadata`` is wired to :data:`smartkcet.db.base.Base.metadata`
  with all model modules imported so every table is registered.
* The DB URL is read from :data:`smartkcet.db.session.DATABASE_URL` (which
  honours ``DATABASE_URL`` from ``backend/.env`` and falls back to the
  development SQLite file at ``backend/smartkcet.db``).
* ``render_as_batch`` is enabled in online mode so future ``ALTER`` ops
  work transparently on SQLite.
"""

from __future__ import annotations

import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import engine_from_config, pool

from alembic import context

# ---------------------------------------------------------------------------
# Make ``backend/`` importable so ``import smartkcet`` works from anywhere.
# ---------------------------------------------------------------------------

_BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

# Import after sys.path is fixed.
from smartkcet.db.base import Base  # noqa: E402
from smartkcet.db import models  # noqa: E402, F401  (registers all tables)
from smartkcet.db import subscription_models  # noqa: E402, F401  (registers subscription tables)
from smartkcet.db.session import DATABASE_URL  # noqa: E402

# ---------------------------------------------------------------------------
# Standard alembic boilerplate.
# ---------------------------------------------------------------------------

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Inject the application's DB URL so the ini does not need to hard-code it.
config.set_main_option("sqlalchemy.url", DATABASE_URL.replace("%", "%%"))

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (emit SQL without a live DB)."""

    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=url is not None and url.startswith("sqlite"),
        version_num_dim=64,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode against a live database."""

    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            # Defence in depth: enable batch mode so future ALTERs work on
            # SQLite without rewriting every migration manually.
            render_as_batch=connection.dialect.name == "sqlite",
            version_num_dim=64,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
