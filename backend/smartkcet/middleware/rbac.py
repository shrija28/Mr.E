"""Role-Based Access Control middleware (FastAPI dependencies).

Implements the contract documented in design.md §1.6:

| Token state                              | Result |
|------------------------------------------|--------|
| Missing on protected endpoint            | 401    |
| Malformed/expired on protected endpoint  | 401    |
| Student role on admin endpoint           | 403    |
| Student requesting another student's data| 403    |
| Admin role on admin endpoint             | proceed|
| Student role on student endpoint         | proceed|

The Session_Token is read from the ``httpOnly`` cookie named
:data:`smartkcet.auth.routes.SESSION_COOKIE_NAME` (``smartkcet_session``).
Decoding and revocation checks delegate to
:func:`smartkcet.auth.tokens.validate_token`, which raises
:class:`TokenError` on any failure (missing signature, malformed payload,
expired ``exp``, or revoked ``jti``).

Public surface
--------------

``require_authenticated``
    FastAPI dependency. Returns the decoded JWT payload dict
    (``{sub, role, iat, exp, jti}``).  Raises ``HTTPException(401)`` when
    the cookie is missing or the token fails validation.

``require_student``
    FastAPI dependency.  Builds on ``require_authenticated`` and adds a
    role guard: raises ``HTTPException(403)`` when ``role != 'student'``.

``require_admin``
    FastAPI dependency.  Builds on ``require_authenticated`` and adds a
    role guard: raises ``HTTPException(403)`` when ``role != 'admin'``.

``current_user_id(request)``
    Best-effort helper that returns the ``sub`` claim from the cookie
    token (the KCET_Student_ID for students, the admin email for admins)
    or ``None`` when no valid token is present.  Intended for
    data-scoping queries (e.g. "submissions for *this* student").
    Does **not** raise — callers that need enforcement should depend on
    ``require_student`` / ``require_admin`` separately.

``current_user(request, session)``
    Best-effort helper that resolves the cookie token to the matching
    :class:`User` ORM row, or ``None`` when the token is absent /
    invalid / does not point at a known user.  Used by endpoints that
    need the full user record (display name, email, etc.).

``resolve_payload(request, session)``
    Best-effort helper used by HTML route handlers (task 3.5) to decide
    whether to render the page or issue a ``RedirectResponse``.
    Returns the decoded payload or ``None``; never raises.

JSON vs HTML routes
-------------------

These dependencies always raise ``HTTPException`` (401/403) — they are
the primary surface for the ``/api/*`` JSON routes.  HTML/browser
routes (task 3.5) inspect the cookie via :func:`resolve_payload` and
issue a ``RedirectResponse`` to ``/login`` (unauthenticated) or to the
role-appropriate home (``/dashboard`` / ``/admin``) on role mismatch.
"""

from __future__ import annotations

from typing import Any, Optional

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth.routes import SESSION_COOKIE_NAME
from ..auth.tokens import TokenError, validate_token
from ..db.models import User
from ..db.session import get_async_session as get_session


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _read_token(request: Request) -> Optional[str]:
    """Return the raw Session_Token from the cookie, or ``None``."""

    raw = request.cookies.get(SESSION_COOKIE_NAME)
    if not isinstance(raw, str) or not raw:
        return None
    return raw


def _unauthorized() -> HTTPException:
    """401 used for missing/malformed/expired tokens on protected endpoints."""

    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={"error": "auth_required", "message": "Authentication required."},
    )


def _forbidden() -> HTTPException:
    """403 used for role mismatch and cross-student data access."""

    return HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail={"error": "forbidden", "message": "Access denied."},
    )


# ---------------------------------------------------------------------------
# FastAPI dependencies — primary surface for /api/* routes
# ---------------------------------------------------------------------------


