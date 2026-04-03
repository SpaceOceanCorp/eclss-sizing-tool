"""Trace contaminant estimation from BVAD Table 4-3.

Models crew metabolic and equipment off-gassing contaminant generation.
Compares worst-case cabin concentration against SMAC limits to size
the Trace Contaminant Control System (TCCS).

Contaminant generation is constant per crewmember (NOT BMR-scaled).
Equipment generation scales with total equipment mass.
"""

from __future__ import annotations
from eclss.constants import TRACE_CONTAMINANTS


class ContaminantEstimator:
    """Trace contaminant generation and SMAC assessment.

    Can be constructed directly or from a Habitat object.

    Examples:
        # Direct construction
        est = ContaminantEstimator(crew_count=4, cabin_volume_m3=25.0)

        # From a Habitat
        est = ContaminantEstimator.from_habitat(habitat, equipment_mass_kg=2000)

        # With custom contaminants
        est = ContaminantEstimator(crew_count=4, cabin_volume_m3=25.0,
            custom_contaminants={"Siloxane-D5": {
                "metabolic_mg_per_cm_day": 0.0,
                "equipment_mg_per_kg_day": 0.01,
                "smac_180d_mg_m3": 5.0,
            }})
    """

    def __init__(self, crew_count: int, cabin_volume_m3: float,
                 equipment_mass_kg: float = 0.0,
                 custom_contaminants: dict[str, dict] | None = None):
        if crew_count < 1:
            raise ValueError(f"crew_count must be >= 1, got {crew_count}")
        if cabin_volume_m3 <= 0:
            raise ValueError(f"cabin_volume_m3 must be > 0, got {cabin_volume_m3}")
        if equipment_mass_kg < 0:
            raise ValueError(f"equipment_mass_kg must be >= 0, got {equipment_mass_kg}")
        self.crew_count = crew_count
        self.cabin_volume_m3 = cabin_volume_m3
        self.equipment_mass_kg = equipment_mass_kg

        self._contaminants = dict(TRACE_CONTAMINANTS)  # copy BVAD defaults
        if custom_contaminants:
            self._contaminants.update(custom_contaminants)

    @classmethod
    def from_habitat(cls, habitat, equipment_mass_kg: float = 0.0,
                     custom_contaminants: dict[str, dict] | None = None) -> ContaminantEstimator:
        """Create from a Habitat, pulling crew_count and cabin_volume_m3 automatically."""
        return cls(
            crew_count=habitat.crew_count,
            cabin_volume_m3=habitat.cabin_volume_m3,
            equipment_mass_kg=equipment_mass_kg,
            custom_contaminants=custom_contaminants,
        )

    def add_contaminant(self, name: str, metabolic_mg_per_cm_day: float,
                        equipment_mg_per_kg_day: float, smac_180d_mg_m3: float) -> None:
        """Add or override a contaminant."""
        self._contaminants[name] = {
            "metabolic_mg_per_cm_day": metabolic_mg_per_cm_day,
            "equipment_mg_per_kg_day": equipment_mg_per_kg_day,
            "smac_180d_mg_m3": smac_180d_mg_m3,
        }

    def metabolic_generation_rates(self) -> dict[str, float]:
        """Crew metabolic generation rates in mg/day (constant per CM)."""
        return {
            name: data["metabolic_mg_per_cm_day"] * self.crew_count
            for name, data in self._contaminants.items()
        }

    def equipment_generation_rates(self) -> dict[str, float]:
        """Equipment off-gassing rates in mg/day (scales with equipment mass)."""
        return {
            name: data["equipment_mg_per_kg_day"] * self.equipment_mass_kg
            for name, data in self._contaminants.items()
        }

    def total_generation_rates(self) -> dict[str, float]:
        """Total generation rate in mg/day (metabolic + equipment)."""
        return {
            name: (data["metabolic_mg_per_cm_day"] * self.crew_count
                   + data["equipment_mg_per_kg_day"] * self.equipment_mass_kg)
            for name, data in self._contaminants.items()
        }

    def check_smac_limits(self, days: int = 180) -> list[dict]:
        """Check if uncontrolled accumulation exceeds SMAC over given period.

        Assumes no active removal (worst case). Used to size TCCS.

        Returns a list of dicts per contaminant with:
        - name, generation_mg_day (total), metabolic_mg_day, equipment_mg_day
        - accumulation_mg_m3 (worst-case no-removal concentration)
        - smac_mg_m3, exceeds_smac
        - removal_rate_required_mg_day (minimum TCCS removal to stay under SMAC)
        """
        results = []
        for name, data in self._contaminants.items():
            metabolic = data["metabolic_mg_per_cm_day"] * self.crew_count
            equipment = data["equipment_mg_per_kg_day"] * self.equipment_mass_kg
            gen_total = metabolic + equipment
            accumulation = (gen_total * days) / self.cabin_volume_m3
            smac = data["smac_180d_mg_m3"]
            max_gen_no_removal = (smac * self.cabin_volume_m3) / days
            removal_needed = max(0.0, gen_total - max_gen_no_removal)
            results.append({
                "name": name,
                "generation_mg_day": gen_total,
                "metabolic_mg_day": metabolic,
                "equipment_mg_day": equipment,
                "accumulation_mg_m3": accumulation,
                "smac_mg_m3": smac,
                "exceeds_smac": accumulation > smac,
                "removal_rate_required_mg_day": removal_needed,
            })
        return results
