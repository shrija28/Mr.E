"""HTTP endpoints for the Auth_Service using Flask Blueprint.

Mounted under /api/auth from smartkcet.main.
"""

from __future__ import annotations

import hmac
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from flask import Blueprint, jsonify, make_response, request
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm import Session

from ..db.models import User
from ..db.session import get_db
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

router = Blueprint("auth", __name__, url_prefix="/api/auth")

SESSION_COOKIE_NAME = "smartkcet_session"
MAX_FAILED_LOGINS = 5
LOCKOUT_WINDOW = timedelta(minutes=15)


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _set_cookie_on_response(res, token: str, max_age: int):
    res.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        max_age=max_age,
        httponly=True,
        samesite="Lax",
        path="/",
    )
    return res


def _validation_error(failure: ValidationFailure):
    return jsonify({
        "error": "validation_error",
        "field": failure.field,
        "message": failure.reason,
    }), 400


def _generic_auth_failure():
    return jsonify({"error": "auth_failed", "message": "Invalid credentials"}), 401


def _is_locked(user: User, now: datetime) -> bool:
    return user.lockout_until is not None and user.lockout_until > now


def _record_failed_attempt(user: User, now: datetime) -> None:
    user.failed_login_count = (user.failed_login_count or 0) + 1
    if user.failed_login_count >= MAX_FAILED_LOGINS:
        user.lockout_until = now + LOCKOUT_WINDOW


def _reset_lockout(user: User) -> None:
    user.failed_login_count = 0
    user.lockout_until = None


@router.route("/register", methods=["POST"])
def register():
    session: Session = get_db()
    data = request.get_json(silent=True) or {}
    email = data.get("email", "")
    password = data.get("password", "")
    display_name = data.get("display_name", "")
    invite_code = data.get("invite_code")

    email_v = validate_email(email)
    if isinstance(email_v, ValidationFailure):
        return _validation_error(email_v)

    password_v = validate_password(password)
    if isinstance(password_v, ValidationFailure):
        return _validation_error(password_v)

    name_v = validate_display_name(display_name)
    if isinstance(name_v, ValidationFailure):
        return _validation_error(name_v)

    normalised_email = email_v.lower()

    existing = session.execute(
        select(User.id).where(User.email == normalised_email)
    ).first()
    if existing is not None:
        return jsonify({
            "error": "email_already_registered",
            "message": "This email is already registered.",
        }), 409

    invitation = None
    institution_for_linking = None
    institution_student_id = None
    
    if invite_code and str(invite_code).strip():
        code = str(invite_code).strip()
        try:
            from ..db.subscription_models import Invitation, Institution
            import logging as _log
            _logger = _log.getLogger("smartkcet.auth.register")
            
            invitation = session.query(Invitation).filter(
                Invitation.code == code,
                Invitation.status == "pending",
            ).first()
            
            if invitation and (invitation.expires_at is None or invitation.expires_at >= datetime.utcnow()):
                institution_for_linking = session.query(Institution).filter(
                    Institution.id == invitation.institution_id
                ).first()
                if institution_for_linking and institution_for_linking.institution_code:
                    try:
                        institution_student_id = next_institution_student_id(
                            session, str(invitation.institution_id)
                        )
                    except Exception as e:
                        _logger.warning("Failed to pre-generate institution student ID: %s", e)
        except Exception as e:
            import logging
            logging.getLogger("smartkcet.auth").warning("Invite code error: %s", e)

    password_hash = hash_password(password_v)
    student_id = institution_student_id or next_kcet_id(session)

    user = User(
        email=normalised_email,
        kcet_student_id=student_id,
        display_name=name_v,
        password_hash=password_hash,
        role="student",
        student_subtype="direct_subscriber",
    )
    session.add(user)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        return jsonify({
            "error": "email_already_registered",
            "message": "This email is already registered.",
        }), 409

    institution_name = None
    institution_id_for_token = None
    if invitation and institution_for_linking:
        try:
            from ..institution.service import InstitutionService
            inst_service = InstitutionService(session)
            inst_service.accept_invitation(invite_code, user.id)
            session.refresh(user)
            if user.student_subtype != "institution_linked":
                user.student_subtype = "institution_linked"
                session.commit()
                session.refresh(user)
            institution_name = institution_for_linking.name
            institution_id_for_token = str(user.institution_id) if user.institution_id else None
        except Exception as e:
            import logging
            logging.getLogger("smartkcet.auth").warning("Auto-link failed: %s", e)

    message = f"Account created! Your Student ID: {student_id}"
    if institution_for_linking and institution_student_id:
        message = f"Account created! Your Student ID: {institution_student_id} ({institution_name})"

    response_data = {
        "kcet_student_id": student_id,
        "email": normalised_email,
        "display_name": name_v,
        "message": message,
    }

    if institution_name:
        response_data["institution_name"] = institution_name
        response_data["institution_linked"] = True
        response_data["auto_login"] = True

        token, _jti, _iat, _exp = issue_token(
            sub=user.kcet_student_id,
            role="student",
            student_subtype="institution_linked",
            institution_id=institution_id_for_token,
            subscription_status=None,
        )
        res = jsonify(response_data)
        _set_cookie_on_response(res, token, STUDENT_TOKEN_TTL_SEC)
        return res, 201

    return jsonify(response_data), 201


