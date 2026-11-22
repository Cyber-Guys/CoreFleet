<script setup>
/* Network analysis: CLOUD and EDGE traffic and energy.
Estimates bandwidth and energy for the current fleet in each mode and shows how
much EDGE saves. Payload sizes match the protocol; fleet size and mode split
come from the store. */
import { computed } from 'vue'
import BaseWidget from '@/components/ui/BaseWidget.vue'
import { useFleet } from '@/composables/useFleet'

const { activeCount, cloudCount, edgeCount, state } = useFleet()

// protocol payload sizes / cadence
const RAW_BYTES = 250 // one CLOUD raw sample
const SUMMARY_BYTES = 240 // one EDGE window summary
const WINDOW_S = 15
const CLOUD_HZ = 1
const JOULES_PER_MB = 1100

const n = computed(() => activeCount.value)

const allCloudBps = computed(() => n.value * RAW_BYTES * CLOUD_HZ)
const allEdgeBps = computed(() => (n.value * SUMMARY_BYTES) / WINDOW_S)
const currentBps = computed(
  () => cloudCount.value * RAW_BYTES * CLOUD_HZ + (edgeCount.value * SUMMARY_BYTES) / WINDOW_S,
)

const reductionPct = computed(() =>
  allCloudBps.value > 0 ? Math.round((1 - allEdgeBps.value / allCloudBps.value) * 100) : 0,
)
const factor = computed(() =>
  allEdgeBps.value > 0 ? (allCloudBps.value / allEdgeBps.value).toFixed(1) : '—',
)

function jPerHour(bps) {
  return (bps * 3600 * JOULES_PER_MB) / 1e6
}
const savedJPerHour = computed(() => jPerHour(allCloudBps.value) - jPerHour(allEdgeBps.value))

function fmtBps(b) {
  return b >= 1000 ? (b / 1000).toFixed(1) + ' kB/s' : Math.round(b) + ' B/s'
}
function fmtJ(j) {
  return j >= 1000 ? (j / 1000).toFixed(1) + ' kJ/h' : Math.round(j) + ' J/h'
}
function barPct(b) {
  return allCloudBps.value > 0 ? Math.max(3, (b / allCloudBps.value) * 100) : 0
}
</script>

<template>
  <div class="wrap">
    <section class="hero">
      <div class="hero__main">
        <span class="cf-eyebrow">Bandwidth reduction · EDGE vs CLOUD</span>
        <div class="hero__num"><span class="cf-mono">{{ reductionPct }}</span><small>%</small></div>
        <p class="hero__sub">
          Aggregating on the edge sends <b>{{ factor }}×</b> less data for the same
          {{ n }} vehicles — the transmission energy drops with it.
        </p>
      </div>
      <div class="hero__side">
        <div class="hero__stat">
          <span class="cf-eyebrow">Energy saved</span>
          <b class="cf-mono">{{ fmtJ(savedJPerHour) }}</b>
        </div>
        <div class="hero__stat">
          <span class="cf-eyebrow">Fleet directive</span>
          <b class="cf-mono" :class="state.fleet.directive === 'EDGE' ? 'edge' : 'cloud'">
            {{ state.fleet.directive }}
          </b>
        </div>
      </div>
    </section>

    <div class="grid">
      <BaseWidget title="All CLOUD" eyebrow="Every vehicle streams 1 Hz raw" icon="cloud" accent="var(--orange)">
        <div class="mode">
          <div class="mode__row"><span>Bandwidth</span><b class="cf-mono">{{ fmtBps(allCloudBps) }}</b></div>
          <div class="mode__bar"><i style="--c: var(--orange)" :style="{ width: barPct(allCloudBps) + '%' }" /></div>
          <div class="mode__row"><span>Energy</span><b class="cf-mono">{{ fmtJ(jPerHour(allCloudBps)) }}</b></div>
          <p class="mode__note">Full fidelity, maximum bandwidth.</p>
        </div>
      </BaseWidget>

      <BaseWidget title="All EDGE" eyebrow="Every vehicle sends a 15 s summary" icon="cpu" accent="var(--purple)">
        <div class="mode">
          <div class="mode__row"><span>Bandwidth</span><b class="cf-mono">{{ fmtBps(allEdgeBps) }}</b></div>
          <div class="mode__bar"><i style="--c: var(--purple-glow)" :style="{ width: barPct(allEdgeBps) + '%' }" /></div>
          <div class="mode__row"><span>Energy</span><b class="cf-mono">{{ fmtJ(jPerHour(allEdgeBps)) }}</b></div>
          <p class="mode__note">Coarser data, drastically lower cost.</p>
        </div>
      </BaseWidget>

      <BaseWidget title="Current fleet" eyebrow="Live mix" icon="activity" accent="var(--cyan)">
        <div class="mode">
          <div class="mode__row"><span>Bandwidth</span><b class="cf-mono">{{ fmtBps(currentBps) }}</b></div>
          <div class="mode__bar"><i style="--c: var(--cyan)" :style="{ width: barPct(currentBps) + '%' }" /></div>
          <div class="mix">
            <span class="mix__item"><i style="--c: var(--orange)" />{{ cloudCount }} Cloud</span>
            <span class="mix__item"><i style="--c: var(--purple-glow)" />{{ edgeCount }} Edge</span>
            <span class="mix__item">{{ n }} active</span>
          </div>
          <p class="mode__note">The server shifts the fleet along this axis as load changes.</p>
        </div>
      </BaseWidget>
    </div>

    <p class="foot">
      Estimated from protocol payload sizes (raw ≈ {{ RAW_BYTES }} B @ 1 Hz, summary ≈
      {{ SUMMARY_BYTES }} B / {{ WINDOW_S }} s) and {{ JOULES_PER_MB }} J/MB. The fleet
      server reports the measured figures in its <code>[stats]</code> logs.
    </p>
  </div>
