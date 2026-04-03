"""CrewMember model with BVAD metabolic scaling.

Basal metabolic rate computed from NASA HIDH equations:
  - Eq 3-2: males > 19 years
  - Eq 3-3: females > 19 years

Daily metabolic rates (O2, CO2, heat, water, food) are scaled
proportionally from the 82 kg reference crewmember using the
ratio of individual BMR to reference BMR. This linear scaling
is an approximation - Table 3-26 shows that actual metabolic
partitioning varies nonlinearly with body size.

Per-astronaut overrides are supported via CrewMetabolicProfile.
"""

from __future__ import annotations
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
    FOOD_WATER_KG_PER_CM_DAY,
    METABOLIC_WATER_KG_PER_CM_DAY,
    URINE_OUTPUT_KG_PER_CM_DAY,
    FECAL_OUTPUT_KG_PER_CM_DAY,
    FECAL_SOLIDS_KG_PER_CM_DAY,
    URINE_SOLIDS_KG_PER_CM_DAY,
    PERSPIRATION_SOLIDS_KG_PER_CM_DAY,
    SWEAT_OUTPUT_KG_PER_CM_DAY,
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
    combines unit conversion and per-day integration.

    Args:
        vo2_lpm: O2 consumed (L/min at STPD)
        vco2_lpm: CO2 produced (L/min at STPD)

    Returns:
        Metabolic rate in MJ/CM-day.
    """
    return 0.166 * (3.941 * vo2_lpm + 1.106 * vco2_lpm)


# Cached reference BMR - computed once, used for all scaling
_REFERENCE_BMR = _bmr_male(REFERENCE_CM_AGE, REFERENCE_CM_MASS_KG, REFERENCE_CM_HEIGHT_M)


@dataclass(frozen=True)
class CrewMetabolicProfile:
    """Optional per-astronaut metabolic rate overrides.

    All fields default to None, meaning "use BVAD default scaled by BMR".
    Set a field to a specific value to override the BVAD-scaled rate.
    All values are in kg/day or kJ/day as indicated by the field name.

    Example:
        # Override only O2 consumption; everything else BVAD-scaled
        profile = CrewMetabolicProfile(o2_kg_day=0.85)
    """

    o2_kg_day: float | None = None
    co2_kg_day: float | None = None
    metabolic_rate_kj_day: float | None = None
    sensible_heat_kj_day: float | None = None
    latent_heat_kj_day: float | None = None
    water_vapor_kg_day: float | None = None
    potable_water_kg_day: float | None = None
    food_kg_day: float | None = None
    food_water_kg_day: float | None = None
    metabolic_water_kg_day: float | None = None
    urine_kg_day: float | None = None
    fecal_water_kg_day: float | None = None
    sweat_kg_day: float | None = None
    fecal_solids_kg_day: float | None = None
    urine_solids_kg_day: float | None = None
    perspiration_solids_kg_day: float | None = None

    @classmethod
    def zero(cls) -> CrewMetabolicProfile:
        """All rates zeroed -- see system requirements without crew metabolic load."""
        return cls(
            o2_kg_day=0.0, co2_kg_day=0.0, metabolic_rate_kj_day=0.0,
            sensible_heat_kj_day=0.0, latent_heat_kj_day=0.0,
            water_vapor_kg_day=0.0, potable_water_kg_day=0.0,
            food_kg_day=0.0, food_water_kg_day=0.0, metabolic_water_kg_day=0.0,
            urine_kg_day=0.0, fecal_water_kg_day=0.0, sweat_kg_day=0.0,
            fecal_solids_kg_day=0.0, urine_solids_kg_day=0.0,
            perspiration_solids_kg_day=0.0,
        )



@dataclass(frozen=True)
class CrewMember:
    """An individual crew member with BVAD-scaled metabolic rates.

    Metabolic rates default to BVAD values scaled by BMR ratio.
    Override any rate via the profile parameter.

    Args:
        name: Crew member identifier.
        age: Age in years (must be >= 19).
        mass_kg: Body mass in kg (must be > 0).
        height_m: Height in meters (must be > 0).
        sex: "male" or "female" (determines BMR equation).
        profile: Optional metabolic rate overrides.

    Example:
        # BVAD defaults
        cm = CrewMember("Kirk", 35, 80.0, 1.80, "male")

        # With overrides
        cm = CrewMember("Kirk", 35, 80.0, 1.80, "male",
                        profile=CrewMetabolicProfile(o2_kg_day=0.85))
    """

    name: str
    age: float
    mass_kg: float
    height_m: float
    sex: str
    profile: CrewMetabolicProfile | None = None

    def __post_init__(self):
        if self.sex not in ("male", "female"):
            raise ValueError(f"sex must be 'male' or 'female', got '{self.sex}'")
        if self.mass_kg <= 0:
            raise ValueError(f"mass_kg must be > 0, got {self.mass_kg}")
        if self.height_m <= 0:
            raise ValueError(f"height_m must be > 0, got {self.height_m}")
        if self.age < 19:
            raise ValueError(
                f"age must be >= 19 (BMR equations only valid for adults), got {self.age}"
            )
        # Cache BMR and scale
        if self.sex == "male":
            bmr = _bmr_male(self.age, self.mass_kg, self.height_m)
        else:
            bmr = _bmr_female(self.age, self.mass_kg, self.height_m)
        object.__setattr__(self, '_cached_bmr_mj_day', bmr)
        object.__setattr__(self, '_cached_bmr_scale', bmr / _REFERENCE_BMR)

    @classmethod
    def reference_crew(cls, n: int = 4) -> list[CrewMember]:
        """Create n BVAD reference crew members (82 kg, 40 yr, 1.77 m, male)."""
        return [
            cls(f"CM-{i+1}", REFERENCE_CM_AGE, REFERENCE_CM_MASS_KG,
                REFERENCE_CM_HEIGHT_M, "male")
            for i in range(n)
        ]

    @property
    def basal_metabolic_rate_mj_day(self) -> float:
        """Basal metabolic rate from Eq 3-2 (male) or Eq 3-3 (female), cached."""
        return self._cached_bmr_mj_day

    @property
    def bmr_scale(self) -> float:
        """Ratio of this crew member's BMR to the reference CM's BMR."""
        return self._cached_bmr_scale

    # --- Helper for override-or-scale pattern ---

    def _get(self, profile_field: str, bvad_constant: float) -> float:
        if self.profile is not None:
            val = getattr(self.profile, profile_field)
            if val is not None:
                return val
        return bvad_constant * self.bmr_scale

    # --- Scaled daily rates (all use BVAD default unless profile overrides) ---

    @property
    def daily_o2_kg(self) -> float:
        return self._get("o2_kg_day", O2_CONSUMPTION_KG_PER_CM_DAY)

    @property
    def daily_co2_kg(self) -> float:
        return self._get("co2_kg_day", CO2_PRODUCTION_KG_PER_CM_DAY)

    @property
    def daily_metabolic_rate_kj(self) -> float:
        return self._get("metabolic_rate_kj_day", METABOLIC_RATE_KJ_PER_CM_DAY)

    @property
    def daily_sensible_heat_kj(self) -> float:
        return self._get("sensible_heat_kj_day", METABOLIC_HEAT_SENSIBLE_KJ_PER_CM_DAY)

    @property
    def daily_latent_heat_kj(self) -> float:
        return self._get("latent_heat_kj_day", METABOLIC_HEAT_LATENT_KJ_PER_CM_DAY)

    @property
    def daily_water_vapor_kg(self) -> float:
        return self._get("water_vapor_kg_day", WATER_VAPOR_OUTPUT_KG_PER_CM_DAY)

    @property
    def daily_potable_water_kg(self) -> float:
        return self._get("potable_water_kg_day", POTABLE_WATER_KG_PER_CM_DAY)

    @property
    def daily_food_kg(self) -> float:
        return self._get("food_kg_day", FOOD_DRY_MASS_KG_PER_CM_DAY)

    @property
    def daily_urine_kg(self) -> float:
        return self._get("urine_kg_day", URINE_OUTPUT_KG_PER_CM_DAY)

    @property
    def daily_fecal_water_kg(self) -> float:
        return self._get("fecal_water_kg_day", FECAL_OUTPUT_KG_PER_CM_DAY)

    @property
    def daily_food_water_kg(self) -> float:
        return self._get("food_water_kg_day", FOOD_WATER_KG_PER_CM_DAY)

    @property
    def daily_metabolic_water_kg(self) -> float:
        return self._get("metabolic_water_kg_day", METABOLIC_WATER_KG_PER_CM_DAY)

    @property
    def daily_sweat_kg(self) -> float:
        return self._get("sweat_kg_day", SWEAT_OUTPUT_KG_PER_CM_DAY)

    # --- Waste solids (Figure 3-4) ---

    @property
    def daily_fecal_solids_kg(self) -> float:
        return self._get("fecal_solids_kg_day", FECAL_SOLIDS_KG_PER_CM_DAY)

    @property
    def daily_urine_solids_kg(self) -> float:
        return self._get("urine_solids_kg_day", URINE_SOLIDS_KG_PER_CM_DAY)

    @property
    def daily_perspiration_solids_kg(self) -> float:
        return self._get("perspiration_solids_kg_day", PERSPIRATION_SOLIDS_KG_PER_CM_DAY)

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

    def summary(self) -> dict[str, float]:
        """All daily metabolic rates as a dict."""
        return {
            "o2_kg": self.daily_o2_kg,
            "co2_kg": self.daily_co2_kg,
            "metabolic_rate_kj": self.daily_metabolic_rate_kj,
            "sensible_heat_kj": self.daily_sensible_heat_kj,
            "latent_heat_kj": self.daily_latent_heat_kj,
            "water_vapor_kg": self.daily_water_vapor_kg,
            "potable_water_kg": self.daily_potable_water_kg,
            "food_kg": self.daily_food_kg,
            "food_water_kg": self.daily_food_water_kg,
            "metabolic_water_kg": self.daily_metabolic_water_kg,
            "urine_kg": self.daily_urine_kg,
            "fecal_water_kg": self.daily_fecal_water_kg,
            "sweat_kg": self.daily_sweat_kg,
            "fecal_solids_kg": self.daily_fecal_solids_kg,
            "urine_solids_kg": self.daily_urine_solids_kg,
            "perspiration_solids_kg": self.daily_perspiration_solids_kg,
        }

    def __repr__(self) -> str:
        return (f"CrewMember({self.name!r}, {self.sex}, {self.mass_kg}kg, "
                f"BMR={self.bmr_scale:.3f}, O2={self.daily_o2_kg:.3f} kg/d)")

