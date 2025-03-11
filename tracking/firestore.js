const { initializeApp } = require("firebase/app");
const { getFirestore, setDoc, doc } = require("firebase/firestore");

const firebaseConfig = {
    apiKey: "AIzaSyAOgdbddMw93MExNBz3tceZ8_NrNAl5q40",
    authDomain: "fitquest-9b891.firebaseapp.com",
    projectId: "fitquest-9b891",
    storageBucket: "fitquest-9b891.appspot.com",
    messagingSenderId: "275044631678",
    appId: "1:275044631678:web:7fa9586ba031270baa042f",
    measurementId: "G-6W3V2DH02K"
};

const app = initializeApp(firebaseConfig);
const db = getFirestore(app);

const exercisesData = {
    beginner: {
        strength: [
            { exercise: "Squats", type: "Reps", count: "3x10", rest: "30 sec" },
            { exercise: "Wall Push-ups", type: "Reps", count: "3x10", rest: "30 sec" },
            { exercise: "Glute Bridges", type: "Reps", count: "3x12", rest: "30 sec" }
        ],
        cardio: [
            { exercise: "March in Place", type: "Time", count: "2 min", rest: "20 sec" },
            { exercise: "Jumping Jacks", type: "Time", count: "3x30 sec", rest: "20 sec" }
        ],
        flexibility: [
            { exercise: "Forward Fold Stretch", type: "Hold", count: "20 sec", rest: "-" },
            { exercise: "Cat-Cow Stretch", type: "Hold", count: "20 sec", rest: "-" }
        ]
    },
    intermediate: {
        strength: [
            { exercise: "Lunges", type: "Reps", count: "3x12", rest: "30 sec" },
            { exercise: "Push-ups", type: "Reps", count: "3x10", rest: "30 sec" },
            { exercise: "Deadlifts (light)", type: "Reps", count: "3x10", rest: "30 sec" }
        ],
        cardio: [
            { exercise: "Running", type: "Time", count: "3 min", rest: "30 sec" },
            { exercise: "Burpees", type: "Time", count: "3x30 sec", rest: "30 sec" }
        ],
        flexibility: [
            { exercise: "Seated Forward Fold", type: "Hold", count: "25 sec", rest: "-" },
            { exercise: "Standing Hamstring Stretch", type: "Hold", count: "25 sec", rest: "-" }
        ]
    },
    advanced: {
        strength: [
            { exercise: "Deadlifts", type: "Reps", count: "4x8", rest: "45 sec" },
            { exercise: "Bench Press", type: "Reps", count: "4x8", rest: "45 sec" },
            { exercise: "Pull-ups", type: "Reps", count: "3x8", rest: "45 sec" }
        ],
        cardio: [
            { exercise: "Sprints", type: "Time", count: "3x30 sec", rest: "40 sec" },
            { exercise: "Jump Rope", type: "Time", count: "3 min", rest: "30 sec" }
        ],
        flexibility: [
            { exercise: "Pigeon Pose", type: "Hold", count: "30 sec", rest: "-" },
            { exercise: "Butterfly Stretch", type: "Hold", count: "30 sec", rest: "-" }
        ]
    }
};

// Function to add exercises for each category
async function addExercises() {
    for (const level in exercisesData) {
        const exercisesRef = doc(db, "exercises", level);
        await setDoc(exercisesRef, exercisesData[level]);
        console.log(`${level} exercises added!`);
    }
}

addExercises();
