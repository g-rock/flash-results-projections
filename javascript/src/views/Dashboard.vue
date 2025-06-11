<template>
  <div class="dashboard">
    <header class="acc-header">
      <div class="header-left">
        <img src="@/assets/ncaa.svg" alt="ACC Logo" class="acc-logo" />
        <div class="header-text">
          <h1>NCAA Championship. Hayward Field Eugene Oregon</h1>
        </div>
      </div>
      <!-- <button @click="logout" class="logout-button">Logout</button> -->
    </header>

    <div class="tabs">
      <button
        :class="{ active: selectedTab === 'Women' }"
        @click="selectedTab = 'Women'"
      >
        Women
      </button>
      <button
        :class="{ active: selectedTab === 'Men' }"
        @click="selectedTab = 'Men'"
      >
        Men
      </button>
    </div>

    <ProjectionsTable
      v-if="selectedTab === 'Women'"
      title="Women"
      :rowData="womenData"
      :columnDefs="columnDefsWomen"
      :defaultColDef="defaultColDef"
    />

    <ProjectionsTable
      v-if="selectedTab === 'Men'"
      title="Men"
      :rowData="menData"
      :columnDefs="columnDefsMen"
      :defaultColDef="defaultColDef"
    />


  </div>
</template>

<script setup>
import ProjectionsTable from '@/components/ProjectionsTable.vue'
import { useRouter } from 'vue-router'
import { signOut } from 'firebase/auth'
import { auth } from '@/firebase'
import { ref } from 'vue'

// 📥 Load JSON data
import columnDefsWomen from '@/data/columnDefs.women.json'
import columnDefsMen from '@/data/columnDefs.men.json'
import womenData from '@/data/womenData.json'
import menData from '@/data/menData.json'

const selectedTab = ref('Women')

const router = useRouter()

const logout = async () => {
  try {
    await signOut(auth)
    router.push('/login')
  } catch (err) {
    console.error('Logout failed:', err)
  }
}

const defaultColDef = {
  resizable: false,
  sortable: true,
  filter: false,
}
</script>


<style scoped>
.dashboard {
  padding: 20px;
  font-family: Arial, sans-serif;
}

.acc-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background-color: #0f2c52;
  color: white;
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 20px;
}

.header-left {
  display: flex;
  align-items: center;
}

.acc-logo {
  width: 80px;
  height: auto;
  margin-right: 20px;
}

.header-text h1 {
  margin: 0;
  font-size: 24px;
}

.header-text p {
  margin: 5px 0 0;
  font-size: 16px;
}

.logout-button {
  background-color: #e74c3c;
  color: white;
  border: none;
  padding: 8px 14px;
  font-size: 14px;
  border-radius: 4px;
  cursor: pointer;
}

.logout-button:hover {
  background-color: #c0392b;
}

.tabs {
  margin-bottom: 20px;
}

.tabs button {
  background: #ddd;
  border: none;
  padding: 10px 20px;
  margin-right: 10px;
  font-size: 16px;
  border-radius: 6px;
  cursor: pointer;
}

.tabs button.active {
  background: #0f2c52;
  color: white;
}

</style>
