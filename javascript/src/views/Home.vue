<template>
  <div>
    <h2>Available Meets</h2>
    
    <div v-if="loadingMeets">Loading...</div>
    <div v-if="meetsError" style="color: red;">
      Error loading meets: {{ meetsError.message }}
    </div>

    <div v-else-if="meets.length > 0">
      <div v-for="(seasonMeets, year) in meetsByYearAndSeason" :key="year">
        <h3>{{ year }}</h3>

        <div v-for="(meetsList, season) in seasonMeets" :key="season" style="margin-left: 20px;">
          <h4>{{ season.charAt(0).toUpperCase() + season.slice(1) }}</h4>
          <ul>
            <li v-for="meet in meetsList" :key="meet.id">
              <router-link :to="{ name: 'MeetTableHolder', params: { meetYear: year, meetSeason: season, meetId: meet.id } }">
                {{ meet.name }}
              </router-link>
            </li>
          </ul>
        </div>
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

const meetsByYearAndSeason = computed(() => {
  const groups = {};

  meets.value.forEach(meet => {
    const year = meet.year || 'Unknown';
    const season = meet.season || 'Unknown';

    if (!groups[year]) groups[year] = {};
    if (!groups[year][season]) groups[year][season] = [];

    groups[year][season].push(meet);
  });

  // Optional: sort years descending and seasons
  const sortedYears = Object.keys(groups).sort((a, b) => b - a);
  const result = {};
  sortedYears.forEach(year => {
    result[year] = {};
    Object.keys(groups[year]).forEach(season => {
      result[year][season] = groups[year][season];
    });
  });

  return result;
});

</script>

