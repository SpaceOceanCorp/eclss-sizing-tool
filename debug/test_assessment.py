"""Tests for SystemAssessment and MinimumRequirements."""

import pytest
from eclss import Habitat, EclssSystem
from eclss.crew import CrewMember
from eclss.simulation import Simulation
from eclss.assessment import MinimumRequirements, assess_system


class TestMinimumRequirements:
    def test_from_simulation_positive(self):
        hab = Habitat(CrewMember.reference_crew(4), 25, 7)
        ts = Simulation(hab).run()
        reqs = MinimumRequirements.from_simulation(ts)
        assert reqs.peak_o2_generation_kg_hr > 0
        assert reqs.peak_co2_removal_kg_hr > 0
        assert reqs.peak_heat_rejection_w > 0

    def test_with_margin_scales(self):
        hab = Habitat(CrewMember.reference_crew(4), 25, 1)
        ts = Simulation(hab).run()
        reqs = MinimumRequirements.from_simulation(ts)
        margined = reqs.with_margin(1.5)
        assert margined.peak_o2_generation_kg_hr == pytest.approx(
            reqs.peak_o2_generation_kg_hr * 1.5
        )
        assert margined.peak_co2_removal_kg_hr == pytest.approx(
            reqs.peak_co2_removal_kg_hr * 1.5
        )
        assert margined.peak_heat_rejection_w == pytest.approx(
            reqs.peak_heat_rejection_w * 1.5
        )

    def test_default_margin_1_2(self):
        hab = Habitat(CrewMember.reference_crew(4), 25, 1)
        ts = Simulation(hab).run()
        reqs = MinimumRequirements.from_simulation(ts)
        margined = reqs.with_margin()
        assert margined.peak_o2_generation_kg_hr == pytest.approx(
            reqs.peak_o2_generation_kg_hr * 1.2
        )


class TestAssessSystem:
    def test_adequate_system_passes(self):
        hab = Habitat(CrewMember.reference_crew(4), 25, 7)
        ts = Simulation(hab).run()  # unlimited ECLSS
        assessment = assess_system(ts)
        assert assessment.overall_pass is True
        assert len(assessment.violations) == 0

    def test_undersized_co2_fails(self):
        hab = Habitat(CrewMember.reference_crew(4), 25, 7)
        sys = EclssSystem(co2_removal_capacity_kg_hr=0.01)
        ts = Simulation(hab, system=sys).run()
        assessment = assess_system(ts)
        assert assessment.overall_pass is False
        assert any(v.subsystem == "co2" for v in assessment.violations)

    def test_violation_has_details(self):
        hab = Habitat(CrewMember.reference_crew(4), 25, 1)
        sys = EclssSystem(co2_removal_capacity_kg_hr=0.01)
        ts = Simulation(hab, system=sys).run()
        assessment = assess_system(ts)
        v = assessment.violations[0]
        assert isinstance(v.start_hour, float)
        assert isinstance(v.end_hour, float)
        assert v.end_hour >= v.start_hour
        assert isinstance(v.peak_value_kpa, float)
        assert isinstance(v.limit_kpa, float)
        assert v.duration_hours > 0
        assert len(v.description) > 0

    def test_violations_aggregated_into_windows(self):
        """Long violation should be a single window, not per-timestep."""
        hab = Habitat(CrewMember.reference_crew(4), 25, 7)
        sys = EclssSystem(co2_removal_capacity_kg_hr=0.01)
        ts = Simulation(hab, system=sys).run()
        assessment = assess_system(ts)
        # Should have far fewer violations than timesteps
        co2_violations = [v for v in assessment.violations if v.subsystem == "co2"]
        assert len(co2_violations) < 168  # less than total steps
        # Total duration should be substantial
        total_hours = sum(v.duration_hours for v in co2_violations)
        assert total_hours > 0

    def test_repr_pass(self):
        hab = Habitat(CrewMember.reference_crew(4), 25, 1)
        ts = Simulation(hab).run()
        assessment = assess_system(ts)
        assert "PASS" in repr(assessment)

    def test_repr_fail(self):
        hab = Habitat(CrewMember.reference_crew(4), 25, 1)
        sys = EclssSystem(co2_removal_capacity_kg_hr=0.01)
        ts = Simulation(hab, system=sys).run()
        assessment = assess_system(ts)
        assert "FAIL" in repr(assessment)
