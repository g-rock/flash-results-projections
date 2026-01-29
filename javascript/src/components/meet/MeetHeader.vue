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
          <span>
            {{ meet?.location || '' }} | {{ meet?.date || '' }}

            <template v-if="auth.user && config?.meetDocumentId">
              <span class="meet-db-id">
                | {{ config.meetDocumentId }}
                <button
                  class="copy-btn"
                  title="Copy meet document ID"
                  @click="copyMeetId"
                >
                  📋
                </button>
              </span>
            </template>
          </span>
        </div>
      </div>
    </div>

    <!-- Right side: user controls -->
    <div class="user-controls">
      <!-- Hamburger button (mobile) -->
      <button class="hamburger" @click="menuOpen = !menuOpen">
        ☰
      </button>

      <!-- Links (desktop or expanded mobile) -->
      <div :class="['links', { open: menuOpen }]">
        <router-link
          v-if="auth.user"
          :to="dynamicLink.to"
          class="admin-link"
          @click="menuOpen = false"
        >
          {{ dynamicLink.text }}
        </router-link>

        <router-link to="/admin" class="admin-link" @click="menuOpen = false">
          Admin
        </router-link>

        <!-- Mobile-only UI toggles -->
        <div class="mobile-toggles">
          <button class="menu-toggle" @click="ui.showHover = !ui.showHover">
            <span>Tooltips</span>
            <span v-if="ui.showHover">✔</span>
          </button>

          <button class="menu-toggle" @click="ui.showTeamAbbr = !ui.showTeamAbbr">
            <span>Team abbr</span>
            <span v-if="ui.showTeamAbbr">✔</span>
          </button>

          <button
            class="menu-toggle"
            @click="ui.showFullColumnName = !ui.showFullColumnName"
          >
            <span>Full column name</span>
            <span v-if="ui.showFullColumnName">✔</span>
          </button>
        </div>


        <a
          v-if="auth.user"
          @click="handleLogout"
          class="logout-link"
          @click.prevent="menuOpen = false"
        >
          Logout
        </a>
      </div>
    </div>
  </header>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRoute } from 'vue-router'
import { useConfigStore } from '@/stores/config.store'
import { useAuthStore } from '@/stores/auth.store'
import { useUIStore } from '@/stores/ui.store'


const props = defineProps({
  meetId: { type: String, required: true }
})

const config = useConfigStore()
const auth = useAuthStore()
const ui = useUIStore()
const route = useRoute()

const menuOpen = ref(false)

// Dynamic link logic for Meet Settings / Meet Results
const dynamicLink = computed(() => {
  if (route.name === 'MeetSettings') {
    return {
      text: '📓 Meet Results',
      to: {
        name: 'MeetTableHolder',
        params: {
          meetYear: route.params.meetYear,
          meetSeason: route.params.meetSeason,
          meetId: route.params.meetId
        }
      }
    }
  } else {
    return {
      text: '⚙️ Meet Settings',
      to: {
        name: 'MeetSettings',
        params: {
          meetYear: route.params.meetYear,
          meetSeason: route.params.meetSeason,
          meetId: route.params.meetId
        }
      }
    }
  }
})

const meet = computed(() => {
  if (!props.meetId || !config.meets.length) return null
  return config.meets.find(m => m.id === props.meetId) || null
})

function copyMeetId() {
  if (!config?.meetDocumentId) return
  navigator.clipboard.writeText(config.meetDocumentId)
}

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
  padding: 0 16px;
  color: white;
  height: 90px;
}

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

/* Right side */
.user-controls {
  display: flex;
  align-items: center;
  gap: 10px;
  position: relative;
}

/* Hamburger button (mobile) */
.hamburger {
  display: none;
  background: none;
  border: none;
  font-size: 1.5rem;
  color: white;
  cursor: pointer;
}

/* Links row (desktop) */
.links {
  display: flex;
  gap: 15px;
  align-items: center;
}

/* Mobile collapsed menu */
.links.open {
  display: flex;
  flex-direction: column;
  position: absolute;
  top: 100%;
  right: 0;
  background-color: #062134;
  padding: 10px;
  border-radius: 4px;
  z-index: 10;
}

/* Links styling */
.admin-link {
  text-decoration: none;
  color: white;
  display: inline-flex;
  align-items: center;
  gap: 4px;
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
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.copy-btn {
  background: none;
  border: none;
  color: #ccc;
  cursor: pointer;
  padding: 0;
  font-size: 0.85rem;
}

.copy-btn:hover {
  color: #fff;
}

.mobile-toggles {
  display: none;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 6px;
}

.menu-toggle {
  background: none;
  border: none;
  color: white;
  font-size: 0.9rem;
  padding: 4px 0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
  text-align: left;
}

.menu-toggle:hover {
  opacity: 0.85;
}

@media (max-width: 768px) {
  .links {
    display: none;
  }
  .links.open {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    position: absolute;
    right: 0;
    top: 100%;
    background-color: #062134;
    padding: 10px 14px;
    gap: 10px;
    border-radius: 4px;
    z-index: 10;
    min-width: 150px;
  }
  .hamburger {
    display: block;
  }
  .meet-name {
    font-size: 1rem;
    line-height: 1.2;
  }
  .meet-details {
    font-size: 0.75rem;
  }
  .meet-info {
    gap: 2px;
  }
  .header-text {
    height: 70px;
  }
  .meet-db-id {
    display: none;
  }
  .mobile-toggles {
    display: flex;
  }
}
</style>
