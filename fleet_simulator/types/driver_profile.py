"""
Profilo Guidatore:
    determina quanto è aggressivo il guidatore
"""
from dataclasses import dataclass



@dataclass
class DriverProfile:
    name: str
    accel_peak: float        # accelerazione max desiderata (m/s^2)
    brake_peak: float        # decelerazione max (m/s^2, valore positivo)
    shift_rpm: int           # rpm a cui cambia marcia (alto = over-revving)
    overshoot: float         # quanto supera il limite (es. 0.20 = +20%)
    idle_tendency: float     # probabilità di soste/idle (0..1)
    cold_aggression: float   # quanto spinge a motore freddo (0..1)
    jerk_noise: float        # irregolarità della guida (strappi)
    reaction_s: float        # tempo per raggiungere la velocità target

