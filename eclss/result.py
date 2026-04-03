"""Result dataclasses for ECLSS sizing and simulation output."""

from dataclasses import dataclass, field

import numpy as np
from numpy.typing import NDArray


@dataclass
class ECLSSResult:
    """ECLSS sizing results grouped by subsystem.

    All rates are daily. All totals are for the full mission duration.
    Heat values are in watts. Mass values are in kg.
    """

    # --- Inputs (echoed for traceability) ---
    crew_count: int
    cabin_volume_m3: float
    mission_duration_days: int
    loop_mode: str

    # --- Atmosphere ---
    o2_generation_rate_kg_day: float
    co2_removal_rate_kg_day: float
    cabin_leakage_rate_kg_day: float

    # --- Thermal ---
    crew_metabolic_heat_w: float
    equipment_heat_w: float
    total_heat_rejection_w: float

    # --- Water (daily rates) ---
    water_consumption_kg_day: float
    water_production_kg_day: float
    water_recovery_efficiency_required: float  # 0.0 for open-loop
    water_resupply_kg_day: float

    # --- Consumables (mission totals) ---
    total_o2_kg: float
    total_water_kg: float
    total_food_kg: float
    o2_from_co2_recovery_kg: float   # 0.0 for open-loop
    water_recovered_kg: float        # 0.0 for open-loop
    sabatier_water_kg_day: float     # 0.0 for open-loop

    def __repr__(self) -> str:
        w = 50  # column width for labels
        lines = [
            "=" * (w + 18),
            f"  ECLSS Sizing Results: {self.loop_mode.upper()}-LOOP",
            "=" * (w + 18),
            "",
            "  CONFIGURATION",
            "-" * (w + 18),
            f"  {'Crew count':<{w}} {self.crew_count}",
            f"  {'Cabin volume':<{w}} {self.cabin_volume_m3:.1f} m3",
            f"  {'Mission duration':<{w}} {self.mission_duration_days} days",
            f"  {'Loop mode':<{w}} {self.loop_mode}",
            "",
            "  ATMOSPHERE",
            "-" * (w + 18),
            f"  {'O2 generation rate':<{w}} {self.o2_generation_rate_kg_day:.3f} kg/day",
            f"  {'CO2 removal rate':<{w}} {self.co2_removal_rate_kg_day:.3f} kg/day",
            f"  {'Cabin leakage rate':<{w}} {self.cabin_leakage_rate_kg_day:.4f} kg/day",
            "",
            "  THERMAL",
            "-" * (w + 18),
            f"  {'Crew metabolic heat':<{w}} {self.crew_metabolic_heat_w:.1f} W",
            f"  {'Equipment heat':<{w}} {self.equipment_heat_w:.1f} W",
            f"  {'Total heat rejection':<{w}} {self.total_heat_rejection_w:.1f} W",
            "",
            "  WATER (daily)",
            "-" * (w + 18),
            f"  {'Water consumption':<{w}} {self.water_consumption_kg_day:.3f} kg/day",
            f"  {'Water production (crew output)':<{w}} {self.water_production_kg_day:.3f} kg/day",
        ]

        if self.loop_mode == "closed":
            lines.append(
                f"  {'Recovery efficiency required':<{w}} {self.water_recovery_efficiency_required:.1%}"
            )
            lines.append(
                f"  {'Water resupply (shortfall)':<{w}} {self.water_resupply_kg_day:.3f} kg/day"
            )
        else:
            lines.append(
                f"  {'Water resupply':<{w}} {self.water_resupply_kg_day:.3f} kg/day"
            )

        lines.extend([
            "",
            "  CONSUMABLES (mission total)",
            "-" * (w + 18),
            f"  {'Total O2':<{w}} {self.total_o2_kg:.1f} kg",
            f"  {'Total water':<{w}} {self.total_water_kg:.1f} kg",
            f"  {'Total food (dry)':<{w}} {self.total_food_kg:.1f} kg",
        ])

        if self.loop_mode == "closed":
            lines.extend([
                f"  {'O2 recovered from CO2 (Sabatier)':<{w}} {self.o2_from_co2_recovery_kg:.1f} kg",
                f"  {'Water recovered':<{w}} {self.water_recovered_kg:.1f} kg",
                f"  {'Sabatier water production':<{w}} {self.sabatier_water_kg_day:.3f} kg/day",
            ])

        lines.extend([
            "",
            "=" * (w + 18),
        ])

        return "\n".join(lines)


@dataclass
class TimeSeriesResult:
    """Time-series output from hourly simulation.

    All 1-D arrays have shape (n_steps + 1,) where index 0 is initial
    conditions at t=0 and indices 1..n are post-timestep values.
    Per-crew dicts map crew name to (n_steps,) arrays (no t=0 entry).
    """

    # Time axis
    time_hours: NDArray[np.float64]
    timestep_hours: float

    # Cabin atmosphere state
    cabin_o2_mass_kg: NDArray[np.float64]
    cabin_co2_mass_kg: NDArray[np.float64]
    cabin_o2_pp_kpa: NDArray[np.float64]
    cabin_co2_pp_kpa: NDArray[np.float64]

    # Aggregate crew demands (summed across crew, per timestep)
    total_o2_demand_kg_hr: NDArray[np.float64]
    total_co2_production_kg_hr: NDArray[np.float64]
    total_heat_w: NDArray[np.float64]

    # ECLSS system delivery (after rate capping)
    o2_injected_kg_hr: NDArray[np.float64]
    co2_removed_kg_hr: NDArray[np.float64]

    # Heat actually rejected (after capacity capping)
    heat_rejected_w: NDArray[np.float64]

    # Per-crew breakdown
    crew_o2_demand_kg_hr: dict[str, NDArray[np.float64]]
    crew_co2_production_kg_hr: dict[str, NDArray[np.float64]]
    crew_activity: dict[str, list[str]]

    # Safe ranges (from BVAD Table 4-1)
    o2_pp_safe_range_kpa: tuple[float, float]
    co2_pp_safe_range_kpa: tuple[float, float]

    @property
    def n_points(self) -> int:
        """Number of data points (initial conditions + simulation steps)."""
        return len(self.time_hours)

    @property
    def n_steps(self) -> int:
        """Number of simulation steps (excludes initial conditions at t=0)."""
        return len(self.time_hours) - 1

    @property
    def duration_hours(self) -> float:
        """Mission duration in hours."""
        return float(self.time_hours[-1])

    def __repr__(self) -> str:
        o2_min = float(self.cabin_o2_pp_kpa.min())
        o2_max = float(self.cabin_o2_pp_kpa.max())
        co2_max = float(self.cabin_co2_pp_kpa.max())
        return (f"TimeSeriesResult({self.n_steps} steps, "
                f"{self.duration_hours:.0f}h, "
                f"O2={o2_min:.1f}-{o2_max:.1f} kPa, "
                f"CO2 peak={co2_max:.3f} kPa)")
