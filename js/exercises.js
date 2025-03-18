import { initializeApp } from "https://www.gstatic.com/firebasejs/9.6.1/firebase-app.js";
import { getAuth, onAuthStateChanged } from "https://www.gstatic.com/firebasejs/9.6.1/firebase-auth.js";
import { getDatabase, ref, get } from "https://www.gstatic.com/firebasejs/9.6.1/firebase-database.js";
import { getFirestore, doc, getDoc } from "https://www.gstatic.com/firebasejs/9.6.1/firebase-firestore.js";
import { update } from "https://www.gstatic.com/firebasejs/9.6.1/firebase-database.js";

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
let userId = null;
document.addEventListener("DOMContentLoaded", () => {
    onAuthStateChanged(auth, (user) => {
        if (user) {
            userId = user.uid; // Store the user ID
            displayExercises(userId);
        } else {
            // Handle not logged in state
            console.log("User not logged in");
            document.getElementById("exercise-container").innerHTML = 
                `<p>Please log in to view exercises.</p>`;
        }
    });
});

const loadCompletedExercises = async (userId) => {
    const completedRef = ref(dbRealtime, `users/${userId}/completedExercises`);
    try {
        const snapshot = await get(completedRef);
        if (snapshot.exists()) {
            return snapshot.val(); // Returns an object of completed exercises
        }
    } catch (error) {
        console.error("Error fetching completed exercises:", error);
    }
    return {};
};

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

const renderExercises = async (exercises) => {
    const container = document.getElementById("exercise-container");
    container.innerHTML = "";
    const completedExercisesData = await loadCompletedExercises(userId);
    
    // Initialize progress counters
    totalExercises = 0;
    completedExercises = 0;
    
    Object.keys(exercises).forEach(type => {
        exercises[type].forEach(exercise => {
            totalExercises++; // Count total exercises
            
            const card = document.createElement("div");
            card.classList.add("exercise-card");

            let isCompleted = completedExercisesData[exercise.exercise];
            
            // Count completed exercises
            if (isCompleted) {
                completedExercises++;
                card.classList.add("completed"); // Add visual class
            }

            card.innerHTML = `
                <h4>${exercise.exercise}</h4>
                <p>Type: ${exercise.type}</p>
                <p>Sets: ${exercise.sets || 1}</p>
                <p>Rest: ${exercise.rest || 30}s</p>
                <button class="start-btn" ${isCompleted ? 'disabled' : ''}>
                    ${isCompleted ? '✔ Completed' : 'Start'}
                </button>
            `;

            const startButton = card.querySelector(".start-btn");
            if (!isCompleted) {
                startButton.addEventListener("click", () => startExercise(exercise, card));
            }

            container.appendChild(card);
        });
    });

    updateProgressBar();
    addProgressSummary(); 
};


const updateProgressBar = () => {
    const progressBar = document.getElementById("progress-bar");
    const progressText = document.getElementById("progress-text");
    
    if (!progressBar || !progressText) return;
    
    const progressPercentage = totalExercises > 0 ? Math.round((completedExercises / totalExercises) * 100) : 0;
    
    // Animate the progress bar
    progressBar.style.width = `${progressPercentage}%`;
    progressText.textContent = `Progress: ${completedExercises} of ${totalExercises} (${progressPercentage}%)`;
    
    // Add visual feedback based on progress
    if (progressPercentage === 100) {
        progressBar.style.backgroundColor = "#4CAF50"; // Green for complete
        progressText.textContent = `Completed! All ${totalExercises} exercises done.`;
    } else if (progressPercentage >= 75) {
        progressBar.style.backgroundColor = "#8BC34A"; // Light green for almost complete
    } else if (progressPercentage >= 50) {
        progressBar.style.backgroundColor = "#FFC107"; // Amber for halfway
    } else if (progressPercentage >= 25) {
        progressBar.style.backgroundColor = "#FF9800"; // Orange for started
    } else {
        progressBar.style.backgroundColor = "#F44336"; // Red for just beginning
    }
};
// Fix the markExerciseCompleted function to accept exercise name parameter
const markExerciseCompleted = async (exerciseName) => {
    completedExercises++;
    updateProgressBar();

    if (userId) {
        await update(ref(dbRealtime, `users/${userId}/completedExercises/${exerciseName}`), {
            completed: true,
            timestamp: Date.now()
        });
    }

    // Hide completed exercises dynamically
    document.querySelectorAll('.exercise-card').forEach(card => {
        if (card.querySelector('h4').textContent === exerciseName) {
            card.classList.add('completed');
            card.querySelector('button').textContent = "Completed";
            card.querySelector('button').disabled = true;
        }
    });
};

