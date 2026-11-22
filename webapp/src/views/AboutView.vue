<script setup>
import BaseWidget from '@/components/ui/BaseWidget.vue'
import AppIcon from '@/components/ui/AppIcon.vue'

const pillars = [
  {
    icon: 'broadcast',
    title: 'Telemetry over Zenoh',
    body: 'Every vehicle is an edge device (OBD2 + GPS + IMU) publishing telemetry to the Zenoh router.',
  },
  {
    icon: 'cpu',
    title: 'Adaptive Cloud ↔ Edge',
    body: 'The server measures bandwidth and switches the fleet between real-time streaming (CLOUD) and local aggregation (EDGE).',
  },
  {
    icon: 'report',
    title: 'LLM reports',
    body: 'A Jakarta EE service generates on-demand driver reports mapped onto the Hourglass Model.',
  },
]
</script>

<template>
  <div class="about">
    <BaseWidget title="CoreFleet" eyebrow="About" icon="info" accent="var(--cyan)" scan>
      <p class="hero">
        A <b>car / taxi sharing</b> fleet where the startup's cars are handed to drivers.
        On-board IoT devices stream telemetry in real time along the
        <b>cloud-edge continuum</b>, cutting bandwidth and energy when the network saturates.
      </p>

      <div class="pillars">
        <div v-for="p in pillars" :key="p.title" class="pillar">
          <span class="pillar__icon"><AppIcon :name="p.icon" :size="20" /></span>
          <h4>{{ p.title }}</h4>
          <p>{{ p.body }}</p>
        </div>
      </div>

      <div class="meta">
        <span class="cf-eyebrow">CEI-Sphere Hackathon · Code the Continuum</span>
        <span class="cf-eyebrow">Challenge 1 · Eclipse Zenoh &nbsp;+&nbsp; Challenge 3 · Jakarta EE + LLM</span>
      </div>
    </BaseWidget>
  </div>
</template>

<style scoped>
.about {
  max-width: 980px;
}
.hero {
  margin: 0 0 24px;
  max-width: 72ch;
  font-size: 17px;
  line-height: 1.6;
  color: var(--text);
}
.hero b {
  color: var(--cyan);
  font-weight: 600;
}
.pillars {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 14px;
}
.pillar {
  padding: 18px;
  border-radius: var(--r-sm);
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid var(--line);
}
.pillar__icon {
  display: grid;
  place-items: center;
  width: 40px;
  height: 40px;
  border-radius: 11px;
  color: var(--cyan);
  background: rgba(34, 211, 255, 0.1);
  border: 1px solid rgba(34, 211, 255, 0.32);
  margin-bottom: 12px;
}
.pillar h4 {
  font-size: 15px;
  margin-bottom: 7px;
}
.pillar p {
  margin: 0;
  font-size: 13px;
  line-height: 1.5;
  color: var(--muted);
}
.meta {
  display: flex;
  flex-wrap: wrap;
  gap: 6px 18px;
  margin-top: 24px;
  padding-top: 18px;
  border-top: 1px solid var(--line);
}
</style>
