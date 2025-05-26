<template>
  <router-view v-if="ready" />
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { waitForAuthReady } from './auth'

const ready = ref(false)

onMounted(async () => {
  await waitForAuthReady()
  ready.value = true
})
</script>

<style>
/* Optional global styles */
body {
  font-family: sans-serif;
  margin: 0;
  padding: 0;
  background: #f4f4f4;
}
</style>
