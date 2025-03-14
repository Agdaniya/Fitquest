// 🔥 Your Firebase Config
const firebaseConfig = {
    apiKey: "AIzaSyAOgdbddMw93MExNBz3tceZ8_NrNAl5q40",
    authDomain: "fitquest-9b891.firebaseapp.com",
    projectId: "fitquest-9b891",
    storageBucket: "fitquest-9b891.appspot.com",
    messagingSenderId: "275044631678",
    appId: "1:275044631678:web:7fa9586ba031270baa042f",
    measurementId: "G-6W3V2DH02K"
};

// 🔥 Firestore API URL

const firestoreUrl = `https://firestore.googleapis.com/v1/projects/${firebaseConfig.projectId}/databases/(default)/documents/users/${userId}/exercises`;

document.addEventListener("DOMContentLoaded", () => {
    const startButton = document.getElementById("start-plan");
    const stopButton = document.getElementById("stop-plan");
    const progressBar = document.getElementById("progress-bar");
    const progressText = document.getElementById("progress-text");
    
    let workoutActive = false;
    let progressInterval = null;

    // Add event listeners
    startButton.addEventListener("click", () => {
        if (workoutActive) {
            resumeWorkout();
        } else {
            startWorkout();
        }
    });

    stopButton.addEventListener("click", () => {
        stopWorkout();
    });

    function startWorkout() {
        // First, get the user's fitness level
        getUserFitnessLevel()
            .then(fitnessLevel => {
                // Then fetch exercises based on the fitness level
                fetchExercisesAndStart(fitnessLevel.toLowerCase());
            })
            .catch(error => {
                console.error("Error getting user fitness level:", error);
                alert("Failed to get your fitness level. Please try again.");
            });
    }
    function getUserFitnessLevel() {
        return fetch(`${rtdbUrl}/users/${userId}.json`)
            .then(response => response.json())
            .then(userData => {
                console.log("User data:", userData);
                // Extract fitness level from user data, default to "beginner" if not found
                const fitnessLevel = userData && userData.fitnessLevel ? userData.fitnessLevel : "Beginner";
                console.log("User fitness level:", fitnessLevel);
                return fitnessLevel;
            });
    }

    function fetchExercisesAndStart(fitnessLevel) {
        // Use the user's fitness level to determine which collection to query
        const firestoreUrl = `https://firestore.googleapis.com/v1/projects/${firebaseConfig.projectId}/databases/(default)/documents/exercises/${fitnessLevel}`;
        
        const categories = ['strength', 'cardio', 'flexibility'];
        let allExercises = [];
        
        console.log(`Fetching exercises for fitness level: ${fitnessLevel}`);
        
        // Create an array of promises for fetching each category
        const fetchPromises = categories.map(category => {
            const categoryUrl = `${firestoreUrl}/${category}`;
            console.log(`Fetching exercises from: ${categoryUrl}`);
            
            return fetch(categoryUrl)
                .then(response => response.json())
                .then(data => {
                    if (data.documents) {
                        const exercises = data.documents.map(doc => {
                            const fields = doc.fields;
                            return {
                                name: fields.exercise ? fields.exercise.stringValue : "Unknown Exercise",
                                sets: parseInt(fields.sets ? fields.sets.integerValue : 1),
                                reps: parseInt(fields.reps ? fields.reps.integerValue : 10),
                                rest: parseInt(fields.rest ? fields.rest.integerValue : 20),
                                type: fields.type ? fields.type.stringValue : "Reps",
                                unit: fields.unit ? fields.unit.stringValue : "reps"
                            };
                        });
                        return exercises;
                    }
                    return [];
                })
                .catch(error => {
                    console.error(`Error fetching ${category} exercises:`, error);
                    return []; // Return empty array on error to avoid breaking the Promise.all
                });
        });
        
        // Wait for all fetches to complete
        Promise.all(fetchPromises)
            .then(results => {
                // Flatten the array of arrays into a single array
                results.forEach(categoryExercises => {
                    allExercises = allExercises.concat(categoryExercises);
                });
                
                console.log("All exercises:", allExercises);
                
                if (allExercises.length === 0) {
                    alert("No exercises found for your fitness level!");
                    return;
                }
                
                startExerciseTracking(allExercises);
            })
            .catch(error => {
                console.error("Error fetching exercises:", error);
                alert("Failed to fetch exercises. Please try again.");
            });
    }

    function startExerciseTracking(exercises) {
        fetch("http://localhost:5001/track/start-exercise", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                user_id: userId,
                exercises: exercises
            })
        })
        .then(response => response.json())
        .then(data => {
            console.log("Tracking started:", data);
            if (data.status === "started") {
                workoutActive = true;
                startButton.textContent = "Resume";
                startProgressUpdates();
            } else {
                alert("Failed to start tracking: " + (data.message || "Unknown error"));
            }
        })
        .catch(error => {
            console.error("Error starting tracking:", error);
            alert("Failed to connect to the tracking server. Make sure the server is running.");
        });
    }

    function resumeWorkout() {
        fetch("http://localhost:5001/track/resume", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                user_id: userId
            })
        })
        .then(response => response.json())
        .then(data => {
            console.log("Workout resumed:", data);
            startProgressUpdates();
        })
        .catch(error => {
            console.error("Error resuming workout:", error);
            alert("Failed to resume workout. Please try again.");
        });
    }

    function stopWorkout() {
        fetch("http://localhost:5001/track/stop-exercise", {
            method: "POST",
            headers: { "Content-Type": "application/json" }
        })
        .then(response => response.json())
        .then(data => {
            console.log("Workout stopped:", data);
            stopProgressUpdates();
            workoutActive = false;
            startButton.textContent = "Start Again";
        })
        .catch(error => {
            console.error("Error stopping workout:", error);
        });
    }

    function startProgressUpdates() {
        // Clear existing interval if any
        if (progressInterval) {
            clearInterval(progressInterval);
        }
        
        // Start polling for progress updates
        progressInterval = setInterval(updateProgress, 1000);
    }

    function stopProgressUpdates() {
        if (progressInterval) {
            clearInterval(progressInterval);
            progressInterval = null;
        }
    }

    function updateProgress() {
        fetch("http://localhost:5001/track/progress")
            .then(response => response.json())
            .then(data => {
                console.log("Progress update:", data);
                
                if (data.status === "inactive") {
                    // Workout not active or completed
                    stopProgressUpdates();
                    workoutActive = false;
                    startButton.textContent = "Start Plan";
                    return;
                }
                
                // Update exercise info display
                const exerciseInfo = document.createElement("div");
                exerciseInfo.innerHTML = `
                    <div class="exercise-info">
                        <p>Current Exercise: ${data.current_exercise || "None"}</p>
                        <p>Set: ${data.set || 0}/${data.total_sets || 0}</p>
                        <p>Rep: ${data.rep || 0}/${data.total_reps || 0}</p>
                        <p>State: ${data.exercise_state || "waiting"}</p>
                    </div>
                `;
                
                // Calculate overall progress
                let totalExercises = 1 + (data.remaining_exercises || 0);
                let completedExercisesPct = (totalExercises - (data.remaining_exercises || 0) - 1) / totalExercises;
                let currentExercisePct = data.progress || 0;
                let overallProgress = (completedExercisesPct + (currentExercisePct / totalExercises)) * 100;
                
                // Update progress bar
                const percentage = Math.round(overallProgress);
                progressBar.style.width = percentage + "%";
                progressText.innerText = `Progress: ${percentage}%`;
                
                // Check if workout is complete
                if (data.status === "completed" && data.remaining_exercises === 0) {
                    alert("Workout complete!");
                    stopProgressUpdates();
                    workoutActive = false;
                    startButton.textContent = "Start Again";
                }
            })
            .catch(error => {
                console.error("Error updating progress:", error);
            });
    }
});