console.log("Script starting execution");

import { initializeApp } from "https://www.gstatic.com/firebasejs/10.13.2/firebase-app.js";
import { getAuth, onAuthStateChanged } from "https://www.gstatic.com/firebasejs/10.13.2/firebase-auth.js";
import { getDatabase, ref, onValue, get, set, update } from "https://www.gstatic.com/firebasejs/10.13.2/firebase-database.js";
import { getFirestore, doc, getDoc } from "https://www.gstatic.com/firebasejs/10.13.2/firebase-firestore.js";
import { initializeLevelDisplay } from './leveldisplay.js';

console.log("Imports completed");

// Your web app's Firebase configuration
const firebaseConfig = {
    apiKey: "AIzaSyAOgdbddMw93MExNBz3tceZ8_NrNAl5q40",
    authDomain: "fitquest-9b891.firebaseapp.com",
    projectId: "fitquest-9b891",
    storageBucket: "fitquest-9b891.appspot.com",
    messagingSenderId: "275044631678",
    appId: "1:275044631678:web:7fa9586ba031270baa042f",
    measurementId: "G-6W3V2DH02K"
};

console.log("Initializing Firebase");
const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const database = getDatabase(app);
const firestore = getFirestore(app);

console.log("Firebase initialized");

document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM fully loaded and parsed');

    onAuthStateChanged(auth, (user) => {
        console.log("Auth state changed");
        if (user) {
            console.log("User is logged in:", user.uid);
            fetchTotalCaloriesBurned(user.uid);
            fetchTotalWorkouts(user.uid);
            updateLoginStreak(user.uid);
            fetchExerciseCounts(user.uid);
            initializeWaterIntakeTracker();
            initializeWelcomeMessage();
            fetchUserFitnessLevel(user.uid);
            initializeLevelDisplay(user.uid);

        } else {
            console.log("No user is authenticated");
            window.location.href = 'home.html'; // Redirect to login page
        }
    });

    //initializeCardFlipListeners();
});

function fetchTotalCaloriesBurned(userId) {
    console.log("Attempting to fetch total calories burned for user:", userId);
    const totalCaloriesRef = ref(database, `users/${userId}/totalCaloriesBurned`);

    console.log("Database reference created:", totalCaloriesRef.toString());

    onValue(totalCaloriesRef, (snapshot) => {
        console.log("onValue callback triggered");
        if (snapshot.exists()) {
            const totalCalories = snapshot.val();
            console.log("Total calories fetched:", totalCalories);
            updateCaloriesBurnedDisplay(totalCalories);
        } else {
            console.log("No total calories data found. Displaying 0.");
            updateCaloriesBurnedDisplay(0);
        }
    }, (error) => {
        console.error('Error fetching total calories burned:', error);
    });
}

function updateCaloriesBurnedDisplay(totalCalories) {
    console.log("Updating calories burned display with value:", totalCalories);
    const caloriesBurnedDisplay = document.getElementById('calories-burned');
    console.log("Element found:", caloriesBurnedDisplay);
    if (caloriesBurnedDisplay) {
        caloriesBurnedDisplay.textContent = totalCalories;
        console.log("Calories burned display updated successfully");
    } else {
        console.error("Element with ID 'calories-burned' not found");
    }
}

function fetchExerciseCounts(userId) {
    const exerciseTypes = ['jumping-jacks', 'squats', 'pushups', 'planks'];

    exerciseTypes.forEach(exerciseType => {
        const userExerciseRef = ref(database, `users/${userId}/exercises/${exerciseType}`);
        onValue(userExerciseRef, (snapshot) => {
            if (snapshot.exists()) {
                const data = snapshot.val();
                updateExerciseCountDisplay(exerciseType, data.count);
            } else {
                updateExerciseCountDisplay(exerciseType, 0);
            }
        });
    });
}

function updateExerciseCountDisplay(exerciseType, count) {
    const countDisplay = document.getElementById(`${exerciseType}-count`);
    if (countDisplay) {
        countDisplay.textContent = count;
    }
}

function fetchTotalWorkouts(userId) {
    const totalWorkoutsRef = ref(database, `users/${userId}/totalWorkouts`);
    onValue(totalWorkoutsRef, (snapshot) => {
        if (snapshot.exists()) {
            const totalWorkouts = snapshot.val();
            updateTotalWorkoutsDisplay(totalWorkouts);
        } else {
            updateTotalWorkoutsDisplay(0);
        }
    });
}

function updateTotalWorkoutsDisplay(totalWorkouts) {
    const totalWorkoutsDisplay = document.getElementById('total-workouts');
    if (totalWorkoutsDisplay) {
        totalWorkoutsDisplay.textContent = totalWorkouts;
    }
}

