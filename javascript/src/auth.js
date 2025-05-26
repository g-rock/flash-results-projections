// src/auth.js
import { auth } from './firebase'
import { onAuthStateChanged } from 'firebase/auth'

export function waitForAuthReady() {
  return new Promise((resolve) => {
    const unsubscribe = onAuthStateChanged(auth, () => {
      unsubscribe()
      resolve()
    })
  })
}
