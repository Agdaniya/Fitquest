import cv2
import mediapipe as mp
import sys
import time

print("Track.py script started")  # Debug print

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
cv2.namedWindow('Body Tracking', cv2.WINDOW_NORMAL)
screen = cv2.getWindowImageRect('Body Tracking')
screen_width = screen[2]
screen_height = screen[3]

print(f"Screen resolution: {screen_width}x{screen_height}")  # Debug print

# Set the window to fullscreen
cv2.setWindowProperty('Body Tracking', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
# Initialize variables to track the state and counts
hands_up = False
hands_down = True
legs_apart = False
legs_together = True
total_count = 0

# Set a confidence threshold for pose detection
confidence_threshold = 0.6  # Adjust this as needed

print("Tracking script initialized")  # Debug print

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
        
        # Get the landmarks for wrists, elbows, shoulders, knees, hips, and ankles
        landmarks = results.pose_landmarks.landmark
        left_wrist = landmarks[mp_pose.PoseLandmark.LEFT_WRIST]
        right_wrist = landmarks[mp_pose.PoseLandmark.RIGHT_WRIST]
        left_elbow = landmarks[mp_pose.PoseLandmark.LEFT_ELBOW]
        right_elbow = landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW]
        left_shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER]
        right_shoulder = landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER]
        left_knee = landmarks[mp_pose.PoseLandmark.LEFT_KNEE]
        right_knee = landmarks[mp_pose.PoseLandmark.RIGHT_KNEE]
        left_hip = landmarks[mp_pose.PoseLandmark.LEFT_HIP]
        right_hip = landmarks[mp_pose.PoseLandmark.RIGHT_HIP]
        left_ankle = landmarks[mp_pose.PoseLandmark.LEFT_ANKLE]
        right_ankle = landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE]

        # Hand Cycle Detection (hands above shoulders)
        hands_up_detected = (
            (left_wrist.y < left_elbow.y < left_shoulder.y and left_wrist.y < left_shoulder.y) and
            (right_wrist.y < right_elbow.y < right_shoulder.y and right_wrist.y < right_shoulder.y)
        )
        
        if hands_up_detected:
            if hands_down:
                hands_up = True
                hands_down = False
                print("Hands up detected")  # Debug print
            
        # Leg Cycle Detection with Confidence Check (Both Legs Move Together)
        left_leg_visible = (left_knee.visibility > confidence_threshold and left_ankle.visibility > confidence_threshold)
        right_leg_visible = (right_knee.visibility > confidence_threshold and right_ankle.visibility > confidence_threshold)

        if left_leg_visible and right_leg_visible:
            # Legs are detected confidently, proceed with cycle detection
            legs_apart_detected = (
                (left_knee.x < left_hip.x) and (right_knee.x > right_hip.x) and
                (left_ankle.x < left_knee.x) and (right_ankle.x > right_knee.x)
            )

            if legs_apart_detected:
                # Both legs must be together initially
                if legs_together:
                    legs_apart = True
                    legs_together = False
                    print("Legs apart detected")  # Debug print

            # If legs were apart and now are back together, increment the cycle count
            legs_together_detected = (
                (left_knee.x > left_hip.x and right_knee.x < right_hip.x) and
                (left_ankle.x > left_knee.x and right_ankle.x < right_knee.x)
            )

            if legs_apart and legs_together_detected and hands_up and not hands_up_detected:
                legs_apart = False
                legs_together = True
                hands_up = False
                hands_down = True
                total_count += 1
                print(f"jumping jack Count: {total_count}")
                sys.stdout.flush()  # Ensure the output is immediately visible to the parent process
                start_time = time.time()  # Reset the timeout

        # Display the cycle counts on the frame
        cv2.putText(frame, f'Jumping Jack Count: {total_count}', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
    else:
        print("No pose detected")  # Debug print
    
    # Add "Press 'q' to exit" text
    cv2.putText(frame, "Press 'q' to exit", (10, screen_height - 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
        
    # Display the frame
    cv2.imshow('Body Tracking', frame)

    # Break the loop on 'q' key press
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release the capture and close the window
cap.release()
cv2.destroyAllWindows()

print("Tracking script ended")  # Debug print