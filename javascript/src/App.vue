<template>
  <div>
    <!-- Header -->
    <MeetHeader
      v-if="isMeetRoute"
      :meetId="currentMeetId"
    />
    <GenericHeader v-else />

    <!-- Main content -->
    <router-view v-if="!isMeetRoute || config.meets.length" :key="$route.params.meetId" />
    <div v-else>Loading meets...</div>
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useConfigStore } from '@/stores/config.store'
import MeetHeader from '@/components/meet/MeetHeader.vue'
import GenericHeader from '@/components/GenericHeader.vue'

const config = useConfigStore()
const route = useRoute()

// Determine if current route is a meet route
const isMeetRoute = computed(() => route.name === 'MeetTableHolder' || route.name === 'MeetSettings')

// Current meet ID from route
const currentMeetId = computed(() => route.params.meetId)

// Fetch all meets once
onMounted(async () => {
  if (!config.meets.length) {
    await config.fetchMeets()
  }
})
</script>
<style scoped>
</style>
