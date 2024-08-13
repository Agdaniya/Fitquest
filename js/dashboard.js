// dashboard.js

// Example data for the chart
const goalProgressData = {
    labels: ['Completed', 'Remaining'],
    datasets: [{
        label: 'Daily Goal Progress',
        data: [60, 40], // Example data
        backgroundColor: ['#4caf50', '#f44336'],
        borderColor: '#fff',
        borderWidth: 1
    }]
};

// Initialize the chart
const ctx = document.getElementById('goal-progress-chart').getContext('2d');
const goalProgressChart = new Chart(ctx, {
    type: 'doughnut',
    data: goalProgressData,
    options: {
        responsive: true,
        plugins: {
            legend: {
                position: 'top',
            },
            tooltip: {
                callbacks: {
                    label: function(context) {
                        let label = context.label || '';
                        if (context.parsed !== null) {
                            label += ': ' + context.parsed + '%';
                        }
                        return label;
                    }
                }
            }
        }
    }
});

// Example function to update total workouts and notifications dynamically
function updateDashboard() {
    // Example dynamic data
    document.getElementById('total-workouts').textContent = '42'; // Replace with real data

    // Example notifications
    const notifications = [
        
    ];
    
    const notificationsList = document.getElementById('notifications-list');
    notificationsList.innerHTML = '';
    notifications.forEach(notification => {
        const li = document.createElement('li');
        li.textContent = notification;
        notificationsList.appendChild(li);
    });
}

// Call the function to update dashboard
updateDashboard();
