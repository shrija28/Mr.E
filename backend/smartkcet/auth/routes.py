"""HTTP endpoints for the Auth_Service.

Mounted under ``/api/auth`` from :mod:`smartkcet.main`:

* ``POST /api/auth/register``     — REQ-1.x, registration with pre-hash
                                     duplicate-email check.
* ``POST /api/auth/login``        — REQ-2.x, student login with lockout.
* ``POST /api/auth/admin/login``  — REQ-3.x, admin login with the
                                     no-token-on-failure guarantee.
* ``POST /api/auth/logout``       — REQ-2.7, jti-revocation logout.

The endpoints are deliberately kept compact so the duplicate-email-before-
hashing ordering (REQ-1.2 / Property 2) and the single ``issue_token(...)``
call site for admin login (REQ-3.2 / Property 7) are obvious from a
straight read of the file.
"""

from __future__ import annotations

import hmac
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, Request, Response, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm import Session

from ..db.models import User
from ..db.session import get_async_session as get_session
from .admin_config import load_admin_credentials
from .identity import next_kcet_id, next_institution_student_id
from .passwords import hash_password, verify_password
from .tokens import (
    ADMIN_TOKEN_TTL_SEC,
    STUDENT_TOKEN_TTL_SEC,
    TokenError,
    issue_token,
    revoke_token,
    validate_token,
)
from .validation import (
    ValidationFailure,
    validate_display_name,
    validate_email,
    validate_password,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


# Cookie used by the browser session.  REQ-14.5 — token never lives in
# localStorage; ``httpOnly`` keeps it out of JS reach.
SESSION_COOKIE_NAME = "smartkcet_session"

# REQ-2.6 lockout policy.
MAX_FAILED_LOGINS = 5
LOCKOUT_WINDOW = timedelta(minutes=15)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _now() -> datetime:
    """UTC ``now``.  ORM columns store naive UTC, so strip tzinfo."""

    return datetime.now(timezone.utc).replace(tzinfo=None)


def _set_session_cookie(response: Response, token: str, max_age: int) -> None:
    """Write the Session_Token to an ``httpOnly`` cookie."""

    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        max_age=max_age,
        httponly=True,
        samesite="lax",
        secure=False,  # production should set secure=True (TLS-only).
        path="/",
    )


def _clear_session_cookie(response: Response) -> None:
    response.delete_cookie(key=SESSION_COOKIE_NAME, path="/")


def _validation_error(failure: ValidationFailure) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": "validation_error",
            "field": failure.field,
            "message": failure.reason,
        },
    )


# REQ-2.2 / REQ-3.2: byte-identical generic auth failure response.  The
# function returns a fresh dict each time so callers can't mutate the
# canonical body.
def _generic_auth_failure() -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"error": "auth_failed", "message": "Invalid credentials"},
    )


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------


class RegisterRequest(BaseModel):
    email: str
    password: str
    display_name: str
    invite_code: Optional[str] = None  # If provided, auto-links to institution on signup


class LoginRequest(BaseModel):
    email: str
    password: str


