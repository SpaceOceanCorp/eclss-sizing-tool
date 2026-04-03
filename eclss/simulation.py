"""Time-stepped ECLSS simulation engine.

Runs an hourly (configurable) simulation of cabin atmosphere dynamics,
tracking O2/CO2 partial pressures, crew metabolic loads by activity
schedule, and ECLSS hardware rate limits.
"""

import numpy as np

from eclss.habitat import Habitat
from eclss.system import EclssSystem
from eclss.crew import CrewMember
from eclss.activity import ActivityLevel
from eclss.schedule import ConstantSchedule, REFERENCE_SCHEDULE
from eclss.result import TimeSeriesResult
from eclss.constants import (
    O2_MOLAR_MASS, CO2_MOLAR_MASS,
    R_UNIVERSAL, TEMP_NOMINAL_K,
    O2_PP_TARGET_KPA, CO2_PP_DESIGN_TARGET_KPA,
    O2_PP_SAFE_RANGE_KPA, CO2_PP_SAFE_RANGE_KPA,
    REFERENCE_CM_AGE, REFERENCE_CM_MASS_KG, REFERENCE_CM_HEIGHT_M,
    O2_CONSUMPTION_KG_PER_CM_DAY,
    CO2_PRODUCTION_KG_PER_CM_DAY,
    METABOLIC_RATE_KJ_PER_CM_DAY,
)

# kJ/hr to watts: 1 kJ = 1000 J, 1 hr = 3600 s
_KJ_HR_TO_W = 1000.0 / 3600.0


def _compute_normalization(
    schedule, timestep_hours: float = 1.0
) -> tuple[float, float, float]:
    """Compute normalization factors by simulating one reference day.

    Table 3-24 per-activity rates don't exactly match Table 3-31 daily totals.
    Additionally, hourly sampling of sub-hourly activity blocks (e.g., 0.5h aerobic)
    overestimates high-rate activities. We normalize by running the given schedule
    through the same discretization the simulation uses, then scaling so the
    daily total matches the validated Table 3-31 constants.

    Args:
        schedule: A schedule object with schedule_for_day(day) method, or a
            DailySchedule with activity_at(hour) method.
        timestep_hours: Simulation timestep in hours.
    """
    steps_per_day = int(24.0 / timestep_hours)
    sampled_o2 = 0.0
    sampled_co2 = 0.0
    sampled_heat = 0.0

    # Support both DailySchedule (has activity_at) and schedule wrappers
    # (have schedule_for_day). Use day 0 for normalization.
    if hasattr(schedule, 'schedule_for_day'):
        daily = schedule.schedule_for_day(0)
    else:
        daily = schedule

    for step in range(steps_per_day):
        hour = step * timestep_hours
        act = daily.activity_at(hour)
        sampled_o2 += act.o2_consumption_g_min * 60.0 / 1000.0 * timestep_hours
        sampled_co2 += act.co2_production_g_min * 60.0 / 1000.0 * timestep_hours
        sampled_heat += act.metabolic_rate_kj_hr * timestep_hours
    o2_norm = O2_CONSUMPTION_KG_PER_CM_DAY / sampled_o2 if sampled_o2 > 0 else 1.0
    co2_norm = CO2_PRODUCTION_KG_PER_CM_DAY / sampled_co2 if sampled_co2 > 0 else 1.0
    heat_norm = METABOLIC_RATE_KJ_PER_CM_DAY / sampled_heat if sampled_heat > 0 else 1.0
    return o2_norm, co2_norm, heat_norm


