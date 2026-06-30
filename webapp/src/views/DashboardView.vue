<script setup>
import ActiveVehiclesWidget from '@/components/widgets/ActiveVehiclesWidget.vue'
import StatusWidget from '@/components/widgets/StatusWidget.vue'
import ModeChartWidget from '@/components/widgets/ModeChartWidget.vue'
import VehicleListWidget from '@/components/widgets/VehicleListWidget.vue'
</script>

<template>
  <div class="grid">
    <ActiveVehiclesWidget class="grid__a" />
    <StatusWidget class="grid__b" />
    <ModeChartWidget class="grid__c" />
    <VehicleListWidget class="grid__d" />
  </div>
</template>

<style scoped>
.grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  grid-template-rows: minmax(220px, auto) minmax(280px, auto);
  gap: 20px;
}
.grid > * {
  animation: cf-rise 0.45s ease both;
}
.grid__b {
  animation-delay: 0.06s;
}
.grid__c {
  animation-delay: 0.12s;
}
.grid__d {
  animation-delay: 0.18s;
}

@media (max-width: 1040px) {
  .grid {
    grid-template-columns: minmax(0, 1fr);
    grid-template-rows: none;
  }
}
</style>