# ---------------------------------------------------------------------------
# POST /api/auth/register
# ---------------------------------------------------------------------------


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, session: Session = Depends(get_session)) -> Any:
    """Register a new student account.

    Order of operations:
    1. Pure validation (no DB, no hashing)
    2. Duplicate-email SELECT (DB)
    3. Check if invite code is valid (if provided)
    4. hash_password (only if step 2 found nothing)
    5. Generate appropriate student ID (KCET#### or institution-specific)
    6. INSERT user with ID

    Steps 4, 5, and 6 share a transaction so a crash leaves the DB clean.
    The UNIQUE constraint on users.email and users.kcet_student_id provides race guards.
    """

    # Step 1 — validation. No DB / no hashing yet.
    email_v = validate_email(payload.email)
    if isinstance(email_v, ValidationFailure):
        return _validation_error(email_v)

    password_v = validate_password(payload.password)
    if isinstance(password_v, ValidationFailure):
        return _validation_error(password_v)

    name_v = validate_display_name(payload.display_name)
    if isinstance(name_v, ValidationFailure):
        return _validation_error(name_v)

    normalised_email = email_v.lower()

    # Step 2 — duplicate-email pre-check. Runs BEFORE hash_password.
    existing = session.execute(
        select(User.id).where(User.email == normalised_email)
    ).first()
    if existing is not None:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "error": "email_already_registered",
                "message": "This email is already registered.",
            },
        )

    # Step 3 — Check if invite code is provided and valid
    invitation = None
    institution_for_linking = None
    institution_student_id = None
    
    if payload.invite_code and payload.invite_code.strip():
        invite_code = payload.invite_code.strip()
        try:
            from ..db.subscription_models import Invitation, Institution
            import logging as _log
            
            _logger = _log.getLogger("smartkcet.auth.register")
            
            invitation = session.query(Invitation).filter(
                Invitation.code == invite_code,
                Invitation.status == "pending",
            ).first()
            
            if invitation is None:
                _logger.warning("Register invite-link: invitation code %r not found or not pending", invite_code)
            elif invitation.expires_at is None or invitation.expires_at < datetime.utcnow():
                _logger.warning("Register invite-link: invitation code %r expired (expires_at=%s)", invite_code, invitation.expires_at)
                invitation = None
            else:
                # Get institution and check it has a code
                institution_for_linking = session.query(Institution).filter(
                    Institution.id == invitation.institution_id
                ).first()
                
                if institution_for_linking and institution_for_linking.institution_code:
                    # Pre-generate institution-specific ID before creating user
                    try:
                        institution_student_id = next_institution_student_id(
                            session, 
                            str(invitation.institution_id)
                        )
                        _logger.info(
                            "Pre-generated institution student ID: %s for institution: %s",
                            institution_student_id,
                            institution_for_linking.name
                        )
                    except Exception as e:
                        _logger.warning("Failed to pre-generate institution student ID: %s", e)
                        institution_student_id = None
                else:
                    _logger.warning(
                        "Institution %s does not have institution_code set",
                        institution_for_linking.id if institution_for_linking else invitation.institution_id
                    )
        except Exception as e:
            import logging
            logging.getLogger("smartkcet.auth").warning(
                "Failed to validate invite code %s: %s", payload.invite_code, e
            )

    # Step 4 — hashing. Reachable only when the email is free.
    password_hash = hash_password(password_v)

    # Step 5 — Generate appropriate student ID
    if institution_student_id:
        # Use institution-specific ID if available
        student_id = institution_student_id
    else:
        # Use generic KCET#### ID
        student_id = next_kcet_id(session)

    # Step 6 — Create and persist user
    user = User(
        email=normalised_email,
        kcet_student_id=student_id,
        display_name=name_v,
        password_hash=password_hash,
        role="student",
        student_subtype="direct_subscriber",  # default; may be changed below
    )
    session.add(user)
    try:
        session.commit()
    except IntegrityError:
        # A concurrent register hit the unique constraint after our pre-check.
        session.rollback()
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "error": "email_already_registered",
                "message": "This email is already registered.",
            },
        )

    # Step 7 — If invite_code is valid, finalize institution linking
    institution_name = None
    institution_id_for_token = None
    if invitation and institution_for_linking:
        try:
            from ..institution.service import InstitutionService
            import logging as _log

            _logger = _log.getLogger("smartkcet.auth.register")
            
            inst_service = InstitutionService(session)
            inst_service.accept_invitation(invite_code, user.id)
            # Refresh user to pick up institution_id and updated subtype
            session.refresh(user)
            # Ensure subtype is set
            if user.student_subtype != "institution_linked":
                user.student_subtype = "institution_linked"
                session.commit()
                session.refresh(user)
            
            institution_name = institution_for_linking.name
            institution_id_for_token = str(user.institution_id) if user.institution_id else None
            _logger.info(
                "Register invite-link SUCCESS: user=%s subtype=%s institution_id=%s institution=%s",
                user.kcet_student_id, user.student_subtype, user.institution_id, institution_name,
            )
        except Exception as e:
            # Don't fail registration if invite linking fails — user is already created
            import logging
            logging.getLogger("smartkcet.auth").warning(
                "Auto-link to institution failed for invite code %s: %s", payload.invite_code, e
            )

    # Step 8 — Build response message
    if institution_for_linking and institution_student_id:
        message = f"Account created! Your Student ID: {institution_student_id} ({institution_name})"
    else:
        message = f"Account created! Your Student ID: {student_id}"

    response_data = {
        "kcet_student_id": student_id,
        "email": normalised_email,
        "display_name": name_v,
        "message": message,
    }

    # If the student was linked to an institution, auto-login by issuing a
    # session cookie so the frontend can redirect straight to their institution platform.
    if institution_name:
        response_data["institution_name"] = institution_name
        response_data["institution_linked"] = True
        response_data["auto_login"] = True

        # Build a JSONResponse so we can attach the cookie
        from fastapi.responses import JSONResponse as _JSONResponse

        # Issue JWT for the newly-registered institution student
        token, _jti, _iat, _exp = issue_token(
            sub=user.kcet_student_id,
            role="student",
            student_subtype="institution_linked",
            institution_id=institution_id_for_token,
            subscription_status=None,
        )
        resp = _JSONResponse(content=response_data, status_code=status.HTTP_201_CREATED)
        _set_session_cookie(resp, token, max_age=STUDENT_TOKEN_TTL_SEC)
        return resp

    return response_data


