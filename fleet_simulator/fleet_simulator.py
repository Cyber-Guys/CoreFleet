"""
Fleet runner.

Spawns simulated vehicles, each as an independent :class:`VehicleAgent` that
streams telemetry to the Zenoh router. Vehicles are added gradually (a new one
every ``spawn_interval_s``) up to ``max_vehicles`` so the fleet ramps into
network congestion and the server can demonstrate the CLOUD -> EDGE switch.
"""
import logging
import os
import random
import signal
import string
import threading
import time

from .agent import VehicleAgent
from .config import PROFILES
from .vehicle_simulator import VehicleSimulator

log = logging.getLogger(__name__)


class FleetSimulator:
    def __init__(
        self,
        router: str,
        start_num_vehicles: int,
        max_vehicles: int,
        profiles: list,
        duration_s: int,
        spawn_interval_s: float = 8.0,
    ):
        self.router = router
        self.start_num_vehicles = start_num_vehicles
        self.max_vehicles = max_vehicles
        self.profiles = list(profiles)
        self.duration_s = duration_s
        self.spawn_interval_s = spawn_interval_s

        self.agents: list[VehicleAgent] = []
        self.vehicles_id: set[str] = set()
        self._stop = threading.Event()

    # --- vehicle factory ---
    def add_vehicle(self) -> None:
        if len(self.agents) >= self.max_vehicles:
            return

        vid = self._generate_vehicle_id()
        while vid in self.vehicles_id:
            vid = self._generate_vehicle_id()
        self.vehicles_id.add(vid)

        profile_name = random.choice(self.profiles)
        sim = VehicleSimulator(vid, self._gen_init_pos(), PROFILES[profile_name])

        agent = VehicleAgent(sim, self.router)
        self.agents.append(agent)
        agent.start()
        log.info(
            "spawned vehicle %s (profile=%s) [%d/%d]",
            vid, profile_name, len(self.agents), self.max_vehicles,
        )

    def _generate_vehicle_id(self) -> str:
        return (
            "".join(random.choices(string.ascii_uppercase, k=2)) +
            "".join(random.choices(string.digits, k=3)) +
            "".join(random.choices(string.ascii_uppercase, k=2))
        )

    def _gen_init_pos(self) -> tuple[float, float]:
        # posizione iniziale casuale intorno a Cagliari
        return (random.uniform(39.1, 39.3), random.uniform(9.0, 9.2))

    # --- lifecycle ---
    def run(self) -> None:
        log.info(
            "fleet starting: %d->%d vehicles over %ss, router=%s",
            self.start_num_vehicles, self.max_vehicles, self.duration_s, self.router,
        )

        signal.signal(signal.SIGINT, self._on_signal)
        signal.signal(signal.SIGTERM, self._on_signal)

        for _ in range(self.start_num_vehicles):
            self.add_vehicle()

        started = time.monotonic()
        last_spawn = started
        while not self._stop.is_set():
            now = time.monotonic()
            if now - started >= self.duration_s:
                break
            if len(self.agents) < self.max_vehicles and now - last_spawn >= self.spawn_interval_s:
                self.add_vehicle()
                last_spawn = now
            self._stop.wait(0.5)

        self.shutdown()

    def shutdown(self) -> None:
        log.info("fleet stopping: %d vehicles", len(self.agents))
        for agent in self.agents:
            agent.stop()
        for agent in self.agents:
            agent.join(timeout=5.0)
        log.info("fleet stopped")

    def _on_signal(self, _signum, _frame) -> None:
        self._stop.set()


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, default))
    except ValueError:
        return default


def main() -> None:
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO"),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    seed = os.getenv("SEED") or "".join(random.choices("0123456789abcdef", k=32))
    random.seed(seed)
    log.info("using seed %s", seed)

    router = os.getenv("ZENOH_ROUTER", "tcp/localhost:7447")
    start_num = _env_int("START_VEHICLES", 3)
    max_vehicles = _env_int("MAX_VEHICLES", 15)
    duration_s = _env_int("DURATION_S", 300)
    spawn_interval = float(os.getenv("SPAWN_INTERVAL_S", "8"))

    sim = FleetSimulator(
        router=router,
        start_num_vehicles=start_num,
        max_vehicles=max_vehicles,
        profiles=list(PROFILES.keys()),
        duration_s=duration_s,
        spawn_interval_s=spawn_interval,
    )
    sim.run()


if __name__ == "__main__":
    main()
