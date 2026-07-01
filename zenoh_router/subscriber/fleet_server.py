"""
CoreFleet server: subscriber + congestion controller + session finalizer.

Responsibilities
----------------
* Track presence via liveliness tokens (``core/fleet/*/alive``).
* Ingest telemetry: ``raw`` (CLOUD, 1 Hz) and ``summary`` (EDGE windows).
* Decide the fleet transmission mode from the projected CLOUD bandwidth, with
  hysteresis, and broadcast it on ``core/fleet/mode`` (also answered via a
  queryable so late-joining vehicles can read the current mode on boot).
* Finalize a driving session when its full-session aggregate arrives on
  ``core/fleet/*/session`` and emit the report payload (LLM/Jakarta hand-off).
* Report bandwidth and estimated transmission energy saved vs an all-CLOUD
  baseline -- the headline Challenge 1 metric.
"""
from __future__ import annotations

import json
import logging
import os
import random
import signal
import threading
import time
import urllib.error
import urllib.request

import zenoh

from corefleet import protocol as P
from corefleet.client import build_client_config

log = logging.getLogger(__name__)


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, default))
    except ValueError:
        return default


def _full_name(data: dict) -> str:
    """Driver full name (nome + cognome) from a telemetry payload."""
    return f"{data.get('driver_name', '')} {data.get('driver_surname', '')}".strip()


def _bad_behaviours(summary: dict) -> list[str]:
    """Names of the unsafe/wasteful behaviours present in a trip aggregate.
    Note: 'speeding' (a fine) is added separately — not every moment over the
    limit becomes a multa."""
    flags = []
    if summary.get("harsh_accel", 0) > 0:
        flags.append("harsh_accel")
    if summary.get("harsh_brake", 0) > 0:
        flags.append("harsh_brake")
    if summary.get("overrev_s", 0) > 0:
        flags.append("overrev")
    if summary.get("cold_overrev_s", 0) > 0:
        flags.append("cold_overrev")
    if summary.get("idle_s", 0) > 30:
        flags.append("excess_idle")
    return flags


