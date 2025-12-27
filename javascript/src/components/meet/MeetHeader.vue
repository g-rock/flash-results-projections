<template>
  <header class="header-text">
    <!-- Left side: logo + meet info -->
    <div class="header-left">
      <router-link to="/">
        <img src="/logo.png" alt="FR Logo" class="fr-logo" />
      </router-link>

      <div class="meet-info">
        <h1 class="meet-name">{{ meet?.name || 'Loading meet...' }}</h1>
        <div class="meet-details">
          <span>{{ meet?.location || '' }} | {{ meet?.date || '' }}</span>
        </div>
      </div>
    </div>

    <!-- Right side: user controls -->
    <div class="user-controls">
      <router-link to="/admin" class="admin-link">
        <span class="icon">⚙️</span> Admin
      </router-link>
      <a v-if="auth.user" @click="handleLogout" class="logout-link">Logout</a>
      <div v-if="auth.user" class="meet-db-id">
        Meet Database ID: {{ config?.meetDocumentId || '' }}
      </div>
    </div>
  </header>
</template>

<script setup>
import { computed } from 'vue'
import { useConfigStore } from '@/stores/config.store'
import { useAuthStore } from '@/stores/auth.store'

const props = defineProps({
  meetId: { type: String, required: true }
})

const config = useConfigStore()
const auth = useAuthStore()

const meet = computed(() => {
  if (!props.meetId || !config.meets.length) return null
  return config.meets.find(m => m.id === props.meetId) || null
})

function handleLogout() {
  auth.logout?.()
}
</script>

<style scoped>
.header-text {
  display: flex;
  align-items: center;
  justify-content: space-between; /* left group + right group */
  gap: 15px;
  margin-bottom: 20px;
  background-color: #062134;
  padding: 1em;
  color: white;
}

/* left group: logo + meet info */
.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.fr-logo {
  height: 40px;
}

.meet-info {
  display: flex;
  flex-direction: column;
  justify-content: center;
  text-align: left;
}

.meet-name {
  margin: 0;
}

.meet-details {
  font-size: 0.9rem;
}

.user-controls {
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 5px;
  align-items: flex-end;
}

.admin-link {
  text-decoration: none;
  color: white;
  display: flex;
  align-items: center;
  gap: 4px;
}

.icon {
  font-size: 0.9rem;
}

.logout-link {
  cursor: pointer;
  text-decoration: none;
  color: white;
  font-size: 0.95rem;
}

.logout-link:hover,
.admin-link:hover {
  text-decoration: underline;
}

.meet-db-id {
  font-size: 0.85rem;
  color: #ccc;
  text-align: right;
}
</style>
