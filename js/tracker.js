// Import Firebase modules
import { initializeApp } from "https://www.gstatic.com/firebasejs/10.13.2/firebase-app.js";
import { getAuth } from "https://www.gstatic.com/firebasejs/10.13.2/firebase-auth.js";
import { getDatabase, ref, set, get } from "https://www.gstatic.com/firebasejs/10.13.2/firebase-database.js";

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

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const database = getDatabase(app);

document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM fully loaded and parsed');

    const API_BASE_URL = 'http://localhost:5000';

    const startButton = document.getElementById('start-jumping-jacks');
    const resetButton = document.getElementById('reset-jumping-jacks');
    const countDisplay = document.getElementById('jumping-jack-count');
    const totalCountDisplay = document.getElementById('total-jumping-jack-count');

    if (!startButton || !resetButton || !countDisplay || !totalCountDisplay) {
        console.error('One or more required elements not found');
        return;
    }

    let previousCount = 0;
    let totalCount = 0;
    let currentUser = null;
    let isTracking = false;

    auth.onAuthStateChanged(user => {
        if (user) {
            currentUser = user;
            console.log('User logged in, fetching initial count');
            resetLocalCounters();
            fetchInitialCount();
        } else {
            console.log('No user logged in');
            currentUser = null;
            resetLocalCounters();
            updateDisplays(0);
        }
    });

    function resetLocalCounters() {
        previousCount = 0;
        totalCount = 0;
        isTracking = false;
        startButton.disabled = false;
        startButton.textContent = 'Start Tracking';
    }

    function fetchInitialCount() {
        const userExerciseRef = ref(database, `users/${currentUser.uid}/exercises/jumping-jacks`);
        get(userExerciseRef).then((snapshot) => {
            if (snapshot.exists()) {
                const data = snapshot.val();
                totalCount = data.count || 0;
                previousCount = totalCount;
                updateDisplays(totalCount);
                console.log('Initial count loaded:', totalCount);
            } else {
                console.log('No existing count found for user');
                totalCount = 0;
                previousCount = 0;
                updateDisplays(0);
            }
        }).catch((error) => {
            console.error('Error fetching initial count:', error);
        });
    }

    function updateDisplays(count) {
        countDisplay.textContent = count;
        totalCountDisplay.textContent = `Total: ${count}`;
    }

    function updateTotalCount(newCount) {
        if (!currentUser || !isTracking) {
            console.log('No user logged in or not tracking, skipping count update');
            return;
        }

        const difference = newCount - previousCount;
        if (difference > 0) {
            totalCount += difference;
            updateDisplays(totalCount);
            console.log(`Total count updated: ${totalCount}`);
            updateFirebaseCount('jumping-jacks', totalCount);
        }
        previousCount = newCount;
    }

    startButton.addEventListener('click', function() {
        if (!currentUser) {
            showNotification('Please log in to track your exercises', 'warning');
            return;
        }

        console.log('Start button clicked');
        fetch(`${API_BASE_URL}/track/start-jumping-jacks`, { 
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
        })
        .then(response => {
            console.log('Response status:', response.status);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Data received:', data);
            if (data.status === 'started') {
                this.disabled = true;
                this.textContent = 'Tracking...';
                isTracking = true;
                updateJumpingJackCount();
            } else if (data.status === 'already_running') {
                showNotification('Tracking is already in progress!', 'warning');
                isTracking = true;
                updateJumpingJackCount();
            } else {
                throw new Error('Unexpected response status');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showNotification('Failed to start tracking. Please try again.', 'error');
        });
    });

    resetButton.addEventListener('click', function() {
        if (!currentUser) {
            showNotification('Please log in to reset your count', 'warning');
            return;
        }

        console.log('Reset button clicked');
        fetch(`${API_BASE_URL}/track/reset-jumping-jacks`, { 
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
        })
        .then(response => {
            console.log('Response status:', response.status);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Data received:', data);
            if (data.status === 'reset') {
                resetLocalCounters();
                updateDisplays(0);
                showNotification('Jumping Jack count has been reset!', 'success');
                updateFirebaseCount('jumping-jacks', 0);
            } else {
                throw new Error('Unexpected response status');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showNotification('Failed to reset count. Please try again.', 'error');
        });
    });

    function updateJumpingJackCount() {
        if (!isTracking) {
            console.log('Tracking stopped');
            return;
        }

        console.log('Updating jumping jack count');
        fetch(`${API_BASE_URL}/track/get-jumping-jack-count`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                console.log('Count data received:', data);
                updateTotalCount(data.count);
                if (data.status === 'running' && isTracking) {
                    setTimeout(updateJumpingJackCount, 1000);
                } else {
                    isTracking = false;
                    startButton.disabled = false;
                    startButton.textContent = 'Start Tracking';
                    showNotification('Jumping Jack tracking completed!', 'success');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                isTracking = false;
                startButton.disabled = false;
                startButton.textContent = 'Start Tracking';
                showNotification('Error while tracking. Please try again.', 'error');
            });
    }

    function showNotification(message, type = 'info') {
        console.log(`Notification: ${message} (${type})`);
        const notificationContainer = document.getElementById('notification-container');
        if (!notificationContainer) {
            console.error('Notification container not found');
            return;
        }
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        notificationContainer.appendChild(notification);
        setTimeout(() => {
            notification.classList.add('fade-out');
            setTimeout(() => {
                notification.remove();
            }, 300);
        }, 5000);
    }

    function updateFirebaseCount(exerciseType, count) {
        if (!currentUser) {
            console.log('No user logged in, skipping Firebase update');
            return;
        }

        set(ref(database, `users/${currentUser.uid}/exercises/${exerciseType}`), {
            count: count,
            lastUpdated: Date.now()
        }).then(() => {
            console.log('Firebase updated successfully');
        }).catch(error => {
            console.error('Error updating Firebase:', error);
        });
    }
});