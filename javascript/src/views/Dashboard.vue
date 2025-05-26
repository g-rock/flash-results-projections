<template>
  <div class="dashboard">
    <header class="acc-header">
      <div class="header-left">
        <img src="@/assets/acc-logo.png" alt="ACC Logo" class="acc-logo" />
        <div class="header-text">
          <h1>2025 ACC Outdoor Track & Field Championships Projections</h1>
          <p>Winston-Salem, NC | May 15–17, 2025</p>
        </div>
      </div>
      <button @click="logout" class="logout-button">Logout</button>
    </header>

    <ProjectionsTable title="Women" :rowData="womenData" :columnDefs="columnDefs" :defaultColDef="defaultColDef" />
    <ProjectionsTable title="Men" :rowData="menData" :columnDefs="columnDefs" :defaultColDef="defaultColDef" />
  </div>
</template>



<script setup>
import ProjectionsTable from '@/components/ProjectionsTable.vue'
import { useRouter } from 'vue-router'
import { signOut } from 'firebase/auth'
import { auth } from '@/firebase' // adjust path if needed

const router = useRouter()

const logout = async () => {
  try {
    await signOut(auth)
    router.push('/login')
  } catch (err) {
    console.error('Logout failed:', err)
  }
}

const columnDefs = [
  { headerName: 'School', field: 'school', pinned: 'left', width: 160 },
  { field: '60' }, { field: '200' }, { field: '400' }, { field: '800' },
  { field: 'Mile' }, { field: '3000' }, { field: '5000' }, { field: '60HH' },
  { field: '4x400' }, { field: 'DMR' }, { field: 'HJ' }, { field: 'PV' },
  { field: 'LJ' }, { field: 'TJ' }, { field: 'SP' }, { field: 'WT' },
  { field: 'PENT' }, { field: 'HEP' },
  { field: 'TOTAL', cellStyle: { fontWeight: 'bold' } },
  { field: 'Place' },
]

const defaultColDef = {
  resizable: false,
  sortable: true,
  filter: false,
  width: 90,
}

const womenData = [
  { school: 'Boston College', '3000': 8, '5000': 3, 'DMR': 6, 'TOTAL': 17, 'Place': 11 },
  { school: 'Clemson', '60': 22, '200': 25, '400': 11, '800': 6, 'Mile': 10, '3000': 5, '5000': 3, '60HH': 31, '4x400': 10, 'DMR': 2, 'HJ': 9, 'PV': 4, 'LJ': 8, 'TJ': 11, 'SP': 10, 'WT': 3, 'PENT': 3, 'TOTAL': 156, 'Place': 1 },
  { school: 'Duke', '400': 5, '5000': 10, '4x400': 5, 'HJ': 1, 'PV': 7, 'PENT': 15, 'TOTAL': 54, 'Place': 6 },
  { school: 'Florida State', '60': 2, '800': 10, 'Mile': 16, '3000': 12, '4x400': 1, 'DMR': 10, 'TJ': 10, 'SP': 6, 'WT': 3, 'TOTAL': 81, 'Place': 3 },
  { school: 'Georgia Tech', '60': 1, '60HH': 5, 'LJ': 9, 'TJ': 9, 'SP': 2, 'TOTAL': 26, 'Place': 10 },
  { school: 'Maryland', 'DMR': 2, 'HJ': 18, 'SP': 2, 'WT': 2, 'PENT': 8, 'TOTAL': 32, 'Place': 9 },
  { school: 'Miami', '60': 6, '200': 5, '400': 1, '4x400': 4, 'PV': 5, 'LJ': 3, 'TJ': 7, 'PENT': 11, 'TOTAL': 42, 'Place': 8 },
  { school: 'North Carolina', '60': 3, '200': 17, '400': 13, '800': 12, 'Mile': 8, 'DMR': 8, 'HJ': 4, 'PV': 9, 'PENT': 8, 'TOTAL': 88, 'Place': 2 },
  { school: 'North Carolina St.', '800': 11, 'Mile': 1, '5000': 3, 'DMR': 3, 'LJ': 6, 'TJ': 12, 'SP': 6, 'WT': 6, 'TOTAL': 43, 'Place': 7 },
  { school: 'Virginia', 'Mile': 4, '3000': 10, '5000': 4, 'DMR': 6, 'HJ': 3, 'PV': 4, 'SP': 10, 'WT': 5, 'PENT': 5, 'TOTAL': 56, 'Place': 5 },
  { school: 'Virginia Tech', '60': 8, '200': 6, '400': 6, '800': 8, '60HH': 3, 'HJ': 6, 'PV': 20, 'TOTAL': 62, 'Place': 4 },
  { school: 'Wake Forest', 'Mile': 2, 'TJ': 4, 'PENT': 6, 'TOTAL': 12, 'Place': 12 },
]

const menData = [
  { school: 'Boston College', 'PV': 1, 'TOTAL': 1, 'Place': 12 },
  { school: 'Clemson', '60': 9, '200': 4, '400': 3, '800': 5, 'Mile': 2, '5000': 3, '60HH': 18, '4x400': 6, 'DMR': 4, 'HJ': 2, 'PV': 9, 'TJ': 1, 'SP': 5, 'TOTAL': 71, 'Place': 5 },
  { school: 'Duke', 'Mile': 5, '3000': 6, 'DMR': 3, 'HJ': 6, 'WT': 13, 'TOTAL': 42, 'Place': 7 },
  { school: 'Florida State', '60': 15, '200': 20, '400': 10, '800': 13, 'Mile': 6, '60HH': 1, '4x400': 10, 'DMR': 6, 'PV': 2, 'LJ': 10, 'TJ': 6, 'SP': 8, 'WT': 3, 'TOTAL': 110, 'Place': 2 },
  { school: 'Georgia Tech', '60': 2, '200': 4, '400': 1, '4x400': 1, 'HJ': 2, 'PV': 6.5, 'TJ': 3, 'TOTAL': 19.5, 'Place': 8 },
  { school: 'Maryland', 'Mile': 1, '60HH': 4, '4x400': 3, 'SP': 2, 'WT': 1, 'TOTAL': 11, 'Place': 10 },
  { school: 'Miami', '60HH': 8, '4x400': 2, 'PV': 4, 'WT': 1, 'TOTAL': 15, 'Place': 9 },
  { school: 'North Carolina', '200': 17, '400': 6, '800': 8, '4x400': 2, 'DMR': 2, 'PV': 15.5, 'TJ': 7, 'HEP': 13, 'TOTAL': 83.5, 'Place': 4 },
  { school: 'North Carolina St.', '200': 2, '800': 5, '3000': 18, '60HH': 6, 'DMR': 10, 'HJ': 8, 'LJ': 3, 'SP': 7, 'TOTAL': 64, 'Place': 6 },
  { school: 'Virginia', '60': 6, '200': 10, '400': 15, '800': 8, '3000': 18, '4x400': 4, 'DMR': 8, 'PV': 2, 'LJ': 10, 'TJ': 10, 'WT': 9, 'TOTAL': 100, 'Place': 3 },
  { school: 'Virginia Tech', '60': 13, '200': 11, '400': 4, '800': 6, '60HH': 2, '4x400': 6, 'DMR': 5, 'HJ': 5, 'PV': 10, 'LJ': 12, 'TJ': 14, 'SP': 12, 'WT': 3, 'HEP': 24, 'TOTAL': 137, 'Place': 1 },
  { school: 'Wake Forest', 'PV': 6, 'TOTAL': 6, 'Place': 11 },
]

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
  background-color: #013ca6;
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
</style>
