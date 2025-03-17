import cv2
import mediapipe as mp
import sys
import time

print("Glute Bridge Tracker started")  # Debug print

# Initialize MediaPipe pose solution
mp_pose = mp.solutions.pose
pose = mp_pose.Pose()

# Initialize MediaPipe drawing utils
mp_drawing = mp.solutions.drawing_utils

# Start video capture (0 for webcam, or provide a video file path)
print("Attempting to open camera...")  # Debug print
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Error: Could not open camera.")
    print("Available cameras:")
    for i in range(10):  # Check first 10 camera indices
        temp_cap = cv2.VideoCapture(i)
        if temp_cap.isOpened():
            print(f"Camera index {i} is available")
            temp_cap.release()
    sys.exit(1)

print("Camera opened successfully")
# Get the camera properties
frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
fps = int(cap.get(cv2.CAP_PROP_FPS))

print(f"Camera properties: {frame_width}x{frame_height} @ {fps}fps")  # Debug print

# Try to get a frame
ret, frame = cap.read()
if not ret:
    print("Failed to grab frame from camera")
    cap.release()
    sys.exit(1)

print("Successfully grabbed a frame from camera")  # Debug print

# Set up display window
cv2.namedWindow('Glute Bridge Tracker', cv2.WINDOW_NORMAL)
screen = cv2.getWindowImageRect('Glute Bridge Tracker')
screen_width = screen[2]
screen_height = screen[3]

print(f"Screen resolution: {screen_width}x{screen_height}")  # Debug print

# Set the window to fullscreen
cv2.setWindowProperty('Glute Bridge Tracker', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

# Initialize variables to track the state and counts
bridge_up = False
rep_count = 0

# Set a confidence threshold for pose detection
confidence_threshold = 0.5  # Reduced threshold for better detection

print("Glute Bridge Tracker initialized")  # Debug print

# Add a timeout mechanism
start_time = time.time()
timeout_duration = 120  # Increased timeout to 2 minutes

while cap.isOpened():
    if time.time() - start_time > timeout_duration:
        print("Timeout reached. Ending tracking.")
        break

    ret, frame = cap.read()
    if not ret:
        print("Failed to capture frame")  # Debug print
        continue  # Try to capture the next frame instead of breaking

    # Resize the frame to fit the screen
    frame = cv2.resize(frame, (screen_width, screen_height))

    # Convert the frame to RGB
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Process the frame to detect the pose
    results = pose.process(rgb_frame)

    # Draw the pose annotation on the frame
    if results.pose_landmarks:
        mp_drawing.draw_landmarks(
            frame, results.pose_landmarks, mp_pose.POSE_CONNECTIONS,
            mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=2),
            mp_drawing.DrawingSpec(color=(0, 0, 255), thickness=2, circle_radius=2)
        )
        
        # Get the landmarks for hips and shoulders
        landmarks = results.pose_landmarks.landmark
        left_hip = landmarks[mp_pose.PoseLandmark.LEFT_HIP]
        right_hip = landmarks[mp_pose.PoseLandmark.RIGHT_HIP]
        left_shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER]
        right_shoulder = landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER]
        
        # Check if key body parts are visible with sufficient confidence
        body_visible = (
            left_hip.visibility > confidence_threshold and 
            right_hip.visibility > confidence_threshold and 
            left_shoulder.visibility > confidence_threshold and 
            right_shoulder.visibility > confidence_threshold
        )
        
        if body_visible:
            # Calculate the vertical displacement of the hips
            hip_average_y = (left_hip.y + right_hip.y) / 2
            shoulder_average_y = (left_shoulder.y + right_shoulder.y) / 2
            
            # Define thresholds for glute bridge detection
            bridge_threshold = 0.15  # Adjusted threshold
            
            # Detect glute bridge movement
            if hip_average_y < shoulder_average_y - bridge_threshold:
                bridge_up = True
            elif bridge_up and hip_average_y >= shoulder_average_y - bridge_threshold:
                rep_count += 1
                bridge_up = False
                print(f"Glute Bridge Count: {rep_count}")
                sys.stdout.flush()
                start_time = time.time()
        
        # Display the status on the frame
        cv2.putText(frame, f'Glute Bridges: {rep_count}', (10, 70), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
    else:
        print("No pose detected")  # Debug print
        cv2.putText(frame, "No pose detected", (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)
    
    # Add "Press 'q' to exit" text
    cv2.putText(frame, "Press 'q' to exit", (10, screen_height - 30), 
                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
        
    # Display the frame
    cv2.imshow('Glute Bridge Tracker', frame)

    # Break the loop on 'q' key press
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release the capture and close the window
cap.release()
cv2.destroyAllWindows()

print("Glute Bridge Tracker ended")  # Debug print
