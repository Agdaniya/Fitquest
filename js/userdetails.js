import { initializeApp } from "https://www.gstatic.com/firebasejs/10.13.2/firebase-app.js";
import { getAuth } from "https://www.gstatic.com/firebasejs/10.13.2/firebase-auth.js";
import { getDatabase, ref, update } from "https://www.gstatic.com/firebasejs/10.13.2/firebase-database.js";

// Firebase configuration
const firebaseConfig = {
    apiKey: "AIzaSyAOgdbddMw93MExNBz3tceZ8_NrNAl5q40",
    authDomain: "fitquest-9b891.firebaseapp.com",
    projectId: "fitquest-9b891",
    storageBucket: "fitquest-9b891.appspot.com",
    messagingSenderId: "275044631678",
    appId: "1:275044631678:web:7fa9586ba031270baa042f",
    measurementId: "G-6W3V2DH02K"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const database = getDatabase(app);

// Function to calculate BMI
function calculateBMI(weight, height) {
    const heightInMeters = height / 100;
    return Math.round((weight / (heightInMeters * heightInMeters)) * 100) / 100;
}

// Wait for the DOM to be fully loaded
document.addEventListener('DOMContentLoaded', () => {
    const userDetailsForm = document.getElementById('user-details-form');
    const skipBtn = document.getElementById('skip-btn');

    // Form submission handler
    userDetailsForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        // Get current user
        const user = auth.currentUser;
        if (!user) {
            alert('Please log in first');
            window.location.href = '../home.html';
            return;
        }

        // Collect form data
        const age = document.getElementById('age').value;
        const gender = document.getElementById('gender').value;
        const height = parseFloat(document.getElementById('height').value);
        const weight = parseFloat(document.getElementById('weight').value);
        const activityLevel = document.getElementById('activity-level').value;

        // Validate inputs
        if (!age || !gender || !height || !weight || !activityLevel) {
            alert("Please fill in all fields.");
            return;
        }

        if (isNaN(height) || isNaN(weight)) {
            alert("Please enter valid numbers for height and weight.");
            return;
        }

        // Calculate BMI
        const bmi = calculateBMI(weight, height);

        // Prepare user details for database and prediction
        const userDetails = {
            age: age,
            gender: gender,
            height: height,
            weight: weight,
            bmi: bmi,
            activityLevel: activityLevel
        };

        try {
            // Log the user details before sending
            console.log('User Details:', JSON.stringify(userDetails));

            // Call the backend to predict fitness level
            const response = await fetch('http://localhost:5000/predict-fitness-level', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    age: userDetails.age,
                    height: userDetails.height,
                    weight: userDetails.weight,
                    activityLevel: userDetails.activityLevel,
                    gender: userDetails.gender
                })
            });

            // Check if the response is successful
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to predict fitness level');
            }

            const data = await response.json();
            const fitnessLevel = data.fitness_level;

            // Add fitness level to user details
            userDetails.fitnessLevel = fitnessLevel;

            // Update user details in the database
            await update(ref(database, 'users/' + user.uid), userDetails);

            // Redirect to home page
            window.location.href = '../home.html';

        } catch (error) {
            console.error('Error predicting fitness level:', error);
            alert(`Failed to predict fitness level: ${error.message}`);
        }
    });

    // Skip button handler
    skipBtn.addEventListener('click', () => {
        window.location.href = '../home.html';
    });
});