/**
 * Fleet API service.
 *
 * Single seam between the UI and the data source. Today it returns mock data;
 * when the backend is ready, flip `USE_MOCK` to false (or set VITE_USE_MOCK=false)
 * and the same methods will read live state from the Zenoh router's REST API.
 *
 * The Zenoh router exposes its key space over HTTP on :8000, so a GET on
 * `core/fleet/**` returns the latest telemetry samples — no extra backend needed.
 */
import { buildSnapshot } from '@/data/mockData'

const BASE = import.meta.env.VITE_FLEET_API_URL || 'http://localhost:8000'
const REPORT_BASE = import.meta.env.VITE_REPORT_API_URL || 'http://localhost:9080'
const USE_MOCK = (import.meta.env.VITE_USE_MOCK ?? 'true') !== 'false'

function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

/** Map a raw Zenoh REST payload into our snapshot shape (live mode). */
function adaptZenoh(_entries) {
  // TODO: parse `core/fleet/*/raw|summary` samples into { fleet, vehicles }.
  // Left as the integration point once the live endpoint is wired.
  throw new Error('Live Zenoh adapter not implemented yet')
}

export const fleetApi = {
  /** Full fleet snapshot: { fleet, vehicles }. */
  async getSnapshot() {
    if (USE_MOCK) {
      await delay(280) // simulate network latency
      return buildSnapshot()
    }
    const res = await fetch(`${BASE}/core/fleet/**`, {
      headers: { Accept: 'application/json' },
    })
    if (!res.ok) throw new Error(`Fleet API ${res.status}`)
    return adaptZenoh(await res.json())
  },

  /**
   * Live LLM driving reports from the Jakarta service (newest first).
   * Throws on any non-2xx / network error so the caller can fall back to mock.
   */
  async getReports({ signal } = {}) {
    const res = await fetch(`${REPORT_BASE}/report/api/report`, {
      headers: { Accept: 'application/json' },
      signal,
    })
    if (!res.ok) throw new Error(`Report API ${res.status}`)
    return res.json() // DrivingReport[]
  },
}
