"""Activity-level metabolic rates from BVAD Table 3-24.

Reference crewmember (82 kg), standard exploration exercise schedule.
Each ActivityLevel holds per-hour rates for a single activity type.
REFERENCE_DAY maps activities to their daily durations (must sum to 24h).
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ActivityLevel:
    """Metabolic rates for a single activity type (reference crewmember).

    All rates are for an 82 kg reference CM. Scale by BMR ratio for
    individualized crew members.
    """

    name: str
    metabolic_rate_kj_hr: float
    o2_consumption_g_min: float
    co2_production_g_min: float


# BVAD Table 3-24 - per-activity rates for reference crewmember
AEROBIC_EXERCISE = ActivityLevel("Aerobic Exercise", 3484.0, 3.99, 5.22)
RESISTIVE_EXERCISE = ActivityLevel("Resistive Exercise", 1250.0, 1.43, 1.89)
RECOVERY = ActivityLevel("Recovery", 500.0, 0.59, 0.69)
NOMINAL = ActivityLevel("Nominal", 500.0, 0.59, 0.69)
SLEEP = ActivityLevel("Sleep", 316.0, 0.37, 0.44)

ALL_ACTIVITIES = [AEROBIC_EXERCISE, RESISTIVE_EXERCISE, RECOVERY, NOMINAL, SLEEP]

# Table 3-24 reference day - hours per activity (must sum to 24.0)
REFERENCE_DAY: dict[ActivityLevel, float] = {
    AEROBIC_EXERCISE: 0.5,
    RESISTIVE_EXERCISE: 1.0,
    RECOVERY: 1.0,
    NOMINAL: 13.5,
    SLEEP: 8.0,
}
