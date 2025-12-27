<template>
  <div class="dashboard">
    <div class="status">
      <h3>Score Status</h3>
      <span>🔵 | Projection</span><br>
      <span>🔴 | In-progress</span><br>
      <span>🟢 | Scored</span><br>
    </div>

    <GenderTabs />

    <!-- Meet Settings link (only if logged in) -->
    <div v-if="auth.user" class="meet-settings-link">
      <router-link :to="settingsLink">Meet Settings</router-link>
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
import { useRoute } from 'vue-router'

import MeetTable from '@/components/meet/MeetTable.vue'
import GenderTabs from '@/components/GenderTabs.vue'

const config = useConfigStore()
const auth = useAuthStore()
const route = useRoute()

// Build link to meet settings
const settingsLink = {
  name: 'MeetSettings',
  params: {
    meetYear: route.params.meetYear,
    meetSeason: route.params.meetSeason,
    meetId: route.params.meetId
  }
}
</script>

<style scoped>
.tabs {
  display: flex;
  justify-content: center;
  margin: 16px 0;
  gap: 10px;
}

.tabs button {
  background: none;
  border: none;
  font-size: 1rem;
  padding: 10px 20px;
  cursor: pointer;
  color: #666;
  position: relative;
  transition: color 0.2s;
}

.tabs button:hover {
  color: #000;
}

.tabs button.active {
  color: #000;
  font-weight: 600;
}

.tabs button.active::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  height: 3px;
  width: 60%;
  background-color: #007bff;
  border-radius: 2px;
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
</style>
