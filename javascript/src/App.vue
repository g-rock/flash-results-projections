<template>
  <div>
    <header>
      <!-- Logo stays linking to home -->
      <router-link to="/">
        <img src="/logo.png" alt="FR Logo" class="fr-logo" />
      </router-link>
      <router-link to="/admin" class="admin-link">
        Admin
      </router-link>
      <button v-if="auth.user" @click="handleLogout" class="logout">
				Logout
			</button>
    </header>

    <router-view v-if="config.meets.length" :key="$route.params.meetId" />
    <div v-else>Loading meets...</div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useConfigStore } from '@/stores/config.store';
import { useAuthStore } from '@/stores/auth.store';
import router from './router';

const config = useConfigStore();
const auth = useAuthStore();

const handleLogout = async () => {
  await auth.logout();
  router.push('/');
};

onMounted(async () => {
  config.fetchMeets();
  console.log('Fetching all meets')
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
    }
  }
  eventSource.onerror = (error) => {
    console.error("SSE error:", error)
  }
})
</script>

<style scoped>
header {
  display: flex;
  align-items: center;
}

.admin-link {
  margin-left: auto; /* pushes this link to the right */
  font-weight: bold;
  color: #007bff;
  text-decoration: none;
}

.admin-link:hover {
  text-decoration: underline;
}

.router-link-active.admin-link {
  text-decoration: underline;
}

.fr-logo {
  width: 50px;
  height: 50px;
}
</style>
