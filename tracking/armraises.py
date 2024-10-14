import cv2
import mediapipe as mp
import time
import sys

# Initialize MediaPipe pose solution
mp_pose = mp.solutions.pose
pose = mp_pose.Pose()

# Initialize MediaPipe drawing utils
mp_drawing = mp.solutions.drawing_utils

# Start video capture
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Error: Could not open camera.")
    sys.exit(1)

# Create a named window for full-screen display
cv2.namedWindow('Lateral Arm Raise Tracking', cv2.WINDOW_NORMAL)
cv2.setWindowProperty('Lateral Arm Raise Tracking', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

# Initialize variables to track the state and counts
arms_down = True
arms_up = False
total_arm_raises = 0
confidence_threshold = 0.6  # Confidence threshold for detection

print("Tracking lateral arm raises...")

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        print("Failed to capture frame")
        continue

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
        
        # Get landmarks for shoulders, elbows, and wrists
        landmarks = results.pose_landmarks.landmark
        left_wrist = landmarks[mp_pose.PoseLandmark.LEFT_WRIST]
        right_wrist = landmarks[mp_pose.PoseLandmark.RIGHT_WRIST]
        left_elbow = landmarks[mp_pose.PoseLandmark.LEFT_ELBOW]
        right_elbow = landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW]
        left_shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER]
        right_shoulder = landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER]

        # Detect if arms are up (wrist above the shoulder level)
        arms_up_detected = (
            left_wrist.y < left_shoulder.y and right_wrist.y < right_shoulder.y
        )

        # Detect if arms are down (wrist below the shoulder level)
        arms_down_detected = (
            left_wrist.y > left_elbow.y and right_wrist.y > right_elbow.y
        )

        # Check for upward motion (from down to up)
        if arms_down and arms_up_detected:
            arms_up = True
            arms_down = False
            print("Arms raised")

        # Check for downward motion (from up to down)
        if arms_up and arms_down_detected:
            arms_up = False
            arms_down = True
            total_arm_raises += 1
            print(f"Arm Raises Count: {total_arm_raises}")
        
        # Display arm raise count on the frame
        cv2.putText(frame, f'Arm Raise Count: {total_arm_raises}', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
    else:
        print("No pose detected")
    
    # Display the frame in full screen
    cv2.imshow('Lateral Arm Raise Tracking', frame)

    # Exit if 'q' is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release resources
cap.release()
cv2.destroyAllWindows()
