"""Tests for DailySchedule, MissionSchedule classes, and pre-built templates."""

import pytest
from eclss.schedule import (
    DailySchedule,
    ActivityBlock,
    ConstantSchedule,
    WeeklySchedule,
    CustomSchedule,
    REFERENCE_SCHEDULE,
    ISS_WEEKDAY,
    ISS_WEEKEND,
    ISS_WEEKLY,
)
from eclss.activity import NOMINAL, SLEEP, AEROBIC_EXERCISE


class TestScheduleValidation:
    def test_overlap_raises(self):
        """Two blocks that overlap should be rejected."""
        blocks = [
            ActivityBlock(NOMINAL, 0.0, 13.0),  # ends at 13
            ActivityBlock(SLEEP, 12.0, 12.0),    # starts at 12 - overlap
        ]
        with pytest.raises(ValueError):
            DailySchedule(blocks)

    def test_under_24h_raises(self):
        blocks = [ActivityBlock(NOMINAL, 0.0, 10.0)]
        with pytest.raises(ValueError, match="24"):
            DailySchedule(blocks)

    def test_over_24_raises(self):
        blocks = [ActivityBlock(NOMINAL, 0.0, 25.0)]
        with pytest.raises(ValueError, match="24"):
            DailySchedule(blocks)

    def test_gap_with_correct_total_raises(self):
        """Gap between blocks should be caught even if total is 24h."""
        blocks = [
            ActivityBlock(NOMINAL, 0.0, 10.0),   # ends at 10
            ActivityBlock(SLEEP, 11.0, 14.0),     # starts at 11 - 1h gap, total=24
        ]
        with pytest.raises(ValueError, match="Gap or overlap"):
            DailySchedule(blocks)

    def test_must_start_at_zero(self):
        blocks = [ActivityBlock(NOMINAL, 2.0, 24.0)]
        with pytest.raises(ValueError, match="start at 0h"):
            DailySchedule(blocks)

    def test_empty_blocks_raises(self):
        with pytest.raises(ValueError):
            DailySchedule([])


class TestReferenceSchedule:
    def test_sums_to_24(self):
        total = sum(b.duration_hours for b in REFERENCE_SCHEDULE.blocks)
        assert total == pytest.approx(24.0)

    def test_activity_at_sleep(self):
        assert REFERENCE_SCHEDULE.activity_at(1.0) is SLEEP

    def test_activity_at_nominal(self):
        assert REFERENCE_SCHEDULE.activity_at(9.0) is NOMINAL

    def test_activity_at_exercise(self):
        assert REFERENCE_SCHEDULE.activity_at(13.1) is AEROBIC_EXERCISE

    def test_activity_at_wraps_24(self):
        """Hour 25 should wrap to hour 1 (sleep)."""
        assert REFERENCE_SCHEDULE.activity_at(25.0) is SLEEP


class TestISSSchedules:
    def test_weekday_sums_to_24(self):
        total = sum(b.duration_hours for b in ISS_WEEKDAY.blocks)
        assert total == pytest.approx(24.0)

    def test_weekend_sums_to_24(self):
        total = sum(b.duration_hours for b in ISS_WEEKEND.blocks)
        assert total == pytest.approx(24.0)

    def test_weekend_more_sleep_than_weekday(self):
        """Weekend has more total sleep hours than weekday."""
        weekday_sleep = sum(
            b.duration_hours for b in ISS_WEEKDAY.blocks if b.activity is SLEEP
        )
        weekend_sleep = sum(
            b.duration_hours for b in ISS_WEEKEND.blocks if b.activity is SLEEP
        )
        assert weekend_sleep > weekday_sleep

    def test_same_exercise_duration(self):
        """Both weekday and weekend have the same exercise block durations."""
        weekday_ex = sum(
            b.duration_hours for b in ISS_WEEKDAY.blocks
            if b.activity is not NOMINAL and b.activity is not SLEEP
        )
        weekend_ex = sum(
            b.duration_hours for b in ISS_WEEKEND.blocks
            if b.activity is not NOMINAL and b.activity is not SLEEP
        )
        assert weekday_ex == pytest.approx(weekend_ex)


class TestConstantSchedule:
    def test_same_every_day(self):
        cs = ConstantSchedule(REFERENCE_SCHEDULE)
        assert cs.schedule_for_day(0) is REFERENCE_SCHEDULE
        assert cs.schedule_for_day(99) is REFERENCE_SCHEDULE
        assert cs.schedule_for_day(365) is REFERENCE_SCHEDULE


class TestWeeklySchedule:
    def test_weekday_days_0_through_4(self):
        ws = WeeklySchedule(ISS_WEEKDAY, ISS_WEEKEND)
        for day in range(5):
            assert ws.schedule_for_day(day) is ISS_WEEKDAY

    def test_weekend_days_5_and_6(self):
        ws = WeeklySchedule(ISS_WEEKDAY, ISS_WEEKEND)
        assert ws.schedule_for_day(5) is ISS_WEEKEND
        assert ws.schedule_for_day(6) is ISS_WEEKEND

    def test_wraps_to_next_week(self):
        ws = WeeklySchedule(ISS_WEEKDAY, ISS_WEEKEND)
        assert ws.schedule_for_day(7) is ISS_WEEKDAY   # next Monday
        assert ws.schedule_for_day(12) is ISS_WEEKEND   # next Saturday

    def test_iss_weekly_prebuild(self):
        """ISS_WEEKLY should be a WeeklySchedule with ISS_WEEKDAY/WEEKEND."""
        assert isinstance(ISS_WEEKLY, WeeklySchedule)
        assert ISS_WEEKLY.schedule_for_day(0) is ISS_WEEKDAY
        assert ISS_WEEKLY.schedule_for_day(5) is ISS_WEEKEND


class TestCustomSchedule:
    def test_mapped_days_use_mapping(self):
        custom = CustomSchedule(
            mapping={0: ISS_WEEKEND, 10: ISS_WEEKEND},
            default=ISS_WEEKDAY,
        )
        assert custom.schedule_for_day(0) is ISS_WEEKEND
        assert custom.schedule_for_day(10) is ISS_WEEKEND

    def test_unmapped_days_use_default(self):
        custom = CustomSchedule(
            mapping={0: ISS_WEEKEND},
            default=ISS_WEEKDAY,
        )
        assert custom.schedule_for_day(1) is ISS_WEEKDAY
        assert custom.schedule_for_day(99) is ISS_WEEKDAY

    def test_rest_week_pattern(self):
        """Model a rest week (days 7-13) with lighter schedule."""
        rest_day = REFERENCE_SCHEDULE  # lighter than ISS weekday
        mapping = {d: rest_day for d in range(7, 14)}
        custom = CustomSchedule(mapping=mapping, default=ISS_WEEKDAY)
        assert custom.schedule_for_day(6) is ISS_WEEKDAY
        assert custom.schedule_for_day(7) is rest_day
        assert custom.schedule_for_day(13) is rest_day
        assert custom.schedule_for_day(14) is ISS_WEEKDAY
