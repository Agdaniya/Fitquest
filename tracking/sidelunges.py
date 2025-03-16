import cv2
import mediapipe as mp
import sys
import time

print("Side Lunges Tracker started")  # Debug print

# Initialize MediaPipe pose solution with higher detection confidence
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

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
# Get the screen resolution
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

# Get the screen resolution
cv2.namedWindow('Side Lunges Tracker', cv2.WINDOW_NORMAL)
screen = cv2.getWindowImageRect('Side Lunges Tracker')
screen_width = screen[2]
screen_height = screen[3]

print(f"Screen resolution: {screen_width}x{screen_height}")  # Debug print

# Set the window to fullscreen
cv2.setWindowProperty('Side Lunges Tracker', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

# Initialize variables to track the state and counts
left_lunge_state = "center"  # Can be "center", "left", "returning_from_left"
right_lunge_state = "center"  # Can be "center", "right", "returning_from_right"
left_count = 0
right_count = 0
total_count = 0

# Set a confidence threshold for pose detection - lower value for more leniency
confidence_threshold = 0.4  # Reduced from 0.6

# Threshold for leg movement detection - lower value for more leniency
leg_distance_threshold = 0.05  # Reduced from 0.1

# Add smoothing for stability
smoothing_window_size = 5
left_distances = [0] * smoothing_window_size
right_distances = [0] * smoothing_window_size

print("Side Lunges Tracker initialized")  # Debug print

# Add a timeout mechanism
start_time = time.time()
timeout_duration = 120  # Increased from 60 seconds timeout

# Cooldown between lunge counts to prevent double counting
cooldown_period = 1.0  # seconds
last_left_count_time = 0
last_right_count_time = 0

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

    # Flip the frame horizontally for a more intuitive mirror view
    frame = cv2.flip(frame, 1)

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
        
        # Since we flipped the frame, we need to swap left and right for display
        # But the detection logic remains the same
        display_left_hip, display_right_hip = right_hip, left_hip
        display_left_knee, display_right_knee = right_knee, left_knee
        display_left_ankle, display_right_ankle = right_ankle, left_ankle
        
        # Check if the relevant landmarks are visible
        legs_visible = True  # Assume visible and check individual points
        
        # Calculate baseline distance between hips (for normalization)
        hip_distance = abs(right_hip.x - left_hip.x)
        if hip_distance < 0.01:  # Avoid division by near-zero
            hip_distance = 0.01
        
        # Left lunge detection (based on horizontal distance between knees)
        raw_left_knee_distance = (left_knee.x - right_knee.x) / hip_distance
        
        # Add to smoothing window and calculate average
        left_distances.pop(0)
        left_distances.append(raw_left_knee_distance)
        left_knee_distance = sum(left_distances) / len(left_distances)
        
        # Debug visualization for left knee position
        left_knee_x = int(display_left_knee.x * frame_width)
        left_knee_y = int(display_left_knee.y * frame_height)
        cv2.circle(frame, (left_knee_x, left_knee_y), 8, (0, 255, 255), -1)
        
        # Right lunge detection
        raw_right_knee_distance = (right_knee.x - left_knee.x) / hip_distance
        
        # Add to smoothing window and calculate average
        right_distances.pop(0)
        right_distances.append(raw_right_knee_distance)  
        right_knee_distance = sum(right_distances) / len(right_distances)
        
        # Debug visualization for right knee position
        right_knee_x = int(display_right_knee.x * frame_width)
        right_knee_y = int(display_right_knee.y * frame_height)
        cv2.circle(frame, (right_knee_x, right_knee_y), 8, (255, 0, 255), -1)
        
        current_time = time.time()
        
        # State machine for left lunge with more lenient conditions
        if left_lunge_state == "center" and left_knee_distance > leg_distance_threshold:
            left_lunge_state = "left"
            print("Left lunge detected")
        elif left_lunge_state == "left" and left_knee_distance <= leg_distance_threshold:
            left_lunge_state = "returning_from_left"
        elif left_lunge_state == "returning_from_left" and abs(left_knee.x - left_hip.x) < 0.05:  # More lenient center check
            # Check cooldown to prevent double counting
            if current_time - last_left_count_time > cooldown_period:
                left_lunge_state = "center"
                left_count += 1
                total_count += 1
                last_left_count_time = current_time
                print(f"Left lunge completed. Count: {left_count}, Total: {total_count}")
                sys.stdout.flush()  # Ensure the output is immediately visible
                start_time = time.time()  # Reset the timeout
        
        # State machine for right lunge with more lenient conditions
        if right_lunge_state == "center" and right_knee_distance > leg_distance_threshold:
            right_lunge_state = "right"
            print("Right lunge detected")
        elif right_lunge_state == "right" and right_knee_distance <= leg_distance_threshold:
            right_lunge_state = "returning_from_right"
        elif right_lunge_state == "returning_from_right" and abs(right_knee.x - right_hip.x) < 0.05:  # More lenient center check
            # Check cooldown to prevent double counting
            if current_time - last_right_count_time > cooldown_period:
                right_lunge_state = "center"
                right_count += 1
                total_count += 1
                last_right_count_time = current_time
                print(f"Right lunge completed. Count: {right_count}, Total: {total_count}")
                sys.stdout.flush()  # Ensure the output is immediately visible
                start_time = time.time()  # Reset the timeout
        
        # Display state information on frame (with smaller text)
        cv2.putText(frame, f"Left state: {left_lunge_state}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
        cv2.putText(frame, f"Right state: {right_lunge_state}", (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
        
        # Display the distances for debugging (with smaller text)
        cv2.putText(frame, f"Left distance: {left_knee_distance:.2f}", (10, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
        cv2.putText(frame, f"Right distance: {right_knee_distance:.2f}", (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
        cv2.putText(frame, f"Threshold: {leg_distance_threshold:.2f}", (10, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
    else:
        print("No pose detected")  # Debug print
    
    # Display the cycle counts on the frame (with smaller text for main counter)
    cv2.putText(frame, f'Side Lunges Count - Left: {left_count} | Right: {right_count} | Total: {total_count}', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA)
    
    # Add "Press 'q' to exit" text (with smaller text)
    cv2.putText(frame, "Press 'q' to exit", (10, screen_height - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)
    
    # Add adjustment keys
    cv2.putText(frame, "Press '+' to increase threshold, '-' to decrease", (10, screen_height - 40), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
        
    # Display the frame
    cv2.imshow('Side Lunges Tracker', frame)

    # Process key presses
    key = cv2.waitKey(1) & 0xFF
    
    # Break the loop on 'q' key press
    if key == ord('q'):
        break
    # Increase threshold
    elif key == ord('+'):
        leg_distance_threshold += 0.01
        print(f"Increased threshold to {leg_distance_threshold:.2f}")
    # Decrease threshold
    elif key == ord('-'):
        leg_distance_threshold = max(0.01, leg_distance_threshold - 0.01)
        print(f"Decreased threshold to {leg_distance_threshold:.2f}")

# Release the capture and close the window
cap.release()
cv2.destroyAllWindows()

print("Side Lunges Tracker ended")  # Debug print