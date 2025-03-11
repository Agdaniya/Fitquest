import { initializeApp } from "https://www.gstatic.com/firebasejs/9.6.1/firebase-app.js";
import { getAuth, onAuthStateChanged } from "https://www.gstatic.com/firebasejs/9.6.1/firebase-auth.js";
import { getDatabase, ref, get } from "https://www.gstatic.com/firebasejs/9.6.1/firebase-database.js";
import { getFirestore, doc, getDoc } from "https://www.gstatic.com/firebasejs/9.6.1/firebase-firestore.js";

// 🔥 Firebase Configuration
const firebaseConfig = {
    apiKey: "AIzaSyAOgdbddMw93MExNBz3tceZ8_NrNAl5q40",
    authDomain: "fitquest-9b891.firebaseapp.com",
    databaseURL: "https://fitquest-9b891-default-rtdb.firebaseio.com/",
    projectId: "fitquest-9b891",
    storageBucket: "fitquest-9b891.appspot.com",
    messagingSenderId: "275044631678",
    appId: "1:275044631678:web:7fa9586ba031270baa042f",
    measurementId: "G-6W3V2DH02K"
};

const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const dbRealtime = getDatabase(app);
const dbFirestore = getFirestore(app);

// ✅ Wait for DOM to load
document.addEventListener("DOMContentLoaded", () => {
    console.log("DOM fully loaded and ready for exercises.js");
    
    // Give a small delay to ensure other scripts have run
    setTimeout(() => {
        console.log("Checking for exercise-container:", document.getElementById("exercise-container"));
        
        onAuthStateChanged(auth, (user) => {
            if (user) {
                console.log("Logged-in user:", user.uid);
                displayExercises(user.uid);
            } else {
                console.log("No user is logged in.");
            }
        });
    }, 200); // Small delay to ensure DOM is fully processed
});

// 🔥 Function to Fetch Fitness Level from Realtime Database
const getFitnessLevel = async (userId) => {
    if (!userId) {
        console.error("No authenticated user found.");
        return "beginner"; // Default if no user
    }

    const userRef = ref(dbRealtime, `users/${userId}/fitnessLevel`);
    try {
        const snapshot = await get(userRef);
        if (snapshot.exists()) {
            return snapshot.val().toLowerCase(); // Ensure lowercase match
        } else {
            console.log("No fitness level found, defaulting to beginner.");
            return "beginner";
        }
    } catch (error) {
        console.error("Error fetching fitness level:", error);
        return "beginner";
    }
};

// 🔥 Function to Fetch and Display Exercises
const displayExercises = async (userId) => {
    console.log("displayExercises called for user:", userId);
    const container = document.getElementById("exercise-container");

    if (!container) {
        console.error("Error: #exercise-container not found in the DOM.");
        console.log("Available IDs:", Array.from(document.querySelectorAll('[id]')).map(el => el.id));
        return;
    }

    const fitnessLevel = await getFitnessLevel(userId);
    console.log("User fitness level:", fitnessLevel);
    console.log("Fetching document from path:", `exercises/${fitnessLevel}`);

    const exercisesRef = doc(dbFirestore, "exercises", fitnessLevel);

    try {
        const docSnap = await getDoc(exercisesRef);
        if (docSnap.exists()) {
            const exercises = docSnap.data();
            console.log("Fetched Firestore Data:", exercises);

            renderExercises(exercises);
        } else {
            console.log("No exercises found for this fitness level:", fitnessLevel);
            container.innerHTML = `<p>No exercises available for fitness level: ${fitnessLevel}</p>`;
        }
    } catch (error) {
        console.error("Error fetching exercises:", error);
        container.innerHTML = `<p>Error loading exercises: ${error.message}</p>`;
    }
};

// 🔥 Function to Render Exercises in HTML
const renderExercises = (exercises) => {
    console.log("Rendering exercises:", exercises);
    const container = document.getElementById("exercise-container");
    container.innerHTML = "";

    // Add title
    const title = document.createElement("h2");
    title.textContent = "Recommended Exercises";
    title.classList.add("section-title");
    container.appendChild(title);

    Object.keys(exercises).forEach(type => {
        const section = document.createElement("div");
        section.classList.add("exercise-section");
        section.innerHTML = `<h3>${type.toUpperCase()}</h3>`;

        exercises[type].forEach(exercise => {
            console.log("Rendering exercise:", exercise);

            const card = document.createElement("div");
            card.classList.add("exercise-card");
            card.innerHTML = `
                <h4>${exercise.exercise}</h4>
                <p><strong>Category:</strong> ${exercise.type}</p>
                <p><strong>Reps:</strong> ${exercise.count}</p>
                <p><strong>Rest Time:</strong> ${exercise.rest}</p>
            `;
            section.appendChild(card);
        });

        container.appendChild(section);
    });
};