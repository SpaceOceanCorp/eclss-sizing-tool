"""Habitat class — core ECLSS sizing computation."""

from eclss.constants import (
    O2_CONSUMPTION_KG_PER_CM_DAY,
    CO2_PRODUCTION_KG_PER_CM_DAY,
    METABOLIC_RATE_KJ_PER_CM_DAY,
    METABOLIC_HEAT_SENSIBLE_KJ_PER_CM_DAY,
    METABOLIC_HEAT_LATENT_KJ_PER_CM_DAY,
    WATER_VAPOR_OUTPUT_KG_PER_CM_DAY,
    POTABLE_WATER_KG_PER_CM_DAY,
    FOOD_DRY_MASS_KG_PER_CM_DAY,
    URINE_OUTPUT_KG_PER_CM_DAY,
    FECAL_OUTPUT_KG_PER_CM_DAY,
    CABIN_PRESSURE_NOMINAL_KPA,
    O2_PP_TARGET_KPA,
    CO2_PP_LIMIT_KPA,
    CABIN_LEAKAGE_RATE_KG_PER_MODULE_DAY,
    EQUIPMENT_HEAT_W_PER_CREW,
    WATER_RECOVERY_EFFICIENCY,
)
from eclss.result import ECLSSResult


# Sabatier + electrolysis O2 recovery: 1 mol CO2 (44 g) -> 1 mol O2 (32 g)
_SABATIER_O2_MASS_RATIO = 32.0 / 44.0

# kJ/day to watts: 1 kJ = 1000 J, 1 day = 86400 s
_KJ_PER_DAY_TO_W = 1000.0 / 86400.0


