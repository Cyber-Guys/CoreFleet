<script setup>
/* Driver reports.
   A report is about the DRIVER (person), built from a trip and compared to that
   driver's previous trips (improved / worsened / stable / recidivist).
   Pulls live from the Jakarta service; falls back to a local preview. */
import { computed, onMounted, onUnmounted, ref } from 'vue'
import BaseWidget from '@/components/ui/BaseWidget.vue'
import { fleetApi } from '@/services/fleetApi'
import { useFleet } from '@/composables/useFleet'

const { filteredVehicles, searchQuery } = useFleet()

const liveReports = ref([])
const source = ref('loading') // 'loading' | 'live' | 'preview'
const lastError = ref('')
let timer = null
let controller = null

const BEHAVIOUR_IT = {
  harsh_accel: 'accelerate brusche',
  harsh_brake: 'frenate brusche',
  speeding: 'eccesso velocità',
  overrev: 'fuorigiri',
  cold_overrev: 'fuorigiri a freddo',
  excess_idle: 'sosta eccessiva',
}

function grade(score) {
  if (score >= 85) return 'A'
  if (score >= 70) return 'B'
  if (score >= 55) return 'C'
  return 'D'
}
function tone(score) {
  if (score >= 80) return 'var(--green)'
  if (score >= 60) return 'var(--orange)'
  return 'var(--danger)'
}
function behaviour(name) {
  return BEHAVIOUR_IT[name] || name
}

/** Trend → { label, color, icon } for the badge. */
function trendBadge(trend) {
  if (!trend) return null
  if (trend.recidivist && trend.recidivist.length) {
    return { label: 'Recidivo', color: 'var(--orange)', icon: '⟳' }
  }
  switch (trend.verdict) {
    case 'improved':
      return { label: 'Migliorato', color: 'var(--green)', icon: '↑' }
    case 'worsened':
      return { label: 'Peggiorato', color: 'var(--danger)', icon: '↓' }
    case 'first_trip':
      return { label: '1° trip', color: 'var(--cyan)', icon: '◆' }
    default:
      return { label: 'Invariato', color: 'var(--muted)', icon: '=' }
  }
}
function fmtDelta(d) {
  if (d === null || d === undefined) return ''
  return (d > 0 ? '+' : '') + d
}

/** Preview reports derived from mock vehicles, shaped like a DrivingReport. */
const previewReports = computed(() =>
  filteredVehicles.value.map((v) => ({
    did: '—',
    driverName: 'Anteprima',
    vid: v.vid,
    safetyScore: v.safety,
    ecoScore: v.eco,
    overallGrade: grade((v.eco + v.safety) / 2),
    summary: 'Anteprima locale: il servizio report Jakarta non è raggiungibile.',
    recommendations: [],
    maintenanceHints: [],
    trend: null,
    hourglass: null,
  })),
)

const query = computed(() => searchQuery.value.trim().toUpperCase())

const reports = computed(() => {
  const base = source.value === 'live' ? liveReports.value : previewReports.value
  if (!query.value) return base
  return base.filter((r) =>
    [r.driverName, r.did, r.vid].some((s) => (s || '').toUpperCase().includes(query.value)),
  )
})

const hasResults = computed(() => reports.value.length > 0)
const waitingForSessions = computed(() => !query.value && reports.value.length === 0)

async function fetchReports() {
  controller?.abort()
  controller = new AbortController()
  try {
    const data = await fleetApi.getReports({ signal: controller.signal })
    liveReports.value = Array.isArray(data) ? data : []
    source.value = 'live'
    lastError.value = ''
  } catch (err) {
    if (err.name === 'AbortError') return
    source.value = 'preview'
    lastError.value = err.message || 'servizio non raggiungibile'
  }
}

onMounted(() => {
  fetchReports()
  timer = setInterval(fetchReports, 5000)
})
onUnmounted(() => {
  if (timer) clearInterval(timer)
  controller?.abort()
})
</script>

