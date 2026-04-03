"""ECLSS hardware system model.

Three modes:
  EclssSystem()          — BVAD defaults (None = unlimited, ideal sizing)
  EclssSystem.zero()     — all capacities 0.0 (see raw requirements)
  EclssSystem(o2=0.2)    — explicit hardware values
"""

from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class EclssSystem:
    """ECLSS hardware capacity limits.

    Default: None = unlimited (ideal sizing mode).
    Use .zero() to see raw requirements with no processing.
    Set explicit values for real hardware analysis.
    """

    o2_generation_capacity_kg_hr: float | None = None
    co2_removal_capacity_kg_hr: float | None = None
    heat_rejection_capacity_w: float | None = None
    water_recovery_rate_kg_hr: float | None = None
    water_recovery_efficiency: float = 0.93
    sabatier_co2_capacity_kg_hr: float | None = None

    @classmethod
    def unlimited(cls) -> EclssSystem:
        """All capacities unlimited (same as default). Explicit intent."""
        return cls()

    @classmethod
    def zero(cls) -> EclssSystem:
        """All capacities zero — no processing. Shows raw crew requirements."""
        return cls(
            o2_generation_capacity_kg_hr=0.0,
            co2_removal_capacity_kg_hr=0.0,
            heat_rejection_capacity_w=0.0,
            water_recovery_rate_kg_hr=0.0,
            water_recovery_efficiency=0.0,
            sabatier_co2_capacity_kg_hr=0.0,
        )

    def _effective_rate(self, demand: float, capacity: float | None) -> float:
        if capacity is None:
            return demand
        return min(demand, capacity)

    def effective_o2_rate(self, demand_kg_hr: float) -> float:
        return self._effective_rate(demand_kg_hr, self.o2_generation_capacity_kg_hr)

    def effective_co2_rate(self, demand_kg_hr: float) -> float:
        return self._effective_rate(demand_kg_hr, self.co2_removal_capacity_kg_hr)

    def effective_heat_rate(self, demand_w: float) -> float:
        return self._effective_rate(demand_w, self.heat_rejection_capacity_w)

    def can_meet_o2_demand(self, demand_kg_hr: float) -> bool:
        return self.o2_generation_capacity_kg_hr is None or demand_kg_hr <= self.o2_generation_capacity_kg_hr

    def can_meet_co2_demand(self, demand_kg_hr: float) -> bool:
        return self.co2_removal_capacity_kg_hr is None or demand_kg_hr <= self.co2_removal_capacity_kg_hr

    def can_meet_thermal_demand(self, demand_w: float) -> bool:
        return self.heat_rejection_capacity_w is None or demand_w <= self.heat_rejection_capacity_w

    def __repr__(self) -> str:
        parts = []
        for field, unit in [
            ("o2_generation_capacity_kg_hr", "kg/hr"),
            ("co2_removal_capacity_kg_hr", "kg/hr"),
            ("heat_rejection_capacity_w", "W"),
            ("water_recovery_rate_kg_hr", "kg/hr"),
            ("sabatier_co2_capacity_kg_hr", "kg/hr"),
        ]:
            val = getattr(self, field)
            if val is None:
                parts.append(f"{field.split('_capacity')[0]}=unlimited")
            elif val > 0:
                parts.append(f"{field.split('_capacity')[0]}={val} {unit}")
            else:
                parts.append(f"{field.split('_capacity')[0]}=0")
        return f"EclssSystem({', '.join(parts)})"
