// Import the functions you need from the SDKs you need
import { initializeApp } from "https://www.gstatic.com/firebasejs/10.13.2/firebase-app.js";
import { getAnalytics } from "https://www.gstatic.com/firebasejs/10.13.2/firebase-analytics.js";
import { getDatabase } from "https://www.gstatic.com/firebasejs/10.13.2/firebase-database.js";
import { getAuth, createUserWithEmailAndPassword } from "https://www.gstatic.com/firebasejs/10.13.2/firebase-auth.js";
// TODO: Add SDKs for Firebase products that you want to use
// https://firebase.google.com/docs/web/setup#available-libraries

// Your web app's Firebase configuration
// For Firebase JS SDK v7.20.0 and later, measurementId is optional
const firebaseConfig = {
  apiKey: "AIzaSyAOgdbddMw93MExNBz3tceZ8_NrNAl5q40",
  authDomain: "fitquest-9b891.firebaseapp.com",
  projectId: "fitquest-9b891",
  storageBucket: "fitquest-9b891.appspot.com",
  messagingSenderId: "275044631678",
  appId: "1:275044631678:web:7fa9586ba031270baa042f",
  measurementId: "G-6W3V2DH02K"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const database= getDatabase(app);
const auth = getAuth();

const analytics = getAnalytics(app);

submit.addEventListener("click",(e)=>{
    const email= document.getElementById('email').value;
    const password= document.getElementById('password').value;
   // const submit= document.getElementById('submit');
    createUserWithEmailAndPassword(auth, email, password)
  .then((userCredential) => {
    // Signed up 
    const user = userCredential.user;
    // ...
    alert('user created')
  })
  .catch((error) => {
    const errorCode = error.code;
    const errorMessage = error.message;
    // ..
    alert(errorMessage);
  });

})