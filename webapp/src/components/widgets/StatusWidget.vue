<script setup>
/* Global transmission directive the server broadcasts on core/fleet/mode. */
import { computed } from 'vue'
import BaseWidget from '@/components/ui/BaseWidget.vue'
import { useFleet } from '@/composables/useFleet'

const { state, cloudCount, edgeCount } = useFleet()

const mode = computed(() => state.fleet.directive)
const isEdge = computed(() => mode.value === 'EDGE')
const accentColor = computed(() => (isEdge.value ? 'var(--purple-glow)' : 'var(--orange)'))
const reason = computed(() =>
  isEdge.value
    ? 'Channel saturated — vehicles aggregate on the edge'
    : 'Bandwidth available — real-time streaming',
)

function pct(n) {
  const total = cloudCount.value + edgeCount.value || 1
  return `${Math.round((n / total) * 100)}%`
}
</script>

<template>
  <BaseWidget title="Status" eyebrow="Server / directive" icon="broadcast" :accent="accentColor">
    <template #meta>
      <span class="tag" :style="{ '--c': accentColor }">{{ mode }}</span>
    </template>

    <div class="state">
      <span class="state__label">Active</span>
      <span class="state__mode cf-mono" :style="{ '--c': accentColor }">{{ mode }}</span>
    </div>
    <p class="reason">{{ reason }}</p>

    <div class="bars">
      <div class="bar">
        <div class="bar__head">
          <span>Cloud</span><span class="cf-mono">{{ cloudCount }}</span>
        </div>
        <div class="bar__track">
          <i style="--c: var(--orange)" :style="{ width: pct(cloudCount) }" />
        </div>
      </div>
      <div class="bar">
        <div class="bar__head">
          <span>Edge</span><span class="cf-mono">{{ edgeCount }}</span>
        </div>
        <div class="bar__track">
          <i style="--c: var(--purple-glow)" :style="{ width: pct(edgeCount) }" />
        </div>
      </div>
    </div>
  </BaseWidget>
</template>

<style scoped>
.tag {
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.12em;
  color: var(--c);
  padding: 4px 9px;
  border-radius: 7px;
  background: color-mix(in srgb, var(--c) 14%, transparent);
  border: 1px solid color-mix(in srgb, var(--c) 40%, transparent);
}
.state {
  display: flex;
  align-items: baseline;
  gap: 14px;
}
.state__label {
  font-size: 14px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--muted);
}
.state__mode {
  font-family: var(--font-display);
  font-weight: 700;
  font-size: clamp(38px, 5vw, 52px);
  line-height: 1;
  color: var(--c);
  text-shadow: 0 0 24px color-mix(in srgb, var(--c) 60%, transparent);
}
.reason {
  margin: 12px 0 0;
  font-size: 13px;
  color: var(--muted);
}
.bars {
  margin-top: auto;
  display: grid;
  gap: 12px;
  padding-top: 18px;
}
.bar__head {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--muted);
  margin-bottom: 6px;
}
.bar__track {
  height: 7px;
  border-radius: 99px;
  background: rgba(255, 255, 255, 0.05);
  overflow: hidden;
}
.bar__track i {
  display: block;
  height: 100%;
  border-radius: 99px;
  background: var(--c);
  box-shadow: 0 0 12px var(--c);
  transition: width 0.5s ease;
}
</style>
