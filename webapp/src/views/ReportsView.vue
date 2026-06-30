<script setup>
/* Driving reports — preview of the per-session reports the server emits on
   shutdown (core/fleet/{vid}/session) and hands to the Jakarta EE / LLM service. */
import { computed } from 'vue'
import BaseWidget from '@/components/ui/BaseWidget.vue'
import { useFleet } from '@/composables/useFleet'

const { filteredVehicles } = useFleet()

const reports = computed(() =>
  filteredVehicles.value.map((v) => ({
    vid: v.vid,
    profile: v.profile,
    eco: v.eco,
    safety: v.safety,
    grade: grade((v.eco + v.safety) / 2),
  })),
)

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
</script>

<template>
  <BaseWidget title="Report di guida" eyebrow="Session reports · preview" icon="report">
    <template #meta>
      <span class="src cf-mono">Jakarta · LLM</span>
    </template>

    <p class="lede">
      Ogni sessione di guida (accensione → spegnimento) genera un report. Gli score sono
      deterministici; l'LLM ne scrive solo la narrativa nel modello a clessidra.
    </p>

    <div class="cards">
      <article v-for="r in reports" :key="r.vid" class="card">
        <header class="card__top">
          <span class="card__plate cf-mono">{{ r.vid }}</span>
          <span class="card__grade" :style="{ '--c': tone((r.eco + r.safety) / 2) }">{{ r.grade }}</span>
        </header>
        <span class="card__profile" :data-p="r.profile">{{ r.profile }}</span>

        <div class="metric">
          <div class="metric__head"><span>Sicurezza</span><b class="cf-mono">{{ r.safety }}</b></div>
          <div class="metric__track"><i :style="{ width: r.safety + '%', '--c': tone(r.safety) }" /></div>
        </div>
        <div class="metric">
          <div class="metric__head"><span>Eco</span><b class="cf-mono">{{ r.eco }}</b></div>
          <div class="metric__track"><i :style="{ width: r.eco + '%', '--c': tone(r.eco) }" /></div>
        </div>
      </article>
    </div>
  </BaseWidget>
</template>

<style scoped>
.src {
  font-size: 11px;
  color: var(--purple-glow);
  padding: 3px 9px;
  border-radius: 7px;
  background: rgba(139, 92, 255, 0.12);
  border: 1px solid rgba(139, 92, 255, 0.35);
}
.lede {
  margin: 0 0 18px;
  max-width: 70ch;
  font-size: 14px;
  line-height: 1.5;
  color: var(--muted);
}
.cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(244px, 1fr));
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
  align-items: center;
  justify-content: space-between;
}
.card__plate {
  font-size: 14px;
  font-weight: 700;
  letter-spacing: 0.06em;
  padding: 3px 8px;
  border-radius: 6px;
  background: rgba(125, 150, 255, 0.07);
  border: 1px solid var(--line-strong);
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
}
.card__profile {
  display: inline-block;
  margin: 10px 0 14px;
  font-size: 11px;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--muted);
}
.card__profile[data-p='aggressive'] {
  color: var(--danger);
}
.card__profile[data-p='calm'] {
  color: var(--green);
}
.metric + .metric {
  margin-top: 11px;
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
</style>
