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
let userId = null;
// Store workout state
let currentWorkout = {
    exercises: [],
    currentExerciseIndex: -1,
    inProgress: false,
    flattenedExercises: []
};

// Progress tracking
let totalExercises = 0;
let completedExercises = 0;

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

const getExercises = async (userId) => {
    const fitnessLevel = await getFitnessLevel(userId);
    const exercisesRef = doc(dbFirestore, "exercises", fitnessLevel);

    try {
        const docSnap = await getDoc(exercisesRef);
        if (docSnap.exists()) {
            const exercises = docSnap.data();
            console.log("Retrieved exercises for fitness level:", fitnessLevel, exercises);
            return exercises;
        } else {
            console.log("No exercises found for fitness level:", fitnessLevel);
            return {};
        }
    } catch (error) {
        console.error("Error fetching exercises:", error);
        return {};
    }
};

// Create a flattened list of exercises from the categorized format
const flattenExercises = (exercisesData) => {
    const flatList = [];
    
    Object.keys(exercisesData).forEach(category => {
        exercisesData[category].forEach(exercise => {
            flatList.push({
                ...exercise,
                category: category
            });
        });
    });
    
    totalExercises = flatList.length;
    completedExercises = 0;
    
    return flatList;
};

// Initialize progress display
const createProgressDisplay = () => {
    let progressContainer = document.getElementById("workout-progress-container");
    
    if (!progressContainer) {
        progressContainer = document.createElement("div");
        progressContainer.id = "workout-progress-container";
        progressContainer.className = "progress-container";
        
        progressContainer.innerHTML = `
            <h3>Workout Progress</h3>
            <div class="progress-bar-container">
                <div id="workout-progress-bar" class="progress-bar"></div>
            </div>
            <p id="workout-progress-text">Progress: 0%</p>
            <p id="current-exercise-name">Starting workout...</p>
        `;
        
        document.body.appendChild(progressContainer);
    }
    
    return progressContainer;
};

// Update progress display
const updateProgressDisplay = () => {
    const progressBar = document.getElementById("workout-progress-bar");
    const progressText = document.getElementById("workout-progress-text");
    
    if (!progressBar || !progressText) return;
    
    const progressPercentage = totalExercises > 0 ? 
        Math.round((completedExercises / totalExercises) * 100) : 0;
    
    progressBar.style.width = `${progressPercentage}%`;
    progressText.textContent = `Progress: ${progressPercentage}%`;
};

document.getElementById("start-plan").addEventListener("click", async () => {
    console.log("Start Plan clicked");
    
    const user = auth.currentUser;
    if (!user) {
        console.log("No user signed in.");
        alert("Please log in to start a workout plan.");
        return;
    }
    
    userId = user.uid; // Store the user ID

    try {
        // If workout is already in progress, stop it
        if (currentWorkout.inProgress) {
            await stopWorkout();
            return;
        }

        // Get exercises based on fitness level
        const exercises = await getExercises(user.uid);
        if (Object.keys(exercises).length > 0) {
            startWorkoutSession(exercises);
        } else {
            console.log("No exercises found.");
            alert("No exercises found for your fitness level.");
        }
    } catch (error) {
        console.error("Error starting workout plan:", error);
    }
});

const startWorkoutSession = async (exercisesData) => {
    console.log("Workout session started");
    
    // Flatten exercise data for sequential processing
    const flattenedExercises = flattenExercises(exercisesData);
    
    if (flattenedExercises.length === 0) {
        alert("No exercises available to start.");
        return;
    }
    
    // Load completed exercises to filter out already completed ones
    const completedExercisesData = await loadCompletedExercises(userId);
    
    // Filter out completed exercises
    const availableExercises = flattenedExercises.filter(exercise => 
        !completedExercisesData || !completedExercisesData[exercise.exercise]
    );
    
    if (availableExercises.length === 0) {
        alert("All exercises are completed for today!");
        return;
    }
    
    // Initialize workout state
    currentWorkout = {
        exercises: exercisesData,
        flattenedExercises: availableExercises,
        currentExerciseIndex: -1,
        inProgress: true
    };
    
    // Set up UI
    createProgressDisplay();
    updateProgressDisplay();
    
    // Update button text
    document.getElementById("start-plan").textContent = "Stop Workout";
    
    // Start camera first
    try {
        const response = await fetch("http://localhost:5001/start-camera", { 
            method: "POST",
            headers: { "Content-Type": "application/json" }
        });
        
        const data = await response.json();
        console.log("Camera response:", data);
        
        // Start the first exercise after a short delay
        setTimeout(() => {
            moveToNextExercise();
        }, 3000);
        
    } catch (err) {
        console.error("Error starting camera:", err);
        alert("Failed to start camera. Please check that the server is running on port 5001.");
        resetWorkout();
    }
};