# ---------------------------------------------------------------------------
# POST /api/auth/login (student)
# ---------------------------------------------------------------------------


def _is_locked(user: User, now: datetime) -> bool:
    return user.lockout_until is not None and user.lockout_until > now


def _record_failed_attempt(user: User, now: datetime) -> None:
    """Increment counter and lock account on the 5th consecutive failure."""

    user.failed_login_count = (user.failed_login_count or 0) + 1
    if user.failed_login_count >= MAX_FAILED_LOGINS:
        user.lockout_until = now + LOCKOUT_WINDOW


def _reset_lockout(user: User) -> None:
    user.failed_login_count = 0
    user.lockout_until = None


@router.post("/login")
def login(
    payload: LoginRequest,
    response: Response,
    session: Session = Depends(get_session),
) -> Any:
    """Student login with lockout policy and generic-failure response.

    Per REQ-2.2 / Property 3 the response for "wrong password" and
    "unregistered email" is byte-identical.  Lockout (REQ-2.6 /
    Property 5) returns a separate 423 response carrying the remaining
    wait time.
    """

    # Lightweight shape check — empty strings short-circuit to the
    # generic auth failure (no DB call needed).
    if not isinstance(payload.email, str) or not payload.email:
        return _generic_auth_failure()
    if not isinstance(payload.password, str) or not payload.password:
        return _generic_auth_failure()

    normalised_email = payload.email.strip().lower()
    now = _now()

    try:
        user = session.execute(
            select(User).where(User.email == normalised_email)
        ).scalar_one_or_none()
    except OperationalError:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "error": "service_unavailable",
                "message": "Database temporarily unavailable. Please try again later.",
            },
        )

    # Unregistered email or non-student user
    if user is None or user.role != "student":
        return _generic_auth_failure()

    # Locked account → 423, with remaining wait time.
    if _is_locked(user, now):
        retry_after_sec = max(int((user.lockout_until - now).total_seconds()), 1)
        # Failed login while locked does NOT increment the counter
        # (design.md §1.5).
        return JSONResponse(
            status_code=status.HTTP_423_LOCKED,
            content={
                "error": "account_locked",
                "message": "Account temporarily locked. Try again later.",
                "retry_after_sec": retry_after_sec,
            },
            headers={"Retry-After": str(retry_after_sec)},
        )

    # Lockout window may have elapsed since the last attempt — clean up
    # before evaluating the password (design.md §1.5 row 5).
    if user.lockout_until is not None and user.lockout_until <= now:
        _reset_lockout(user)

    if not verify_password(payload.password, user.password_hash):
        _record_failed_attempt(user, now)
        try:
            session.commit()
        except OperationalError:
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={
                    "error": "service_unavailable",
                    "message": "Database temporarily unavailable. Please try again later.",
                },
            )
        return _generic_auth_failure()

    # Successful login.
    _reset_lockout(user)
    try:
        session.commit()
    except OperationalError:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "error": "service_unavailable",
                "message": "Database temporarily unavailable. Please try again later.",
            },
        )

    # Get subscription status for token claims
    from ..db.subscription_models import Subscription
    from sqlalchemy import and_

    subscription_status = None
    active_subscription = session.execute(
        select(Subscription)
        .where(
            and_(
                Subscription.user_id == user.id,
                Subscription.status.in_(["trial", "active", "overdue", "grace_period"]),
            )
        )
    ).scalar_one_or_none()

    if active_subscription:
        subscription_status = active_subscription.status

    # Check if user needs subscription selection (for popup on frontend)
    from ..subscription.service import SubscriptionService
    subscription_service = SubscriptionService(session)
    needs_subscription_selection = subscription_service.needs_subscription_selection(user.id)

    # Issue token with extended claims — read from DB (authoritative, not cached)
    token, _jti, _iat, _exp = issue_token(
        sub=user.kcet_student_id,
        role="student",
        student_subtype=user.student_subtype,
        institution_id=str(user.institution_id) if user.institution_id else None,
        subscription_status=subscription_status,
    )
    _set_session_cookie(response, token, max_age=STUDENT_TOKEN_TTL_SEC)

    import logging as _log
    _log.getLogger("smartkcet.auth.login").info(
        "LOGIN: kcet_id=%s subtype=%s institution_id=%s needs_popup=%s redirect=%s",
        user.kcet_student_id,
        user.student_subtype,
        user.institution_id,
        needs_subscription_selection,
        "/student/institution/dashboard" if user.student_subtype == "institution_linked" else "/dashboard",
    )

    return {
        "kcet_student_id": user.kcet_student_id,
        "display_name": user.display_name,
        "role": "student",
        "student_subtype": user.student_subtype,
        # redirect hint for the client — institution students go to their platform
        "redirect": "/student/institution/dashboard" if user.student_subtype == "institution_linked" else "/dashboard",
        # Include subscription selection flag for frontend popup logic
        "needs_subscription_selection": needs_subscription_selection,
    }


