function displayWorkout(workout) {
    const workoutContent = document.getElementById('workoutContent');
    let html = `<h3>${workout.title}</h3>`;
    workout.exercises.forEach(exercise => {
        html += `<div class="exercise-card">
                    <h3>${exercise.name}</h3>
                    <p>${exercise.reps} ${exercise.unit}</p>
                </div>`;
    });
    workoutContent.innerHTML = html;
}

document.addEventListener('DOMContentLoaded', () => {
    const storedWorkout = localStorage.getItem('currentWorkout');
    
    if (storedWorkout) {
        const workout = JSON.parse(storedWorkout);
        displayWorkout(workout);
    } else {
        document.getElementById('workoutContent').innerHTML = '<p>No workout selected. Please choose a goal.</p>';
    }
});