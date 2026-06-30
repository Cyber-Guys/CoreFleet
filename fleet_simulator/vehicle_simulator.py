"""
Simulatore di telemetria OBD2 di un veicolo.
"""
import math
import random

from .types import DriverProfile, EdgeAggregate, VehicleState
from .config import (
    IDLE_RPM, IDLE_SPEED_MS, MAX_RPM, COLD_THRESHOLD_C,
    WHEEL_CIRCUMFERENCE_M, FINAL_DRIVE, GEAR_RATIOS,
    TARGET_COOLANT_C, COOLANT_TAU_S, HARSH_ACCEL_MS2,
    HARSH_BRAKE_MS2, SPEED_LIMITS_KMH
)



class VehicleSimulator:
    def __init__(self, vid: str, init_pos: tuple[float, float], profile: DriverProfile):
        self.vid = vid
        self.p = profile
        self.st = VehicleState(lat=init_pos[0], lon=init_pos[1])
        # two aggregation scopes: a rolling window flushed in EDGE mode, and a
        # full-session accumulator used to build the end-of-session report.
        self.window_agg = EdgeAggregate()
        self.session_agg = EdgeAggregate()
        self.limit_kmh = random.choice(SPEED_LIMITS_KMH)
        self.target_ms = self.limit_kmh / 3.6
        self.segment_timer = random.uniform(15, 40)
        self._was_harsh_accel = False
        self._was_harsh_brake = False


    # --- scelta di un nuovo "segmento di strada" / obiettivo di velocità ---
    def _new_segment(self):
        self.limit_kmh = random.choice(SPEED_LIMITS_KMH)
        if random.random() < self.p.idle_tendency:
            self.target_ms = 0.0  # sosta / semaforo
            self.segment_timer = random.uniform(4, 15)
        else:
            tgt = self.limit_kmh * (1.0 + self.p.overshoot * random.uniform(0.4, 1.0))
            self.target_ms = tgt / 3.6
            self.segment_timer = random.uniform(20, 55)
        # piccola sterzata realistica
        self.st.heading += random.uniform(-0.6, 0.6)


    # --- modello marce/RPM fisicamente fondato ---
    def _update_gear_rpm(self):
        st = self.st
        if st.speed_ms < IDLE_SPEED_MS:
            st.gear = 1
            st.rpm = IDLE_RPM + random.uniform(-30, 60)
            return
        wheel_rps = st.speed_ms / WHEEL_CIRCUMFERENCE_M
        rpm = wheel_rps * 60.0 * GEAR_RATIOS[st.gear] * FINAL_DRIVE
        # cambia marcia in base alle abitudini del guidatore
        if rpm > self.p.shift_rpm and st.gear < 5:
            st.gear += 1
            rpm = wheel_rps * 60.0 * GEAR_RATIOS[st.gear] * FINAL_DRIVE
        elif rpm < 1200 and st.gear > 1:
            st.gear -= 1
            rpm = wheel_rps * 60.0 * GEAR_RATIOS[st.gear] * FINAL_DRIVE
        st.rpm = max(IDLE_RPM, min(MAX_RPM, rpm))


    def step(self, dt: float):
        st, p = self.st, self.p
        self.segment_timer -= dt
        if self.segment_timer <= 0:
            self._new_segment()

        # accelerazione desiderata verso il target, limitata dal profilo
        desired = (self.target_ms - st.speed_ms) / p.reaction_s
        # a motore freddo l'aggressivo spinge di più (cattiva cura del veicolo)
        cold_factor = 1.0
        if st.coolant_c < COLD_THRESHOLD_C:
            cold_factor = 1.0 + p.cold_aggression * 0.6
        accel = max(-p.brake_peak, min(p.accel_peak * cold_factor, desired))
        accel += random.gauss(0, p.jerk_noise)  # strappi / irregolarità
        st.accel_ms2 = accel

        st.speed_ms = max(0.0, st.speed_ms + accel * dt)
        self._update_gear_rpm()

        # carico motore e farfalla derivati da accelerazione + resistenze
        resistance = 0.012 * st.speed_ms + 0.0006 * st.speed_ms ** 2
        load = 18 + (max(0.0, accel) * 14) + resistance * 6
        st.engine_load = max(0.0, min(100.0, load))
        st.throttle = st.engine_load if accel > -0.2 else random.uniform(0, 6)

        # riscaldamento motore (approccio esponenziale al target)
        st.coolant_c += (TARGET_COOLANT_C - st.coolant_c) * (dt / COOLANT_TAU_S)

        # consumo: minimo a vuoto + quota carico*rpm + extra per accelerazioni
        # (l'extra penalizza chi tira il motore -> l'aggressivo consuma di più)
        st.fuel_rate_lph = (
            0.9
            + (st.engine_load / 100.0) * (st.rpm / 1000.0) * 2.8
            + max(0.0, accel) * 0.35
        )
        st.fuel_used_l += st.fuel_rate_lph / 3600.0 * dt

        # integrazione posizione GPS
        d = st.speed_ms * dt
        st.lat += d * math.cos(st.heading) / 111_111.0
        st.lon += d * math.sin(st.heading) / (111_111.0 * math.cos(math.radians(st.lat)))

        # rilevazione eventi (sul fronte di salita, non a ogni tick)
        harsh_accel = accel > HARSH_ACCEL_MS2 and not self._was_harsh_accel
        harsh_brake = accel < HARSH_BRAKE_MS2 and not self._was_harsh_brake
        self._was_harsh_accel = accel > HARSH_ACCEL_MS2
        self._was_harsh_brake = accel < HARSH_BRAKE_MS2

        # feed both the rolling window (EDGE transmissions) and the session total
        for agg in (self.window_agg, self.session_agg):
            if harsh_accel:
                agg.harsh_accel += 1
            if harsh_brake:
                agg.harsh_brake += 1
            agg.add_tick(st, dt, self.limit_kmh)


    def raw_sample(self, t: float) -> dict:
        """Campione OBD2 grezzo: nomi vicini ai PID SAE J1979 + GPS augmented."""
        st = self.st
        return {
            "vid": self.vid,
            "t": round(t, 1),
            "speed_kmh": round(st.speed_ms * 3.6, 1),     # PID 0x0D
            "rpm": round(st.rpm),                         # PID 0x0C
            "throttle": round(st.throttle, 1),            # PID 0x11
            "load": round(st.engine_load, 1),             # PID 0x04
            "coolant_c": round(st.coolant_c, 1),          # PID 0x05
            "fuel_lph": round(st.fuel_rate_lph, 2),       # PID 0x5E
            "lat": round(st.lat, 6),                      # GPS (augmented)
            "lon": round(st.lon, 6),                      # GPS (augmented)
            "limit_kmh": self.limit_kmh,                  # limite strada corrente (augmented)
        }

    def window_summary(self) -> dict:
        """Aggregate of the current EDGE window (last WINDOW_S seconds)."""
        s = self.window_agg.summary_dict(self.vid)
        s["lat"] = round(self.st.lat, 6)
        s["lon"] = round(self.st.lon, 6)
        return s

    def reset_window(self) -> None:
        """Start a fresh EDGE window after a summary has been transmitted."""
        self.window_agg = EdgeAggregate()

    def session_summary(self) -> dict:
        """Full-session aggregate, used to build the end-of-session report."""
        return self.session_agg.summary_dict(self.vid)

