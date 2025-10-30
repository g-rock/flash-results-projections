import { initializeApp } from "firebase/app";
import { getAuth } from "firebase/auth";
import { getAnalytics } from "firebase/analytics";
import { getFirestore } from "firebase/firestore";

const firebaseConfig = {
  apiKey: "AIzaSyAPsjkWj_zXerOZt0Z-1YnefSXepmWAdYw",
  authDomain: "flash-results-projections.firebaseapp.com",
  projectId: "flash-results-projections",
  storageBucket: "flash-results-projections.firebasestorage.app",
  messagingSenderId: "224895366733",
  appId: "1:224895366733:web:54d6a17a58b188fc4f8e04",
  measurementId: "G-82Z01Y60NV"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const analytics = getAnalytics(app);
const db = getFirestore(app);

export { auth, analytics, db };
