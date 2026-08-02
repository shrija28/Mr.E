"""HTTP route registrations.

Modules:

* :mod:`smartkcet.routes.legacy` — the original ExamForge endpoints
  (``/upload``, ``/generate``, ``/analyze``, ``/health``, ``/debug``)
  preserved for backward compatibility during the refactor.
* :mod:`smartkcet.routes.pages` — HTML routes for ``/dashboard`` and
  ``/admin`` with role-aware redirects (task 3.5).

Auth, admin-API, and student-API routers live alongside this package
under :mod:`smartkcet.auth`, :mod:`smartkcet.admin`, and
:mod:`smartkcet.student` respectively.
"""

from . import legacy, pages  # noqa: F401

__all__ = ["legacy", "pages"]
