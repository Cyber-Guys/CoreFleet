"""
VehicleAgent: one simulated edge device.

Couples a :class:`VehicleSimulator` (physics) with a :class:`VehicleClient`
(Zenoh transport) and runs the per-vehicle streaming loop in its own thread:

    * step the physics at ~1 Hz wall-clock;
    * in CLOUD mode, publish a raw sample every tick;
    * in EDGE mode, publish a window summary every WINDOW_S and reset the window;
    * on shutdown, flush a final window (if pending) and publish the full-session
      aggregate that drives the end-of-session report.
"""
from __future__ import annotations

import logging
import threading
import time

from corefleet import VehicleClient
from corefleet import protocol as P

from .vehicle_simulator import VehicleSimulator

log = logging.getLogger(__name__)


class VehicleAgent:
    def __init__(
        self,
        sim: VehicleSimulator,
        router: str,
        hz: float = P.CLOUD_HZ,
        window_s: float = P.WINDOW_S,
    ) -> None:
        self.sim = sim
        self.vid = sim.vid
        self.client = VehicleClient(sim.vid, router)
        self.dt = 1.0 / hz
        self.window_s = window_s
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        self._thread = threading.Thread(
            target=self._run, name=f"veh-{self.vid}", daemon=True
        )
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()

    def join(self, timeout: float | None = None) -> None:
        if self._thread is not None:
            self._thread.join(timeout)

    def _run(self) -> None:
        try:
            self.client.open()
        except Exception as exc:
            log.error("vehicle %s failed to connect: %s", self.vid, exc)
            return

        t = 0.0
        last_flush = 0.0
        try:
            while not self._stop.is_set():
                tick_start = time.monotonic()

                self.sim.step(self.dt)
                t += self.dt

                if self.client.mode == P.Mode.CLOUD:
                    self.client.publish_raw(self.sim.raw_sample(t))
                elif t - last_flush >= self.window_s:
                    self.client.publish_summary(self.sim.window_summary())
                    self.sim.reset_window()
                    last_flush = t

                # hold ~1 Hz wall-clock so sim seconds track real seconds
                elapsed = time.monotonic() - tick_start
                self._stop.wait(max(0.0, self.dt - elapsed))
        finally:
            self._shutdown(t, last_flush)

    def _shutdown(self, t: float, last_flush: float) -> None:
        try:
            if self.client.mode == P.Mode.EDGE and t - last_flush > 0:
                self.client.publish_summary(self.sim.window_summary())
            self.client.publish_session(self.sim.session_summary())
        except Exception as exc:
            log.warning("vehicle %s final publish failed: %s", self.vid, exc)
        self.client.close()
