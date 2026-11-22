"""
Server-side trip aggregator.

In CLOUD mode the device streams raw 1 Hz telemetry and this module computes
the driving features on the server. In EDGE mode the raw stream stops and the
device sends window aggregates it computed itself; they are added in here, so
the trip aggregate stays complete when a vehicle changes mode. The trip score
always comes from the server. CLOUD and EDGE differ only in where the features
are computed (server or device) and how many bytes cross the link.

:meth:`ServerTripAggregator.result` returns the same fields as the device's
``EdgeAggregate.summary_dict`` (fleet_simulator), so its output can replace the
feature fields of the session payload as they are.

Thresholds mirror ``fleet_simulator/config.py`` (kept in sync by hand).
"""
from __future__ import annotations

# --- driving-quality thresholds (mirror fleet_simulator/config.py) ---
HARSH_ACCEL_MS2 = 3.0
HARSH_BRAKE_MS2 = -3.5
OVERREV_RPM = 4500
COLD_THRESHOLD_C = 60.0
IDLE_SPEED_MS = 0.6

#: Feature fields the server (re)computes and overrides on the session payload.
FEATURE_KEYS = (
    "dist_km", "dur_min", "avg_kmh", "max_kmh", "avg_rpm", "fuel_l",
    "l_per_100km", "harsh_accel", "harsh_brake", "overrev_s",
    "cold_overrev_s", "idle_s", "speeding_s",
)


class ServerTripAggregator:
    """Accumulates one trip's driving features on the server side.

    * :meth:`add_raw` (CLOUD): computes features from a 1 Hz raw sample,
      including acceleration as ``Δspeed/Δt`` to detect harsh events.
    * :meth:`fold_summary` (EDGE): adds a window aggregate computed on the device.

    Values are weighted by ``dt``, so raw ticks and EDGE windows add up to one
    aggregate for the whole trip.
    """

    def __init__(self, trip_id: str | None = None) -> None:
        self.trip_id = trip_id
        self.duration_s = 0.0
        self.dist_km = 0.0
        self.fuel_l = 0.0
        self.speed_time = 0.0   # Σ speed_kmh · dt  -> avg_kmh = /duration_s
        self.rpm_time = 0.0     # Σ rpm · dt        -> avg_rpm = /duration_s
        self.max_kmh = 0.0
        self.harsh_accel = 0
        self.harsh_brake = 0
        self.overrev_s = 0.0
        self.cold_overrev_s = 0.0
        self.idle_s = 0.0
        self.speeding_s = 0.0
        # provenance: how many raw ticks (server-derived) vs folded EDGE windows
        self.raw_ticks = 0
        self.edge_windows = 0
        # acceleration-derivation state (raw path only)
        self._prev_t: float | None = None
        self._prev_speed_ms: float | None = None
        self._was_harsh_accel = False
        self._was_harsh_brake = False

    # --- CLOUD: derive from raw ---
    def add_raw(self, s: dict) -> None:
        t = s.get("t")
        speed_kmh = float(s.get("speed_kmh", 0.0))
        speed_ms = speed_kmh / 3.6
        rpm = float(s.get("rpm", 0.0))
        coolant_c = float(s.get("coolant_c", 100.0))
        fuel_lph = float(s.get("fuel_lph", 0.0))
        limit_kmh = float(s.get("limit_kmh", 0.0) or 0.0)

        # dt from consecutive sample timestamps; fall back to one CLOUD tick and
        # clamp gaps left by a mode switch or out-of-order delivery.
        if t is not None and self._prev_t is not None:
            dt = float(t) - self._prev_t
        else:
            dt = 1.0  # 1 / CLOUD_HZ
        if dt <= 0.0 or dt > 5.0:
            dt = 1.0

        self.duration_s += dt
        self.dist_km += speed_ms * dt / 1000.0
        self.fuel_l += fuel_lph / 3600.0 * dt
        self.speed_time += speed_kmh * dt
        self.rpm_time += rpm * dt
        self.max_kmh = max(self.max_kmh, speed_kmh)

        if rpm > OVERREV_RPM:
            self.overrev_s += dt
            if coolant_c < COLD_THRESHOLD_C:
                self.cold_overrev_s += dt
        if speed_ms < IDLE_SPEED_MS and rpm > 0:
            self.idle_s += dt
        if limit_kmh > 0 and speed_kmh > limit_kmh * 1.05:
            self.speeding_s += dt

        # Acceleration computed on the server as Δspeed/Δt. A 1 Hz feed is
        # coarser than what the device samples, so harsh spikes shorter than a
        # second can be missed here.
        if self._prev_speed_ms is not None:
            accel = (speed_ms - self._prev_speed_ms) / dt
            if accel > HARSH_ACCEL_MS2 and not self._was_harsh_accel:
                self.harsh_accel += 1
            if accel < HARSH_BRAKE_MS2 and not self._was_harsh_brake:
                self.harsh_brake += 1
            self._was_harsh_accel = accel > HARSH_ACCEL_MS2
            self._was_harsh_brake = accel < HARSH_BRAKE_MS2

        self._prev_t = float(t) if t is not None else self.duration_s
        self._prev_speed_ms = speed_ms
        self.raw_ticks += 1

    # --- EDGE: fold a pre-computed window ---
    def fold_summary(self, s: dict) -> None:
        dur_s = float(s.get("dur_min", 0.0)) * 60.0
        self.duration_s += dur_s
        self.dist_km += float(s.get("dist_km", 0.0))
        self.fuel_l += float(s.get("fuel_l", 0.0))
        self.speed_time += float(s.get("avg_kmh", 0.0)) * dur_s
        self.rpm_time += float(s.get("avg_rpm", 0.0)) * dur_s
        self.max_kmh = max(self.max_kmh, float(s.get("max_kmh", 0.0)))
        self.harsh_accel += int(s.get("harsh_accel", 0))
        self.harsh_brake += int(s.get("harsh_brake", 0))
        self.overrev_s += float(s.get("overrev_s", 0.0))
        self.cold_overrev_s += float(s.get("cold_overrev_s", 0.0))
        self.idle_s += float(s.get("idle_s", 0.0))
        self.speeding_s += float(s.get("speeding_s", 0.0))
        # a folded window breaks raw acceleration continuity
        self._prev_t = None
        self._prev_speed_ms = None
        self._was_harsh_accel = False
        self._was_harsh_brake = False
        self.edge_windows += 1

    # --- output ---
    @property
    def has_data(self) -> bool:
        return self.duration_s > 0.0

    def provenance(self) -> str:
        """Where this trip's stats came from: the server, the device, or both."""
        if self.raw_ticks and self.edge_windows:
            return "server-mixed"
        if self.raw_ticks:
            return "server-cloud"
        return "edge"

    def result(self) -> dict:
        dur = max(self.duration_s, 1e-6)
        dist = self.dist_km
        return {
            "dist_km": round(dist, 3),
            "dur_min": round(self.duration_s / 60.0, 2),
            "avg_kmh": round(self.speed_time / dur, 1),
            "max_kmh": round(self.max_kmh, 1),
            "avg_rpm": round(self.rpm_time / dur),
            "fuel_l": round(self.fuel_l, 3),
            "l_per_100km": round(self.fuel_l / dist * 100, 2) if dist > 0.05 else 0.0,
            "harsh_accel": self.harsh_accel,
            "harsh_brake": self.harsh_brake,
            "overrev_s": round(self.overrev_s, 1),
            "cold_overrev_s": round(self.cold_overrev_s, 1),
            "idle_s": round(self.idle_s, 1),
            "speeding_s": round(self.speeding_s, 1),
        }
