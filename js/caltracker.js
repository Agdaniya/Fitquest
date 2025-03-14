document.addEventListener('DOMContentLoaded', () => {
    const modal = document.getElementById('imageModal');
    const cameraButton = document.getElementById('cameraButton');
    const closeBtn = document.querySelector('.close-btn');
    const videoElement = document.getElementById('videoElement');
    const canvas = document.getElementById('canvas');
    const imagePreview = document.getElementById('imagePreview');
    const captureBtn = document.getElementById('captureBtn');
    const analyzeBtn = document.getElementById('analyzeBtn');
    const imageUpload = document.getElementById('imageUpload');
    const results = document.getElementById('results');
    const caloriesIntakeDisplay = document.querySelector('#calories-intake');

    let stream = null;
    let optionsMenu = null;
    let totalDailyCalorieIntake = 0

     // Load saved calorie intake from localStorage if available
     if (localStorage.getItem('totalCalorieIntake')) {
        totalDailyCalorieIntake = parseInt(localStorage.getItem('totalCalorieIntake'));
        updateCalorieIntakeDisplay();
    }

    function createOptionsMenu() {
        const menu = document.createElement('div');
        menu.className = 'camera-options-menu';
        menu.innerHTML = `
            <button class="option-btn" id="takePhotoBtn">
                <span class="option-icon">📸</span>
                Take a Photo
            </button>
            <button class="option-btn" id="uploadPhotoBtn">
                <span class="option-icon">📤</span>
                Upload a Photo
            </button>
        `;
        document.body.appendChild(menu);
        return menu;
    }

    // Menu event listeners
    cameraButton.addEventListener('click', (e) => {
        e.stopPropagation();
        if (!optionsMenu) {
            optionsMenu = createOptionsMenu();
        }

        const buttonRect = cameraButton.getBoundingClientRect();
        optionsMenu.style.display = 'flex';
        optionsMenu.style.top = `${buttonRect.bottom + 10}px`;
        optionsMenu.style.right = `${window.innerWidth - buttonRect.right}px`;

        document.getElementById('takePhotoBtn').onclick = () => {
            optionsMenu.style.display = 'none';
            modal.style.display = 'block';
            startCamera();
        };

        document.getElementById('uploadPhotoBtn').onclick = () => {
            optionsMenu.style.display = 'none';
            imageUpload.click();
        };
    });

    async function startCamera() {
        try {
            stream = await navigator.mediaDevices.getUserMedia({ 
                video: { 
                    facingMode: 'environment',
                    width: { ideal: 1280 },
                    height: { ideal: 720 }
                } 
            });
            videoElement.srcObject = stream;
            videoElement.style.display = 'block';
            imagePreview.style.display = 'none';
            canvas.style.display = 'none';
            captureBtn.style.display = 'block';
            analyzeBtn.style.display = 'none';
        } catch (err) {
            console.error('Error accessing camera:', err);
            results.innerHTML = '<p>Unable to access camera. Please ensure camera permissions are granted.</p>';
        }
    }

    function stopCamera() {
        if (stream) {
            stream.getTracks().forEach(track => track.stop());
            videoElement.srcObject = null;
        }
    }

    // Image capture and upload handling
    captureBtn.addEventListener('click', () => {
        if (videoElement.style.display === 'block') {
            canvas.width = videoElement.videoWidth;
            canvas.height = videoElement.videoHeight;
            const ctx = canvas.getContext('2d');
            ctx.drawImage(videoElement, 0, 0);
            
            imagePreview.src = canvas.toDataURL('image/jpeg');
            videoElement.style.display = 'none';
            imagePreview.style.display = 'block';
            analyzeBtn.style.display = 'block';
            captureBtn.textContent = 'Retake';
            stopCamera();
        } else {
            captureBtn.textContent = 'Capture';
            startCamera();
        }
    });

    imageUpload.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = (event) => {
                modal.style.display = 'block';
                imagePreview.src = event.target.result;
                videoElement.style.display = 'none';
                imagePreview.style.display = 'block';
                analyzeBtn.style.display = 'block';
                captureBtn.style.display = 'none';
            };
            reader.readAsDataURL(file);
        }
    });

    // Function to update the calorie intake display
    function updateCalorieIntakeDisplay() {
        if (caloriesIntakeDisplay) {
            caloriesIntakeDisplay.textContent = totalDailyCalorieIntake;
        } else {
            console.error("Calories intake display element not found");
        }
        
        // Save to localStorage for persistence
        localStorage.setItem('totalCalorieIntake', totalDailyCalorieIntake);
    }

     // Function to add calories to the daily total
     function addCaloriesToDaily(calories) {
        totalDailyCalorieIntake += calories;
        updateCalorieIntakeDisplay();
        
        // Show notification
        showNotification(`Added ${calories} calories to your daily intake!`);
        
        // Create a food entry in the history if needed
        addFoodEntryToHistory(calories);
    }

     // Function to add a food entry to history
     function addFoodEntryToHistory(calories) {
        const historyContainer = document.getElementById('food-history');
        if (historyContainer) {
            const entryTime = new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
            const entry = document.createElement('div');
            entry.className = 'food-entry';
            entry.innerHTML = `
                <span class="entry-time">${entryTime}</span>
                <span class="entry-calories">${calories} calories</span>
            `;
            historyContainer.prepend(entry);
        }
    }
    
    // Function to show notification
    function showNotification(message) {
        const notificationContainer = document.getElementById('notification-container');
        if (notificationContainer) {
            const notification = document.createElement('div');
            notification.className = 'notification';
            notification.textContent = message;
            notificationContainer.appendChild(notification);
            setTimeout(() => {
                notification.classList.add('fade-out');
                setTimeout(() => {
                    notification.remove();
                }, 500);
            }, 2500);
        }
    }

    // Image analysis with Gemini API
    analyzeBtn.addEventListener('click', async () => {
        try {
            results.innerHTML = '<p>Analyzing image...</p>';
            
            // Convert image to base64 and remove data URL prefix
            const imageData = imagePreview.src.split(',')[1];

            const requestData = {
                contents: [{
                    parts: [
                        {
                            text: "Analyze the image and provide only the following details:List of detected food items with estimated calories.    Total estimated calories.Strictly provide only the information requested without any additional explanations, disclaimers, or notes."
                        },
                        {
                            inline_data: {
                                mime_type: "image/jpeg",
                                data: imageData
                            }
                        }
                    ]
                }],
                safety_settings: {
                    category: "HARM_CATEGORY_DANGEROUS_CONTENT",
                    threshold: "BLOCK_MEDIUM_AND_ABOVE"
                }
            };

            const GEMINI_API_KEY = 'AIzaSyCrS2PcAvphF2aV9RFTBWvBcqAjiCmLWqg'; // Replace with your actual API key
            const response = await fetch(`https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key=${GEMINI_API_KEY}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(requestData)
            });

            if (!response.ok) {
                throw new Error(`API Error: ${response.status} - ${await response.text()}`);
            }

            const data = await response.json();

            if (!data.candidates || !data.candidates[0] || !data.candidates[0].content) {
                throw new Error('Invalid response from API');
            }

            const analysisText = data.candidates[0].content.parts[0].text;
            
            // Extract total calories - specifically looking for "Total estimated calories" format
const calorieMatches = analysisText.match(/total\s+estimated\s+calories:?\s*(\d+)/i);

// Add logging to help diagnose issues
console.log("Analysis text:", analysisText);
console.log("Calorie matches:", calorieMatches);

let totalCalories = 0;
if (calorieMatches && calorieMatches[1]) {
    totalCalories = parseInt(calorieMatches[1]);
    console.log("Extracted calories:", totalCalories);
} else {
    // Fallback: look for the last occurrence of a number followed by "calories"
    const allCalorieMatches = [...analysisText.matchAll(/(\d+)\s*calories/gi)];
    if (allCalorieMatches.length > 0) {
        // Get the last match, which is likely the total
        const lastMatch = allCalorieMatches[allCalorieMatches.length - 1];
        totalCalories = parseInt(lastMatch[1]);
        console.log("Fallback calories extraction (last match):", totalCalories);
    } else {
        console.warn("Could not extract calorie information from API response");
    }
}

            results.innerHTML = `
                <div class="analysis-results">
                    <h3>Food Analysis Results</h3>
                    <div class="results-text">
                        ${analysisText.replace(/\n/g, '<br>')}
                    </div>
                    <div class="action-buttons">
                        <button class="action-btn" id="addCaloriesBtn">
                            Add ${totalCalories} calories to Daily Intake
                        </button>
                        <button class="action-btn" onclick="document.querySelector('.close-btn').click()">
                            Cancel
                        </button>
                    </div>
                </div>
            `;
            
            // Add event listener to the "Add calories" button
            document.getElementById('addCaloriesBtn').addEventListener('click', () => {
                addCaloriesToDaily(totalCalories);
                setTimeout(() => {
                    modal.style.display = 'none';
                    resetPreview();
                }, 1000);
            });
        } catch (error) {
            console.error('Error analyzing image:', error);
            results.innerHTML = `
                <div class="analysis-results error">
                    <p>Error analyzing image: ${error.message}</p>
                    <p>Please check your API key and try again.</p>
                </div>
            `;
        }
    });

    // Reset calorie intake for a new day
    function resetDailyCalories() {
        // Check if we need to reset based on last saved date
        const today = new Date().toDateString();
        const lastDate = localStorage.getItem('lastCalorieIntakeDate');
        
        if (lastDate !== today) {
            totalDailyCalorieIntake = 0;
            localStorage.setItem('totalCalorieIntake', 0);
            localStorage.setItem('lastCalorieIntakeDate', today);
            updateCalorieIntakeDisplay();
            
            // Clear food history if it exists
            const historyContainer = document.getElementById('food-history');
            if (historyContainer) {
                historyContainer.innerHTML = '';
            }
        }
    }
    
    // Check if we need to reset the daily calories on load
    resetDailyCalories();

    // Cleanup and reset functions
    document.addEventListener('click', (e) => {
        if (optionsMenu && !optionsMenu.contains(e.target) && e.target !== cameraButton) {
            optionsMenu.style.display = 'none';
        }
    });

    closeBtn.addEventListener('click', () => {
        modal.style.display = 'none';
        stopCamera();
        resetPreview();
    });

    function resetPreview() {
        imagePreview.style.display = 'none';
        videoElement.style.display = 'none';
        analyzeBtn.style.display = 'none';
        captureBtn.style.display = 'block';
        captureBtn.textContent = 'Capture';
        results.innerHTML = '';
    }
});