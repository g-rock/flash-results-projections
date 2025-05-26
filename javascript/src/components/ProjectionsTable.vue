<template>
  <div class="projections-table">
    <h2>{{ title }}</h2>
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
import { AgGridVue } from 'ag-grid-vue3'
import { themeQuartz } from 'ag-grid-community';

// Props
defineProps({
  title: String,
  rowData: Array,
  columnDefs: Array,
  defaultColDef: Object,
})

const theme = themeQuartz
</script>

<style scoped>
.projections-table {
  margin-bottom: 40px;
}
</style>
