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
          <tr
            v-for="event in config.selectedGenderEventData"
            :key="event.id"
          >
            <td>{{ event.id }}</td>
            <td>{{ event.event_name }}</td>
            <td>
              <select
                v-model="event.project_points_by_sb"
                @change="updateProjectPoints(event)"
              >
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
          Update Season Best for
          {{ config.selectedGender === 'men' ? 'Men' : 'Women' }}
          {{ activeEvent.event_name }}
        </h4>

        <table class="sb-table">
          <thead>
            <tr>
              <th>Athlete Name</th>
              <th>Team</th>
              <th>Season Best (mm:ss.ss)</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="(row, index) in editableSBs"
              :key="row.athlete_id"
            >
              <td>{{ row.athlete_name }}</td>
              <td>{{ row.team_name }}</td>
              <td>
                <input
                  type="text"
                  class="sb-input"
                  placeholder="mm:ss.ss"
                  v-model="row.sb_display"
                  @blur="commitSB(index)"
                  @keydown.enter.prevent="commitSB(index)"
                />
              </td>
            </tr>
          </tbody>
        </table>

        <div class="action-buttons">
          <button class="btn save-btn" @click="saveSeasonBest(activeEvent)">
            Save
          </button>
          <button class="btn cancel-btn" @click="cancelSeasonBest">
            Cancel
          </button>
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

/* ---------------- STATE ---------------- */

const showSavedBanner = ref(false)
let bannerTimeout = null

config.selectedGenderEventData.forEach(event => {
  if (event.project_points_by_sb === undefined)
    event.project_points_by_sb = false
  if (!event.projection) event.projection = { event_results: [] }
})

const state = reactive({ activeEventId: null })

const activeEvent = computed(() =>
  config.selectedGenderEventData.find(e => e.id === state.activeEventId)
)

const editableSBs = reactive([])

/* ---------------- WATCH ACTIVE EVENT ---------------- */

watch(
  () => activeEvent.value,
  newEvent => {
    editableSBs.splice(0)
    if (!newEvent?.projection?.event_results) return

    const mapped = newEvent.projection.event_results.map(r => ({
      athlete_id: r.athlete_id,
      athlete_name: r.athlete_name,
      team_name: r.team_name,
      sb_seconds: r.sb_numeric ?? null,
      sb_display: secondsToMMSS(r.sb_numeric)
    }))

    mapped.sort((a, b) => {
      const aVal = Number.isNaN(a.sb_seconds) ? Infinity : a.sb_seconds ?? 0
      const bVal = Number.isNaN(b.sb_seconds) ? Infinity : b.sb_seconds ?? 0
      return newEvent.sort_ascending ? aVal - bVal : bVal - aVal
    })

    editableSBs.push(...mapped)
  },
  { immediate: true }
)

/* ---------------- TIME HELPERS ---------------- */

function secondsToMMSS(seconds) {
  if (Number.isNaN(seconds)) return 'NaN'
  if (seconds === null || seconds === undefined) return ''

  const total = Number(seconds)
  const minutes = Math.floor(total / 60)
  const remaining = total - minutes * 60

  return `${minutes}:${remaining.toFixed(2).padStart(5, '0')}`
}

function mmssToSeconds(value) {
  if (value === 'NaN') return NaN
  if (!value) return null

  const match = value.match(/^(\d+):(\d{1,2})(?:\.(\d{1,2}))?$/)
  if (!match) return NaN

  const minutes = parseInt(match[1], 10)
  const seconds = parseInt(match[2], 10)
  const hundredths = match[3]
    ? parseInt(match[3].padEnd(2, '0'), 10)
    : 0

  if (seconds > 59) return NaN

  return minutes * 60 + seconds + hundredths / 100
}

function commitSB(index) {
  const parsed = mmssToSeconds(editableSBs[index].sb_display)
  editableSBs[index].sb_seconds = parsed
  editableSBs[index].sb_display = secondsToMMSS(parsed)
}

/* ---------------- ACTIONS ---------------- */

function toggleSeasonBest(eventId) {
  state.activeEventId =
    state.activeEventId === eventId ? null : eventId
}

function updateProjectPoints(event) {
  config.updateEventDoc(event.id, {
    project_points_by_sb: event.project_points_by_sb
  })
}

function saveSeasonBest(event) {
  editableSBs.forEach(edited => {
    const original = event.projection.event_results.find(
      r => r.athlete_id === edited.athlete_id
    )

    if (original) {
      original.sb_numeric = edited.sb_seconds
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

.event-table {
  border-collapse: collapse;
  width: 50%;
}

.event-table th,
.event-table td {
  border: 1px solid #ccc;
  padding: 6px 8px;
}

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
}

.sb-input {
  width: 95px;
  text-align: center;
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
  z-index: 1000;
}

/* Mobile */
@media (max-width: 768px) {
  .events-container {
    flex-direction: column;
  }

  .event-table,
  .season-best-container {
    width: 100%;
  }
}
</style>
