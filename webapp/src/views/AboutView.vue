<script setup>
import BaseWidget from '@/components/ui/BaseWidget.vue'
import AppIcon from '@/components/ui/AppIcon.vue'

const pillars = [
  {
    icon: 'broadcast',
    title: 'Telemetria su Zenoh',
    body: 'Ogni veicolo è un dispositivo edge (OBD2 + GPS + IMU) che pubblica le telemetrie sul router Zenoh.',
  },
  {
    icon: 'cpu',
    title: 'Cloud ↔ Edge adattivo',
    body: 'Il server misura la banda e commuta la flotta tra streaming in tempo reale (CLOUD) e aggregazione locale (EDGE).',
  },
  {
    icon: 'report',
    title: 'Report con LLM',
    body: 'A fine sessione un servizio Jakarta EE genera il report di guida secondo il modello a clessidra.',
  },
]
</script>

<template>
  <div class="about">
    <BaseWidget title="CoreFleet SDV" eyebrow="About" icon="info" accent="var(--cyan)" scan>
      <p class="hero">
        Una flotta di <b>car/taxi sharing</b> in cui le auto della startup vengono affidate ai
        driver. I dispositivi IoT a bordo trasmettono le telemetrie in tempo reale lungo il
        <b>continuum cloud–edge</b>, riducendo banda ed energia quando la rete si satura.
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
