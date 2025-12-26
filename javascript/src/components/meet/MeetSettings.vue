<template>
  <div class="dashboard">
    <h3>Meet Settings</h3>
    <GenderTabs />

    <div class="events-container">
      <!-- Event Table -->
      <table class="event-table">
        <thead>
          <tr>
            <th>Event ID</th>
            <th>Event Name</th>
            <th>Project Points By SB</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="event in config.selectedGenderEventData" :key="event.id">
            <td>{{ event.id }}</td>
            <td>{{ event.event_name }}</td>
            <td>
              <select v-model="event.project_points_by_sb" @change="updateProjectPoints(event)">
                <option :value="true">Yes</option>
                <option :value="false">No</option>
              </select>
            </td>
            <td>
              <button class="btn" @click="toggleSeasonBest(event.id)">
                Update Season Best
              </button>
            </td>
          </tr>
        </tbody>
      </table>

      <!-- Season Best Panel -->
      <div class="season-best-container" v-if="activeEvent">
        <h4>
          Update Season Best for {{ config.selectedGender === 'men' ? 'Men' : 'Women' }} 
          {{ activeEvent.event_name }}
        </h4>

        <table class="sb-table">
          <thead>
            <tr>
              <th>Athlete Name</th>
              <th>Team</th>
              <th>Season Best</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(result, index) in editableSBs" :key="result.athlete_id">
              <td>{{ result.athlete_name }}</td>
              <td>{{ result.team_name }}</td>
              <td>
                <input
                  type="text"
                  v-model="editableSBs[index].sb_numeric"
                  placeholder="Enter SB time"
                />
              </td>
            </tr>
          </tbody>
        </table>

        <div class="action-buttons">
          <button class="btn save-btn" @click="saveSeasonBest(activeEvent)">Save</button>
          <button class="btn cancel-btn" @click="cancelSeasonBest()">Cancel</button>
        </div>
      </div>
    </div>

    <div v-if="showSavedBanner" class="saved-banner">
      Saved
    </div>
  </div>
</template>

<script setup>
import { reactive, computed, watch, ref } from 'vue'
import { useConfigStore } from '@/stores/config.store'
import GenderTabs from '@/components/GenderTabs.vue'

const config = useConfigStore()
const showSavedBanner = ref(false)
let bannerTimeout = null

config.selectedGenderEventData.forEach(event => {
  if (event.project_points_by_sb === undefined) event.project_points_by_sb = false
  if (!event.projection) event.projection = { event_results: [] }
})

const state = reactive({ activeEventId: null })

const activeEvent = computed(() =>
  config.selectedGenderEventData.find(e => e.id === state.activeEventId)
)

const editableSBs = reactive([])

watch(
  () => activeEvent.value,
  (newEvent) => {
    editableSBs.splice(0)
    if (newEvent?.projection?.event_results) {
      const mappedSBs = newEvent.projection.event_results.map(r => ({
        athlete_id: r.athlete_id,
        athlete_name: r.athlete_name,
        team_name: r.team_name,
        sb_numeric: r.sb_numeric !== null && r.sb_numeric !== undefined
          ? parseFloat(r.sb_numeric).toFixed(2)
          : ''
      }))
      mappedSBs.sort((a, b) => {
        const aVal = parseFloat(a.sb_numeric) || 0
        const bVal = parseFloat(b.sb_numeric) || 0
        return newEvent.sort_ascending ? aVal - bVal : bVal - aVal
      })
      editableSBs.push(...mappedSBs)
    }
  },
  { immediate: true }
)

function toggleSeasonBest(eventId) {
  state.activeEventId = state.activeEventId === eventId ? null : eventId
}

function updateProjectPoints(event) {
  config.updateEventDoc(event.id, { project_points_by_sb: event.project_points_by_sb })
}

function saveSeasonBest(event) {
  editableSBs.forEach(edited => {
    const original = event.projection.event_results.find(
      r => r.athlete_id === edited.athlete_id
    )
    if (original) {
      original.sb_numeric =
        edited.sb_numeric !== '' ? parseFloat(edited.sb_numeric) : null
    }
  })

  config.updateEventDoc(event.id, { projection: event.projection })

  showSavedBanner.value = true
  clearTimeout(bannerTimeout)
  bannerTimeout = setTimeout(() => {
    showSavedBanner.value = false
  }, 2000)
}

function cancelSeasonBest() {
  state.activeEventId = null
}
</script>

<style scoped>
.events-container {
  display: flex;
  gap: 20px;
  align-items: flex-start;
}

/* Event table */
.event-table {
  border-collapse: collapse;
  width: 50%;
}

.event-table th,
.event-table td {
  border: 1px solid #ccc;
  padding: 6px 8px;
  text-align: left;
}

/* Season best panel */
.season-best-container {
  flex: 1;
  border: 1px solid #ccc;
  padding: 10px;
}

.sb-table {
  border-collapse: collapse;
  width: 100%;
}

.sb-table th,
.sb-table td {
  border: 1px solid #ccc;
  padding: 6px 8px;
  text-align: left;
}

.sb-input {
  width: 80px;
}

.action-buttons {
  margin-top: 10px;
}

.save-btn {
  margin-right: 5px;
  background-color: #4caf50;
  color: white;
}

.cancel-btn {
  background-color: #f44336;
  color: white;
}

.btn {
  padding: 2px 6px;
  font-size: 0.85rem;
  cursor: pointer;
}

.saved-banner {
  position: fixed;
  bottom: 0;
  left: 0;
  width: 100%;
  background-color: #4caf50;
  color: white;
  text-align: center;
  padding: 12px 0;
  font-weight: 600;
  letter-spacing: 0.5px;
  z-index: 1000;
}

/* ---------------- MOBILE RESPONSIVE ---------------- */
@media (max-width: 768px) {
  .events-container {
    flex-direction: column;
  }

  .event-table,
  .season-best-container {
    width: 100%;
  }

  .event-table th,
  .event-table td,
  .sb-table th,
  .sb-table td {
    font-size: 0.85rem;
    padding: 4px 6px;
  }
}
</style>
