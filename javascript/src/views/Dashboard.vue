<template>
  <div class="dashboard">
    <div class="header-text">
      <h1>{{ currentMeet?.name || 'Loading...' }}</h1>
      <span>Meet ID: {{ currentMeet?.id }}</span>
    </div>

    <div class="status">
      <h3>Score Status</h3>
      <span>🔵 | Startlist Projection</span><br>
      <span>🟣 | Prelim Projection</span><br>
      <span>🟡 | Semis Projection</span><br>
      <span>🟢 | Scored</span><br>
    </div>

    <!-- Gender Tabs -->
    <div class="tabs">
      <button
        :class="{ active: config.selectedGender === 'women' }"
        @click="config.setSelectedGender('women')"
      >
        Women
      </button>
      <button
        :class="{ active: config.selectedGender === 'men' }"
        @click="config.setSelectedGender('men')"
      >
        Men
      </button>
    </div>

    <!-- Loading / Error -->
    <div v-if="config.loadingEvents">Loading events...</div>
    <div v-if="config.eventsError" style="color: red;">
      Error loading events: {{ config.eventsError }}
    </div>

    <!-- AG Grid Table -->
    <ProjectionsTable
      v-if="!config.loadingEvents && !config.eventsError"
      :title="config.selectedGender"
      :rowData="config.gridRowData"
      :columnDefs="config.columnDefs"
      :defaultColDef="defaultColDef"
      :viewMode="config.viewMode"
    />
  </div>
</template>

<script setup>
import { computed, watch, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useConfigStore } from '@/stores/config.store'
import ProjectionsTable from '@/components/ProjectionsTable.vue'

const config = useConfigStore()
const route = useRoute()

// Current meet based on route param
const currentMeet = computed(() =>
  config.meets.find(meet => meet.id === route.params.meetId)
)

// Load events for the current meet
const loadEvents = () => {
  const meetId = route.params.meetId
  if (meetId) config.fetchEvents(meetId)
}

// Watch for gender change or route change
watch(
  [() => config.selectedGender, () => route.params.meetId],
  () => loadEvents()
)

onMounted(() => {
  if (!config.meets.length) {
    config.fetchMeets().then(loadEvents)
  } else {
    loadEvents()
  }
})

const defaultColDef = {
  resizable: true,
  sortable: true,
  filter: false,
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
  background-color: #007bff; /* or your theme color */
  border-radius: 2px;
}
</style>