function updateLoginStreak(userId) {
    const userRef = ref(database, `users/${userId}`);
    const today = new Date().toDateString();
    const yesterday = new Date(Date.now() - 86400000).toDateString();

    get(userRef).then((snapshot) => {
        if (snapshot.exists()) {
            const userData = snapshot.val();
            const lastLogin = userData.lastLogin || '';
            const currentStreak = userData.loginStreak || 0;

            if (lastLogin !== today) {
                let newStreak = (lastLogin === yesterday) ? currentStreak + 1 : 1;

                update(userRef, {
                    lastLogin: today,
                    loginStreak: newStreak
                }).then(() => {
                    updateLoginStreakDisplay(newStreak);
                }).catch((error) => {
                    console.error("Error updating user data:", error);
                });
            } else {
                updateLoginStreakDisplay(currentStreak);
            }
        } else {
            set(userRef, {
                lastLogin: today,
                loginStreak: 1
            }).then(() => {
                updateLoginStreakDisplay(1);
            }).catch((error) => {
                console.error("Error setting user data:", error);
            });
        }
    }).catch((error) => {
        console.error("Error fetching user data:", error);
    });
}

function updateLoginStreakDisplay(streak) {
    const streakDisplay = document.getElementById('login-streak');
    if (streakDisplay) {
        streakDisplay.textContent = streak;
    }
}
const todaysGoal = document.getElementById('todaysGoals');
function initializeWelcomeMessage() {
    const welcomeMessage = document.getElementById('welcomeMessage');
    
    
    const currentHour = new Date().getHours();
    let greeting;

    if (currentHour < 12) {
        greeting = "Good morning";
    } else if (currentHour < 18) {
        greeting = "Good afternoon";
    } else {
        greeting = "Good evening";
    }

    if (welcomeMessage) {
        welcomeMessage.textContent = `${greeting}!`;
    }
}
if (todaysGoal) {
    const storedGoal = localStorage.getItem('todaysGoal');
    console.log('Retrieved todaysGoal from localStorage:', storedGoal);

    if (storedGoal) {
        todaysGoal.innerHTML = `<p>${storedGoal}</p>`;
    } else {
        todaysGoal.innerHTML = '<p>No goal set for today. Visit the Workout Plan page to set your goal.</p>';
        console.log('No goal found in localStorage');
    }
} else {
    console.warn("Today's goal element not found");
}

function initializeWaterIntakeTracker() {
    let waterIntake = 0;
    const waterLevel = document.getElementById('waterLevel');
    const waterAmount = document.getElementById('waterAmount');

    if (localStorage.getItem('waterIntake')) {
        waterIntake = parseInt(localStorage.getItem('waterIntake'));
        console.log("Restored water intake from localStorage:", waterIntake);
        updateWaterDisplay();
    }

    console.log("Initial water intake:", waterIntake);

    document.getElementById('hundred')?.addEventListener('click', () => addWater(100));
    document.getElementById('twofifty')?.addEventListener('click', () => addWater(250));
    document.getElementById('fivehundred')?.addEventListener('click', () => addWater(500));
    document.getElementById('reset')?.addEventListener('click', resetWaterIntake);

    function addWater(amount) {
        console.log("addWater called with amount:", amount);
        waterIntake += amount;
        console.log("New water intake:", waterIntake);

        localStorage.setItem('waterIntake', waterIntake);

        updateWaterDisplay();
        showNotification(`Great job! You've added ${amount}ml of water.`);
    }

    function updateWaterDisplay() {
        console.log("updateWaterDisplay called");
        const maxHeight = 300;
        const maxWater = 2000;
        const height = Math.min((waterIntake / maxWater) * maxHeight, maxHeight);

        console.log("Calculated height:", height);
        if (waterLevel) {
            waterLevel.style.height = `${height}px`;
        }
        if (waterAmount) {
            waterAmount.textContent = `${waterIntake} ml`;
        }
        console.log("Updated water amount text:", waterAmount?.textContent);

        if (waterIntake >= 2000) {
            showNotification("Wow! You're a hydration superstar! 🌊");
        } else if (waterIntake >= 1500) {
            showNotification("You're doing great! Keep it flowing! 💧");
        } else if (waterIntake >= 1000) {
            showNotification("Halfway there! You're making waves! 🌊");
        } else if (waterIntake >= 500) {
            showNotification("Nice start! Keep sipping! 💦");
        }
    }

    function resetWaterIntake() {
        console.log("resetWaterIntake called");
        waterIntake = 0;
        localStorage.setItem('waterIntake', waterIntake);
        updateWaterDisplay();
        showNotification("Water intake has been reset.");
    }
}

