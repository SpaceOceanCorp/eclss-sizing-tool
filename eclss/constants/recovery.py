"""
Recovery assumptions and equipment parameters.

Water recovery based on ISS WPA reference.
Equipment heat is an engineering estimate.
"""

# === Recovery Assumptions (closed-loop) ===

WATER_RECOVERY_EFFICIENCY = 0.93           # ISS WPA reference (~93%)

# === Equipment ===

EQUIPMENT_HEAT_W_PER_CREW = 1_500.0        # assumption (1-2 kW/person)
