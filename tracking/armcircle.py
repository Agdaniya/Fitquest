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
cv2.namedWindow('Arm Circle Tracking', cv2.WINDOW_NORMAL)
cv2.setWindowProperty('Arm Circle Tracking', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

# Initialize variables to track the state and counts
arm_circle_started = False
total_arm_circles = 0
arm_moving_up = False
arm_moving_down = False
confidence_threshold = 0.6  # Confidence threshold for detection

print("Tracking arm circles...")

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
        
        # Get landmarks for shoulder and wrist
        landmarks = results.pose_landmarks.landmark
        left_wrist = landmarks[mp_pose.PoseLandmark.LEFT_WRIST]
        left_shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER]

        if left_wrist.visibility > confidence_threshold and left_shoulder.visibility > confidence_threshold:
            # Arm moving up
            if left_wrist.y < left_shoulder.y and not arm_moving_up:
                arm_moving_up = True
                arm_moving_down = False
                print("Arm moving up")

            # Arm moving down (completes an arm circle)
            if left_wrist.y > left_shoulder.y and arm_moving_up:
                arm_moving_down = True
                arm_moving_up = False
                total_arm_circles += 1
                print(f"Arm Circle Count: {total_arm_circles}")

        # Display arm circle count on the frame
        cv2.putText(frame, f'Arm Circle Count: {total_arm_circles}', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)

    else:
        print("No pose detected")
    
    # Display the frame in full screen
    cv2.imshow('Arm Circle Tracking', frame)

    # Exit if 'q' is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release resources
cap.release()
cv2.destroyAllWindows()
