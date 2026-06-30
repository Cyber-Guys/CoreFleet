"""
Stato del veicolo:
    contiene le informazioni sullo stato attuale del veicolo
"""
import random
import math

from dataclasses import dataclass, field

from config import IDLE_RPM, AMBIENT_C



@dataclass
class VehicleState:
    speed_ms: float = 0.0
    accel_ms2: float = 0.0
    rpm: float = IDLE_RPM
    gear: int = 1
    throttle: float = 0.0
    engine_load: float = 0.0
    coolant_c: float = AMBIENT_C
    fuel_rate_lph: float = 0.8
    fuel_used_l: float = 0.0
    lat: float
    lon: float
    heading: float = field(default_factory=lambda: random.uniform(0, 2 * math.pi))

