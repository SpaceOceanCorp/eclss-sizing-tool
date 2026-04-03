"""System assessment — PASS/FAIL checks and minimum requirements extraction.

Given a TimeSeriesResult from a simulation, extracts peak demands and
checks whether cabin conditions stayed within BVAD Table 4-1 safe ranges.
"""

import numpy as np
from dataclasses import dataclass, field

from eclss.result import TimeSeriesResult


@dataclass(frozen=True)
class MinimumRequirements:
    """Minimum ECLSS hardware specs derived from simulation peak demands."""

    peak_o2_generation_kg_hr: float
    peak_co2_removal_kg_hr: float
    peak_heat_rejection_w: float

    @classmethod
    def from_simulation(cls, ts: TimeSeriesResult) -> "MinimumRequirements":
        """Extract peak demands from simulation results."""
        return cls(
            peak_o2_generation_kg_hr=float(np.max(ts.total_o2_demand_kg_hr)),
            peak_co2_removal_kg_hr=float(np.max(ts.total_co2_production_kg_hr)),
            peak_heat_rejection_w=float(np.max(ts.total_heat_w)),
        )

    def with_margin(self, factor: float = 1.2) -> "MinimumRequirements":
        """Apply a design safety margin to all requirements."""
        return MinimumRequirements(
            peak_o2_generation_kg_hr=self.peak_o2_generation_kg_hr * factor,
            peak_co2_removal_kg_hr=self.peak_co2_removal_kg_hr * factor,
            peak_heat_rejection_w=self.peak_heat_rejection_w * factor,
        )


@dataclass(frozen=True)
class Violation:
    """A contiguous window where a safe limit was exceeded."""

    subsystem: str          # "o2" or "co2"
    start_hour: float       # first hour of violation
    end_hour: float         # last hour of violation
    peak_value_kpa: float   # worst-case partial pressure in this window
    limit_kpa: float        # the limit that was exceeded
    duration_hours: float   # total duration of violation
    description: str


@dataclass
class SystemAssessment:
    """Overall PASS/FAIL assessment of a simulation run."""

    overall_pass: bool
    violations: list[Violation] = field(default_factory=list)
    summary: str = ""

    def __repr__(self) -> str:
        if self.overall_pass:
            return "SystemAssessment: PASS — all subsystems within limits"
        return f"SystemAssessment: FAIL — {len(self.violations)} violation(s)\n{self.summary}"


def _aggregate_violations(
    indices: np.ndarray,
    time_hours: np.ndarray,
    values_kpa: np.ndarray,
    limit_kpa: float,
    subsystem: str,
    description_template: str,
    dt: float,
    use_min: bool = False,
) -> list[Violation]:
    """Aggregate contiguous violation timesteps into windows."""
    if len(indices) == 0:
        return []

    violations = []
    # Split into contiguous runs (gaps > 1 step apart)
    splits = np.where(np.diff(indices) > 1)[0] + 1
    runs = np.split(indices, splits)

    for run in runs:
        start = float(time_hours[run[0]])
        end = float(time_hours[run[-1]])
        if use_min:
            peak = float(np.min(values_kpa[run]))
        else:
            peak = float(np.max(values_kpa[run]))
        duration = (end - start) + dt
        violations.append(Violation(
            subsystem=subsystem,
            start_hour=start,
            end_hour=end,
            peak_value_kpa=peak,
            limit_kpa=limit_kpa,
            duration_hours=duration,
            description=description_template.format(peak=peak, limit=limit_kpa),
        ))

    return violations


def assess_system(ts: TimeSeriesResult) -> SystemAssessment:
    """Check simulation results against BVAD Table 4-1 safe ranges.

    Contiguous violation timesteps are aggregated into windows.

    Checks:
    - O2 partial pressure within safe range (20.7–50.6 kPa)
    - CO2 partial pressure below limit (1.01 kPa)
    """
    violations: list[Violation] = []
    dt = ts.timestep_hours

    o2_low, o2_high = ts.o2_pp_safe_range_kpa
    _co2_low, co2_high = ts.co2_pp_safe_range_kpa

    # O2 too low
    violations.extend(_aggregate_violations(
        np.where(ts.cabin_o2_pp_kpa < o2_low)[0],
        ts.time_hours, ts.cabin_o2_pp_kpa, o2_low,
        "o2", "O2 pp {peak:.2f} kPa below minimum {limit} kPa", dt, use_min=True,
    ))

    # O2 too high
    violations.extend(_aggregate_violations(
        np.where(ts.cabin_o2_pp_kpa > o2_high)[0],
        ts.time_hours, ts.cabin_o2_pp_kpa, o2_high,
        "o2", "O2 pp {peak:.2f} kPa above maximum {limit} kPa", dt,
    ))

    # CO2 too high
    violations.extend(_aggregate_violations(
        np.where(ts.cabin_co2_pp_kpa > co2_high)[0],
        ts.time_hours, ts.cabin_co2_pp_kpa, co2_high,
        "co2", "CO2 pp {peak:.2f} kPa above limit {limit} kPa", dt,
    ))

    overall = len(violations) == 0
    if overall:
        summary = "PASS: All parameters within safe ranges"
    else:
        total_hours = sum(v.duration_hours for v in violations)
        summary = f"FAIL: {len(violations)} violation window(s), {total_hours:.1f} total hours"

    return SystemAssessment(overall_pass=overall, violations=violations, summary=summary)
