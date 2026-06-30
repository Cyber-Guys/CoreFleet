/**
 * useFleet — singleton fleet store (module-scoped reactive state).
 *
 * Holds the snapshot, the search query, and derived views. A lightweight live
 * simulation jitters the mock data so the dashboard feels real; swapping in the
 * backend means replacing `_tick` with a poll of `fleetApi.getSnapshot()`.
 */
import { computed, reactive, readonly, ref } from 'vue'
import { fleetApi } from '@/services/fleetApi'

const state = reactive({
  vehicles: [],
  fleet: { directive: 'CLOUD', router: '', bandwidthBytesS: 0, energySavedJ: 0, updatedAt: 0 },
  loading: true,
  error: null,
})

const searchQuery = ref('')
let pollTimer = null

// --- derived views ---
const normalizedQuery = computed(() => searchQuery.value.trim().toUpperCase())

const filteredVehicles = computed(() => {
  const q = normalizedQuery.value
  if (!q) return state.vehicles
  return state.vehicles.filter(
    (v) => v.vid.includes(q) || v.profile.toUpperCase().includes(q),
  )
})

const activeCount = computed(() => state.vehicles.length)
const cloudCount = computed(() => state.vehicles.filter((v) => v.mode === 'CLOUD').length)
const edgeCount = computed(() => state.vehicles.filter((v) => v.mode === 'EDGE').length)
const hasResults = computed(() => filteredVehicles.value.length > 0)

// --- actions ---
async function load() {
  state.loading = true
  state.error = null
  try {
    const snap = await fleetApi.getSnapshot()
    state.vehicles = snap.vehicles
    state.fleet = snap.fleet
    recomputeFleet()
  } catch (err) {
    state.error = err.message || 'Impossibile caricare i dati della flotta'
  } finally {
    state.loading = false
  }
}

function setSearch(value) {
  searchQuery.value = value
}

/** Recompute the global directive + headline metrics from current vehicles. */
function recomputeFleet() {
  const edges = state.vehicles.filter((v) => v.mode === 'EDGE').length
  // server logic: a congested fleet (mostly EDGE) means the EDGE directive is on
  state.fleet.directive = edges > state.vehicles.length / 2 ? 'EDGE' : 'CLOUD'
  const cloudBps = cloudCount.value * 220 // ~raw payload size at 1 Hz
  const edgeBps = edgeCount.value * (240 / 15) // one summary per 15 s window
  state.fleet.bandwidthBytesS = Math.round(cloudBps + edgeBps)
  const baseline = state.vehicles.length * 220
  state.fleet.energySavedJ = Math.max(0, ((baseline - state.fleet.bandwidthBytesS) / 1e6) * 1100)
  state.fleet.updatedAt = Date.now()
}

/** Jitter the mock data to emulate a live feed. */
function _tick() {
  if (!state.vehicles.length) return
  for (const v of state.vehicles) {
    v.speedKmh = Math.max(0, Math.min(160, v.speedKmh + Math.round((Math.random() - 0.5) * 14)))
  }
  // occasionally flip one vehicle's transmission mode
  if (Math.random() < 0.4) {
    const v = state.vehicles[Math.floor(Math.random() * state.vehicles.length)]
    v.mode = v.mode === 'CLOUD' ? 'EDGE' : 'CLOUD'
  }
  recomputeFleet()
}

function startPolling(intervalMs = 2000) {
  stopPolling()
  pollTimer = setInterval(_tick, intervalMs)
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
    filteredVehicles,
    activeCount,
    cloudCount,
    edgeCount,
    hasResults,
    // actions
    load,
    setSearch,
    startPolling,
    stopPolling,
  }
}
