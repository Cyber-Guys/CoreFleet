<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { ArcElement, Chart, DoughnutController, Tooltip } from 'chart.js'
import BaseWidget from '@/components/ui/BaseWidget.vue'
import { useFleet } from '@/composables/useFleet'

Chart.register(DoughnutController, ArcElement, Tooltip)

const CLOUD = '#ff7a1a'
const EDGE = '#b794ff'

const { cloudCount, edgeCount } = useFleet()
const total = computed(() => cloudCount.value + edgeCount.value)
const cloudPct = computed(() => (total.value ? Math.round((cloudCount.value / total.value) * 100) : 0))

const canvas = ref(null)
let chart = null

function data() {
  return {
    labels: ['Cloud', 'Edge'],
    datasets: [
      {
        data: [cloudCount.value, edgeCount.value],
        backgroundColor: [CLOUD, EDGE],
        hoverBackgroundColor: [CLOUD, EDGE],
        borderWidth: 0,
        borderRadius: 8,
        spacing: 4,
      },
    ],
  }
}

onMounted(() => {
  chart = new Chart(canvas.value, {
    type: 'doughnut',
    data: data(),
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: '72%',
      animation: { duration: 600 },
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: '#0c1631',
          borderColor: 'rgba(125,150,255,0.24)',
          borderWidth: 1,
          titleColor: '#e8edff',
          bodyColor: '#8a98c8',
          padding: 10,
          callbacks: { label: (c) => ` ${c.label}: ${c.parsed} vehicles` },
        },
      },
    },
  })
})

watch([cloudCount, edgeCount], () => {
  if (!chart) return
  // mutate the existing dataset in place so Chart.js tweens from the current
  // arc values instead of re-animating from zero
  chart.data.datasets[0].data = [cloudCount.value, edgeCount.value]
  chart.update()
})

onBeforeUnmount(() => chart?.destroy())
</script>

<template>
  <BaseWidget title="Cloud vs Edge" eyebrow="Transmission split" icon="activity">
    <div class="chart">
      <div class="chart__canvas">
        <canvas ref="canvas" />
        <div class="chart__center">
          <span class="chart__total cf-mono">{{ total }}</span>
          <span class="chart__hint">{{ cloudPct }}% cloud</span>
        </div>
      </div>

      <ul class="legend">
        <li>
          <span class="legend__sw" style="--c: #ff7a1a" />
          <span class="legend__name">Cloud</span>
          <span class="legend__val cf-mono">{{ cloudCount }}</span>
        </li>
        <li>
          <span class="legend__sw" style="--c: #b794ff" />
          <span class="legend__name">Edge</span>
          <span class="legend__val cf-mono">{{ edgeCount }}</span>
        </li>
      </ul>
    </div>
  </BaseWidget>
</template>

<style scoped>
.chart {
  flex: 1;
  display: grid;
  grid-template-columns: 1.1fr 1fr;
  gap: 18px;
  align-items: center;
  min-height: 0;
}
.chart__canvas {
  position: relative;
  min-height: 150px;
  height: 100%;
  display: grid;
  place-items: center;
}
/* luminescent glow on the doughnut arcs (no hard border) */
.chart__canvas canvas {
  filter: drop-shadow(0 0 9px rgba(255, 122, 26, 0.4)) drop-shadow(0 0 9px rgba(139, 92, 255, 0.35));
}
.chart__center {
  position: absolute;
  inset: 0;
  display: grid;
  place-content: center;
  text-align: center;
  pointer-events: none;
}
.chart__total {
  font-family: var(--font-display);
  font-weight: 700;
  font-size: 38px;
  line-height: 1;
  color: var(--text);
}
.chart__hint {
  margin-top: 4px;
  font-size: 11px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--orange-glow);
}
.legend {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  gap: 10px;
}
.legend li {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 11px 13px;
  border-radius: var(--r-sm);
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid var(--line);
}
.legend__sw {
  width: 11px;
  height: 11px;
  border-radius: 3px;
  background: var(--c);
  box-shadow: 0 0 10px var(--c);
}
.legend__name {
  font-size: 13px;
  color: var(--muted);
  letter-spacing: 0.04em;
}
.legend__val {
  margin-left: auto;
  font-size: 17px;
  font-weight: 700;
  color: var(--text);
}
</style>