<template>
  <BaseWidget title="Report conducenti" eyebrow="Driver reports" icon="report">
    <template #meta>
      <span class="src" :class="source">
        <i />{{ source === 'live' ? 'LIVE' : source === 'loading' ? '…' : 'PREVIEW' }}
      </span>
    </template>

    <p class="lede">
      Ogni report è sul <b>conducente</b>: confronta il trip con i precedenti dello
      stesso guidatore (migliorato, peggiorato, invariato, o comportamento recidivo).
      <span v-if="source === 'preview' && lastError" class="lede__err">
        · servizio offline ({{ lastError }})
      </span>
    </p>

    <div v-if="hasResults" class="cards">
      <article v-for="(r, i) in reports" :key="(r.did || '') + '-' + (r.tripId || i)" class="card">
        <header class="card__top">
          <div class="who">
            <span class="who__name">{{ r.driverName }}</span>
            <span class="who__sub cf-mono">{{ r.did }} · su {{ r.vid }}</span>
          </div>
          <span class="card__grade" :style="{ '--c': tone(((r.ecoScore || 0) + (r.safetyScore || 0)) / 2) }">
            {{ r.overallGrade }}
          </span>
        </header>

        <div v-if="trendBadge(r.trend)" class="trend">
          <span class="trend__badge" :style="{ '--c': trendBadge(r.trend).color }">
            {{ trendBadge(r.trend).icon }} {{ trendBadge(r.trend).label }}
          </span>
          <span v-if="r.trend.tripCount" class="trend__count">trip #{{ r.trend.tripCount }}</span>
          <span v-if="r.trend.deltaSafety !== null && r.trend.deltaSafety !== undefined" class="trend__delta cf-mono">
            sicurezza {{ fmtDelta(r.trend.deltaSafety) }} · eco {{ fmtDelta(r.trend.deltaEco) }}
          </span>
        </div>

        <p v-if="r.summary" class="card__summary">{{ r.summary }}</p>

        <div v-if="r.trend && r.trend.recidivist && r.trend.recidivist.length" class="recid">
          <span class="recid__label">⟳ Recidivo su</span>
          <span class="chips">
            <b v-for="(b, k) in r.trend.recidivist" :key="'rc' + k">{{ behaviour(b) }}</b>
          </span>
        </div>

        <div class="metric">
          <div class="metric__head"><span>Sicurezza</span><b class="cf-mono">{{ r.safetyScore }}</b></div>
          <div class="metric__track"><i :style="{ width: (r.safetyScore || 0) + '%', '--c': tone(r.safetyScore || 0) }" /></div>
        </div>
        <div class="metric">
          <div class="metric__head"><span>Eco</span><b class="cf-mono">{{ r.ecoScore }}</b></div>
          <div class="metric__track"><i :style="{ width: (r.ecoScore || 0) + '%', '--c': tone(r.ecoScore || 0) }" /></div>
        </div>

        <div v-if="r.recommendations && r.recommendations.length" class="block">
          <span class="block__label">Consigli</span>
          <ul class="block__list">
            <li v-for="(t, k) in r.recommendations.slice(0, 4)" :key="'rec' + k">{{ t }}</li>
          </ul>
        </div>

        <div v-if="r.maintenanceHints && r.maintenanceHints.length" class="block">
          <span class="block__label">Manutenzione</span>
          <ul class="block__list block__list--warn">
            <li v-for="(t, k) in r.maintenanceHints.slice(0, 4)" :key="'mnt' + k">{{ t }}</li>
          </ul>
        </div>

        <div v-if="r.hourglass" class="hourglass">
          <span class="block__label">Hourglass</span>
          <div class="hourglass__row" v-if="r.hourglass.stakeholders">
            <span class="hourglass__k">Stakeholder</span>
            <span class="chips"><b v-for="(s, k) in r.hourglass.stakeholders" :key="'st' + k">{{ s }}</b></span>
          </div>
          <div class="hourglass__row hourglass__row--waist" v-if="r.hourglass.capabilities">
            <span class="hourglass__k">Capabilities</span>
            <span class="chips"><b v-for="(s, k) in r.hourglass.capabilities" :key="'cp' + k">{{ s }}</b></span>
          </div>
          <div class="hourglass__row" v-if="r.hourglass.standardsGroups">
            <span class="hourglass__k">Standards</span>
            <span class="chips"><b v-for="(s, k) in r.hourglass.standardsGroups" :key="'sg' + k">{{ s }}</b></span>
          </div>
        </div>
      </article>
    </div>

    <div v-else-if="waitingForSessions" class="empty">
      <span class="empty__glyph">◴</span>
      <p class="empty__title">In attesa di sessioni</p>
      <p class="empty__hint">Nessun report ancora. Si popola quando un conducente termina un trip.</p>
    </div>

    <div v-else class="empty">
      <span class="empty__glyph">⌀</span>
      <p class="empty__title">Nessun risultato trovato</p>
      <p class="empty__hint">Nessun conducente corrisponde a “<b>{{ searchQuery }}</b>”.</p>
    </div>
  </BaseWidget>
</template>

