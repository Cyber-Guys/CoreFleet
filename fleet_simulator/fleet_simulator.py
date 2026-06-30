"""
Fleet runner.

Models a car-sharing operation:

  * a pool of **cars** (assets) that grows over the simulation;
  * a pool of **drivers** (people), each with a baseline driving style;
  * **trips**: a driver takes an available car for a finite trip, then returns
    it; the same driver may later take another car (or the same one).

Each active trip runs as an independent :class:`VehicleAgent` streaming telemetry
to Zenoh. When a trip ends the car and driver return to their pools, and the
session is published (tagged with the driver) so the server can build a
driver-centric report and track behaviour across that driver's trips.
"""
import logging
import os
import random
import signal
import string
import threading
import time
import uuid
from dataclasses import dataclass, replace

from .agent import VehicleAgent
from .config import PROFILES
from .types import Driver
from .vehicle_simulator import VehicleSimulator

log = logging.getLogger(__name__)

# a small roster of names so reports read like people, not ids
_NAMES = [
    "Marco", "Giulia", "Luca", "Sara", "Paolo", "Elena", "Davide", "Chiara",
    "Andrea", "Federica", "Matteo", "Alessia", "Simone", "Martina", "Roberto",
    "Valentina", "Stefano", "Ilaria", "Francesco", "Beatrice",
]


@dataclass
class Car:
    vid: str
    lat: float
    lon: float
    in_use: bool = False


def _jitter_profile(p) -> object:
    """A per-trip variation of a driver's baseline style, so successive trips
    differ and trends (improved / worsened) actually emerge."""
    def s(x, lo, hi):
        return max(lo, min(hi, x * random.uniform(0.82, 1.18)))
    return replace(
        p,
        accel_peak=s(p.accel_peak, 1.0, 6.0),
        brake_peak=s(p.brake_peak, 1.0, 6.0),
        shift_rpm=int(s(p.shift_rpm, 2000, 6000)),
        overshoot=s(p.overshoot, 0.0, 0.5),
        cold_aggression=s(p.cold_aggression, 0.0, 1.0),
        jerk_noise=s(p.jerk_noise, 0.05, 1.2),
        reaction_s=s(p.reaction_s, 1.2, 5.0),
    )


