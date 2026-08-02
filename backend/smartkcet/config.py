"""Configuration and startup config guard.

This module owns two responsibilities:

1. The legacy ``Settings`` snapshot + ``require_groq_api_key`` helpers that
   the existing RAG client and SQLAlchemy session factory already consume.
2. The **startup config guard** described in design.md §3.5 (REQ-3.5):
   four env vars (``ADMIN_EMAIL``, ``ADMIN_PASSWORD_HASH``, ``JWT_SECRET``,
   ``DATABASE_URL``) are read once at process start, validated, and on any
   failure a fatal error is logged and the process exits with code 1
   *before* Uvicorn begins accepting connections.  Once the guard passes,
   no per-request "warming up" gate is imposed — requests are served
   immediately.

The guard exposes two test/dev escape hatches:

* ``SMARTKCET_SKIP_STARTUP_GUARD=1`` — return a stub ``StartupConfig``
  without validating env vars.  Pytest fixtures set this so importing
  :mod:`smartkcet.main` does not abort the test process.
* ``SMARTKCET_DEV_MODE=1`` — when set, a missing or short ``JWT_SECRET``
  falls back to the development secret defined in
  :mod:`smartkcet.auth.tokens` with a warning log; admin credentials are
  still required.

The function is idempotent: once a validated :class:`StartupConfig` has
been cached, subsequent calls return the same instance.  Pass
``force=True`` to re-read the environment (used in tests).
"""

from __future__ import annotations

import logging
import os
import sys
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv

# Load ``.env`` once at import time so any submodule that reads ``os.environ``
# afterwards sees the same values the legacy ``app.py`` saw.
load_dotenv(override=True)


logger = logging.getLogger("smartkcet.config")


# ---------------------------------------------------------------------------
# Legacy ``Settings`` snapshot (kept for backward compatibility)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Settings:
    """Runtime settings derived from environment variables."""

    groq_api_key: str | None
    host: str
    port: int

    @property
    def has_groq(self) -> bool:
        return bool(self.groq_api_key)


def load_settings() -> Settings:
    """Build a :class:`Settings` snapshot from the current process env."""

    return Settings(
        groq_api_key=os.getenv("GROQ_API_KEY"),
        host=os.getenv("SMARTKCET_HOST", "127.0.0.1"),
        port=int(os.getenv("SMARTKCET_PORT", "8000")),
    )


def require_groq_api_key() -> str:
    """Return the Groq API key or raise the same error the legacy app raised."""

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY environment variable is not set. "
            "Please set it before running the app."
        )
    return api_key


# ---------------------------------------------------------------------------
# Startup config guard (REQ-3.5)
# ---------------------------------------------------------------------------


# Validation thresholds.  These mirror the rules laid out in the task
# description and design.md.
_MAX_EMAIL_LENGTH = 254
_MIN_JWT_SECRET_LENGTH = 16
_BCRYPT_PREFIXES = ("$2a$", "$2b$", "$2y$")

_SKIP_GUARD_ENV = "SMARTKCET_SKIP_STARTUP_GUARD"
_DEV_MODE_ENV = "SMARTKCET_DEV_MODE"


@dataclass(frozen=True)
class StartupConfig:
    """Validated startup configuration.

    Attributes
    ----------
    admin_email
        Lower-cased admin email (REQ-3.5).
    admin_password_hash
        Bcrypt password hash for the admin account.
    jwt_secret
        Secret used to sign Session_Tokens.  In dev mode this may be the
        development fallback defined in :mod:`smartkcet.auth.tokens`.
    database_url
        Optional database URL.  ``None`` means "fall back to the SQLite
        default in ``smartkcet.db.session``".
    dev_mode
        ``True`` when ``SMARTKCET_DEV_MODE=1`` was set at startup.
    skipped
        ``True`` when ``SMARTKCET_SKIP_STARTUP_GUARD=1`` was set, in
        which case no validation was performed and the other fields hold
        empty/None placeholders.
    """

    admin_email: str
    admin_password_hash: str
    jwt_secret: str
    database_url: Optional[str]
    dev_mode: bool = False
    skipped: bool = False


# Cached, validated config.  Reset by tests via ``force=True``.
_cached_config: Optional[StartupConfig] = None


class StartupConfigError(ValueError):
    """Raised internally when validation fails.

    The public ``validate_startup_config`` helper catches this, logs a
    fatal error, and calls ``sys.exit(1)``.  Tests that want to assert on
    the underlying error message can call :func:`_collect_validation_errors`
    directly.
    """


def _truthy(value: Optional[str]) -> bool:
    if value is None:
        return False
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _validate_admin_email(value: Optional[str]) -> str:
    """Return the normalised admin email or raise."""

    email = (value or "").strip()
    if not email:
        raise StartupConfigError("ADMIN_EMAIL is not set")
    if "@" not in email:
        raise StartupConfigError("ADMIN_EMAIL must contain '@'")
    if len(email) > _MAX_EMAIL_LENGTH:
        raise StartupConfigError(
            f"ADMIN_EMAIL exceeds maximum length of {_MAX_EMAIL_LENGTH} characters"
        )
    return email.lower()


def _validate_admin_password_hash(value: Optional[str]) -> str:
    """Return the admin password hash or raise."""

    pw_hash = (value or "").strip()
    if not pw_hash:
        raise StartupConfigError("ADMIN_PASSWORD_HASH is not set")
    if not pw_hash.startswith(_BCRYPT_PREFIXES):
        raise StartupConfigError(
            "ADMIN_PASSWORD_HASH does not look like a bcrypt hash "
            f"(expected one of {_BCRYPT_PREFIXES})"
        )
    return pw_hash


