<template>
  <div>
    <header>
      <!-- Logo stays linking to home -->
      <router-link to="/">
        <img src="/logo.png" alt="FR Logo" class="fr-logo" />
      </router-link>

      <!-- Separate link to docs, right-aligned -->
      <a 
        href="https://flash-results-projections-224895366733.us-central1.run.app/docs" 
        target="_blank" 
        rel="noopener"
        class="docs-link"
      >
        API
      </a>
    </header>

    <router-view :key="$route.params.meetId" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useConfigStore } from '@/stores/config.store';

const store = useConfigStore();

onMounted(async () => {
  store.fetchMeets();
  const eventSource = new EventSource(`${import.meta.env.VITE_API_HOST}/stream`)

  eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data)
    console.log("SSE message:", data)
    if (data.type === "event_uploaded") {
      store.fetchEvents(data.meet_id)
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

.docs-link {
  margin-left: auto; /* pushes this link to the right */
  font-weight: bold;
  color: #007bff;
  text-decoration: none;
}

.docs-link:hover {
  text-decoration: underline;
}

.fr-logo {
  width: 50px;
  height: 50px;
}
</style>
