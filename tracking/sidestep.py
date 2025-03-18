import cv2
import mediapipe as mp
import sys
import time

print("Side Step Tracker started")  # Debug print

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
cv2.namedWindow('Side Step Tracker', cv2.WINDOW_NORMAL)
screen = cv2.getWindowImageRect('Side Step Tracker')
screen_width = screen[2]
screen_height = screen[3]

print(f"Screen resolution: {screen_width}x{screen_height}")  # Debug print

# Set the window to fullscreen
cv2.setWindowProperty('Side Step Tracker', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

# Initialize variables to track side steps
step_count = 0
left_step_count = 0
right_step_count = 0
step_direction = "center"  # "left", "right", or "center"
last_step_direction = "center"

# Variables to track hip position
initial_hip_x = None
current_hip_x = None
hip_movement_threshold = 0.1  # Threshold for significant hip movement

# Set a confidence threshold for pose detection
confidence_threshold = 0.6  # Adjust this as needed

print("Side Step Tracker initialized")  # Debug print

# Add a timeout mechanism
start_time = time.time()
timeout_duration = 60  # 60 seconds timeout

# Variables for step detection
mid_point = None
step_complete = False
in_step = False
step_start_pos = None

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
        
        # Get the landmarks for hips
        landmarks = results.pose_landmarks.landmark
        left_hip = landmarks[mp_pose.PoseLandmark.LEFT_HIP]
        right_hip = landmarks[mp_pose.PoseLandmark.RIGHT_HIP]
        
        # Calculate the midpoint between hips
        hip_midpoint_x = (left_hip.x + right_hip.x) / 2
        
        # Check if hips are visible with sufficient confidence
        hips_visible = (left_hip.visibility > confidence_threshold and 
                        right_hip.visibility > confidence_threshold)
        
        if hips_visible:
            # Initialize the mid-point if not set
            if mid_point is None:
                mid_point = hip_midpoint_x
                print(f"Initial mid-point set to: {mid_point}")  # Debug print
            
            # Calculate the current position relative to the mid-point
            current_position = hip_midpoint_x - mid_point
            
            # Draw a line to show the mid-point
            mid_point_x = int(mid_point * frame.shape[1])
            cv2.line(frame, (mid_point_x, 0), (mid_point_x, frame.shape[0]), (0, 255, 0), 2)
            
            # Step detection logic
            if not in_step:
                # Check if person has moved significantly to start a step
                if abs(current_position) > hip_movement_threshold:
                    in_step = True
                    step_start_pos = current_position
                    step_direction = "right" if current_position > 0 else "left"
                    print(f"Starting step to the {step_direction}")  # Debug print
            else:
                # Check if person has moved back to center or to the opposite side to complete a step
                opposite_direction = current_position * step_start_pos < 0
                returned_to_center = abs(current_position) < hip_movement_threshold / 2
                
                if opposite_direction or returned_to_center:
                    in_step = False
                    if step_direction == "left":
                        left_step_count += 1
                    else:
                        right_step_count += 1
                    step_count += 1
                    print(f"Step to {step_direction} completed. Total steps: {step_count}")
                    sys.stdout.flush()  # Ensure the output is immediately visible
                    start_time = time.time()  # Reset the timeout
                    step_direction = "center" if returned_to_center else step_direction
            
            # Display the status on the frame
            status_text = f"Moving {step_direction.capitalize()}" if in_step else "Standing Center"
            cv2.putText(frame, f'Status: {status_text}', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
            cv2.putText(frame, f'Left Steps: {left_step_count}', (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
            cv2.putText(frame, f'Right Steps: {right_step_count}', (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
            cv2.putText(frame, f'Total Steps: {step_count}', (10, 150), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
            
            # Draw a marker for the current hip position
            current_hip_x_pixel = int(hip_midpoint_x * frame.shape[1])
            cv2.circle(frame, (current_hip_x_pixel, frame.shape[0] // 2), 10, (0, 0, 255), -1)
        else:
            print("Hips not fully visible")  # Debug print
            cv2.putText(frame, "Hips not visible", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)
    else:
        print("No pose detected")  # Debug print
        cv2.putText(frame, "No pose detected", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)
    
    # Add "Press 'q' to exit" text
    cv2.putText(frame, "Press 'q' to exit", (10, screen_height - 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
        
    # Display the frame
    cv2.imshow('Side Step Tracker', frame)

    # Break the loop on 'q' key press
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release the capture and close the window
cap.release()
cv2.destroyAllWindows()

print("Side Step Tracker ended")  # Debug print