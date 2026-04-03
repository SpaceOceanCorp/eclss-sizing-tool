"""Mass balance validation against BVAD Figure 3-4.

Figure 3-4 shows the complete daily mass balance for an 82 kg astronaut:
  IN:  0.895 O2 + 0.800 food solids + 0.760 food liquids + 3.217 water = 5.672 kg
  OUT: 1.085 CO2 + 0.032 fecal solids + 0.027 persp solids + 0.061 urine solids
       + 0.101 fecal water + 2.946 resp/persp water + 1.420 urine water = 5.672 kg
  Internal: +0.487 kg metabolic water from food oxidation
"""

import pytest
from eclss.constants import (
    O2_CONSUMPTION_KG_PER_CM_DAY,
    FOOD_DRY_MASS_KG_PER_CM_DAY,
    FOOD_WATER_KG_PER_CM_DAY,
    POTABLE_WATER_KG_PER_CM_DAY,
    CO2_PRODUCTION_KG_PER_CM_DAY,
    FECAL_SOLIDS_KG_PER_CM_DAY,
    PERSPIRATION_SOLIDS_KG_PER_CM_DAY,
    URINE_SOLIDS_KG_PER_CM_DAY,
    FECAL_OUTPUT_KG_PER_CM_DAY,
    RESP_PERSPIRATION_WATER_KG_PER_CM_DAY,
    URINE_OUTPUT_KG_PER_CM_DAY,
    WATER_VAPOR_OUTPUT_KG_PER_CM_DAY,
    METABOLIC_WATER_KG_PER_CM_DAY,
)
from eclss.crew import CrewMember
from eclss.constants import REFERENCE_CM_AGE, REFERENCE_CM_MASS_KG, REFERENCE_CM_HEIGHT_M


class TestFigure34MassBalance:
    def test_total_mass_in(self):
        mass_in = (O2_CONSUMPTION_KG_PER_CM_DAY
                   + FOOD_DRY_MASS_KG_PER_CM_DAY
                   + FOOD_WATER_KG_PER_CM_DAY
                   + POTABLE_WATER_KG_PER_CM_DAY)
        assert mass_in == pytest.approx(5.672, rel=0.01)

    def test_total_mass_out(self):
        mass_out = (CO2_PRODUCTION_KG_PER_CM_DAY
                    + FECAL_SOLIDS_KG_PER_CM_DAY
                    + PERSPIRATION_SOLIDS_KG_PER_CM_DAY
                    + URINE_SOLIDS_KG_PER_CM_DAY
                    + FECAL_OUTPUT_KG_PER_CM_DAY
                    + RESP_PERSPIRATION_WATER_KG_PER_CM_DAY
                    + URINE_OUTPUT_KG_PER_CM_DAY)
        assert mass_out == pytest.approx(5.672, rel=0.01)

    def test_mass_balance_closes(self):
        mass_in = (O2_CONSUMPTION_KG_PER_CM_DAY
                   + FOOD_DRY_MASS_KG_PER_CM_DAY
                   + FOOD_WATER_KG_PER_CM_DAY
                   + POTABLE_WATER_KG_PER_CM_DAY)
        mass_out = (CO2_PRODUCTION_KG_PER_CM_DAY
                    + FECAL_SOLIDS_KG_PER_CM_DAY
                    + PERSPIRATION_SOLIDS_KG_PER_CM_DAY
                    + URINE_SOLIDS_KG_PER_CM_DAY
                    + FECAL_OUTPUT_KG_PER_CM_DAY
                    + RESP_PERSPIRATION_WATER_KG_PER_CM_DAY
                    + URINE_OUTPUT_KG_PER_CM_DAY)
        assert mass_in == pytest.approx(mass_out, rel=0.01)

    def test_metabolic_water_explains_surplus(self):
        """Water output exceeds water input by the metabolic water amount."""
        water_in = POTABLE_WATER_KG_PER_CM_DAY + FOOD_WATER_KG_PER_CM_DAY
        water_out = (URINE_OUTPUT_KG_PER_CM_DAY
                     + FECAL_OUTPUT_KG_PER_CM_DAY
                     + RESP_PERSPIRATION_WATER_KG_PER_CM_DAY)
        surplus = water_out - water_in
        assert surplus == pytest.approx(METABOLIC_WATER_KG_PER_CM_DAY, rel=0.05)


class TestWaterVaporDiscrepancy:
    def test_figure_34_vapor_greater_than_table_323(self):
        """Figure 3-4 (2.946) is more complete than Table 3-23 (2.27).

        The difference (~0.68 kg) is sweat runoff that Table 3-23 counts
        under wet heat rather than water vapor output.
        """
        assert RESP_PERSPIRATION_WATER_KG_PER_CM_DAY > WATER_VAPOR_OUTPUT_KG_PER_CM_DAY
        diff = RESP_PERSPIRATION_WATER_KG_PER_CM_DAY - WATER_VAPOR_OUTPUT_KG_PER_CM_DAY
        assert diff == pytest.approx(0.676, rel=0.05)


class TestCrewMemberWasteProperties:
    def test_reference_cm_waste_solids(self):
        cm = CrewMember("Ref", REFERENCE_CM_AGE, REFERENCE_CM_MASS_KG,
                        REFERENCE_CM_HEIGHT_M, "male")
        assert cm.daily_fecal_solids_kg == pytest.approx(FECAL_SOLIDS_KG_PER_CM_DAY, rel=1e-6)
        assert cm.daily_urine_solids_kg == pytest.approx(URINE_SOLIDS_KG_PER_CM_DAY, rel=1e-6)
        assert cm.daily_perspiration_solids_kg == pytest.approx(PERSPIRATION_SOLIDS_KG_PER_CM_DAY, rel=1e-6)

    def test_total_fecal_mass(self):
        cm = CrewMember("Ref", REFERENCE_CM_AGE, REFERENCE_CM_MASS_KG,
                        REFERENCE_CM_HEIGHT_M, "male")
        expected = FECAL_SOLIDS_KG_PER_CM_DAY + FECAL_OUTPUT_KG_PER_CM_DAY
        assert cm.daily_total_fecal_kg == pytest.approx(expected, rel=1e-6)

    def test_total_urine_mass(self):
        cm = CrewMember("Ref", REFERENCE_CM_AGE, REFERENCE_CM_MASS_KG,
                        REFERENCE_CM_HEIGHT_M, "male")
        expected = URINE_SOLIDS_KG_PER_CM_DAY + URINE_OUTPUT_KG_PER_CM_DAY
        assert cm.daily_total_urine_kg == pytest.approx(expected, rel=1e-6)

    def test_total_waste_solids(self):
        cm = CrewMember("Ref", REFERENCE_CM_AGE, REFERENCE_CM_MASS_KG,
                        REFERENCE_CM_HEIGHT_M, "male")
        expected = (FECAL_SOLIDS_KG_PER_CM_DAY + URINE_SOLIDS_KG_PER_CM_DAY
                    + PERSPIRATION_SOLIDS_KG_PER_CM_DAY)
        assert cm.daily_total_waste_solids_kg == pytest.approx(expected, rel=1e-6)
