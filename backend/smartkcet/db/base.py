"""Declarative base for all SmartKCET ORM models.

Kept in its own module so that Alembic (task 1.3) and any future utility
script can import :class:`Base` without pulling in the model definitions
themselves.
"""

from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Common declarative base for every ORM model in the project."""

    pass


__all__ = ["Base"]
