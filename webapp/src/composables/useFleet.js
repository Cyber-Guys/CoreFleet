/**
 * useFleet — singleton fleet store (module-scoped reactive state).
 *
 * Live data only: polls the Jakarta service for the connected vehicles
 * (`/report/api/active`, with per-vehicle mode + telemetry) and the full vehicle
 * registry (`/report/api/vehicles`). No mock data.
 */
import { computed, reactive, readonly, ref } from 'vue'
import { fleetApi } from '@/services/fleetApi'

const state = reactive({
  active: [], // vehicles currently on a trip (mode + live telemetry)
  vehicles: [], // full vehicle registry
  fleet: { directive: 'CLOUD', updatedAt: 0, online: false },
  loading: true,
  error: null,
})

const searchQuery = ref('')
let pollTimer = null

// --- derived views ---
const activeCount = computed(() => state.active.length)
// true fleet size = cars seen in the registry ∪ cars currently on a trip
// (a car only enters the registry after its first trip ends)
const totalFleet = computed(() => {
  const ids = new Set(state.vehicles.map((v) => v.vid))
  for (const a of state.active) ids.add(a.vid)
  return ids.size
})
const cloudCount = computed(() => state.active.filter((v) => v.mode === 'CLOUD').length)
const edgeCount = computed(() => state.active.filter((v) => v.mode === 'EDGE').length)

// --- actions ---
async function load() {
  try {
    const [active, vehicles] = await Promise.all([
      fleetApi.getActive(),
      fleetApi.getVehicles(),
    ])
    state.active = Array.isArray(active) ? active : []
    state.vehicles = Array.isArray(vehicles) ? vehicles : []
    // the transmission mode is global; derive the directive from the fleet
    state.fleet.directive = edgeCount.value > cloudCount.value ? 'EDGE' : 'CLOUD'
    state.fleet.updatedAt = Date.now()
    state.fleet.online = true
    state.error = null
  } catch (err) {
    state.fleet.online = false
    state.error = err.message || 'Fleet API unreachable'
  } finally {
    state.loading = false
  }
}

function setSearch(value) {
  searchQuery.value = value
}

function startPolling(intervalMs = 2500) {
  stopPolling()
  load()
  pollTimer = setInterval(load, intervalMs)
}

function stopPolling() {
  if (pollTimer) clearInterval(pollTimer)
  pollTimer = null
}

export function useFleet() {
  return {
    state: readonly(state),
    searchQuery,
    // derived
    activeCount,
    totalFleet,
    cloudCount,
    edgeCount,
    // actions
    load,
    setSearch,
    startPolling,
    stopPolling,
  }
}
