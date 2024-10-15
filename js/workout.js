function displayWorkout(workout) {
    const workoutContent = document.getElementById('workoutContent');
    if (!workoutContent) {
        console.warn("Workout content element not found");
        return;
    }

    let html = `<h3>${workout.title}</h3>`;
    if (Array.isArray(workout.exercises)) {
        workout.exercises.forEach(exercise => {
            html += `<div class="exercise-card">
                        <h3>${exercise.name}</h3>
                        <p>${exercise.reps} ${exercise.unit}</p>
                    </div>`;
        });
        workoutContent.innerHTML = html;

        // Store workout title as the goal
        localStorage.setItem('todaysGoal', workout.title);
        
        console.log('Goal set in localStorage:', workout.title);
    } else {
        console.warn("Workout exercises are not in the expected format");
        workoutContent.innerHTML = '<p>Error loading workout. Please try again.</p>';
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const storedWorkout = localStorage.getItem('currentWorkout');
    
    if (storedWorkout) {
        try {
            const workout = JSON.parse(storedWorkout);
            displayWorkout(workout);
        } catch (error) {
            console.error('Error parsing stored workout:', error);
            document.getElementById('workoutContent').innerHTML = '<p>Error loading workout. Please try again.</p>';
        }
    } else {
        document.getElementById('workoutContent').innerHTML = '<p>No workout selected. Please choose a goal.</p>';
        localStorage.removeItem('todaysGoal'); // Clear goal if no workout
        console.log('No workout found, goal cleared');
    }

    console.log('Current todaysGoal in localStorage:', localStorage.getItem('todaysGoal'));
});