class FleetServer:
    def __init__(self, router: str) -> None:
        self.router = router

        # channel capacity (bytes/s). Vehicles are kept in CLOUD up to
        # cloud_saturation of it; the overflow is offloaded to EDGE.
        self.bw_limit = _env_float("BW_LIMIT_BYTES_S", 4000.0)
        self.cloud_saturation = _env_float("CLOUD_SATURATION", 0.8)
        self.joules_per_mb = _env_float("JOULES_PER_MB", 1100.0)
        self.stats_interval_s = _env_float("STATS_INTERVAL_S", 5.0)
        # a fine (multa) needs sustained speeding AND being caught — not every
        # second over the limit is a fine
        self.fine_min_speeding_s = _env_float("FINE_MIN_SPEEDING_S", 6.0)
        self.fine_catch_rate = _env_float("FINE_CATCH_RATE", 0.3)
        # Jakarta stats/registry service. Empty -> ingest disabled (log only).
        self.ingest_url = os.getenv("INGEST_URL", os.getenv("REPORT_URL", "")).strip()
        # live "who is driving now" endpoint (defaults next to the ingest one)
        default_active = self.ingest_url.replace("/trips", "/active") if self.ingest_url else ""
        self.active_url = os.getenv("ACTIVE_URL", default_active).strip()
        self.active_interval_s = _env_float("ACTIVE_INTERVAL_S", 2.0)

        self._lock = threading.Lock()
        self._active: set[str] = set()
        self._last_pos: dict[str, tuple[float, float]] = {}
        self._current: dict[str, dict] = {}   # vid -> {did, name, ...} currently driving
        self._vmode: dict[str, P.Mode] = {}   # vid -> assigned transmission mode
        self._join_seq: dict[str, int] = {}   # vid -> join order (CLOUD priority)
        self._seq = 0

        # rolling traffic counters (since last stats tick)
        self._raw_msgs = 0
        self._raw_bytes = 0
        self._sum_msgs = 0
        self._sum_bytes = 0
        self._avg_raw_bytes = 220.0  # seed estimate, refined from live samples

        # cumulative energy accounting
        self._baseline_bytes = 0.0
        self._actual_bytes = 0.0

        self._stop = threading.Event()
        self._session: zenoh.Session | None = None

    # --- per-vehicle mode ---
    def _publish_vehicle_mode(self, vid: str, mode: P.Mode) -> None:
        if self._session is not None:
            self._session.put(P.mode_key(vid), mode.value, encoding=zenoh.Encoding.TEXT_PLAIN)

    def _on_mode_query(self, query: "zenoh.Query") -> None:
        key = str(query.key_expr)
        vid = P.vid_from_key(key)
        with self._lock:
            mode = self._vmode.get(vid, P.Mode.CLOUD).value
        query.reply(key, mode, encoding=zenoh.Encoding.TEXT_PLAIN)
        query.drop()

    # --- presence (liveliness) ---
    def _on_liveliness(self, sample: "zenoh.Sample") -> None:
        vid = P.vid_from_key(str(sample.key_expr))
        if not vid:
            return
        with self._lock:
            if sample.kind == zenoh.SampleKind.PUT:
                if vid not in self._active:
                    self._active.add(vid)
                    self._seq += 1
                    self._join_seq[vid] = self._seq   # older vehicles keep CLOUD priority
                log.info("[+] vehicle online: %s (active=%d)", vid, len(self._active))
            else:  # DELETE -> token dropped
                self._active.discard(vid)
                self._last_pos.pop(vid, None)
                self._current.pop(vid, None)
                self._vmode.pop(vid, None)
                self._join_seq.pop(vid, None)
                log.info("[-] vehicle offline: %s (active=%d)", vid, len(self._active))

    # --- telemetry ---
    def _on_raw(self, sample: "zenoh.Sample") -> None:
        size = len(bytes(sample.payload))
        try:
            data = P.decode(sample.payload.to_string())
        except json.JSONDecodeError:
            return
        with self._lock:
            self._raw_msgs += 1
            self._raw_bytes += size
            self._avg_raw_bytes = 0.98 * self._avg_raw_bytes + 0.02 * size
            self._actual_bytes += size
            self._last_pos[data["vid"]] = (data.get("lat"), data.get("lon"))
            # full live telemetry snapshot (CLOUD, 1 Hz)
            self._current[data["vid"]] = {
                "vid": data["vid"], "did": data.get("did"), "name": _full_name(data),
                "tripId": data.get("trip_id"),
                "mode": self._vmode.get(data["vid"], P.Mode.CLOUD).value,
                "speed_kmh": data.get("speed_kmh"), "rpm": data.get("rpm"),
                "throttle": data.get("throttle"), "load": data.get("load"),
                "coolant_c": data.get("coolant_c"), "fuel_lph": data.get("fuel_lph"),
                "limit_kmh": data.get("limit_kmh"),
                "lat": data.get("lat"), "lon": data.get("lon"),
                "ts": time.time(),
            }

    def _on_summary(self, sample: "zenoh.Sample") -> None:
        size = len(bytes(sample.payload))
        try:
            data = P.decode(sample.payload.to_string())
        except json.JSONDecodeError:
            return
        with self._lock:
            self._sum_msgs += 1
            self._sum_bytes += size
            self._actual_bytes += size
            if data.get("lat") is not None:
                self._last_pos[data["vid"]] = (data["lat"], data["lon"])
            # coarser live snapshot in EDGE (window aggregate every 15 s)
            self._current[data["vid"]] = {
                "vid": data["vid"], "did": data.get("did"), "name": _full_name(data),
                "tripId": data.get("trip_id"),
                "mode": self._vmode.get(data["vid"], P.Mode.CLOUD).value,
                "speed_kmh": data.get("avg_kmh"), "rpm": data.get("avg_rpm"),
                "lat": data.get("lat"), "lon": data.get("lon"),
                "ts": time.time(),
            }

    def _on_session(self, sample: "zenoh.Sample") -> None:
        try:
            summary = P.decode(sample.payload.to_string())
        except json.JSONDecodeError:
            return
        self._finalize_session(summary)

    # --- session report (LLM / Jakarta hand-off) ---
    def _finalize_session(self, summary: dict) -> None:
        scores = self._score(summary)
        flags = _bad_behaviours(summary)
        # issue a fine only for sustained speeding that gets caught
        if (summary.get("speeding_s", 0) > self.fine_min_speeding_s
                and random.random() < self.fine_catch_rate):
            flags.append("speeding")
        did = summary.get("did") or "UNKNOWN"

        # structured trip record for the Jakarta stats/registry service
        trip = {
            "tripId": summary.get("trip_id"),
            "endedAt": time.time(),
            "driver": {
                "did": did,
                "name": summary.get("driver_name") or did,
                "surname": summary.get("driver_surname", ""),
                "cf": summary.get("driver_cf", ""),
                "nationality": summary.get("driver_nationality", ""),
            },
            "vehicle": {
                "vid": summary.get("vid"),
                **(summary.get("vehicle") or {}),
            },
            "session": summary,
            "scores": scores,
            "flags": flags,
        }
        log.info("TRIP %s driver=%s vid=%s safety=%s eco=%s",
                 trip["tripId"], did, summary.get("vid"), scores["safety"], scores["eco"])
        # Ingest into the Jakarta service (best-effort, off the Zenoh thread).
        if self.ingest_url:
            threading.Thread(target=self._post_ingest, args=(trip,), daemon=True).start()

    def _post_ingest(self, trip: dict) -> None:
        data = json.dumps(trip).encode("utf-8")
        req = urllib.request.Request(
            self.ingest_url, data=data,
            headers={"Content-Type": "application/json"}, method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                log.info("trip %s ingested -> %s %d",
                         trip.get("tripId"), self.ingest_url, resp.status)
        except (urllib.error.URLError, OSError) as exc:
            log.warning("trip ingest failed (%s): %s", self.ingest_url, exc)

    @staticmethod
    def _score(s: dict) -> dict:
        """Deterministic eco/safety scores; the LLM only narrates these."""
        dur_min = max(s.get("dur_min", 0.0), 1e-6)
        events_per_min = (s.get("harsh_accel", 0) + s.get("harsh_brake", 0)) / dur_min
        safety = max(0.0, 100.0 - 12.0 * events_per_min - 0.5 * s.get("speeding_s", 0))
        eco = max(0.0, 100.0 - 4.0 * s.get("l_per_100km", 0.0)
                  - 0.4 * s.get("overrev_s", 0.0) - 0.2 * s.get("idle_s", 0.0))
        return {"safety": round(min(100.0, safety), 1), "eco": round(min(100.0, eco), 1)}

    # --- congestion control + stats ---
    def _control_tick(self) -> None:
        """Keep as many vehicles in CLOUD as the channel allows (up to
        cloud_saturation of the limit); offload the overflow to EDGE. Older
        vehicles keep CLOUD priority, so new ones spill to EDGE when saturated."""
        changes = []
        with self._lock:
            avg = max(self._avg_raw_bytes, 1.0)
            # how many 1 Hz CLOUD streams fit under the saturation threshold
            max_cloud = max(1, int(self.bw_limit * self.cloud_saturation / (avg * P.CLOUD_HZ)))
            order = sorted(self._active, key=lambda v: self._join_seq.get(v, 0))
            for i, vid in enumerate(order):
                want = P.Mode.CLOUD if i < max_cloud else P.Mode.EDGE
                if self._vmode.get(vid) != want:
                    self._vmode[vid] = want
                    changes.append((vid, want))
                if vid in self._current:
                    self._current[vid]["mode"] = want.value
            cloud = min(len(order), max_cloud)
            edge = max(0, len(order) - max_cloud)

        for vid, want in changes:
            self._publish_vehicle_mode(vid, want)
        if changes:
            log.info("MODE reassign: %d cloud + %d edge (max_cloud=%d, avg_raw=%.0fB) [%d changed]",
                     cloud, edge, max_cloud, avg, len(changes))

    def _stats_tick(self, dt: float) -> None:
        with self._lock:
            active = len(self._active)
            cloud = sum(1 for v in self._active if self._vmode.get(v) == P.Mode.CLOUD)
            edge = active - cloud
            raw_msgs, raw_bytes = self._raw_msgs, self._raw_bytes
            sum_msgs, sum_bytes = self._sum_msgs, self._sum_bytes
            self._baseline_bytes += active * self._avg_raw_bytes * P.CLOUD_HZ * dt
            baseline, actual = self._baseline_bytes, self._actual_bytes
            self._raw_msgs = self._raw_bytes = 0
            self._sum_msgs = self._sum_bytes = 0

        total_bps = (raw_bytes + sum_bytes) / dt
        saved_bytes = max(0.0, baseline - actual)
        saved_j = saved_bytes / 1e6 * self.joules_per_mb
        log.info(
            "[stats] cloud=%d edge=%d active=%d raw=%d/%.0fB/s summary=%d in=%.0fB/s "
            "saved=%.2fMB ~%.1fJ",
            cloud, edge, active, raw_msgs, raw_bytes / dt, sum_msgs,
            total_bps, saved_bytes / 1e6, saved_j,
        )

    def _post_active(self) -> None:
        """Push the current 'who is driving now' map to the Jakarta service."""
        if not self.active_url:
            return
        with self._lock:
            payload = list(self._current.values())
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            self.active_url, data=data,
            headers={"Content-Type": "application/json"}, method="POST",
        )
        try:
            urllib.request.urlopen(req, timeout=5).close()
        except (urllib.error.URLError, OSError) as exc:
            log.debug("active push failed (%s): %s", self.active_url, exc)

    def _active_loop(self) -> None:
        """Evaluate the mode and push live telemetry frequently, independent of
        the (slower) stats cadence, so CLOUD<->EDGE switches promptly."""
        while not self._stop.is_set():
            self._control_tick()
            self._post_active()
            self._stop.wait(self.active_interval_s)

    # --- lifecycle ---
    def run(self) -> None:
        signal.signal(signal.SIGINT, lambda *_: self._stop.set())
        signal.signal(signal.SIGTERM, lambda *_: self._stop.set())

        self._session = zenoh.open(build_client_config(self.router))
        s = self._session
        log.info("server connected to %s", self.router)

        subs = [
            s.liveliness().declare_subscriber(P.ALIVE_WILD, self._on_liveliness, history=True),
            s.declare_subscriber(P.RAW_WILD, self._on_raw),
            s.declare_subscriber(P.SUMMARY_WILD, self._on_summary),
            s.declare_subscriber(P.SESSION_WILD, self._on_session),
        ]
        # answer each vehicle's per-vehicle mode query (core/fleet/{vid}/mode)
        queryable = s.declare_queryable(P.MODE_WILD, self._on_mode_query)

        threading.Thread(target=self._active_loop, name="active-push", daemon=True).start()

        log.info("server ready: bw_limit=%.0f B/s, cloud_saturation=%.0f%%",
                 self.bw_limit, self.cloud_saturation * 100)
        last = time.monotonic()
        try:
            while not self._stop.is_set():
                self._stop.wait(self.stats_interval_s)
                now = time.monotonic()
                # mode is evaluated in the faster active loop; here we just log stats
                self._stats_tick(max(now - last, 1e-6))
                last = now
        finally:
            queryable.undeclare()
            for sub in subs:
                sub.undeclare()
            s.close()
            log.info("server stopped")


def main() -> None:
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO"),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    zenoh.init_log_from_env_or("error")
    router = os.getenv("ZENOH_ROUTER", "tcp/localhost:7447")
    FleetServer(router).run()


if __name__ == "__main__":
    main()