const loadCompletedExercises = async (userId) => {
    if (!userId) return {};
    
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

// This is the key function that needs fixing
const moveToNextExercise = async () => {
    // Move to next exercise
    currentWorkout.currentExerciseIndex++;
    
    // Check if workout is complete
    if (currentWorkout.currentExerciseIndex >= currentWorkout.flattenedExercises.length) {
        console.log("Workout complete!");
        await stopWorkout();
        alert("Congratulations! You've completed your workout.");
        return;
    }
    
    // Get current exercise
    const exercise = currentWorkout.flattenedExercises[currentWorkout.currentExerciseIndex];
    console.log(`Starting exercise ${currentWorkout.currentExerciseIndex + 1}/${currentWorkout.flattenedExercises.length}: ${exercise.exercise}`);
    
    // Update UI to show current exercise
    updateExerciseUI(exercise);
    
    // Start tracking for this exercise
    try {
        const response = await fetch("http://localhost:5001/start-exercise", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ 
                name: exercise.exercise, 
                type: exercise.type, 
                details: exercise 
            })
        });
        
        const data = await response.json();
        console.log(`${exercise.exercise} tracking started:`, data);
        
        // Set up continuous checking for exercise completion
        startExerciseCompletionCheck(exercise);
        
    } catch (err) {
        console.error(`Error tracking ${exercise.exercise}:`, err);
        // Continue to next exercise if there's an error
        setTimeout(() => {
            moveToNextExercise();
        }, 3000);
    }
};

// New function to periodically check if an exercise is complete
const startExerciseCompletionCheck = (exercise) => {
    const completionTime = calculateExerciseTime(exercise);
    let elapsedTime = 0;
    const checkInterval = 1000; // Check every second
    
    const timer = setInterval(() => {
        elapsedTime += checkInterval / 1000;
        
        // Update time remaining in UI
        const remainingTime = Math.max(0, completionTime - elapsedTime);
        updateExerciseTimeUI(exercise, remainingTime);
        
        // If time is up, consider exercise complete
        if (elapsedTime >= completionTime) {
            clearInterval(timer);
            console.log(`Exercise ${exercise.exercise} completed based on time.`);
            
            // Mark as complete and move to next exercise
            markExerciseCompleted(exercise)
                .then(() => moveToNextExercise())
                .catch(err => {
                    console.error(`Error completing ${exercise.exercise}:`, err);
                    moveToNextExercise(); // Move to next exercise even if there's an error
                });
        }
    }, checkInterval);
    
    // Store the timer ID in the exercise object to clear it if needed
    exercise.completionTimer = timer;
};

// New function to update time remaining in UI
const updateExerciseTimeUI = (exercise, remainingTime) => {
    const timeElement = document.getElementById("exercise-time-remaining");
    if (!timeElement) {
        const timeDisplay = document.createElement("p");
        timeDisplay.id = "exercise-time-remaining";
        timeDisplay.className = "time-display";
        document.getElementById("current-exercise-details").appendChild(timeDisplay);
    }
    
    document.getElementById("exercise-time-remaining").textContent = 
        `Time remaining: ${Math.round(remainingTime)}s`;
};

const calculateExerciseTime = (exercise) => {
    // Calculate estimated time for an exercise (in seconds)
    const type = exercise.type?.toLowerCase() || "reps";
    const sets = exercise.sets || 1;
    const rest = exercise.rest || 30;
    
    let totalTime = 0;
    
    if (type === "reps") {
        const reps = exercise.reps || 10;
        // Estimate 3 seconds per rep + rest between sets
        totalTime = (reps * 3 * sets) + (rest * (sets - 1));
    } else if (type === "time") {
        const duration = exercise.time || 30;
        totalTime = (duration * sets) + (rest * (sets - 1));
    } else if (type === "hold") {
        const duration = exercise.hold || 30;
        totalTime = (duration * sets) + (rest * (sets - 1));
    }
    
    // Add a buffer of 10 seconds
    return totalTime + 10;
};

