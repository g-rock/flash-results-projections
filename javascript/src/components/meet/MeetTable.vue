<template>
  <div class="results-table-wrapper">
    <!-- Tooltip toggle -->
    <div class="tooltip-toggle">
      <label>
        <input type="checkbox" v-model="showHover" />
        Show tooltips
      </label>
    </div>

    <div class="table-scroll" ref="tableScrollRef">
      <table class="results-table">
        <colgroup>
          <col v-for="col in columnDefs" :key="col.field" :style="getColStyle(col)" />
        </colgroup>

        <thead>
          <tr>
            <th
              v-for="(col, index) in columnDefs"
              :key="col.field"
              ref="headerCells"
              @click="onSort(col); debouncedFlashHeaderTooltip(col, 1000)"
              :class="[
                { sortable: col.sortable !== false, active: isSortFieldActive(col) },
                stickyClass(col),
                getEventHeaderClass(col)
              ]"
              :style="stickyStyle(col)"
            >
              <div
                class="cell-inner header-cell"
                @mouseenter="showHeaderTooltip($event, col)"
                @mouseleave="hideHeaderTooltip"
              >
                {{ col.headerName }}
                <span v-if="col.sortable !== false" class="sort-triangle">
                  {{ isSortFieldActive(col) ? (sortDirection === 'asc' ? '▲' : '▼') : '' }}
                </span>

                <!-- Tooltip -->
                <div
                  v-if="activeHeaderTooltip === col.field && showHover"
                  ref="headerTooltip"
                  class="header-tooltip"
                  :style="headerTooltipStyle"
                >
                  {{ getFullHeaderName(col) }}
                </div>
              </div>
            </th>
          </tr>
        </thead>

        <tbody>
          <tr v-for="row in sortedRows" :key="row._id">
            <td
                v-for="col in columnDefs"
                :key="col.field"
                :class="[stickyClass(col), { 
                  'active-event-cell': activeEventCell.value?.rowId === row._id && activeEventCell.value?.field === col.field
                }]"
                :style="stickyStyle(col)"
                @mouseenter="!isTouchDevice && isEventCell(row, col.field) ? showEventTooltip($event, row, col) : null"
                @mouseleave="!isTouchDevice && hideEventTooltip"
                @click="isEventCell(row, col.field) ? toggleEventTooltip($event, row, col) : null"
              >
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
                  <span v-if="isEventCell(row, col.field)" class="event-cell">
                    {{ formatNumber(row[col.field].event_pts) }}
                  </span>
                  <span v-else>
                    {{ formatNumber(row[col.field]) }}
                  </span>
                </template>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Floating Event Tooltip -->
    <div
      v-if="floatingEventTooltip.show"
      class="event-tooltip"
      :style="{ top: floatingEventTooltip.top, left: floatingEventTooltip.left }"
    >
      <div class="tooltip-header">
        <span>Athlete</span>
        <span>Score</span>
      </div>

      <template v-if="floatingEventTooltip.scorers?.length">
        <div
          v-for="(scorer, idx) in floatingEventTooltip.scorers"
          :key="idx"
          class="tooltip-row"
        >
          <span class="tooltip-name">{{ scorer.athlete_name }}</span>
          <span class="tooltip-score">{{ formatNumber(scorer.score) }}</span>
        </div>
      </template>

      <div v-else class="tooltip-empty">No participating athletes</div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, watch } from 'vue'
const isTouchDevice = 'ontouchstart' in window || navigator.maxTouchPoints > 0
const props = defineProps({
  title: String,
  rowData: { type: Array, default: () => [] },
  columnDefs: { type: Array, default: () => [] }
})

const sortField = ref(null)
const sortDirection = ref('desc')
const showHover = ref(true)
const activeHeaderTooltip = ref(null)
const activeEventCell = ref({ rowId: null, field: null })
const floatingEventTooltip = ref({ show: false, top: '0px', left: '0px', scorers: [] })
const tableScrollRef = ref(null)
const headerCells = ref([])
const stickyOffsets = ref({})

const headerTooltip = ref(null)
const headerTooltipStyle = ref({ left: '0px', top: '100%' })

// ----------------------
// Header tooltip
// ----------------------
function showHeaderTooltip(event, col) {
  activeHeaderTooltip.value = col.field
}

