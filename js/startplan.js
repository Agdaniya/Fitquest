import { initializeApp } from "https://www.gstatic.com/firebasejs/9.6.1/firebase-app.js";
import { getAuth, onAuthStateChanged } from "https://www.gstatic.com/firebasejs/9.6.1/firebase-auth.js";
import { getDatabase, ref, get } from "https://www.gstatic.com/firebasejs/9.6.1/firebase-database.js";
import { getFirestore, doc, getDoc } from "https://www.gstatic.com/firebasejs/9.6.1/firebase-firestore.js";

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
 const app = initializeApp(firebaseConfig);
 const auth = getAuth(app);
 const dbRealtime = getDatabase(app);
 const dbFirestore = getFirestore(app);
 onAuthStateChanged(auth, (user) => {
    if (user) {
        console.log("User authenticated:", user.uid);
        getExercises(user.uid);
    } else {
        console.log("No user signed in.");
    }
});

 
const getFitnessLevel = async (userId) => {
    const userRef = ref(dbRealtime, `users/${userId}/fitnessLevel`);
    try {
        const snapshot = await get(userRef);
        return snapshot.exists() ? snapshot.val().toLowerCase() : "beginner";
    } catch (error) {
        console.error("Error fetching fitness level:", error);
        return "beginner";
    }
};
const getExercises = async (userId) => {
    const fitnessLevel = await getFitnessLevel(userId);
    const exercisesRef = doc(dbFirestore, "exercises", fitnessLevel);

    try {
        const docSnap = await getDoc(exercisesRef);
        if (docSnap.exists()) {
            const exercises = docSnap.data();
            Object.keys(exercises).forEach(type => {
                exercises[type].forEach(exercise => {
                    console.log(exercise.exercise); // Logs only the names
                });
            });
        } else {
            console.log("No exercises found.");
        }
    } catch (error) {
        console.error("Error fetching exercises:", error);
    }
};

// Fetch exercises when the user is authenticated
onAuthStateChanged(auth, (user) => {
    if (user) {
        getExercises(user.uid);
    } else {
        console.log("No user signed in.");
    }
});
document.getElementById("start-plan").addEventListener("click", async () => {
    console.log("Start Plan clicked");
    
    const user = auth.currentUser;
    if (!user) {
        console.log("No user signed in.");
        return;
    }

    const fitnessLevel = await getFitnessLevel(user.uid);
    const exercisesRef = doc(dbFirestore, "exercises", fitnessLevel);

    try {
        const docSnap = await getDoc(exercisesRef);
        if (docSnap.exists()) {
            const exercises = docSnap.data();
            startWorkoutSession(exercises);
        } else {
            console.log("No exercises found.");
        }
    } catch (error) {
        console.error("Error fetching exercises:", error);
    }
});
const startWorkoutSession = (exercises) => {
    console.log("Workout session started");

    // Start the camera (assuming Python backend at localhost:5000)
    fetch("http://localhost:5001/start-camera", { method: "POST" })
        .then(() => {
            console.log("Camera started");
            beginExercise(exercises);
        })
        .catch(err => console.error("Error starting camera:", err));
};
const beginExercise = (exercises) => {
    Object.keys(exercises).forEach(type => {
        exercises[type].forEach(exercise => {
            console.log(`Starting: ${exercise.exercise} (${exercise.type})`);

            fetch("http://localhost:5001/start-exercise", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ name: exercise.exercise, type: exercise.type, details: exercise })
            })
            .then(() => console.log(`${exercise.exercise} tracking started`))
            .catch(err => console.error(`Error tracking ${exercise.exercise}:`, err));
        });
    });
};
