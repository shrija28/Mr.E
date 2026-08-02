"""Leaderboard ranking with tie-breaking and rank-skipping.

Implements design.md §6.4 (Tie-Breaking and Rank Skipping).

Requirements covered: REQ-11.3, REQ-11.4.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List, Tuple, Union


@dataclass
class RankedEntry:
    """A single entry in the ranked leaderboard (rich variant).

    Used by the leaderboard service for full-featured ranking with
    additional metadata.

    Attributes:
        student_id: The student's user ID (UUID or similar).
        composite_score: The computed composite score.
        rank: The assigned integer rank (1-based, with ties sharing rank).
        display_name: The student's display name.
        kcet_student_id: The student's KCET ID string.
        average_score: The student's average score.
        attempt_count: The student's attempt count.
    """

    student_id: Any
    composite_score: float
    rank: int = 0
    display_name: str = ""
    kcet_student_id: str = ""
    average_score: float = 0.0
    attempt_count: int = 0


def assign_ranks(
    entries: Union[List[Tuple[str, float]], List[RankedEntry]],
) -> Union[List[Tuple[str, int, float]], List[RankedEntry]]:
    """Sort entries by composite_score descending and assign ranks.

    Uses shared-rank-and-skip semantics (standard competition ranking):
    if two students tie at rank 1, the next student gets rank 3.

    Accepts either:
    - A list of (student_id, composite_score) tuples — returns
      (student_id, rank, composite_score) tuples.
    - A list of RankedEntry dataclass instances — mutates and returns them.
    """
    if not entries:
        return entries

    # Detect input type
    if isinstance(entries[0], tuple):
        return _assign_ranks_tuples(entries)  # type: ignore[arg-type]
    else:
        return _assign_ranks_entries(entries)  # type: ignore[arg-type]


def _assign_ranks_tuples(
    entries: List[Tuple[str, float]],
) -> List[Tuple[str, int, float]]:
    """Rank a list of (student_id, composite_score) tuples.

    Returns a list of (student_id, rank, composite_score) sorted
    descending by score.
    """
    # Sort descending by composite_score
    sorted_entries = sorted(entries, key=lambda e: e[1], reverse=True)

    result: List[Tuple[str, int, float]] = []
    current_rank = 1

    for i, (student_id, score) in enumerate(sorted_entries):
        if i == 0:
            current_rank = 1
        elif score < sorted_entries[i - 1][1]:
            current_rank = i + 1
        result.append((student_id, current_rank, score))

    return result


def _assign_ranks_entries(entries: List[RankedEntry]) -> List[RankedEntry]:
    """Rank a list of RankedEntry objects in-place.

    Sorts descending by composite_score and assigns rank fields.
    """
    entries.sort(key=lambda e: e.composite_score, reverse=True)

    current_rank = 1
    entries[0].rank = current_rank

    for i in range(1, len(entries)):
        if entries[i].composite_score < entries[i - 1].composite_score:
            current_rank = i + 1
        entries[i].rank = current_rank

    return entries


__all__ = [
    "RankedEntry",
    "assign_ranks",
]
