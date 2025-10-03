<template>
  <div class="dashboard">
    <header class="acc-header">
      <div class="header-left">
        <img src="@/assets/ncaa.svg" alt="ACC Logo" class="acc-logo" />
        <div class="header-text">
          <h1>NCAA Championship. Hayward Field Eugene Oregon</h1>
        </div>
      </div>
    </header>

    <div class="tabs">
      <button
        :class="{ active: selectedTab === 'Women' }"
        @click="selectedTab = 'Women'"
      >
        Women
      </button>
      <button
        :class="{ active: selectedTab === 'Men' }"
        @click="selectedTab = 'Men'"
      >
        Men
      </button>
    </div>

    <div class="score-toggle">
      <label>
        <input type="radio" value="projected" v-model="config.viewMode" />
        Projected
      </label>
      <label>
        <input type="radio" value="actual" v-model="config.viewMode" />
        Actual
      </label>
    </div>

    <!-- Loading / Error states -->
    <div v-if="loading">Loading meet data...</div>
    <div v-if="error" style="color: red;">Error loading data: {{ error }}</div>

    <ProjectionsTable
      v-if="!loading && !error"
      :title="selectedTab"
      :rowData="selectedTab === 'Women' ? womenData : menData"
      :columnDefs="selectedTab === 'Women' ? columnDefsWomen : columnDefsMen"
      :defaultColDef="defaultColDef"
      :viewMode="config.viewMode"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useConfigStore } from '@/stores/config.store'
import ProjectionsTable from '@/components/ProjectionsTable.vue'

const selectedTab = ref('Women')
const config = useConfigStore()

// Get meetName from route params
const route = useRoute()
const meetName = ref(route.params.meetName || '')

// Reactive state for JSON data
const womenData = ref([])
const menData = ref([])
const columnDefsWomen = ref([])
const columnDefsMen = ref([])
const loading = ref(true)
const error = ref(null)

const defaultColDef = {
  resizable: false,
  sortable: true,
  filter: false,
}

// Helper to fetch JSON from FastAPI
const fetchJSON = async (url) => {
  const res = await fetch(url)
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
  return await res.json()
}

const fetchMeetData = async () => {
  if (!meetName.value) return
  loading.value = true
  error.value = null
  try {
    const [wData, mData, colW, colM] = await Promise.all([
      fetchJSON(`http://127.0.0.1:8000/get_meet_data/${meetName.value}/womenData`),
      fetchJSON(`http://127.0.0.1:8000/get_meet_data/${meetName.value}/menData`),
      fetchJSON(`http://127.0.0.1:8000/get_meet_data/${meetName.value}/columnDefs.women`),
      fetchJSON(`http://127.0.0.1:8000/get_meet_data/${meetName.value}/columnDefs.men`)
    ])
    womenData.value = wData
    menData.value = mData
    columnDefsWomen.value = colW
    columnDefsMen.value = colM
  } catch (err) {
    error.value = err.message
    console.error(err)
  } finally {
    loading.value = false
  }
}

// Fetch when component mounts and if route param changes
onMounted(fetchMeetData)
watch(() => route.params.meetName, (newVal) => {
  meetName.value = newVal
  fetchMeetData()
})
</script>
