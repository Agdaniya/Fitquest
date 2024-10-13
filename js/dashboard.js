import { getAuth } from "https://www.gstatic.com/firebasejs/10.13.2/firebase-auth.js";
import { getDatabase, ref, onValue } from "https://www.gstatic.com/firebasejs/10.13.2/firebase-database.js";

document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM fully loaded and parsed');

    const auth = getAuth();
    const database = getDatabase();
    const API_BASE_URL = 'http://localhost:5000';

    auth.onAuthStateChanged((user) => {
        if (user) {
            // Get the username from localStorage
            const username = localStorage.getItem('username');

            if (username) {
                // Display the username on the dashboard
                document.getElementById('welcomeMessage').textContent = `Welcome, ${username}!`;
            } else {
                console.error("No username found in localStorage");
            }

            // Fetch and display exercise counts
            fetchExerciseCounts(user.uid);
        } else {
            window.location.href = 'home.html'; // Redirect to login if not authenticated
        }
    });

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

    // Fetch total workouts count when dashboard loads
    auth.onAuthStateChanged((user) => {
        if (user) {
            fetchTotalWorkouts(user.uid);
        }
    });
});