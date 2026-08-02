"""Pre-DB input validation for auth endpoints.

REQ-1.3 / REQ-1.4 require validation to fire **before** any DB call.
REQ-1.2 / Property 2 require the duplicate-email DB check to fire
**before** password hashing.  Both ordering constraints are kept honest
by using the small helpers in this module — call them at the top of the
handler so validation errors short-circuit before either DB or hashing.

Returned :class:`ValidationFailure` instances carry the field name and a
short reason; the caller maps these to HTTP 400.
"""

from __future__ import annotations

from dataclasses import dataclass

import email_validator

EMAIL_MAX_LEN = 254
PASSWORD_MIN_LEN = 8
DISPLAY_NAME_MIN_LEN = 1
DISPLAY_NAME_MAX_LEN = 50


@dataclass(frozen=True)
class ValidationFailure:
    field: str
    reason: str


def validate_email(value: str) -> str | ValidationFailure:
    """Return the normalised email or a :class:`ValidationFailure`.

    Uses :mod:`email_validator` for RFC 5322 syntax + domain shape,
    enforces the ≤254 char overall cap (REQ-1.3), and lowercases the
    domain so duplicate-detection can be performed case-insensitively.
    Deliverability checks (DNS) are disabled — pure syntactic check.
    """

    if not isinstance(value, str) or not value:
        return ValidationFailure("email", "email is required")
    if len(value) > EMAIL_MAX_LEN:
        return ValidationFailure(
            "email", f"email must be {EMAIL_MAX_LEN} characters or fewer"
        )
    try:
        info = email_validator.validate_email(
            value, check_deliverability=False
        )
    except email_validator.EmailNotValidError as exc:
        return ValidationFailure("email", str(exc))
    return info.normalized


def validate_password(value: str) -> str | ValidationFailure:
    """Enforce REQ-1.4: ≥8 chars and ≥1 digit."""

    if not isinstance(value, str):
        return ValidationFailure("password", "password is required")
    if len(value) < PASSWORD_MIN_LEN:
        return ValidationFailure(
            "password", f"password must be at least {PASSWORD_MIN_LEN} characters"
        )
    if not any(ch.isdigit() for ch in value):
        return ValidationFailure(
            "password", "password must contain at least one digit"
        )
    return value


def validate_display_name(value: str) -> str | ValidationFailure:
    """Enforce REQ-1.1: 1–50 character display name (after trimming)."""

    if not isinstance(value, str):
        return ValidationFailure("display_name", "display name is required")
    trimmed = value.strip()
    if len(trimmed) < DISPLAY_NAME_MIN_LEN:
        return ValidationFailure("display_name", "display name is required")
    if len(trimmed) > DISPLAY_NAME_MAX_LEN:
        return ValidationFailure(
            "display_name",
            f"display name must be {DISPLAY_NAME_MAX_LEN} characters or fewer",
        )
    return trimmed


__all__ = [
    "DISPLAY_NAME_MAX_LEN",
    "DISPLAY_NAME_MIN_LEN",
    "EMAIL_MAX_LEN",
    "PASSWORD_MIN_LEN",
    "ValidationFailure",
    "validate_display_name",
    "validate_email",
    "validate_password",
]
