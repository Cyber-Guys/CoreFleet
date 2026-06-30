<script setup>
/* Reusable HUD panel. The accent colour drives the border, glow and header chip
   so every widget shares one structural language. */
import AppIcon from './AppIcon.vue'

defineProps({
  title: { type: String, required: true },
  eyebrow: { type: String, default: '' },
  icon: { type: String, default: 'activity' },
  accent: { type: String, default: 'var(--purple)' },
  scan: { type: Boolean, default: false },
})
</script>

<template>
  <section class="widget" :style="{ '--wc': accent }">
    <div v-if="scan" class="widget__scan" aria-hidden="true"><i /></div>

    <header class="widget__head">
      <span class="widget__chip"><AppIcon :name="icon" :size="18" /></span>
      <div class="widget__titles">
        <span v-if="eyebrow" class="cf-eyebrow">{{ eyebrow }}</span>
        <h3 class="widget__title">{{ title }}</h3>
      </div>
      <div class="widget__meta"><slot name="meta" /></div>
    </header>

    <div class="widget__body">
      <slot />
    </div>
  </section>
</template>

<style scoped>
.widget {
  position: relative;
  display: flex;
  flex-direction: column;
  min-height: 0;
  padding: 20px 22px;
  border-radius: var(--r);
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.025), transparent 42%),
    linear-gradient(180deg, var(--panel-2), var(--panel));
  border: 1px solid color-mix(in srgb, var(--wc) 34%, var(--line-strong));
  box-shadow:
    var(--shadow),
    0 0 0 1px rgba(0, 0, 0, 0.25) inset,
    0 0 34px -22px color-mix(in srgb, var(--wc) 80%, transparent);
  overflow: hidden;
}
/* top accent rail */
.widget::before {
  content: '';
  position: absolute;
  inset: 0 0 auto 0;
  height: 2px;
  background: linear-gradient(90deg, transparent, var(--wc), transparent);
  opacity: 0.85;
}

.widget__scan {
  position: absolute;
  inset: 2px 0 auto 0;
  height: 100%;
  overflow: hidden;
  pointer-events: none;
}
.widget__scan i {
  position: absolute;
  top: 0;
  left: 0;
  width: 22%;
  height: 100%;
  background: linear-gradient(90deg, transparent, color-mix(in srgb, var(--wc) 16%, transparent), transparent);
  animation: cf-sweep 6.5s linear infinite;
}

.widget__head {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}
.widget__chip {
  display: grid;
  place-items: center;
  width: 38px;
  height: 38px;
  border-radius: 11px;
  color: var(--wc);
  background: color-mix(in srgb, var(--wc) 14%, transparent);
  border: 1px solid color-mix(in srgb, var(--wc) 38%, transparent);
  flex: none;
}
.widget__titles {
  display: flex;
  flex-direction: column;
  gap: 3px;
  min-width: 0;
}
.widget__title {
  font-size: 15px;
  letter-spacing: 0.02em;
  color: var(--text);
}
.widget__meta {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 8px;
}
.widget__body {
  position: relative;
  z-index: 1;
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}
</style>
