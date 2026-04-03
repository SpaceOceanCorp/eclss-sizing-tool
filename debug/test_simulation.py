"""Tests for the time-stepped ECLSS simulation engine."""

import numpy as np
import pytest
from eclss import Habitat, CrewMember, EclssSystem, REFERENCE_SCHEDULE
from eclss.simulation import Simulation
from eclss.schedule import ConstantSchedule, DailySchedule, ActivityBlock
from eclss.activity import ActivityLevel
from eclss.constants import (
    O2_CONSUMPTION_KG_PER_CM_DAY,
    CO2_PRODUCTION_KG_PER_CM_DAY,
    O2_PP_SAFE_RANGE_KPA,
    CO2_PP_SAFE_RANGE_KPA,
    O2_PP_TARGET_KPA,
    CO2_PP_DESIGN_TARGET_KPA,
)


# --- Constructor + Initial Conditions ---


class TestSimulationConstructor:
    def test_default_system(self):
        hab = Habitat(CrewMember.reference_crew(4), 25, 1)
        sim = Simulation(hab)
        assert sim.system.o2_generation_capacity_kg_hr is None

    def test_synthetic_crew_when_no_crew_list(self):
        hab = Habitat(CrewMember.reference_crew(4), 25, 1)
        sim = Simulation(hab)
        assert len(sim.crew) == 4
        assert sim.crew[0].name == "CM-1"

    def test_real_crew_used(self):
        crew = [CrewMember("Alice", 30, 70, 1.70, "female")]
        hab = Habitat(crew, 25, 1)
        sim = Simulation(hab)
        assert sim.crew[0].name == "Alice"

    def test_initial_o2_mass_positive(self):
        hab = Habitat(CrewMember.reference_crew(4), 25, 1)
        sim = Simulation(hab)
        assert sim.initial_o2_kg > 0

    def test_initial_co2_mass_positive(self):
        hab = Habitat(CrewMember.reference_crew(4), 25, 1)
        sim = Simulation(hab)
        assert sim.initial_co2_kg > 0

    def test_n_steps_1_day(self):
        hab = Habitat(CrewMember.reference_crew(4), 25, 1)
        sim = Simulation(hab, timestep_hours=1.0)
        assert sim.n_steps == 24

    def test_n_steps_half_hour(self):
        hab = Habitat(CrewMember.reference_crew(4), 25, 1)
        sim = Simulation(hab, timestep_hours=0.5)
        assert sim.n_steps == 48

    def test_n_steps_7_days(self):
        hab = Habitat(CrewMember.reference_crew(4), 25, 7)
        sim = Simulation(hab)
        assert sim.n_steps == 168


# --- Schedule Precomputation ---


class TestSchedulePrecomputation:
    def test_rate_array_shape(self):
        hab = Habitat(CrewMember.reference_crew(4), 25, 1)
        sim = Simulation(hab)
        assert sim._crew_o2_rate.shape == (4, 24)
        assert sim._crew_co2_rate.shape == (4, 24)
        assert sim._crew_heat_rate.shape == (4, 24)

    def test_sleep_rate_lower_than_exercise(self):
        """At hour 1 (sleep), O2 rate should be lower than hour 13 (aerobic)."""
        hab = Habitat(CrewMember.reference_crew(1), 25, 1)
        sim = Simulation(hab)
        sleep_rate = sim._crew_o2_rate[0, 1]   # hour 1: sleep
        exercise_rate = sim._crew_o2_rate[0, 13]  # hour 13: aerobic exercise
        assert sleep_rate < exercise_rate

    def test_activity_names_recorded(self):
        hab = Habitat(CrewMember.reference_crew(1), 25, 1)
        sim = Simulation(hab)
        names = sim._crew_activity_names["CM-1"]
        assert len(names) == 24
        assert "Sleep" in names
        assert "Nominal" in names


# --- Basic Simulation Output ---