class Simulation:
    """Time-stepped ECLSS simulation producing TimeSeriesResult.

    Tracks cabin O2/CO2 mass and partial pressure at each timestep.
    Crew metabolic demands vary by activity schedule and BMR scaling.
    ECLSS hardware rate limits cap O2 generation, CO2 removal, and
    heat rejection at each timestep.

    Args:
        habitat: Habitat instance defining crew, volume, and mission duration.
        system: ECLSS hardware limits (None = unlimited).
        schedules: Dict mapping crew name to a schedule object with
            schedule_for_day(day) method. Defaults to REFERENCE_SCHEDULE.
        timestep_hours: Simulation timestep (default 1.0 hour).
            Must evenly divide 24 hours.
    """

    def __init__(
        self,
        habitat: Habitat,
        system: EclssSystem | None = None,
        schedules: dict | None = None,
        timestep_hours: float = 1.0,
    ):
        # B11: Validate timestep divides 24h evenly
        steps_per_day = 24.0 / timestep_hours
        if abs(steps_per_day - round(steps_per_day)) > 1e-9:
            raise ValueError(
                f"timestep_hours={timestep_hours} does not evenly divide 24 hours"
            )

        self.habitat = habitat
        self.system = system or EclssSystem.unlimited()
        self.timestep_hours = timestep_hours

        # Resolve crew list
        if habitat.crew is not None:
            self.crew = list(habitat.crew)
        else:
            self.crew = [
                CrewMember(f"CM-{i+1}", REFERENCE_CM_AGE, REFERENCE_CM_MASS_KG,
                           REFERENCE_CM_HEIGHT_M, "male")
                for i in range(habitat.crew_count)
            ]

        # Resolve schedules -- default to REFERENCE_SCHEDULE for all crew
        default_schedule = ConstantSchedule(REFERENCE_SCHEDULE)
        if schedules is None:
            self._schedules = {cm.name: default_schedule for cm in self.crew}
        else:
            self._schedules = {
                cm.name: schedules.get(cm.name, default_schedule)
                for cm in self.crew
            }

        # Validate schedule keys match crew names
        if schedules is not None:
            crew_names = {cm.name for cm in self.crew}
            unknown = set(schedules.keys()) - crew_names
            if unknown:
                raise ValueError(
                    f"Schedule keys {unknown} don't match any crew member. "
                    f"Valid names: {crew_names}"
                )

        # Total simulation steps
        self.n_steps = int(habitat.mission_duration_days * 24 / timestep_hours)

        # Initial cabin conditions from ideal gas law: PV = nRT
        V = habitat.cabin_volume_m3
        T = TEMP_NOMINAL_K
        self.initial_o2_kg = (O2_PP_TARGET_KPA * 1000 * V) / (R_UNIVERSAL * T) * O2_MOLAR_MASS
        self.initial_co2_kg = (CO2_PP_DESIGN_TARGET_KPA * 1000 * V) / (R_UNIVERSAL * T) * CO2_MOLAR_MASS

        # Equipment heat (constant per step)
        self._equipment_heat_w = habitat.equipment_heat * len(self.crew)

        # Pre-compute metabolic rate arrays
        self._precompute_rates()

    def _precompute_rates(self) -> None:
        """Build numpy arrays of per-crew metabolic rates indexed by schedule.

        Activity indices are built dynamically from the actual activities
        encountered in each crew member's schedule, rather than from a
        hardcoded list. This supports custom activities.

        Normalization is computed per-schedule so that each crew member's
        schedule produces correct daily totals independent of the others.
        """
        n_crew = len(self.crew)
        n_steps = self.n_steps
        dt = self.timestep_hours

        self._crew_o2_rate = np.zeros((n_crew, n_steps))
        self._crew_co2_rate = np.zeros((n_crew, n_steps))
        self._crew_heat_rate = np.zeros((n_crew, n_steps))
        self._crew_activity_names: dict[str, list[str]] = {}

        for i, cm in enumerate(self.crew):
            scale = cm.bmr_scale
            schedule = self._schedules[cm.name]

            # B10: Per-schedule normalization
            o2_norm, co2_norm, heat_norm = _compute_normalization(schedule, dt)

            # Collect all unique activities from this crew member's schedule
            all_activities: list[ActivityLevel] = []
            seen: set[str] = set()
            activity_names: list[str] = []

            for step in range(n_steps):
                hour = step * dt
                day = int(hour // 24)
                hour_of_day = hour % 24.0
                daily = schedule.schedule_for_day(day)
                activity = daily.activity_at(hour_of_day)
                if activity.name not in seen:
                    seen.add(activity.name)
                    all_activities.append(activity)
                activity_names.append(activity.name)

            # Build activity index for this crew member
            activity_index = {act: idx for idx, act in enumerate(all_activities)}

            # Per-activity rates for this crew member, scaled by BMR and
            # normalized so daily average matches Table 3-31.
            # O2/CO2: g/min -> kg/hr (* 60 / 1000), then * norm * bmr_scale
            activity_o2 = np.array([
                act.o2_consumption_g_min * 60.0 / 1000.0 * o2_norm * scale
                for act in all_activities
            ])
            activity_co2 = np.array([
                act.co2_production_g_min * 60.0 / 1000.0 * co2_norm * scale
                for act in all_activities
            ])
            # Heat: kJ/hr -> watts, normalized
            activity_heat = np.array([
                act.metabolic_rate_kj_hr * _KJ_HR_TO_W * heat_norm * scale
                for act in all_activities
            ])

            # Build schedule index array for entire mission
            schedule_indices = np.empty(n_steps, dtype=np.int32)
            for step in range(n_steps):
                hour = step * dt
                day = int(hour // 24)
                hour_of_day = hour % 24.0
                daily = schedule.schedule_for_day(day)
                activity = daily.activity_at(hour_of_day)
                schedule_indices[step] = activity_index[activity]

            # Fancy-index: map schedule to actual rates
            self._crew_o2_rate[i, :] = activity_o2[schedule_indices]
            self._crew_co2_rate[i, :] = activity_co2[schedule_indices]
            self._crew_heat_rate[i, :] = activity_heat[schedule_indices]
            self._crew_activity_names[cm.name] = activity_names

    def run(self) -> TimeSeriesResult:
        """Execute the simulation and return time-series results."""
        dt = self.timestep_hours
        V = self.habitat.cabin_volume_m3
        T = TEMP_NOMINAL_K
        equip_heat = self._equipment_heat_w

        # B8: Pre-allocate output arrays with n+1 elements (initial + n steps)
        n = self.n_steps
        total = n + 1  # +1 for initial conditions at t=0
        cabin_o2 = np.empty(total)
        cabin_co2 = np.empty(total)
        cabin_o2_pp = np.empty(total)
        cabin_co2_pp = np.empty(total)
        total_o2_demand = np.empty(total)
        total_co2_prod = np.empty(total)
        total_heat = np.empty(total)
        o2_injected = np.empty(total)
        co2_removed = np.empty(total)
        heat_rejected = np.empty(total)

        # Initial state
        o2_mass = self.initial_o2_kg
        co2_mass = self.initial_co2_kg

        # Partial pressure conversion factor: pp = (mass / M) * R * T / (V * 1000) -> kPa
        pp_factor_o2 = R_UNIVERSAL * T / (O2_MOLAR_MASS * V * 1000.0)
        pp_factor_co2 = R_UNIVERSAL * T / (CO2_MOLAR_MASS * V * 1000.0)

        # B8: Record initial conditions at index 0 BEFORE the loop
        cabin_o2[0] = o2_mass
        cabin_co2[0] = co2_mass
        cabin_o2_pp[0] = o2_mass * pp_factor_o2
        cabin_co2_pp[0] = co2_mass * pp_factor_co2
        total_o2_demand[0] = 0.0   # no demand at t=0
        total_co2_prod[0] = 0.0
        total_heat[0] = 0.0
        o2_injected[0] = 0.0
        co2_removed[0] = 0.0
        heat_rejected[0] = 0.0

        # B8: Loop fills indices 1..n
        for t in range(1, total):
            step = t - 1  # index into crew rate arrays (0-based)

            # 1. Sum crew demands (vectorized across crew dimension)
            o2_demand = float(self._crew_o2_rate[:, step].sum())
            co2_prod = float(self._crew_co2_rate[:, step].sum())
            heat_demand = float(self._crew_heat_rate[:, step].sum()) + equip_heat

            # 2. Apply ECLSS rate caps
            o2_supply = self.system.effective_o2_rate(o2_demand)
            co2_removal = self.system.effective_co2_rate(co2_prod)

            # B9: Enforce heat rejection capacity
            heat = self.system.effective_heat_rate(heat_demand)

            # 3. Update cabin mass (supply replaces what crew consumed)
            o2_mass += (o2_supply - o2_demand) * dt
            co2_mass += (co2_prod - co2_removal) * dt
            o2_mass = max(0.0, o2_mass)
            co2_mass = max(0.0, co2_mass)

            # 4. Convert to partial pressure
            pp_o2 = o2_mass * pp_factor_o2
            pp_co2 = co2_mass * pp_factor_co2

            # 5. Store
            cabin_o2[t] = o2_mass
            cabin_co2[t] = co2_mass
            cabin_o2_pp[t] = pp_o2
            cabin_co2_pp[t] = pp_co2
            total_o2_demand[t] = o2_demand
            total_co2_prod[t] = co2_prod
            total_heat[t] = heat_demand
            o2_injected[t] = o2_supply
            co2_removed[t] = co2_removal
            heat_rejected[t] = heat

        # Build per-crew dicts (reference into pre-computed arrays)
        crew_o2 = {self.crew[i].name: self._crew_o2_rate[i, :].copy()
                   for i in range(len(self.crew))}
        crew_co2 = {self.crew[i].name: self._crew_co2_rate[i, :].copy()
                    for i in range(len(self.crew))}

        return TimeSeriesResult(
            time_hours=np.arange(total, dtype=np.float64) * dt,
            timestep_hours=dt,
            cabin_o2_mass_kg=cabin_o2,
            cabin_co2_mass_kg=cabin_co2,
            cabin_o2_pp_kpa=cabin_o2_pp,
            cabin_co2_pp_kpa=cabin_co2_pp,
            total_o2_demand_kg_hr=total_o2_demand,
            total_co2_production_kg_hr=total_co2_prod,
            total_heat_w=total_heat,
            o2_injected_kg_hr=o2_injected,
            co2_removed_kg_hr=co2_removed,
            heat_rejected_w=heat_rejected,
            crew_o2_demand_kg_hr=crew_o2,
            crew_co2_production_kg_hr=crew_co2,
            crew_activity=self._crew_activity_names,
            o2_pp_safe_range_kpa=O2_PP_SAFE_RANGE_KPA,
            co2_pp_safe_range_kpa=CO2_PP_SAFE_RANGE_KPA,
        )
