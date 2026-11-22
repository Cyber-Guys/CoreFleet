/**
 * Fleet API client.
 *
 * Calls `/report-api` on the same origin by default. In production nginx
 * proxies it to the report service, in development the Vite dev server does.
 * Set VITE_REPORT_API_URL at build time to use another base URL.
 */
const REPORT_BASE = import.meta.env.VITE_REPORT_API_URL || '/report-api'

export const fleetApi = {
  /** History of generated driver reports (newest first). */
  async getReports({ signal } = {}) {
    return getJson(`${REPORT_BASE}/report/api/report`, signal)
  },

  /** Who is driving now, with telemetry per vehicle (mode, speed, rpm, ...). */
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

  /** Generate a driver's LLM report, or return the cached one. Returns quickly;
   *  the hourglass image is generated in the background (poll getDriverReportImage). */
  async generateDriverReport(did) {
    const res = await fetch(`${REPORT_BASE}/report/api/drivers/${encodeURIComponent(did)}/report`, {
      method: 'POST',
      headers: { Accept: 'application/json' },
    })
    if (!res.ok) throw new Error(`Report API ${res.status}`)
    return res.json() // DriverReport
  },

  /** Poll the hourglass image: { status: 'ready'|'pending'|'none', imageUrl }. */
  async getDriverReportImage(did, { signal } = {}) {
    return getJson(`${REPORT_BASE}/report/api/drivers/${encodeURIComponent(did)}/report/image`, signal)
  },
}

async function getJson(url, signal) {
  const res = await fetch(url, { headers: { Accept: 'application/json' }, signal })
  if (!res.ok) throw new Error(`API ${res.status}`)
  return res.json()
}
