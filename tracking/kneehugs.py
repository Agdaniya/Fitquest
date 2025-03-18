import cv2
import mediapipe as mp
import sys
import time

print("Knee Hugs Tracker started")  # Debug print

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
cv2.namedWindow('Knee Hugs Tracker', cv2.WINDOW_NORMAL)
screen = cv2.getWindowImageRect('Knee Hugs Tracker')
screen_width = screen[2]
screen_height = screen[3]

print(f"Screen resolution: {screen_width}x{screen_height}")  # Debug print

# Set the window to fullscreen
cv2.setWindowProperty('Knee Hugs Tracker', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

# Initialize variables to track the state and counts
left_knee_up = False
left_knee_down = True
right_knee_up = False
right_knee_down = True
left_count = 0
right_count = 0
total_count = 0

# Set a confidence threshold for pose detection
confidence_threshold = 0.6  # Adjust this as needed

# Define threshold for knee hug detection
knee_hug_threshold = 0.3  # Adjust based on testing - higher values mean knee needs to be closer to chest

# Track which knee is currently being hugged
current_knee = "none"  # "left", "right", or "none"

print("Knee Hugs Tracker initialized")  # Debug print

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
        
        # Get the landmarks for hips, knees, and shoulders
        landmarks = results.pose_landmarks.landmark
        left_hip = landmarks[mp_pose.PoseLandmark.LEFT_HIP]
        right_hip = landmarks[mp_pose.PoseLandmark.RIGHT_HIP]
        left_knee = landmarks[mp_pose.PoseLandmark.LEFT_KNEE]
        right_knee = landmarks[mp_pose.PoseLandmark.RIGHT_KNEE]
        left_shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER]
        right_shoulder = landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER]
        
        # Check if knees and hips are visible with sufficient confidence
        left_parts_visible = (left_hip.visibility > confidence_threshold and 
                             left_knee.visibility > confidence_threshold and 
                             left_shoulder.visibility > confidence_threshold)
        
        right_parts_visible = (right_hip.visibility > confidence_threshold and 
                              right_knee.visibility > confidence_threshold and 
                              right_shoulder.visibility > confidence_threshold)
        
        if left_parts_visible and right_parts_visible:
            # For knee hugs, we need to detect when the knee gets closer to the chest/shoulder
            # Calculate the vertical distance ratio between knee and hip (normalized by shoulder-hip distance)
            shoulder_hip_height_left = abs(left_shoulder.y - left_hip.y)
            shoulder_hip_height_right = abs(right_shoulder.y - right_hip.y)
            
            # Calculate normalized knee position relative to hip
            # In MediaPipe, Y increases downward, so we need to check if knee.y < hip.y
            left_knee_lift_ratio = (left_hip.y - left_knee.y) / shoulder_hip_height_left if shoulder_hip_height_left > 0 else 0
            right_knee_lift_ratio = (right_hip.y - right_knee.y) / shoulder_hip_height_right if shoulder_hip_height_right > 0 else 0
            
            # Check if left knee is hugged (lifted toward chest)
            left_knee_hugged = left_knee_lift_ratio > knee_hug_threshold
            
            # Check if right knee is hugged (lifted toward chest)
            right_knee_hugged = right_knee_lift_ratio > knee_hug_threshold
            
            # LEFT KNEE HUG DETECTION
            if left_knee_hugged and not right_knee_hugged:
                if left_knee_down and current_knee in ["none", "left"]:
                    left_knee_up = True
                    left_knee_down = False
                    current_knee = "left"
                    print("Left knee hug detected")  # Debug print
            elif not left_knee_hugged and left_knee_up and current_knee == "left":
                left_knee_up = False
                left_knee_down = True
                left_count += 1
                total_count += 1
                current_knee = "none"
                print(f"Left Knee Hug Count: {left_count}, Total: {total_count}")
                sys.stdout.flush()  # Ensure the output is immediately visible
                start_time = time.time()  # Reset the timeout
            
            # RIGHT KNEE HUG DETECTION
            if right_knee_hugged and not left_knee_hugged:
                if right_knee_down and current_knee in ["none", "right"]:
                    right_knee_up = True
                    right_knee_down = False
                    current_knee = "right"
                    print("Right knee hug detected")  # Debug print
            elif not right_knee_hugged and right_knee_up and current_knee == "right":
                right_knee_up = False
                right_knee_down = True
                right_count += 1
                total_count += 1
                current_knee = "none"
                print(f"Right Knee Hug Count: {right_count}, Total: {total_count}")
                sys.stdout.flush()  # Ensure the output is immediately visible
                start_time = time.time()  # Reset the timeout
            
            # Add debug visualization for knee hug thresholds
            left_knee_pos = (int(left_knee.x * frame.shape[1]), int(left_knee.y * frame.shape[0]))
            right_knee_pos = (int(right_knee.x * frame.shape[1]), int(right_knee.y * frame.shape[0]))
            
            # Show threshold indicators
            left_color = (0, 255, 0) if left_knee_hugged else (0, 0, 255)  # Green if hugged, red if not
            right_color = (0, 255, 0) if right_knee_hugged else (0, 0, 255)  # Green if hugged, red if not
            
            cv2.circle(frame, left_knee_pos, 15, left_color, -1)
            cv2.circle(frame, right_knee_pos, 15, right_color, -1)
            
            # Show knee hug ratio values
            cv2.putText(frame, f'L Ratio: {left_knee_lift_ratio:.2f}', (left_knee_pos[0], left_knee_pos[1] - 20), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
            cv2.putText(frame, f'R Ratio: {right_knee_lift_ratio:.2f}', (right_knee_pos[0], right_knee_pos[1] - 20), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
        
        else:
            print("Knees or hips not fully visible")  # Debug print
        
        # Display the status on the frame
        status_text = ""
        if current_knee == "left":
            status_text = "Left Knee Hugging"
        elif current_knee == "right":
            status_text = "Right Knee Hugging"
        else:
            status_text = "Standing"
        
        cv2.putText(frame, f'Status: {status_text}', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(frame, f'Left Knee Hugs: {left_count}', (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(frame, f'Right Knee Hugs: {right_count}', (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(frame, f'Total Hugs: {total_count}', (10, 150), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(frame, f'Threshold: {knee_hug_threshold:.2f}', (10, 190), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
    else:
        print("No pose detected")  # Debug print
    
    # Add "Press 'q' to exit" text
    cv2.putText(frame, "Press 'q' to exit", (10, screen_height - 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
        
    # Display the frame
    cv2.imshow('Knee Hugs Tracker', frame)

    # Break the loop on 'q' key press
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release the capture and close the window
cap.release()
cv2.destroyAllWindows()

print("Knee Hugs Tracker ended")  # Debug print