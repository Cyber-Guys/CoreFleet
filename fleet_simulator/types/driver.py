"""
Conducente (driver).

A driver is the person who gets scored. During a simulation a driver takes a
car for a trip and may later take another car (or the same one), so their
behaviour can be followed across trips. The driving style belongs to the
driver, not to the car.
"""
from dataclasses import dataclass

from .driver_profile import DriverProfile


@dataclass
class Driver:
    did: str           # e.g. "DRV-07"
    name: str
    surname: str
    cf: str            # codice fiscale (fake but plausible)
    nationality: str
    profile: DriverProfile   # the driver's baseline style
