"""Activity schedules for crew members.

Defines daily schedules as sequences of ActivityBlocks that must cover
exactly 24 hours with no overlaps or gaps.

Schedule hierarchy:
  - DailySchedule: a single 24-hour activity profile
  - ConstantSchedule: same DailySchedule every day of the mission
  - WeeklySchedule: 5 weekday + 2 weekend day rotation (ISS pattern)
  - CustomSchedule: arbitrary day-to-schedule mapping with fallback default

Includes pre-built schedules:
  - REFERENCE_SCHEDULE: Table 3-24 exploration day
  - ISS_WEEKDAY: Table 3-28 weekday crew timeline
  - ISS_WEEKEND: Table 3-28 weekend crew timeline
  - ISS_WEEKLY: WeeklySchedule combining ISS_WEEKDAY and ISS_WEEKEND
"""

from dataclasses import dataclass
from eclss.activity import (
    ActivityLevel,
    SLEEP,
    NOMINAL,
    AEROBIC_EXERCISE,
    RESISTIVE_EXERCISE,
    RECOVERY,
)


@dataclass(frozen=True)
class ActivityBlock:
    """A time block within a daily schedule.

    Attributes:
        activity: The activity level for this block.
        start_hour: Start time (0.0 to 23.99, wraps at 24).
        duration_hours: Duration of this block.
    """

    activity: ActivityLevel
    start_hour: float
    duration_hours: float


class DailySchedule:
    """A 24-hour activity profile for one crew member.

    Blocks must cover exactly 24 hours with no overlaps.
    """

    def __init__(self, blocks: list[ActivityBlock]):
        self.blocks = sorted(blocks, key=lambda b: b.start_hour)
        self._validate()

    def _validate(self) -> None:
        if not self.blocks:
            raise ValueError("Schedule must have at least one block")
        total = sum(b.duration_hours for b in self.blocks)
        if abs(total - 24.0) > 0.01:
            raise ValueError(f"Schedule must total 24h, got {total:.2f}h")
        if abs(self.blocks[0].start_hour) > 0.001:
            raise ValueError(
                f"Schedule must start at 0h, got {self.blocks[0].start_hour:.2f}h"
            )
        for i in range(len(self.blocks) - 1):
            end = self.blocks[i].start_hour + self.blocks[i].duration_hours
            next_start = self.blocks[i + 1].start_hour
            if abs(end - next_start) > 0.001:
                raise ValueError(
                    f"Gap or overlap between '{self.blocks[i].activity.name}' "
                    f"(ends {end:.2f}h) and '{self.blocks[i + 1].activity.name}' "
                    f"(starts {next_start:.2f}h)"
                )

    def activity_at(self, hour: float) -> ActivityLevel:
        """Return the activity level at a given hour of the day."""
        h = hour % 24.0
        for b in self.blocks:
            if b.start_hour <= h < b.start_hour + b.duration_hours:
                return b.activity
        return self.blocks[-1].activity  # edge case: exactly 24.0


class ConstantSchedule:
    """Same DailySchedule every day of the mission.

    The simplest mission schedule - no variation across days.
    """

    def __init__(self, schedule: DailySchedule):
        self.schedule = schedule

    def schedule_for_day(self, day: int) -> DailySchedule:
        return self.schedule


class WeeklySchedule:
    """7-day rotation: 5 weekdays (days 0-4) + 2 weekend days (days 5-6).

    Mirrors the ISS crew schedule pattern.
    """

    def __init__(self, weekday: DailySchedule, weekend: DailySchedule):
        self.weekday = weekday
        self.weekend = weekend

    def schedule_for_day(self, day: int) -> DailySchedule:
        return self.weekend if (day % 7) >= 5 else self.weekday


class CustomSchedule:
    """Arbitrary day-to-schedule mapping with a fallback default.

    Use for missions with non-repeating schedules (rest weeks,
    ramp-up periods, special event days).
    """

    def __init__(self, mapping: dict[int, DailySchedule], default: DailySchedule):
        self.mapping = mapping
        self.default = default

    def schedule_for_day(self, day: int) -> DailySchedule:
        return self.mapping.get(day, self.default)


# BVAD Table 3-24 reference day (exploration schedule)
REFERENCE_SCHEDULE = DailySchedule([
    ActivityBlock(SLEEP, 0.0, 8.0),
    ActivityBlock(NOMINAL, 8.0, 5.0),
    ActivityBlock(AEROBIC_EXERCISE, 13.0, 0.5),
    ActivityBlock(RESISTIVE_EXERCISE, 13.5, 1.0),
    ActivityBlock(RECOVERY, 14.5, 1.0),
    ActivityBlock(NOMINAL, 15.5, 8.5),
])

# BVAD Table 3-28 - ISS weekday crew schedule
# Exercise/Hygiene/Setup (2.5h) mapped to: Aerobic(0.5) + Resistive(1.0) + Recovery(1.0)
# All other waking activities (Planning, Review, Work Prep, Assembly,
# Meals, Housekeeping, Post Sleep, Pre-Sleep) mapped to NOMINAL.
# Weekday: 8h sleep (7h + 1h pre-sleep), 2.5h exercise, 13.5h nominal
ISS_WEEKDAY = DailySchedule([
    ActivityBlock(SLEEP, 0.0, 7.0),
    ActivityBlock(NOMINAL, 7.0, 6.0),         # post-sleep through morning work
    ActivityBlock(AEROBIC_EXERCISE, 13.0, 0.5),
    ActivityBlock(RESISTIVE_EXERCISE, 13.5, 1.0),
    ActivityBlock(RECOVERY, 14.5, 1.0),
    ActivityBlock(NOMINAL, 15.5, 7.5),         # afternoon work through pre-sleep
    ActivityBlock(SLEEP, 23.0, 1.0),           # pre-sleep counted as sleep
])

# BVAD Table 3-28 - ISS weekend crew schedule
# Weekend: 8.7h sleep (sleep + pre-sleep), 2.5h exercise, 12.8h nominal
ISS_WEEKEND = DailySchedule([
    ActivityBlock(SLEEP, 0.0, 8.7),
    ActivityBlock(NOMINAL, 8.7, 4.3),          # post-sleep, meals, housekeeping
    ActivityBlock(AEROBIC_EXERCISE, 13.0, 0.5),
    ActivityBlock(RESISTIVE_EXERCISE, 13.5, 1.0),
    ActivityBlock(RECOVERY, 14.5, 1.0),
    ActivityBlock(NOMINAL, 15.5, 8.5),         # recreation, meals, pre-sleep
])

# Pre-built weekly rotation combining ISS weekday and weekend
ISS_WEEKLY = WeeklySchedule(ISS_WEEKDAY, ISS_WEEKEND)
