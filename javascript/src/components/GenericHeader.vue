<template>
  <header class="header-text">
    <div class="header-left">
      <router-link to="/">
        <img src="/logo.png" alt="FR Logo" class="fr-logo" />
      </router-link>
      <h1 class="header-title">Welcome to the FR Projections</h1>
    </div>

    <div class="user-controls">
      <router-link to="/admin" class="admin-link">
        <span class="icon">⚙️</span> Admin
      </router-link>
      <a v-if="auth.user" @click="handleLogout" class="logout-link">Logout</a>
    </div>
  </header>
</template>

<script setup>
import { useAuthStore } from '@/stores/auth.store'

const auth = useAuthStore()

function handleLogout() {
  auth.logout?.()
}
</script>

<style scoped>
.header-text {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 15px;
  background-color: #062134;
  color: white;
  padding: 1em;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 15px;
}

.fr-logo {
  height: 40px;
}

.header-title {
  margin: 0;
}

.user-controls {
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 5px;
  align-items: flex-end;
}

.admin-link {
  color: white;
  text-decoration: none;
  font-weight: 500;
}

.logout-link:hover,
.admin-link:hover {
  text-decoration: underline;
}

.logout-link {
  cursor: pointer;
  text-decoration: none;
  color: white;
  font-size: 0.95rem;
}
</style>
