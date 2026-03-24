"""CrewMember model with BVAD metabolic scaling.

Basal metabolic rate computed from NASA HIDH equations:
  - Eq 3-2: males > 19 years
  - Eq 3-3: females > 19 years

Daily metabolic rates (O2, CO2, heat, water, food) are scaled
proportionally from the 82 kg reference crewmember using the
ratio of individual BMR to reference BMR. This linear scaling
is an approximation - Table 3-26 shows that actual metabolic
partitioning varies nonlinearly with body size.
"""

from dataclasses import dataclass
from eclss.constants import (
    REFERENCE_CM_AGE,
    REFERENCE_CM_MASS_KG,
    REFERENCE_CM_HEIGHT_M,
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
    FECAL_SOLIDS_KG_PER_CM_DAY,
    URINE_SOLIDS_KG_PER_CM_DAY,
    PERSPIRATION_SOLIDS_KG_PER_CM_DAY,
)


def _bmr_male(age: float, mass_kg: float, height_m: float) -> float:
    """BVAD Eq 3-2: BMR for males > 19 years.

    Returns energy in MJ/CM-day.
    Formula: (622 - 9.53*age + 1.25*(15.9*mass + 539.6*height)) / 239.006
    The divisor 239.006 converts from kcal to MJ (via 239.006 kcal/MJ).
    """
    return (622 - 9.53 * age + 1.25 * (15.9 * mass_kg + 539.6 * height_m)) / 239.006


def _bmr_female(age: float, mass_kg: float, height_m: float) -> float:
    """BVAD Eq 3-3: BMR for females > 19 years.

    Returns energy in MJ/CM-day.
    Formula: (354 - 6.91*age + 1.25*(9.36*mass + 726*height)) / 239.006
    """
    return (354 - 6.91 * age + 1.25 * (9.36 * mass_kg + 726 * height_m)) / 239.006


def metabolic_rate_from_respiratory(vo2_lpm: float, vco2_lpm: float) -> float:
    """BVAD Eq 3-4: Metabolic rate from respiratory gas exchange.

    Uses the modified Weir equation. The coefficients 3.941 and 1.106
    are kcal per liter of O2 consumed and CO2 produced respectively.
    The 0.166 factor is an empirical coefficient from the BVAD that
    combines unit conversion and per-day integration. Treat it as a
    fixed constant from Eq 3-4 rather than deriving it independently.

    Args:
        vo2_lpm: O2 consumed (L/min at STPD)
        vco2_lpm: CO2 produced (L/min at STPD)

    Returns:
        Metabolic rate in MJ/CM-day.
    """
    return 0.166 * (3.941 * vo2_lpm + 1.106 * vco2_lpm)


# Cached reference BMR - computed once, used for all scaling
_REFERENCE_BMR = _bmr_male(REFERENCE_CM_AGE, REFERENCE_CM_MASS_KG, REFERENCE_CM_HEIGHT_M)


@dataclass
class CrewMember:
    """An individual crew member with BVAD-scaled metabolic rates.

    Attributes:
        name: Crew member identifier.
        age: Age in years (must be > 0).
        mass_kg: Body mass in kg (must be > 0).
        height_m: Height in meters (must be > 0).
        sex: Biological sex - "male" or "female" (determines BMR equation).
    """

    name: str
    age: float
    mass_kg: float
    height_m: float
    sex: str

    def __post_init__(self):
        if self.sex not in ("male", "female"):
            raise ValueError(f"sex must be 'male' or 'female', got '{self.sex}'")
        if self.mass_kg <= 0:
            raise ValueError(f"mass_kg must be > 0, got {self.mass_kg}")
        if self.height_m <= 0:
            raise ValueError(f"height_m must be > 0, got {self.height_m}")
        if self.age <= 0:
            raise ValueError(f"age must be > 0, got {self.age}")

    @property
    def basal_metabolic_rate_mj_day(self) -> float:
        """Basal metabolic rate from Eq 3-2 (male) or Eq 3-3 (female)."""
        if self.sex == "male":
            return _bmr_male(self.age, self.mass_kg, self.height_m)
        return _bmr_female(self.age, self.mass_kg, self.height_m)

    @property
    def _bmr_scale(self) -> float:
        """Ratio of this crew member's BMR to the reference CM's BMR."""
        return self.basal_metabolic_rate_mj_day / _REFERENCE_BMR

    # --- Scaled daily rates (all proportional to BMR ratio) ---

    @property
    def daily_o2_kg(self) -> float:
        return O2_CONSUMPTION_KG_PER_CM_DAY * self._bmr_scale

    @property
    def daily_co2_kg(self) -> float:
        return CO2_PRODUCTION_KG_PER_CM_DAY * self._bmr_scale

    @property
    def daily_metabolic_rate_kj(self) -> float:
        return METABOLIC_RATE_KJ_PER_CM_DAY * self._bmr_scale

    @property
    def daily_sensible_heat_kj(self) -> float:
        return METABOLIC_HEAT_SENSIBLE_KJ_PER_CM_DAY * self._bmr_scale

    @property
    def daily_latent_heat_kj(self) -> float:
        return METABOLIC_HEAT_LATENT_KJ_PER_CM_DAY * self._bmr_scale

    @property
    def daily_water_vapor_kg(self) -> float:
        return WATER_VAPOR_OUTPUT_KG_PER_CM_DAY * self._bmr_scale

    @property
    def daily_potable_water_kg(self) -> float:
        return POTABLE_WATER_KG_PER_CM_DAY * self._bmr_scale

    @property
    def daily_food_kg(self) -> float:
        return FOOD_DRY_MASS_KG_PER_CM_DAY * self._bmr_scale

    @property
    def daily_urine_kg(self) -> float:
        return URINE_OUTPUT_KG_PER_CM_DAY * self._bmr_scale

    @property
    def daily_fecal_water_kg(self) -> float:
        return FECAL_OUTPUT_KG_PER_CM_DAY * self._bmr_scale

    # --- Waste solids (Figure 3-4) ---

    @property
    def daily_fecal_solids_kg(self) -> float:
        return FECAL_SOLIDS_KG_PER_CM_DAY * self._bmr_scale

    @property
    def daily_urine_solids_kg(self) -> float:
        return URINE_SOLIDS_KG_PER_CM_DAY * self._bmr_scale

    @property
    def daily_perspiration_solids_kg(self) -> float:
        return PERSPIRATION_SOLIDS_KG_PER_CM_DAY * self._bmr_scale

    @property
    def daily_total_waste_solids_kg(self) -> float:
        return self.daily_fecal_solids_kg + self.daily_urine_solids_kg + self.daily_perspiration_solids_kg

    @property
    def daily_total_fecal_kg(self) -> float:
        """Fecal solids + fecal water combined."""
        return self.daily_fecal_solids_kg + self.daily_fecal_water_kg

    @property
    def daily_total_urine_kg(self) -> float:
        """Urine solids + urine water combined."""
        return self.daily_urine_solids_kg + self.daily_urine_kg
