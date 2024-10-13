import { initializeApp } from "https://www.gstatic.com/firebasejs/10.13.2/firebase-app.js";
import { getAuth, createUserWithEmailAndPassword, updatePassword, reauthenticateWithCredential, EmailAuthProvider } from "https://www.gstatic.com/firebasejs/10.13.2/firebase-auth.js";
import { getDatabase, ref, set } from "https://www.gstatic.com/firebasejs/10.13.2/firebase-database.js";
  // Initialize Firebase
  const firebaseConfig = {
    apiKey: "AIzaSyAOgdbddMw93MExNBz3tceZ8_NrNAl5q40",
    authDomain: "fitquest-9b891.firebaseapp.com",
    projectId: "fitquest-9b891",
    storageBucket: "fitquest-9b891.appspot.com",
    messagingSenderId: "275044631678",
    appId: "1:275044631678:web:7fa9586ba031270baa042f",
    measurementId: "G-6W3V2DH02K"
};
  const app = initializeApp(firebaseConfig);
  const auth = getAuth(app);
  const database = getDatabase(app);
  //const auth = firebase.auth();

  document.getElementById('change-password-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const currentPassword = document.getElementById('current-password').value;
    const newPassword = document.getElementById('new-password').value;
    const user = auth.currentUser;
    console.log("Current User:", user);

    if (!user) {
      alert("No user is currently logged in.");
      return;
    }

    const credential = EmailAuthProvider.credential(user.email, currentPassword);

    try {
      // Re-authenticate user with their current password
      await reauthenticateWithCredential(user, credential);
      // Update password after successful re-authentication
      await updatePassword(user, newPassword);
      displayMessage("Password changed successfully", "success");
    } catch (error) {
      if (error.code === 'auth/wrong-password') {
        displayMessage("Incorrect current password. Please try again.", "error");
      } else if (error.code === 'auth/weak-password') {
        displayMessage("New password is too weak. Please use a stronger password.", "error");
      } else {
        displayMessage("Error changing password: " + error.message, "error");
      }
    }
  });

  // Display message function
  function displayMessage(message, type) {
    const messageDiv = document.getElementById("message");
    messageDiv.innerText = message;
    messageDiv.style.color = type === "success" ? "green" : "red";
  }
