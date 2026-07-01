<script setup>
/* Vehicles registry — list + detail (odometer, trips, fuel/oil, warning lights,
   recent drivers). Data from the Jakarta fleet store. */
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppIcon from '@/components/ui/AppIcon.vue'
import { fleetApi } from '@/services/fleetApi'
import { useFleet } from '@/composables/useFleet'

const { searchQuery } = useFleet()
const route = useRoute()
const router = useRouter()

const vehicles = ref([])
const activeMap = ref({})
const selectedVid = ref(route.query.vid || null)
const source = ref('loading')
let timer = null
let controller = null

const live = computed(() => activeMap.value[selected.value?.vid] || null)

watch(() => route.query.vid, (v) => {
  if (v) selectedVid.value = v
})
function select(vid) {
  selectedVid.value = vid
  router.replace({ query: { vid } })
}

const LIGHT_IT = {
  low_fuel: 'Carburante basso',
  low_oil: 'Olio basso',
  check_engine: 'Motore',
  tpms: 'Pressione gomme',
}
function light(n) {
  return LIGHT_IT[n] || n
}
function fuelTone(p) {
  if (p > 50) return 'var(--green)'
  if (p > 20) return 'var(--orange)'
  return 'var(--danger)'
}

const query = computed(() => searchQuery.value.trim().toUpperCase())
const filtered = computed(() => {
  if (!query.value) return vehicles.value
  return vehicles.value.filter((v) => (v.vid || '').toUpperCase().includes(query.value))
})
const selected = computed(
  () => vehicles.value.find((v) => v.vid === selectedVid.value) || filtered.value[0] || null,
)

async function load() {
  controller?.abort()
  controller = new AbortController()
  const signal = controller.signal
  try {
    const [veh, act] = await Promise.all([
      fleetApi.getVehicles({ signal }),
      fleetApi.getActive({ signal }),
    ])
    vehicles.value = (Array.isArray(veh) ? veh : []).sort((a, b) => a.vid.localeCompare(b.vid))
    activeMap.value = Object.fromEntries((Array.isArray(act) ? act : []).map((a) => [a.vid, a]))
    source.value = 'live'
  } catch (err) {
    if (err.name === 'AbortError') return
    source.value = 'offline'
  }
}

onMounted(() => {
  load()
  timer = setInterval(load, 2500)
})
onUnmounted(() => {
  if (timer) clearInterval(timer)
  controller?.abort()
})
</script>

