<script setup>
/* Pulsing presence indicator. Green = alive (Zenoh liveliness token held). */
defineProps({
  color: { type: String, default: 'var(--green)' },
  size: { type: Number, default: 10 },
  live: { type: Boolean, default: true },
})
</script>

<template>
  <span
    class="dot"
    :class="{ live }"
    :style="{ '--dot': color, width: size + 'px', height: size + 'px' }"
  />
</template>

<style scoped>
.dot {
  display: inline-block;
  border-radius: 50%;
  background: var(--dot);
  flex: none;
}
.dot.live {
  animation: cf-pulse 1.9s ease-out infinite;
}
</style>
