"""ECLSS -- Python library for life support system sizing based on NASA BVAD."""

# Core classes
from eclss.habitat import Habitat, LoopMode
from eclss.crew import CrewMember, CrewMetabolicProfile
from eclss.system import EclssSystem
from eclss.simulation import Simulation
from eclss.contaminants import ContaminantEstimator

# Results
from eclss.result import ECLSSResult, TimeSeriesResult

# Assessment
from eclss.assessment import (
    MinimumRequirements, SystemAssessment, Violation, assess_system,
)

# Activities (short-mission defaults)
from eclss.activity import (
    ActivityLevel,
    AEROBIC_EXERCISE, RESISTIVE_EXERCISE, RECOVERY, NOMINAL, SLEEP,
    ALL_ACTIVITIES, REFERENCE_DAY,
    # Long-mission sub-blocks
    SLEEP_LONG, NOMINAL_LONG,
    AEROBIC_0_15, AEROBIC_15_30,
    RESISTIVE_0_15, RESISTIVE_15_30, RESISTIVE_30_45, RESISTIVE_45_60,
    RECOVERY_0_15, RECOVERY_15_30, RECOVERY_30_45, RECOVERY_45_60,
    ALL_ACTIVITIES_LONG, REFERENCE_DAY_LONG,
)

# Schedules
from eclss.schedule import (
    Schedule, DailySchedule, ActivityBlock,
    ConstantSchedule, WeeklySchedule, CustomSchedule,
    REFERENCE_SCHEDULE, ISS_WEEKDAY, ISS_WEEKEND, ISS_WEEKLY,
)

__all__ = [
    # Core
    "Habitat", "LoopMode", "CrewMember", "CrewMetabolicProfile",
    "EclssSystem", "Simulation", "ContaminantEstimator",
    # Results
    "ECLSSResult", "TimeSeriesResult",
    # Assessment
    "MinimumRequirements", "SystemAssessment", "Violation", "assess_system",
    # Activities
    "ActivityLevel",
    "AEROBIC_EXERCISE", "RESISTIVE_EXERCISE", "RECOVERY", "NOMINAL", "SLEEP",
    "ALL_ACTIVITIES", "REFERENCE_DAY",
    "SLEEP_LONG", "NOMINAL_LONG",
    "AEROBIC_0_15", "AEROBIC_15_30",
    "RESISTIVE_0_15", "RESISTIVE_15_30", "RESISTIVE_30_45", "RESISTIVE_45_60",
    "RECOVERY_0_15", "RECOVERY_15_30", "RECOVERY_30_45", "RECOVERY_45_60",
    "ALL_ACTIVITIES_LONG", "REFERENCE_DAY_LONG",
    # Schedules
    "Schedule", "DailySchedule", "ActivityBlock",
    "ConstantSchedule", "WeeklySchedule", "CustomSchedule",
    "REFERENCE_SCHEDULE", "ISS_WEEKDAY", "ISS_WEEKEND", "ISS_WEEKLY",
]