def _validate_jwt_secret(value: Optional[str], *, dev_mode: bool) -> str:
    """Return the JWT secret or raise.

    In dev mode a missing or short secret is replaced with the development
    fallback from :mod:`smartkcet.auth.tokens`, with a warning log.
    """

    secret = value or ""
    if len(secret) >= _MIN_JWT_SECRET_LENGTH:
        return secret

    if dev_mode:
        # Lazy import to avoid a circular import at module load time.
        from .auth.tokens import _DEV_JWT_SECRET  # type: ignore[attr-defined]

        if not secret:
            logger.warning(
                "JWT_SECRET is not set; falling back to the development secret "
                "because %s=1 is enabled. DO NOT use this in production.",
                _DEV_MODE_ENV,
            )
        else:
            logger.warning(
                "JWT_SECRET is shorter than %d characters; falling back to the "
                "development secret because %s=1 is enabled. DO NOT use this "
                "in production.",
                _MIN_JWT_SECRET_LENGTH,
                _DEV_MODE_ENV,
            )
        return _DEV_JWT_SECRET

    if not secret:
        raise StartupConfigError("JWT_SECRET is not set")
    raise StartupConfigError(
        f"JWT_SECRET must be at least {_MIN_JWT_SECRET_LENGTH} characters long"
    )


def _validate_database_url(value: Optional[str]) -> Optional[str]:
    """Return the database URL or raise.

    DATABASE_URL is optional — when unset the SQLite default in
    :mod:`smartkcet.db.session` is used.  When the env var *is* present it
    must not be the empty string.
    """

    if value is None:
        return None
    stripped = value.strip()
    # Distinguish "set to empty" (invalid) from "not set" (fine).
    if value != "" and not stripped:
        raise StartupConfigError("DATABASE_URL is set but contains only whitespace")
    if value == "":
        raise StartupConfigError("DATABASE_URL is set but empty")
    return stripped


def _collect_validation_errors(env: Optional[dict[str, str]] = None) -> StartupConfig:
    """Validate the four env vars and return a :class:`StartupConfig`.

    Raises :class:`StartupConfigError` on the first failing field.  Used
    directly by tests so they can assert on error messages without
    invoking ``sys.exit``.
    """

    src = env if env is not None else os.environ

    dev_mode = _truthy(src.get(_DEV_MODE_ENV))

    admin_email = _validate_admin_email(src.get("ADMIN_EMAIL"))
    admin_password_hash = _validate_admin_password_hash(src.get("ADMIN_PASSWORD_HASH"))
    jwt_secret = _validate_jwt_secret(src.get("JWT_SECRET"), dev_mode=dev_mode)
    # ``DATABASE_URL`` is "not set" iff the key is absent.  Tests pass in a
    # filtered dict where missing keys reflect "unset"; the live call path
    # uses ``os.environ`` where the same semantics hold.
    database_url = _validate_database_url(src.get("DATABASE_URL"))

    return StartupConfig(
        admin_email=admin_email,
        admin_password_hash=admin_password_hash,
        jwt_secret=jwt_secret,
        database_url=database_url,
        dev_mode=dev_mode,
        skipped=False,
    )


def validate_startup_config(*, force: bool = False) -> StartupConfig:
    """Validate startup configuration and return a :class:`StartupConfig`.

    On any validation failure this logs a fatal error and calls
    ``sys.exit(1)`` — the calling process terminates before Uvicorn
    binds a port.  On success a :class:`StartupConfig` is returned and
    cached so repeated calls are cheap and idempotent.

    Test/dev escapes:

    * ``SMARTKCET_SKIP_STARTUP_GUARD=1`` — returns a stub ``StartupConfig``
      with ``skipped=True`` and empty/None field values.  Validation is
      not performed.
    * ``SMARTKCET_DEV_MODE=1`` — see :func:`_validate_jwt_secret`.

    Parameters
    ----------
    force
        When ``True`` the cached result is discarded and validation is
        re-run.  Tests use this to re-check after mutating ``os.environ``.
    """

    global _cached_config

    if force:
        _cached_config = None

    if _cached_config is not None:
        return _cached_config

    if _truthy(os.environ.get(_SKIP_GUARD_ENV)):
        logger.info(
            "%s=1; skipping startup config guard. This is intended for tests "
            "and development only.",
            _SKIP_GUARD_ENV,
        )
        _cached_config = StartupConfig(
            admin_email="",
            admin_password_hash="",
            jwt_secret="",
            database_url=None,
            dev_mode=_truthy(os.environ.get(_DEV_MODE_ENV)),
            skipped=True,
        )
        return _cached_config

    try:
        cfg = _collect_validation_errors()
    except StartupConfigError as exc:
        # Log a fatal-level message and exit non-zero before any HTTP
        # listener is bound.  Using ``logger.critical`` plus a plain
        # stderr write covers both structured-logging and unconfigured
        # environments (e.g., a freshly started container with no logging
        # config yet).
        logger.critical("FATAL: startup config invalid: %s", exc)
        print(f"FATAL: startup config invalid: {exc}", file=sys.stderr, flush=True)
        sys.exit(1)

    _cached_config = cfg
    return cfg


def reset_startup_config_cache() -> None:
    """Drop the cached :class:`StartupConfig` (test helper)."""

    global _cached_config
    _cached_config = None


__all__ = [
    "Settings",
    "StartupConfig",
    "StartupConfigError",
    "load_settings",
    "require_groq_api_key",
    "reset_startup_config_cache",
    "validate_startup_config",
]