</template>

<style scoped>
.wrap {
  display: flex;
  flex-direction: column;
  gap: 20px;
}
.hero {
  display: flex;
  gap: 24px;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  padding: 26px 28px;
  border-radius: var(--r);
  background:
    radial-gradient(600px 200px at 90% 0%, rgba(43, 255, 158, 0.12), transparent 60%),
    linear-gradient(180deg, var(--panel-2), var(--panel));
  border: 1px solid color-mix(in srgb, var(--green) 30%, var(--line-strong));
  box-shadow: var(--shadow);
}
.hero__num {
  display: flex;
  align-items: baseline;
  gap: 4px;
  font-family: var(--font-display);
  font-weight: 700;
  line-height: 0.9;
  margin: 6px 0 8px;
}
.hero__num span {
  font-size: clamp(56px, 9vw, 96px);
  color: var(--green);
  text-shadow: 0 0 34px rgba(43, 255, 158, 0.5);
}
.hero__num small {
  font-size: 28px;
  color: var(--green-glow);
}
.hero__sub {
  margin: 0;
  max-width: 52ch;
  font-size: 14px;
  line-height: 1.5;
  color: var(--muted);
}
.hero__sub b {
  color: var(--text);
}
.hero__side {
  display: flex;
  gap: 14px;
}
.hero__stat {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 16px 18px;
  border-radius: var(--r-sm);
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid var(--line);
}
.hero__stat b {
  font-size: 22px;
  color: var(--text);
}
.hero__stat b.cloud {
  color: var(--orange);
}
.hero__stat b.edge {
  color: var(--purple-glow);
}
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 20px;
}
.mode {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.mode__row {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  font-size: 13px;
  color: var(--muted);
}
.mode__row b {
  font-size: 20px;
  color: var(--text);
}
.mode__bar {
  height: 10px;
  border-radius: 99px;
  background: rgba(255, 255, 255, 0.05);
  overflow: hidden;
}
.mode__bar i {
  display: block;
  height: 100%;
  border-radius: 99px;
  background: var(--c);
  box-shadow: 0 0 14px var(--c);
  transition: width 0.5s ease;
}
.mix {
  display: flex;
  flex-wrap: wrap;
  gap: 14px;
  font-size: 12px;
  color: var(--muted);
}
.mix__item {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}
.mix__item i {
  width: 9px;
  height: 9px;
  border-radius: 50%;
  background: var(--c);
  box-shadow: 0 0 8px var(--c);
}
.mode__note {
  margin: 0;
  font-size: 12px;
  color: var(--faint);
}
.foot {
  margin: 0;
  font-size: 12px;
  line-height: 1.5;
  color: var(--faint);
}
.foot code {
  font-family: var(--font-mono);
  color: var(--muted);
}
</style>
