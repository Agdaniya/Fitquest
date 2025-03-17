import cv2
import mediapipe as mp
import sys
import time

print("Skipping tracker script started")

# Initialize MediaPipe pose solution
mp_pose = mp.solutions.pose
pose = mp_pose.Pose()

# Initialize MediaPipe drawing utils
mp_drawing = mp.solutions.drawing_utils

# Start video capture
print("Attempting to open camera...")
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

print(f"Camera properties: {frame_width}x{frame_height} @ {fps}fps")

# Try to get a frame
ret, frame = cap.read()
if not ret:
    print("Failed to grab frame from camera")
    cap.release()
    sys.exit(1)

print("Successfully grabbed a frame from camera")

# Create window
cv2.namedWindow('Skipping Tracker', cv2.WINDOW_NORMAL)
screen = cv2.getWindowImageRect('Skipping Tracker')
screen_width = screen[2]
screen_height = screen[3]

print(f"Screen resolution: {screen_width}x{screen_height}")

# Set the window to fullscreen
cv2.setWindowProperty('Skipping Tracker', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

# Initialize variables to track skipping state and counts
feet_up = False
feet_down = True
skipping_count = 0

# Set a confidence threshold for pose detection
confidence_threshold = 0.6

# Variables to track foot positions
prev_left_ankle_y = 0
prev_right_ankle_y = 0
y_threshold = 0.02  # Threshold for significant vertical movement

# Debounce variables to prevent multiple counts for a single skip
last_skip_time = 0
skip_cooldown = 0.3  # Seconds between possible skips

print("Skipping tracker initialized")

# Add a timeout mechanism
start_time = time.time()
timeout_duration = 60  # 60 seconds timeout

while cap.isOpened():
    if time.time() - start_time > timeout_duration:
        print("Timeout reached. Ending tracking.")
        break

    ret, frame = cap.read()
    if not ret:
        print("Failed to capture frame")
        continue

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
        
        # Get the landmarks for ankles, knees, and feet
        landmarks = results.pose_landmarks.landmark
        left_ankle = landmarks[mp_pose.PoseLandmark.LEFT_ANKLE]
        right_ankle = landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE]
        left_knee = landmarks[mp_pose.PoseLandmark.LEFT_KNEE]
        right_knee = landmarks[mp_pose.PoseLandmark.RIGHT_KNEE]
        left_foot_index = landmarks[mp_pose.PoseLandmark.LEFT_FOOT_INDEX]
        right_foot_index = landmarks[mp_pose.PoseLandmark.RIGHT_FOOT_INDEX]
        
        # Check if feet are visible with sufficient confidence
        if (left_ankle.visibility > confidence_threshold and 
            right_ankle.visibility > confidence_threshold and
            left_foot_index.visibility > confidence_threshold and
            right_foot_index.visibility > confidence_threshold):
            
            # Calculate vertical movement
            if prev_left_ankle_y != 0 and prev_right_ankle_y != 0:
                left_moved_up = left_ankle.y < prev_left_ankle_y - y_threshold
                right_moved_up = right_ankle.y < prev_right_ankle_y - y_threshold
                
                # For skipping, we need to detect a jump (both feet moving up)
                if left_moved_up and right_moved_up and feet_down:
                    feet_up = True
                    feet_down = False
                    print("Feet up detected")
                
                # Then detect landing (both feet moving down)
                left_moved_down = left_ankle.y > prev_left_ankle_y + y_threshold
                right_moved_down = right_ankle.y > prev_right_ankle_y + y_threshold
                
                if left_moved_down and right_moved_down and feet_up:
                    feet_up = False
                    feet_down = True
                    
                    # Check if enough time has passed since the last skip
                    current_time = time.time()
                    if current_time - last_skip_time > skip_cooldown:
                        skipping_count += 1
                        last_skip_time = current_time
                        print(f"Skipping Count: {skipping_count}")
                        sys.stdout.flush()  # Ensure the output is immediately visible
                        start_time = time.time()  # Reset the timeout
            
            # Store current positions for next comparison
            prev_left_ankle_y = left_ankle.y
            prev_right_ankle_y = right_ankle.y
            
            # Draw additional visual indicators for debug
            left_ankle_pos = (int(left_ankle.x * frame_width), int(left_ankle.y * frame_height))
            right_ankle_pos = (int(right_ankle.x * frame_width), int(right_ankle.y * frame_height))
            left_foot_pos = (int(left_foot_index.x * frame_width), int(left_foot_index.y * frame_height))
            right_foot_pos = (int(right_foot_index.x * frame_width), int(right_foot_index.y * frame_height))
            
            # Draw circles at ankle and foot positions
            cv2.circle(frame, left_ankle_pos, 10, (255, 0, 0), -1)
            cv2.circle(frame, right_ankle_pos, 10, (255, 0, 0), -1)
            cv2.circle(frame, left_foot_pos, 10, (0, 0, 255), -1)
            cv2.circle(frame, right_foot_pos, 10, (0, 0, 255), -1)
        else:
            print("Feet not visible with sufficient confidence")
    else:
        print("No pose detected")
    
    # Display the count on the frame
    cv2.putText(frame, f'Skipping Count: {skipping_count}', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
    
    # Add "Press 'q' to exit" text
    cv2.putText(frame, "Press 'q' to exit", (10, screen_height - 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
    
    # Display the frame
    cv2.imshow('Skipping Tracker', frame)

    # Break the loop on 'q' key press
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release the capture and close the window
cap.release()
cv2.destroyAllWindows()

print("Skipping tracker ended")