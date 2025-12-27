<template>
  <div class="dashboard">
    <router-view />
  </div>
</template>

<script setup>
import { computed, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useConfigStore } from '@/stores/config.store'

const config = useConfigStore()
const route = useRoute()

const meetDocumentId = computed(() => {
  const { meetYear, meetSeason, meetId } = route.params
  return `${meetYear}/${meetSeason}/${meetId}`
})

watch(
  () => meetDocumentId.value,
  (newVal) => {
    config.setMeetDocumentId(newVal)
    config.fetchEvents(newVal)
  },
  { immediate: true }
)
</script>