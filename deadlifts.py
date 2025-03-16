import cv2
import mediapipe as mp
import sys

# Initialize MediaPipe Pose
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)

# Initialize MediaPipe drawing
mp_drawing = mp.solutions.drawing_utils

# Start video capture
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Error: Could not open camera.")
    sys.exit(1)

# Create a named window for full-screen display
cv2.namedWindow('Deadlift Tracking', cv2.WINDOW_NORMAL)
cv2.setWindowProperty('Deadlift Tracking', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

# Initialize variables for deadlift tracking
total_deadlifts = 0
confidence_threshold = 0.6  # Visibility threshold

# Deadlift movement stages
STAGE_STANDING = 0  # Standing upright
STAGE_LOWERING = 1  # Lowering phase
STAGE_LIFTING = 2   # Lifting phase

current_stage = STAGE_STANDING

print("Tracking deadlifts...")

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        print("Failed to capture frame")
        break

    # Convert the frame to RGB
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Process frame with MediaPipe
    results = pose.process(rgb_frame)

    # Draw landmarks on frame
    if results.pose_landmarks:
        mp_drawing.draw_landmarks(
            frame, results.pose_landmarks, mp_pose.POSE_CONNECTIONS,
            mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=2),
            mp_drawing.DrawingSpec(color=(0, 0, 255), thickness=2, circle_radius=2)
        )

        # Get key landmarks
        landmarks = results.pose_landmarks.landmark
        left_hip = landmarks[mp_pose.PoseLandmark.LEFT_HIP]
        left_knee = landmarks[mp_pose.PoseLandmark.LEFT_KNEE]
        left_shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER]

        # Ensure visibility of key points
        if all(lm.visibility > confidence_threshold for lm in [left_hip, left_knee, left_shoulder]):
            # Detect movement phases
            if current_stage == STAGE_STANDING and left_hip.y < left_shoulder.y:
                current_stage = STAGE_LOWERING
                print("Lowering phase...")

            elif current_stage == STAGE_LOWERING and left_hip.y > left_knee.y:
                current_stage = STAGE_LIFTING
                print("Lifting phase...")

            elif current_stage == STAGE_LIFTING and left_hip.y < left_shoulder.y:
                current_stage = STAGE_STANDING
                total_deadlifts += 1
                print(f"Deadlift Count: {total_deadlifts}")

        # Display count and stage
        cv2.putText(frame, f'Deadlift Count: {total_deadlifts}', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(frame, f'Stage: {current_stage}', (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)

    else:
        print("No pose detected")

    # Show video feed
    cv2.imshow('Deadlift Tracking', frame)

    # Exit on 'q' key press
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release resources (Closing the file properly)
cap.release()
cv2.destroyAllWindows()
