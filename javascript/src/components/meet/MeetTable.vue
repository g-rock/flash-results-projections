<template>
  <div class="projections-table">
    <div class="results-table-wrapper">
      <h3>{{ title }}</h3>

      <div class="table-scroll">
        <table class="results-table">
          <!-- COLGROUP DEFINES WIDTHS -->
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
                  stickyClass(col.field)
                ]"
              >
                <div class="cell-inner">
                  {{ col.headerName || col.field }}
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
                :class="stickyClass(col.field)"
              >
                <div class="cell-inner">
                  {{ formatNumber(row[col.field]) }}
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
// Sticky helpers
// ----------------------
function stickyClass(field) {
  if (field === 'rank') return 'sticky sticky-rank'
  if (field === 'team') return 'sticky sticky-team'
  if (field === 'points') return 'sticky sticky-points'
  return ''
}

// Column widths driven by header intent
function getColStyle(col) {
  if (col.field === 'rank') return { width: '60px' }
  if (col.field === 'team') return { width: '220px' }
  if (col.field === 'points') return { width: '100px' }
  return { width: '120px' } // default for events
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
  table-layout: fixed; /* REQUIRED for colgroup */
  min-width: max-content;
  font-size: 0.95rem;
}

/* Remove padding from sticky container */
th, td {
  padding: 0;
  background: white;
}

.cell-inner {
  padding: 8px 10px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* Headers */
thead th {
  background: #f8f8f8;
  border-bottom: 2px solid #ccc;
  font-weight: 600;
}

/* Sticky columns */
.sticky {
  position: sticky;
  z-index: 3;
  background: white;
}

.sticky-rank {
  left: 0;
  z-index: 6;
}

.sticky-team {
  left: 60px;
  z-index: 5;
}

.sticky-points {
  left: 280px;
  z-index: 4;
}

thead .sticky {
  z-index: 10;
}

/* Rows */
tbody tr:nth-child(even) {
  background: #fafafa;
}

tbody tr:hover {
  background: #eef6fc;
}
</style>
