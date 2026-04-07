import { initializeApp } from "https://www.gstatic.com/firebasejs/10.12.2/firebase-app.js";
import { getAuth } from "https://www.gstatic.com/firebasejs/10.12.2/firebase-auth.js";
import { getFirestore } from "https://www.gstatic.com/firebasejs/10.12.2/firebase-firestore.js";

const firebaseConfig = {
  apiKey: "AIzaSyAs-Xl_59cRc79Das-ZEgElYtaF41PsnC8",
  authDomain: "biasfree-642026.firebaseapp.com",
  projectId: "biasfree-642026",
  storageBucket: "biasfree-642026.firebasestorage.app",
  messagingSenderId: "237763382673",
  appId: "1:237763382673:web:ace9f0ee1f2ef330801e30",
  measurementId: "G-T8EFZQNQ18"
};

const app = initializeApp(firebaseConfig);

export const auth = getAuth(app);
export const db = getFirestore(app);