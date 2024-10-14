import { initializeApp } from "https://www.gstatic.com/firebasejs/10.13.2/firebase-app.js";
import { getAuth, signInWithEmailAndPassword } from "https://www.gstatic.com/firebasejs/10.13.2/firebase-auth.js";
import { getFirestore, doc, getDoc } from 'https://www.gstatic.com/firebasejs/10.13.2/firebase-firestore.js';

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
const db = getFirestore(app);

function displayWorkout(workout) {
  const workoutContent = document.getElementById('workoutContent');
  let html = `<h3>${workout.title}</h3>`;
  workout.exercises.forEach(exercise => {
    html += `<div class="exercise-card">
              <h3>${exercise.name}</h3>
              <p>${exercise.reps} ${exercise.unit}</p>
            </div>`;
  });
  workoutContent.innerHTML = html;
}

document.addEventListener('DOMContentLoaded', async () => {
  const executePlanBtn = document.getElementById('executePlanBtn');

  try {
    // Fetch workout data from Firestore
    const docRef = doc(db, 'workouts', 'abs');
    const docSnap = await getDoc(docRef);

    if (docSnap.exists()) {
      const workout = docSnap.data();
      displayWorkout(workout);

      // Set up button click event
      executePlanBtn.addEventListener('click', () => {
        localStorage.setItem('currentWorkout', JSON.stringify(workout));
        window.location.href = 'workout.html';
      });
    } else {
      console.log("No such document!");
    }
  } catch (error) {
    console.log("Error getting document:", error);
  }
});