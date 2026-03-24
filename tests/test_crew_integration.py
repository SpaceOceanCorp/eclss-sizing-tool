"""Tests for CrewMember integration with Habitat."""

import pytest
from eclss import Habitat
from eclss.crew import CrewMember
from eclss.constants import (
    REFERENCE_CM_AGE,
    REFERENCE_CM_MASS_KG,
    REFERENCE_CM_HEIGHT_M,
)


def _ref_cm(name: str = "Ref") -> CrewMember:
    """Create a reference crewmember matching BVAD 82 kg baseline."""
    return CrewMember(name, REFERENCE_CM_AGE, REFERENCE_CM_MASS_KG,
                      REFERENCE_CM_HEIGHT_M, "male")


class TestHabitatCrewIntegration:
    def test_crew_list_matches_crew_count(self):
        """4 reference CMs should produce identical results to crew_count=4."""
        crew = [_ref_cm(f"CM-{i}") for i in range(4)]
        result_crew = Habitat(crew=crew, cabin_volume_m3=25,
                              mission_duration_days=180).calculate()
        result_old = Habitat(crew_count=4, cabin_volume_m3=25,
                             mission_duration_days=180).calculate()
        assert result_crew.total_o2_kg == pytest.approx(result_old.total_o2_kg, rel=1e-6)
        assert result_crew.total_water_kg == pytest.approx(result_old.total_water_kg, rel=1e-6)
        assert result_crew.crew_metabolic_heat_w == pytest.approx(
            result_old.crew_metabolic_heat_w, rel=1e-6
        )

    def test_crew_count_mismatch_raises(self):
        """Passing both crew and a different crew_count should raise."""
        crew = [_ref_cm(), _ref_cm()]
        with pytest.raises(ValueError, match="crew_count"):
            Habitat(crew=crew, crew_count=4, cabin_volume_m3=25,
                    mission_duration_days=180)

    def test_crew_count_match_ok(self):
        """Passing matching crew_count and crew should work."""
        crew = [_ref_cm(), _ref_cm()]
        hab = Habitat(crew=crew, crew_count=2, cabin_volume_m3=25,
                      mission_duration_days=180)
        assert hab.crew_count == 2

    def test_mixed_crew_different_results(self):
        """Heterogeneous crew should produce different totals than homogeneous."""
        big = CrewMember("Big", 35, 95.0, 1.90, "male")
        small = CrewMember("Small", 28, 55.0, 1.60, "female")

        result_mixed = Habitat(crew=[big, small], cabin_volume_m3=25,
                               mission_duration_days=180).calculate()
        result_ref = Habitat(crew_count=2, cabin_volume_m3=25,
                             mission_duration_days=180).calculate()

        # Mixed crew should have different O2 total (not exactly 2x reference)
        assert result_mixed.crew_count == 2
        assert result_mixed.total_o2_kg != pytest.approx(result_ref.total_o2_kg, rel=0.01)

    def test_crew_stored_on_habitat(self):
        """Habitat should store the crew list for downstream use."""
        crew = [_ref_cm("A"), _ref_cm("B")]
        hab = Habitat(crew=crew, cabin_volume_m3=25, mission_duration_days=180)
        assert hab.crew is not None
        assert len(hab.crew) == 2
        assert hab.crew[0].name == "A"

    def test_no_crew_no_count_raises(self):
        """Must provide either crew or crew_count."""
        with pytest.raises(ValueError, match="Must provide"):
            Habitat(cabin_volume_m3=25, mission_duration_days=180)

    def test_empty_crew_list_raises(self):
        """Empty crew list should raise, not crash with ZeroDivisionError."""
        with pytest.raises(ValueError, match="must not be empty"):
            Habitat(crew=[], cabin_volume_m3=25, mission_duration_days=180)

    def test_closed_loop_with_crew(self):
        """Crew list should work with closed-loop mode."""
        crew = [CrewMember("A", 30, 75, 1.80, "male"),
                CrewMember("B", 28, 60, 1.65, "female")]
        result = Habitat(crew=crew, cabin_volume_m3=25,
                         mission_duration_days=180, loop_mode="closed").calculate()
        assert result.loop_mode == "closed"
        assert result.o2_from_co2_recovery_kg > 0
