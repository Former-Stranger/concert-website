// Firebase configuration and initialization

// Import Firebase modules (using the CDN version)
import { initializeApp } from 'https://www.gstatic.com/firebasejs/10.8.0/firebase-app.js';
import { getAuth, GoogleAuthProvider, FacebookAuthProvider, signInWithPopup, signOut, onAuthStateChanged } from 'https://www.gstatic.com/firebasejs/10.8.0/firebase-auth.js';
import { getFirestore, collection, addDoc, getDocs, query, where, orderBy, serverTimestamp, doc, setDoc, getDoc, deleteDoc } from 'https://www.gstatic.com/firebasejs/10.8.0/firebase-firestore.js';
import { getStorage, ref, uploadBytesResumable, getDownloadURL, deleteObject } from 'https://www.gstatic.com/firebasejs/10.8.0/firebase-storage.js';

// Your Firebase configuration
const firebaseConfig = {
  apiKey: "AIzaSyBfRFD6UUO36Qc1dmzTbEu78rbJeuiqdkY",
  authDomain: "earplugs-and-memories.firebaseapp.com",
  projectId: "earplugs-and-memories",
  storageBucket: "earplugs-and-memories.firebasestorage.app",
  messagingSenderId: "251013809771",
  appId: "1:251013809771:web:3295c7c7b9274d94ee132e",
  measurementId: "G-5LCQZ03QVH"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const db = getFirestore(app);
const storage = getStorage(app);

// Auth Providers
const googleProvider = new GoogleAuthProvider();
const facebookProvider = new FacebookAuthProvider();

// Export for use in other files
export {
  auth,
  db,
  storage,
  googleProvider,
  facebookProvider,
  signInWithPopup,
  signOut,
  onAuthStateChanged,
  collection,
  addDoc,
  getDocs,
  query,
  where,
  orderBy,
  serverTimestamp,
  doc,
  setDoc,
  getDoc,
  deleteDoc,
  ref,
  uploadBytesResumable,
  getDownloadURL,
  deleteObject
};
