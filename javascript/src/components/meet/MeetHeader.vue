<template>
  <div class="header-text">
    <h1>{{ currentMeet?.name || 'Loading...' }}</h1>
    <span>Meet Database ID: {{ config.meetDocumentId }}</span><br>
    <span>Meet Location: {{ currentMeet?.location }}</span><br>
    <span>Meet Date: {{ currentMeet?.date }}</span><br>

    <!-- Admin link: conditionally show -->
    <div v-if="auth.isAdmin" class="admin-link">
      <router-link
        v-if="isOnTable"
        :to="settingsLink"
      >
        ⚙️ Meet Settings
      </router-link>

      <router-link
        v-else
        :to="tableLink"
      >
        📊 Back to Table
      </router-link>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useConfigStore } from '@/stores/config.store'
import { useAuthStore } from '@/stores/auth.store'

const route = useRoute()
const config = useConfigStore()
const auth = useAuthStore()

const { meetYear, meetSeason, meetId } = route.params

const currentMeet = computed(() =>
  config.meets.find(meet => meet.id === meetId)
)

// Links
const settingsLink = computed(() => ({
  name: 'MeetSettings',
  params: { meetYear, meetSeason, meetId }
}))

const tableLink = computed(() => ({
  name: 'MeetTableHolder',
  params: { meetYear, meetSeason, meetId }
}))

// Detect current view
const isOnTable = computed(() => route.name === 'MeetTableHolder')
</script>

<style scoped>
.header-text {
  margin-bottom: 20px;
}

.admin-link {
  margin-top: 10px;
}
</style>