<style scoped>
.src {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  font-family: var(--font-mono);
  font-size: 11px;
  letter-spacing: 0.14em;
  padding: 3px 9px;
  border-radius: 7px;
}
.src i {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: currentColor;
  box-shadow: 0 0 9px currentColor;
}
.src.live {
  color: var(--green-glow);
  background: rgba(43, 255, 158, 0.1);
  border: 1px solid rgba(43, 255, 158, 0.3);
}
.src.preview {
  color: var(--orange-glow);
  background: rgba(255, 122, 26, 0.1);
  border: 1px solid rgba(255, 122, 26, 0.32);
}
.src.loading {
  color: var(--muted);
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid var(--line);
}
.lede {
  margin: 0 0 18px;
  max-width: 78ch;
  font-size: 14px;
  line-height: 1.5;
  color: var(--muted);
}
.lede b {
  color: var(--text);
}
.lede__err {
  color: var(--orange-glow);
}
.cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(290px, 1fr));
  gap: 14px;
}
.card {
  padding: 16px;
  border-radius: var(--r-sm);
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid var(--line);
  animation: cf-rise 0.35s ease both;
}
.card__top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 10px;
}
.who {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}
.who__name {
  font-family: var(--font-display);
  font-size: 17px;
  font-weight: 600;
  color: var(--text);
}
.who__sub {
  font-size: 11px;
  letter-spacing: 0.04em;
  color: var(--faint);
}
.card__grade {
  display: grid;
  place-items: center;
  width: 30px;
  height: 30px;
  border-radius: 9px;
  font-family: var(--font-display);
  font-weight: 700;
  color: var(--c);
  background: color-mix(in srgb, var(--c) 14%, transparent);
  border: 1px solid color-mix(in srgb, var(--c) 45%, transparent);
  flex: none;
}
.trend {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 12px;
}
.trend__badge {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.04em;
  color: var(--c);
  padding: 3px 9px;
  border-radius: 7px;
  background: color-mix(in srgb, var(--c) 14%, transparent);
  border: 1px solid color-mix(in srgb, var(--c) 42%, transparent);
}
.trend__count {
  font-size: 11px;
  color: var(--faint);
  text-transform: uppercase;
  letter-spacing: 0.08em;
}
.trend__delta {
  font-size: 11px;
  color: var(--muted);
  margin-left: auto;
}
.card__summary {
  margin: 12px 0 0;
  font-size: 13px;
  line-height: 1.5;
  color: var(--text);
}
.recid {
  display: flex;
  align-items: baseline;
  gap: 8px;
  margin-top: 12px;
}
.recid__label {
  flex: none;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.04em;
  color: var(--orange-glow);
}
.metric {
  margin-top: 12px;
}
.metric:first-of-type {
  margin-top: 14px;
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
  height: 6px;
  border-radius: 99px;
  background: rgba(255, 255, 255, 0.05);
  overflow: hidden;
}
.metric__track i {
  display: block;
  height: 100%;
  border-radius: 99px;
  background: var(--c);
  box-shadow: 0 0 10px var(--c);
  transition: width 0.5s ease;
}
.block {
  margin-top: 14px;
}
.block__label {
  display: block;
  font-family: var(--font-mono);
  font-size: 10px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--faint);
  margin-bottom: 7px;
}
.block__list {
  margin: 0;
  padding-left: 16px;
  display: grid;
  gap: 4px;
  font-size: 13px;
  line-height: 1.4;
  color: var(--muted);
}
.block__list--warn li {
  color: var(--orange-glow);
}
.hourglass {
  margin-top: 14px;
  padding-top: 12px;
  border-top: 1px solid var(--line);
}
.hourglass__row {
  display: flex;
  gap: 10px;
  align-items: baseline;
  margin-bottom: 8px;
}
.hourglass__k {
  flex: none;
  width: 86px;
  font-size: 11px;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--faint);
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
  color: var(--muted);
  background: rgba(125, 150, 255, 0.07);
  border: 1px solid var(--line);
}
.recid .chips b {
  color: var(--orange-glow);
  background: rgba(255, 122, 26, 0.1);
  border-color: rgba(255, 122, 26, 0.3);
}
.hourglass__row--waist .chips b {
  color: var(--purple-glow);
  background: rgba(139, 92, 255, 0.12);
  border-color: rgba(139, 92, 255, 0.34);
}
.empty {
  flex: 1;
  display: grid;
  place-content: center;
  text-align: center;
  gap: 4px;
  padding: 40px 0;
}
.empty__glyph {
  font-size: 40px;
  color: var(--faint);
  line-height: 1;
}
.empty__title {
  margin: 8px 0 0;
  font-family: var(--font-display);
  font-size: 16px;
  color: var(--text);
}
.empty__hint {
  margin: 0;
  font-size: 13px;
  color: var(--muted);
}
.empty__hint b {
  color: var(--cyan);
}
</style>
