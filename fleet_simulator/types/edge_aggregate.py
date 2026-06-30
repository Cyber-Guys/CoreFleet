"""
Aggregatore edge:
    accumula le telemetrie che poi alimentano lo score
"""
from dataclasses import dataclass
from typing import TYPE_CHECKING

from ..config import IDLE_SPEED_MS, OVERREV_RPM, COLD_THRESHOLD_C

if TYPE_CHECKING:
    from .vehicle_state import VehicleState



@dataclass
class EdgeAggregate:
    distance_m: float = 0.0
    duration_s: float = 0.0
    speed_sum: float = 0.0
    speed_samples: int = 0
    max_speed_kmh: float = 0.0
    rpm_sum: float = 0.0
    fuel_l: float = 0.0
    harsh_accel: int = 0
    harsh_brake: int = 0
    overrev_s: float = 0.0
    cold_overrev_s: float = 0.0
    idle_s: float = 0.0
    speeding_s: float = 0.0

    def add_tick(self, st: "VehicleState", dt: float, limit_kmh: float):
        speed_kmh = st.speed_ms * 3.6
        self.distance_m += st.speed_ms * dt
        self.duration_s += dt
        self.speed_sum += speed_kmh
        self.speed_samples += 1
        self.max_speed_kmh = max(self.max_speed_kmh, speed_kmh)
        self.rpm_sum += st.rpm
        self.fuel_l += st.fuel_rate_lph / 3600.0 * dt

        if st.rpm > OVERREV_RPM:
            self.overrev_s += dt
            if st.coolant_c < COLD_THRESHOLD_C:
                self.cold_overrev_s += dt
        if st.speed_ms < IDLE_SPEED_MS and st.rpm > 0:
            self.idle_s += dt
        if speed_kmh > limit_kmh * 1.05:
            self.speeding_s += dt

    def summary_dict(self, vid: str) -> dict:
        dist_km = self.distance_m / 1000.0
        dur_min = self.duration_s / 60.0
        avg_speed = self.speed_sum / max(1, self.speed_samples)
        return {
            "vid": vid,
            "dist_km": round(dist_km, 3),
            "dur_min": round(dur_min, 2),
            "avg_kmh": round(avg_speed, 1),
            "max_kmh": round(self.max_speed_kmh, 1),
            "avg_rpm": round(self.rpm_sum / max(1, self.speed_samples)),
            "fuel_l": round(self.fuel_l, 3),
            "l_per_100km": round(self.fuel_l / dist_km * 100, 2) if dist_km > 0.05 else 0.0,
            "harsh_accel": self.harsh_accel,
            "harsh_brake": self.harsh_brake,
            "overrev_s": round(self.overrev_s, 1),
            "cold_overrev_s": round(self.cold_overrev_s, 1),
            "idle_s": round(self.idle_s, 1),
            "speeding_s": round(self.speeding_s, 1),
        }

