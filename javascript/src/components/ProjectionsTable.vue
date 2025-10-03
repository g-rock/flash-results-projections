<template>
  <div class="projections-table">
    <h2>{{ title }}</h2>
    <ag-grid-vue
      style="width: 100%"
      :columnDefs="columnDefs"
      :rowData="filteredRowData"
      :defaultColDef="defaultColDef"
      :theme="theme"
      domLayout="autoHeight"
    />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { AgGridVue } from 'ag-grid-vue3'
import { themeQuartz } from 'ag-grid-community';
import { useConfigStore } from '../stores/config.store'

// Props
const props = defineProps({
  title: String,
  rowData: Array,
  columnDefs: Array,
  defaultColDef: Object,
})

const theme = themeQuartz
const configStore = useConfigStore()
const isProjected = computed(() => configStore.isProjected)
const filteredRowData = computed(() => {
  return props.rowData.map(r => {
    const newRow = {}
    Object.keys(r).forEach(key => {
      console.log();
      if (key === 'school') {
        newRow[key] = r[key]
      } else {
        newRow[key] = isProjected.value ? r[key].projected : r[key].actual
      }
    })
    return newRow
  })
})

</script>

<style scoped>
.projections-table {
  margin-bottom: 40px;
}
</style>
