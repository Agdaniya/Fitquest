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

// Track progress data
let totalExercises = 0;
let completedExercises = 0;
let completedExercisesList = {};

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
            
            // Load completed exercises for today
            await setupCompletedExercisesListener(user.uid);
            
            // Display exercises for user
            displayExercises(user.uid);
        }
    });
});
const setupCompletedExercisesListener = (userId) => {
    const today = new Date().toISOString().split('T')[0];
    const completedRef = ref(dbRealtime, `users/${userId}/completedExercises/${today}`);
    
    // Set up a real-time listener
    onValue(completedRef, (snapshot) => {
        if (snapshot.exists()) {
            completedExercisesList = snapshot.val();
            console.log("Updated completed exercises:", completedExercisesList);
            updateCompletedExercisesUI();
        } else {
            completedExercisesList = {};
        }
    });
};
const updateCompletedExercisesUI = () => {
    completedExercises = 0;
    
    document.querySelectorAll('.exercise-card').forEach(card => {
        const startBtn = card.querySelector('button');
        const exerciseTitle = card.querySelector('h4').textContent;
        const exerciseType = card.querySelector('p:nth-child(2)').textContent.split(':')[1].trim();
        const exerciseId = `${exerciseType.toLowerCase()}_${exerciseTitle}`.replace(/\s+/g, '_').toLowerCase();
        
        if (completedExercisesList[exerciseId]) {
            startBtn.textContent = "Completed";
            startBtn.disabled = true;
            card.classList.add("completed");
            completedExercises++;
        } else if (!card.classList.contains("in-progress")) {
            startBtn.textContent = "Start";
            startBtn.disabled = false;
            card.classList.remove("completed");
        }
    });
    
    updateProgressBar();
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
            if (completedExercisesList[exerciseId]) {
                startButton.textContent = "Completed";
                startButton.disabled = true;
                card.classList.add("completed");
                completedExercises++;
            } else {
                startButton.textContent = "Start";
                startButton.addEventListener("click", () => startExercise(exercise, card));
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

const updateProgressBar = () => {
    const progressBar = document.getElementById("progress-bar");
    const progressText = document.getElementById("progress-text");
    
    if (!progressBar || !progressText) return;
    
    const progressPercentage = totalExercises > 0 ? Math.round((completedExercises / totalExercises) * 100) : 0;
    
    progressBar.style.width = `${progressPercentage}%`;
    progressText.textContent = `Progress: ${progressPercentage}%`;
};


// Function to mark exercise as completed
const markExerciseCompleted = (exercise) => {
    const userId = auth.currentUser.uid;
    const today = new Date().toISOString().split('T')[0];
    const exerciseId = `${exercise.category}_${exercise.exercise}`.replace(/\s+/g, '_').toLowerCase();
    
    completedExercisesList[exerciseId] = true;
    completedExercises++;
    updateProgressBar();
    
    // Save to database
    const completedRef = ref(dbRealtime, `users/${userId}/completedExercises/${today}/${exerciseId}`);
    set(completedRef, true);
    
    // Update daily progress
    updateDailyProgress(userId, today);
    
    // Important: Update the UI to reflect completion across all exercises
    updateCompletedExercisesUI();
};
const startExercise = async (exercise, card) => {
    const startBtn = card.querySelector("button");
    startBtn.disabled = true;
    startBtn.textContent = "In Progress";
    card.classList.add("in-progress");
    
    try {
        // Start exercise tracking
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
        
        // For reps exercises
        if (exercise.type === "reps") {
            // Show timer for estimated duration
            const estimatedTime = exercise.reps * 3; // 3 seconds per rep
            let countdown = estimatedTime;
            
            const timer = setInterval(() => {
                // Keep "In Progress" text
                countdown--;
                
                if (countdown < 0) {
                    clearInterval(timer);
                    // Stop tracking and mark as completed
                    fetch("http://localhost:5001/stop-tracking", {
                        method: "POST"
                    }).then(() => {
                        // Mark exercise as completed both in UI and database
                        markExerciseCompleted(exercise);
                        card.classList.add("completed");
                        card.classList.remove("in-progress");
                        startBtn.textContent = "Completed";
                        startBtn.disabled = true;
                    });
                }
            }, 1000);
        } 
        // For time-based or hold exercises
        else {
            const duration = exercise.type === "hold" ? exercise.hold : exercise.time;
            let countdown = duration;
            
            const timer = setInterval(() => {
                // Keep "In Progress" text
                countdown--;
                
                if (countdown < 0) {
                    clearInterval(timer);
                    // Stop tracking and show rest period
                    fetch("http://localhost:5001/stop-tracking", {
                        method: "POST"
                    }).then(() => {
                        showRestPeriod(exercise, card);
                    });
                }
            }, 1000);
        }
    } catch (error) {
        console.error("Error starting exercise:", error);
        startBtn.disabled = false;
        startBtn.textContent = "Start";
        card.classList.remove("in-progress");
    }
};

const showRestPeriod = (exercise, card) => {
    let countdown = exercise.rest;
    const startBtn = card.querySelector("button");
    startBtn.textContent = "Resting";
    
    const interval = setInterval(() => {
        if (--countdown < 0) {
            clearInterval(interval);
            // Mark exercise as completed both in UI and database
            markExerciseCompleted(exercise);
            startBtn.textContent = "Completed";
            startBtn.disabled = true;
            card.classList.add("completed");
            card.classList.remove("in-progress");
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
                    markExerciseCompleted(exercise); 
                    clearInterval(checkInterval); 
                }
            });
    }, 3000);
};
const isExerciseCompleted = (exercise) => {
    const exerciseId = `${exercise.category}_${exercise.exercise}`.replace(/\s+/g, '_').toLowerCase();
    return completedExercisesList[exerciseId] === true;
};
// Update daily progress percentage
const updateDailyProgress = async (userId, date) => {
    const progressPercentage = totalExercises > 0 ? Math.round((completedExercises / totalExercises) * 100) : 0;
    const progressRef = ref(dbRealtime, `users/${userId}/dailyProgress/${date}`);
    await set(progressRef, progressPercentage);
    
    // Check if stage progression criteria are met
    checkStageProgression(userId);
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
