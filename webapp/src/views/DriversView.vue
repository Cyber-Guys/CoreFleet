<script setup>
/* Drivers registry — list + detail (anagrafica, trips, km, infractions) and an
   on-demand "Genera report" button (cached when the driver's data is unchanged). */
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppIcon from '@/components/ui/AppIcon.vue'
import DriverReportCard from '@/components/DriverReportCard.vue'
import { fleetApi } from '@/services/fleetApi'
import { useFleet } from '@/composables/useFleet'

const { searchQuery } = useFleet()
const route = useRoute()
const router = useRouter()

const drivers = ref([])
const selectedDid = ref(route.query.did || null)
const source = ref('loading')

watch(() => route.query.did, (v) => {
  if (v) selectedDid.value = v
})
function select(did) {
  selectedDid.value = did
  router.replace({ query: { did } })
}
const report = ref(null)
const generating = ref(false)
const reportError = ref('')
let timer = null
let controller = null

const BEHAVIOUR_EN = {
  harsh_accel: 'harsh acceleration',
  harsh_brake: 'harsh braking',
  speeding: 'speeding',
  overrev: 'over-revving',
  cold_overrev: 'cold-engine over-rev',
  excess_idle: 'excessive idling',
}
function behaviour(n) {
  return BEHAVIOUR_EN[n] || n
}
function tone(s) {
  if (s >= 80) return 'var(--green)'
  if (s >= 60) return 'var(--orange)'
  return 'var(--danger)'
}

const query = computed(() => searchQuery.value.trim().toUpperCase())
const filtered = computed(() => {
  if (!query.value) return drivers.value
  return drivers.value.filter((d) =>
    [d.fullName, d.did, d.surname].some((s) => (s || '').toUpperCase().includes(query.value)),
  )
})
const selected = computed(
  () => drivers.value.find((d) => d.did === selectedDid.value) || filtered.value[0] || null,
)
const carsUsed = computed(() => {
  const hist = selected.value?.scoreHistory || []
  return [...new Set(hist.map((t) => t.vid).filter(Boolean))]
})

let imageTimer = null
function stopImagePoll() {
  if (imageTimer) clearInterval(imageTimer)
  imageTimer = null
}

watch(selected, (d, prev) => {
  if (!d || (prev && d.did !== prev.did)) {
    report.value = null
    reportError.value = ''
    stopImagePoll()
  }
})

async function load() {
  controller?.abort()
  controller = new AbortController()
  try {
    const data = await fleetApi.getDrivers({ signal: controller.signal })
    drivers.value = (Array.isArray(data) ? data : []).sort((a, b) => a.did.localeCompare(b.did))
    source.value = 'live'
  } catch (err) {
    if (err.name === 'AbortError') return
    source.value = 'offline'
  }
}

async function generate() {
  if (!selected.value) return
  const did = selected.value.did
  generating.value = true
  reportError.value = ''
  stopImagePoll()
  try {
    report.value = await fleetApi.generateDriverReport(did)
    if (report.value?.imageStatus === 'pending') pollImage(did)
  } catch (err) {
    reportError.value = err.message || 'report generation failed'
  } finally {
    generating.value = false
  }
}

// poll the async hourglass image until it's ready
function pollImage(did) {
  stopImagePoll()
  imageTimer = setInterval(async () => {
    try {
      const res = await fleetApi.getDriverReportImage(did)
      if (!report.value || report.value.did !== did) return stopImagePoll()
      if (res.status === 'ready' && res.imageUrl) {
        report.value.hourglassImageUrl = res.imageUrl
        report.value.imageStatus = 'ready'
        stopImagePoll()
      } else if (res.status === 'none') {
        report.value.imageStatus = 'none'
        stopImagePoll()
      }
    } catch {
      /* keep polling */
    }
  }, 3000)
}

onMounted(() => {
  load()
  timer = setInterval(load, 5000)
})
onUnmounted(() => {
  if (timer) clearInterval(timer)
  stopImagePoll()
  controller?.abort()
})
</script>

