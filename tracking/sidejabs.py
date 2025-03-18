import cv2
import mediapipe as mp
import sys
import time

print("Side to Side Jabs Tracker started")  # Debug print

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
cv2.namedWindow('Side to Side Jabs Tracker', cv2.WINDOW_NORMAL)
screen = cv2.getWindowImageRect('Side to Side Jabs Tracker')
screen_width = screen[2]
screen_height = screen[3]

print(f"Screen resolution: {screen_width}x{screen_height}")  # Debug print

# Set the window to fullscreen
cv2.setWindowProperty('Side to Side Jabs Tracker', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

# Initialize variables to track the state and counts
left_jab_extended = False
left_jab_retracted = True
right_jab_extended = False
right_jab_retracted = True
left_jab_count = 0
right_jab_count = 0
total_jab_count = 0

# Set a confidence threshold for pose detection
confidence_threshold = 0.6  # Adjust this as needed

# Track which arm is currently jabbing
current_jab = "none"  # "left", "right", or "none"

print("Side to Side Jabs Tracker initialized")  # Debug print

# Add a timeout mechanism
start_time = time.time()
timeout_duration = 60  # 60 seconds timeout

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
        
        # Get the landmarks for shoulders, elbows, and wrists
        landmarks = results.pose_landmarks.landmark
        left_shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER]
        right_shoulder = landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER]
        left_elbow = landmarks[mp_pose.PoseLandmark.LEFT_ELBOW]
        right_elbow = landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW]
        left_wrist = landmarks[mp_pose.PoseLandmark.LEFT_WRIST]
        right_wrist = landmarks[mp_pose.PoseLandmark.RIGHT_WRIST]
        
        # Check if arms are visible with sufficient confidence
        left_arm_visible = (left_shoulder.visibility > confidence_threshold and 
                           left_elbow.visibility > confidence_threshold and 
                           left_wrist.visibility > confidence_threshold)
        
        right_arm_visible = (right_shoulder.visibility > confidence_threshold and 
                            right_elbow.visibility > confidence_threshold and 
                            right_wrist.visibility > confidence_threshold)
        
        if left_arm_visible and right_arm_visible:
            # Calculate the horizontal distance between shoulder and wrist for each arm
            # For side jabs, we care about the horizontal distance (x-coordinate)
            left_shoulder_wrist_distance = left_wrist.x - left_shoulder.x
            right_shoulder_wrist_distance = right_shoulder.x - right_wrist.x
            
            # Define thresholds for jab detection
            # When the arm is extended for a jab, the horizontal distance increases
            left_jab_threshold = 0.2  # Adjust based on testing
            right_jab_threshold = 0.2  # Adjust based on testing
            
            # Check if arms are extended for a jab
            # For left jab, the wrist should be further left than the shoulder
            left_jab = left_shoulder_wrist_distance < -left_jab_threshold
            
            # For right jab, the wrist should be further right than the shoulder
            right_jab = right_shoulder_wrist_distance < -right_jab_threshold
            
            # Check if the arm is somewhat straight during the jab
            left_arm_straight = abs(left_elbow.y - ((left_shoulder.y + left_wrist.y) / 2)) < 0.05
            right_arm_straight = abs(right_elbow.y - ((right_shoulder.y + right_wrist.y) / 2)) < 0.05
            
            # LEFT JAB DETECTION
            if left_jab and left_arm_straight and not right_jab:
                if left_jab_retracted and current_jab in ["none", "left"]:
                    left_jab_extended = True
                    left_jab_retracted = False
                    current_jab = "left"
                    print("Left jab extended detected")  # Debug print
            elif not left_jab and left_jab_extended and current_jab == "left":
                left_jab_extended = False
                left_jab_retracted = True
                left_jab_count += 1
                total_jab_count += 1
                current_jab = "none"
                print(f"Left Jab Count: {left_jab_count}, Total: {total_jab_count}")
                sys.stdout.flush()  # Ensure the output is immediately visible
                start_time = time.time()  # Reset the timeout
            
            # RIGHT JAB DETECTION
            if right_jab and right_arm_straight and not left_jab:
                if right_jab_retracted and current_jab in ["none", "right"]:
                    right_jab_extended = True
                    right_jab_retracted = False
                    current_jab = "right"
                    print("Right jab extended detected")  # Debug print
            elif not right_jab and right_jab_extended and current_jab == "right":
                right_jab_extended = False
                right_jab_retracted = True
                right_jab_count += 1
                total_jab_count += 1
                current_jab = "none"
                print(f"Right Jab Count: {right_jab_count}, Total: {total_jab_count}")
                sys.stdout.flush()  # Ensure the output is immediately visible
                start_time = time.time()  # Reset the timeout
        
        else:
            print("Arms not fully visible")  # Debug print
        
        # Display the status on the frame
        status_text = ""
        if current_jab == "left":
            status_text = "Left Jab"
        elif current_jab == "right":
            status_text = "Right Jab"
        else:
            status_text = "Ready"
        
        cv2.putText(frame, f'Status: {status_text}', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(frame, f'Left Jabs: {left_jab_count}', (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(frame, f'Right Jabs: {right_jab_count}', (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(frame, f'Total Jabs: {total_jab_count}', (10, 150), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
    else:
        print("No pose detected")  # Debug print
    
    # Add "Press 'q' to exit" text
    cv2.putText(frame, "Press 'q' to exit", (10, screen_height - 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
        
    # Display the frame
    cv2.imshow('Side to Side Jabs Tracker', frame)

    # Break the loop on 'q' key press
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release the capture and close the window
cap.release()
cv2.destroyAllWindows()

print("Side to Side Jabs Tracker ended")  # Debug print