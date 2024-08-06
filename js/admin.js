import { initializeApp } from "https://www.gstatic.com/firebasejs/10.12.5/firebase-app.js";
        import { getAnalytics } from "https://www.gstatic.com/firebasejs/10.12.5/firebase-analytics.js";
        // TODO: Add SDKs for Firebase products that you want to use
        // https://firebase.google.com/docs/web/setup#available-libraries
      
        // Your web app's Firebase configuration
        // For Firebase JS SDK v7.20.0 and later, measurementId is optional
        const firebaseConfig = {
          apiKey: "AIzaSyDNliFkzGd3x8S39olKVTkMEmFiADILBgo",
          authDomain: "fitquest-39c54.firebaseapp.com",
          projectId: "fitquest-39c54",
          storageBucket: "fitquest-39c54.appspot.com",
          messagingSenderId: "224028445642",
          appId: "1:224028445642:web:412d394f40869d99d79d33",
          measurementId: "G-S89M8RXG52"
        };
      
        // Initialize Firebase
        const app = initializeApp(firebaseConfig);
        const analytics = getAnalytics(app);