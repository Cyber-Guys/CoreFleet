<script setup>
/* Fleet search. Two-way bound to the store; filtering happens in useFleet. */
import { computed } from 'vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import { useFleet } from '@/composables/useFleet'

const { searchQuery, setSearch, filteredVehicles } = useFleet()

const value = computed({
  get: () => searchQuery.value,
  set: (v) => setSearch(v),
})
</script>

<template>
  <div class="search" role="search">
    <AppIcon name="search" :size="18" class="search__icon" />
    <input
      v-model="value"
      type="text"
      class="search__input"
      placeholder="Cerca per targa o profilo…"
      aria-label="Cerca veicoli per targa o profilo"
      spellcheck="false"
    />
    <span v-if="value" class="search__count cf-mono">{{ filteredVehicles.length }}</span>
    <button v-if="value" class="search__clear" type="button" aria-label="Pulisci ricerca" @click="setSearch('')">
      ✕
    </button>
  </div>
</template>

<style scoped>
.search {
  display: flex;
  align-items: center;
  gap: 11px;
  width: min(440px, 46vw);
  padding: 0 14px;
  height: 46px;
  border-radius: 13px;
  background: rgba(255, 255, 255, 0.025);
  border: 1px solid var(--line-strong);
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}
.search:focus-within {
  border-color: color-mix(in srgb, var(--cyan) 55%, transparent);
  box-shadow: 0 0 0 4px rgba(34, 211, 255, 0.12), 0 0 30px -10px var(--cyan);
}
.search__icon {
  color: var(--muted);
  flex: none;
}
.search__input {
  flex: 1;
  min-width: 0;
  background: none;
  border: none;
  outline: none;
  color: var(--text);
  font-size: 14px;
  letter-spacing: 0.02em;
}
.search__input::placeholder {
  color: var(--faint);
}
.search__count {
  font-size: 12px;
  color: var(--cyan);
  padding: 2px 8px;
  border-radius: 6px;
  background: rgba(34, 211, 255, 0.1);
}
.search__clear {
  display: grid;
  place-items: center;
  width: 24px;
  height: 24px;
  border-radius: 7px;
  border: none;
  cursor: pointer;
  color: var(--muted);
  background: rgba(255, 255, 255, 0.05);
  font-size: 12px;
  transition: color 0.2s ease, background 0.2s ease;
}
.search__clear:hover {
  color: var(--text);
  background: rgba(255, 255, 255, 0.12);
}

@media (max-width: 620px) {
  .search {
    width: 100%;
  }
}
</style>
