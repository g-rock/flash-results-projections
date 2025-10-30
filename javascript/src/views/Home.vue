<template>
  <div>
    <h2>Available Meets</h2>
    
    <div v-if="loadingMeets">Loading...</div>
    <div v-if="meetsError" style="color: red;">
      Error loading meets: {{ meetsError.message }}
    </div>

    <div v-else-if="meets.length > 0">
      <!-- Group meets by year -->
      <div v-for="(yearMeets, year) in meetsByYear" :key="year">
        <h3>{{ year }}</h3>
        <ul>
          <li v-for="meet in yearMeets" :key="meet.id">
            <router-link :to="{ name: 'Dashboard', params: { meetId: meet.id } }">
              {{ meet.name }}
            </router-link>
          </li>
        </ul>
      </div>
    </div>

    <div v-else>No meets available</div>
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue';
import { storeToRefs } from 'pinia';
import { useConfigStore } from '@/stores/config.store';

const store = useConfigStore();
const { meets, loadingMeets, meetsError } = storeToRefs(store);

// Compute meets grouped by year
const meetsByYear = computed(() => {
  const groups = {};
  meets.value.forEach(meet => {
    const year = meet.year || 'Unknown';
    if (!groups[year]) groups[year] = [];
    groups[year].push(meet);
  });

  // Optional: sort years descending
  return Object.fromEntries(
    Object.entries(groups).sort((a, b) => b[0] - a[0])
  );
});
</script>