function debounce(fn, delay = 1000) {
  let timer
  return (...args) => {
    if (timer) clearTimeout(timer)
    timer = setTimeout(() => fn(...args), delay)
  }
}

const debouncedFlashHeaderTooltip = debounce((col, duration = 1000) => {
  if (!showHover.value) return
  activeHeaderTooltip.value = col.field
  setTimeout(() => {
    if (activeHeaderTooltip.value === col.field) {
      activeHeaderTooltip.value = null
    }
  }, duration)
}, 1000)

function hideHeaderTooltip() {
  activeHeaderTooltip.value = null
}

function toggleHeaderTooltip(col) {
  if (!showHover.value) return
  hideEventTooltip()
  if (activeHeaderTooltip.value === col.field) {
    activeHeaderTooltip.value = null
  } else {
    activeHeaderTooltip.value = col.field
  }
}

// ----------------------
// Sorting
// ----------------------
function onSort(col) {
  // Always hide other tooltips
  hideEventTooltip()
  activeHeaderTooltip.value = col.field

  if (col.sortable === false) return
  const sortKey = col.meta?.isEventColumn ? `${col.field}.event_pts` : col.field
  if (sortField.value === sortKey) {
    if (sortDirection.value === 'desc') sortDirection.value = 'asc'
    else if (sortDirection.value === 'asc') {
      sortField.value = null
      sortDirection.value = null
    }
  } else {
    sortField.value = sortKey
    sortDirection.value = 'desc'
  }
}


// ----------------------
// Event tooltip
// ----------------------
function showEventTooltip(event, row, col) {
  if (!showHover.value) return

  const cellRect = event.currentTarget.getBoundingClientRect()
  const tooltipWidth = 220
  const viewportWidth = window.innerWidth
  const viewportHeight = window.innerHeight

  // Horizontal position
  let left = cellRect.left
  if (left + tooltipWidth > viewportWidth) left = cellRect.right - tooltipWidth
  if (left < 0) left = 0

  // Temporarily render tooltip offscreen to measure height
  floatingEventTooltip.value = {
    show: true,
    top: `0px`,
    left: `0px`,
    scorers: row[col.field].scorers || []
  }

  nextTick(() => {
    const tooltipEl = document.querySelector('.event-tooltip')
    if (!tooltipEl) return

    const tooltipHeight = tooltipEl.offsetHeight
    let top = cellRect.bottom + 4 // default below cell

    // Flip above if it would overflow bottom
    if (cellRect.bottom + tooltipHeight > viewportHeight) {
      top = cellRect.top - tooltipHeight - 4
      if (top < 0) top = 4 // clamp to top of viewport
    }

    floatingEventTooltip.value.top = `${top}px`
    floatingEventTooltip.value.left = `${left}px`
  })
}


function toggleEventTooltip(event, row, col) {
  if (!showHover.value) return

  hideHeaderTooltip()

  const currentCellScorers = row[col.field].scorers || []

  if (floatingEventTooltip.value.show && currentCellScorers) {
    // Hide tooltip if clicking the same cell again
    hideEventTooltip()
    activeEventCell.value = { rowId: null, field: null } // reset highlight
    return
  }

  // Show tooltip
  showEventTooltip(event, row, col)

  // Highlight clicked cell
  activeEventCell.value = { rowId: row._id, field: col.field }
}



function hideEventTooltip() {
  floatingEventTooltip.value.show = false
}

// ----------------------
// Header tooltip helpers
// ----------------------
function getFullHeaderName(col) {
  return col.meta?.fullHeaderName || col.headerName 
}

// ----------------------
// Rows & sorting
// ----------------------
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

function getSortValue(row, key) {
  if (!key.includes('.')) return row[key]
  return key.split('.').reduce((obj, k) => (obj ? obj[k] : undefined), row)
}

// ----------------------
// Logos
// ----------------------
const LOGO_BASE_URL = 'https://storage.googleapis.com/projections-data/logos/NCAA'
function getLogoUrl(row) {
  return row.team_abbr ? `${LOGO_BASE_URL}/${row.team_abbr}.png` : null
}

// ----------------------
// Helpers
// ----------------------
function isSortFieldActive(col) {
  const sortKey = col.meta?.isEventColumn ? `${col.field}.event_pts` : col.field
  return sortField.value === sortKey
}

