<template>
  <header class="header-text">
    <!-- Left: logo + title -->
    <div class="header-left">
      <router-link to="/">
        <img src="/logo.png" alt="FR Logo" class="fr-logo" />
      </router-link>
      <h1 class="header-title">Welcome to the FR Projections</h1>
    </div>

    <!-- Right: user controls -->
    <div class="user-controls">
      <!-- Hamburger (mobile) -->
      <button class="hamburger" @click="menuOpen = !menuOpen">
        ☰
      </button>

      <!-- Links -->
      <div class="links" :class="{ open: menuOpen }">
        <router-link to="/admin" class="admin-link" @click="menuOpen = false">
          Admin
        </router-link>

        <a
          v-if="auth.user"
          @click.prevent="handleLogout"
          class="logout-link"
        >
          Logout
        </a>
      </div>
    </div>
  </header>
</template>

<script setup>
import { ref } from 'vue'
import { useAuthStore } from '@/stores/auth.store'

const auth = useAuthStore()
const menuOpen = ref(false)

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
  padding: 0 16px;
  height: 90px;
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

/* ===== User controls ===== */
.user-controls {
  display: flex;
  align-items: center;
  position: relative;
}

/* Desktop links */
.links {
  display: flex;
  gap: 15px;
  align-items: center;
}

.admin-link,
.logout-link {
  color: white;
  text-decoration: none;
  font-weight: 500;
  cursor: pointer;
}

.logout-link {
  font-size: 0.95rem;
}

.admin-link:hover,
.logout-link:hover {
  text-decoration: underline;
}

/* ===== Hamburger ===== */
.hamburger {
  display: none;
  background: none;
  border: none;
  font-size: 1.5rem;
  color: white;
  cursor: pointer;
}

/* ===== Mobile ===== */
@media (max-width: 768px) {
  .header-title {
    font-size: 1rem;
    line-height: 1.2;
  }

  .hamburger {
    display: block;
  }

  .links {
    display: none;
  }

  .links.open {
    display: flex;
    flex-direction: column;
    position: absolute;
    right: 0;
    top: 100%;
    background-color: #062134;
    padding: 10px 14px;
    gap: 10px;
    border-radius: 4px;
    z-index: 10;
    min-width: 120px;
  }

  .header-text {
    height: 70px;
  }
}
</style>
