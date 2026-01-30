<template>
  <div class="dashboard">
    <!-- Header with back link -->
    <div class="settings-header">
      <h3>Meet Settings</h3>
    </div>

    <GenderTabs />

    <!-- Loading / Error -->
    <div v-if="config.loadingEvents">Loading events...</div>
    <div v-if="config.eventsError" style="color: red;">
      Error loading events: {{ config.eventsError }}
    </div>

    <!-- Events Table and SB Panel -->
    <div class="events-container" v-if="!config.loadingEvents && !config.eventsError">
      <!-- Event Table -->
      <table class="event-table">
        <thead>
          <tr>
            <th>Event ID</th>
            <th>Event Name</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="event in config.selectedGenderEventData" :key="event.id">
            <td>{{ event.id }}</td>
            <td>{{ event.event_name }}</td>
            <td>
              <button class="btn" @click="toggleSeasonBest(event.id)">Update Season Best</button>
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
              <th>Rk</th>
              <th>ID</th>
              <th>Athlete Name</th>
              <th>Team</th>
              <th>
                Season Best
                <span v-if="['running','relay'].includes(activeEvent.event_type)">(mm:ss.tt)</span>
                <span v-else-if="activeEvent.event_type === 'field'">(xx.xx)</span>
                <span v-else-if="activeEvent.event_type === 'multi'">(xxxx)</span>
              </th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(row, index) in editableSBs" :key="row.athlete_id">
              <td>{{ index + 1 }}</td>
              <td>{{ row.athlete_id }}</td>
              <td>{{ row.athlete_name }}</td>
              <td>{{ row.team_name }}</td>
              <td>
                <input
                  type="text"
                  class="sb-input"
                  :placeholder="getFormatPlaceholder(activeEvent.event_type || 'running')"
                  v-model="row.sb_display"
                  @blur="commitSB(index)"
                  @keydown.enter.prevent="commitSB(index)"
                />
              </td>
            </tr>
          </tbody>
        </table>

        <div class="action-buttons">
          <button class="btn save-btn" @click="saveSeasonBest(activeEvent)">Save</button>
          <button class="btn cancel-btn" @click="cancelSeasonBest">Cancel</button>
        </div>
      </div>
    </div>

    <!-- Saved Banner -->
    <div v-if="showSavedBanner" class="saved-banner">Saved</div>
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
  if (event.project_points_by_sb === undefined) event.project_points_by_sb = false
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
      sb_display: formatValue(r.sb_numeric, newEvent.event_type)
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

/* ---------------- FORMAT HELPERS ---------------- */
function formatValue(value, type) {
  if (value === null || value === undefined || Number.isNaN(value)) {
    // always return the placeholder for invalid/empty values
    return getFormatPlaceholder(type)
  }

  switch(type) {
    case 'running': // mm:ss.tt
    case 'relay':
      const minutes = Math.floor(value / 60)
      const seconds = value - minutes * 60
      return `${minutes}:${seconds.toFixed(2).padStart(5,'0')}`
    case 'field': // xx.xx
      return Number(value).toFixed(2)
    case 'multi': // xxxx
      return Math.round(value)
    default:
      return value
  }
}

function getFormatPlaceholder(type) {
  switch(type) {
    case 'running':
    case 'relay':
      return 'mm:ss.tt'
    case 'field':
      return 'xx.xx'
    case 'multi':
      return 'xxxx'
    default:
      return ''
  }
}

function parseValue(str, type) {
  if (!str) return null
  switch(type) {
    case 'running':
    case 'relay':
      const match = str.match(/^(\d+):(\d{1,2})(?:\.(\d{1,2}))?$/)
      if (!match) return NaN
      const minutes = parseInt(match[1], 10)
      const seconds = parseInt(match[2], 10)
      const hundredths = match[3] ? parseInt(match[3].padEnd(2,'0'),10) : 0
      if (seconds > 59) return NaN
      return minutes*60 + seconds + hundredths/100
    case 'field':
      return parseFloat(str)
    case 'multi':
      const cleaned = str.replace(/\D/g,'')
      return cleaned ? parseInt(cleaned, 10) : NaN
    default:
      return str
  }
}

/* ---------------- ACTIONS ---------------- */
function commitSB(index) {
  const type = activeEvent.value?.event_type || 'running'
  const raw = editableSBs[index].sb_display
  let parsed = null

  if (type === 'multi') {
    const cleaned = raw.replace(/\D/g, '')
    parsed = cleaned ? parseInt(cleaned, 10) : null
  } else if (['running','relay'].includes(type)) {
    const match = raw.match(/^(\d+):(\d{1,2})(?:\.(\d{1,2}))?$/)
    parsed = match ? parseInt(match[1],10)*60 + parseInt(match[2],10) + (match[3]?parseInt(match[3].padEnd(2,'0'),10)/100:0) : null
  } else if (type === 'field') {
    parsed = parseFloat(raw)
  }

  editableSBs[index].sb_seconds = parsed

  // Only format if parsed is valid, otherwise show the correct placeholder format
  if (parsed != null && !Number.isNaN(parsed)) {
    editableSBs[index].sb_display = formatValue(parsed, type)
  } else {
    editableSBs[index].sb_display = getFormatPlaceholder(type)
  }
}

function toggleSeasonBest(eventId) {
  state.activeEventId = state.activeEventId === eventId ? null : eventId
}

function saveSeasonBest(event) {
  editableSBs.forEach(edited => {
    const original = event.projection.event_results.find(r => r.athlete_id === edited.athlete_id)
    if (original) original.sb_numeric = edited.sb_seconds
  })

  config.updateEventDoc(event.id, { projection: event.projection })

  showSavedBanner.value = true
  clearTimeout(bannerTimeout)
  bannerTimeout = setTimeout(() => (showSavedBanner.value = false), 2000)
}

function cancelSeasonBest() {
  state.activeEventId = null
}
</script>

<style scoped>
.settings-header {
  align-items: center;
  margin-bottom: 10px;
}

.back-link {
  text-decoration: none;
  color: #007bff;
  font-weight: 500;
  cursor: pointer;
}

.back-link:hover {
  text-decoration: underline;
}

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

tbody tr:nth-of-type(odd) {
  background-color: #ffffff;
}

tbody tr:nth-of-type(even) {
  background-color: rgba(0,0,0,.05);
}

tbody tr:hover,
tbody tr.active {
  background-color: rgba(0,0,0,.05) !important;
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