class FleetSimulator:
    def __init__(
        self,
        router: str,
        start_cars: int,
        max_cars: int,
        num_drivers: int,
        profiles: list,
        duration_s: int,
        spawn_interval_s: float = 2.0,
        trip_min_s: float = 25.0,
        trip_max_s: float = 70.0,
    ):
        self.router = router
        self.start_cars = start_cars
        self.max_cars = max_cars
        self.num_drivers = num_drivers
        self.profiles = list(profiles)
        self.duration_s = duration_s
        self.spawn_interval_s = spawn_interval_s
        self.trip_min_s = trip_min_s
        self.trip_max_s = trip_max_s

        self.cars: list[Car] = []
        self.drivers: list[Driver] = []
        self.idle_drivers: set[str] = set()
        self.busy_cars: dict[str, Car] = {}     # trip_id -> car
        self.busy_drivers: dict[str, str] = {}  # trip_id -> did
        self.agents: list[VehicleAgent] = []

        self._used_vids: set[str] = set()
        self._stop = threading.Event()

    # --- pools --------------------------------------------------------------
    def _build_drivers(self) -> None:
        names = random.sample(_NAMES, min(self.num_drivers, len(_NAMES)))
        for i in range(self.num_drivers):
            did = f"DRV-{i + 1:02d}"
            name = names[i] if i < len(names) else f"Driver{i + 1}"
            profile = PROFILES[random.choice(self.profiles)]
            self.drivers.append(Driver(did=did, name=name, profile=profile))
            self.idle_drivers.add(did)
        log.info("driver pool: %d drivers", len(self.drivers))

    def add_car(self) -> None:
        if len(self.cars) >= self.max_cars:
            return
        vid = self._generate_vehicle_id()
        while vid in self._used_vids:
            vid = self._generate_vehicle_id()
        self._used_vids.add(vid)
        lat, lon = random.uniform(39.1, 39.3), random.uniform(9.0, 9.2)
        self.cars.append(Car(vid=vid, lat=lat, lon=lon))
        log.info("added car %s [%d/%d]", vid, len(self.cars), self.max_cars)

    def _generate_vehicle_id(self) -> str:
        return (
            "".join(random.choices(string.ascii_uppercase, k=2)) +
            "".join(random.choices(string.digits, k=3)) +
            "".join(random.choices(string.ascii_uppercase, k=2))
        )

    # --- trips --------------------------------------------------------------
    def _driver(self, did: str) -> Driver:
        return next(d for d in self.drivers if d.did == did)

    def _start_trip(self) -> None:
        free_cars = [c for c in self.cars if not c.in_use]
        if not self.idle_drivers or not free_cars:
            return

        did = random.choice(list(self.idle_drivers))
        car = random.choice(free_cars)
        driver = self._driver(did)
        trip_id = uuid.uuid4().hex[:8]

        sim = VehicleSimulator(
            vid=car.vid,
            init_pos=(car.lat, car.lon),
            profile=_jitter_profile(driver.profile),
            did=driver.did,
            driver_name=driver.name,
            trip_id=trip_id,
        )
        agent = VehicleAgent(sim, self.router, trip_s=random.uniform(self.trip_min_s, self.trip_max_s))

        self.idle_drivers.discard(did)
        car.in_use = True
        self.busy_cars[trip_id] = car
        self.busy_drivers[trip_id] = did
        self.agents.append(agent)
        agent.start()
        log.info("trip %s: %s (%s) drives %s", trip_id, driver.name, did, car.vid)

    def _reap(self) -> None:
        """Return cars and drivers from finished trips to their pools."""
        for agent in [a for a in self.agents if a.done.is_set()]:
            agent.join(timeout=0.1)
            tid = agent.trip_id
            car = self.busy_cars.pop(tid, None)
            if car is not None:
                # the car stays where the trip left it
                car.lat, car.lon = agent.sim.st.lat, agent.sim.st.lon
                car.in_use = False
            did = self.busy_drivers.pop(tid, None)
            if did is not None:
                self.idle_drivers.add(did)
            self.agents.remove(agent)

    # --- lifecycle ----------------------------------------------------------
    def run(self) -> None:
        log.info(
            "fleet starting: %d->%d cars, %d drivers, %ss, router=%s",
            self.start_cars, self.max_cars, self.num_drivers, self.duration_s, self.router,
        )

        signal.signal(signal.SIGINT, self._on_signal)
        signal.signal(signal.SIGTERM, self._on_signal)

        self._build_drivers()
        for _ in range(self.start_cars):
            self.add_car()

        started = time.monotonic()
        last_car_add = started
        while not self._stop.is_set():
            now = time.monotonic()
            if now - started >= self.duration_s:
                break

            self._reap()

            # the fleet grows over time
            if len(self.cars) < self.max_cars and now - last_car_add >= self.spawn_interval_s:
                self.add_car()
                last_car_add = now

            # keep every available car on the road while drivers are free
            while self.idle_drivers and any(not c.in_use for c in self.cars):
                self._start_trip()

            self._stop.wait(0.5)

        self.shutdown()

    def shutdown(self) -> None:
        log.info("fleet stopping: %d active trips", len(self.agents))
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
    start_cars = _env_int("START_VEHICLES", 3)
    max_cars = _env_int("MAX_VEHICLES", 15)
    num_drivers = _env_int("NUM_DRIVERS", max_cars)
    duration_s = _env_int("DURATION_S", 300)
    spawn_interval = float(os.getenv("SPAWN_INTERVAL_S", "2"))
    trip_min = float(os.getenv("TRIP_MIN_S", "25"))
    trip_max = float(os.getenv("TRIP_MAX_S", "70"))

    sim = FleetSimulator(
        router=router,
        start_cars=start_cars,
        max_cars=max_cars,
        num_drivers=num_drivers,
        profiles=list(PROFILES.keys()),
        duration_s=duration_s,
        spawn_interval_s=spawn_interval,
        trip_min_s=trip_min,
        trip_max_s=trip_max,
    )
    sim.run()


if __name__ == "__main__":
    main()
