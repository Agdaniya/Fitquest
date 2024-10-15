import cv2
import mediapipe as mp
import sys

# Initialize MediaPipe pose solution
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)

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
total_arm_circles = 0
confidence_threshold = 0.6  # Confidence threshold for detection

# Define stages of arm circle
STAGE_START = 0
STAGE_ABOVE_HEAD = 1
STAGE_SIDE = 2
STAGE_BELOW_HIP = 3

current_stage = STAGE_START

print("Tracking arm circles...")

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        print("Failed to capture frame")
        break

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
        
        # Get landmarks for wrist, shoulder, hip, and head
        landmarks = results.pose_landmarks.landmark
        left_wrist = landmarks[mp_pose.PoseLandmark.LEFT_WRIST]
        left_shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER]
        left_hip = landmarks[mp_pose.PoseLandmark.LEFT_HIP]
        left_ear = landmarks[mp_pose.PoseLandmark.LEFT_EAR]  # Using ear as reference for head

        if all(lm.visibility > confidence_threshold for lm in [left_wrist, left_shoulder, left_hip, left_ear]):
            # Check stages of arm circle
            if current_stage == STAGE_START and left_wrist.y < left_ear.y:
                current_stage = STAGE_ABOVE_HEAD
                print("Hand above head")
            elif current_stage == STAGE_ABOVE_HEAD and left_wrist.y > left_shoulder.y and left_wrist.y < left_hip.y:
                current_stage = STAGE_SIDE
                print("Hand at side")
            elif current_stage == STAGE_SIDE and left_wrist.y > left_hip.y:
                current_stage = STAGE_BELOW_HIP
                print("Hand below hip")
            elif current_stage == STAGE_BELOW_HIP and left_wrist.y < left_shoulder.y:
                current_stage = STAGE_START
                total_arm_circles += 1
                print(f"Arm Circle Count: {total_arm_circles}")

        # Display arm circle count and current stage on the frame
        cv2.putText(frame, f'Arm Circle Count: {total_arm_circles}', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(frame, f'Stage: {current_stage}', (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)

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