@router.route("/login", methods=["POST"])
def login():
    session: Session = get_db()
    data = request.get_json(silent=True) or {}
    email = data.get("email")
    password = data.get("password")

    if not isinstance(email, str) or not email or not isinstance(password, str) or not password:
        return _generic_auth_failure()

    normalised_email = email.strip().lower()
    now = _now()

    try:
        user = session.execute(
            select(User).where(User.email == normalised_email)
        ).scalar_one_or_none()
    except OperationalError:
        return jsonify({
            "error": "service_unavailable",
            "message": "Database temporarily unavailable. Please try again later.",
        }), 503

    if user is None or user.role != "student" or normalised_email in ["admin@smartkcet.com", "admin@gmail.com"]:
        return _generic_auth_failure()

    if _is_locked(user, now):
        retry_after_sec = max(int((user.lockout_until - now).total_seconds()), 1)
        res = jsonify({
            "error": "account_locked",
            "message": "Account temporarily locked. Try again later.",
            "retry_after_sec": retry_after_sec,
        })
        res.headers["Retry-After"] = str(retry_after_sec)
        return res, 423

    if user.lockout_until is not None and user.lockout_until <= now:
        _reset_lockout(user)

    if not verify_password(password, user.password_hash):
        _record_failed_attempt(user, now)
        try:
            session.commit()
        except OperationalError:
            return jsonify({
                "error": "service_unavailable",
                "message": "Database temporarily unavailable.",
            }), 503
        return _generic_auth_failure()

    _reset_lockout(user)
    try:
        session.commit()
    except OperationalError:
        return jsonify({
            "error": "service_unavailable",
            "message": "Database temporarily unavailable.",
        }), 503

    from ..db.subscription_models import Subscription
    from sqlalchemy import and_

    active_subscription = session.execute(
        select(Subscription).where(
            and_(
                Subscription.user_id == user.id,
                Subscription.status.in_(["trial", "active", "overdue", "grace_period"]),
            )
        )
    ).scalar_one_or_none()

    subscription_status = active_subscription.status if active_subscription else None

    from ..subscription.service import SubscriptionService
    subscription_service = SubscriptionService(session)
    needs_subscription_selection = subscription_service.needs_subscription_selection(user.id)

    token, _jti, _iat, _exp = issue_token(
        sub=user.kcet_student_id,
        role="student",
        student_subtype=user.student_subtype,
        institution_id=str(user.institution_id) if user.institution_id else None,
        subscription_status=subscription_status,
    )

    body = {
        "kcet_student_id": user.kcet_student_id,
        "display_name": user.display_name,
        "role": "student",
        "student_subtype": user.student_subtype,
        "redirect": "/student/institution/dashboard" if user.student_subtype == "institution_linked" else "/dashboard",
        "needs_subscription_selection": needs_subscription_selection,
    }

    res = jsonify(body)
    _set_cookie_on_response(res, token, STUDENT_TOKEN_TTL_SEC)
    return res, 200


@router.route("/admin/login", methods=["POST"])
def admin_login():
    session: Session = get_db()
    data = request.get_json(silent=True) or {}
    email = data.get("email")
    password = data.get("password")

    email_str = email.strip().lower() if isinstance(email, str) else ""
    password_str = password if isinstance(password, str) else ""

    if not email_str or not password_str:
        return _generic_auth_failure()

    creds = load_admin_credentials()
    authenticated = False
    admin_email = email_str

    if creds and hmac.compare_digest(email_str, creds.email):
        if verify_password(password_str, creds.password_hash):
            authenticated = True
            admin_email = creds.email

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
            return jsonify({
                "error": "service_unavailable",
                "message": "Database temporarily unavailable.",
            }), 503

    if not authenticated:
        return _generic_auth_failure()

    token, _jti, _iat, _exp = issue_token(sub=admin_email, role="platform_admin")
    res = jsonify({
        "role": "platform_admin",
        "email": admin_email,
        "redirect": "/admin/upload",
        "access_token": token,
    })
    _set_cookie_on_response(res, token, ADMIN_TOKEN_TTL_SEC)
    return res, 200


