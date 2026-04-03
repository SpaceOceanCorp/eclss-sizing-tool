"""Habitat -- defines a crewed habitat and computes ECLSS requirements.

The Habitat holds crew, volume, duration, and loop mode. Call calculate()
to get steady-state daily rates and mission totals as an ECLSSResult.
"""

from enum import Enum

from eclss.crew import CrewMember
from eclss.constants import (
    CABIN_PRESSURE_NOMINAL_KPA,
    O2_PP_TARGET_KPA,
    CO2_PP_LIMIT_KPA,
    CABIN_LEAKAGE_RATE_KG_PER_MODULE_DAY,
    EQUIPMENT_HEAT_W_PER_CREW,
    WATER_RECOVERY_EFFICIENCY,
)
from eclss.result import ECLSSResult


class LoopMode(str, Enum):
    """Habitat loop mode. Inherits from str so "open" == LoopMode.OPEN."""
    OPEN = "open"
    CLOSED = "closed"


# Sabatier + electrolysis stoichiometry
_SABATIER_O2_RATIO = 32.0 / 44.0    # 1 mol CO2 -> 1 mol O2
_SABATIER_H2O_RATIO = 36.0 / 44.0   # 1 mol CO2 -> 2 mol H2O
_KJ_PER_DAY_TO_W = 1000.0 / 86400.0


def _resolve_loop_mode(loop_mode: str | LoopMode) -> str:
    """Normalize loop_mode to a plain string ("open" or "closed")."""
    if isinstance(loop_mode, LoopMode):
        return loop_mode.value
    if loop_mode in ("open", "closed"):
        return loop_mode
    raise ValueError(f"loop_mode must be 'open' or 'closed', got '{loop_mode}'")


class Habitat:
    """ECLSS sizing model for a crewed habitat.

    Args:
        crew: List of CrewMember objects.
        cabin_volume_m3: Habitable free volume.
        mission_duration_days: Mission length.
        loop_mode: "open" (all resupply) or "closed" (recovery).
        cabin_pressure_kpa: Total cabin pressure (default 101.0).
        o2_pp_target_kpa: O2 partial pressure target (default 21.2).
        cabin_leakage_rate_kg_per_day: Atmosphere leakage (default 0.02).
        equipment_heat_w_per_crew: Equipment heat per crew member.
        water_recovery_efficiency: WPA efficiency for closed-loop.
        sabatier_efficiency: Sabatier reactor efficiency (default 1.0).
    """

    def __init__(
        self,
        crew: list[CrewMember],
        cabin_volume_m3: float,
        mission_duration_days: int,
        *,
        loop_mode: str | LoopMode = LoopMode.OPEN,
        cabin_pressure_kpa: float = CABIN_PRESSURE_NOMINAL_KPA,
        o2_pp_target_kpa: float = O2_PP_TARGET_KPA,
        co2_pp_limit_kpa: float = CO2_PP_LIMIT_KPA,
        cabin_leakage_rate_kg_per_day: float = CABIN_LEAKAGE_RATE_KG_PER_MODULE_DAY,
        equipment_heat_w_per_crew: float = EQUIPMENT_HEAT_W_PER_CREW,
        water_recovery_efficiency: float = WATER_RECOVERY_EFFICIENCY,
        sabatier_efficiency: float = 1.0,
    ):
        if not crew:
            raise ValueError("crew must not be empty")
        if cabin_volume_m3 <= 0:
            raise ValueError(f"cabin_volume_m3 must be > 0, got {cabin_volume_m3}")
        if mission_duration_days < 1:
            raise ValueError(f"mission_duration_days must be >= 1, got {mission_duration_days}")

        self.crew = list(crew)
        self.crew_count = len(crew)
        self.cabin_volume_m3 = cabin_volume_m3
        self.mission_duration_days = mission_duration_days
        self.loop_mode = _resolve_loop_mode(loop_mode)
        self.cabin_pressure_kpa = cabin_pressure_kpa
        self.o2_pp_target_kpa = o2_pp_target_kpa
        self.co2_pp_limit_kpa = co2_pp_limit_kpa
        self.cabin_leakage = cabin_leakage_rate_kg_per_day
        self.equipment_heat = equipment_heat_w_per_crew
        self.water_recovery_efficiency = water_recovery_efficiency
        self.sabatier_efficiency = sabatier_efficiency

    def _avg(self, attr: str) -> float:
        """Average a daily property across the crew."""
        return sum(getattr(cm, attr) for cm in self.crew) / self.crew_count

    def calculate(self) -> ECLSSResult:
        """Compute steady-state ECLSS sizing requirements."""
        n = self.crew_count
        d = self.mission_duration_days

        # Per-capita averages from crew
        o2 = self._avg("daily_o2_kg")
        co2 = self._avg("daily_co2_kg")
        sensible = self._avg("daily_sensible_heat_kj")
        latent = self._avg("daily_latent_heat_kj")
        potable = self._avg("daily_potable_water_kg")
        food_water = self._avg("daily_food_water_kg")
        food = self._avg("daily_food_kg")
        urine = self._avg("daily_urine_kg")
        fecal = self._avg("daily_fecal_water_kg")
        vapor = self._avg("daily_water_vapor_kg")
        met_water = self._avg("daily_metabolic_water_kg")

        # Atmosphere
        o2_frac = self.o2_pp_target_kpa / self.cabin_pressure_kpa
        o2_gen = (o2 * n) + (self.cabin_leakage * o2_frac)
        co2_rem = co2 * n

        # Thermal
        crew_heat = (sensible + latent) * _KJ_PER_DAY_TO_W * n
        equip_heat = self.equipment_heat * n

        # Water
        consumption = (potable + food_water) * n
        production = (urine + fecal + vapor + met_water) * n

        if self.loop_mode == "open":
            resupply = consumption
            eff_req = 0.0
            sab_water = 0.0
            o2_total = o2 * n * d
            o2_recovered = 0.0
            water_recovered = 0.0
        else:
            eff_req = consumption / production if production > 0 else 0.0
            sab_water = co2 * n * _SABATIER_H2O_RATIO * self.sabatier_efficiency
            recovered = production * self.water_recovery_efficiency + sab_water
            resupply = max(0.0, consumption - recovered)
            o2_rec_daily = co2 * n * _SABATIER_O2_RATIO * self.sabatier_efficiency
            o2_total = max(0.0, o2 * n - o2_rec_daily) * d
            o2_recovered = o2_rec_daily * d
            water_recovered = recovered * d

        return ECLSSResult(
            crew_count=n,
            cabin_volume_m3=self.cabin_volume_m3,
            mission_duration_days=d,
            loop_mode=self.loop_mode,
            o2_generation_rate_kg_day=o2_gen,
            co2_removal_rate_kg_day=co2_rem,
            cabin_leakage_rate_kg_day=self.cabin_leakage,
            crew_metabolic_heat_w=crew_heat,
            equipment_heat_w=equip_heat,
            total_heat_rejection_w=crew_heat + equip_heat,
            water_consumption_kg_day=consumption,
            water_production_kg_day=production,
            water_recovery_efficiency_required=eff_req,
            water_resupply_kg_day=resupply,
            sabatier_water_kg_day=sab_water,
            total_o2_kg=o2_total,
            total_water_kg=resupply * d,
            total_food_kg=food * n * d,
            o2_from_co2_recovery_kg=o2_recovered,
            water_recovered_kg=water_recovered,
        )

    def __repr__(self) -> str:
        return (f"Habitat({self.crew_count} crew, {self.cabin_volume_m3} m³, "
                f"{self.mission_duration_days} days, {self.loop_mode})")
