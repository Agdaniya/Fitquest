import cv2
import mediapipe as mp
import sys
import time

print("Side Leg Lifts Tracker started")  # Debug print

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
cv2.namedWindow('Side Leg Lifts Tracker', cv2.WINDOW_NORMAL)
screen = cv2.getWindowImageRect('Side Leg Lifts Tracker')
screen_width = screen[2]
screen_height = screen[3]

print(f"Screen resolution: {screen_width}x{screen_height}")  # Debug print

# Set the window to fullscreen
cv2.setWindowProperty('Side Leg Lifts Tracker', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

# Initialize variables to track the state and counts
left_leg_up = False
left_leg_down = True
right_leg_up = False
right_leg_down = True
left_count = 0
right_count = 0
total_count = 0

# Set a confidence threshold for pose detection
confidence_threshold = 0.6  # Adjust this as needed

# Track which leg is currently being lifted
current_leg = "none"  # "left", "right", or "none"

print("Side Leg Lifts Tracker initialized")  # Debug print

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
        
        if left_leg_visible and right_leg_visible:
            # Calculate the horizontal distance between hip and ankle for each leg
            left_hip_ankle_distance = abs(left_ankle.x - left_hip.x)
            right_hip_ankle_distance = abs(right_ankle.x - right_hip.x)
            
            # Define thresholds for leg lift detection
            # When the leg is lifted to the side, the horizontal distance increases
            left_leg_lift_threshold = 0.15  # Adjust based on testing
            right_leg_lift_threshold = 0.15  # Adjust based on testing
            
            # Check if left leg is lifted to the side
            left_leg_lifted = left_hip_ankle_distance > left_leg_lift_threshold
            
            # Check if right leg is lifted to the side
            right_leg_lifted = right_hip_ankle_distance > right_leg_lift_threshold
            
            # Ensure knees are relatively straight during the lift (not bent)
            left_knee_straight = abs(left_knee.y - ((left_hip.y + left_ankle.y) / 2)) < 0.05
            right_knee_straight = abs(right_knee.y - ((right_hip.y + right_ankle.y) / 2)) < 0.05
            
            # LEFT LEG LIFT DETECTION
            if left_leg_lifted and left_knee_straight and not right_leg_lifted:
                if left_leg_down and current_leg in ["none", "left"]:
                    left_leg_up = True
                    left_leg_down = False
                    current_leg = "left"
                    print("Left leg up detected")  # Debug print
            elif not left_leg_lifted and left_leg_up and current_leg == "left":
                left_leg_up = False
                left_leg_down = True
                left_count += 1
                total_count += 1
                current_leg = "none"
                print(f"Left Leg Lift Count: {left_count}, Total: {total_count}")
                sys.stdout.flush()  # Ensure the output is immediately visible
                start_time = time.time()  # Reset the timeout
            
            # RIGHT LEG LIFT DETECTION
            if right_leg_lifted and right_knee_straight and not left_leg_lifted:
                if right_leg_down and current_leg in ["none", "right"]:
                    right_leg_up = True
                    right_leg_down = False
                    current_leg = "right"
                    print("Right leg up detected")  # Debug print
            elif not right_leg_lifted and right_leg_up and current_leg == "right":
                right_leg_up = False
                right_leg_down = True
                right_count += 1
                total_count += 1
                current_leg = "none"
                print(f"Right Leg Lift Count: {right_count}, Total: {total_count}")
                sys.stdout.flush()  # Ensure the output is immediately visible
                start_time = time.time()  # Reset the timeout
        
        else:
            print("Legs not fully visible")  # Debug print
        
        # Display the status on the frame
        status_text = ""
        if current_leg == "left":
            status_text = "Left Leg Lifting"
        elif current_leg == "right":
            status_text = "Right Leg Lifting"
        else:
            status_text = "Standing"
        
        cv2.putText(frame, f'Status: {status_text}', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(frame, f'Left Leg Lifts: {left_count}', (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(frame, f'Right Leg Lifts: {right_count}', (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(frame, f'Total Lifts: {total_count}', (10, 150), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
    else:
        print("No pose detected")  # Debug print
    
    # Add "Press 'q' to exit" text
    cv2.putText(frame, "Press 'q' to exit", (10, screen_height - 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
        
    # Display the frame
    cv2.imshow('Side Leg Lifts Tracker', frame)

    # Break the loop on 'q' key press
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release the capture and close the window
cap.release()
cv2.destroyAllWindows()

print("Side Leg Lifts Tracker ended")  # Debug print