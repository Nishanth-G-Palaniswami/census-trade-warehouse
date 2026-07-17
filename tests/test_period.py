"""Unit tests for the publication-lag period computation."""

from datetime import date

from census_trade.period import latest_published_period


def test_mid_year():
    assert latest_published_period(date(2026, 7, 10)) == "2026-05"


def test_year_boundary_january():
    assert latest_published_period(date(2026, 1, 10)) == "2025-11"


def test_year_boundary_february():
    assert latest_published_period(date(2026, 2, 10)) == "2025-12"


def test_march_lands_on_january():
    assert latest_published_period(date(2026, 3, 1)) == "2026-01"
