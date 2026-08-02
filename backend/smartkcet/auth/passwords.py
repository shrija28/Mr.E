"""Password hashing helpers wrapping :mod:`bcrypt`.

The module exposes a tiny :class:`collections.Counter`-based test hook,
``HASHING_INVOKED``, so property tests can assert whether the hashing
routine fired during a given flow (notably the duplicate-email
short-circuit, REQ-1.2 / Property 2).  Production code calls
:func:`hash_password` and :func:`verify_password` exactly the way it would
without the hook — the counter just observes.

The actual hashing uses bcrypt (work factor pinned to the ``bcrypt`` default,
which is currently 12).  Argon2 can be swapped in later by replacing this
file; the public API is intentionally minimal.
"""

from __future__ import annotations

from collections import Counter

import bcrypt

# Test hook (REQ-1.2 / Property 2).
#
# ``HASHING_INVOKED["hash"]``    increments per :func:`hash_password` call.
# ``HASHING_INVOKED["verify"]``  increments per :func:`verify_password` call.
#
# Tests should call :func:`reset_hashing_counter` between scenarios.
HASHING_INVOKED: Counter = Counter()


def reset_hashing_counter() -> None:
    """Clear the :data:`HASHING_INVOKED` counter (useful in tests)."""

    HASHING_INVOKED.clear()


def hash_password(plaintext: str) -> str:
    """Return a bcrypt hash for ``plaintext``.

    The salt is generated fresh per call.  The return type is ``str`` so
    callers can persist the value into an ORM ``String`` column directly.
    """

    HASHING_INVOKED["hash"] += 1
    if not isinstance(plaintext, str):
        raise TypeError("plaintext password must be a str")
    salt = bcrypt.gensalt()
    digest = bcrypt.hashpw(plaintext.encode("utf-8"), salt)
    return digest.decode("utf-8")


def verify_password(plaintext: str, hashed: str) -> bool:
    """Return ``True`` iff ``plaintext`` matches ``hashed``.

    A malformed ``hashed`` string (wrong prefix, wrong length, etc.) is
    treated as "no match" rather than propagating the underlying
    :class:`ValueError`, so callers don't need to wrap the call.
    """

    HASHING_INVOKED["verify"] += 1
    if not isinstance(plaintext, str) or not isinstance(hashed, str):
        return False
    try:
        return bcrypt.checkpw(plaintext.encode("utf-8"), hashed.encode("utf-8"))
    except (ValueError, TypeError):
        return False


__all__ = [
    "HASHING_INVOKED",
    "hash_password",
    "reset_hashing_counter",
    "verify_password",
]
