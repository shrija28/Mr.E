"""Session_Token (JWT) issuance and validation.

Design.md §1.4 specifies the claim shape ``{sub, role, iat, exp, jti}``
with HS256 signing.  Student tokens are capped at 24 h
(:data:`STUDENT_TOKEN_TTL_SEC` = 86400) and admin tokens at 8 h
(:data:`ADMIN_TOKEN_TTL_SEC` = 28800).

This module is the **single source** of token issuance for the entire
backend.  The admin-login path (REQ-3.2 / Property 7) is required to have
exactly one ``issue_token(...)`` call site — that call lives in
:mod:`smartkcet.auth.routes` and is gated on a full credential match.
A test hook, :data:`TOKEN_ISSUE_INVOKED`, lets property tests spy on
issuance to confirm the no-token-on-failure guarantee.
"""

from __future__ import annotations

import os
import time
import uuid
from collections import Counter
from datetime import datetime
from typing import Literal

import jwt
from sqlalchemy.orm import Session

from ..db.models import RevokedToken

# Token lifetimes (seconds).  REQ-2.5, REQ-3.1, Property 4.
STUDENT_TOKEN_TTL_SEC = 24 * 60 * 60  # 86 400
ADMIN_TOKEN_TTL_SEC = 8 * 60 * 60  # 28 800

ALGORITHM = "HS256"

# Test spy (Property 7).  ``TOKEN_ISSUE_INVOKED["student" | "admin"]`` is
# incremented exactly once per successful :func:`issue_token` call.
TOKEN_ISSUE_INVOKED: Counter = Counter()


def reset_token_counter() -> None:
    """Reset the :data:`TOKEN_ISSUE_INVOKED` counter (used by tests)."""

    TOKEN_ISSUE_INVOKED.clear()


# ---------------------------------------------------------------------------
# Secret resolution
# ---------------------------------------------------------------------------


# Development fallback.  The real startup guard (task 3.1) will require
# JWT_SECRET to be set in the environment and refuse to boot otherwise.
# Picking a stable-but-clearly-non-prod string here keeps imports working
# during the structural refactor.
_DEV_JWT_SECRET = "smartkcet-dev-secret-do-not-use-in-prod"


def _secret() -> str:
    return os.getenv("JWT_SECRET") or _DEV_JWT_SECRET


# ---------------------------------------------------------------------------
# Issuance
# ---------------------------------------------------------------------------


Role = Literal["platform_admin", "institution_admin", "student"]


def _ttl_for(role: Role) -> int:
    if role == "student":
        return STUDENT_TOKEN_TTL_SEC
    if role in ("platform_admin", "institution_admin"):
        return ADMIN_TOKEN_TTL_SEC
    raise ValueError(f"unknown role: {role!r}")


def issue_token(
    *,
    sub: str,
    role: Role,
    student_subtype: str | None = None,
    institution_id: str | None = None,
    subscription_status: str | None = None,
) -> tuple[str, str, int, int]:
    """Mint a new Session_Token with extended claims.

    Parameters
    ----------
    sub
        Subject claim — the KCET_Student_ID for students, the admin email
        for platform_admin, or the institution_admin email.
    role
        One of ``"platform_admin"``, ``"institution_admin"``, or ``"student"``.
        Picks the TTL bound.
    student_subtype
        For students: one of ``"direct_subscriber"``, ``"institution_linked"``,
        or ``"dual"``. Required when role is ``"student"``.
    institution_id
        Institution UUID string. Required for ``"institution_admin"`` and
        institution-linked/dual students.
    subscription_status
        Current subscription status for students (e.g., ``"trial"``, ``"active"``,
        ``"expired"``). Required when role is ``"student"``.

    Returns
    -------
    tuple
        ``(token, jti, iat_unix, exp_unix)``
    """

    if not isinstance(sub, str) or not sub:
        raise ValueError("sub must be a non-empty string")

    ttl = _ttl_for(role)
    iat = int(time.time())
    exp = iat + ttl
    jti = uuid.uuid4().hex

    payload = {
        "sub": sub,
        "role": role,
        "iat": iat,
        "exp": exp,
        "jti": jti,
    }

    # Add extended claims based on role
    if role == "student":
        if student_subtype:
            payload["student_subtype"] = student_subtype
        if subscription_status:
            payload["subscription_status"] = subscription_status

    # Add institution_id for institution_admin and institution-linked students
    if role == "institution_admin" and institution_id:
        payload["institution_id"] = institution_id
    elif role == "student" and student_subtype in ("institution_linked", "dual") and institution_id:
        payload["institution_id"] = institution_id

    token = jwt.encode(payload, _secret(), algorithm=ALGORITHM)
    # PyJWT >=2 returns ``str`` already; older versions returned ``bytes``.
    if isinstance(token, bytes):  # pragma: no cover - safety belt
        token = token.decode("utf-8")

    TOKEN_ISSUE_INVOKED[role] += 1
    return token, jti, iat, exp