async def require_authenticated(
    request: Request,
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    """Require any authenticated user."""
    raw = _read_token(request)
    if raw is None:
        raise _unauthorized()
    try:
        payload = validate_token(session, raw)
    except TokenError as exc:
        raise _unauthorized() from exc
    return payload


async def require_student(
    payload: dict[str, Any] = Depends(require_authenticated),
) -> dict[str, Any]:
    """Require a student-role Session_Token."""
    if payload.get("role") != "student":
        raise _forbidden()
    return payload


async def require_admin(
    payload: dict[str, Any] = Depends(require_authenticated),
) -> dict[str, Any]:
    """Require a platform_admin-role Session_Token."""
    if payload.get("role") != "platform_admin":
        raise _forbidden()
    return payload


async def require_platform_admin(
    payload: dict[str, Any] = Depends(require_authenticated),
) -> dict[str, Any]:
    """Require a platform_admin-role Session_Token. Alias for require_admin."""
    if payload.get("role") != "platform_admin":
        raise _forbidden()
    return payload


async def require_institution_admin(
    payload: dict[str, Any] = Depends(require_authenticated),
) -> dict[str, Any]:
    """Require an institution_admin-role Session_Token."""
    if payload.get("role") != "institution_admin":
        raise _forbidden()
    return payload


# ---------------------------------------------------------------------------
# Best-effort helpers — never raise
# ---------------------------------------------------------------------------


def resolve_payload(
    request: Request, session: Session
) -> Optional[dict[str, Any]]:
    """Return the decoded JWT payload, or ``None`` on any failure.

    HTML route handlers (task 3.5) call this to choose between rendering
    the page and issuing a ``RedirectResponse``.  Never raises.
    """

    raw = _read_token(request)
    if raw is None:
        return None
    try:
        return validate_token(session, raw)
    except TokenError:
        return None


def current_user_id(request: Request) -> Optional[str]:
    """Return the ``sub`` claim from the cookie token, or ``None``.

    For student tokens this is the ``KCET_Student_ID`` and is the value
    that data-scoping queries should filter ``submissions.user_id`` /
    similar columns by.  For admin tokens this is the configured admin
    email.

    This helper does **not** consult the revocation table — it is a
    convenience for endpoints that have already passed through one of
    the ``require_*`` dependencies (which performs the revocation
    check).  Standalone callers that need enforcement should use the
    dependencies instead.
    """

    raw = _read_token(request)
    if raw is None:
        return None
    # Decode without revocation check — callers that need enforcement
    # are expected to depend on require_authenticated, which already
    # validates revocation.  Decoding still verifies signature + exp.
    try:
        from ..auth.tokens import decode_token  # local import keeps module load light

        payload = decode_token(raw)
    except TokenError:
        return None
    sub = payload.get("sub")
    return sub if isinstance(sub, str) else None


def current_user(request: Request, session: Session) -> Optional[User]:
    """Resolve the cookie token to a :class:`User` ORM row, or ``None``.

    The lookup column depends on role:

    * ``role == 'student'`` → ``users.kcet_student_id == sub``
    * ``role == 'platform_admin'``   → ``users.email == sub``
    * ``role == 'institution_admin'`` → ``users.email == sub``

    Returns ``None`` when the token is absent, invalid, revoked, or
    points at a user that no longer exists.
    """

    payload = resolve_payload(request, session)
    if payload is None:
        return None
    sub = payload.get("sub")
    role = payload.get("role")
    if not isinstance(sub, str) or not sub:
        return None

    if role == "student":
        stmt = select(User).where(User.kcet_student_id == sub)
    elif role in ("platform_admin", "institution_admin"):
        stmt = select(User).where(User.email == sub)
    else:
        return None

    return session.execute(stmt).scalar_one_or_none()


def require_active_subscription(
    payload: dict[str, Any] = Depends(require_authenticated),
) -> dict[str, Any]:
    """Require student with active subscription.

    Raises
    ------
    HTTPException
        401 — propagated from :func:`require_authenticated`.
        403 when the student's subscription is not active (trial, active, or grace_period).
    """

    if payload.get("role") != "student":
        raise _forbidden()
    
    subscription_status = payload.get("subscription_status")
    if subscription_status not in ("trial", "active", "grace_period"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "subscription_required",
                "message": "Active subscription required.",
                "subscription_status": subscription_status,
            },
        )
    
    return payload


