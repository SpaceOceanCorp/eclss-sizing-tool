"""
ECLSS reference values from NASA/TP-2015-218570/REV2
(Life Support Baseline Values and Assumptions Document)

82 kg reference crewmember, 90 min/day exercise assumption.
All values from specific BVAD tables.
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

# Figure 3-4 uses 2.946 kg/day for resp + perspiration water (more complete than
# the 2.27 from Table 3-23 which excludes some sweat runoff paths).
# WATER_VAPOR_OUTPUT_KG_PER_CM_DAY (2.27) is kept as the Habitat default for backward compat.
RESP_PERSPIRATION_WATER_KG_PER_CM_DAY = 2.946  # Figure 3-4, all vapor water paths

# Hygiene water (not included in default water loop, available for full sizing)
HYGIENE_WATER_KG_PER_CM_DAY = 2.84         # Table 3-31, handwash + shower

# Waste storage estimate
WASTE_COMPACTION_DENSITY_KG_M3 = 600.0     # Engineering estimate for compacted solid waste

# === Atmosphere Parameters ===
# Reference: BVAD Table 4-1

CABIN_PRESSURE_NOMINAL_KPA = 101.0         # Table 4-1, nominal
CABIN_PRESSURE_REDUCED_KPA = 70.3          # Table 4-1, reduced-pressure vehicles
O2_PP_MIN_KPA = 15.2                       # Table 4-1, lower (allowable 1 hr)
O2_PP_MAX_KPA = 50.6                       # Table 4-1, upper
O2_PP_TARGET_KPA = 21.2                    # Table 4-1, nominal (no impairment)
CO2_PP_LIMIT_KPA = 0.507                   # Table 4-1, nominal for crew
CO2_PP_DESIGN_TARGET_KPA = 0.4             # Long-duration design target
TEMP_MIN_K = 291.0                         # Table 4-1, lower (18 C)
TEMP_NOMINAL_K = 296.0                     # Table 4-1, nominal (23 C)
TEMP_MAX_K = 300.0                         # Table 4-1, upper (27 C)
RH_MIN_PCT = 25.0                          # Table 4-1, lower
RH_NOMINAL_PCT = 40.0                      # Table 4-1, nominal
RH_MAX_PCT = 75.0                          # Table 4-1, upper
CABIN_LEAKAGE_RATE_KG_PER_MODULE_DAY = 0.02  # Table 4-1, nominal (per module)

# === Recovery Assumptions (closed-loop) ===

WATER_RECOVERY_EFFICIENCY = 0.93           # ISS WPA reference (~93%)

# === Equipment ===

EQUIPMENT_HEAT_W_PER_CREW = 1_500.0        # assumption (1-2 kW/person)

# === Reference Crewmember Demographics ===
# Used as baseline for BMR scaling (Eq 3-2 / 3-3)

REFERENCE_CM_AGE = 40.0
REFERENCE_CM_MASS_KG = 82.0
REFERENCE_CM_HEIGHT_M = 1.77
REFERENCE_CM_SEX = "male"

# === Table 4-1 Safe Ranges===

O2_PP_SAFE_RANGE_KPA = (20.7, 50.6)       # (min no-impairment, max)
CO2_PP_SAFE_RANGE_KPA = (0.0, 1.01)       # (min, max for crew)
CO2_PP_NOMINAL_KPA = 0.507                # nominal for crew
TEMP_SAFE_RANGE_K = (291.0, 300.0)        # (min, max)
RH_SAFE_RANGE_PCT = (25.0, 75.0)          # (min, max)

# === Gas Properties (partial pressure conversion) ===

O2_MOLAR_MASS = 0.032      # kg/mol
CO2_MOLAR_MASS = 0.044     # kg/mol
N2_MOLAR_MASS = 0.028      # kg/mol
R_UNIVERSAL = 8.314        # J/(mol·K)
