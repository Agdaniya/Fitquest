document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM fully loaded and parsed');

    // Jumping Jack Tracker
    const startButton = document.getElementById('start-jumping-jacks');
    const countDisplay = document.getElementById('jumping-jack-count');

    const API_BASE_URL = 'http://localhost:5000';

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
                    updateJumpingJackCount(); // Start updating the count even if already running
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
                countDisplay.textContent = data.count;
                if (data.status === 'running') {
                    setTimeout(updateJumpingJackCount, 1000); // Update every second
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

    // Function to show notifications
    function showNotification(message, type = 'info') {
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

    // You can add other functions here (updateUserName, updateStats, updateWorkoutList, updateDashboard)
});