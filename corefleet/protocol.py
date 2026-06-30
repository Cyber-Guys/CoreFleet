"""
CoreFleet Zenoh protocol.

Single source of truth for key expressions, transmission modes and the payload
codec shared by vehicles and the server. `vid` is the vehicle id (licence plate).

Key space (all under ``core/fleet``):

    core/fleet/{vid}/alive     liveliness token  V -> S   presence (auto DELETE on disconnect)
    core/fleet/{vid}/raw       JSON              V -> S   CLOUD telemetry, 1 Hz
    core/fleet/{vid}/summary   JSON              V -> S   EDGE aggregate, every WINDOW_S
    core/fleet/{vid}/session   JSON              V -> S   final full-session aggregate, on shutdown
    core/fleet/mode            "CLOUD"|"EDGE"    S -> V   global mode (published + queryable)
"""
from __future__ import annotations

import json
from enum import Enum

KEY_ROOT = "core/fleet"

#: Cadence of CLOUD raw samples and of EDGE summary windows.
CLOUD_HZ = 1.0
WINDOW_S = 15.0


class Mode(str, Enum):
    """Transmission mode dictated by the server."""
    CLOUD = "CLOUD"
    EDGE = "EDGE"


# --- per-vehicle keys ---
def alive_key(vid: str) -> str:
    return f"{KEY_ROOT}/{vid}/alive"


def raw_key(vid: str) -> str:
    return f"{KEY_ROOT}/{vid}/raw"


def summary_key(vid: str) -> str:
    return f"{KEY_ROOT}/{vid}/summary"


def session_key(vid: str) -> str:
    return f"{KEY_ROOT}/{vid}/session"


# --- server-side wildcards ---
ALIVE_WILD = f"{KEY_ROOT}/*/alive"
RAW_WILD = f"{KEY_ROOT}/*/raw"
SUMMARY_WILD = f"{KEY_ROOT}/*/summary"
SESSION_WILD = f"{KEY_ROOT}/*/session"

#: Global mode key (server publishes here and answers queries on it).
MODE_KEY = f"{KEY_ROOT}/mode"


def vid_from_key(key: str) -> str:
    """Extract the vehicle id from a ``core/fleet/{vid}/...`` key expression."""
    parts = key.split("/")
    # core / fleet / {vid} / leaf
    return parts[2] if len(parts) >= 4 else ""


# --- payload codec ---
def encode(obj: dict) -> bytes:
    return json.dumps(obj, separators=(",", ":")).encode("utf-8")


def decode(payload: str | bytes) -> dict:
    if isinstance(payload, bytes):
        payload = payload.decode("utf-8")
    return json.loads(payload)
