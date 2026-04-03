"""
Trace contaminant generation rates.

Source: NASA/TP-2015-218570/REV2 (BVAD) Table 4-3.
SMAC values from Ryder et al. (2020).
"""

# === Trace Contaminant Generation Rates (Table 4-3) ===
# BVAD Table 4-3: Model for Trace Contaminant Generation
# metabolic_mg_per_cm_day: crew metabolic generation (constant per CM, NOT BMR-scaled)
# equipment_mg_per_kg_day: equipment off-gassing per kg of equipment mass per day
# smac_180d_mg_m3: 180-day SMAC from Ryder et al. (2020)
# Note: Methane SMAC is 10% LEL (lower explosive limit), not toxicity-based.
# 10% LEL ≈ 5000 ppm ≈ 3,275 mg/m³ for methane at STP.
TRACE_CONTAMINANTS: dict[str, dict] = {
    "Methanol":       {"metabolic_mg_per_cm_day": 0.9,   "equipment_mg_per_kg_day": 1.3e-3,  "smac_180d_mg_m3": 26.0},
    "Ethanol":        {"metabolic_mg_per_cm_day": 4.3,   "equipment_mg_per_kg_day": 7.8e-3,  "smac_180d_mg_m3": 2000.0},
    "n-Butanol":      {"metabolic_mg_per_cm_day": 0.5,   "equipment_mg_per_kg_day": 4.7e-3,  "smac_180d_mg_m3": 40.0},
    "Formaldehyde":   {"metabolic_mg_per_cm_day": 0.4,   "equipment_mg_per_kg_day": 4.4e-6,  "smac_180d_mg_m3": 0.12},
    "Acetaldehyde":   {"metabolic_mg_per_cm_day": 0.6,   "equipment_mg_per_kg_day": 1.1e-4,  "smac_180d_mg_m3": 4.0},
    "Benzene":        {"metabolic_mg_per_cm_day": 2.2,   "equipment_mg_per_kg_day": 2.5e-5,  "smac_180d_mg_m3": 0.2},
    "Toluene":        {"metabolic_mg_per_cm_day": 0.6,   "equipment_mg_per_kg_day": 2.0e-3,  "smac_180d_mg_m3": 15.0},
    "Xylenes":        {"metabolic_mg_per_cm_day": 0.2,   "equipment_mg_per_kg_day": 3.7e-3,  "smac_180d_mg_m3": 37.0},
    "Furan":          {"metabolic_mg_per_cm_day": 0.3,   "equipment_mg_per_kg_day": 1.8e-6,  "smac_180d_mg_m3": 0.07},
    "Dichloromethane": {"metabolic_mg_per_cm_day": 0.09, "equipment_mg_per_kg_day": 2.2e-3,  "smac_180d_mg_m3": 10.0},
    "Acetone":        {"metabolic_mg_per_cm_day": 19.0,  "equipment_mg_per_kg_day": 3.6e-3,  "smac_180d_mg_m3": 52.0},
    "Trimethylsilanol": {"metabolic_mg_per_cm_day": 0.0, "equipment_mg_per_kg_day": 1.7e-4,  "smac_180d_mg_m3": 4.0},
    "Hexamethylcyclotrisiloxane": {"metabolic_mg_per_cm_day": 0.0, "equipment_mg_per_kg_day": 1.7e-4, "smac_180d_mg_m3": 9.0},
    "Ammonia":        {"metabolic_mg_per_cm_day": 50.0,  "equipment_mg_per_kg_day": 8.5e-5,  "smac_180d_mg_m3": 2.0},
    "Carbon Monoxide": {"metabolic_mg_per_cm_day": 18.0, "equipment_mg_per_kg_day": 2.0e-3,  "smac_180d_mg_m3": 17.0},
    "Hydrogen":       {"metabolic_mg_per_cm_day": 42.0,  "equipment_mg_per_kg_day": 5.9e-6,  "smac_180d_mg_m3": 340.0},
    "Methane":        {"metabolic_mg_per_cm_day": 329.0, "equipment_mg_per_kg_day": 6.4e-4,  "smac_180d_mg_m3": 3275.0},
}
