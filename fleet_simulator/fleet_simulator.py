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

# small rosters so drivers read like people, not ids
_NAMES = [
    "Marco", "Giulia", "Luca", "Sara", "Paolo", "Elena", "Davide", "Chiara",
    "Andrea", "Federica", "Matteo", "Alessia", "Simone", "Martina", "Roberto",
    "Valentina", "Stefano", "Ilaria", "Francesco", "Beatrice",
]
_SURNAMES = [
    "Rossi", "Russo", "Ferrari", "Esposito", "Bianchi", "Romano", "Colombo",
    "Ricci", "Marino", "Greco", "Bruno", "Gallo", "Conti", "De Luca", "Mancini",
    "Costa", "Giordano", "Rizzo", "Lombardi", "Moretti",
]
_NATIONALITIES = [
    "Italia", "Italia", "Italia", "Italia", "Romania", "Albania",
    "Marocco", "Germania", "Francia", "Spagna",
]
_CF_CONS = "BCDFGHJKLMNPRSTVWXYZ"


def _fake_cf(name: str, surname: str) -> str:
    """A plausible-looking (not valid) codice fiscale."""
    def trip3(s):
        cons = [c for c in s.upper() if c in _CF_CONS]
        return "".join((cons + ["X", "X", "X"])[:3])
    digits = "".join(random.choices("0123456789", k=2))
    tail = "".join(random.choices(string.ascii_uppercase + string.digits, k=8))
    return f"{trip3(surname)}{trip3(name)}{digits}{tail}"