const markExerciseCompleted = async (exercise) => {
    if (!exercise) {
        console.error("No exercise provided to markExerciseCompleted");
        return;
    }
    
    // Clear any ongoing timers for this exercise
    if (exercise.completionTimer) {
        clearInterval(exercise.completionTimer);
    }
    
    completedExercises++;
    updateProgressDisplay();

    if (userId) {
        // Save to Firebase that this exercise is completed
        await update(ref(dbRealtime, `users/${userId}/completedExercises/${exercise.exercise}`), {
            completed: true,
            timestamp: Date.now()
        });
    }

    // Also update the backend to ensure it knows the exercise is complete
    try {
        await fetch("http://localhost:5001/complete-exercise", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ exercise: exercise.exercise })
        });
    } catch (err) {
        console.error("Error marking exercise as complete on backend:", err);
    }

    // Update UI to reflect completion status
    document.querySelectorAll(".exercise-card").forEach(card => {
        if (card.querySelector("h4")?.textContent === exercise.exercise) {
            const btn = card.querySelector("button");
            if (btn) {
                btn.textContent = "✔ Completed";
                btn.disabled = true;
            }
        }
    });

    console.log(`Exercise ${exercise.exercise} marked as completed`);
};

const updateExerciseUI = (exercise) => {
    // Update the exercise name in the progress display
    const exerciseNameElement = document.getElementById("current-exercise-name");
    if (exerciseNameElement) {
        exerciseNameElement.textContent = `Current: ${exercise.exercise} (${currentWorkout.currentExerciseIndex + 1}/${currentWorkout.flattenedExercises.length})`;
    }
    
    // Create or update a more detailed exercise info element
    let exerciseDisplay = document.getElementById("current-exercise-details");
    if (!exerciseDisplay) {
        exerciseDisplay = document.createElement("div");
        exerciseDisplay.id = "current-exercise-details";
        exerciseDisplay.className = "exercise-details-display";
        document.body.appendChild(exerciseDisplay);
    }
    
    // Different display based on exercise type
    let typeSpecificDetails = '';
    if (exercise.type === "reps") {
        typeSpecificDetails = `<p><strong>Reps:</strong> ${exercise.reps || 10}</p>`;
    } else if (exercise.type === "time") {
        typeSpecificDetails = `<p><strong>Duration:</strong> ${exercise.time || 30}s</p>`;
    } else if (exercise.type === "hold") {
        typeSpecificDetails = `<p><strong>Hold Time:</strong> ${exercise.hold || 30}s</p>`;
    }
    
    exerciseDisplay.innerHTML = `
        <h3>${exercise.exercise}</h3>
        <div class="exercise-details">
            <p><strong>Category:</strong> ${exercise.category}</p>
            <p><strong>Type:</strong> ${exercise.type}</p>
            ${typeSpecificDetails}
            <p><strong>Sets:</strong> ${exercise.sets || 1}</p>
            <p><strong>Rest:</strong> ${exercise.rest || 30}s</p>
        </div>
    `;
};

const stopWorkout = async () => {
    try {
        // Stop the tracker
        await fetch("http://localhost:5001/stop-tracking", {
            method: "POST",
            headers: { "Content-Type": "application/json" }
        });
        
        console.log("Workout stopped");
        resetWorkout();
        
    } catch (err) {
        console.error("Error stopping workout:", err);
    }
};

const resetWorkout = () => {
    // Clear any ongoing timers
    if (currentWorkout.flattenedExercises) {
        currentWorkout.flattenedExercises.forEach(exercise => {
            if (exercise.completionTimer) {
                clearInterval(exercise.completionTimer);
            }
        });
    }
    
    // Reset workout state
    currentWorkout = {
        exercises: [],
        flattenedExercises: [],
        currentExerciseIndex: -1,
        inProgress: false
    };
    
    // Reset progress counters
    totalExercises = 0;
    completedExercises = 0;
    
    // Update UI
    document.getElementById("start-plan").textContent = "Start Plan";
    
    // Remove exercise displays if they exist
    const exerciseDetails = document.getElementById("current-exercise-details");
    if (exerciseDetails) {
        exerciseDetails.remove();
    }
    
    const progressContainer = document.getElementById("workout-progress-container");
    if (progressContainer) {
        progressContainer.remove();
    }
    
    const timeRemaining = document.getElementById("exercise-time-remaining");
    if (timeRemaining) {
        timeRemaining.remove();
    }
};

// Initialize on page load
window.addEventListener("load", () => {
    // Check for existing workout on page reload
    resetWorkout();
});