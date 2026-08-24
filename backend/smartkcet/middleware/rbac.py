"""Role-Based Access Control middleware for Flask.

Implements the contract documented in design.md §1.6:

| Token state                              | Result |
|------------------------------------------|--------|
| Missing on protected endpoint            | 401    |
| Malformed/expired on protected endpoint  | 401    |
| Student role on admin endpoint           | 403    |
| Student requesting another student's data| 403    |
| Admin role on admin endpoint             | proceed|
| Student role on student endpoint         | proceed|

Session_Token is read from the httpOnly cookie named SESSION_COOKIE_NAME.
"""

from __future__ import annotations

from functools import wraps
from typing import Any, Callable, Optional, Union

from flask import g, jsonify, request
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth.routes import SESSION_COOKIE_NAME
from ..auth.tokens import TokenError, validate_token
from ..db.models import User
from ..db.session import get_db


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _read_token(req: Any = None) -> Optional[str]:
    """Return the raw Session_Token from cookies or Authorization header, or None."""
    r = req if req is not None and hasattr(req, "cookies") else request
    try:
        raw = r.cookies.get(SESSION_COOKIE_NAME)
        if isinstance(raw, str) and raw:
            return raw
        auth_header = r.headers.get("Authorization") if hasattr(r, "headers") else None
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:].strip()
            if token:
                return token
        return None
    except Exception:
        return None


def _unauthorized():
    return jsonify({"error": "auth_required", "message": "Authentication required."}), 401


def _forbidden():
    return jsonify({"error": "forbidden", "message": "Access denied."}), 403


# ---------------------------------------------------------------------------
# Core Token & User Resolution
# ---------------------------------------------------------------------------


def resolve_payload(req: Any = None, session: Session | None = None) -> Optional[dict[str, Any]]:
    """Return the decoded JWT payload, or None on any failure."""
    db_sess = session if session is not None else get_db()
    raw = _read_token(req)
    if raw is None:
        return None
    try:
        return validate_token(db_sess, raw)
    except TokenError:
        return None


def current_user_id(req: Any = None) -> Optional[str]:
    """Return the sub claim from the cookie token, or None."""
    raw = _read_token(req)
    if raw is None:
        return None
    try:
        from ..auth.tokens import decode_token

        payload = decode_token(raw)
    except TokenError:
        return None
    sub = payload.get("sub")
    return sub if isinstance(sub, str) else None


def current_user(req: Any = None, session: Session | None = None) -> Optional[User]:
    """Resolve the cookie token to a User ORM row, or None."""
    db_sess = session if session is not None else get_db()
    payload = resolve_payload(req, db_sess)
    if payload is None:
        return None
    sub = payload.get("sub")
    role = payload.get("role")
    if not isinstance(sub, str) or not sub:
        return None

    if role == "student":
        stmt = select(User).where(User.kcet_student_id == sub)
    elif role in ("platform_admin", "institution_admin", "admin"):
        stmt = select(User).where(User.email == sub)
    else:
        return None

    return db_sess.execute(stmt).scalar_one_or_none()


# ---------------------------------------------------------------------------
# Flask Decorators & Functions
# ---------------------------------------------------------------------------


def require_authenticated(func: Callable | None = None) -> Any:
    """Require any authenticated user (decorator or function)."""
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            db_sess = get_db()
            raw = _read_token()
            if raw is None:
                return _unauthorized()
            try:
                payload = validate_token(db_sess, raw)
                g.token_payload = payload
                g.user = current_user(request, db_sess)
            except TokenError:
                return _unauthorized()
            return f(*args, **kwargs)

        return wrapper

    if func is not None and callable(func):
        return decorator(func)

    db_sess = get_db()
    raw = _read_token()
    if raw is None:
        return None
    try:
        return validate_token(db_sess, raw)
    except TokenError:
        return None


