"""Leaderboard composite-score algorithm and eligibility filter.

Implements design.md §6.1 (Composite Score Algorithm) and §6.2
(Inclusion / Exclusion Rules).

Requirements covered: REQ-10.2, REQ-11.1, REQ-11.2.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List


@dataclass
class StudentStats:
    """Per-student statistics used for composite score computation.

    Attributes:
        average_score: Mean exam score across all attempts (0..100).
        attempt_count: Total number of exam submissions.
        scores: List of individual exam scores (used to derive std dev).
        submission_count: Number of submissions (used for eligibility).
        overall_average_score: Overall average score (used for eligibility,
            may differ from ``average_score`` if subject-filtered).
    """

    average_score: float
    attempt_count: int
    scores: List[float] = field(default_factory=list)
    submission_count: int = 0
    overall_average_score: float = 0.0


@dataclass
class CohortStats:
    """Cohort-level statistics used for normalisation in the composite formula.

    Attributes:
        max_attempts_in_cohort: Maximum attempt count among all students
            in the cohort.  May be 0 when the cohort is empty.
        max_std_dev_in_cohort: Maximum standard deviation of scores among
            all students in the cohort.  May be 0 when the cohort is
            empty or all students have exactly one attempt.
    """

    max_attempts_in_cohort: int = 0
    max_std_dev_in_cohort: float = 0.0


def _std_dev(scores: List[float]) -> float:
    """Compute the population standard deviation of *scores*.

    Returns 0.0 when the list has fewer than 2 elements.
    """
    if len(scores) < 2:
        return 0.0
    mean = sum(scores) / len(scores)
    variance = sum((s - mean) ** 2 for s in scores) / len(scores)
    return math.sqrt(variance)


def compute_composite(student_stats: StudentStats, cohort_stats: CohortStats) -> float:
    """Compute the composite leaderboard score for a student.

    Formula (design.md §6.1):
        composite = (avg * 0.6) + (attempt_norm * 0.2) + (consistency * 0.2)

    Where:
        - avg = student's average exam score (0..100)
        - attempt_norm = (student_attempts / max_attempts_in_cohort) * 100
        - consistency = 100 - ((student_std_dev / max_std_dev_in_cohort) * 100)

    Fallbacks (REQ-11.1):
        - When student has exactly 1 attempt: consistency = 100
        - When max_attempts_in_cohort == 0: divisor = 1
        - When max_std_dev_in_cohort == 0: divisor = 1
    """
    avg = student_stats.average_score
    student_attempts = student_stats.attempt_count
    student_std_dev = _std_dev(student_stats.scores)

    # Consistency score
    if student_attempts == 1:
        consistency = 100.0
    else:
        max_std = cohort_stats.max_std_dev_in_cohort
        std_div = max_std if max_std > 0 else 1.0  # REQ-11.1 fallback
        consistency = 100.0 - ((student_std_dev / std_div) * 100.0)

    # Attempt normalisation
    max_att = cohort_stats.max_attempts_in_cohort
    att_div = max_att if max_att > 0 else 1  # REQ-11.1 fallback
    attempt_norm = (student_attempts / att_div) * 100.0

    return (avg * 0.6) + (attempt_norm * 0.2) + (consistency * 0.2)


def is_eligible(student_stats: StudentStats) -> bool:
    """Return True if the student meets leaderboard inclusion criteria.

    Eligibility (design.md §6.2, REQ-10.2, REQ-11.2):
        - submission_count >= 1
        - overall_average_score >= 30

    Students who fail either condition are excluded from the ranked list
    and receive rank = "—" on the dashboard.
    """
    return (
        student_stats.submission_count >= 1
        and student_stats.overall_average_score >= 30
    )


__all__ = [
    "StudentStats",
    "CohortStats",
    "compute_composite",
    "is_eligible",
]
