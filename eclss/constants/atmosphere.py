"""
Cabin atmosphere parameters and safe operating ranges.

Source: NASA/TP-2015-218570/REV2 (BVAD) Table 4-1.
"""

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

# === Table 4-1 Safe Ranges ===

O2_PP_SAFE_RANGE_KPA = (20.7, 50.6)       # (min no-impairment, max)
CO2_PP_SAFE_RANGE_KPA = (0.0, 1.01)       # (min, max for crew)
CO2_PP_NOMINAL_KPA = 0.507                # nominal for crew
TEMP_SAFE_RANGE_K = (291.0, 300.0)        # (min, max)
RH_SAFE_RANGE_PCT = (25.0, 75.0)          # (min, max)