def check_feature_access(
    payload: dict[str, Any],
    feature: str,
    session: Session | None = None,
) -> bool:
    """Evaluate access control matrix for a specific feature.
    
    Implements the access control matrix defined in design.md, evaluating
    role + subscription_status + subtype against feature requirements.
    
    **Requirements:** 12.1, 12.2, 12.3, 12.4, 12.5, 12.6, 12.7, 12.8, 12.9, 7.5, 7.6, 7.7, 7.8, 11.5
    
    Features:
    - exam_access: Can start exams
    - full_analytics: Can access full analytics (topic breakdowns, AI recommendations)
    - basic_analytics: Can access basic analytics (score, pass/fail)
    - leaderboard: Can view leaderboard rank
    - question_management: Can manage question banks
    - institution_management: Can manage institution settings
    - platform_settings: Can access platform-wide settings
    
    Access rules:
    - platform_admin: Full access to all features
    - institution_admin: Access to question_management, institution_management (scoped to their institution)
    - student (trial): Limited exam access (5 lifetime), basic_analytics only, no leaderboard
    - student (active/grace_period): Unlimited exams, full_analytics, leaderboard
    - student (expired/cancelled): No access
    - dual subscription: Higher of two permission levels
    
    Args:
        payload: Decoded JWT token payload
        feature: Feature to check access for
        session: Optional database session for dual subscription resolution
        
    Returns:
        True if access is granted, False otherwise
    """
    role = payload.get("role")
    
    # Platform admin has full access to everything
    if role == "platform_admin":
        return True
    
    # Institution admin access
    if role == "institution_admin":
        if feature in ("question_management", "institution_management"):
            return True
        return False
    
    # Student access
    if role == "student":
        subscription_status = payload.get("subscription_status")
        student_subtype = payload.get("student_subtype")
        
        # Handle dual subscription: higher of two permission levels (REQ-12.6)
        # For MVP, dual subscription is treated as having Pro-level access
        # In production, this would query both subscriptions and compare
        if student_subtype == "dual":
            # Treat dual as active for all permission checks
            subscription_status = "active"
        
        # Exam access rules (REQ-12.3)
        if feature == "exam_access":
            # Trial: 5 lifetime attempts (enforced by usage tracker)
            # Active/grace_period: unlimited
            # Institution: plan limits (enforced by usage tracker)
            if subscription_status in ("trial", "active", "grace_period"):
                return True
            return False
        
        # Analytics access rules (REQ-12.4)
        if feature == "basic_analytics":
            # All active subscriptions get basic analytics
            if subscription_status in ("trial", "active", "grace_period"):
                return True
            return False
        
        if feature == "full_analytics":
            # Only Pro (active/grace_period) gets full analytics
            # Trial gets basic only
            if subscription_status in ("active", "grace_period"):
                return True
            return False
        
        # Leaderboard access rules (REQ-12.5)
        if feature == "leaderboard":
            # Trial: hidden
            # Pro: full global
            # Institution: scoped to institution
            if subscription_status in ("active", "grace_period"):
                return True
            return False
        
        # Question bank access (REQ-12.7)
        if feature == "question_management":
            # Only platform_admin and institution_admin
            return False
        
        # Institution management (REQ-12.7)
        if feature == "institution_management":
            # Only platform_admin and institution_admin
            return False
        
        # Platform settings (REQ-11.5)
        if feature == "platform_settings":
            # Only platform_admin
            return False
    
    # Default: deny access
    return False


__all__ = [
    "require_authenticated",
    "require_student",
    "require_admin",
    "require_platform_admin",
    "require_institution_admin",
    "require_active_subscription",
    "check_feature_access",
    "resolve_payload",
    "current_user_id",
    "current_user",
]