@dataclass
class Car:
    vid: str
    lat: float
    lon: float
    odo_km: float = 0.0
    fuel_pct: float = 100.0
    oil_pct: float = 100.0
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
        profiles: list,
        duration_s: int,
        spawn_interval_s: float = 2.0,
        trip_min_s: float = 25.0,
        trip_max_s: float = 70.0,
        reconfirm_rate: float = 0.5,
        satisfaction_rate: float = 0.6,
    ):
        self.router = router
        self.start_cars = start_cars
        self.max_cars = max_cars
        self.profiles = list(profiles)
        self.duration_s = duration_s
        self.spawn_interval_s = spawn_interval_s
        self.trip_min_s = trip_min_s
        self.trip_max_s = trip_max_s
        # chance a free car goes to a returning (satisfied) customer vs a new one
        self.reconfirm_rate = reconfirm_rate
        # chance a driver is happy with the trip and may come back
        self.satisfaction_rate = satisfaction_rate

        self.cars: list[Car] = []
        self.drivers: dict[str, Driver] = {}    # registry of everyone who drove (grows)
        self.idle_returning: set[str] = set()   # satisfied drivers available to reconfirm
        self.busy_cars: dict[str, Car] = {}     # trip_id -> car
        self.busy_drivers: dict[str, str] = {}  # trip_id -> did
        self.last_car: dict[str, str] = {}      # did -> last vid driven
        self.agents: list[VehicleAgent] = []

        self._used_vids: set[str] = set()
        self._driver_seq = 0
        self._stop = threading.Event()

    # --- pools --------------------------------------------------------------
    def _new_driver(self) -> Driver:
        """Mint a brand-new customer and add them to the registry."""
        self._driver_seq += 1
        did = f"DRV-{self._driver_seq:03d}"
        name = random.choice(_NAMES)
        surname = random.choice(_SURNAMES)
        driver = Driver(
            did=did, name=name, surname=surname,
            cf=_fake_cf(name, surname),
            nationality=random.choice(_NATIONALITIES),
            profile=PROFILES[random.choice(self.profiles)],
        )
        self.drivers[did] = driver
        return driver

    def _pick_driver(self, exclude_last_vid: str | None = None) -> Driver:
        """A returning satisfied customer (sometimes) or a new one. A returning
        driver is only reused if they did NOT last drive `exclude_last_vid`, so a
        car is never immediately handed back to the driver who just dropped it."""
        if self.idle_returning and random.random() < self.reconfirm_rate:
            cands = [d for d in self.idle_returning if self.last_car.get(d) != exclude_last_vid]
            if cands:
                did = random.choice(cands)
                self.idle_returning.discard(did)
                return self.drivers[did]
        return self._new_driver()

    def add_car(self) -> None:
        if len(self.cars) >= self.max_cars:
            return
        vid = self._generate_vehicle_id()
        while vid in self._used_vids:
            vid = self._generate_vehicle_id()
        self._used_vids.add(vid)
        lat, lon = random.uniform(39.1, 39.3), random.uniform(9.0, 9.2)
        self.cars.append(Car(
            vid=vid, lat=lat, lon=lon,
            odo_km=round(random.uniform(5_000, 90_000), 1),
            fuel_pct=round(random.uniform(35, 100), 1),
            oil_pct=round(random.uniform(60, 100), 1),
        ))
        log.info("added car %s [%d/%d]", vid, len(self.cars), self.max_cars)

    def _generate_vehicle_id(self) -> str:
        return (
            "".join(random.choices(string.ascii_uppercase, k=2)) +
            "".join(random.choices(string.digits, k=3)) +
            "".join(random.choices(string.ascii_uppercase, k=2))
        )

    # --- trips --------------------------------------------------------------
    def _start_trip(self) -> None:
        free_cars = [c for c in self.cars if not c.in_use]
        if not free_cars:
            return

        # pick the car first, then a driver who didn't just drive it
        car = random.choice(free_cars)
        driver = self._pick_driver(exclude_last_vid=car.vid)
        did = driver.did
        self.last_car[did] = car.vid
        trip_id = uuid.uuid4().hex[:8]

        sim = VehicleSimulator(
            vid=car.vid,
            init_pos=(car.lat, car.lon),
            profile=_jitter_profile(driver.profile),
            did=driver.did,
            driver_name=driver.name,
            driver_surname=driver.surname,
            driver_cf=driver.cf,
            driver_nationality=driver.nationality,
            trip_id=trip_id,
            odo_km=car.odo_km,
            fuel_pct=car.fuel_pct,
            oil_pct=car.oil_pct,
        )
        agent = VehicleAgent(sim, self.router, trip_s=random.uniform(self.trip_min_s, self.trip_max_s))

        car.in_use = True
        self.busy_cars[trip_id] = car
        self.busy_drivers[trip_id] = did
        self.agents.append(agent)
        agent.start()
        log.info("trip %s: %s %s (%s) drives %s [%d drivers seen]",
                 trip_id, driver.name, driver.surname, did, car.vid, len(self.drivers))

    def _reap(self) -> None:
        """Return cars and drivers from finished trips to their pools."""
        for agent in [a for a in self.agents if a.done.is_set()]:
            agent.join(timeout=0.1)
            tid = agent.trip_id
            car = self.busy_cars.pop(tid, None)
            bad_experience = False
            if car is not None:
                snap = agent.sim.vehicle_snapshot()
                bad_experience = bool(snap["lights"])
                # the car keeps its mileage/levels and stays where it was left
                car.lat, car.lon = agent.sim.st.lat, agent.sim.st.lon
                car.odo_km = snap["odo_km"]
                car.fuel_pct = snap["fuel_pct"]
                car.oil_pct = snap["oil_pct"]
                # depot service: refuel / top up oil when low
                if car.fuel_pct < 20:
                    car.fuel_pct = 100.0
                    log.info("car %s refuelled at depot", car.vid)
                if car.oil_pct < 25:
                    car.oil_pct = 100.0
                    log.info("car %s oil serviced at depot", car.vid)
                car.in_use = False

            did = self.busy_drivers.pop(tid, None)
            if did is not None:
                # satisfied customers may come back; a bad car experience (warning
                # lights at hand-back) makes them less likely to reconfirm
                chance = self.satisfaction_rate * (0.5 if bad_experience else 1.0)
                if random.random() < chance:
                    self.idle_returning.add(did)
            self.agents.remove(agent)

    # --- lifecycle ----------------------------------------------------------
    def run(self) -> None:
        log.info(
            "fleet starting: %d->%d cars, reconfirm=%.0f%% satisfaction=%.0f%%, %ss, router=%s",
            self.start_cars, self.max_cars, self.reconfirm_rate * 100,
            self.satisfaction_rate * 100, self.duration_s, self.router,
        )

        signal.signal(signal.SIGINT, self._on_signal)
        signal.signal(signal.SIGTERM, self._on_signal)

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

            # every free car gets a driver — a returning customer or a new one
            while any(not c.in_use for c in self.cars):
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
    start_cars = _env_int("START_VEHICLES", 6)
    max_cars = _env_int("MAX_VEHICLES", 15)
    duration_s = _env_int("DURATION_S", 300)
    spawn_interval = float(os.getenv("SPAWN_INTERVAL_S", "2"))
    trip_min = float(os.getenv("TRIP_MIN_S", "25"))
    trip_max = float(os.getenv("TRIP_MAX_S", "70"))
    # new customers arrive continuously; satisfied ones may reconfirm
    reconfirm_rate = float(os.getenv("RECONFIRM_RATE", "0.5"))
    satisfaction_rate = float(os.getenv("SATISFACTION_RATE", "0.6"))

    sim = FleetSimulator(
        router=router,
        start_cars=start_cars,
        max_cars=max_cars,
        profiles=list(PROFILES.keys()),
        duration_s=duration_s,
        spawn_interval_s=spawn_interval,
        trip_min_s=trip_min,
        trip_max_s=trip_max,
        reconfirm_rate=reconfirm_rate,
        satisfaction_rate=satisfaction_rate,
    )
    sim.run()


if __name__ == "__main__":
    main()
