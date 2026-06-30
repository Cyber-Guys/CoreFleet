<script setup>
/* Inline SVG icon set — no icon dependency, renders crisp at any size. */
import { computed } from 'vue'

const props = defineProps({
  name: { type: String, required: true },
  size: { type: [Number, String], default: 20 },
})

const PATHS = {
  gauge: 'M12 13l3-3M3.5 14a8.5 8.5 0 1 1 17 0M12 13a1 1 0 1 0 0 2 1 1 0 0 0 0-2Z',
  report: 'M7 3h7l5 5v13H7zM14 3v5h5M10 13h6M10 17h6M10 9h2',
  info: 'M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18ZM12 11v5M12 8h.01',
  search: 'M11 4a7 7 0 1 0 0 14 7 7 0 0 0 0-14ZM20 20l-3.5-3.5',
  car: 'M5 11l1.6-4.2A2 2 0 0 1 8.5 5.5h7A2 2 0 0 1 17.4 6.8L19 11M4 11h16v5H4zM7.5 16v1.5M16.5 16v1.5M7 13.5h.01M17 13.5h.01',
  cloud: 'M7 18a4 4 0 0 1-.5-7.97A5.5 5.5 0 0 1 17 10.5a3.5 3.5 0 0 1-.5 7H7Z',
  cpu: 'M7 7h10v10H7zM10 10h4v4h-4zM9 3v2M15 3v2M9 19v2M15 19v2M3 9h2M3 15h2M19 9h2M19 15h2',
  activity: 'M3 12h4l2.5 7L14 5l2.5 7H21',
  bolt: 'M13 3 5 13h6l-1 8 8-10h-6z',
  broadcast: 'M12 12a1.5 1.5 0 1 0 0 .01ZM8.5 8.5a5 5 0 0 0 0 7M15.5 8.5a5 5 0 0 1 0 7M6 6a8 8 0 0 0 0 12M18 6a8 8 0 0 1 0 12',
  fuel: 'M6 21V5a2 2 0 0 1 2-2h5a2 2 0 0 1 2 2v16M4 21h13M15 9h2.5A1.5 1.5 0 0 1 19 10.5V16a1.5 1.5 0 0 0 3 0V8l-3-3',
}

const d = computed(() => PATHS[props.name] || PATHS.activity)
</script>

<template>
  <svg
    :width="size"
    :height="size"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="1.7"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
  >
    <path :d="d" />
  </svg>
</template>