function showNotification(message) {
    console.log("showNotification called with message:", message);
    const notificationContainer = document.getElementById('notification-container');
    if (notificationContainer) {
        const notification = document.createElement('div');
        notification.className = 'notification';
        notification.textContent = message;
        notificationContainer.appendChild(notification);
        setTimeout(() => {
            notification.remove();
        }, 3000);
    }
}

        /*function initializeCardFlipListeners() {
            const cards = document.querySelectorAll('.stat-card');
            cards.forEach(card => {
                card.addEventListener('click', () => {
                    const cardInner = card.querySelector('.card-inner');
                    if (cardInner) {
                        cardInner.style.transform = 
                            cardInner.style.transform === 'rotateY(180deg)' 
                                ? 'rotateY(0deg)' 
                                : 'rotateY(180deg)';
                    }
                });
            });
        }*/
            
            async function fetchUserFitnessLevel(userId) {
                try {
                    const userRef = ref(database, `users/${userId}`);
                    const snapshot = await get(userRef);
                    
                    if (snapshot.exists()) {
                        const userData = snapshot.val();
                        let fitnessLevel = userData.fitnessLevel; // Check if fitness level is set
                        let userStage = userData.stage; // Check if stage is set
            
                        // If no fitness level exists, set it to "beginner" and store in Firebase
                        if (!fitnessLevel) {
                            fitnessLevel = "beginner";
                            await update(userRef, { fitnessLevel }); // Save fitness level
                        }
            
                        // If no stage exists, initialize based on fitness level
                        if (!userStage) {
                            if (fitnessLevel === "beginner") {
                                userStage = "beginner1";
                            } else if (fitnessLevel === "intermediate") {
                                userStage = "intermediate1";
                            } else {
                                userStage = "advanced1";
                            }
            
                            // Save the initial stage in Firebase
                            await update(userRef, { stage: userStage });
                        }
            
                        updateFitnessLevelDisplay(fitnessLevel);
                        await fetchExercisesForFitnessLevel(fitnessLevel);
                    }
                } catch (error) {
                    console.error("Error fetching user fitness level:", error);
                }
            }
            
            
function updateFitnessLevelDisplay(fitnessLevel) {
    const fitnessLevelDisplay = document.getElementById('fitness-level');
    if (fitnessLevelDisplay) {
        fitnessLevelDisplay.textContent = fitnessLevel;
        
        // Remove previous fitness level classes
        fitnessLevelDisplay.classList.remove('beginner', 'intermediate', 'professional');
        
        // Add class based on fitness level
        fitnessLevelDisplay.classList.add(fitnessLevel.toLowerCase());
    }
}
async function fetchExercisesForFitnessLevel(fitnessLevel) {
    try {
        // Fetch exercises from Firestore for the specific fitness level
        const exerciseDocRef = doc(firestore, 'exercises', fitnessLevel);
        const exerciseDoc = await getDoc(exerciseDocRef);
        
        if (exerciseDoc.exists()) {
            const exercisesData = exerciseDoc.data().exercises;
            updateWorkoutCards(exercisesData);
        } else {
            console.error('No exercises found for fitness level:', fitnessLevel);
        }
    } catch (error) {
        console.error('Error fetching exercises:', error);
    }
}

function updateWorkoutCards(exercises) {
    const workoutsContainer = document.querySelector('.workouts');
    
    // Clear existing workout cards
    workoutsContainer.innerHTML = '';
    
    // Create new workout cards based on fetched exercises
    exercises.forEach(exercise => {
        const workoutCard = `
            <div class="workout-card">
                <div class="card-inner">
                    <div class="card-front">
                        <img src="${exercise.image}" alt="${exercise.name}">
                        <h2 class="para">${exercise.name}</h2>
                    </div>
                    <div class="card-back">
                        <h3>${exercise.name}</h3>
                        <p>${exercise.description}</p>
                        <p>Sets: ${exercise.sets}</p>
                        <p>${exercise.reps ? `Reps: ${exercise.reps}` : `Duration: ${exercise.duration}`}</p>
                        <p>Rest: ${exercise.rest}</p>
                    </div>
                </div>
            </div>
        `;
        
        workoutsContainer.innerHTML += workoutCard;
    });
    
    // Reinitialize card flip listeners
    initializeCardFlipListeners();
}

// Keep your existing initializeCardFlipListeners function
function initializeCardFlipListeners() {
    const cards = document.querySelectorAll('.workout-card');
    cards.forEach(card => {
        card.addEventListener('click', () => {
            const cardInner = card.querySelector('.card-inner');
            if (cardInner) {
                cardInner.style.transform = 
                    cardInner.style.transform === 'rotateY(180deg)' 
                        ? 'rotateY(0deg)' 
                        : 'rotateY(180deg)';
            }
        });
    });
}

console.log("Script finished loading");