class TestSimulationBasic:
    def test_1_day_24_steps(self):
        """1-day sim with 1h timestep: 24 steps, 25 data points."""
        hab = Habitat(CrewMember.reference_crew(4), 25, 1)
        ts = Simulation(hab).run()
        assert ts.n_steps == 24
        assert ts.n_points == 25

    def test_half_hour_48_steps(self):
        """1-day sim with 0.5h timestep: 48 steps, 49 data points."""
        hab = Habitat(CrewMember.reference_crew(4), 25, 1)
        ts = Simulation(hab, timestep_hours=0.5).run()
        assert ts.n_steps == 48
        assert ts.n_points == 49

    def test_time_array_starts_at_zero(self):
        hab = Habitat(CrewMember.reference_crew(4), 25, 1)
        ts = Simulation(hab).run()
        assert ts.time_hours[0] == pytest.approx(0.0)
        assert ts.time_hours[-1] == pytest.approx(24.0)

    def test_duration_hours(self):
        hab = Habitat(CrewMember.reference_crew(4), 25, 1)
        ts = Simulation(hab).run()
        assert ts.duration_hours == pytest.approx(24.0)

    def test_safe_ranges_populated(self):
        hab = Habitat(CrewMember.reference_crew(4), 25, 1)
        ts = Simulation(hab).run()
        assert ts.o2_pp_safe_range_kpa == O2_PP_SAFE_RANGE_KPA
        assert ts.co2_pp_safe_range_kpa == CO2_PP_SAFE_RANGE_KPA

    def test_all_arrays_same_length(self):
        hab = Habitat(CrewMember.reference_crew(4), 25, 1)
        ts = Simulation(hab).run()
        n = ts.n_points
        assert len(ts.cabin_o2_mass_kg) == n
        assert len(ts.cabin_co2_mass_kg) == n
        assert len(ts.cabin_o2_pp_kpa) == n
        assert len(ts.cabin_co2_pp_kpa) == n
        assert len(ts.total_o2_demand_kg_hr) == n
        assert len(ts.total_co2_production_kg_hr) == n
        assert len(ts.total_heat_w) == n
        assert len(ts.heat_rejected_w) == n


# --- Mass Conservation ---


class TestMassConservation:
    def test_o2_consumption_7_day(self):
        """Total O2 consumed over 7 days should match Table 3-31 daily rate.

        Activity rates are normalized so weighted daily average matches
        Table 3-31. With the reference schedule, total should match closely.
        Index 0 has zero demand (initial conditions), so sum of [1:] is used.
        """
        hab = Habitat(CrewMember.reference_crew(4), 25, 7)
        ts = Simulation(hab).run()
        total_consumed = float(np.sum(ts.total_o2_demand_kg_hr[1:])) * ts.timestep_hours
        steady_state = O2_CONSUMPTION_KG_PER_CM_DAY * 4 * 7
        assert total_consumed == pytest.approx(steady_state, rel=0.01)

    def test_co2_production_7_day(self):
        hab = Habitat(CrewMember.reference_crew(4), 25, 7)
        ts = Simulation(hab).run()
        total_produced = float(np.sum(ts.total_co2_production_kg_hr[1:])) * ts.timestep_hours
        steady_state = CO2_PRODUCTION_KG_PER_CM_DAY * 4 * 7
        assert total_produced == pytest.approx(steady_state, rel=0.01)


# --- Partial Pressure ---


class TestPartialPressure:
    def test_o2_pp_stays_in_range(self):
        """With unlimited ECLSS, O2 pp should stay near nominal."""
        hab = Habitat(CrewMember.reference_crew(4), 25, 7)
        ts = Simulation(hab).run()
        assert all(pp > 15.0 for pp in ts.cabin_o2_pp_kpa)
        assert all(pp < 30.0 for pp in ts.cabin_o2_pp_kpa)

    def test_co2_pp_stays_low(self):
        """With unlimited ECLSS, CO2 pp should stay below SMAC."""
        hab = Habitat(CrewMember.reference_crew(4), 25, 7)
        ts = Simulation(hab).run()
        assert all(pp < 1.5 for pp in ts.cabin_co2_pp_kpa)

    def test_o2_pp_initial_exact_target(self):
        """B8: Index 0 should be exact initial O2 partial pressure."""
        hab = Habitat(CrewMember.reference_crew(4), 25, 1)
        ts = Simulation(hab).run()
        assert ts.cabin_o2_pp_kpa[0] == pytest.approx(O2_PP_TARGET_KPA, rel=1e-10)


