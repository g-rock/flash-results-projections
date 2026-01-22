<template>
  <div class="dashboard">
    <!-- Tabs + Event Status (desktop & mobile) -->
    <div class="top-row">
      <GenderTabs />

      <EventStatusChart
        class="event-status-chart"
        :numEvents="config.selectedGenderEventStats.numEvents"
        :numEventsScored="config.selectedGenderEventStats.numEventsScored"
        :numEventsProjected="config.selectedGenderEventStats.numEventsProjected"
        :numEventsInProgress="config.selectedGenderEventStats.numEventsInProgress"
      />
    </div>

    <!-- Loading / Error -->
    <div v-if="config.loadingEvents">Loading events...</div>
    <div v-if="config.eventsError" style="color: red;">
      Error loading events: {{ config.eventsError }}
    </div>

    <!-- AG Grid Table -->
    <MeetTable
      v-if="!config.loadingEvents && !config.eventsError"
      :title="config.selectedGender"
      :rowData="config.selectedGenderTableData"
      :columnDefs="config.selectedGenderColumnDefs"
    />
  </div>
</template>

<script setup>
import { useConfigStore } from '@/stores/config.store'
import { useAuthStore } from '@/stores/auth.store'

import MeetTable from '@/components/meet/MeetTable.vue'
import GenderTabs from '@/components/GenderTabs.vue'
import EventStatusChart from '@/components/charts/EventStatusChart.vue'

const config = useConfigStore()
const auth = useAuthStore()
</script>

<style scoped>
/* Active tab underline */
.tabs button.active::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  transform: none;
  height: 3px;
  width: 60%;
  background-color: #007bff;
  border-radius: 2px;
}

/* ===== Tabs + chart layout (desktop & mobile) ===== */
.top-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 0 16px;
}

/* Tabs container */
.top-row :deep(.tabs) {
  display: flex;
  justify-content: flex-start;
  flex: 2;
}

/* Ensure tab buttons align left */
.top-row :deep(.tabs button) {
  text-align: left;
}

/* Chart on the right */
.event-status-chart {
  flex: 1;
  max-width: 33%;
}

.meet-settings-link {
  margin: 12px 0;
}
.meet-settings-link a {
  text-decoration: none;
  color: #007bff;
  font-weight: 500;
}
.meet-settings-link a:hover {
  text-decoration: underline;
}

@media (max-width: 768px) {
  .top-row {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
    gap: 0;
    padding: 0;
  }

  .top-row :deep(.tabs) {
    justify-content: center;
  }

  .event-status-chart {
    max-width: 100%;
    max-height: 100px;
    width: 100%;
    min-width: unset;
  }
}

</style>