@router.route("/institution/login", methods=["POST"])
def institution_admin_login():
    session: Session = get_db()
    data = request.get_json(silent=True) or {}
    email = data.get("email")
    password = data.get("password")

    if not isinstance(email, str) or not email or not isinstance(password, str) or not password:
        return _generic_auth_failure()

    normalised_email = email.strip().lower()
    now = _now()

    try:
        user = session.execute(
            select(User).where(
                User.email == normalised_email, User.role == "institution_admin"
            )
        ).scalar_one_or_none()
    except OperationalError:
        return jsonify({
            "error": "service_unavailable",
            "message": "Database temporarily unavailable.",
        }), 503

    if user is None or normalised_email in ["admin@smartkcet.com", "admin@gmail.com"]:
        return _generic_auth_failure()

    if _is_locked(user, now):
        retry_after_sec = max(int((user.lockout_until - now).total_seconds()), 1)
        res = jsonify({
            "error": "account_locked",
            "message": "Account temporarily locked.",
            "retry_after_sec": retry_after_sec,
        })
        res.headers["Retry-After"] = str(retry_after_sec)
        return res, 423

    if user.lockout_until is not None and user.lockout_until <= now:
        _reset_lockout(user)

    if not verify_password(password, user.password_hash):
        _record_failed_attempt(user, now)
        try:
            session.commit()
        except OperationalError:
            return jsonify({"error": "service_unavailable", "message": "Database temporarily unavailable."}), 503
        return _generic_auth_failure()

    _reset_lockout(user)
    try:
        session.commit()
    except OperationalError:
        return jsonify({"error": "service_unavailable", "message": "Database temporarily unavailable."}), 503

    token, _jti, _iat, _exp = issue_token(
        sub=user.email,
        role="institution_admin",
        institution_id=str(user.institution_id) if user.institution_id else None,
    )
    res = jsonify({
        "email": user.email,
        "display_name": user.display_name,
        "role": "institution_admin",
        "institution_id": str(user.institution_id) if user.institution_id else None,
    })
    _set_cookie_on_response(res, token, ADMIN_TOKEN_TTL_SEC)
    return res, 200


@router.route("/logout", methods=["POST"])
def logout():
    session: Session = get_db()
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
                expires_at = datetime.fromtimestamp(exp_unix, tz=timezone.utc).replace(tzinfo=None)
            if revoke_token(session, jti, expires_at=expires_at):
                session.commit()
                revoked = True

    res = jsonify({"logged_out": True, "revoked": revoked})
    res.delete_cookie(SESSION_COOKIE_NAME, path="/")
    return res, 200


@router.route("/me", methods=["GET"])
def me():
    session: Session = get_db()
    raw = request.cookies.get(SESSION_COOKIE_NAME)
    if not raw:
        auth_hdr = request.headers.get("Authorization", "")
        if auth_hdr.startswith("Bearer "):
            raw = auth_hdr[7:].strip()
    if not raw:
        return jsonify({"error": "not_authenticated", "message": "No active session."}), 401
    try:
        payload = validate_token(session, raw)
    except TokenError:
        return jsonify({"error": "not_authenticated", "message": "No active session."}), 401

    role = payload.get("role")
    sub = payload.get("sub")

    result: dict[str, Any] = {"authenticated": True, "role": role, "sub": sub}

    if "student_subtype" in payload:
        result["student_subtype"] = payload["student_subtype"]
    if "institution_id" in payload:
        result["institution_id"] = payload["institution_id"]
    if "subscription_status" in payload:
        result["subscription_status"] = payload["subscription_status"]

    if role == "student":
        target_sub = sub.replace("KCET", "MrE").replace("ID", "MrE") if sub else sub
        user = session.execute(
            select(User).where(
                (User.kcet_student_id == sub) | (User.kcet_student_id == target_sub)
            )
        ).scalars().first()
        if user:
            result["email"] = user.email
            result["display_name"] = user.display_name
            sid = user.kcet_student_id or target_sub
            if sid and (sid.startswith("KCET") or sid.startswith("ID")):
                sid = sid.replace("KCET", "MrE").replace("ID", "MrE")
            result["kcet_student_id"] = sid
            result["student_subtype"] = user.student_subtype
            result["institution_id"] = str(user.institution_id) if user.institution_id else None
            if user.institution_id:
                from ..db.subscription_models import Institution
                inst = session.get(Institution, user.institution_id)
                if inst:
                    result["institution_name"] = inst.name

    if role == "institution_admin":
        user = session.execute(
            select(User).where(User.email == sub, User.role == "institution_admin")
        ).scalar_one_or_none()
        if user:
            result["display_name"] = user.display_name

    return jsonify(result), 200


__all__ = ["router", "SESSION_COOKIE_NAME"]
