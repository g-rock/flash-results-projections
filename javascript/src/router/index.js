import { createRouter, createWebHistory } from 'vue-router'
import Login from '@/views/Login.vue'
import Dashboard from '@/views/Dashboard.vue'
import { auth } from '@/firebase'
import { waitForAuthReady } from '@/auth'

const routes = [
  { path: '/login', component: Login },
  {
    path: '/dashboard',
    component: Dashboard,
    meta: { requiresAuth: true },
  },
  { path: '/', redirect: '/dashboard' },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(async (to, from, next) => {
  await waitForAuthReady()
  const currentUser = auth.currentUser

  if (to.meta.requiresAuth && !currentUser) {
    next('/login')
  } else if (to.path === '/login' && currentUser) {
    next('/dashboard')
  } else {
    next()
  }
})

export default router
