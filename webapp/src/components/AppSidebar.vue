<script setup>
import AppIcon from '@/components/ui/AppIcon.vue'
import StatusDot from '@/components/ui/StatusDot.vue'
import { useFleet } from '@/composables/useFleet'

const { state, activeCount } = useFleet()

const nav = [
  { to: '/', label: 'Dashboard', icon: 'gauge' },
  { to: '/vehicles', label: 'Vehicles', icon: 'car' },
  { to: '/drivers', label: 'Drivers', icon: 'users' },
  { to: '/network', label: 'Network', icon: 'activity' },
  { to: '/reports', label: 'Reports', icon: 'report' },
  { to: '/about', label: 'About', icon: 'info' },
]
</script>

<template>
  <aside class="rail">
    <div class="brand">
      <span class="brand__mark"><AppIcon name="broadcast" :size="22" /></span>
      <span class="brand__text">
        <b>CoreFleet</b>
        <small>Control Room</small>
      </span>
    </div>

    <nav class="nav">
      <RouterLink
        v-for="item in nav"
        :key="item.to"
        :to="item.to"
        class="nav__link"
        active-class="is-active"
        :exact-active-class="item.to === '/' ? 'is-active' : ''"
      >
        <AppIcon :name="item.icon" :size="20" />
        <span>{{ item.label }}</span>
        <i class="nav__rail" />
      </RouterLink>
    </nav>

    <div class="status">
      <div class="status__row">
        <StatusDot :size="8" :color="state.fleet.online ? 'var(--green)' : 'var(--danger)'" :live="state.fleet.online" />
        <span>{{ state.fleet.online ? 'Fleet API online' : 'Fleet API offline' }}</span>
      </div>
      <p class="status__router cf-mono">mode · {{ state.fleet.directive }}</p>
      <div class="status__metric">
        <span class="cf-eyebrow">Active</span>
        <span class="status__n cf-mono">{{ activeCount }}</span>
      </div>
    </div>
  </aside>
</template>

<style scoped>
.rail {
  position: sticky;
  top: 0;
  height: 100vh;
  width: var(--rail);
  flex: none;
  display: flex;
  flex-direction: column;
  padding: 22px 16px;
  background: linear-gradient(180deg, rgba(139, 92, 255, 0.06), transparent 28%), var(--bg-elev);
  border-right: 1px solid var(--line);
}
.brand {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 6px 8px 22px;
}
.brand__mark {
  display: grid;
  place-items: center;
  width: 42px;
  height: 42px;
  border-radius: 12px;
  color: var(--bg);
  background: linear-gradient(135deg, var(--cyan), var(--purple));
  box-shadow: 0 0 24px -4px var(--purple);
  flex: none;
}
.brand__text {
  display: flex;
  flex-direction: column;
  line-height: 1.1;
}
.brand__text b {
  font-family: var(--font-display);
  font-size: 18px;
  letter-spacing: 0.02em;
}
.brand__text small {
  font-size: 11px;
  color: var(--faint);
  letter-spacing: 0.06em;
}

.nav {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-top: 8px;
}
.nav__link {
  position: relative;
  display: flex;
  align-items: center;
  gap: 13px;
  padding: 12px 14px;
  border-radius: var(--r-sm);
  color: var(--muted);
  font-size: 14px;
  font-weight: 500;
  letter-spacing: 0.01em;
  transition: color 0.2s ease, background 0.2s ease;
}
.nav__link:hover {
  color: var(--text);
  background: rgba(255, 255, 255, 0.03);
}
.nav__link.is-active {
  color: var(--text);
  background: linear-gradient(90deg, rgba(139, 92, 255, 0.16), rgba(139, 92, 255, 0.02));
}
.nav__rail {
  position: absolute;
  left: -16px;
  top: 50%;
  transform: translateY(-50%) scaleY(0);
  width: 3px;
  height: 22px;
  border-radius: 0 4px 4px 0;
  background: var(--purple-glow);
  box-shadow: 0 0 12px var(--purple-glow);
  transition: transform 0.2s ease;
}
.nav__link.is-active .nav__rail {
  transform: translateY(-50%) scaleY(1);
}

.status {
  margin-top: auto;
  padding: 14px;
  border-radius: var(--r-sm);
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid var(--line);
}
.status__row {
  display: flex;
  align-items: center;
  gap: 9px;
  font-size: 12px;
  color: var(--text);
}
.status__router {
  margin: 8px 0 12px;
  font-size: 11px;
  color: var(--faint);
  word-break: break-all;
}
.status__metric {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-top: 10px;
  border-top: 1px solid var(--line);
}
.status__n {
  font-size: 18px;
  font-weight: 700;
  color: var(--green);
}

@media (max-width: 920px) {
  .rail {
    width: 76px;
    padding: 18px 12px;
  }
  .brand__text,
  .nav__link span,
  .status__router,
  .status__row span,
  .status__metric .cf-eyebrow {
    display: none;
  }
  .nav__link {
    justify-content: center;
    padding: 12px 0;
  }
  .status {
    display: grid;
    place-items: center;
  }
}
</style>
