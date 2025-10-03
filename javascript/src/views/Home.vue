<template>
  <div>
    <h2>Available Meets</h2>
    <div v-if="loadingMeets">Loading...</div>
    <div v-if="meetsError" style="color: red;">Error loading meets: {{ meetsError.message }}</div>

    <ul v-if="meets.length > 0">
      <li v-for="meet in meets" :key="meet">
        <!-- Clickable meet to navigate to dashboard -->
        <router-link :to="{ name: 'Dashboard', params: { meetName: meet } }">
          {{ meet }}
        </router-link>
      </li>
    </ul>
    <div v-else-if="!loadingMeets && !meetsError">No meets available</div>
  </div>
</template>

<script setup>
import { onMounted } from 'vue';
import { storeToRefs } from 'pinia';
import { useConfigStore } from '@/stores/config.store';

const store = useConfigStore();
const { meets, loadingMeets, meetsError } = storeToRefs(store);

const fetchMeets = () => store.fetchMeets();

onMounted(() => {
  fetchMeets();
});
</script>
