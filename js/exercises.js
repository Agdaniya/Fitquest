import { initializeApp } from "https://www.gstatic.com/firebasejs/9.6.1/firebase-app.js";
import { getAuth, onAuthStateChanged } from "https://www.gstatic.com/firebasejs/9.6.1/firebase-auth.js";
import { getDatabase, ref, set, get , update , onValue} from "https://www.gstatic.com/firebasejs/9.6.1/firebase-database.js";
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
window.globalCompletedExercisesList = {};
let eventSource = null;
// Progress tracking
let totalExercises = 0;
let completedExercises = 0;

const initializeUserData = async (userId) => {
    const userRef = ref(dbRealtime, `users/${userId}`);
    const snapshot = await get(userRef);
    
    if (!snapshot.exists() || !snapshot.val().stage) {
        // User doesn't have stage set
        await set(ref(dbRealtime, `users/${userId}/stage`), 1);
    }
    
    // Clear completed exercises if it's a new day
    const lastActiveRef = ref(dbRealtime, `users/${userId}/lastActive`);
    const lastActiveSnapshot = await get(lastActiveRef);
    const today = new Date().toISOString().split('T')[0];
    
    if (!lastActiveSnapshot.exists() || lastActiveSnapshot.val() !== today) {
        // It's a new day, clear completed exercises
        await set(ref(dbRealtime, `users/${userId}/lastActive`), today);
    }
};