// Fix port number in the fetch calls
// In exercises.js, modify the startExercise function:
const startExercise = (exercise, card) => {
    card.querySelector("button").disabled = true;
    card.querySelector("button").textContent = "Starting...";
    
    // First start the camera
    fetch(`http://localhost:5001/start-camera`, { 
        method: "POST",
        headers: { "Content-Type": "application/json" }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        console.log("Camera started:", data);
        
        // Now start the specific exercise
        return fetch(`http://localhost:5001/start-exercise`, { 
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ 
                name: exercise.exercise, 
                type: exercise.type, 
                details: exercise 
            })
        });
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return response.json();
    })
    .then(() => {
        if (exercise.type === "reps") {
            // For rep-based exercises, check completion status
            checkCompletion(exercise, card);
        } else {
            // For time-based exercises, start the timer
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
    })
    .catch(error => {
        console.error("Error in exercise start sequence:", error);
        card.querySelector("button").textContent = "Error - Try again";
        card.querySelector("button").disabled = false;
    });
};

const showRestPeriod = (exercise, card) => {
    let countdown = exercise.rest;
    const interval = setInterval(() => {
        card.querySelector("button").textContent = `Rest: ${countdown}s`;
        if (--countdown < 0) {
            clearInterval(interval);
            card.querySelector("button").textContent = "Completed";
            card.querySelector("button").disabled = true;
            markExerciseCompleted(exercise.exercise);
            
            // Stop tracking/camera when exercise is complete
            fetch(`http://localhost:5001/stop-tracking`, {
                method: "POST",
                headers: { "Content-Type": "application/json" }
            }).catch(err => {
                console.error("Error stopping tracking:", err);
            });
        }
    }, 1000);
};

const checkCompletion = (exercise, card) => {
    const checkInterval = setInterval(() => {
        fetch(`http://localhost:5001/complete-exercise`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ exercise: exercise.exercise })
        })
        .then(res => res.json())
        .then(data => {
            if (data.status === "success") {
                clearInterval(checkInterval);
                card.querySelector("button").textContent = "Completed";
                card.querySelector("button").disabled = true;
                markExerciseCompleted(exercise.exercise);
                
                // Stop tracking/camera when exercise is complete
                fetch(`http://localhost:5001/stop-tracking`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" }
                }).catch(err => {
                    console.error("Error stopping tracking:", err);
                });
            }
        })
        .catch(err => {
            console.error("Error checking completion:", err);
        });
    }, 3000);
};

const addProgressSummary = () => {
    let summaryElement = document.getElementById("exercise-summary");
    
    if (!summaryElement) {
        summaryElement = document.createElement("div");
        summaryElement.id = "exercise-summary";
        summaryElement.className = "exercise-summary";
        
        const container = document.getElementById("exercise-container");
        container.parentNode.insertBefore(summaryElement, container);
    }
    
    const progressPercentage = totalExercises > 0 ? Math.round((completedExercises / totalExercises) * 100) : 0;
    
    summaryElement.innerHTML = `
        <h3>Your Progress</h3>
        <div class="progress-bar-container">
            <div id="progress-bar" class="progress-bar" style="width: ${progressPercentage}%"></div>
        </div>
        <p id="progress-text">Progress: ${completedExercises} of ${totalExercises} (${progressPercentage}%)</p>
        <p>${progressPercentage === 100 ? 
            'Great job! You completed all exercises.' : 
            `You have ${totalExercises - completedExercises} exercises remaining.`}
        </p>
    `;
};