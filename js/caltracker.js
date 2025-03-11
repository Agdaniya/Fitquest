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
    const caloriesIntakeDisplay = document.querySelector('#calories-burned');

    let stream = null;
    let optionsMenu = null;

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
            
            // Extract total calories
            const calorieMatches = analysisText.match(/(?:total calories:?\s*(\d+))|(?:(\d+)\s*calories?\s*total)/i);
            const totalCalories = calorieMatches ? parseInt(calorieMatches[1] || calorieMatches[2]) : 0;

            results.innerHTML = `
                <div class="analysis-results">
                    <h3>Food Analysis Results</h3>
                    <div class="results-text">
                        ${analysisText.replace(/\n/g, '<br>')}
                    </div>
                    <div class="action-buttons">
                        <button class="action-btn" onclick="document.querySelector('#calories-burned').textContent = ${totalCalories}">
                            Add ${totalCalories} calories to Daily Intake
                        </button>
                        <button class="action-btn" onclick="document.querySelector('.close-btn').click()">
                            Cancel
                        </button>
                    </div>
                </div>
            `;
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