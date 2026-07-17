"""Compute the most recent Census reporting month likely to be published.

Census international-trade statistics publish with roughly a two-month lag
(December data lands in early February), so "latest available" as of any date
is that date's month minus PUBLICATION_LAG_MONTHS. Pure function so it is
unit-testable without touching the network or the clock.
"""

from __future__ import annotations

from datetime import date

PUBLICATION_LAG_MONTHS = 2


def latest_published_period(as_of: date) -> str:
    """Return the newest 'YYYY-MM' period expected to be available on `as_of`."""
    months = as_of.year * 12 + (as_of.month - 1) - PUBLICATION_LAG_MONTHS
    return f"{months // 12:04d}-{months % 12 + 1:02d}"
