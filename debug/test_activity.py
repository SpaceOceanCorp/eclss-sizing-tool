"""Tests for activity-level metabolic rates (BVAD Table 3-24)."""

import pytest
from eclss.activity import (
    AEROBIC_EXERCISE,
    RESISTIVE_EXERCISE,
    RECOVERY,
    NOMINAL,
    SLEEP,
    ALL_ACTIVITIES,
    REFERENCE_DAY,
)
from eclss.constants import METABOLIC_RATE_KJ_PER_CM_DAY


def test_reference_day_sums_to_24h():
    total = sum(REFERENCE_DAY.values())
    assert total == pytest.approx(24.0)


def test_reference_day_weighted_metabolic_rate():
    """Weighted average from Table 3-24 should approximate Table 3-23 daily total.

    ~6% discrepancy is expected: Table 3-24 per-activity rates and Table 3-23
    daily totals come from different BVAD measurement approaches.
    """
    weighted = sum(act.metabolic_rate_kj_hr * hrs for act, hrs in REFERENCE_DAY.items())
    assert weighted == pytest.approx(METABOLIC_RATE_KJ_PER_CM_DAY, rel=0.10)


def test_all_activities_length():
    assert len(ALL_ACTIVITIES) == 5


def test_activity_level_frozen():
    """ActivityLevel should be immutable (frozen dataclass)."""
    with pytest.raises(AttributeError):
        NOMINAL.metabolic_rate_kj_hr = 999


def test_aerobic_highest_metabolic_rate():
    """Aerobic exercise should have the highest metabolic rate."""
    assert AEROBIC_EXERCISE.metabolic_rate_kj_hr > max(
        a.metabolic_rate_kj_hr for a in ALL_ACTIVITIES if a is not AEROBIC_EXERCISE
    )


def test_sleep_lowest_metabolic_rate():
    """Sleep should have the lowest metabolic rate."""
    assert SLEEP.metabolic_rate_kj_hr < min(
        a.metabolic_rate_kj_hr for a in ALL_ACTIVITIES if a is not SLEEP
    )
