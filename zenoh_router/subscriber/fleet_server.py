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
import signal
import threading
import time

import zenoh

from corefleet import protocol as P
from corefleet.client import build_client_config

log = logging.getLogger(__name__)


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, default))
    except ValueError:
        return default


class FleetServer:
    def __init__(self, router: str) -> None:
        self.router = router

        # congestion thresholds (bytes/s of projected CLOUD traffic), hysteresis
        self.bw_high = _env_float("BW_LIMIT_BYTES_S", 4000.0)
        self.bw_low = self.bw_high * _env_float("BW_HYSTERESIS", 0.6)
        self.joules_per_mb = _env_float("JOULES_PER_MB", 1100.0)
        self.stats_interval_s = _env_float("STATS_INTERVAL_S", 5.0)

        self._lock = threading.Lock()
        self._active: set[str] = set()
        self._last_pos: dict[str, tuple[float, float]] = {}
        self._mode = P.Mode.CLOUD

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
        self._mode_pub = None

    # --- mode broadcasting ---
    def _publish_mode(self) -> None:
        if self._mode_pub is not None:
            self._mode_pub.put(self._mode.value, encoding=zenoh.Encoding.TEXT_PLAIN)

    def _on_mode_query(self, query: "zenoh.Query") -> None:
        with self._lock:
            mode = self._mode.value
        query.reply(P.MODE_KEY, mode, encoding=zenoh.Encoding.TEXT_PLAIN)
        query.drop()

    # --- presence (liveliness) ---
    def _on_liveliness(self, sample: "zenoh.Sample") -> None:
        vid = P.vid_from_key(str(sample.key_expr))
        if not vid:
            return
        with self._lock:
            if sample.kind == zenoh.SampleKind.PUT:
                self._active.add(vid)
                log.info("[+] vehicle online: %s (active=%d)", vid, len(self._active))
            else:  # DELETE -> token dropped
                self._active.discard(vid)
                self._last_pos.pop(vid, None)
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

    def _on_session(self, sample: "zenoh.Sample") -> None:
        try:
            summary = P.decode(sample.payload.to_string())
        except json.JSONDecodeError:
            return
        self._finalize_session(summary)

    # --- session report (LLM / Jakarta hand-off) ---
    def _finalize_session(self, summary: dict) -> None:
        report = {
            "vid": summary.get("vid"),
            "ended_at": time.time(),
            "session": summary,
            "scores": self._score(summary),
        }
        # Hand-off point for the Jakarta EE / LLM report service. For now we emit
        # the structured payload; a downstream consumer can pick it up.
        log.info("SESSION REPORT %s", json.dumps(report, separators=(",", ":")))

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
        with self._lock:
            projected = len(self._active) * self._avg_raw_bytes * P.CLOUD_HZ
            new_mode = self._mode
            if self._mode == P.Mode.CLOUD and projected > self.bw_high:
                new_mode = P.Mode.EDGE
            elif self._mode == P.Mode.EDGE and projected < self.bw_low:
                new_mode = P.Mode.CLOUD
            changed = new_mode != self._mode
            self._mode = new_mode

        if changed:
            log.warning(
                "MODE -> %s (active=%d, projected=%.0f B/s, high=%.0f low=%.0f)",
                new_mode.value, len(self._active), projected, self.bw_high, self.bw_low,
            )
            self._publish_mode()

    def _stats_tick(self, dt: float) -> None:
        with self._lock:
            active = len(self._active)
            raw_msgs, raw_bytes = self._raw_msgs, self._raw_bytes
            sum_msgs, sum_bytes = self._sum_msgs, self._sum_bytes
            mode = self._mode.value
            self._baseline_bytes += active * self._avg_raw_bytes * P.CLOUD_HZ * dt
            baseline, actual = self._baseline_bytes, self._actual_bytes
            self._raw_msgs = self._raw_bytes = 0
            self._sum_msgs = self._sum_bytes = 0

        total_bps = (raw_bytes + sum_bytes) / dt
        saved_bytes = max(0.0, baseline - actual)
        saved_j = saved_bytes / 1e6 * self.joules_per_mb
        log.info(
            "[stats] mode=%s active=%d raw=%d/%.0fB/s summary=%d in=%.0fB/s "
            "saved=%.2fMB ~%.1fJ",
            mode, active, raw_msgs, raw_bytes / dt, sum_msgs,
            total_bps, saved_bytes / 1e6, saved_j,
        )

    # --- lifecycle ---
    def run(self) -> None:
        signal.signal(signal.SIGINT, lambda *_: self._stop.set())
        signal.signal(signal.SIGTERM, lambda *_: self._stop.set())

        self._session = zenoh.open(build_client_config(self.router))
        s = self._session
        log.info("server connected to %s", self.router)

        self._mode_pub = s.declare_publisher(P.MODE_KEY)
        subs = [
            s.liveliness().declare_subscriber(P.ALIVE_WILD, self._on_liveliness, history=True),
            s.declare_subscriber(P.RAW_WILD, self._on_raw),
            s.declare_subscriber(P.SUMMARY_WILD, self._on_summary),
            s.declare_subscriber(P.SESSION_WILD, self._on_session),
        ]
        queryable = s.declare_queryable(P.MODE_KEY, self._on_mode_query)
        self._publish_mode()  # announce initial CLOUD mode

        log.info("server ready: bw_high=%.0f bw_low=%.0f B/s", self.bw_high, self.bw_low)
        last = time.monotonic()
        try:
            while not self._stop.is_set():
                self._stop.wait(self.stats_interval_s)
                now = time.monotonic()
                self._control_tick()
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