def require_student(func: Callable | None = None) -> Any:
    """Require student role (decorator or function)."""
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            db_sess = get_db()
            raw = _read_token()
            if raw is None:
                return _unauthorized()
            try:
                payload = validate_token(db_sess, raw)
                if payload.get("role") != "student":
                    return _forbidden()
                g.token_payload = payload
                g.user = current_user(request, db_sess)
            except TokenError:
                return _unauthorized()
            return f(*args, **kwargs)

        return wrapper

    if func is not None and callable(func):
        return decorator(func)

    db_sess = get_db()
    raw = _read_token()
    if raw is None:
        return None
    try:
        payload = validate_token(db_sess, raw)
        return payload if payload.get("role") == "student" else None
    except TokenError:
        return None


def require_admin(func: Callable | None = None) -> Any:
    """Require platform_admin role (decorator or function)."""
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            db_sess = get_db()
            raw = _read_token()
            if raw is None:
                return _unauthorized()
            try:
                payload = validate_token(db_sess, raw)
                if payload.get("role") not in ("platform_admin", "admin"):
                    return _forbidden()
                g.token_payload = payload
                g.user = current_user(request, db_sess)
            except TokenError:
                return _unauthorized()
            return f(*args, **kwargs)

        return wrapper

    if func is not None and callable(func):
        return decorator(func)

    db_sess = get_db()
    raw = _read_token()
    if raw is None:
        return None
    try:
        payload = validate_token(db_sess, raw)
        return payload if payload.get("role") in ("platform_admin", "admin") else None
    except TokenError:
        return None


require_platform_admin = require_admin


def require_institution_admin(func: Callable | None = None) -> Any:
    """Require institution_admin role (decorator or function)."""
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            db_sess = get_db()
            raw = _read_token()
            if raw is None:
                return _unauthorized()
            try:
                payload = validate_token(db_sess, raw)
                if payload.get("role") != "institution_admin":
                    return _forbidden()
                g.token_payload = payload
                g.user = current_user(request, db_sess)
            except TokenError:
                return _unauthorized()
            return f(*args, **kwargs)

        return wrapper

    if func is not None and callable(func):
        return decorator(func)

    db_sess = get_db()
    raw = _read_token()
    if raw is None:
        return None
    try:
        payload = validate_token(db_sess, raw)
        return payload if payload.get("role") == "institution_admin" else None
    except TokenError:
        return None


def require_active_subscription(func: Callable | None = None) -> Any:
    """Require active subscription."""
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            db_sess = get_db()
            raw = _read_token()
            if raw is None:
                return _unauthorized()
            try:
                payload = validate_token(db_sess, raw)
                if payload.get("role") != "student":
                    return _forbidden()
                status = payload.get("subscription_status")
                if status not in ("trial", "active", "grace_period"):
                    return jsonify({
                        "error": "subscription_required",
                        "message": "Active subscription required.",
                        "subscription_status": status,
                    }), 403
                g.token_payload = payload
                g.user = current_user(request, db_sess)
            except TokenError:
                return _unauthorized()
            return f(*args, **kwargs)

        return wrapper

    if func is not None and callable(func):
        return decorator(func)

    return None


def check_feature_access(
    payload: dict[str, Any],
    feature: str,
    session: Session | None = None,
) -> bool:
    """Evaluate access control matrix for a feature."""
    role = payload.get("role")
    
    if role == "platform_admin":
        return True
    
    if role == "institution_admin":
        return feature in ("question_management", "institution_management")
    
    if role == "student":
        subscription_status = payload.get("subscription_status")
        student_subtype = payload.get("student_subtype")
        
        if student_subtype == "dual":
            subscription_status = "active"
        
        if feature == "exam_access":
            return subscription_status in ("trial", "active", "grace_period")
        
        if feature == "basic_analytics":
            return subscription_status in ("trial", "active", "grace_period")
        
        if feature == "full_analytics":
            return subscription_status in ("active", "grace_period")
        
        if feature == "leaderboard":
            return subscription_status in ("active", "grace_period")
        
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
