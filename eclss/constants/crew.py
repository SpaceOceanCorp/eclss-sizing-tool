"""
Crew metabolic rates and reference crewmember demographics.

Source: NASA/TP-2015-218570/REV2 (BVAD)
Tables 3-23, 3-31, Figure 3-4.
82 kg reference crewmember, 90 min/day exercise assumption.
"""

# === Crew Metabolic Rates ===
# Reference: BVAD Tables 3-23 and 3-31
# 82 kg reference crewmember, standard exploration exercise (90 min/day)

O2_CONSUMPTION_KG_PER_CM_DAY = 0.895       # Table 3-31, Oxygen Consumed
CO2_PRODUCTION_KG_PER_CM_DAY = 1.085       # Table 3-31, Carbon Dioxide Load
METABOLIC_RATE_KJ_PER_CM_DAY = 12_027.0    # Table 3-23, total metabolic rate
METABOLIC_HEAT_SENSIBLE_KJ_PER_CM_DAY = 6_283.0  # Table 3-23, sensible (dry) heat
METABOLIC_HEAT_LATENT_KJ_PER_CM_DAY = 5_512.0    # Table 3-23, wet heat (latent + sweat runoff)
WATER_VAPOR_OUTPUT_KG_PER_CM_DAY = 2.27    # Table 3-23, water vapor output
POTABLE_WATER_KG_PER_CM_DAY = 3.217        # Table 3-31, Potable Water Content
FOOD_DRY_MASS_KG_PER_CM_DAY = 0.800        # Table 3-31, Food Solids (without packaging)
URINE_OUTPUT_KG_PER_CM_DAY = 1.420         # Table 3-31, Urine Water
FECAL_OUTPUT_KG_PER_CM_DAY = 0.101         # Table 3-31, Fecal Water

# === Complete Metabolic Interface (Figure 3-4 / Table 3-31) ===
# These values close the full daily mass balance (5.672 kg in = 5.672 kg out)

FOOD_WATER_KG_PER_CM_DAY = 0.760           # Figure 3-4, water content in food
FECAL_SOLIDS_KG_PER_CM_DAY = 0.032         # Figure 3-4 / Table 3-31
URINE_SOLIDS_KG_PER_CM_DAY = 0.061         # Figure 3-4 (0.059 in Table 3-31, using Figure value)
PERSPIRATION_SOLIDS_KG_PER_CM_DAY = 0.027  # Figure 3-4, sweat salts + misc solids
METABOLIC_WATER_KG_PER_CM_DAY = 0.487      # Figure 3-4, generated internally from food oxidation

# Figure 3-4 uses 2.946 kg/day for resp + perspiration water (includes all
# sweat runoff paths). Table 3-23 uses 2.27 (excludes some sweat runoff).
# Both are available; Habitat defaults to the Table 3-23 value.
RESP_PERSPIRATION_WATER_KG_PER_CM_DAY = 2.946  # Figure 3-4, all vapor water paths

# Hygiene water (not included in default water loop, available for full sizing)
HYGIENE_WATER_KG_PER_CM_DAY = 2.84         # Table 3-31, handwash + shower

# Waste storage estimate
WASTE_COMPACTION_DENSITY_KG_M3 = 600.0     # Engineering estimate for compacted solid waste

# === Reference Crewmember Demographics ===
# Used as baseline for BMR scaling (Eq 3-2 / 3-3)

REFERENCE_CM_AGE = 40.0
REFERENCE_CM_MASS_KG = 82.0
REFERENCE_CM_HEIGHT_M = 1.77
REFERENCE_CM_SEX = "male"

# === Table 3-25: Long-Mission Metabolic Loads (82 kg reference CM) ===
LONG_MISSION_METABOLIC_RATE_KJ_PER_CM_DAY = 12_778.0
LONG_MISSION_SENSIBLE_HEAT_KJ_PER_CM_DAY = 6_308.0
LONG_MISSION_LATENT_HEAT_KJ_PER_CM_DAY = 6_118.0
LONG_MISSION_WATER_VAPOR_KG_PER_CM_DAY = 2.52
LONG_MISSION_SWEAT_KG_PER_CM_DAY = 0.43
LONG_MISSION_O2_KG_PER_CM_DAY = 0.90
LONG_MISSION_CO2_KG_PER_CM_DAY = 1.08

# Short-mission sweat (Table 3-23: lumped into latent heat)
SWEAT_OUTPUT_KG_PER_CM_DAY = 0.64