# ---------------------------------------------------------------------------
# POST /api/auth/admin/login
# ---------------------------------------------------------------------------


@router.post("/admin/login")
async def admin_login(
    payload: LoginRequest,
    response: Response,
    session: Session = Depends(get_session),
) -> Any:
    """Admin login.  REQ-3.2 / Property 7 — no token of any kind on failure.

    The handler resolves the configured admin credentials from environment or database,
    runs a constant-time email compare and a bcrypt password verify.
    The ``issue_token(...)`` call site lives at the bottom of the function.
    """

    email_str = payload.email.strip().lower() if isinstance(payload.email, str) else ""
    password_str = payload.password if isinstance(payload.password, str) else ""

    if not email_str or not password_str:
        return _generic_auth_failure()

    # 1. Check env-configured admin credentials
    creds = load_admin_credentials()
    authenticated = False
    admin_email = email_str

    if creds and hmac.compare_digest(email_str, creds.email):
        if verify_password(password_str, creds.password_hash):
            authenticated = True
            admin_email = creds.email

    # 2. If env check didn't match, check database for platform_admin user
    if not authenticated:
        try:
            db_user = session.execute(
                select(User).where(
                    User.email == email_str,
                    User.role.in_(["platform_admin", "admin"]),
                )
            ).scalar_one_or_none()
            if db_user and verify_password(password_str, db_user.password_hash):
                authenticated = True
                admin_email = db_user.email
        except OperationalError:
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={
                    "error": "service_unavailable",
                    "message": "Database temporarily unavailable. Please try again later.",
                },
            )

    if not authenticated:
        # No Set-Cookie header is written.  No token is issued.  The
        # response body is identical to the student-login generic failure.
        return _generic_auth_failure()

    # Single issuance site, gated on full credential match.
    token, _jti, _iat, _exp = issue_token(sub=admin_email, role="platform_admin")
    _set_session_cookie(response, token, max_age=ADMIN_TOKEN_TTL_SEC)
    return {
        "role": "platform_admin",
        "email": admin_email,
        "redirect": "/admin/upload",
    }


# ---------------------------------------------------------------------------
# POST /api/auth/institution/login
# ---------------------------------------------------------------------------


