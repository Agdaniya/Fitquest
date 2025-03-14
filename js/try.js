import { initializeApp } from "https://www.gstatic.com/firebasejs/9.6.1/firebase-app.js";
import { getAuth, onAuthStateChanged } from "https://www.gstatic.com/firebasejs/9.6.1/firebase-auth.js";
import { getDatabase, ref, get } from "https://www.gstatic.com/firebasejs/9.6.1/firebase-database.js";
import { getFirestore, doc, getDoc } from "https://www.gstatic.com/firebasejs/9.6.1/firebase-firestore.js";
const getFitnessLevel = async (userId) => {
    if (!userId) {
        console.error("No authenticated user found.");
        return "beginner"; // Default if no user
    }

    const userRef = ref(dbRealtime, `users/${userId}/fitnessLevel`);
    try {
        const snapshot = await get(userRef);
        if (snapshot.exists()) {
            return snapshot.val().toLowerCase(); // Ensure lowercase match
        } else {
            console.log("No fitness level found, defaulting to beginner.");
            return "beginner";
        }
    } catch (error) {
        console.error("Error fetching fitness level:", error);
        return "beginner";
    }
};
