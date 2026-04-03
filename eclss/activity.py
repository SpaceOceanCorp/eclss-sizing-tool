"""Activity-level metabolic and thermal rates from BVAD Tables 3-24 / 3-25.

Reference crewmember (82 kg), standard exploration exercise schedule.
Each ActivityLevel holds per-hour metabolic and thermal rates for one activity.
REFERENCE_DAY maps activities to daily durations (sums to 24h).
REFERENCE_DAY_LONG uses 15-minute sub-blocks from Table 3-25.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ActivityLevel:
    """Metabolic and thermal rates for a single activity (reference crewmember).

    All rates are for an 82 kg reference CM. Scale by BMR ratio for
    individualized crew members.

    Heat columns are in kJ/hr. Water vapor and sweat are in g/min.
    """

    name: str
    metabolic_rate_kj_hr: float
    o2_consumption_g_min: float
    co2_production_g_min: float
    sensible_heat_kj_hr: float
    latent_heat_kj_hr: float
    water_vapor_g_min: float
    sweat_g_min: float


# ---------------------------------------------------------------------------
# Table 3-24 / 3-25 short-mission activities (averaged thermal values)
#
# Metabolic rate, O2, CO2 from Table 3-24.
# Thermal values: Sleep and Nominal taken directly from Table 3-25.
# Aerobic, Resistive, Recovery averaged across their sub-blocks
# (equal-duration 15-min blocks, so simple arithmetic mean).
# ---------------------------------------------------------------------------

SLEEP = ActivityLevel(
    "Sleep", 316.0, 0.37, 0.44,
    sensible_heat_kj_hr=160.0,
    latent_heat_kj_hr=157.0,
    water_vapor_g_min=1.08,
    sweat_g_min=0.0,
)

NOMINAL = ActivityLevel(
    "Nominal", 500.0, 0.59, 0.69,
    sensible_heat_kj_hr=306.0,
    latent_heat_kj_hr=194.0,
    water_vapor_g_min=1.33,
    sweat_g_min=0.0,
)

AEROBIC_EXERCISE = ActivityLevel(
    "Aerobic Exercise", 3484.0, 3.99, 5.22,
    sensible_heat_kj_hr=474.5,       # mean of 2 sub-blocks
    latent_heat_kj_hr=1490.0,
    water_vapor_g_min=10.235,
    sweat_g_min=6.58,
)

RESISTIVE_EXERCISE = ActivityLevel(
    "Resistive Exercise", 1250.0, 1.43, 1.89,
    sensible_heat_kj_hr=360.5,       # mean of 4 sub-blocks
    latent_heat_kj_hr=1189.0,
    water_vapor_g_min=8.1575,
    sweat_g_min=3.8175,
)

RECOVERY = ActivityLevel(
    "Recovery", 500.0, 0.59, 0.69,
    sensible_heat_kj_hr=298.5,       # mean of 4 sub-blocks
    latent_heat_kj_hr=288.0,
    water_vapor_g_min=1.98,
    sweat_g_min=0.0,
)

ALL_ACTIVITIES = [AEROBIC_EXERCISE, RESISTIVE_EXERCISE, RECOVERY, NOMINAL, SLEEP]

# Table 3-24 reference day (hours per activity, sums to 24.0)
REFERENCE_DAY: dict[ActivityLevel, float] = {
    AEROBIC_EXERCISE: 0.5,
    RESISTIVE_EXERCISE: 1.0,
    RECOVERY: 1.0,
    NOMINAL: 13.5,
    SLEEP: 8.0,
}


# ---------------------------------------------------------------------------
# Table 3-25 long-mission sub-blocks (15-minute resolution)
#
# Heat values (kJ/hr) and vapor/sweat (g/min) are taken directly from
# Table 3-25 -- no unit conversion needed. Each sub-block represents one
# 15-minute interval (0.25 hr). O2/CO2 are constant within each activity
# type (same as Table 3-24).
# ---------------------------------------------------------------------------

SLEEP_LONG = ActivityLevel(
    "Sleep", 316.0, 0.37, 0.44,
    sensible_heat_kj_hr=160.0,
    latent_heat_kj_hr=157.0,
    water_vapor_g_min=1.08,
    sweat_g_min=0.0,
)

NOMINAL_LONG = ActivityLevel(
    "Nominal", 500.0, 0.59, 0.69,
    sensible_heat_kj_hr=306.0,
    latent_heat_kj_hr=194.0,
    water_vapor_g_min=1.33,
    sweat_g_min=0.0,
)

# Aerobic exercise (2 x 15-min sub-blocks)
AEROBIC_0_15 = ActivityLevel(
    "Aerobic 0-15", 3484.0, 3.99, 5.22,
    sensible_heat_kj_hr=482.0,
    latent_heat_kj_hr=1018.0,
    water_vapor_g_min=6.99,
    sweat_g_min=1.34,
)
AEROBIC_15_30 = ActivityLevel(
    "Aerobic 15-30", 3484.0, 3.99, 5.22,
    sensible_heat_kj_hr=467.0,
    latent_heat_kj_hr=1962.0,
    water_vapor_g_min=13.48,
    sweat_g_min=11.82,
)

# Resistive exercise (4 x 15-min sub-blocks)
RESISTIVE_0_15 = ActivityLevel(
    "Resistive 0-15", 1250.0, 1.43, 1.89,
    sensible_heat_kj_hr=417.0,
    latent_heat_kj_hr=1689.0,
    water_vapor_g_min=11.60,
    sweat_g_min=11.86,
)
RESISTIVE_15_30 = ActivityLevel(
    "Resistive 15-30", 1250.0, 1.43, 1.89,
    sensible_heat_kj_hr=347.0,
    latent_heat_kj_hr=1231.0,
    water_vapor_g_min=8.44,
    sweat_g_min=2.18,
)
RESISTIVE_30_45 = ActivityLevel(
    "Resistive 30-45", 1250.0, 1.43, 1.89,
    sensible_heat_kj_hr=338.0,
    latent_heat_kj_hr=972.0,
    water_vapor_g_min=6.66,
    sweat_g_min=0.78,
)
RESISTIVE_45_60 = ActivityLevel(
    "Resistive 45-60", 1250.0, 1.43, 1.89,
    sensible_heat_kj_hr=340.0,
    latent_heat_kj_hr=864.0,
    water_vapor_g_min=5.93,
    sweat_g_min=0.45,
)

# Recovery (4 x 15-min sub-blocks)
RECOVERY_0_15 = ActivityLevel(
    "Recovery 0-15", 500.0, 0.59, 0.69,
    sensible_heat_kj_hr=298.0,
    latent_heat_kj_hr=301.0,
    water_vapor_g_min=2.07,
    sweat_g_min=0.0,
)
RECOVERY_15_30 = ActivityLevel(
    "Recovery 15-30", 500.0, 0.59, 0.69,
    sensible_heat_kj_hr=301.0,
    latent_heat_kj_hr=260.0,
    water_vapor_g_min=1.79,
    sweat_g_min=0.0,
)
RECOVERY_30_45 = ActivityLevel(
    "Recovery 30-45", 500.0, 0.59, 0.69,
    sensible_heat_kj_hr=295.0,
    latent_heat_kj_hr=320.0,
    water_vapor_g_min=2.20,
    sweat_g_min=0.0,
)
RECOVERY_45_60 = ActivityLevel(
    "Recovery 45-60", 500.0, 0.59, 0.69,
    sensible_heat_kj_hr=300.0,
    latent_heat_kj_hr=271.0,
    water_vapor_g_min=1.86,
    sweat_g_min=0.0,
)

ALL_ACTIVITIES_LONG = [
    SLEEP_LONG, NOMINAL_LONG,
    AEROBIC_0_15, AEROBIC_15_30,
    RESISTIVE_0_15, RESISTIVE_15_30, RESISTIVE_30_45, RESISTIVE_45_60,
    RECOVERY_0_15, RECOVERY_15_30, RECOVERY_30_45, RECOVERY_45_60,
]

# Long-mission reference day (sub-blocks sum to 24.0h)
REFERENCE_DAY_LONG: dict[ActivityLevel, float] = {
    AEROBIC_0_15: 0.25,
    AEROBIC_15_30: 0.25,
    RESISTIVE_0_15: 0.25,
    RESISTIVE_15_30: 0.25,
    RESISTIVE_30_45: 0.25,
    RESISTIVE_45_60: 0.25,
    RECOVERY_0_15: 0.25,
    RECOVERY_15_30: 0.25,
    RECOVERY_30_45: 0.25,
    RECOVERY_45_60: 0.25,
    NOMINAL_LONG: 13.5,
    SLEEP_LONG: 8.0,
}