# --- Undersized System ---


class TestUndersizedSystem:
    def test_undersized_co2_scrubber(self):
        """CO2 should accumulate when scrubber cannot keep up."""
        hab = Habitat(CrewMember.reference_crew(4), 25, 1)
        # Set CO2 removal to ~50% of demand
        sys = EclssSystem(co2_removal_capacity_kg_hr=0.01)
        ts = Simulation(hab, system=sys).run()
        # Index 0 is initial; final should have more CO2 than initial
        assert ts.cabin_co2_mass_kg[-1] > ts.cabin_co2_mass_kg[0]

    def test_undersized_o2_generator(self):
        """O2 should deplete when generator cannot keep up."""
        hab = Habitat(CrewMember.reference_crew(4), 25, 1)
        sys = EclssSystem(o2_generation_capacity_kg_hr=0.01)
        ts = Simulation(hab, system=sys).run()
        assert ts.cabin_o2_mass_kg[-1] < ts.cabin_o2_mass_kg[0]


# --- Crew Activity ---


class TestCrewActivity:
    def test_activity_names_in_result(self):
        hab = Habitat(CrewMember.reference_crew(2), 25, 1)
        ts = Simulation(hab).run()
        assert "CM-1" in ts.crew_activity
        assert "CM-2" in ts.crew_activity

    def test_activity_variation(self):
        """Reference schedule should produce multiple activity types."""
        hab = Habitat(CrewMember.reference_crew(1), 25, 1)
        ts = Simulation(hab).run()
        activities = set(ts.crew_activity["CM-1"])
        assert len(activities) >= 2  # at least Sleep and Nominal

    def test_per_crew_rates_in_result(self):
        hab = Habitat(CrewMember.reference_crew(2), 25, 1)
        ts = Simulation(hab).run()
        assert "CM-1" in ts.crew_o2_demand_kg_hr
        # Per-crew arrays are still n_steps (no initial condition entry)
        assert len(ts.crew_o2_demand_kg_hr["CM-1"]) == 24

    def test_custom_schedule(self):
        crew = [CrewMember("Alice", 30, 70, 1.70, "female")]
        hab = Habitat(crew, 25, 1)
        sched = ConstantSchedule(REFERENCE_SCHEDULE)
        ts = Simulation(hab, schedules={"Alice": sched}).run()
        assert "Alice" in ts.crew_activity


# --- B8: Initial Conditions at t=0 ---


class TestInitialConditions:
    def test_initial_conditions_recorded(self):
        """t=0 should have exact initial partial pressure values, no consumption."""
        hab = Habitat(CrewMember.reference_crew(4), 25, 1)
        ts = Simulation(hab).run()
        # O2 pp at t=0 should be exactly the target
        assert ts.cabin_o2_pp_kpa[0] == pytest.approx(O2_PP_TARGET_KPA, rel=1e-10)
        # CO2 pp at t=0 should be exactly the design target
        assert ts.cabin_co2_pp_kpa[0] == pytest.approx(CO2_PP_DESIGN_TARGET_KPA, rel=1e-10)
        # No demand/production at t=0
        assert ts.total_o2_demand_kg_hr[0] == 0.0
        assert ts.total_co2_production_kg_hr[0] == 0.0
        assert ts.total_heat_w[0] == 0.0
        assert ts.o2_injected_kg_hr[0] == 0.0
        assert ts.co2_removed_kg_hr[0] == 0.0
        assert ts.heat_rejected_w[0] == 0.0

    def test_time_starts_at_zero(self):
        hab = Habitat(CrewMember.reference_crew(4), 25, 1)
        ts = Simulation(hab).run()
        assert ts.time_hours[0] == 0.0

    def test_array_length_n_plus_1(self):
        """Output arrays should have n_steps + 1 elements (initial + sim steps)."""
        hab = Habitat(CrewMember.reference_crew(4), 25, 1)
        sim = Simulation(hab)
        ts = sim.run()
        expected = sim.n_steps + 1
        assert len(ts.time_hours) == expected
        assert len(ts.cabin_o2_mass_kg) == expected
        assert len(ts.cabin_o2_pp_kpa) == expected


