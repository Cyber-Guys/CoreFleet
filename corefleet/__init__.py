"""
CoreFleet shared library.

Holds the Zenoh wire protocol (key expressions, modes, payload codec) and the
client used by edge devices to stream telemetry. Imported by both the vehicle
simulator (publisher side) and the fleet server (subscriber/controller side).
"""
from . import protocol
from .client import VehicleClient

__all__ = ["protocol", "VehicleClient"]