<template>
  <div class="page">
    <section class="list-panel">
      <header class="panel__head"><span class="cf-eyebrow">Drivers · {{ drivers.length }}</span></header>
      <div v-if="filtered.length" class="list">
        <button
          v-for="d in filtered"
          :key="d.did"
          class="row"
          :class="{ active: selected && selected.did === d.did }"
          @click="select(d.did)"
        >
          <span class="avatar">{{ (d.name || '?').charAt(0) }}</span>
          <span class="row__name">
            {{ d.fullName }}<small class="cf-mono">{{ d.did }} · {{ d.trips }} trips</small>
          </span>
          <span v-if="d.infractions" class="row__fines">{{ d.infractions }} fines</span>
        </button>
      </div>
      <p v-else class="muted">{{ source === 'offline' ? 'Service unreachable.' : 'No drivers.' }}</p>
    </section>

    <section v-if="selected" class="detail">
      <header class="detail__head">
        <div>
          <span class="cf-eyebrow">Driver</span>
          <h2>{{ selected.fullName }}</h2>
          <span class="anag cf-mono">{{ selected.did }} · Tax ID {{ selected.cf }} · {{ selected.nationality }}</span>
        </div>
        <AppIcon name="users" :size="34" class="detail__icon" />
      </header>

      <div class="stats">
        <div class="stat"><span>Trips</span><b class="cf-mono">{{ selected.trips }}</b></div>
        <div class="stat"><span>Total km</span><b class="cf-mono">{{ Math.round(selected.totalKm).toLocaleString('en-US') }}</b></div>
        <div class="stat"><span>Fines</span><b class="cf-mono" :class="{ bad: selected.infractions }">{{ selected.infractions }}</b></div>
        <div class="stat"><span>Warnings</span><b class="cf-mono">{{ selected.warnings }}</b></div>
      </div>

      <div class="metric">
        <div class="metric__head"><span>Avg safety</span><b class="cf-mono">{{ selected.avgSafety }}</b></div>
        <div class="metric__track"><i :style="{ width: selected.avgSafety + '%', '--c': tone(selected.avgSafety) }" /></div>
      </div>
      <div class="metric">
        <div class="metric__head"><span>Avg eco</span><b class="cf-mono">{{ selected.avgEco }}</b></div>
        <div class="metric__track"><i :style="{ width: selected.avgEco + '%', '--c': tone(selected.avgEco) }" /></div>
      </div>

      <div v-if="selected.recidivist && selected.recidivist.length" class="recid">
        <span class="recid__label">⟳ Repeat offender:</span>
        <span class="chips"><b v-for="(b, k) in selected.recidivist" :key="'rc' + k">{{ behaviour(b) }}</b></span>
      </div>

      <div class="cars">
        <span class="block__label">Cars used ({{ carsUsed.length }})</span>
        <div v-if="carsUsed.length" class="chips">
          <RouterLink
            v-for="vid in carsUsed"
            :key="vid"
            class="carlink cf-mono"
            :to="{ path: '/vehicles', query: { vid } }"
          >{{ vid }}</RouterLink>
        </div>
        <span v-else class="muted">—</span>
      </div>

      <div class="actions">
        <button class="gen" :disabled="generating || !selected.trips" @click="generate">
          <AppIcon name="report" :size="17" />
          {{ generating ? 'Generating…' : 'Generate Report' }}
        </button>
        <span v-if="reportError" class="err">{{ reportError }}</span>
      </div>

      <div v-if="report" class="report-out">
        <DriverReportCard :report="report" />
      </div>
    </section>
  </div>
</template>

