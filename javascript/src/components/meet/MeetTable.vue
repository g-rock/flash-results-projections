<template>
  <div class="results-table-wrapper">
    <div class="tooltip-toggle">
      <label>
        <input type="checkbox" v-model="showHover" />
        Show hover tooltips
      </label>
    </div>

    <div class="table-scroll">
      <table class="results-table">
        <colgroup>
          <col
            v-for="col in columnDefs"
            :key="col.field"
            :style="getColStyle(col)"
          />
        </colgroup>

        <thead>
          <tr>
            <th
              v-for="(col, index) in columnDefs"
              :key="col.field"
              ref="headerCells"
              @click="onSort(col)"
              :class="[
                { sortable: col.sortable !== false, active: isSortFieldActive(col) },
                stickyClass(col),
                getEventHeaderClass(col)
              ]"
              :style="stickyStyle(col)"
            >
              <div class="cell-inner">
                {{ col.headerName }}
                <span v-if="sortField === col.field">
                  {{ sortDirection === 'asc' ? '▲' : '▼' }}
                </span>
              </div>
            </th>
          </tr>
        </thead>

        <tbody>
          <tr v-for="row in sortedRows" :key="row._id">
            <td
              v-for="col in columnDefs"
              :key="col.field"
              :class="stickyClass(col)"
              :style="stickyStyle(col)"
            >
              <!-- MAIN CELL CONTENT -->
              <div class="cell-inner">
                <template v-if="col.field === 'logo'">
                  <img
                    v-if="row.team_abbr"
                    :src="getLogoUrl(row)"
                    :alt="row.team + ' logo'"
                    class="team-logo"
                    loading="lazy"
                    @error="e => (e.target.style.display = 'none')"
                  />
                </template>

                <template v-else>
                  <span
                    v-if="isEventCell(row, col.field)"
                    class="event-cell"
                  >
                    {{ formatNumber(row[col.field].event_pts) }}
                  </span>

                  <span v-else>
                    {{ formatNumber(row[col.field]) }}
                  </span>
                </template>
              </div>

              <!-- TOOLTIP -->
              <div
                v-if="isEventCell(row, col.field) && showHover"
                class="event-tooltip"
              >
                <div class="tooltip-header">
                  <span>Athlete</span>
                  <span>Score</span>
                </div>

                <template v-if="row[col.field].scorers?.length">
                  <div
                    v-for="(scorer, idx) in row[col.field].scorers"
                    :key="idx"
                    class="tooltip-row"
                  >
                    <span class="tooltip-name">{{ scorer.athlete_name }}</span>
                    <span class="tooltip-score">{{ formatNumber(scorer.score) }}</span>
                  </div>
                </template>

                <div v-else class="tooltip-empty">
                  No participating athletes
                </div>
              </div>

            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, watch } from 'vue'

const props = defineProps({
  title: String,
  rowData: { type: Array, default: () => [] },
  columnDefs: { type: Array, default: () => [] }
})

// ----------------------
// Sorting
// ----------------------
const sortField = ref(null)
const sortDirection = ref('desc')
const showHover = ref(true)

function onSort(col) {
  if (col.sortable === false) return

  const sortKey = col.meta?.isEventColumn ? `${col.field}.event_pts` : col.field

  if (sortField.value === sortKey) {
    if (sortDirection.value === 'desc') sortDirection.value = 'asc'
    else if (sortDirection.value === 'asc') {
      sortDirection.value = null
      sortField.value = null
    }
  } else {
    sortField.value = sortKey
    sortDirection.value = 'desc'
  }
}

const sortedRows = computed(() => {
  if (!props.rowData.length) return []

  if (!sortField.value || !sortDirection.value) {
    return [...props.rowData].sort((a, b) => (a.rank || 0) - (b.rank || 0))
  }

  return [...props.rowData].sort((a, b) => {
    const aVal = getSortValue(a, sortField.value)
    const bVal = getSortValue(b, sortField.value)

    const aNum = parseFloat(aVal)
    const bNum = parseFloat(bVal)

    if (!isNaN(aNum) && !isNaN(bNum)) {
      return sortDirection.value === 'asc' ? aNum - bNum : bNum - aNum
    }

    return sortDirection.value === 'asc'
      ? String(aVal).localeCompare(String(bVal))
      : String(bVal).localeCompare(String(aVal))
  })
})

// helper to get value from nested keys like "19.event_pts"
function getSortValue(row, key) {
  if (!key.includes('.')) return row[key]
  return key.split('.').reduce((obj, k) => (obj ? obj[k] : undefined), row)
}

const LOGO_BASE_URL = 'https://storage.googleapis.com/projections-data/logos/NCAA'

