console.log("Script starting execution");

import { initializeApp } from "https://www.gstatic.com/firebasejs/10.13.2/firebase-app.js";
import { getAuth, onAuthStateChanged } from "https://www.gstatic.com/firebasejs/10.13.2/firebase-auth.js";
import { getDatabase, ref, onValue } from "https://www.gstatic.com/firebasejs/10.13.2/firebase-database.js";

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

console.log("Firebase initialized");

document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM fully loaded and parsed');

    onAuthStateChanged(auth, (user) => {
        console.log("Auth state changed");
        if (user) {
            console.log("User is logged in:", user.uid);
            fetchTotalCaloriesBurned(user.uid);
            fetchTotalWorkouts(user.uid); // Moved this to combine with user check
        } else {
            console.log("No user is authenticated");
            window.location.href = 'home.html'; // Redirect to login page
        }
    });
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
    console.log("Element found:", caloriesBurnedDisplay); // Check if the element is found
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

// Fetch total workouts count
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

// Welcome message
document.addEventListener('DOMContentLoaded', (event) => {
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

    welcomeMessage.textContent = `${greeting}!`;

    // Water intake tracker
    let waterIntake = 0;
    const waterLevel = document.getElementById('waterLevel');
    const waterAmount = document.getElementById('waterAmount');

    // Check if there's water intake data in localStorage
    if (localStorage.getItem('waterIntake')) {
        waterIntake = parseInt(localStorage.getItem('waterIntake'));
        console.log("Restored water intake from localStorage:", waterIntake);
        updateWaterDisplay();
    }

    console.log("Initial water intake:", waterIntake);

    // Add event listeners for each button
    document.getElementById('hundred').addEventListener('click', () => addWater(100));
    document.getElementById('twofifty').addEventListener('click', () => addWater(250));
    document.getElementById('fivehundred').addEventListener('click', () => addWater(500));
    document.getElementById('reset').addEventListener('click', resetWaterIntake); // Reset button listener

    function addWater(amount) {
        console.log("addWater called with amount:", amount);
        waterIntake += amount;
        console.log("New water intake:", waterIntake);

        // Store updated water intake in localStorage
        localStorage.setItem('waterIntake', waterIntake);

        updateWaterDisplay();
        showNotification(`Great job! You've added ${amount}ml of water.`);
    }

    function updateWaterDisplay() {
        console.log("updateWaterDisplay called");
        const maxHeight = 300; // Height of the water container
        const maxWater = 2000; // Set a max water intake (e.g., 2 liters)
        const height = Math.min((waterIntake / maxWater) * maxHeight, maxHeight);

        console.log("Calculated height:", height);
        waterLevel.style.height = `${height}px`;
        waterAmount.textContent = `${waterIntake} ml`;
        console.log("Updated water amount text:", waterAmount.textContent);

        // Add some fun messages based on water intake
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
        waterIntake = 0; // Reset the water intake to 0
        localStorage.setItem('waterIntake', waterIntake); // Reset in localStorage
        updateWaterDisplay();
        showNotification("Water intake has been reset.");
    }

    function showNotification(message) {
        console.log("showNotification called with message:", message);
        const notificationContainer = document.getElementById('notification-container');
        const notification = document.createElement('div');
        notification.className = 'notification';
        notification.textContent = message;
        notificationContainer.appendChild(notification);
        setTimeout(() => {
            notification.remove();
        }, 3000);
    }

    console.log("Script finished loading");
});

const cards = document.querySelectorAll('.stat-card');
cards.forEach(card => {
    card.addEventListener('click', () => {
        card.querySelector('.card-inner').style.transform = 
            card.querySelector('.card-inner').style.transform === 'rotateY(180deg)' 
                ? 'rotateY(0deg)' 
                : 'rotateY(180deg)';
    });
});
