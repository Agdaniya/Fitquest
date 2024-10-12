
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
  const app = firebase.initializeApp(firebaseConfig);
  const auth = firebase.auth();

  function reauthenticateUser(currentPassword) {
    const user = firebase.auth().currentUser;
    const cred = firebase.auth.EmailAuthProvider.credential(
      user.email, currentPassword);
    
    return user.reauthenticateWithCredential(cred);
  }

  function changePassword(newPassword) {
    const user = firebase.auth().currentUser;
    user.updatePassword(newPassword).then(() => {
      console.log("Password updated successfully.");
    }).catch((error) => {
      console.error("Error updating password:", error);
    });
  }

  async function handleChangePassword(currentPassword, newPassword) {
    try {
      await reauthenticateUser(currentPassword);
      await changePassword(newPassword);
      alert("Password changed successfully");
    } catch (error) {
      alert("Error: " + error.message);
    }
  }

