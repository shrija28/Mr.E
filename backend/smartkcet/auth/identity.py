"""KCET_Student_ID generator.

REQ-1.1 mandates the format ``KCET\\d{4}`` — the literal prefix ``KCET``
followed by a zero-padded 4-digit sequence number.  This module owns the
allocation logic.

The generator scans the existing ``users.kcet_student_id`` column for the
highest assigned numeric suffix and returns the next one.  It is
race-free in the single-writer (SQLite, dev) deployment; a
``UNIQUE`` constraint on ``users.kcet_student_id`` provides defence in
depth in case of concurrent inserts.

Calling :func:`next_kcet_id` does *not* allocate a row in the DB — it
simply returns the next ID string.  Persisting the new user (and thus
"consuming" the ID) is the caller's responsibility, normally inside the
same transaction as the duplicate-email check + ``hash_password`` flow.

For institution-linked students, the format is ``{institution_code}####``
where institution_code is a unique short code for the institution (e.g., 
'institution', 'smvitm') and #### is a zero-padded 4-digit counter per institution.
"""

from __future__ import annotations

import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db.models import User
from ..db.subscription_models import Institution

# Public regex — also useful for tests.
KCET_ID_RE = re.compile(r"^KCET\d{4}$")
INSTITUTION_ID_RE = re.compile(r"^[a-z]+\d{4}$")

_PREFIX = "KCET"
_DIGITS = 4


def format_kcet_id(n: int) -> str:
    """Format ``n`` as a zero-padded KCET_Student_ID."""

    if n < 0:
        raise ValueError("kcet sequence number must be non-negative")
    return f"{_PREFIX}{n:0{_DIGITS}d}"


def parse_kcet_id(kcet_id: str) -> int | None:
    """Return the integer suffix of ``kcet_id`` or ``None`` if malformed."""

    if not isinstance(kcet_id, str):
        return None
    if not KCET_ID_RE.match(kcet_id):
        return None
    return int(kcet_id[len(_PREFIX):])


def format_institution_id(institution_code: str, n: int) -> str:
    """Format institution-specific student ID as {code}####.
    
    Args:
        institution_code: Short code for institution (e.g., 'institution', 'smvitm')
        n: Sequence number (zero-padded to 4 digits)
        
    Returns:
        Formatted ID like 'institution0001' or 'smvitm0001'
    """
    if n < 0:
        raise ValueError("sequence number must be non-negative")
    if not institution_code or not isinstance(institution_code, str):
        raise ValueError("institution_code must be a non-empty string")
    return f"{institution_code.lower()}{n:04d}"


def parse_institution_id(institution_id: str) -> tuple[str, int] | None:
    """Parse institution student ID to extract code and number.
    
    Args:
        institution_id: ID like 'institution0001'
        
    Returns:
        Tuple of (institution_code, number) or None if invalid
    """
    if not isinstance(institution_id, str):
        return None
    if not INSTITUTION_ID_RE.match(institution_id):
        return None
    
    # Extract alphabetic prefix and numeric suffix
    match = re.match(r"^([a-z]+)(\d{4})$", institution_id)
    if not match:
        return None
    
    code = match.group(1)
    number = int(match.group(2))
    return (code, number)


def next_kcet_id(session: Session) -> str:
    """Return the next available KCET_Student_ID.

    The function inspects every non-null ``kcet_student_id`` value in the
    ``users`` table, ignores anything that doesn't match ``^KCET\\d{4}$``,
    and returns ``KCET<max+1>`` zero-padded.  When the table is empty the
    first issued ID is ``KCET0001``.
    """

    rows = session.execute(
        select(User.kcet_student_id).where(User.kcet_student_id.is_not(None))
    ).all()

    max_seq = 0
    for (raw,) in rows:
        n = parse_kcet_id(raw)
        if n is not None and n > max_seq:
            max_seq = n
    return format_kcet_id(max_seq + 1)


def next_institution_student_id(session: Session, institution_id: str) -> str:
    """Return the next available institution-specific student ID.
    
    Generates IDs like 'institution0001', 'smvitm0002' per institution.
    Each institution maintains its own counter.
    
    Args:
        session: Database session
        institution_id: UUID of the institution
        
    Returns:
        Next available ID in format '{institution_code}####'
        
    Raises:
        ValueError: If institution not found or doesn't have institution_code
    """
    from uuid import UUID
    
    # Get institution and its code
    if isinstance(institution_id, str):
        try:
            institution_id = UUID(institution_id)
        except ValueError:
            raise ValueError(f"Invalid institution UUID: {institution_id}")
    
    institution = session.query(Institution).filter(
        Institution.id == institution_id
    ).first()
    
    if not institution:
        raise ValueError(f"Institution not found: {institution_id}")
    
    if not institution.institution_code:
        raise ValueError(f"Institution {institution_id} does not have institution_code set")
    
    code = institution.institution_code
    
    # Find max number for this institution's code
    rows = session.execute(
        select(User.kcet_student_id).where(User.kcet_student_id.is_not(None))
    ).all()
    
    max_seq = 0
    for (raw,) in rows:
        parsed = parse_institution_id(raw)
        if parsed and parsed[0].lower() == code.lower():
            if parsed[1] > max_seq:
                max_seq = parsed[1]
    
    return format_institution_id(code, max_seq + 1)


__all__ = [
    "KCET_ID_RE",
    "INSTITUTION_ID_RE",
    "format_kcet_id",
    "format_institution_id",
    "next_kcet_id",
    "next_institution_student_id",
    "parse_kcet_id",
    "parse_institution_id",
]
