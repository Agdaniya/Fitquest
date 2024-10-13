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

    function updateTotalCount(newCount) {
        const difference = newCount - previousCount;
        if (difference > 0) {
            totalCount += difference;
            totalCountDisplay.textContent = `Total: ${totalCount}`;
            console.log(`Total count updated: ${totalCount}`);
            updateFirebaseCount('jumping-jacks', totalCount);
        }
        previousCount = newCount;
    }

    function updateCount(count) {
        countDisplay.textContent = count;
        console.log(`Count updated: ${count}`);
        updateTotalCount(count);
    }

    startButton.addEventListener('click', function() {
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
                updateJumpingJackCount();
            } else if (data.status === 'already_running') {
                showNotification('Tracking is already in progress!', 'warning');
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
                previousCount = 0;
                totalCount = 0;
                updateCount(0);
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
                updateCount(data.count);
                if (data.status === 'running') {
                    setTimeout(updateJumpingJackCount, 1000);
                } else {
                    startButton.disabled = false;
                    startButton.textContent = 'Start Tracking';
                    showNotification('Jumping Jack tracking completed!', 'success');
                }
            })
            .catch(error => {
                console.error('Error:', error);
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
        const user = auth.currentUser;
        if (user) {
            set(ref(database, `users/${user.uid}/exercises/${exerciseType}`), {
                count: count,
                lastUpdated: Date.now()
            }).catch(error => {
                console.error('Error updating Firebase:', error);
            });
        } else {
            console.log('No user logged in, skipping Firebase update');
        }
    }


    auth.onAuthStateChanged(user => {
        if (user) {
            console.log('User logged in, fetching initial count');
            const userExerciseRef = ref(database, `users/${user.uid}/exercises/jumping-jacks`);
            onValue(userExerciseRef, (snapshot) => {
                if (snapshot.exists()) {
                    const data = snapshot.val();
                    totalCount = data.count;
                    totalCountDisplay.textContent = `Total: ${totalCount}`;
                    console.log('Initial count loaded:', totalCount);
                } else {
                    console.log('No existing count found for user');
                    totalCount = 0;
                    totalCountDisplay.textContent = `Total: 0`;
                }
            });
        } else {
            console.log('No user logged in');
        }
    });

    // Initial count update
    updateJumpingJackCount();
});