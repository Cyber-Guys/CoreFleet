<script setup>
/* Report history: the driver reports generated from the Drivers tab. Polls the
Jakarta history endpoint. */
import { computed, onMounted, onUnmounted, ref } from 'vue'
import BaseWidget from '@/components/ui/BaseWidget.vue'
import DriverReportCard from '@/components/DriverReportCard.vue'
import { fleetApi } from '@/services/fleetApi'
import { useFleet } from '@/composables/useFleet'

const { searchQuery } = useFleet()

const history = ref([])
const source = ref('loading') // 'loading' | 'live' | 'offline'
let timer = null
let controller = null

const query = computed(() => searchQuery.value.trim().toUpperCase())
const reports = computed(() => {
  if (!query.value) return history.value
  return history.value.filter((r) =>
    [r.driverName, r.did].some((s) => (s || '').toUpperCase().includes(query.value)),
  )
})
const hasResults = computed(() => reports.value.length > 0)
const empty = computed(() => !query.value && reports.value.length === 0)

async function load() {
  controller?.abort()
  controller = new AbortController()
  try {
    const data = await fleetApi.getReports({ signal: controller.signal })
    history.value = Array.isArray(data) ? data : []
    source.value = 'live'
  } catch (err) {
    if (err.name === 'AbortError') return
    source.value = 'offline'
  }
}

onMounted(() => {
  load()
  timer = setInterval(load, 5000)
})
onUnmounted(() => {
  if (timer) clearInterval(timer)
  controller?.abort()
})
</script>

<template>
  <BaseWidget title="Report History" eyebrow="Generated reports" icon="report">
    <template #meta>
      <span class="src" :class="source">
        <i />{{ source === 'live' ? 'LIVE' : source === 'loading' ? '…' : 'OFFLINE' }}
      </span>
    </template>

    <p class="lede">
      History of reports generated on demand from the <b>Drivers</b> tab. A report is not
      regenerated while the driver's data is unchanged (cached).
    </p>

    <div v-if="hasResults" class="cards">
      <DriverReportCard v-for="(r, i) in reports" :key="(r.did || '') + '-' + (r.generatedAt || i)" :report="r" />
    </div>

    <div v-else-if="empty" class="empty">
      <span class="empty__glyph">◴</span>
      <p class="empty__title">No reports yet</p>
      <p class="empty__hint">Go to <b>Drivers</b>, pick a driver and press “Generate Report”.</p>
    </div>

    <div v-else class="empty">
      <span class="empty__glyph">⌀</span>
      <p class="empty__title">No results found</p>
      <p class="empty__hint">No report matches “<b>{{ searchQuery }}</b>”.</p>
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
.src.offline {
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
.cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 14px;
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
