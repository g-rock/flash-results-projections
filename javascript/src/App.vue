<template>
  <div>
    <RestrictOrientation />
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
import RestrictOrientation from '@/components/RestrictOrientation.vue'

const config = useConfigStore()
const route = useRoute()

// Determine if current route is a meet route
const isMeetRoute = computed(() => route.name === 'MeetTableHolder' || route.name === 'MeetSettings')

// Current meet ID from route
const currentMeetId = computed(() => route.params.meetId)

onMounted(async () => {
  if (!config.meets.length) {
    await config.fetchMeets()
  }

  const eventSource = new EventSource(`${import.meta.env.VITE_API_HOST}/stream`)

  eventSource.onopen = () => {
    console.log("✅ Connected to SSE stream");
  };

  eventSource.onclose = () => {
    console.warn("⚠️ SSE connection closed, attempting to reconnect...");
  };

  eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data)
    console.log("💬 SSE message:", data)
    if (data.type === "event_uploaded") {
      config.fetchEvents(data.meet_document_id)
    } else if (data.type === "event_updated") {
      console.log("event updated", event)
      config.fetchEvents(data.meet_document_id)
    }
  }
  eventSource.onerror = (error) => {
    console.error("SSE error:", error)
  }
})

</script>
<style scoped>
</style>
