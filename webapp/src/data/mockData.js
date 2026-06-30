/**
 * Mock fleet snapshot.
 *
 * Shape mirrors the real CoreFleet server state so the API layer can be swapped
 * for live Zenoh data with no change to the components:
 *   - vehicle.vid      -> licence plate / vehicle id (Italian AA000AA format)
 *   - vehicle.mode     -> transmission mode for that vehicle: 'CLOUD' | 'EDGE'
 *   - vehicle.profile  -> driver profile (aggressive | normal | calm)
 *   - vehicle.eco/safety -> deterministic session scores from the server
 *   - fleet.directive  -> the global mode the server is currently broadcasting
 */

const PROFILES = ['aggressive', 'normal', 'calm']

function plate() {
  const L = () => 'ABCDEFGHJKLMNPRSTVWXYZ'[Math.floor(Math.random() * 22)]
  const D = () => Math.floor(Math.random() * 10)
  return `${L()}${L()}${D()}${D()}${D()}${L()}${L()}`
}

// Cagliari bounding box (matches the simulator's initial-position generator)
function nearCagliari() {
  return {
    lat: +(39.1 + Math.random() * 0.2).toFixed(5),
    lon: +(9.0 + Math.random() * 0.2).toFixed(5),
  }
}

function makeVehicle() {
  const profile = PROFILES[Math.floor(Math.random() * PROFILES.length)]
  const aggressive = profile === 'aggressive'
  return {
    vid: plate(),
    profile,
    mode: Math.random() < 0.6 ? 'CLOUD' : 'EDGE',
    status: 'alive',
    speedKmh: Math.round(20 + Math.random() * (aggressive ? 110 : 80)),
    safety: Math.round(aggressive ? 35 + Math.random() * 40 : 75 + Math.random() * 25),
    eco: Math.round(55 + Math.random() * 40),
    ...nearCagliari(),
  }
}

export function buildSnapshot(count = 14) {
  const vehicles = Array.from({ length: count }, makeVehicle)
  return {
    fleet: {
      directive: 'CLOUD', // current global mode the server broadcasts
      router: 'tcp/localhost:7447',
      bandwidthBytesS: 0,
      energySavedJ: 0,
      updatedAt: Date.now(),
    },
    vehicles,
  }
}

export const mockSnapshot = buildSnapshot()
