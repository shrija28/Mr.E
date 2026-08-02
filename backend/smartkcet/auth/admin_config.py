"""Admin credential lookup used by ``POST /api/auth/admin/login``.

The full startup config guard (REQ-3.5) lands in task 3.1; until then
this helper reads ``ADMIN_EMAIL`` and ``ADMIN_PASSWORD_HASH`` from the
environment on demand and returns ``None`` when either is missing or
malformed.  Returning ``None`` causes admin login to fall through to the
generic 401 response — which is precisely the no-token-on-failure
guarantee in REQ-3.2 / Property 7: with no admin credentials configured,
*every* admin login attempt fails, and no token of any kind is issued.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class AdminCredentials:
    email: str
    password_hash: str


def load_admin_credentials() -> Optional[AdminCredentials]:
    """Return the configured admin credentials, or ``None`` if absent."""

    email = (os.getenv("ADMIN_EMAIL") or "").strip()
    password_hash = (os.getenv("ADMIN_PASSWORD_HASH") or "").strip()

    if not email or not password_hash:
        return None
    if "@" not in email or len(email) > 254:
        return None
    return AdminCredentials(email=email.lower(), password_hash=password_hash)


__all__ = ["AdminCredentials", "load_admin_credentials"]