<style scoped>
.page {
  display: grid;
  grid-template-columns: 340px minmax(0, 1fr);
  gap: 20px;
  align-items: start;
}
.list-panel,
.detail {
  padding: 18px;
  border-radius: var(--r);
  background: linear-gradient(180deg, var(--panel-2), var(--panel));
  border: 1px solid var(--line-strong);
  box-shadow: var(--shadow);
}
.panel__head {
  margin-bottom: 12px;
}
.list {
  display: flex;
  flex-direction: column;
  gap: 7px;
  max-height: 64vh;
  overflow-y: auto;
}
.row {
  display: grid;
  grid-template-columns: auto 1fr auto;
  align-items: center;
  gap: 11px;
  width: 100%;
  text-align: left;
  padding: 9px 12px;
  border-radius: var(--r-sm);
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid var(--line);
  color: var(--text);
  cursor: pointer;
  transition: border-color 0.2s, background 0.2s;
}
.row:hover {
  border-color: color-mix(in srgb, var(--cyan) 40%, var(--line));
}
.row.active {
  border-color: var(--purple);
  background: rgba(139, 92, 255, 0.08);
}
.avatar {
  display: grid;
  place-items: center;
  width: 30px;
  height: 30px;
  border-radius: 9px;
  font-family: var(--font-display);
  font-weight: 700;
  color: var(--bg);
  background: linear-gradient(135deg, var(--cyan), var(--purple));
  flex: none;
}
.row__name {
  display: flex;
  flex-direction: column;
  font-size: 14px;
  min-width: 0;
}
.row__name small {
  font-size: 11px;
  color: var(--faint);
}
.row__fines {
  font-size: 11px;
  color: var(--danger);
}
.detail__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
}
.detail__head h2 {
  font-size: 24px;
  margin: 2px 0 4px;
}
.anag {
  font-size: 12px;
  color: var(--faint);
}
.detail__icon {
  color: var(--cyan);
}
.stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 10px;
  margin: 18px 0;
}
.stat {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 12px;
  border-radius: var(--r-sm);
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid var(--line);
}
.stat span {
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--muted);
}
.stat b {
  font-size: 19px;
  color: var(--text);
}
.stat b.bad {
  color: var(--danger);
}
.metric {
  margin-top: 12px;
}
.metric__head {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: var(--muted);
  margin-bottom: 6px;
}
.metric__head b {
  color: var(--text);
}
.metric__track {
  height: 7px;
  border-radius: 99px;
  background: rgba(255, 255, 255, 0.05);
  overflow: hidden;
}
.metric__track i {
  display: block;
  height: 100%;
  border-radius: 99px;
  background: var(--c);
  box-shadow: 0 0 12px var(--c);
  transition: width 0.5s ease;
}
.recid {
  display: flex;
  align-items: baseline;
  gap: 8px;
  margin-top: 14px;
}
.recid__label {
  flex: none;
  font-size: 11px;
  font-weight: 700;
  color: var(--orange-glow);
}
.chips {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
}
.chips b {
  font-weight: 500;
  font-size: 11px;
  padding: 2px 7px;
  border-radius: 6px;
  color: var(--orange-glow);
  background: rgba(255, 122, 26, 0.1);
  border: 1px solid rgba(255, 122, 26, 0.3);
}
.cars {
  margin-top: 16px;
}
.block__label {
  display: block;
  font-family: var(--font-mono);
  font-size: 10px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--faint);
  margin-bottom: 8px;
}
.carlink {
  font-size: 12px;
  font-weight: 700;
  padding: 4px 9px;
  border-radius: 7px;
  color: var(--cyan);
  background: rgba(34, 211, 255, 0.1);
  border: 1px solid rgba(34, 211, 255, 0.3);
  transition: background 0.15s, color 0.15s;
}
.carlink:hover {
  background: rgba(34, 211, 255, 0.2);
  color: var(--text);
}
.actions {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  margin-top: 20px;
}
.gen {
  display: inline-flex;
  align-items: center;
  gap: 9px;
  padding: 11px 18px;
  border-radius: 11px;
  border: 1px solid color-mix(in srgb, var(--purple) 50%, transparent);
  background: linear-gradient(135deg, rgba(34, 211, 255, 0.16), rgba(139, 92, 255, 0.16));
  color: var(--text);
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: box-shadow 0.2s, transform 0.1s;
}
.gen:hover:not(:disabled) {
  box-shadow: 0 0 26px -8px var(--purple);
}
.gen:disabled {
  opacity: 0.55;
  cursor: default;
}
.err {
  color: var(--danger);
  font-size: 13px;
}
.report-out {
  margin-top: 18px;
}
.muted {
  color: var(--muted);
  font-size: 13px;
}

@media (max-width: 900px) {
  .page {
    grid-template-columns: minmax(0, 1fr);
  }
  .stats {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
