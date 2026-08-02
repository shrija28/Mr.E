"""HTTP middleware (RBAC dependencies, request logging).

Re-exports the RBAC dependency surface so callers can write::

    from smartkcet.middleware import require_admin, require_student

without reaching into the submodule path.
"""

from .rbac import (
    current_user,
    current_user_id,
    require_admin,
    require_authenticated,
    require_student,
    resolve_payload,
)

__all__ = [
    "current_user",
    "current_user_id",
    "require_admin",
    "require_authenticated",
    "require_student",
    "resolve_payload",
]
