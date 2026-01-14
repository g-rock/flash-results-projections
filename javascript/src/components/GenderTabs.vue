<template>
  <div class="tabs">
    <button
      :class="{ active: config.selectedGender === 'women' }"
      @click="config.setSelectedGender('women')"
    >
      Women
    </button>
    <button
      :class="{ active: config.selectedGender === 'men' }"
      @click="config.setSelectedGender('men')"
    >
      Men
    </button>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useConfigStore } from '@/stores/config.store'

const config = useConfigStore()
</script>

<style scoped>
.tabs {
  height: 40px;
  display: flex;
  justify-content: center;
  gap: 10px;
}

.tabs button {
  background: none;
  border: none;
  font-size: 1rem;
  padding: 10px 20px;
  cursor: pointer;
  color: #666;
  position: relative;
  transition: color 0.2s;
}

.tabs button:hover {
  color: #000;
}

.tabs button.active {
  color: #000;
  font-weight: 600;
}

.tabs button.active::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  height: 3px;
  width: 60%;
  background-color: #007bff;
  border-radius: 2px;
}
</style>
