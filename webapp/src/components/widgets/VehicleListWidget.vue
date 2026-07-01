<script setup>
/* Connected vehicles — live "who is driving now" from the Jakarta service.
   Row → that vehicle's stats; driver name → that driver's stats. */
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import BaseWidget from '@/components/ui/BaseWidget.vue'
import StatusDot from '@/components/ui/StatusDot.vue'
import { useFleet } from '@/composables/useFleet'
import { fleetApi } from '@/services/fleetApi'

const { searchQuery } = useFleet()
const router = useRouter()

const active = ref([])
const source = ref('loading')
let timer = null
let controller = null

const query = computed(() => searchQuery.value.trim().toUpperCase())
const rows = computed(() => {
  const list = [...active.value].sort((a, b) => a.vid.localeCompare(b.vid))
  if (!query.value) return list
  return list.filter((r) =>
    [r.vid, r.name].some((s) => (s || '').toUpperCase().includes(query.value)),
  )
})
const hasRows = computed(() => rows.value.length > 0)

function openVehicle(vid) {
  router.push({ path: '/vehicles', query: { vid } })
}

async function load() {
  controller?.abort()
  controller = new AbortController()
  try {
    const data = await fleetApi.getActive({ signal: controller.signal })
    active.value = Array.isArray(data) ? data : []
    source.value = 'live'
  } catch (err) {
    if (err.name === 'AbortError') return
    source.value = 'offline'
  }
}

onMounted(() => {
  load()
  timer = setInterval(load, 3000)
})
onUnmounted(() => {
  if (timer) clearInterval(timer)
  controller?.abort()
})
</script>

<template>
  <BaseWidget title="Connected vehicles" eyebrow="Registry · live" icon="gauge">
    <template #meta>
      <span class="counter cf-mono">{{ active.length }}</span>
    </template>

    <ul v-if="hasRows" class="list">
      <li
        v-for="r in rows"
        :key="r.vid"
        class="row"
        role="button"
        tabindex="0"
        @click="openVehicle(r.vid)"
        @keydown.enter="openVehicle(r.vid)"
      >
        <StatusDot :size="9" />
        <span class="plate cf-mono">{{ r.vid }}</span>
        <span class="wheel">⇢</span>
        <RouterLink
          v-if="r.did"
          class="driver"
          :to="{ path: '/drivers', query: { did: r.did } }"
          @click.stop
        >{{ r.name || r.did }}</RouterLink>
        <span v-else class="driver muted">—</span>
        <span v-if="r.speed_kmh != null" class="speed cf-mono">{{ Math.round(r.speed_kmh) }}<small>km/h</small></span>
        <span class="chev">›</span>
      </li>
    </ul>

    <div v-else class="empty">
      <span class="empty__glyph">◴</span>
      <p class="empty__title">{{ source === 'offline' ? 'Service unreachable' : 'No vehicles on the road' }}</p>
      <p class="empty__hint">Populates when drivers are out driving.</p>
    </div>
  </BaseWidget>
</template>

<style scoped>
.counter {
  font-size: 13px;
  font-weight: 700;
  color: var(--muted);
  padding: 3px 9px;
  border-radius: 7px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid var(--line);
}
.list {
  list-style: none;
  margin: 0;
  padding: 2px 6px 2px 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
  overflow-y: auto;
  max-height: 264px;
}
.row {
  display: grid;
  grid-template-columns: auto auto auto 1fr auto auto;
  align-items: center;
  gap: 10px;
  padding: 11px 14px;
  border-radius: var(--r-sm);
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid var(--line);
  cursor: pointer;
  transition: border-color 0.2s, transform 0.2s, background 0.2s;
  animation: cf-rise 0.3s ease both;
}
.row:hover {
  transform: translateX(2px);
  border-color: color-mix(in srgb, var(--purple) 45%, var(--line));
  background: rgba(139, 92, 255, 0.06);
}
.plate {
  font-size: 14px;
  font-weight: 700;
  letter-spacing: 0.06em;
  color: var(--text);
  padding: 3px 8px;
  border-radius: 6px;
  background: rgba(125, 150, 255, 0.07);
  border: 1px solid var(--line-strong);
}
.wheel {
  color: var(--faint);
  font-size: 13px;
}
.driver {
  justify-self: start;
  font-size: 13px;
  color: var(--cyan);
  transition: color 0.15s;
}
.driver:hover {
  color: var(--text);
  text-decoration: underline;
}
.driver.muted {
  color: var(--faint);
}
.speed {
  font-size: 13px;
  font-weight: 700;
  color: var(--green-glow);
}
.speed small {
  font-size: 9px;
  color: var(--muted);
  margin-left: 2px;
  font-weight: 400;
}
.chev {
  color: var(--faint);
  font-size: 18px;
}
.empty {
  flex: 1;
  display: grid;
  place-content: center;
  text-align: center;
  gap: 4px;
  padding: 24px 0;
}
.empty__glyph {
  font-size: 38px;
  color: var(--faint);
  line-height: 1;
}
.empty__title {
  margin: 6px 0 0;
  font-family: var(--font-display);
  font-size: 15px;
  color: var(--text);
}
.empty__hint {
  margin: 0;
  font-size: 12px;
  color: var(--muted);
}
</style>