# --- B9: Heat Rejection Capacity ---


class TestHeatRejection:
    def test_heat_rejection_capped(self):
        """Heat rejection should be capped at system capacity."""
        hab = Habitat(CrewMember.reference_crew(4), 25, 1)
        # Set heat rejection capacity to a small value
        sys = EclssSystem(heat_rejection_capacity_w=100.0)
        ts = Simulation(hab, system=sys).run()
        # heat_rejected_w should be capped at 100 W
        # total_heat_w (demand) may exceed it
        assert all(h <= 100.0 + 1e-9 for h in ts.heat_rejected_w[1:])
        # Demand should exceed cap for at least some steps
        assert any(d > 100.0 for d in ts.total_heat_w[1:])

    def test_unlimited_heat_rejection(self):
        """Without capacity limit, rejected == demand."""
        hab = Habitat(CrewMember.reference_crew(4), 25, 1)
        ts = Simulation(hab).run()
        np.testing.assert_array_almost_equal(
            ts.heat_rejected_w[1:], ts.total_heat_w[1:]
        )


# --- B11: Invalid Timestep ---


class TestTimestepValidation:
    def test_invalid_timestep_raises(self):
        """timestep_hours=0.7 does not evenly divide 24h."""
        hab = Habitat(CrewMember.reference_crew(4), 25, 1)
        with pytest.raises(ValueError, match="does not evenly divide 24 hours"):
            Simulation(hab, timestep_hours=0.7)

    def test_valid_timesteps_accepted(self):
        """Common valid timesteps should not raise."""
        hab = Habitat(CrewMember.reference_crew(4), 25, 1)
        for dt in [0.25, 0.5, 1.0, 2.0, 3.0, 4.0, 6.0, 8.0, 12.0, 24.0]:
            sim = Simulation(hab, timestep_hours=dt)
            assert sim.timestep_hours == dt


# --- Dynamic Activity Indexing ---


class TestDynamicActivityIndex:
    def test_custom_activity_in_schedule(self):
        """Non-standard activity should work with dynamic indexing."""
        # Create a custom activity not in the original hardcoded list
        EVA = ActivityLevel("EVA", 2000.0, 2.5, 3.0, 400.0, 600.0, 4.0, 2.0)
        CUSTOM_SLEEP = ActivityLevel("Sleep", 316.0, 0.37, 0.44, 160.0, 157.0, 1.08, 0.0)
        custom_day = DailySchedule([
            ActivityBlock(EVA, 0.0, 8.0),
            ActivityBlock(CUSTOM_SLEEP, 8.0, 16.0),
        ])
        crew = [CrewMember("Astro", 35, 80, 1.80, "male")]
        hab = Habitat(crew, 25, 1)
        sched = ConstantSchedule(custom_day)
        sim = Simulation(hab, schedules={"Astro": sched})
        ts = sim.run()
        # Verify the custom activity shows up in the results
        assert "EVA" in ts.crew_activity["Astro"]
        assert "Sleep" in ts.crew_activity["Astro"]
        # Verify sim completes without error and produces valid data
        assert ts.n_steps == 24
        assert ts.n_points == 25  # 24 steps + 1 initial
        assert all(pp > 0 for pp in ts.cabin_o2_pp_kpa)


# --- Schedule Validation ---


class TestScheduleValidation:
    def test_unknown_schedule_key_raises(self):
        hab = Habitat(CrewMember.reference_crew(2), 25.0, 1)
        bad_schedules = {"NonExistent": ConstantSchedule(REFERENCE_SCHEDULE)}
        with pytest.raises(ValueError, match="don't match"):
            Simulation(habitat=hab, schedules=bad_schedules)