class Habitat:
    """ECLSS sizing model for a crewed habitat.

    All BVAD reference values can be overridden via constructor kwargs.
    Call calculate() to compute life support requirements.
    """

    def __init__(
        self,
        # Required inputs
        crew_count: int,
        cabin_volume_m3: float,
        mission_duration_days: int,
        # Atmosphere defaults
        cabin_pressure_kpa: float = CABIN_PRESSURE_NOMINAL_KPA,
        o2_pp_target_kpa: float = O2_PP_TARGET_KPA,
        co2_pp_limit_kpa: float = CO2_PP_LIMIT_KPA,
        # Mode
        loop_mode: str = "open",
        # Crew metabolic overrides
        o2_consumption_kg_per_cm_day: float = O2_CONSUMPTION_KG_PER_CM_DAY,
        co2_production_kg_per_cm_day: float = CO2_PRODUCTION_KG_PER_CM_DAY,
        metabolic_rate_kj_per_cm_day: float = METABOLIC_RATE_KJ_PER_CM_DAY,
        metabolic_heat_sensible_kj_per_cm_day: float = METABOLIC_HEAT_SENSIBLE_KJ_PER_CM_DAY,
        metabolic_heat_latent_kj_per_cm_day: float = METABOLIC_HEAT_LATENT_KJ_PER_CM_DAY,
        water_vapor_output_kg_per_cm_day: float = WATER_VAPOR_OUTPUT_KG_PER_CM_DAY,
        potable_water_kg_per_cm_day: float = POTABLE_WATER_KG_PER_CM_DAY,
        food_dry_mass_kg_per_cm_day: float = FOOD_DRY_MASS_KG_PER_CM_DAY,
        urine_output_kg_per_cm_day: float = URINE_OUTPUT_KG_PER_CM_DAY,
        fecal_output_kg_per_cm_day: float = FECAL_OUTPUT_KG_PER_CM_DAY,
        # Leakage & equipment
        cabin_leakage_rate_kg_per_day: float = CABIN_LEAKAGE_RATE_KG_PER_MODULE_DAY,
        equipment_heat_w_per_crew: float = EQUIPMENT_HEAT_W_PER_CREW,
        # Recovery assumptions (closed-loop)
        water_recovery_efficiency: float = WATER_RECOVERY_EFFICIENCY,
    ):
        if loop_mode not in ("open", "closed"):
            raise ValueError(
                f"loop_mode must be 'open' or 'closed', got '{loop_mode}'"
            )

        self.crew_count = crew_count
        self.cabin_volume_m3 = cabin_volume_m3
        self.mission_duration_days = mission_duration_days
        self.cabin_pressure_kpa = cabin_pressure_kpa
        self.o2_pp_target_kpa = o2_pp_target_kpa
        self.co2_pp_limit_kpa = co2_pp_limit_kpa
        self.loop_mode = loop_mode
        self.o2_consumption = o2_consumption_kg_per_cm_day
        self.co2_production = co2_production_kg_per_cm_day
        self.metabolic_rate = metabolic_rate_kj_per_cm_day
        self.sensible_heat = metabolic_heat_sensible_kj_per_cm_day
        self.latent_heat = metabolic_heat_latent_kj_per_cm_day
        self.water_vapor = water_vapor_output_kg_per_cm_day
        self.potable_water = potable_water_kg_per_cm_day
        self.food_dry_mass = food_dry_mass_kg_per_cm_day
        self.urine_output = urine_output_kg_per_cm_day
        self.fecal_output = fecal_output_kg_per_cm_day
        self.cabin_leakage = cabin_leakage_rate_kg_per_day
        self.equipment_heat = equipment_heat_w_per_crew
        self.water_recovery_efficiency = water_recovery_efficiency

    def calculate(self) -> ECLSSResult:
        """Compute ECLSS sizing requirements and return an ECLSSResult."""
        atmo = self._calc_atmosphere()
        thermal = self._calc_thermal()
        water = self._calc_water()
        consumables = self._calc_consumables(water)

        return ECLSSResult(
            crew_count=self.crew_count,
            cabin_volume_m3=self.cabin_volume_m3,
            mission_duration_days=self.mission_duration_days,
            loop_mode=self.loop_mode,
            **atmo,
            **thermal,
            **water,
            **consumables,
        )

    def _calc_atmosphere(self) -> dict:
        """O2 generation and CO2 removal rates."""
        n = self.crew_count

        # O2 fraction of leaked atmosphere (partial pressure ratio)
        o2_fraction = self.o2_pp_target_kpa / self.cabin_pressure_kpa

        # O2 needed: crew metabolic demand + makeup for O2 lost to leakage
        o2_rate = (self.o2_consumption * n) + (self.cabin_leakage * o2_fraction)

        # CO2 removal: must match crew production rate at steady state
        co2_rate = self.co2_production * n

        return {
            "o2_generation_rate_kg_day": o2_rate,
            "co2_removal_rate_kg_day": co2_rate,
            "cabin_leakage_rate_kg_day": self.cabin_leakage,
        }

    def _calc_thermal(self) -> dict:
        """Heat rejection loads in watts."""
        n = self.crew_count

        # Convert kJ/day to W for each crew member, then multiply by crew
        sensible_w = self.sensible_heat * _KJ_PER_DAY_TO_W * n
        latent_w = self.latent_heat * _KJ_PER_DAY_TO_W * n
        crew_heat = sensible_w + latent_w

        equip_heat = self.equipment_heat * n
        total = crew_heat + equip_heat

        return {
            "crew_metabolic_heat_w": crew_heat,
            "equipment_heat_w": equip_heat,
            "total_heat_rejection_w": total,
        }

    def _calc_water(self) -> dict:
        """Water balance: consumption vs production."""
        n = self.crew_count

        consumption = self.potable_water * n
        production = (self.urine_output + self.water_vapor) * n

        if self.loop_mode == "open":
            return {
                "water_consumption_kg_day": consumption,
                "water_production_kg_day": production,
                "water_recovery_efficiency_required": 0.0,
                "water_resupply_kg_day": consumption,
            }

        # Closed-loop: compute recovery
        efficiency_required = consumption / production if production > 0 else 0.0
        recovered = production * self.water_recovery_efficiency
        resupply = consumption - recovered

        return {
            "water_consumption_kg_day": consumption,
            "water_production_kg_day": production,
            "water_recovery_efficiency_required": efficiency_required,
            "water_resupply_kg_day": resupply,
        }

    def _calc_consumables(self, water: dict) -> dict:
        """Mission total consumables in kg."""
        n = self.crew_count
        d = self.mission_duration_days

        # Daily O2 need: crew only, leakage is atmosphere makeup
        daily_o2 = self.o2_consumption * n
        total_food = self.food_dry_mass * n * d

        if self.loop_mode == "open":
            return {
                "total_o2_kg": daily_o2 * d,
                "total_water_kg": water["water_resupply_kg_day"] * d,
                "total_food_kg": total_food,
                "o2_from_co2_recovery_kg": 0.0,
                "water_recovered_kg": 0.0,
            }

        # Closed-loop: Sabatier + electrolysis recovers O2 from CO2
        daily_co2 = self.co2_production * n
        daily_o2_recovered = daily_co2 * _SABATIER_O2_MASS_RATIO
        net_daily_o2 = max(0.0, daily_o2 - daily_o2_recovered)

        # Water recovered per day
        daily_water_recovered = water["water_production_kg_day"] * self.water_recovery_efficiency

        return {
            "total_o2_kg": net_daily_o2 * d,
            "total_water_kg": water["water_resupply_kg_day"] * d,
            "total_food_kg": total_food,
            "o2_from_co2_recovery_kg": daily_o2_recovered * d,
            "water_recovered_kg": daily_water_recovered * d,
        }
