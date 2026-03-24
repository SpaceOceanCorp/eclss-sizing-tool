"""
ECLSS reference values from NASA/TP-2015-218570/REV2
(Life Support Baseline Values and Assumptions Document)

82 kg reference crewmember, 90 min/day exercise assumption.
All values traceable to specific BVAD tables.
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

EQUIPMENT_HEAT_W_PER_CREW = 1_500.0        # Engineering assumption (1-2 kW/person)
