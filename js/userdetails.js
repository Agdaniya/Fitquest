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
    // Convert height to meters
    const heightInMeters = height / 100;
    
    // Calculate BMI
    const bmi = weight / (heightInMeters * heightInMeters);
    
    // Round to two decimal places
    return Math.round(bmi * 100) / 100;
}

// Form submission handler
document.getElementById('user-details-form').addEventListener('submit', (e) => {
    e.preventDefault();
    
    // Get current user
    const user = auth.currentUser;
    if (!user) {
        alert('Please log in first');
        window.location.href = 'home.html';
        return;
    }

    // Collect form data
    const age = document.getElementById('age').value;
    const gender = document.getElementById('gender').value;
    const height = parseFloat(document.getElementById('height').value);
    const weight = parseFloat(document.getElementById('weight').value);
    const activityLevel = document.getElementById('activity-level').value;

    // Calculate BMI
    const bmi = calculateBMI(weight, height);

    // Prepare user details for database
    const userDetails = {
        age: age,
        gender: gender,
        height: height,
        weight: weight,
        bmi: bmi,
        activityLevel: activityLevel
    };

    // Update user details in database
    update(ref(database, 'users/' + user.uid), userDetails)
        .then(() => {
            // Redirect to home.html after successful save
            window.location.href = 'home.html';
        })
        .catch((error) => {
            console.error('Error saving details:', error);
            alert('Failed to save details. Please try again.');
        });
});

// Skip button handler
document.getElementById('skip-btn').addEventListener('click', () => {
    window.location.href = 'home.html';
});