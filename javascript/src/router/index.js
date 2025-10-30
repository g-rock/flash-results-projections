import { createRouter, createWebHistory } from 'vue-router'
import Login from '@/views/Login.vue'
import Home from '@/views/Home.vue'
import Dashboard from '@/views/Dashboard.vue'

const routes = [
  { path: '/', component: Home },
  { path: '/login', component: Login },
  {
    path: '/dashboard/:meetId',
    name: 'Dashboard',
    component: Dashboard,
    // meta: { requiresAuth: true },
  },
]


const router = createRouter({
  history: createWebHistory(),
  routes,
})
export default router
