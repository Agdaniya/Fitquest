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
        return;
    }

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
    
    // Initialize workout state
    currentWorkout = {
        exercises: exercisesData,
        flattenedExercises: flattenedExercises,
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
        
        // Automatically move to next exercise after estimated completion time
        // This is a basic approach - ideally the Python script would signal completion
        const completionTime = calculateExerciseTime(exercise);
        setTimeout(() => {
            markExerciseCompleted();
            moveToNextExercise();
        }, completionTime * 1000);
        
    } catch (err) {
        console.error(`Error tracking ${exercise.exercise}:`, err);
        // Continue to next exercise if there's an error
        setTimeout(() => {
            moveToNextExercise();
        }, 3000);
    }
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

const markExerciseCompleted = () => {
    completedExercises++;
    updateProgressDisplay();
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
};

// Initialize on page load
window.addEventListener("load", () => {
    // Check for existing workout on page reload
    resetWorkout();
});