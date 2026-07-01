<script setup>
/* Renders a generated DriverReport (LLM aggregate over a driver's trips). */
defineProps({
  report: { type: Object, required: true },
})

const BEHAVIOUR_IT = {
  harsh_accel: 'accelerate brusche',
  harsh_brake: 'frenate brusche',
  speeding: 'eccesso velocità',
  overrev: 'fuorigiri',
  cold_overrev: 'fuorigiri a freddo',
  excess_idle: 'sosta eccessiva',
}
function behaviour(n) {
  return BEHAVIOUR_IT[n] || n
}
function tone(s) {
  if (s >= 80) return 'var(--green)'
  if (s >= 60) return 'var(--orange)'
  return 'var(--danger)'
}
function when(ts) {
  if (!ts) return ''
  return new Date(ts).toLocaleTimeString('it-IT', { hour: '2-digit', minute: '2-digit' })
}
</script>

<template>
  <article class="rep">
    <header class="rep__top">
      <div class="who">
        <span class="who__name">{{ report.driverName }}</span>
        <span class="who__sub cf-mono">{{ report.did }}</span>
      </div>
      <span class="rep__grade" :style="{ '--c': tone(((report.avgSafety || 0) + (report.avgEco || 0)) / 2) }">
        {{ report.overallGrade }}
      </span>
    </header>

    <div class="kpis">
      <span><b class="cf-mono">{{ report.tripCount }}</b> viaggi</span>
      <span><b class="cf-mono">{{ Math.round(report.totalKm) }}</b> km</span>
      <span><b class="cf-mono">{{ report.infractions }}</b> multe</span>
      <span v-if="report.cached" class="cached">cache</span>
      <span v-else class="fresh">nuovo</span>
      <span v-if="report.generatedAt" class="ts">{{ when(report.generatedAt) }}</span>
    </div>

    <div class="metric">
      <div class="metric__head"><span>Sicurezza media</span><b class="cf-mono">{{ report.avgSafety }}</b></div>
      <div class="metric__track"><i :style="{ width: (report.avgSafety || 0) + '%', '--c': tone(report.avgSafety || 0) }" /></div>
    </div>
    <div class="metric">
      <div class="metric__head"><span>Eco media</span><b class="cf-mono">{{ report.avgEco }}</b></div>
      <div class="metric__track"><i :style="{ width: (report.avgEco || 0) + '%', '--c': tone(report.avgEco || 0) }" /></div>
    </div>

    <div v-if="report.recidivist && report.recidivist.length" class="recid">
      <span class="recid__label">⟳ Recidivo su</span>
      <span class="chips"><b v-for="(b, k) in report.recidivist" :key="'rc' + k">{{ behaviour(b) }}</b></span>
    </div>

    <p v-if="report.summary" class="rep__summary">{{ report.summary }}</p>

    <div v-if="report.strengths && report.strengths.length" class="block">
      <span class="block__label">Punti di forza</span>
      <ul class="block__list block__list--ok">
        <li v-for="(t, k) in report.strengths.slice(0, 4)" :key="'s' + k">{{ t }}</li>
      </ul>
    </div>
    <div v-if="report.recommendations && report.recommendations.length" class="block">
      <span class="block__label">Consigli</span>
      <ul class="block__list">
        <li v-for="(t, k) in report.recommendations.slice(0, 4)" :key="'r' + k">{{ t }}</li>
      </ul>
    </div>
    <div v-if="report.maintenanceHints && report.maintenanceHints.length" class="block">
      <span class="block__label">Manutenzione</span>
      <ul class="block__list block__list--warn">
        <li v-for="(t, k) in report.maintenanceHints.slice(0, 4)" :key="'m' + k">{{ t }}</li>
      </ul>
    </div>

    <div v-if="report.hourglass" class="hourglass">
      <span class="block__label">Hourglass</span>
      <div class="hourglass__row" v-if="report.hourglass.stakeholders">
        <span class="hourglass__k">Stakeholder</span>
        <span class="chips"><b v-for="(s, k) in report.hourglass.stakeholders" :key="'st' + k">{{ s }}</b></span>
      </div>
      <div class="hourglass__row hourglass__row--waist" v-if="report.hourglass.capabilities">
        <span class="hourglass__k">Capabilities</span>
        <span class="chips"><b v-for="(s, k) in report.hourglass.capabilities" :key="'cp' + k">{{ s }}</b></span>
      </div>
      <div class="hourglass__row" v-if="report.hourglass.standardsGroups">
        <span class="hourglass__k">Standards</span>
        <span class="chips"><b v-for="(s, k) in report.hourglass.standardsGroups" :key="'sg' + k">{{ s }}</b></span>
      </div>
    </div>
  </article>
</template>

<style scoped>
.rep {
  padding: 16px;
  border-radius: var(--r-sm);
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid var(--line);
  animation: cf-rise 0.35s ease both;
}
.rep__top {
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
  color: var(--faint);
}
.rep__grade {
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
.kpis {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px 14px;
  margin-top: 12px;
  font-size: 12px;
  color: var(--muted);
}
.kpis b {
  color: var(--text);
  font-size: 14px;
}
.cached,
.fresh {
  font-family: var(--font-mono);
  font-size: 10px;
  letter-spacing: 0.1em;
  padding: 2px 7px;
  border-radius: 6px;
}
.cached {
  color: var(--muted);
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid var(--line);
}
.fresh {
  color: var(--green-glow);
  background: rgba(43, 255, 158, 0.1);
  border: 1px solid rgba(43, 255, 158, 0.3);
}
.ts {
  margin-left: auto;
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--faint);
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
  color: var(--orange-glow);
}
.rep__summary {
  margin: 12px 0 0;
  font-size: 13px;
  line-height: 1.5;
  color: var(--text);
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
.block__list--ok li {
  color: var(--green-glow);
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
.hourglass__row--waist .chips b {
  color: var(--purple-glow);
  background: rgba(139, 92, 255, 0.12);
  border-color: rgba(139, 92, 255, 0.34);
}
</style>
