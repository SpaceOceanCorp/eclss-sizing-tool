"""Tests for CrewMember model and BMR scaling (BVAD Eq 3-2, 3-3, 3-4)."""

import pytest
from eclss.crew import CrewMember, metabolic_rate_from_respiratory, _bmr_male, _bmr_female
from eclss.constants import (
    O2_CONSUMPTION_KG_PER_CM_DAY,
    CO2_PRODUCTION_KG_PER_CM_DAY,
    REFERENCE_CM_AGE,
    REFERENCE_CM_MASS_KG,
    REFERENCE_CM_HEIGHT_M,
)


# --- BMR Equations ---


class TestBMREquations:
    def test_bmr_male_reference(self):
        """Eq 3-2: hand calculation for 82 kg, 1.77 m, 40-yr male."""
        expected = (622 - 9.53 * 40 + 1.25 * (15.9 * 82 + 539.6 * 1.77)) / 239.006
        result = _bmr_male(40, 82.0, 1.77)
        assert result == pytest.approx(expected, rel=1e-6)

    def test_bmr_female(self):
        """Eq 3-3: hand calculation for 60 kg, 1.65 m, 28-yr female."""
        expected = (354 - 6.91 * 28 + 1.25 * (9.36 * 60 + 726 * 1.65)) / 239.006
        result = _bmr_female(28, 60.0, 1.65)
        assert result == pytest.approx(expected, rel=1e-6)

    def test_bmr_male_positive(self):
        """BMR should be positive for any reasonable human."""
        assert _bmr_male(25, 70, 1.75) > 0

    def test_bmr_female_positive(self):
        assert _bmr_female(25, 55, 1.60) > 0

    def test_bmr_increases_with_mass(self):
        """Heavier person should have higher BMR."""
        light = _bmr_male(30, 60, 1.75)
        heavy = _bmr_male(30, 100, 1.75)
        assert heavy > light

    def test_bmr_decreases_with_age(self):
        """Older person should have lower BMR (negative age coefficient)."""
        young = _bmr_male(25, 80, 1.80)
        old = _bmr_male(55, 80, 1.80)
        assert young > old


# --- Eq 3-4: Respiratory Gas Exchange ---


class TestEquation34:
    def test_metabolic_rate_from_respiratory_positive(self):
        """Should return positive MJ/day for any positive gas exchange."""
        mr = metabolic_rate_from_respiratory(0.59, 0.69)
        assert mr > 0

    def test_nominal_activity_reasonable_range(self):
        """Nominal activity (Table 3-24: O2=0.59 g/min, CO2=0.69 g/min).

        Convert g/min to L/min: O2 density ~1.429 g/L, CO2 ~1.977 g/L.
        Result should be in reasonable MJ/day range.
        """
        vo2_lpm = 0.59 / 1.429
        vco2_lpm = 0.69 / 1.977
        mr = metabolic_rate_from_respiratory(vo2_lpm, vco2_lpm)
        assert 0.1 < mr < 20.0  # reasonable daily range


# --- CrewMember Validation ---


class TestCrewMemberValidation:
    def test_invalid_sex_raises(self):
        with pytest.raises(ValueError, match="sex"):
            CrewMember("X", 30, 70, 1.75, sex="other")

    def test_negative_mass_raises(self):
        with pytest.raises(ValueError, match="mass_kg"):
            CrewMember("X", 30, -70, 1.75, "male")

    def test_zero_height_raises(self):
        with pytest.raises(ValueError, match="height_m"):
            CrewMember("X", 30, 70, 0, "male")

    def test_negative_age_raises(self):
        with pytest.raises(ValueError, match="age"):
            CrewMember("X", -5, 70, 1.75, "male")


# --- CrewMember Scaling ---


class TestCrewMemberScaling:
    def test_reference_cm_bmr_scale_is_1(self):
        """Reference CM should have a BMR scale of exactly 1.0."""
        cm = CrewMember("Ref", REFERENCE_CM_AGE, REFERENCE_CM_MASS_KG,
                        REFERENCE_CM_HEIGHT_M, "male")
        assert cm._bmr_scale == pytest.approx(1.0, rel=1e-6)

    def test_reference_cm_o2_matches_constant(self):
        """Reference CM's scaled O2 should match the BVAD constant exactly."""
        cm = CrewMember("Ref", REFERENCE_CM_AGE, REFERENCE_CM_MASS_KG,
                        REFERENCE_CM_HEIGHT_M, "male")
        assert cm.daily_o2_kg == pytest.approx(O2_CONSUMPTION_KG_PER_CM_DAY, rel=1e-6)

    def test_reference_cm_co2_matches_constant(self):
        cm = CrewMember("Ref", REFERENCE_CM_AGE, REFERENCE_CM_MASS_KG,
                        REFERENCE_CM_HEIGHT_M, "male")
        assert cm.daily_co2_kg == pytest.approx(CO2_PRODUCTION_KG_PER_CM_DAY, rel=1e-6)

    def test_smaller_crew_lower_o2(self):
        ref = CrewMember("Ref", 40, 82.0, 1.77, "male")
        small = CrewMember("Small", 40, 55.0, 1.60, "female")
        assert small.daily_o2_kg < ref.daily_o2_kg

    def test_larger_crew_higher_o2(self):
        ref = CrewMember("Ref", 40, 82.0, 1.77, "male")
        large = CrewMember("Large", 35, 100.0, 1.90, "male")
        assert large.daily_o2_kg > ref.daily_o2_kg

    def test_all_scaled_rates_positive(self):
        """All daily rates should be positive for any valid crew member."""
        cm = CrewMember("Test", 25, 65, 1.70, "female")
        assert cm.daily_o2_kg > 0
        assert cm.daily_co2_kg > 0
        assert cm.daily_metabolic_rate_kj > 0
        assert cm.daily_sensible_heat_kj > 0
        assert cm.daily_latent_heat_kj > 0
        assert cm.daily_water_vapor_kg > 0
        assert cm.daily_potable_water_kg > 0
        assert cm.daily_food_kg > 0
        assert cm.daily_urine_kg > 0
        assert cm.daily_fecal_water_kg > 0

    def test_bmr_scale_proportional(self):
        """If BMR is 1.2x reference, all rates should be 1.2x."""
        cm = CrewMember("Test", 30, 90, 1.85, "male")
        scale = cm._bmr_scale
        assert cm.daily_o2_kg == pytest.approx(
            O2_CONSUMPTION_KG_PER_CM_DAY * scale, rel=1e-6
        )
