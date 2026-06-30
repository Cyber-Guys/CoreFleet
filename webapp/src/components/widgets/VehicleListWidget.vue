<script setup>
import BaseWidget from '@/components/ui/BaseWidget.vue'
import StatusDot from '@/components/ui/StatusDot.vue'
import { useFleet } from '@/composables/useFleet'

const { filteredVehicles, hasResults, searchQuery } = useFleet()
</script>

<template>
  <BaseWidget title="Veicoli connessi" eyebrow="Registry" icon="gauge">
    <template #meta>
      <span class="counter cf-mono">{{ filteredVehicles.length }}</span>
    </template>

    <ul v-if="hasResults" class="list">
      <li v-for="v in filteredVehicles" :key="v.vid" class="row">
        <StatusDot :size="9" />
        <span class="plate cf-mono">{{ v.vid }}</span>
        <span class="profile" :data-p="v.profile">{{ v.profile }}</span>
        <span class="speed cf-mono">{{ v.speedKmh }}<small>km/h</small></span>
        <span class="mode" :class="v.mode.toLowerCase()">{{ v.mode }}</span>
      </li>
    </ul>

    <div v-else class="empty">
      <span class="empty__glyph">⌀</span>
      <p class="empty__title">Nessun risultato trovato</p>
      <p class="empty__hint">
        Nessun veicolo corrisponde a “<b>{{ searchQuery }}</b>”.
      </p>
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
  /* scrollable area: cap height so the list scrolls inside the widget */
  max-height: 264px;
}
.row {
  display: grid;
  grid-template-columns: auto auto 1fr auto auto;
  align-items: center;
  gap: 12px;
  padding: 11px 14px;
  border-radius: var(--r-sm);
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid var(--line);
  transition: border-color 0.2s ease, transform 0.2s ease, background 0.2s ease;
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
.profile {
  justify-self: start;
  font-size: 11px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--muted);
}
.profile[data-p='aggressive'] {
  color: var(--danger);
}
.profile[data-p='calm'] {
  color: var(--green);
}
.speed {
  font-size: 13px;
  color: var(--muted);
}
.speed small {
  font-size: 9px;
  margin-left: 2px;
  opacity: 0.7;
}
.mode {
  font-family: var(--font-mono);
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.1em;
  padding: 3px 8px;
  border-radius: 6px;
}
.mode.cloud {
  color: var(--orange-glow);
  background: rgba(255, 122, 26, 0.12);
  border: 1px solid rgba(255, 122, 26, 0.35);
}
.mode.edge {
  color: var(--purple-glow);
  background: rgba(139, 92, 255, 0.14);
  border: 1px solid rgba(139, 92, 255, 0.4);
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
