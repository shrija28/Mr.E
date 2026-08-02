"""Authentication package — registration, login, JWT issuance, lockout.

Public surface:

* :mod:`smartkcet.auth.identity`   — KCET_Student_ID generator.
* :mod:`smartkcet.auth.passwords`  — bcrypt wrapper + ``HASHING_INVOKED`` test hook.
* :mod:`smartkcet.auth.tokens`     — JWT issuance / validation / revocation.
* :mod:`smartkcet.auth.validation` — pre-DB input checks for register/login.
* :mod:`smartkcet.auth.routes`     — FastAPI router for ``/api/auth/*``.
"""

from .routes import SESSION_COOKIE_NAME, router

__all__ = ["router", "SESSION_COOKIE_NAME"]
