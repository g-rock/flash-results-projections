import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth.store';
import Login from '@/views/Login.vue'
import Home from '@/views/Home.vue'
import MeetLayout from '@/views/MeetLayout.vue'
import MeetTableHolder from '@/components/meet/MeetTableHolder.vue'
import MeetSettings from '@/components/meet/MeetSettings.vue'
import Admin from '@/views/Admin.vue'

const routes = [
  { path: '/', name: 'Home', component: Home },
  { path: '/login', name: 'Login', component: Login },
  { path: '/admin', name: 'Admin', component: Admin, meta: { requiresAuth: true } },
  {
    path: '/meet/:meetYear/:meetSeason/:meetId',
    name: 'MeetLayout',
    component: MeetLayout,
    props: true,
    children: [
      {
        path: '',
        name: 'MeetTableHolder',
        component: MeetTableHolder,
      },
      {
        path: 'settings',
        name: 'MeetSettings',
        component: MeetSettings,
        meta: { requiresAuth: true, requiresAdmin: true },
        props: true
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()
  if (!authStore.ready) {
    await authStore.initAuth()
  }
  if (to.meta.requiresAuth && !authStore.user) {
    next('/login')
  } else {
    next()
  }
})
export default router
