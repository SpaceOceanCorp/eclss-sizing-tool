# ECLSS Sizing Tool

Python tool for computing Environmental Control and Life Support System (ECLSS) requirements for crewed spacecraft and habitat missions, taking from NASA/TP-2015-218570/REV2, *Life Support Baseline Values and Assumptions Document* (BVAD). Take in a crew count, cabin volume, and mission duration, the tool calculates oxygen generation rates, CO2 removal rates, thermal rejection loads, water balance, and consumables mass budgets for both open-loop and closed-loop life support architectures.

## Reference Values (NASA/TP-2015-218570/REV2, *Life Support Baseline Values and Assumptions Document*)

### Crew Metabolic Loads (BVAD Table 3-23)

82 kg reference crewmember, standard exploration exercise assumption (90 min/day at 75% VO2max).

| Parameter | Value | Units |
|-----------|-------|-------|
| Metabolic rate | 12,027 | kJ/CM-day |
| Sensible (dry) heat output | 6,283 | kJ/CM-day |
| Wet heat output (latent + sweat runoff) | 5,512 | kJ/CM-day |
| Water vapor output | 2.27 | kg/CM-day |
| O2 consumption | 0.84 | kg/CM-day |
| CO2 output | 1.01 | kg/CM-day |

### Crew Metabolic Interface (BVAD Table 3-31)

| Parameter | Value | Units |
|-----------|-------|-------|
| Oxygen consumed | 0.895 | kg/CM-day |
| Carbon dioxide load | 1.085 | kg/CM-day |
| Food solids (without packaging) | 0.800 | kg/CM-day |
| Potable water content | 3.217 | kg/CM-day |
| Urine water | 1.420 | kg/CM-day |
| Fecal water | 0.101 | kg/CM-day |

### Vehicle Atmosphere (BVAD Table 4-1)

| Parameter | Lower | Nominal | Upper | Units |
|-----------|-------|---------|-------|-------|
| Total cabin pressure | 48.0 | 101 or 70.3 | 102.7 | kPa |
| ppO2 (no impairment) | 20.7 | 21.2 | 50.6 | kPa |
| ppCO2 (crew) | 0.267 | 0.507 | 1.01 | kPa |
| Temperature | 291 | 296 | 300 | K |
| Relative humidity | 25 | 40 | 75 | % |
| Perspired water vapor | 0.036 | 0.699 | 1.973 | kg/CM-day |
| Respired water vapor | 0.803 | 0.885 | 0.975 | kg/CM-day |
| Air leakage rate | 0.01 | 0.02 | 0.09 | kg/module-day |

## Usage

```python
from eclss import Habitat

# Open-loop: all consumables brought from Earth
hab = Habitat(
    crew_count=4,
    cabin_volume_m3=25.0,
    mission_duration_days=180,
)
result = hab.calculate()
print(result)

# Closed-loop: water recovery + O2 from CO2 (Sabatier)
hab_closed = Habitat(
    crew_count=4,
    cabin_volume_m3=25.0,
    mission_duration_days=180,
    loop_mode="closed",
)
result_closed = hab_closed.calculate()
print(result_closed)
```

All BVAD constants can be overridden at instantiation:

```python
# Custom O2 consumption rate for a different crew profile
hab = Habitat(
    crew_count=6,
    cabin_volume_m3=100.0,
    mission_duration_days=365,
    o2_consumption_kg_per_cm_day=0.84,
    loop_mode="closed",
)
```

## Scope

**Included:**
- Crew metabolic loads (O2, CO2, heat, water, food, waste)
- Atmosphere requirements (O2 generation, CO2 removal, leakage makeup)
- Thermal rejection loads (crew metabolic + equipment heat)
- Water balance (open-loop resupply, closed-loop recovery efficiency)
- Consumables mass budget (mission totals)
- Closed-loop O2 recovery via Sabatier + electrolysis

**Not included**
- Specific hardware sizing (CDRA, OGS, WPA units)
- Trace contaminant control
- Thermal control loop hardware (radiator sizing)
- EVA consumables losses
- 15-minute transient metabolic profiles

## Citation

> NASA/TP-2015-218570/REV2. *Life Support Baseline Values and Assumptions Document.* National Aeronautics and Space Administration, 2015.
