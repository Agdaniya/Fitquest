import { initializeApp } from "https://www.gstatic.com/firebasejs/9.6.1/firebase-app.js";
import { getAuth, onAuthStateChanged } from "https://www.gstatic.com/firebasejs/9.6.1/firebase-auth.js";
import { getDatabase, ref, get } from "https://www.gstatic.com/firebasejs/9.6.1/firebase-database.js";
import { getFirestore, doc, getDoc } from "https://www.gstatic.com/firebasejs/9.6.1/firebase-firestore.js";

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

// Track progress data
let totalExercises = 0;
let completedExercises = 0;

document.addEventListener("DOMContentLoaded", () => {
    onAuthStateChanged(auth, (user) => {
        if (user) {
            displayExercises(user.uid);
        }
    });
});

const getFitnessLevel = async (userId) => {
    const userRef = ref(dbRealtime, `users/${userId}/fitnessLevel`);
    try {
        const snapshot = await get(userRef);
        return snapshot.exists() ? snapshot.val().toLowerCase() : "beginner";
    } catch (error) {
        console.error("Error fetching fitness level:", error);
        return "beginner";
    }
};

const displayExercises = async (userId) => {
    const container = document.getElementById("exercise-container");
    const fitnessLevel = await getFitnessLevel(userId);
    const exercisesRef = doc(dbFirestore, "exercises", fitnessLevel);

    try {
        const docSnap = await getDoc(exercisesRef);
        if (docSnap.exists()) {
            renderExercises(docSnap.data());
        } else {
            container.innerHTML = `<p>No exercises available.</p>`;
        }
    } catch (error) {
        console.error("Error fetching exercises:", error);
    }
};

const renderExercises = (exercises) => {
    const container = document.getElementById("exercise-container");
    container.innerHTML = "";
    
    // Reset exercise counters
    totalExercises = 0;
    completedExercises = 0;
    
    Object.keys(exercises).forEach(type => {
        const section = document.createElement("div");
        section.classList.add("exercise-section");
        section.innerHTML = `<h3>${type.toUpperCase()}</h3>`;

        exercises[type].forEach(exercise => {
            // Increment total exercises counter
            totalExercises++;
            
            const card = document.createElement("div");
            card.classList.add("exercise-card");

            let details = `<h4>${exercise.exercise}</h4>
                <p><strong>Category:</strong> ${exercise.type}</p>`;

            if (exercise.type === "reps") {
                details += `<p><strong>Reps:</strong> ${exercise.reps}</p>`;
            } else if (exercise.type === "hold") {
                details += `<p><strong>Hold Time:</strong> ${exercise.hold} seconds</p>`;
            } else if (exercise.type === "time") {
                details += `<p><strong>Duration:</strong> ${exercise.time} seconds</p>`;
            }
            details += `<p><strong>Rest Time:</strong> ${exercise.rest} seconds</p>`;
            
            const startButton = document.createElement("button");
            startButton.textContent = "Start";
            startButton.classList.add("start-btn");
            startButton.addEventListener("click", () => startExercise(exercise, card));
            
            card.innerHTML = details;
            card.appendChild(startButton);
            section.appendChild(card);
        });
        container.appendChild(section);
    });
    
    // Initialize progress bar at 0%
    updateProgressBar();
};

const updateProgressBar = () => {
    const progressBar = document.getElementById("progress-bar");
    const progressText = document.getElementById("progress-text");
    
    if (!progressBar || !progressText) return;
    
    const progressPercentage = totalExercises > 0 ? Math.round((completedExercises / totalExercises) * 100) : 0;
    
    progressBar.style.width = `${progressPercentage}%`;
    progressText.textContent = `Progress: ${progressPercentage}%`;
};

const markExerciseCompleted = () => {
    completedExercises++;
    updateProgressBar();
};

const startExercise = (exercise, card) => {
    card.querySelector("button").disabled = true;
    if (exercise.type === "reps") {
        fetch(`http://localhost:5000/track/start-${exercise.exercise.toLowerCase()}`, { method: "POST" })
            .then(() => checkCompletion(exercise, card));
    } else {
        let duration = exercise.type === "hold" ? exercise.hold : exercise.time;
        let countdown = duration;
        const interval = setInterval(() => {
            card.querySelector("button").textContent = `Time left: ${countdown}s`;
            if (--countdown < 0) {
                clearInterval(interval);
                showRestPeriod(exercise, card);
            }
        }, 1000);
    }
};

const showRestPeriod = (exercise, card) => {
    let countdown = exercise.rest;
    const interval = setInterval(() => {
        card.querySelector("button").textContent = `Rest: ${countdown}s`;
        if (--countdown < 0) {
            clearInterval(interval);
            card.querySelector("button").textContent = "Completed";
            card.querySelector("button").disabled = true;
            markExerciseCompleted(); 
        }
    }, 1000);
};

const checkCompletion = (exercise, card) => {
    const checkInterval = setInterval(() => {
        fetch(`http://localhost:5000/track/get-${exercise.exercise.toLowerCase()}-count`)
            .then(res => res.json())
            .then(data => {
                if (data.count >= exercise.reps) {
                    card.querySelector("button").textContent = "Completed";
                    card.querySelector("button").disabled = true;
                    markExerciseCompleted(); 
                    clearInterval(checkInterval); 
                }
            });
    }, 3000);
};