"""
Conducente (driver).

A driver is the *person* who is scored. Over a simulation a driver takes a car
from the fleet for a finite trip, then may take another car (or the same one)
for a later trip — so behaviour can be tracked across trips (recidivist /
improved / unchanged). The driving style lives here, on the person, not the car.
"""
from dataclasses import dataclass

from .driver_profile import DriverProfile


@dataclass
class Driver:
    did: str          # e.g. "DRV-07"
    name: str
    profile: DriverProfile   # the driver's baseline style
