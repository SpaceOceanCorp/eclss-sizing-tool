"""Tests for Habitat ECLSS sizing calculations.

Hand-computed reference values based on BVAD constants for a
4-crew, 25 m³, 180-day scenario.
"""

import pytest
from eclss import Habitat
from eclss.crew import CrewMember
from eclss.constants import (
    O2_CONSUMPTION_KG_PER_CM_DAY,
    CO2_PRODUCTION_KG_PER_CM_DAY,
    METABOLIC_HEAT_SENSIBLE_KJ_PER_CM_DAY,
    METABOLIC_HEAT_LATENT_KJ_PER_CM_DAY,
    POTABLE_WATER_KG_PER_CM_DAY,
    URINE_OUTPUT_KG_PER_CM_DAY,
    FECAL_OUTPUT_KG_PER_CM_DAY,
    WATER_VAPOR_OUTPUT_KG_PER_CM_DAY,
    FOOD_WATER_KG_PER_CM_DAY,
    METABOLIC_WATER_KG_PER_CM_DAY,
    FOOD_DRY_MASS_KG_PER_CM_DAY,
    CABIN_LEAKAGE_RATE_KG_PER_MODULE_DAY,
    CABIN_PRESSURE_NOMINAL_KPA,
    O2_PP_TARGET_KPA,
    EQUIPMENT_HEAT_W_PER_CREW,
    WATER_RECOVERY_EFFICIENCY,
)

CREW = 4
VOLUME = 25.0
DAYS = 180
KJ_DAY_TO_W = 1000.0 / 86400.0
SABATIER_O2_RATIO = 32.0 / 44.0
SABATIER_WATER_RATIO = 36.0 / 44.0


@pytest.fixture
def open_result():
    return Habitat(CrewMember.reference_crew(CREW), VOLUME, DAYS, loop_mode="open").calculate()


@pytest.fixture
def closed_result():
    return Habitat(CrewMember.reference_crew(CREW), VOLUME, DAYS, loop_mode="closed").calculate()


# --- Input validation ---


class TestValidation:
    def test_invalid_loop_mode(self):
        with pytest.raises(ValueError, match="loop_mode"):
            Habitat(CrewMember.reference_crew(4), 25.0, 180, loop_mode="hybrid")

    def test_zero_crew(self):
        with pytest.raises(ValueError, match="crew must not be empty"):
            Habitat([], 25, 180)

    def test_negative_volume(self):
        with pytest.raises(ValueError, match="cabin_volume_m3"):
            Habitat(CrewMember.reference_crew(4), -10.0, 180)

    def test_zero_duration(self):
        with pytest.raises(ValueError, match="mission_duration_days"):
            Habitat(CrewMember.reference_crew(4), 25.0, 0)


# --- Atmosphere ---


class TestAtmosphere:
    def test_o2_generation_rate(self, open_result):
        o2_fraction = O2_PP_TARGET_KPA / CABIN_PRESSURE_NOMINAL_KPA
        expected = (O2_CONSUMPTION_KG_PER_CM_DAY * CREW) + (
            CABIN_LEAKAGE_RATE_KG_PER_MODULE_DAY * o2_fraction
        )
        assert open_result.o2_generation_rate_kg_day == pytest.approx(expected)

    def test_co2_removal_rate(self, open_result):
        expected = CO2_PRODUCTION_KG_PER_CM_DAY * CREW
        assert open_result.co2_removal_rate_kg_day == pytest.approx(expected)

    def test_leakage_echoed(self, open_result):
        assert open_result.cabin_leakage_rate_kg_day == pytest.approx(
            CABIN_LEAKAGE_RATE_KG_PER_MODULE_DAY
        )


# --- Thermal ---


class TestThermal:
    def test_crew_metabolic_heat(self, open_result):
        sensible_w = METABOLIC_HEAT_SENSIBLE_KJ_PER_CM_DAY * KJ_DAY_TO_W * CREW
        latent_w = METABOLIC_HEAT_LATENT_KJ_PER_CM_DAY * KJ_DAY_TO_W * CREW
        assert open_result.crew_metabolic_heat_w == pytest.approx(
            sensible_w + latent_w
        )

    def test_equipment_heat(self, open_result):
        assert open_result.equipment_heat_w == pytest.approx(
            EQUIPMENT_HEAT_W_PER_CREW * CREW
        )

    def test_total_heat(self, open_result):
        assert open_result.total_heat_rejection_w == pytest.approx(
            open_result.crew_metabolic_heat_w + open_result.equipment_heat_w
        )


# --- Water ---


