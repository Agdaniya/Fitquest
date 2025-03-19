// levelCalculator.js
import { initializeApp } from "https://www.gstatic.com/firebasejs/10.13.2/firebase-app.js";
import { getDatabase, ref, get, set, update } from "https://www.gstatic.com/firebasejs/10.13.2/firebase-database.js";

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
const database = getDatabase(app);

// Constants for level calculations
const POINTS_PER_LEVEL = 500;
const POINTS_PER_LOGIN_STREAK_DAY = 10;
const POINTS_PER_PROGRESS_PERCENTAGE = 0.75; // 15 points per 20% (0.75 per 1%)

// Main function to calculate and update user level
export async function calculateAndUpdateUserLevel(userId) {
    try {
        const userRef = ref(database, `users/${userId}`);
        const userSnapshot = await get(userRef);

        if (!userSnapshot.exists()) {
            console.error("User data not found");
            return { level: 1, points: 0 };
        }

        const userData = userSnapshot.val();
        
        // Get login streak
        const loginStreak = userData.loginStreak || 0;
        
        // Calculate points from login streak
        const loginStreakPoints = loginStreak * POINTS_PER_LOGIN_STREAK_DAY;
        
        // Get progress percentages from the last 7 days
        const progressPoints = await calculateProgressPoints(userId);
        
        // Calculate total points
        const totalPoints = loginStreakPoints + progressPoints;
        
        // Calculate level based on points
        const level = Math.floor(totalPoints / POINTS_PER_LEVEL) + 1;
        const pointsToNextLevel = POINTS_PER_LEVEL - (totalPoints % POINTS_PER_LEVEL);
        
        // Update user level in Firebase
        await update(userRef, {
            level: level,
            currentPoints: totalPoints,
            pointsToNextLevel: pointsToNextLevel
        });
        
        return {
            level,
            points: totalPoints,
            pointsToNextLevel,
            loginStreakPoints,
            progressPoints
        };
    } catch (error) {
        console.error("Error calculating user level:", error);
        return { level: 1, points: 0 };
    }
}

// Calculate points from progress percentages
async function calculateProgressPoints(userId) {
    try {
        const progressRef = ref(database, `users/${userId}/dailyProgress`);
        const progressSnapshot = await get(progressRef);
        
        if (!progressSnapshot.exists()) {
            return 0;
        }
        
        const progressData = progressSnapshot.val();
        
        // Get the last 7 days of progress
        const today = new Date();
        let totalProgressPoints = 0;
        
        for (let i = 0; i < 7; i++) {
            const date = new Date(today);
            date.setDate(date.getDate() - i);
            const dateStr = date.toISOString().split('T')[0];
            
            if (progressData[dateStr]) {
                // Calculate points for this day's progress
                // For each 20% progress, award 15 points
                const progressPercentage = progressData[dateStr];
                const pointsForDay = Math.floor(progressPercentage * POINTS_PER_PROGRESS_PERCENTAGE);
                totalProgressPoints += pointsForDay;
            }
        }
        
        return totalProgressPoints;
    } catch (error) {
        console.error("Error calculating progress points:", error);
        return 0;
    }
}

// Function to fetch user level data
export async function getUserLevelData(userId) {
    try {
        const userRef = ref(database, `users/${userId}`);
        const userSnapshot = await get(userRef);
        
        if (!userSnapshot.exists()) {
            return { level: 1, points: 0, pointsToNextLevel: POINTS_PER_LEVEL };
        }
        
        const userData = userSnapshot.val();
        return {
            level: userData.level || 1,
            points: userData.currentPoints || 0,
            pointsToNextLevel: userData.pointsToNextLevel || POINTS_PER_LEVEL
        };
    } catch (error) {
        console.error("Error fetching user level data:", error);
        return { level: 1, points: 0, pointsToNextLevel: POINTS_PER_LEVEL };
    }
}