@router.post("/institution/login")
async def institution_admin_login(
    payload: LoginRequest,
    response: Response,
    session: Session = Depends(get_session),
) -> Any:
    """Institution admin login with lockout policy.

    Enforces the same lockout policy as student login (5 failed attempts,
    15-minute lockout) per REQ-6.5.
    """

    # Lightweight shape check
    if not isinstance(payload.email, str) or not payload.email:
        return _generic_auth_failure()
    if not isinstance(payload.password, str) or not payload.password:
        return _generic_auth_failure()

    normalised_email = payload.email.strip().lower()
    now = _now()

    try:
        user = session.execute(
            select(User).where(
                User.email == normalised_email, User.role == "institution_admin"
            )
        ).scalar_one_or_none()
    except OperationalError:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "error": "service_unavailable",
                "message": "Database temporarily unavailable. Please try again later.",
            },
        )

    # Unregistered email → generic failure
    if user is None:
        return _generic_auth_failure()

    # Locked account → 423
    if _is_locked(user, now):
        retry_after_sec = max(int((user.lockout_until - now).total_seconds()), 1)
        return JSONResponse(
            status_code=status.HTTP_423_LOCKED,
            content={
                "error": "account_locked",
                "message": "Account temporarily locked. Try again later.",
                "retry_after_sec": retry_after_sec,
            },
            headers={"Retry-After": str(retry_after_sec)},
        )

    # Clean up expired lockout
    if user.lockout_until is not None and user.lockout_until <= now:
        _reset_lockout(user)

    # Verify password
    if not verify_password(payload.password, user.password_hash):
        _record_failed_attempt(user, now)
        try:
            session.commit()
        except OperationalError:
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={
                    "error": "service_unavailable",
                    "message": "Database temporarily unavailable. Please try again later.",
                },
            )
        return _generic_auth_failure()

    # Successful login
    _reset_lockout(user)
    try:
        session.commit()
    except OperationalError:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "error": "service_unavailable",
                "message": "Database temporarily unavailable. Please try again later.",
            },
        )

    # Issue token with institution_id claim
    token, _jti, _iat, _exp = issue_token(
        sub=user.email,
        role="institution_admin",
        institution_id=str(user.institution_id) if user.institution_id else None,
    )
    _set_session_cookie(response, token, max_age=ADMIN_TOKEN_TTL_SEC)

    return {
        "email": user.email,
        "display_name": user.display_name,
        "role": "institution_admin",
        "institution_id": str(user.institution_id) if user.institution_id else None,
    }


# ---------------------------------------------------------------------------
# POST /api/auth/logout
# ---------------------------------------------------------------------------


@router.post("/logout")
def logout(
    request: Request,
    response: Response,
    session: Session = Depends(get_session),
) -> Any:
    """Revoke the active Session_Token and clear the cookie."""

    raw = request.cookies.get(SESSION_COOKIE_NAME)
    revoked = False
    if raw:
        try:
            payload = validate_token(session, raw)
        except TokenError:
            payload = None
        if payload:
            jti = payload.get("jti")
            exp_unix = payload.get("exp")
            expires_at: datetime | None = None
            if isinstance(exp_unix, (int, float)):
                expires_at = datetime.fromtimestamp(exp_unix, tz=timezone.utc).replace(
                    tzinfo=None
                )
            if revoke_token(session, jti, expires_at=expires_at):
                session.commit()
                revoked = True

    _clear_session_cookie(response)
    return {"logged_out": True, "revoked": revoked}


# ---------------------------------------------------------------------------
# GET /api/auth/me
# ---------------------------------------------------------------------------


@router.get("/me")
def me(
    request: Request,
    session: Session = Depends(get_session),
) -> Any:
    """Return the current user's role and identity.

    Used by the frontend ``auth.js`` module to determine the active
    session without reading the ``httpOnly`` cookie directly.  Returns
    401 when no valid session exists.
    """

    raw = request.cookies.get(SESSION_COOKIE_NAME)
    if not raw:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"error": "not_authenticated", "message": "No active session."},
        )
    try:
        payload = validate_token(session, raw)
    except TokenError:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"error": "not_authenticated", "message": "No active session."},
        )

    role = payload.get("role")
    sub = payload.get("sub")

    result: dict[str, Any] = {"authenticated": True, "role": role, "sub": sub}

    # Include extended claims from token (as fallback)
    if "student_subtype" in payload:
        result["student_subtype"] = payload["student_subtype"]
    if "institution_id" in payload:
        result["institution_id"] = payload["institution_id"]
    if "subscription_status" in payload:
        result["subscription_status"] = payload["subscription_status"]

    # For students, always re-read from DB to get current subtype/institution
    # (the token may be stale if linking happened after token was issued)
    if role == "student":
        user = session.execute(
            select(User).where(User.kcet_student_id == sub)
        ).scalar_one_or_none()
        if user:
            result["display_name"] = user.display_name
            result["kcet_student_id"] = user.kcet_student_id
            # Always use DB values — these are the ground truth
            result["student_subtype"] = user.student_subtype
            result["institution_id"] = str(user.institution_id) if user.institution_id else None
            if user.institution_id:
                from ..db.subscription_models import Institution
                inst = session.get(Institution, user.institution_id)
                if inst:
                    result["institution_name"] = inst.name

    # For institution_admin, include display name
    if role == "institution_admin":
        user = session.execute(
            select(User).where(User.email == sub, User.role == "institution_admin")
        ).scalar_one_or_none()
        if user:
            result["display_name"] = user.display_name

    return result


__all__ = ["router", "SESSION_COOKIE_NAME"]