# ---------------------------------------------------------------------------
# Decode / validation
# ---------------------------------------------------------------------------


class TokenError(Exception):
    """Raised when a Session_Token fails validation."""


def decode_token(raw: str) -> dict:
    """Decode and signature-verify ``raw``; raise :class:`TokenError` on failure."""

    if not isinstance(raw, str) or not raw:
        raise TokenError("missing token")
    try:
        return jwt.decode(raw, _secret(), algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError as exc:
        raise TokenError("expired token") from exc
    except jwt.InvalidTokenError as exc:
        raise TokenError("invalid token") from exc


def is_revoked(session: Session, jti: str) -> bool:
    """Return ``True`` iff ``jti`` has been logged out."""

    if not jti:
        return False
    return session.get(RevokedToken, jti) is not None


def validate_token(session: Session, raw: str) -> dict:
    """Decode ``raw`` and reject revoked ``jti`` values.

    This is the helper that RBAC middleware (task 3.3) and the logout
    endpoint use to short-circuit further auth work.
    """

    payload = decode_token(raw)
    jti = payload.get("jti")
    if jti and is_revoked(session, jti):
        raise TokenError("token revoked")
    return payload


def revoke_token(session: Session, jti: str, expires_at: datetime | None = None) -> bool:
    """Record ``jti`` in the revocation table.

    Returns ``True`` when a new row was inserted, ``False`` when the
    ``jti`` was already present (idempotent semantics — REQ-2.7).
    """

    if not jti:
        return False
    if session.get(RevokedToken, jti) is not None:
        return False
    session.add(RevokedToken(jti=jti, expires_at=expires_at))
    return True


def revoke_user_tokens(session: Session, user_id: uuid.UUID) -> int:
    """Revoke all active tokens for a user (used when subtype/institution changes).

    This is called when a student's subtype or institution linkage changes,
    requiring re-authentication with updated token claims (REQ-10.7).

    Returns the count of tokens revoked.

    Note: This is a simplified implementation that relies on the user
    re-authenticating. In a production system with token tracking, you would
    query active tokens by user_id and revoke them individually.
    """
    # Since we don't track user_id -> jti mappings in the current schema,
    # this function serves as a placeholder for the token invalidation logic.
    # The actual enforcement happens when the user makes their next request:
    # the middleware will detect the mismatch between token claims and DB state.
    # For now, we return 0 to indicate no direct revocations were made.
    return 0


__all__ = [
    "ADMIN_TOKEN_TTL_SEC",
    "ALGORITHM",
    "STUDENT_TOKEN_TTL_SEC",
    "TOKEN_ISSUE_INVOKED",
    "TokenError",
    "Role",
    "decode_token",
    "is_revoked",
    "issue_token",
    "reset_token_counter",
    "revoke_token",
    "revoke_user_tokens",
    "validate_token",
]
