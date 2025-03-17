import cv2
import mediapipe as mp
import sys
import time

print("Standing Leg Raises Tracker started")  # Debug print

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
cv2.namedWindow('Standing Leg Raises Tracker', cv2.WINDOW_NORMAL)
screen = cv2.getWindowImageRect('Standing Leg Raises Tracker')
screen_width = screen[2]
screen_height = screen[3]

print(f"Screen resolution: {screen_width}x{screen_height}")  # Debug print

# Set the window to fullscreen
cv2.setWindowProperty('Standing Leg Raises Tracker', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

# Initialize variables to track the state and counts
left_leg_up = False
left_leg_down = True
right_leg_up = False
right_leg_down = True
left_count = 0
right_count = 0
total_count = 0

# Set a confidence threshold for pose detection
confidence_threshold = 0.5  # Slightly lower threshold for better detection

# Track which leg is currently being raised
current_leg = "none"  # "left", "right", or "none"

# For debugging - optional
debug_mode = True

# Store the baseline position of ankles when in standing position
left_ankle_baseline_y = None
right_ankle_baseline_y = None
calibration_frames = 0
calibration_complete = False
calibration_needed = 30  # Number of frames to use for calibration

print("Standing Leg Raises Tracker initialized")  # Debug print

# Add a timeout mechanism
start_time = time.time()
timeout_duration = 120  # 120 seconds timeout

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
        
        # Get the landmarks for hips, knees, and ankles
        landmarks = results.pose_landmarks.landmark
        left_hip = landmarks[mp_pose.PoseLandmark.LEFT_HIP]
        right_hip = landmarks[mp_pose.PoseLandmark.RIGHT_HIP]
        left_knee = landmarks[mp_pose.PoseLandmark.LEFT_KNEE]
        right_knee = landmarks[mp_pose.PoseLandmark.RIGHT_KNEE]
        left_ankle = landmarks[mp_pose.PoseLandmark.LEFT_ANKLE]
        right_ankle = landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE]
        
        # Check if legs are visible with sufficient confidence
        left_leg_visible = (left_hip.visibility > confidence_threshold and 
                           left_knee.visibility > confidence_threshold and 
                           left_ankle.visibility > confidence_threshold)
        
        right_leg_visible = (right_hip.visibility > confidence_threshold and 
                            right_knee.visibility > confidence_threshold and 
                            right_ankle.visibility > confidence_threshold)
        
        # Calibration phase - establish baseline position
        if not calibration_complete and left_leg_visible and right_leg_visible:
            if left_ankle_baseline_y is None and right_ankle_baseline_y is None:
                left_ankle_baseline_y = left_ankle.y
                right_ankle_baseline_y = right_ankle.y
                calibration_frames = 1
            else:
                # Average the positions over multiple frames
                left_ankle_baseline_y = (left_ankle_baseline_y * calibration_frames + left_ankle.y) / (calibration_frames + 1)
                right_ankle_baseline_y = (right_ankle_baseline_y * calibration_frames + right_ankle.y) / (calibration_frames + 1)
                calibration_frames += 1
                
                if calibration_frames >= calibration_needed:
                    calibration_complete = True
                    print("Calibration complete")
                    # Print calibration values for debugging
                    print(f"Left ankle baseline: {left_ankle_baseline_y}")
                    print(f"Right ankle baseline: {right_ankle_baseline_y}")
        
        # Detection phase
        if calibration_complete and left_leg_visible and right_leg_visible:
            # Calculate the difference in ankle position from baseline
            left_ankle_diff = left_ankle_baseline_y - left_ankle.y
            right_ankle_diff = right_ankle_baseline_y - right_ankle.y
            
            # Define thresholds for leg raise detection
            # Use a lower threshold since we're not enforcing knee straightness
            left_leg_raise_threshold = 0.08  # Adjust based on testing
            right_leg_raise_threshold = 0.08  # Adjust based on testing
            
            # Check if left leg is raised
            left_leg_raised = left_ankle_diff > left_leg_raise_threshold
            
            # Check if right leg is raised
            right_leg_raised = right_ankle_diff > right_leg_raise_threshold
            
            # Debug information
            if debug_mode:
                # Draw baseline and current position indicators
                left_ankle_x = int(left_ankle.x * frame.shape[1])
                left_ankle_y = int(left_ankle.y * frame.shape[0])
                right_ankle_x = int(right_ankle.x * frame.shape[1])
                right_ankle_y = int(right_ankle.y * frame.shape[0])
                
                # Draw current ankle positions
                cv2.circle(frame, (left_ankle_x, left_ankle_y), 8, (0, 255, 255), -1)
                cv2.circle(frame, (right_ankle_x, right_ankle_y), 8, (0, 255, 255), -1)
                
                # Display the ankle height differences
                cv2.putText(frame, f'L Diff: {left_ankle_diff:.3f}', (10, 190), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA)
                cv2.putText(frame, f'R Diff: {right_ankle_diff:.3f}', (10, 220), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA)
                cv2.putText(frame, f'L Thresh: {left_leg_raise_threshold:.3f}', (10, 250), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA)
                cv2.putText(frame, f'R Thresh: {right_leg_raise_threshold:.3f}', (10, 280), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA)
            
            # LEFT LEG RAISE DETECTION
            if left_leg_raised and not right_leg_raised:
                if left_leg_down and current_leg in ["none", "left"]:
                    left_leg_up = True
                    left_leg_down = False
                    current_leg = "left"
                    print("Left leg raised detected")  # Debug print
            elif not left_leg_raised and left_leg_up and current_leg == "left":
                left_leg_up = False
                left_leg_down = True
                left_count += 1
                total_count += 1
                current_leg = "none"
                print(f"Left Leg Raise Count: {left_count}, Total: {total_count}")
                sys.stdout.flush()  # Ensure the output is immediately visible
                start_time = time.time()  # Reset the timeout
            
            # RIGHT LEG RAISE DETECTION
            if right_leg_raised and not left_leg_raised:
                if right_leg_down and current_leg in ["none", "right"]:
                    right_leg_up = True
                    right_leg_down = False
                    current_leg = "right"
                    print("Right leg raised detected")  # Debug print
            elif not right_leg_raised and right_leg_up and current_leg == "right":
                right_leg_up = False
                right_leg_down = True
                right_count += 1
                total_count += 1
                current_leg = "none"
                print(f"Right Leg Raise Count: {right_count}, Total: {total_count}")
                sys.stdout.flush()  # Ensure the output is immediately visible
                start_time = time.time()  # Reset the timeout
        
        else:
            if not calibration_complete:
                cv2.putText(frame, f'Calibrating: {calibration_frames}/{calibration_needed}', (10, 310), 
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
            else:
                print("Legs not fully visible")  # Debug print
        
        # Display the status on the frame
        status_text = ""
        if not calibration_complete:
            status_text = "Calibrating... Stand still"
        elif current_leg == "left":
            status_text = "Left Leg Raising"
        elif current_leg == "right":
            status_text = "Right Leg Raising"
        else:
            status_text = "Standing"
        
        cv2.putText(frame, f'Status: {status_text}', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(frame, f'Left Leg Raises: {left_count}', (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(frame, f'Right Leg Raises: {right_count}', (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(frame, f'Total Raises: {total_count}', (10, 150), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
    else:
        print("No pose detected")  # Debug print
        cv2.putText(frame, "No pose detected", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
    
    # Add "Press 'q' to exit" text
    cv2.putText(frame, "Press 'q' to exit", (10, screen_height - 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
        
    # Display the frame
    cv2.imshow('Standing Leg Raises Tracker', frame)

    # Break the loop on 'q' key press
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release the capture and close the window
cap.release()
cv2.destroyAllWindows()

print("Standing Leg Raises Tracker ended")  # Debug print