class TestWater:
    def test_open_loop_resupply_equals_consumption(self, open_result):
        assert open_result.water_resupply_kg_day == pytest.approx(
            open_result.water_consumption_kg_day
        )

    def test_open_loop_no_recovery(self, open_result):
        assert open_result.water_recovery_efficiency_required == 0.0

    def test_closed_loop_reduces_resupply(self, closed_result):
        open_consumption = (POTABLE_WATER_KG_PER_CM_DAY + FOOD_WATER_KG_PER_CM_DAY) * CREW
        assert closed_result.water_resupply_kg_day < open_consumption

    def test_water_consumption(self, open_result):
        expected = (POTABLE_WATER_KG_PER_CM_DAY + FOOD_WATER_KG_PER_CM_DAY) * CREW
        assert open_result.water_consumption_kg_day == pytest.approx(expected)

    def test_water_production(self, open_result):
        expected = (URINE_OUTPUT_KG_PER_CM_DAY + FECAL_OUTPUT_KG_PER_CM_DAY
                    + WATER_VAPOR_OUTPUT_KG_PER_CM_DAY
                    + METABOLIC_WATER_KG_PER_CM_DAY) * CREW
        assert open_result.water_production_kg_day == pytest.approx(expected)


# --- Consumables ---


class TestConsumables:
    def test_open_loop_o2_total(self, open_result):
        expected = O2_CONSUMPTION_KG_PER_CM_DAY * CREW * DAYS
        assert open_result.total_o2_kg == pytest.approx(expected)

    def test_open_loop_food_total(self, open_result):
        expected = FOOD_DRY_MASS_KG_PER_CM_DAY * CREW * DAYS
        assert open_result.total_food_kg == pytest.approx(expected)

    def test_open_loop_no_recovery(self, open_result):
        assert open_result.o2_from_co2_recovery_kg == 0.0
        assert open_result.water_recovered_kg == 0.0

    def test_closed_loop_sabatier_recovery(self, closed_result):
        daily_co2 = CO2_PRODUCTION_KG_PER_CM_DAY * CREW
        daily_o2_recovered = daily_co2 * SABATIER_O2_RATIO
        assert closed_result.o2_from_co2_recovery_kg == pytest.approx(
            daily_o2_recovered * DAYS
        )

    def test_closed_loop_less_o2_needed(self, open_result, closed_result):
        assert closed_result.total_o2_kg < open_result.total_o2_kg

    def test_closed_loop_water_recovered(self, closed_result):
        """Water recovered = crew output recovery + Sabatier water."""
        daily_production = (
            URINE_OUTPUT_KG_PER_CM_DAY + FECAL_OUTPUT_KG_PER_CM_DAY
            + WATER_VAPOR_OUTPUT_KG_PER_CM_DAY + METABOLIC_WATER_KG_PER_CM_DAY
        ) * CREW
        daily_sabatier_water = CO2_PRODUCTION_KG_PER_CM_DAY * CREW * SABATIER_WATER_RATIO
        expected = (daily_production * WATER_RECOVERY_EFFICIENCY
                    + daily_sabatier_water) * DAYS
        assert closed_result.water_recovered_kg == pytest.approx(expected)

    def test_water_resupply_consistent_with_total(self, closed_result):
        """water_resupply_kg_day * days == total_water_kg (no double-accounting)."""
        assert closed_result.water_resupply_kg_day * DAYS == pytest.approx(
            closed_result.total_water_kg
        )

    def test_sabatier_water_open_loop_zero(self, open_result):
        assert open_result.sabatier_water_kg_day == 0.0

    def test_sabatier_water_closed_loop(self, closed_result):
        expected = CO2_PRODUCTION_KG_PER_CM_DAY * CREW * SABATIER_WATER_RATIO
        assert closed_result.sabatier_water_kg_day == pytest.approx(expected)


# --- Result formatting ---


class TestResult:
    def test_repr_contains_sections(self, open_result):
        text = repr(open_result)
        assert "ATMOSPHERE" in text
        assert "THERMAL" in text
        assert "WATER" in text
        assert "CONSUMABLES" in text

    def test_closed_loop_repr_shows_recovery(self, closed_result):
        text = repr(closed_result)
        assert "Sabatier" in text
        assert "recovery" in text.lower()

    def test_inputs_echoed(self, open_result):
        assert open_result.crew_count == CREW
        assert open_result.cabin_volume_m3 == VOLUME
        assert open_result.mission_duration_days == DAYS
        assert open_result.loop_mode == "open"


# --- LoopMode enum ---


