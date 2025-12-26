<template>
  <div class="projections-table">
    <div class="results-table-wrapper">
      <h3>{{ title }}</h3>

      <div class="table-scroll">
        <table class="results-table">
          <thead>
            <tr>
              <th v-for="col in columnDefs" :key="col.field"
                  @click="onSort(col)"
                  :class="{ sortable: col.sortable !== false, active: sortField === col.field, 'team-column': col.field === 'team' }">
                {{ col.headerName || col.field }}
                <span v-if="sortField === col.field">{{ sortDirection === 'asc' ? '▲' : '▼' }}</span>
              </th>
            </tr>
          </thead>

          <tbody>
            <tr v-for="row in sortedRows" :key="row._id">
              <td v-for="col in columnDefs" :key="col.field" :class="{ 'team-column': col.field === 'team' }">
                {{ formatNumber(row[col.field]) }}
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
  title: { type: String, default: '' },
  rowData: { type: Array, default: () => [] },
  columnDefs: { type: Array, default: () => [] }
})

// --- Sorting state ---
const sortField = ref(null)
const sortDirection = ref('desc')

// --- Sort handler ---
function onSort(col) {
  if (col.sortable === false) return

  if (sortField.value === col.field) {
    // cycle: desc -> asc -> original
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

// --- Sorted rows ---
const sortedRows = computed(() => {
  if (!props.rowData.length) return []

  if (!sortField.value || !sortDirection.value) {
    return [...props.rowData].sort((a, b) => (a.rank || 0) - (b.rank || 0))
  }

  const rows = [...props.rowData]

  return rows.sort((a, b) => {
    let aVal = a[sortField.value]
    let bVal = b[sortField.value]

    if (aVal == null) return 1
    if (bVal == null) return -1

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

// --- Number formatting ---
function formatNumber(value) {
  const num = parseFloat(value)
  if (isNaN(num)) return value
  return Number.isInteger(num) ? num : num.toFixed(2)
}
</script>

<style scoped>
.results-table-wrapper {
  width: 100vw; /* full width of viewport */
}

.table-scroll {
  width: 100%;
  overflow-x: auto; /* allow horizontal scroll */
}

.results-table {
  width: 100%; /* table takes full width inside scroll */
  min-width: 800px; /* optional: force min width for readability */
  border-collapse: collapse;
  font-size: 0.95rem;
}

.results-table thead th {
  background: #f8f8f8;
  color: #222;
  text-align: left;
  padding: 8px 10px;
  border-bottom: 2px solid #ccc;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.results-table thead th.sortable {
  cursor: pointer;
  user-select: none;
}

.results-table thead th.sortable:hover {
  background: #eee;
}

.results-table thead th.active {
  background: #e6f2ff;
}

/* Make team column never wrap */
.results-table td.team-column,
.results-table th.team-column {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.results-table tbody tr {
  border-bottom: 1px solid #e0e0e0;
}

.results-table tbody tr:nth-child(even) {
  background: #fafafa;
}

.results-table tbody tr:hover {
  background: #eef6fc;
}

.results-table td {
  padding: 8px 10px;
  color: #333;
}
</style>
