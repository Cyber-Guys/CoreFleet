"""
VehicleClient: the edge-device side of the CoreFleet protocol.

Wraps a Zenoh session and exposes the few operations a vehicle agent needs:

    * declare presence with a liveliness token (``core/fleet/{vid}/alive``);
    * stream CLOUD telemetry (``raw``) or EDGE aggregates (``summary``);
    * publish the final session aggregate on shutdown (``session``);
    * follow the server-dictated transmission mode, including an initial query
      so a vehicle that joins mid-run learns the current mode immediately.

The class is thread-safe for reading :attr:`mode`; the mode subscriber runs on
a Zenoh background thread and updates it under a lock.
"""
from __future__ import annotations

import json
import logging
import threading
from typing import Callable, Optional

import zenoh

from . import protocol as P

log = logging.getLogger(__name__)


def build_client_config(router: str) -> zenoh.Config:
    """Zenoh client config connecting to a single router, no multicast scouting."""
    config = zenoh.Config()
    config.insert_json5("mode", json.dumps("client"))
    config.insert_json5("connect/endpoints", json.dumps([router]))
    config.insert_json5("scouting/multicast/enabled", json.dumps(False))
    return config


class VehicleClient:
    def __init__(
        self,
        vid: str,
        router: str,
        on_mode: Optional[Callable[[P.Mode], None]] = None,
    ) -> None:
        self.vid = vid
        self.router = router
        self._on_mode = on_mode

        self._mode = P.Mode.CLOUD
        self._lock = threading.Lock()

        self._session: Optional[zenoh.Session] = None
        self._token = None
        self._pub_raw = None
        self._pub_summary = None
        self._pub_session = None
        self._mode_sub = None

    # --- lifecycle ---
    def open(self) -> None:
        self._session = zenoh.open(build_client_config(self.router))
        s = self._session

        # presence: liveliness token, auto-undeclared if the device drops
        self._token = s.liveliness().declare_token(P.alive_key(self.vid))

        # telemetry publishers
        self._pub_raw = s.declare_publisher(P.raw_key(self.vid))
        self._pub_summary = s.declare_publisher(P.summary_key(self.vid))
        self._pub_session = s.declare_publisher(P.session_key(self.vid))

        # follow this vehicle's own mode assignment, then resolve it for boot
        self._mode_sub = s.declare_subscriber(P.mode_key(self.vid), self._on_mode_sample)
        self._query_initial_mode()

        log.info("vehicle %s online (mode=%s)", self.vid, self._mode.value)

    def close(self) -> None:
        for entity in (
            self._mode_sub,
            self._pub_raw,
            self._pub_summary,
            self._pub_session,
            self._token,
        ):
            if entity is not None:
                try:
                    entity.undeclare()
                except Exception:
                    pass
        if self._session is not None:
            try:
                self._session.close()
            except Exception:
                pass
        log.info("vehicle %s offline", self.vid)

    def __enter__(self) -> "VehicleClient":
        self.open()
        return self

    def __exit__(self, *_exc) -> None:
        self.close()

    # --- mode ---
    @property
    def mode(self) -> P.Mode:
        with self._lock:
            return self._mode

    def _set_mode(self, mode: P.Mode) -> None:
        with self._lock:
            changed = mode != self._mode
            self._mode = mode
        if changed:
            log.info("vehicle %s switched to %s", self.vid, mode.value)
            if self._on_mode is not None:
                self._on_mode(mode)

    def _on_mode_sample(self, sample: "zenoh.Sample") -> None:
        try:
            self._set_mode(P.Mode(sample.payload.to_string().strip()))
        except ValueError:
            log.warning("vehicle %s got invalid mode payload", self.vid)

    def _query_initial_mode(self) -> None:
        try:
            for reply in self._session.get(P.mode_key(self.vid), timeout=2.0):
                if reply.ok is not None:
                    try:
                        self._set_mode(P.Mode(reply.ok.payload.to_string().strip()))
                        return
                    except ValueError:
                        continue
        except Exception as exc:  # no server queryable yet -> keep default
            log.debug("vehicle %s initial mode query failed: %s", self.vid, exc)

    # --- telemetry ---
    def publish_raw(self, sample: dict) -> None:
        self._pub_raw.put(P.encode(sample), encoding=zenoh.Encoding.APPLICATION_JSON)

    def publish_summary(self, summary: dict) -> None:
        self._pub_summary.put(P.encode(summary), encoding=zenoh.Encoding.APPLICATION_JSON)

    def publish_session(self, summary: dict) -> None:
        self._pub_session.put(P.encode(summary), encoding=zenoh.Encoding.APPLICATION_JSON)