document.addEventListener("DOMContentLoaded", () => {
    onAuthStateChanged(auth, async (user) => {
        if (user) {
            // Initialize user data
            await initializeUserData(user.uid);
            
            // Set up real-time exercise completion listener
            setupExerciseCompletionListener(user.uid);
            
            // Display exercises for user
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
    
    // Load completed exercises first
    await loadCompletedExercises(userId);
    
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
            // Add category to exercise object
            exercise.category = type;
            
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
            
            // Check if already completed
            const exerciseId = `${type}_${exercise.exercise}`.replace(/\s+/g, '_').toLowerCase();
            if (window.globalCompletedExercisesList[exerciseId]) {
                startButton.textContent = "Completed";
                startButton.disabled = true;
                card.classList.add("completed");
                completedExercises++;
            } else {
                startButton.textContent = "Start";
                startButton.addEventListener("click", async () => {
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
                        
                        // Start the specific exercise instead of getting all exercises
                        startExercise(exercise, card);
                    } catch (error) {
                        console.error("Error starting exercise:", error);
                    }
            });
            }
            
            startButton.classList.add("start-btn");
            card.innerHTML = details;
            card.appendChild(startButton);
            section.appendChild(card);
        });
        container.appendChild(section);
    });
    
    // Update progress bar
    updateProgressBar();
};
const startExercise = async (exercise, card) => {
    try {
        const user = auth.currentUser;
        if (!user) {
            console.log("No user signed in.");
            return;
        }

        // Start camera first
        const cameraResponse = await fetch("http://localhost:5001/start-camera", { 
            method: "POST",
            headers: { "Content-Type": "application/json" }
        });
        
        const cameraData = await cameraResponse.json();
        console.log("Camera response:", cameraData);
        
        // Start tracking for this exercise
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
        
        // Change button state to IN PROGRESS
        const startButton = card.querySelector(".start-btn");
        startButton.textContent = "In Progress";
        startButton.disabled = false; // Allow clicking to stop the exercise
        card.classList.add("in-progress");
        
        // Update button to allow stopping the exercise
        startButton.addEventListener("click", async () => {
            // Stop the tracking
            await fetch("http://localhost:5001/stop-tracking", {
                method: "POST",
                headers: { "Content-Type": "application/json" }
            });
            
            // Reset the button
            startButton.textContent = "Start";
            card.classList.remove("in-progress");
            
            // Remove the click event listener to prevent multiple listeners
            startButton.replaceWith(startButton.cloneNode(true));
            
            // Add the original event listener back
            card.querySelector(".start-btn").addEventListener("click", () => {
                startExercise(exercise, card);
            });
        }, { once: true }); // Use once: true to ensure this listener only fires once
        
        // The exercise completion will be handled by the event listener
        // No need for setTimeout to automatically mark as completed
        
    } catch (err) {
        console.error(`Error starting exercise:`, err);
        alert("Failed to start exercise. Please check that the server is running on port 5001.");
    }
};
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
const updateProgressDisplay = () => {
    const progressBar = document.getElementById("workout-progress-bar");
    const progressText = document.getElementById("workout-progress-text");
    
    if (!progressBar || !progressText) return;
    
    const progressPercentage = totalExercises > 0 ? 
        Math.round((completedExercises / totalExercises) * 100) : 0;
    
    progressBar.style.width = `${progressPercentage}%`;
    progressText.textContent = `Progress: ${progressPercentage}%`;
};
const startWorkoutSession = async (exercisesData) => {
    console.log("Workout session started");
    
    // Flatten exercise data for sequential processing
    const flattenedExercises = flattenExercises(exercisesData);
    
    // Filter out completed exercises
    const today = new Date().toISOString().split('T')[0];
    const userId = auth.currentUser.uid;
    const completedRef = ref(dbRealtime, `users/${userId}/completedExercises/${today}`);
    const completedExercises = window.globalCompletedExercisesList || {};

    try {
        const snapshot = await get(completedRef);
        if (snapshot.exists()) {
            const completedExercises = snapshot.val();
            
            // Filter exercises
            const filteredExercises = flattenedExercises.filter(exercise => {
                const exerciseId = `${exercise.category}_${exercise.exercise}`.replace(/\s+/g, '_').toLowerCase();
                return !completedExercises[exerciseId];
            });
            
            // Update flattened exercises list
            currentWorkout.flattenedExercises = filteredExercises;
        } else {
            currentWorkout.flattenedExercises = flattenedExercises;
        }
    } catch (error) {
        console.error("Error loading completed exercises:", error);
        currentWorkout.flattenedExercises = flattenedExercises;
    }
    
    if (currentWorkout.flattenedExercises.length === 0) {
        alert("All exercises for today are completed! Great job!");
        return;
    }
    
    // Initialize workout state
    currentWorkout.exercises = exercisesData;
    currentWorkout.currentExerciseIndex = -1;
    currentWorkout.inProgress = true;
    
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

// Add to getExercises in startplan.js or exercises.js

const getExercises = async (userId) => {
    const fitnessLevel = await getFitnessLevel(userId);
    
    // Get user stage
    const stageRef = ref(dbRealtime, `users/${userId}/stage`);
    const stageSnapshot = await get(stageRef);
    const stage = stageSnapshot.exists() ? stageSnapshot.val() : 1;
    
    const exercisesRef = doc(dbFirestore, "exercises", fitnessLevel);

    try {
        const docSnap = await getDoc(exercisesRef);
        if (docSnap.exists()) {
            const exercises = docSnap.data();
            
            // Adjust exercise durations based on stage
            Object.keys(exercises).forEach(category => {
                exercises[category].forEach(exercise => {
                    // Adjust times based on stage (add 5 seconds per stage)
                    const stageMultiplier = (stage - 1) * 5;
                    
                    if (exercise.type === "time") {
                        exercise.time += stageMultiplier;
                    } else if (exercise.type === "hold") {
                        exercise.hold += stageMultiplier;
                    } else if (exercise.type === "reps") {
                        // Add 1 rep per stage
                        exercise.reps += (stage - 1);
                    }
                });
            });
            
            console.log(`Retrieved exercises for fitness level: ${fitnessLevel}, stage: ${stage}`, exercises);
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
const markExerciseCompletedInDatabase = (exercise) => {
    const userId = auth.currentUser.uid;
    const today = new Date().toISOString().split('T')[0];
    const exerciseId = `${exercise.category}_${exercise.exercise}`.replace(/\s+/g, '_').toLowerCase();
    
    // Also update the global list directly (for immediate UI feedback)
    if (window.globalCompletedExercisesList) {
        window.globalCompletedExercisesList[exerciseId] = true;
    }
    
    // Save to database
    const completedRef = ref(dbRealtime, `users/${userId}/completedExercises/${today}/${exerciseId}`);
    set(completedRef, true);
    
    // Update daily progress
    updateDailyProgress(userId, today);
};

// Add this function to startplan.js (copied from exercises.js)
const updateDailyProgress = async (userId, date) => {
    // Need to calculate total available exercises 
    const fitnessLevel = await getFitnessLevel(userId);
    const exercisesRef = doc(dbFirestore, "exercises", fitnessLevel);
    
    try {
        const docSnap = await getDoc(exercisesRef);
        if (docSnap.exists()) {
            const exercises = docSnap.data();
            let totalAvailableExercises = 0;
            
            // Count total exercises
            Object.keys(exercises).forEach(category => {
                totalAvailableExercises += exercises[category].length;
            });
            
            // Get current completed count
            const completedRef = ref(dbRealtime, `users/${userId}/completedExercises/${date}`);
            const completedSnap = await get(completedRef);
            const completedCount = completedSnap.exists() ? Object.keys(completedSnap.val()).length : 0;
            
            // Calculate and save progress percentage
            const progressPercentage = totalAvailableExercises > 0 ? 
                Math.round((completedCount / totalAvailableExercises) * 100) : 0;
            
            const progressRef = ref(dbRealtime, `users/${userId}/dailyProgress/${date}`);
            await set(progressRef, progressPercentage);
            
            // Check if stage progression criteria are met
            checkStageProgression(userId);
        }
    } catch (error) {
        console.error("Error updating daily progress:", error);
    }
};
const checkStageProgression = async (userId) => {
    try {
        // Get current stage and fitness level
        const userRef = ref(dbRealtime, `users/${userId}`);
        const snapshot = await get(userRef);
        
        if (!snapshot.exists()) return;
        
        const userData = snapshot.val();
        const currentFitnessLevel = userData.fitnessLevel || "beginner";
        const currentStage = userData.stage || 1;
        
        // Get daily progress for the past 7 days
        const today = new Date();
        const dailyProgressRef = ref(dbRealtime, `users/${userId}/dailyProgress`);
        const progressSnapshot = await get(dailyProgressRef);
        
        if (!progressSnapshot.exists()) return;
        
        const progressData = progressSnapshot.val();
        
        // Count days with >90% progress in the last 7 days
        let highProgressDays = 0;
        for (let i = 0; i < 7; i++) {
            const date = new Date(today);
            date.setDate(date.getDate() - i);
            const dateStr = date.toISOString().split('T')[0];
            
            if (progressData[dateStr] && progressData[dateStr] >= 90) {
                highProgressDays++;
            }
        }
        
        // Check if criteria for progression is met (4+ days with >90%)
        if (highProgressDays >= 4) {
            // Determine next stage
            if (currentStage === 3) {
                // Move to next fitness level
                let nextFitnessLevel;
                if (currentFitnessLevel === "beginner") {
                    nextFitnessLevel = "intermediate";
                } else if (currentFitnessLevel === "intermediate") {
                    nextFitnessLevel = "advanced";
                } else {
                    // Already at advanced level
                    return;
                }
                
                // Update fitness level and reset stage to 1
                await set(ref(dbRealtime, `users/${userId}/fitnessLevel`), nextFitnessLevel);
                await set(ref(dbRealtime, `users/${userId}/stage`), 1);
                
                alert(`Congratulations! You've advanced to ${nextFitnessLevel} level!`);
            } else {
                // Move to next stage within current fitness level
                const nextStage = currentStage + 1;
                await set(ref(dbRealtime, `users/${userId}/stage`), nextStage);
                
                alert(`Congratulations! You've advanced to stage ${nextStage}!`);
            }
        }
    } catch (error) {
        console.error("Error checking stage progression:", error);
    }
};
const updateProgressBar = () => {
    const progressBar = document.getElementById("progress-bar");
    const progressText = document.getElementById("progress-text");
    
    if (!progressBar || !progressText) return;
    
    const progressPercentage = totalExercises > 0 ? Math.round((completedExercises / totalExercises) * 100) : 0;
    
    progressBar.style.width = `${progressPercentage}%`;
    progressText.textContent = `Progress: ${progressPercentage}%`;
};
const updateCompletedExerciseUI = (exercise) => {
    // Create an identifier for the exercise
    const exerciseId = `${exercise.category}_${exercise.exercise}`.replace(/\s+/g, '_').toLowerCase();
    
    // Find all exercise cards on the page
    const exerciseCards = document.querySelectorAll('.exercise-card');
    
    // Loop through all cards to find the matching one
    exerciseCards.forEach(card => {
        const cardTitle = card.querySelector('h4')?.textContent;
        const cardCategory = card.querySelector('p:first-of-type')?.textContent.split(':')[1]?.trim();
        
        // Check if this card matches our completed exercise
        if (cardTitle === exercise.exercise && 
            cardCategory === exercise.type) {
            
            // Update the card's appearance
            card.classList.remove('in-progress');
            card.classList.add('completed');
            
            // Update the button
            const startButton = card.querySelector('.start-btn');
            if (startButton) {
                startButton.textContent = "Completed";
                startButton.disabled = true;
            }
        }
    });
};
const loadCompletedExercises = async (userId) => {
    const today = new Date().toISOString().split('T')[0];
    const completedRef = ref(dbRealtime, `users/${userId}/completedExercises/${today}`);
    
    try {
        const snapshot = await get(completedRef);
        if (snapshot.exists()) {
            // Store in global variable for easy access
            window.globalCompletedExercisesList = snapshot.val();
            return snapshot.val();
        } else {
            window.globalCompletedExercisesList = {};
            return {};
        }
    } catch (error) {
        console.error("Error loading completed exercises:", error);
        window.globalCompletedExercisesList = {};
        return {};
    }
};
const setupExerciseCompletionListener = (userId) => {
    // Close existing connection if any
    if (eventSource) {
        eventSource.close();
    }
    
    // Create new EventSource connection
    eventSource = new EventSource('http://localhost:5001/events');
    
    // Handle exercise completion events
    eventSource.addEventListener('message', (event) => {
        try {
            const data = JSON.parse(event.data);
            
            // Skip heartbeat messages
            if (data.type === 'heartbeat') {
                return;
            }
            
            console.log('Exercise completion event received:', data);
            
            // Handle completed exercise
            if (data.completed) {
                // Create exercise object in the format expected by markExerciseCompletedInDatabase
                const exercise = {
                    exercise: data.exercise,
                    type: data.type,
                    category: data.category
                };
                
                // Mark the exercise as completed
                markExerciseCompletedInDatabase(exercise);
                
                // Update UI
                updateCompletedExerciseUI(exercise);
                
                // Update progress
                completedExercises++;
                updateProgressDisplay();
                
                // Show a notification
                alert(`Exercise "${data.exercise}" completed!`);
            }
        } catch (error) {
            console.error('Error processing exercise completion event:', error);
        }
    });
    
    // Handle connection errors
    eventSource.addEventListener('error', (error) => {
        console.error('EventSource connection error:', error);
        
        // Try to reconnect after 5 seconds
        setTimeout(() => {
            if (eventSource.readyState === EventSource.CLOSED) {
                setupExerciseCompletionListener(userId);
            }
        }, 5000);
    });
    
    console.log('Exercise completion listener set up');
};