<template>
  <div class="page">
    <section class="list-panel">
      <header class="panel__head">
        <span class="cf-eyebrow">Flotta · {{ vehicles.length }} veicoli</span>
      </header>
      <div v-if="filtered.length" class="list">
        <button
          v-for="v in filtered"
          :key="v.vid"
          class="row"
          :class="{ active: selected && selected.vid === v.vid }"
          @click="select(v.vid)"
        >
          <span class="row__plate cf-mono">{{ v.vid }}</span>
          <span class="row__odo cf-mono">{{ Math.round(v.odoKm).toLocaleString('it-IT') }} km</span>
          <span class="row__fuel"><i :style="{ width: v.fuelPct + '%', '--c': fuelTone(v.fuelPct) }" /></span>
          <span v-if="v.lights && v.lights.length" class="row__warn">{{ v.lights.length }}⚠</span>
        </button>
      </div>
      <p v-else class="muted">{{ source === 'offline' ? 'Servizio non raggiungibile.' : 'Nessun veicolo.' }}</p>
    </section>

    <section v-if="selected" class="detail">
      <header class="detail__head">
        <div>
          <span class="cf-eyebrow">Veicolo</span>
          <h2 class="cf-mono">{{ selected.vid }}</h2>
        </div>
        <AppIcon name="car" :size="34" class="detail__icon" />
      </header>

      <div v-if="live" class="livebox">
        <div class="livebox__head">
          <span class="livebox__tag"><i />IN CORSA</span>
          <span class="livebox__mode cf-mono">{{ live.mode }}</span>
          <RouterLink
            v-if="live.did"
            class="livebox__drv link"
            :to="{ path: '/drivers', query: { did: live.did } }"
          >{{ live.name }}</RouterLink>
        </div>
        <div class="tel">
          <div class="tel__cell"><span>Velocità</span><b class="cf-mono">{{ Math.round(live.speed_kmh ?? 0) }}<small>km/h</small></b></div>
          <div class="tel__cell"><span>RPM</span><b class="cf-mono">{{ Math.round(live.rpm ?? 0) }}</b></div>
          <div class="tel__cell" v-if="live.throttle != null"><span>Acceleratore</span><b class="cf-mono">{{ Math.round(live.throttle) }}<small>%</small></b></div>
          <div class="tel__cell" v-if="live.fuel_lph != null"><span>Consumo</span><b class="cf-mono">{{ (live.fuel_lph).toFixed(1) }}<small>L/h</small></b></div>
          <div class="tel__cell" v-if="live.coolant_c != null"><span>Refrig.</span><b class="cf-mono">{{ Math.round(live.coolant_c) }}<small>°C</small></b></div>
          <div class="tel__cell"><span>Posizione</span><b class="cf-mono pos">{{ (live.lat ?? 0).toFixed(4) }}, {{ (live.lon ?? 0).toFixed(4) }}</b></div>
        </div>
        <p v-if="live.mode === 'EDGE'" class="tel__note">Modalità EDGE: dati aggregati ogni 15s (banda ridotta).</p>
      </div>

      <div class="stats">
        <div class="stat"><span>Odometro</span><b class="cf-mono">{{ Math.round(selected.odoKm).toLocaleString('it-IT') }} km</b></div>
        <div class="stat"><span>Viaggi</span><b class="cf-mono">{{ selected.tripCount }}</b></div>
      </div>

      <div class="gauge">
        <div class="gauge__head"><span>Carburante</span><b class="cf-mono">{{ Math.round(selected.fuelPct) }}%</b></div>
        <div class="gauge__track"><i :style="{ width: selected.fuelPct + '%', '--c': fuelTone(selected.fuelPct) }" /></div>
      </div>
      <div class="gauge">
        <div class="gauge__head"><span>Olio</span><b class="cf-mono">{{ Math.round(selected.oilPct) }}%</b></div>
        <div class="gauge__track"><i :style="{ width: selected.oilPct + '%', '--c': fuelTone(selected.oilPct) }" /></div>
      </div>

      <div class="lights">
        <span class="block__label">Spie</span>
        <div v-if="selected.lights && selected.lights.length" class="chips">
          <b v-for="(l, k) in selected.lights" :key="'l' + k" class="warn">⚠ {{ light(l) }}</b>
        </div>
        <span v-else class="ok">Nessuna spia accesa</span>
      </div>

      <div class="drivers">
        <span class="block__label">Ultimi conducenti</span>
        <ul v-if="selected.recentDrivers && selected.recentDrivers.length">
          <li v-for="(d, k) in selected.recentDrivers" :key="'d' + k">
            <span class="dot" />
            <RouterLink class="dname link" :to="{ path: '/drivers', query: { did: d.did } }">{{ d.name }}</RouterLink>
            <span class="cf-mono did">{{ d.did }}</span>
          </li>
        </ul>
        <span v-else class="muted">—</span>
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
  grid-template-columns: auto 1fr auto auto;
  align-items: center;
  gap: 10px;
  width: 100%;
  text-align: left;
  padding: 10px 12px;
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
.row__plate {
  font-weight: 700;
  font-size: 13px;
}
.row__odo {
  font-size: 11px;
  color: var(--faint);
}
.row__fuel {
  width: 46px;
  height: 6px;
  border-radius: 99px;
  background: rgba(255, 255, 255, 0.06);
  overflow: hidden;
}
.row__fuel i {
  display: block;
  height: 100%;
  background: var(--c);
}
.row__warn {
  font-size: 11px;
  color: var(--orange-glow);
}
.detail__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
}
.detail__head h2 {
  font-size: 26px;
  letter-spacing: 0.02em;
  margin-top: 2px;
}
.detail__icon {
  color: var(--cyan);
}
.livebox {
  margin-top: 18px;
  padding: 16px;
  border-radius: var(--r-sm);
  background: linear-gradient(180deg, rgba(43, 255, 158, 0.06), rgba(255, 255, 255, 0.02));
  border: 1px solid color-mix(in srgb, var(--green) 34%, var(--line));
  box-shadow: 0 0 34px -22px var(--green);
}
.livebox__head {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 14px;
}
.livebox__tag {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.14em;
  color: var(--green-glow);
}
.livebox__tag i {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--green);
  animation: cf-pulse 1.9s ease-out infinite;
}
.livebox__mode {
  font-size: 10px;
  letter-spacing: 0.12em;
  padding: 2px 8px;
  border-radius: 6px;
  color: var(--muted);
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid var(--line);
}
.livebox__drv {
  margin-left: auto;
  font-size: 14px;
  font-weight: 600;
}
.tel {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(96px, 1fr));
  gap: 10px;
}
.tel__cell {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 10px 12px;
  border-radius: var(--r-sm);
  background: rgba(0, 0, 0, 0.2);
  border: 1px solid var(--line);
}
.tel__cell span {
  font-size: 10px;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--muted);
}
.tel__cell b {
  font-size: 20px;
  color: var(--text);
}
.tel__cell b small {
  font-size: 10px;
  color: var(--muted);
  margin-left: 2px;
}
.tel__cell b.pos {
  font-size: 13px;
}
.tel__note {
  margin: 10px 0 0;
  font-size: 12px;
  color: var(--orange-glow);
}
.stats {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin: 18px 0;
}
.stat {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 14px;
  border-radius: var(--r-sm);
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid var(--line);
}
.stat span {
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--muted);
}
.stat b {
  font-size: 20px;
  color: var(--text);
}
.gauge {
  margin-top: 12px;
}
.gauge__head {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: var(--muted);
  margin-bottom: 6px;
}
.gauge__head b {
  color: var(--text);
}
.gauge__track {
  height: 9px;
  border-radius: 99px;
  background: rgba(255, 255, 255, 0.05);
  overflow: hidden;
}
.gauge__track i {
  display: block;
  height: 100%;
  border-radius: 99px;
  background: var(--c);
  box-shadow: 0 0 12px var(--c);
  transition: width 0.5s ease;
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
.lights,
.drivers {
  margin-top: 18px;
}
.chips {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.chips b.warn {
  font-weight: 600;
  font-size: 12px;
  padding: 4px 9px;
  border-radius: 7px;
  color: var(--orange-glow);
  background: rgba(255, 122, 26, 0.12);
  border: 1px solid rgba(255, 122, 26, 0.35);
}
.ok {
  font-size: 13px;
  color: var(--green);
}
.drivers ul {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  gap: 8px;
}
.drivers li {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 13px;
  color: var(--text);
}
.dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--green);
  box-shadow: 0 0 8px var(--green);
}
.did {
  margin-left: auto;
  font-size: 11px;
  color: var(--faint);
}
.link {
  color: var(--cyan);
  transition: color 0.15s;
}
.link:hover {
  color: var(--text);
  text-decoration: underline;
}
.muted {
  color: var(--muted);
  font-size: 13px;
}

@media (max-width: 900px) {
  .page {
    grid-template-columns: minmax(0, 1fr);
  }
}
</style>
