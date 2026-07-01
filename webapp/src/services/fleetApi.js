/**
 * Fleet API client.
 *
 * Calls the same-origin `/report-api` path by default (nginx proxies it to the
 * report service in prod; the Vite dev server proxies it in dev). Override the
 * base with VITE_REPORT_API_URL at build time. No host/IP is hardcoded here.
 */
const REPORT_BASE = import.meta.env.VITE_REPORT_API_URL || '/report-api'

export const fleetApi = {
  /** History of generated driver reports (newest first). */
  async getReports({ signal } = {}) {
    return getJson(`${REPORT_BASE}/report/api/report`, signal)
  },

  /** Live "who is driving now" + telemetry (mode, speed, rpm, …) per vehicle. */
  async getActive({ signal } = {}) {
    return getJson(`${REPORT_BASE}/report/api/active`, signal)
  },

  /** Vehicle registry. */
  async getVehicles({ signal } = {}) {
    return getJson(`${REPORT_BASE}/report/api/vehicles`, signal)
  },
  async getVehicle(vid, { signal } = {}) {
    return getJson(`${REPORT_BASE}/report/api/vehicles/${encodeURIComponent(vid)}`, signal)
  },

  /** Driver registry. */
  async getDrivers({ signal } = {}) {
    return getJson(`${REPORT_BASE}/report/api/drivers`, signal)
  },
  async getDriver(did, { signal } = {}) {
    return getJson(`${REPORT_BASE}/report/api/drivers/${encodeURIComponent(did)}`, signal)
  },

  /** Generate (or return cached) LLM report for a driver. Returns fast; the
   *  hourglass image is generated asynchronously (poll getDriverReportImage). */
  async generateDriverReport(did) {
    const res = await fetch(`${REPORT_BASE}/report/api/drivers/${encodeURIComponent(did)}/report`, {
      method: 'POST',
      headers: { Accept: 'application/json' },
    })
    if (!res.ok) throw new Error(`Report API ${res.status}`)
    return res.json() // DriverReport
  },

  /** Poll the async hourglass image: { status: 'ready'|'pending'|'none', imageUrl }. */
  async getDriverReportImage(did, { signal } = {}) {
    return getJson(`${REPORT_BASE}/report/api/drivers/${encodeURIComponent(did)}/report/image`, signal)
  },
}

async function getJson(url, signal) {
  const res = await fetch(url, { headers: { Accept: 'application/json' }, signal })
  if (!res.ok) throw new Error(`API ${res.status}`)
  return res.json()
}
