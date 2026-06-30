<script setup>
import BaseWidget from '@/components/ui/BaseWidget.vue'
import StatusDot from '@/components/ui/StatusDot.vue'
import { useFleet } from '@/composables/useFleet'

const { activeCount, cloudCount, edgeCount } = useFleet()
</script>

<template>
  <BaseWidget title="Veicoli Attivi" eyebrow="Fleet / live" icon="car" scan>
    <template #meta>
      <span class="live"><StatusDot :size="9" /> LIVE</span>
    </template>

    <div class="readout">
      <span class="count cf-mono">{{ String(activeCount).padStart(2, '0') }}</span>
      <span class="unit">veicoli<br />connessi</span>
    </div>

    <div class="split">
      <div class="split__item">
        <span class="split__dot" style="--c: var(--orange)" />
        <span class="split__n cf-mono">{{ cloudCount }}</span>
        <span class="split__l">Cloud</span>
      </div>
      <div class="split__item">
        <span class="split__dot" style="--c: var(--purple-glow)" />
        <span class="split__n cf-mono">{{ edgeCount }}</span>
        <span class="split__l">Edge</span>
      </div>
    </div>
  </BaseWidget>
</template>

<style scoped>
.live {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  font-family: var(--font-mono);
  font-size: 11px;
  letter-spacing: 0.16em;
  color: var(--green-glow);
}
.readout {
  display: flex;
  align-items: baseline;
  gap: 14px;
}
.count {
  font-family: var(--font-display);
  font-weight: 700;
  font-size: clamp(54px, 7vw, 78px);
  line-height: 0.9;
  color: var(--text);
  text-shadow: 0 0 26px rgba(139, 92, 255, 0.55);
}
.unit {
  font-size: 13px;
  line-height: 1.25;
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: 0.06em;
}
.split {
  margin-top: auto;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
  padding-top: 18px;
}
.split__item {
  display: flex;
  align-items: center;
  gap: 9px;
  padding: 10px 13px;
  border-radius: var(--r-sm);
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid var(--line);
}
.split__dot {
  width: 9px;
  height: 9px;
  border-radius: 50%;
  background: var(--c);
  box-shadow: 0 0 10px var(--c);
}
.split__n {
  font-size: 20px;
  font-weight: 700;
  color: var(--text);
}
.split__l {
  margin-left: auto;
  font-size: 12px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--muted);
}
</style>
