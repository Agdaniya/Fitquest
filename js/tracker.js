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

    // Jumping Jacks Elements
    const startJJButton = document.getElementById('start-jumping-jacks');
    const resetJJButton = document.getElementById('reset-jumping-jacks');
    const jjCountDisplay = document.getElementById('jumping-jack-count');
    const totalJJCountDisplay = document.getElementById('total-jumping-jack-count');

    // Arm Raises Elements
    const startARButton = document.getElementById('start-arm-raises');
    const resetARButton = document.getElementById('reset-arm-raises');
    const arCountDisplay = document.getElementById('arm-raise-count');
    const totalARCountDisplay = document.getElementById('total-arm-raise-count');

    if (!startJJButton || !resetJJButton || !jjCountDisplay || !totalJJCountDisplay ||
        !startARButton || !resetARButton || !arCountDisplay || !totalARCountDisplay) {
        console.error('One or more required elements not found');
        return;
    }

    let jjPreviousCount = 0;
    let jjTotalCount = 0;
    let arPreviousCount = 0;
    let arTotalCount = 0;
    let currentUser = null;
    let isJJTracking = false;
    let isARTracking = false;
    let jjUpdateInterval = null;
    let arUpdateInterval = null;

    auth.onAuthStateChanged(user => {
        if (user) {
            currentUser = user;
            console.log('User logged in, fetching initial counts');
            resetLocalCounters();
            fetchInitialCounts();
        } else {
            console.log('No user logged in');
            currentUser = null;
            resetLocalCounters();
            updateDisplays('jumping-jacks', 0);
            updateDisplays('arm-raises', 0);
        }
    });

    function resetLocalCounters() {
        jjPreviousCount = 0;
        jjTotalCount = 0;
        arPreviousCount = 0;
        arTotalCount = 0;
        isJJTracking = false;
        isARTracking = false;
        startJJButton.disabled = false;
        startJJButton.textContent = 'Start Tracking';
        startARButton.disabled = false;
        startARButton.textContent = 'Start Tracking';
    }

    function fetchInitialCounts() {
        fetchInitialCount('jumping-jacks');
        fetchInitialCount('arm-raises');
    }

    function fetchInitialCount(exerciseType) {
        const userExerciseRef = ref(database, `users/${currentUser.uid}/exercises/${exerciseType}`);
        get(userExerciseRef).then((snapshot) => {
            if (snapshot.exists()) {
                const data = snapshot.val();
                if (exerciseType === 'jumping-jacks') {
                    jjTotalCount = data.count || 0;
                    jjPreviousCount = jjTotalCount;
                } else {
                    arTotalCount = data.count || 0;
                    arPreviousCount = arTotalCount;
                }
                updateDisplays(exerciseType, data.count || 0);
                console.log(`Initial ${exerciseType} count loaded:`, data.count || 0);
            } else {
                console.log(`No existing count found for user (${exerciseType})`);
                updateDisplays(exerciseType, 0);
            }
        }).catch((error) => {
            console.error(`Error fetching initial count (${exerciseType}):`, error);
        });
    }

    function updateDisplays(exerciseType, count) {
        if (exerciseType === 'jumping-jacks') {
            jjCountDisplay.textContent = count;
            totalJJCountDisplay.textContent = `Total: ${count}`;
        } else {
            arCountDisplay.textContent = count;
            totalARCountDisplay.textContent = `Total: ${count}`;
        }
    }

    function updateTotalCount(exerciseType, newCount) {
        if (!currentUser || (exerciseType === 'jumping-jacks' && !isJJTracking) || (exerciseType === 'arm-raises' && !isARTracking)) {
            console.log(`No user logged in or not tracking ${exerciseType}, skipping count update`);
            return;
        }

        let difference, totalCount;
        if (exerciseType === 'jumping-jacks') {
            difference = newCount - jjPreviousCount;
            if (difference > 0) {
                jjTotalCount += difference;
                updateDisplays('jumping-jacks', jjTotalCount);
                console.log(`Total jumping jacks count updated: ${jjTotalCount}`);
                updateFirebaseCount('jumping-jacks', jjTotalCount);
            }
            jjPreviousCount = newCount;
        } else {
            difference = newCount - arPreviousCount;
            if (difference > 0) {
                arTotalCount += difference;
                updateDisplays('arm-raises', arTotalCount);
                console.log(`Total arm raises count updated: ${arTotalCount}`);
                updateFirebaseCount('arm-raises', arTotalCount);
            }
            arPreviousCount = newCount;
        }
    }

    startJJButton.addEventListener('click', function() {
        handleStartStop('jumping-jacks');
    });

    startARButton.addEventListener('click', function() {
        handleStartStop('arm-raises');
    });

    function handleStartStop(exerciseType) {
        if (!currentUser) {
            showNotification('Please log in to track your exercises', 'warning');
            return;
        }

        if (exerciseType === 'jumping-jacks') {
            if (isJJTracking) {
                stopTracking('jumping-jacks');
            } else {
                startTracking('jumping-jacks');
            }
        } else {
            if (isARTracking) {
                stopTracking('arm-raises');
            } else {
                startTracking('arm-raises');
            }
        }
    }

    function startTracking(exerciseType) {
        console.log(`Starting ${exerciseType} tracking...`);
        fetch(`${API_BASE_URL}/track/start-${exerciseType === 'jumping-jacks' ? 'jumping-jacks' : 'lateral-arm-raises'}`, { 
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
            if (data.status === 'started' || data.status === 'already_running') {
                if (exerciseType === 'jumping-jacks') {
                    isJJTracking = true;
                    startJJButton.textContent = 'Stop Tracking';
                    updateJumpingJackCount();
                    jjUpdateInterval = setInterval(updateJumpingJackCount, 1000);
                } else {
                    isARTracking = true;
                    startARButton.textContent = 'Stop Tracking';
                    updateArmRaiseCount();
                    arUpdateInterval = setInterval(updateArmRaiseCount, 1000);
                }
            } else {
                throw new Error('Unexpected response status');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showNotification(`Failed to start ${exerciseType} tracking. Please try again.`, 'error');
        });
    }

    function stopTracking(exerciseType) {
        console.log(`Stopping ${exerciseType} tracking...`);
        fetch(`${API_BASE_URL}/track/stop-${exerciseType === 'jumping-jacks' ? 'jumping-jacks' : 'lateral-arm-raises'}`, { 
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
            if (data.status === 'stopped' || data.status === 'not_running') {
                if (exerciseType === 'jumping-jacks') {
                    isJJTracking = false;
                    startJJButton.textContent = 'Start Tracking';
                    clearInterval(jjUpdateInterval);
                } else {
                    isARTracking = false;
                    startARButton.textContent = 'Start Tracking';
                    clearInterval(arUpdateInterval);
                }
                showNotification(`${exerciseType.charAt(0).toUpperCase() + exerciseType.slice(1)} tracking stopped`, 'info');
            } else {
                throw new Error('Unexpected response status');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showNotification(`Failed to stop ${exerciseType} tracking. Please try again.`, 'error');
        });
    }

    resetJJButton.addEventListener('click', function() {
        resetCount('jumping-jacks');
    });

    resetARButton.addEventListener('click', function() {
        resetCount('arm-raises');
    });

    function resetCount(exerciseType) {
        if (!currentUser) {
            showNotification('Please log in to reset your count', 'warning');
            return;
        }

        console.log(`Reset ${exerciseType} button clicked`);
        fetch(`${API_BASE_URL}/track/reset-${exerciseType === 'jumping-jacks' ? 'jumping-jacks' : 'lateral-arm-raises'}`, { 
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
                if (exerciseType === 'jumping-jacks') {
                    jjPreviousCount = 0;
                    jjTotalCount = 0;
                } else {
                    arPreviousCount = 0;
                    arTotalCount = 0;
                }
                updateDisplays(exerciseType, 0);
                showNotification(`${exerciseType.charAt(0).toUpperCase() + exerciseType.slice(1)} count has been reset!`, 'success');
                updateFirebaseCount(exerciseType, 0);
            } else {
                throw new Error('Unexpected response status');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showNotification(`Failed to reset ${exerciseType} count. Please try again.`, 'error');
        });
    }

    function updateJumpingJackCount() {
        updateExerciseCount('jumping-jacks');
    }

    function updateArmRaiseCount() {
        updateExerciseCount('arm-raises');
    }

    function updateExerciseCount(exerciseType) {
        if ((exerciseType === 'jumping-jacks' && !isJJTracking) || (exerciseType === 'arm-raises' && !isARTracking)) {
            console.log(`${exerciseType} tracking stopped`);
            return;
        }

        console.log(`Updating ${exerciseType} count`);
        fetch(`${API_BASE_URL}/track/get-${exerciseType === 'jumping-jacks' ? 'jumping-jack-count' : 'lateral-arm-raise-count'}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                console.log('Count data received:', data);
                updateTotalCount(exerciseType, data.count);
                if (data.status !== 'running') {
                    if (exerciseType === 'jumping-jacks') {
                        isJJTracking = false;
                        startJJButton.textContent = 'Start Tracking';
                        clearInterval(jjUpdateInterval);
                    } else {
                        isARTracking = false;
                        startARButton.textContent = 'Start Tracking';
                        clearInterval(arUpdateInterval);
                    }
                    showNotification(`${exerciseType.charAt(0).toUpperCase() + exerciseType.slice(1)} tracking completed!`, 'success');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                if (exerciseType === 'jumping-jacks') {
                    isJJTracking = false;
                    startJJButton.textContent = 'Start Tracking';
                    clearInterval(jjUpdateInterval);
                } else {
                    isARTracking = false;
                    startARButton.textContent = 'Start Tracking';
                    clearInterval(arUpdateInterval);
                }
                showNotification(`Error while tracking ${exerciseType}. Please try again.`, 'error');
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
            console.log(`Firebase updated successfully for ${exerciseType}`);
        }).catch(error => {
            console.error(`Error updating Firebase for ${exerciseType}:`, error);
        });
    }
});