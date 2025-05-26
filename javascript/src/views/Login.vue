<template>
  <div class="login">
    <h2>Login</h2>
    <input v-model="email" type="email" placeholder="Email" />
    <input v-model="password" type="password" placeholder="Password" />
    <button @click="login">Login</button>
    <p v-if="error">{{ error }}</p>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { signInWithEmailAndPassword } from 'firebase/auth'
import { auth } from '@/firebase'
import { useRouter } from 'vue-router'

const router = useRouter()
const email = ref('')
const password = ref('')
const error = ref('')

const errorMessages = {
  'auth/user-not-found': 'No user found with this email.',
  'auth/wrong-password': 'Incorrect password. Please try again.',
  'auth/invalid-email': 'Invalid email address.',
  'auth/invalid-credential': 'Invalid login credentials.',
  'auth/too-many-requests': 'Too many login attempts. Please try again later.',
}

const login = async () => {
  error.value = ''
  try {
    await signInWithEmailAndPassword(auth, email.value, password.value)
    router.push('/dashboard')
  } catch (err) {
    const code = err.code
    error.value = errorMessages[code] || 'Login failed. Please try again.'
  }
}

</script>