class TestLoopMode:
    def test_enum_open_accepted(self):
        from eclss.habitat import LoopMode
        h = Habitat(CrewMember.reference_crew(4), 25.0, 180, loop_mode=LoopMode.OPEN)
        assert h.loop_mode == "open"

    def test_enum_closed_accepted(self):
        from eclss.habitat import LoopMode
        h = Habitat(CrewMember.reference_crew(4), 25.0, 180, loop_mode=LoopMode.CLOSED)
        assert h.loop_mode == "closed"

    def test_string_still_works(self):
        h = Habitat(CrewMember.reference_crew(4), 25.0, 180, loop_mode="open")
        assert h.loop_mode == "open"

    def test_stored_as_plain_string(self):
        from eclss.habitat import LoopMode
        h = Habitat(CrewMember.reference_crew(4), 25.0, 180, loop_mode=LoopMode.CLOSED)
        assert type(h.loop_mode) is str

    def test_invalid_enum_value_rejected(self):
        with pytest.raises(ValueError, match="loop_mode"):
            Habitat(CrewMember.reference_crew(4), 25.0, 180, loop_mode="hybrid")

    def test_enum_equality(self):
        from eclss.habitat import LoopMode
        assert LoopMode.OPEN == "open"
        assert LoopMode.CLOSED == "closed"

    def test_loop_mode_exported(self):
        from eclss import LoopMode
        assert LoopMode.OPEN.value == "open"


# --- Sabatier efficiency ---


class TestSabatierEfficiency:
    def test_default_efficiency_is_one(self):
        h = Habitat(CrewMember.reference_crew(4), 25.0, 180, loop_mode="closed")
        assert h.sabatier_efficiency == 1.0

    def test_custom_efficiency_stored(self):
        h = Habitat(CrewMember.reference_crew(4), 25.0, 180,
                     loop_mode="closed", sabatier_efficiency=0.75)
        assert h.sabatier_efficiency == 0.75

    def test_half_efficiency_halves_recovery(self):
        full = Habitat(CrewMember.reference_crew(CREW), VOLUME, DAYS,
                       loop_mode="closed", sabatier_efficiency=1.0).calculate()
        half = Habitat(CrewMember.reference_crew(CREW), VOLUME, DAYS,
                       loop_mode="closed", sabatier_efficiency=0.5).calculate()
        assert half.o2_from_co2_recovery_kg == pytest.approx(
            full.o2_from_co2_recovery_kg * 0.5
        )

    def test_half_efficiency_halves_sabatier_water(self):
        full = Habitat(CrewMember.reference_crew(CREW), VOLUME, DAYS,
                       loop_mode="closed", sabatier_efficiency=1.0).calculate()
        half = Habitat(CrewMember.reference_crew(CREW), VOLUME, DAYS,
                       loop_mode="closed", sabatier_efficiency=0.5).calculate()
        assert half.sabatier_water_kg_day == pytest.approx(
            full.sabatier_water_kg_day * 0.5
        )

    def test_zero_efficiency_no_recovery(self):
        r = Habitat(CrewMember.reference_crew(CREW), VOLUME, DAYS,
                    loop_mode="closed", sabatier_efficiency=0.0).calculate()
        assert r.o2_from_co2_recovery_kg == 0.0
        assert r.sabatier_water_kg_day == 0.0

    def test_open_loop_ignores_efficiency(self):
        """Sabatier efficiency should have no effect in open-loop mode."""
        r1 = Habitat(CrewMember.reference_crew(CREW), VOLUME, DAYS,
                     loop_mode="open", sabatier_efficiency=0.5).calculate()
        r2 = Habitat(CrewMember.reference_crew(CREW), VOLUME, DAYS,
                     loop_mode="open", sabatier_efficiency=1.0).calculate()
        assert r1.total_o2_kg == pytest.approx(r2.total_o2_kg)
        assert r1.sabatier_water_kg_day == r2.sabatier_water_kg_day == 0.0

    def test_efficiency_changes_total_o2(self):
        """Lower Sabatier efficiency means more O2 must be supplied."""
        full = Habitat(CrewMember.reference_crew(CREW), VOLUME, DAYS,
                       loop_mode="closed", sabatier_efficiency=1.0).calculate()
        half = Habitat(CrewMember.reference_crew(CREW), VOLUME, DAYS,
                       loop_mode="closed", sabatier_efficiency=0.5).calculate()
        assert half.total_o2_kg > full.total_o2_kg

    def test_efficiency_changes_water_resupply(self):
        """Lower Sabatier efficiency means more water resupply needed."""
        full = Habitat(CrewMember.reference_crew(CREW), VOLUME, DAYS,
                       loop_mode="closed", sabatier_efficiency=1.0).calculate()
        half = Habitat(CrewMember.reference_crew(CREW), VOLUME, DAYS,
                       loop_mode="closed", sabatier_efficiency=0.5).calculate()
        assert half.water_resupply_kg_day >= full.water_resupply_kg_day
