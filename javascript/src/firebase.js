import { initializeApp } from "firebase/app";
import { getAuth } from 'firebase/auth'
import { getFirestore } from "firebase/firestore";

// Your web app's Firebase configuration
const firebaseConfig = {
  apiKey: "AIzaSyAPsjkWj_zXerOZt0Z-1YnefSXepmWAdYw",
  authDomain: "flash-results-projections.firebaseapp.com",
  projectId: "flash-results-projections",
  storageBucket: "flash-results-projections.firebasestorage.app",
  messagingSenderId: "224895366733",
  appId: "1:224895366733:web:54d6a17a58b188fc4f8e04",
  measurementId: "G-82Z01Y60NV"
};
const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);
export const db = getFirestore(app);