function isEventCell(row, field) {
  return row[field] && typeof row[field] === 'object' && 'event_pts' in row[field]
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
// Sticky columns
// ----------------------
function stickyClass(col) {
  return col.sticky ? 'sticky' : ''
}

function stickyStyle(col) {
  if (!col.sticky) return {}
  return { position: 'sticky', left: `${stickyOffsets.value[col.field] || 0}px` }
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

watch(showHover, (val) => {
  hideEventTooltip()
  hideHeaderTooltip()
})

function getColStyle(col) {
  if (col.field === 'logo') return { minWidth: '40px' }
  return {}
}
</script>

<style scoped>
/* Table & scroll wrapper */
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
  border: 1px solid #ccc;
  border-radius: 4px;
  position: relative;
}

.results-table {
  border-collapse: collapse;
  table-layout: fixed;
  min-width: 100%;
  font-size: 0.95rem;
}

th, td { position: relative; }

th.sticky, td.sticky { z-index: 3; }
thead th.sticky { z-index: 4; }

.cell-inner {
  padding: 8px 10px;
  white-space: nowrap;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

thead th {
  background: #f8f8f8;
  border-bottom: 2px solid #ccc;
  font-weight: 600;
  text-align: left;
  position: sticky;
  top: 0;
  z-index: 1;
}

th.status-scored, th.status-official { background-color: #63BE7B; color: #1D6F42; }
th.status-projection { background-color: #e5f7ff; color: #007ac6; }

/* Sort triangle */
.sort-triangle { font-size: 0.7rem; color: #999; }
th.active .sort-triangle { color: #333; }

/* Rows */
tbody tr:nth-of-type(odd) { background-color: #fff; }
tbody tr:nth-of-type(even) { background-color: #f2f2f2; }
tr:nth-child(odd) td.sticky { background-color: #fff; }
tr:nth-child(even) td.sticky { background-color: #f2f2f2; }
tbody tr:hover { background-color: #dcdcdc; }

/* Header tooltip (inside table, reverted) */
.floating-header-tooltip {
  position: absolute;
  z-index: 9999;
  background: #fff;
  border: 1px solid #ccc;
  padding: 6px 10px;
  font-size: 0.75rem;
  font-weight: 500;
  white-space: nowrap;
  border-radius: 4px;
  box-shadow: 0 6px 16px rgba(0,0,0,0.2);
}

/* Event tooltip (floating) */
.event-tooltip {
  position: fixed;
  z-index: 9999;
  background-color: #fff;
  border: 1px solid #ccc;
  border-radius: 4px;
  padding: 8px 10px;
  min-width: 200px;
  max-width: 320px;
  box-shadow: 0 8px 20px rgba(0,0,0,0.25);
  pointer-events: none;
  white-space: normal;
}

/* Logos */
.team-logo { width: 18px; height: 18px; object-fit: contain; }

/* Tooltip toggle */
.tooltip-toggle { height: 20px; }

/* Tooltip rows */
.tooltip-header { display: flex; justify-content: space-between; gap: 12px; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; color: #666; border-bottom: 1px solid #ddd; padding-bottom: 4px; margin-bottom: 6px; }
.tooltip-row { display: flex; justify-content: space-between; gap: 12px; font-size: 0.85rem; line-height: 1.4; padding: 2px 0; }
.tooltip-name { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.tooltip-score { font-weight: 600; }
.tooltip-empty { font-size: 0.8rem; color: #777; font-style: italic; padding: 4px 0; }
.header-tooltip {
  position: absolute;
  top: 100%;
  left: 0;
  margin-top: 4px;
  background: #ffffff;
  border: 1px solid #ccc;
  border-radius: 4px;
  padding: 6px 10px;
  font-size: 0.75rem;
  font-weight: 500;
  white-space: nowrap;
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.2);
  z-index: 9999;
  max-width: 300px;
  overflow: hidden;
  text-overflow: ellipsis;
}

@media (max-width: 768px) {
  .results-table-wrapper { width: 100vw; padding: 0; }
  .table-scroll { max-height: calc(100vh - 150px); }
  td.active-event-cell {
    background-color: rgba(0, 123, 255, 0.1); /* subtle blue highlight */
    transition: background-color 0.2s ease;
  }
}
</style>
