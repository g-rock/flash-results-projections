// Import the functions you need from the SDKs you need
import { initializeApp } from "firebase/app";
import { getAuth } from 'firebase/auth'
import { getAnalytics } from "firebase/analytics";
// TODO: Add SDKs for Firebase products that you want to use
// https://firebase.google.com/docs/web/setup#available-libraries

// Your web app's Firebase configuration
// For Firebase JS SDK v7.20.0 and later, measurementId is optional
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
const auth = getAuth(app)
const analytics = getAnalytics(app);

export { auth }