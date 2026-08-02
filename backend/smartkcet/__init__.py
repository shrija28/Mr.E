"""SmartKCET backend package.

This package replaces the original single-file ``backend/app.py`` layout.
It is split into submodules so the platform upgrade tasks (auth, RBAC,
DB-backed question bank, leaderboard, etc.) can be implemented incrementally
without one file growing unbounded.

Sub-packages:

* ``smartkcet.config`` - environment-driven configuration values.
* ``smartkcet.main``   - FastAPI application factory / module-level ``app``.
* ``smartkcet.rag``    - RAG pipeline (FAISS store, parsing helpers, Groq).
* ``smartkcet.routes`` - HTTP route registrations (currently the legacy
  upload/generate/analyze/health endpoints; will gain student/admin
  routers in later tasks).
* ``smartkcet.auth``, ``smartkcet.submissions``, ``smartkcet.leaderboard``,
  ``smartkcet.admin``, ``smartkcet.db``, ``smartkcet.middleware`` are stub
  packages reserved for upcoming tasks.
"""

__all__ = ["main", "config"]
