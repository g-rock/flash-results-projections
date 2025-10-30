<template>
  <div class="projections-table">
    <ag-grid-vue
      style="width: 100%"
      :columnDefs="columnDefs"
      :rowData="rowData"
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
</script>

<style scoped>
.projections-table {
  margin-bottom: 40px;
}
</style>
