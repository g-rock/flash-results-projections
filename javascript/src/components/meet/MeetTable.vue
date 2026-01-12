<template>
  <div class="projections-table">
    <div class="results-table-wrapper">
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
                v-for="col in columnDefs"
                :key="col.field"
                @click="onSort(col)"
                :class="[
                  { sortable: col.sortable !== false, active: sortField === col.field },
                  stickyClass(col)
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
                <div class="cell-inner">
                  <template v-if="col.field === 'logo'">
                    <img
                      v-if="row.team_abbr"
                      :src="getLogoUrl(row)"
                      :alt="row.team + ' logo'"
                      class="team-logo"
                      loading="lazy"
                      @error="e => e.target.style.display = 'none'"
                    />
                  </template>

                  <template v-else>
                    {{ formatNumber(row[col.field]) }}
                  </template>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const LOGO_BASE_URL = 'https://storage.googleapis.com/projections-data/logos/NCAA'

function getLogoUrl(row) {
  if (!row.team_abbr) return null
  return `${LOGO_BASE_URL}/${row.team_abbr}.png`
}

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

function onSort(col) {
  if (col.sortable === false) return

  if (sortField.value === col.field) {
    if (sortDirection.value === 'desc') sortDirection.value = 'asc'
    else if (sortDirection.value === 'asc') {
      sortDirection.value = null
      sortField.value = null
    }
  } else {
    sortField.value = col.field
    sortDirection.value = 'desc'
  }
}

const sortedRows = computed(() => {
  if (!props.rowData.length) return []

  if (!sortField.value || !sortDirection.value) {
    return [...props.rowData].sort((a, b) => (a.rank || 0) - (b.rank || 0))
  }

  return [...props.rowData].sort((a, b) => {
    const aVal = a[sortField.value]
    const bVal = b[sortField.value]

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

// ----------------------
// Column sizing
// ----------------------
function getColStyle(col) {
  if (col.field === 'rank') return { width: '24px'}
  if (col.field === 'logo') return { width: '24px' }
  if (col.field === 'team') return { width: '170px'}
  if (col.field === 'points') return { width: '40px' }
  return { width: '120px' }
}

// ----------------------
// Sticky helpers
// ----------------------
function stickyClass(col) {
  return col.sticky ? 'sticky' : ''
}

const CELL_PADDING_LEFT = 8
const CELL_PADDING_RIGHT = 8

// Dynamically calculate left offset of sticky column
function stickyStyle(col) {
  if (!col.sticky) return {}

  let left = 0

  for (const c of props.columnDefs) {
    if (c === col) break

    if (c.sticky) {
      const colWidth = getColStyle(c).width
        ? parseInt(getColStyle(c).width)
        : 120

      // width + left padding of that column
      left += colWidth + CELL_PADDING_LEFT + CELL_PADDING_RIGHT
    }
  }

  return {
    position: 'sticky',
    left: `${left}px`,
    background: '#f8f8f8',
  }
}

// ----------------------
// Formatting
// ----------------------
function formatNumber(value) {
  const num = parseFloat(value)
  if (isNaN(num)) return value
  return Number.isInteger(num) ? num : num.toFixed(2)
}
</script>

<style scoped>
.results-table-wrapper {
  width: 100vw;
}

.table-scroll {
  width: 100%;
  overflow-x: auto;
}

.results-table {
  border-collapse: collapse;
  table-layout: fixed;
  min-width: max-content;
  font-size: 0.95rem;
}

/* Base cell stacking */
th,
td {
  position: relative;
  z-index: 1;
}

/* Sticky columns */
th.sticky,
td.sticky {
  position: sticky;
  left: 0;
  z-index: 3;
  background: #f8f8f8;
}

/* Header sticky cells above body sticky cells */
thead th.sticky {
  z-index: 4;
}

.cell-inner {
  padding: 8px 10px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

thead th {
  background: #f8f8f8;
  border-bottom: 2px solid #ccc;
  font-weight: 600;
  text-align: left;
}

/* Rows - alternating background */
tbody tr:nth-of-type(odd) {
  background-color: #ffffff;
}

tbody tr:nth-of-type(even) {
  background-color: rgba(0, 0, 0, 0.05);
}

/* Hover and active row */
tbody tr:hover,
tbody tr.active {
  background-color: rgba(0, 0, 0, 0.05) !important;
}

@media (max-width: 768px) {
  .cell-inner {
    padding: 6px 8px;
    font-size: 0.9rem;
  }
}

.team-logo {
  width: 18px;
  height: 18px;
  object-fit: contain;
}
</style>
