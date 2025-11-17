import { defineStore } from 'pinia'
import { auth } from '@/firebase'
import { 
  signInWithEmailAndPassword, 
  signOut, 
  onAuthStateChanged, 
  setPersistence, 
  browserLocalPersistence 
} from 'firebase/auth'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null,
    isInitialized: false,
    ready: false,
  }),

  getters: {
    isLoggedIn: (state) => !!state.user,
    isAdmin: (state) => state.user?.email?.startsWith('admin') ?? false
  },

  actions: {
    async initAuth() {
      await setPersistence(auth, browserLocalPersistence)

      this.user = await new Promise((resolve) => {
        const unsubscribe = onAuthStateChanged(auth, (user) => {
          resolve(user)
          unsubscribe()
        })
      })

      this.isInitialized = true
      this.ready = true
    },

    async login(email, password) {
      await setPersistence(auth, browserLocalPersistence)
      const userCredential = await signInWithEmailAndPassword(auth, email, password)
      this.user = userCredential.user
    },

    async logout() {
      await signOut(auth)
      this.user = null
    },
  },
})