function getLogoUrl(row) {
  if (!row.team_abbr) return null
  return `${LOGO_BASE_URL}/${row.team_abbr}.png`
}

function isSortFieldActive(col) {
  const sortKey = col.meta?.isEventColumn ? `${col.field}.event_pts` : col.field
  return sortField.value === sortKey
}

function isEventCell(row, field) {
  return (
    row[field] &&
    typeof row[field] === 'object' &&
    'event_pts' in row[field]
  )
}

function getEventHeaderClass(col) {
  if (!col.meta?.isEventColumn) return ''
  return col.meta.status ? `status-${col.meta.status}` : ''
}

function formatNumber(value) {
  const num = parseFloat(value)
  if (isNaN(num)) return value
  return Number.isInteger(num) ? num : num.toFixed(2)
}

// ----------------------
// Sticky Columns (Dynamic Widths)
// ----------------------
const headerCells = ref([])
const stickyOffsets = ref({})

function stickyClass(col) {
  return col.sticky ? 'sticky' : ''
}

function stickyStyle(col) {
  if (!col.sticky) return {}
  return {
    position: 'sticky',
    left: `${stickyOffsets.value[col.field] || 0}px`,
  }
}

function calculateStickyOffsets() {
  const offsets = {}
  let left = 0

  props.columnDefs.forEach((col, index) => {
    if (!col.sticky) return

    offsets[col.field] = left

    const el = headerCells.value[index]
    if (el) left += el.offsetWidth
  })

  stickyOffsets.value = offsets
}

onMounted(async () => {
  await nextTick()
  calculateStickyOffsets()
  window.addEventListener('resize', calculateStickyOffsets)
})

watch(
  () => props.columnDefs,
  async () => {
    await nextTick()
    calculateStickyOffsets()
  },
  { deep: true }
)

// ----------------------
// Optional: Column Styles
// ----------------------
function getColStyle(col) {
  if (col.field === 'logo') return { minWidth: '40px' }
  return {}
}
</script>

<style scoped>
.results-table-wrapper {
  width: calc(100vw - 16px);
  padding: 0 16px;
  margin: auto;
  box-sizing: border-box;
}

.table-scroll {
  width: 100%;
  max-height: calc(100vh - 90px - 100px - 40px);
  overflow: auto;
  border: 1px solid #cccccc;
  border-radius: 4px;
}


.results-table {
  border-collapse: collapse;
  table-layout: fixed;
  min-width: 100%;
  font-size: 0.95rem;
}

th,
td {
  position: relative;
}

th.sticky,
td.sticky {
  z-index: 3;
}

thead th.sticky {
  z-index: 4;
}

.cell-inner {
  padding: 8px 10px;
  white-space: nowrap;
  overflow: hidden;
}

thead th {
  background: #f8f8f8;
  border-bottom: 2px solid #ccc;
  font-weight: 600;
  text-align: left;
}

thead th {
  position: sticky;
  top: 0;                   /* stick to top of the scroll container */
  z-index: 1;               /* higher than other cells to overlap */
}

th.status-scored, th.status-official {
  background-color: #63BE7B;
  color: #1D6F42;
}

th.status-projection {
  background-color: #e5f7ff;
  color: #007ac6;
}

/* Rows */
tbody tr:nth-of-type(odd) {
  background-color: #ffffff;
}

tbody tr:nth-of-type(even) {
  background-color: #f2f2f2;
}

tr:nth-child(odd) td.sticky {
  background-color: #ffffff;
}

tr:nth-child(even) td.sticky {
  background-color: #f2f2f2;
}

tbody tr:hover {
  background-color: #dcdcdc;
}

.event-tooltip {
  display: none;
  position: absolute;
  top: 100%;
  left: 0;

  margin-top: 6px;
  padding: 8px 10px;
  min-width: 200px;

  border: 1px solid #ccc;
  border-radius: 4px;

  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.25);
  z-index: 9999;

  background-color: #ffffff;
}

td:hover .event-tooltip {
  display: block;
}

.tooltip-toggle { 
  height: 20px;
}
.tooltip-header {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  color: #666;
  border-bottom: 1px solid #ddd;
  padding-bottom: 4px;
  margin-bottom: 6px;
}

.tooltip-row {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  font-size: 0.85rem;
  line-height: 1.4;
  padding: 2px 0;
}

.tooltip-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.tooltip-score {
  font-weight: 600;
}

.tooltip-empty {
  font-size: 0.8rem;
  color: #777;
  font-style: italic;
  padding: 4px 0;
}

.team-logo {
  width: 18px;
  height: 18px;
  object-fit: contain;
}

@media (max-width: 1000px) {
  .results-table-wrapper {
    width: 100vw;
    padding: 0;
  }

  .table-scroll {
    max-height: calc(100vh - 150px);
  }
}
</style>
