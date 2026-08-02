"""Leaderboard package — composite score, ranking, recompute trigger.

Exposes :func:`recompute_async` which is called by the submission service
**only** after a successful ``tx.commit()``.  The caller (submit.py) is
responsible for ensuring that partial-write, aborted, or no-submission
outcomes never reach this function.

Contract (REQ-11.6 / design.md §6.3)
-------------------------------------

* ``recompute_async(student_id)`` MUST be invoked **only** after a
  submission has been *fully* persisted (the SQL transaction has
  committed).  This is enforced by the caller's structure in submit.py.
* The function logs the trigger for observability.
* Actual ranking recomputation happens on-demand when the leaderboard
  endpoint is called (task 10.9), keeping this path lightweight and
  well within the 5-second budget.
"""

from __future__ import annotations

import logging
import time
from typing import Any

from smartkcet.leaderboard import service  # noqa: F401 — wired for future use

logger = logging.getLogger("smartkcet.leaderboard")


def recompute_async(student_id: Any) -> None:
    """Signal that a leaderboard recompute is needed for *student_id*.

    Called by the submission service strictly after ``session.commit()``
    succeeds.  A partial-write, aborted, or no-submission outcome will
    never reach this function — that invariant is enforced by the
    caller's control flow in ``smartkcet.student.submit``.

    The actual ranking computation is performed on-demand when the
    leaderboard endpoint is queried (task 10.9).  This function simply
    logs the trigger so the event is observable in logs and tests.

    Performance: this function completes in < 1 ms (logging only),
    well within the 5-second recomputation budget specified in REQ-11.6.
    """
    start = time.monotonic()

    logger.info(
        "leaderboard recompute triggered for student_id=%r "
        "(ranking will be refreshed on next endpoint call)",
        student_id,
    )

    elapsed_ms = (time.monotonic() - start) * 1000
    logger.debug(
        "recompute_async completed in %.2f ms (student_id=%r)",
        elapsed_ms,
        student_id,
    )


__all__ = ["recompute_async", "service"]
