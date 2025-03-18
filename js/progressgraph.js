import { initializeApp } from "https://www.gstatic.com/firebasejs/9.6.1/firebase-app.js";
import { getAuth } from "https://www.gstatic.com/firebasejs/9.6.1/firebase-auth.js";
import { getDatabase, ref, get, set } from "https://www.gstatic.com/firebasejs/9.6.1/firebase-database.js";

// Firebase configuration
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

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const database = getDatabase(app);

// Graph configuration
const graphConfig = {
    days: ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'],
    colors: {
        primary: '#4682B4', // Main line color
        background: 'rgba(70, 130, 180, 0.2)', // Area fill color
        grid: '#e0e0e0', // Grid line color
        text: '#333333' // Text color
    }
};

// Chart instance
let progressChart = null;

// Function to initialize the weekly progress graph
function initProgressGraph() {
    // Create container for the progress graph if it doesn't exist
    let graphContainer = document.getElementById('weekly-progress-graph');
    if (!graphContainer) {
        const mainSection = document.querySelector('.main');
        
        // Create section for the graph
        const graphSection = document.createElement('div');
        graphSection.className = 'section progress-graph';
        graphSection.innerHTML = `
            <h2>Weekly Workout Progress</h2>
            <div class="graph-container">
                <canvas id="weekly-progress-graph"></canvas>
            </div>
            <div class="graph-info">
                <p>Progress resets every Sunday</p>
                <p id="weekly-average">Weekly Average: 0%</p>
            </div>
        `;
        
        // Insert before the motivational quote section or at the end of main
        const motivationalSection = document.querySelector('.section-motivational-quote');
        if (motivationalSection) {
            mainSection.insertBefore(graphSection, motivationalSection);
        } else {
            mainSection.appendChild(graphSection);
        }
        
        graphContainer = document.getElementById('weekly-progress-graph');
    }
    
    // Load weekly progress data when user is authenticated
    auth.onAuthStateChanged(user => {
        if (user) {
            loadWeeklyProgressData(user.uid);
        }
    });
}

// Function to get the date string for a specific day
function getDateString(date) {
    return date.toISOString().split('T')[0];
}

// Function to get the current week's dates
function getCurrentWeekDates() {
    const today = new Date();
    const dayOfWeek = today.getDay(); // 0 = Sunday, 1 = Monday, etc.
    const dates = [];
    
    // Get Sunday (start of week) through Saturday
    for (let i = 0; i < 7; i++) {
        const date = new Date(today);
        date.setDate(today.getDate() - dayOfWeek + i);
        dates.push(getDateString(date));
    }
    
    return dates;
}

// Function to load weekly progress data from Firebase
async function loadWeeklyProgressData(userId) {
    try {
        // Get the current week's dates
        const weekDates = getCurrentWeekDates();
        
        // Check if we need to reset weekly data
        await checkWeeklyReset(userId);
        
        // Get progress data for the current week
        const progressRef = ref(database, `users/${userId}/dailyProgress`);
        const snapshot = await get(progressRef);
        
        const progressData = snapshot.exists() ? snapshot.val() : {};
        
        // Prepare data for the graph
        const weeklyData = weekDates.map(date => progressData[date] || 0);
        
        // Calculate weekly average
        const weeklyAverage = weeklyData.reduce((sum, value) => sum + value, 0) / weeklyData.length;
        document.getElementById('weekly-average').textContent = `Weekly Average: ${weeklyAverage.toFixed(1)}%`;
        
        // Create or update the graph
        createOrUpdateGraph(weeklyData);
        
    } catch (error) {
        console.error("Error loading weekly progress data:", error);
    }
}

// Function to check if we need to reset weekly data
async function checkWeeklyReset(userId) {
    try {
        // Get last reset date
        const lastResetRef = ref(database, `users/${userId}/lastWeeklyReset`);
        const snapshot = await get(lastResetRef);
        const lastReset = snapshot.exists() ? snapshot.val() : null;
        
        const today = new Date();
        const currentDate = getDateString(today);
        
        // If today is Sunday and we haven't reset yet this week
        if (today.getDay() === 0 && lastReset !== currentDate) {
            // Update the last reset date
            await set(lastResetRef, currentDate);
            
            // We don't need to clear the data as we're only displaying the current week
            // The graph will automatically show only the current week's data
            console.log("Weekly progress tracking reset for new week");
        }
    } catch (error) {
        console.error("Error checking weekly reset:", error);
    }
}

// Function to create or update the progress graph
function createOrUpdateGraph(weeklyData) {
    const ctx = document.getElementById('weekly-progress-graph').getContext('2d');
    
    // If chart already exists, update it
    if (progressChart) {
        progressChart.data.datasets[0].data = weeklyData;
        progressChart.update();
        return;
    }
    
    // Create new chart
    progressChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: graphConfig.days,
            datasets: [{
                label: 'Workout Completion',
                data: weeklyData,
                backgroundColor: graphConfig.colors.background,
                borderColor: graphConfig.colors.primary,
                borderWidth: 2,
                pointBackgroundColor: graphConfig.colors.primary,
                pointRadius: 4,
                pointHoverRadius: 6,
                fill: true,
                tension: 0.3
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    ticks: {
                        callback: value => `${value}%`
                    },
                    grid: {
                        color: graphConfig.colors.grid
                    }
                },
                x: {
                    grid: {
                        color: graphConfig.colors.grid
                    }
                }
            },
            plugins: {
                tooltip: {
                    callbacks: {
                        label: context => `Progress: ${context.parsed.y.toFixed(1)}%`
                    }
                },
                legend: {
                    display: false
                }
            }
        }
    });
}

// Function to manually refresh the graph
function refreshProgressGraph() {
    const user = auth.currentUser;
    if (user) {
        loadWeeklyProgressData(user.uid);
    }
}

// Initialize the graph when the DOM is loaded
document.addEventListener('DOMContentLoaded', initProgressGraph);

// Listen for workout completion to refresh the graph
document.addEventListener('workout-completed', refreshProgressGraph);

// Export functions for external use
export { initProgressGraph, refreshProgressGraph };