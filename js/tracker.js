document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM fully loaded and parsed');

    const startButton = document.getElementById('start-jumping-jacks');
    const resetButton = document.getElementById('reset-jumping-jacks');
    const countDisplay = document.getElementById('jumping-jack-count');
    const totalCountDisplay = document.getElementById('total-jumping-jack-count');

    const API_BASE_URL = 'http://localhost:5000';

    let previousCount = 0;
    let totalCount = 0;

    function updateTotalCount(newCount) {
        const difference = newCount - previousCount;
        if (difference > 0) {
            totalCount += difference;
            totalCountDisplay.textContent = `Total: ${totalCount}`;
            console.log(`Total count updated: ${totalCount}`);
        }
        previousCount = newCount;
    }

    function updateCount(count) {
        countDisplay.textContent = count;
        console.log(`Count updated: ${count}`);
        updateTotalCount(count);
    }

    if (startButton) {
        console.log('Start button found');
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
    } else {
        console.error('Start button not found');
    }

    if (resetButton) {
        console.log('Reset button found');
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
                return response.json();
            })
            .then(data => {
                console.log('Data received:', data);
                if (data.status === 'reset') {
                    previousCount = 0;
                    totalCount = 0;
                    updateCount(0);
                    showNotification('Jumping Jack count has been reset!', 'success');
                } else {
                    throw new Error('Unexpected response status');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showNotification('Failed to reset count. Please try again.', 'error');
            });
        });
    } else {
        console.error('Reset button not found');
    }

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

    // Initial count update
    updateJumpingJackCount();
});
 

document.addEventListener('DOMContentLoaded', function() {
    const startButtons = document.querySelectorAll('.tracking-button');
    const API_BASE_URL = 'http://localhost:8000'; // Update with your actual API URL
    const userId = auth.currentUser ? auth.currentUser.uid : null;

    let totalWorkouts = 0; // Local variable to track total workouts

    // Fetch initial total workouts count from Firebase
    fetchTotalWorkouts();

    startButtons.forEach(button => {
        button.addEventListener('click', function() {
            console.log('Tracking started for:', this.getAttribute('data-exercise'));
            const exerciseType = this.getAttribute('data-exercise');
            
            fetch(`${API_BASE_URL}/track/start-${exerciseType}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'started') {
                    updateExerciseCount(exerciseType);
                    incrementTotalWorkouts();  // Increment total workouts when a workout starts
                }
            })
            .catch(error => console.error('Error:', error));
        });
    });

    // Function to increment total workouts locally and in Firebase
    function incrementTotalWorkouts() {
        totalWorkouts += 1; // Increment the local total workouts count

        // Update the total workouts count in Firebase (or your database)
        if (userId) {
            fetch(`${API_BASE_URL}/users/${userId}/totalWorkouts`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ totalWorkouts })
            })
            .then(() => {
                console.log('Total workouts updated in Firebase:', totalWorkouts);
                updateTotalWorkoutsDisplay(totalWorkouts);  // Update the dashboard
            })
            .catch(error => console.error('Error updating total workouts in Firebase:', error));
        } else {
            console.log('User not authenticated');
        }
    }

    // Fetch the total workouts from Firebase when the page loads
    function fetchTotalWorkouts() {
        if (userId) {
            fetch(`${API_BASE_URL}/users/${userId}/totalWorkouts`)
            .then(response => response.json())
            .then(data => {
                totalWorkouts = data.totalWorkouts || 0;  // Set the initial total workouts count
                updateTotalWorkoutsDisplay(totalWorkouts);  // Display the initial count on the dashboard
            })
            .catch(error => console.error('Error fetching total workouts:', error));
        }
    }

    // Update the exercise count display for each individual exercise
    function updateExerciseCount(exerciseType) {
        const exerciseCountDisplay = document.getElementById(`${exerciseType}-count`);

        fetch(`${API_BASE_URL}/track/get-${exerciseType}-count`, {
            method: 'GET',
        })
        .then(response => response.json())
        .then(data => {
            if (data.count !== undefined) {
                exerciseCountDisplay.textContent = data.count;
            }
        })
        .catch(error => console.error('Error fetching exercise count:', error));
    }

    // Function to update the total workouts display on the dashboard
    function updateTotalWorkoutsDisplay(totalWorkouts) {
        const totalWorkoutsDisplay = document.getElementById('total-workouts');
        if (totalWorkoutsDisplay) {
            totalWorkoutsDisplay.textContent = totalWorkouts;
        }
    }
});
