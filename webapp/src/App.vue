<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import AppSidebar from '@/components/AppSidebar.vue'
import AppSearchBar from '@/components/AppSearchBar.vue'
import { useFleet } from '@/composables/useFleet'

const route = useRoute()
const { load, startPolling, stopPolling, state } = useFleet()

const now = ref(new Date())
let clock = null

const pageTitle = computed(() => route.meta.title || 'Dashboard')
const clockText = computed(() =>
  now.value.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
)
const updatedText = computed(() => {
  if (!state.fleet.updatedAt) return '-'
  const s = Math.max(0, Math.round((now.value.getTime() - state.fleet.updatedAt) / 1000))
  return s < 2 ? 'now' : `${s}s ago`
})

onMounted(async () => {
  await load()
  startPolling(2000)
  clock = setInterval(() => (now.value = new Date()), 1000)
})
onUnmounted(() => {
  stopPolling()
  if (clock) clearInterval(clock)
})
</script>

<template>
  <div class="shell">
    <AppSidebar />

    <div class="main">
      <header class="topbar">
        <div class="topbar__title">
          <span class="cf-eyebrow">CoreFleet · {{ state.fleet.directive }}</span>
          <h1>{{ pageTitle }}</h1>
        </div>

        <AppSearchBar />

        <div class="topbar__aside">
          <div class="sync">
            <span class="cf-eyebrow">Sync</span>
            <span class="sync__v cf-mono">{{ updatedText }}</span>
          </div>
          <div class="clock cf-mono">{{ clockText }}</div>
        </div>
      </header>

      <main class="content">
        <RouterView v-slot="{ Component }">
          <component :is="Component" />
        </RouterView>
      </main>
    </div>
  </div>
</template>

<style scoped>
.shell {
  position: relative;
  z-index: 1;
  display: flex;
  min-height: 100vh;
}
.main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}
.topbar {
  position: sticky;
  top: 0;
  z-index: 5;
  display: flex;
  align-items: center;
  gap: 22px;
  padding: 20px 30px;
  background: linear-gradient(180deg, rgba(10, 17, 40, 0.92), rgba(10, 17, 40, 0.6));
  backdrop-filter: blur(10px);
  border-bottom: 1px solid var(--line);
}
.topbar__title {
  display: flex;
  flex-direction: column;
  gap: 3px;
}
.topbar__title h1 {
  font-size: 22px;
  letter-spacing: 0.01em;
}
.topbar__aside {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 18px;
}
.sync {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 2px;
}
.sync__v {
  font-size: 13px;
  color: var(--green);
}
.clock {
  font-size: 15px;
  font-weight: 700;
  color: var(--text);
  padding: 9px 13px;
  border-radius: 11px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid var(--line);
  letter-spacing: 0.06em;
}
.content {
  flex: 1;
  padding: 26px 30px 40px;
}

@media (max-width: 760px) {
  .topbar {
    flex-wrap: wrap;
    gap: 14px;
    padding: 16px 18px;
  }
  .topbar__aside {
    order: 3;
    width: 100%;
    justify-content: space-between;
  }
  .content {
    padding: 18px 16px 32px;
  }
}
</style>
