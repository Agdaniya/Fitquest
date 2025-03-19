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
cv2.namedWindow('Bench Press Tracking', cv2.WINDOW_NORMAL)
cv2.setWindowProperty('Bench Press Tracking', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

# Initialize variables for tracking
total_reps = 0
confidence_threshold = 0.6  # Visibility threshold

# Define Bench Press movement stages
STAGE_START = 0  # Bar at chest level
STAGE_UP = 1     # Bar lifted above chest
STAGE_DOWN = 2   # Bar lowered back

current_stage = STAGE_START

print("Tracking Bench Press...")

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
        left_wrist = landmarks[mp_pose.PoseLandmark.LEFT_WRIST]
        left_shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER]
        left_elbow = landmarks[mp_pose.PoseLandmark.LEFT_ELBOW]

        # Ensure visibility of key points
        if all(lm.visibility > confidence_threshold for lm in [left_wrist, left_shoulder, left_elbow]):
            # Detect movement phases
            if current_stage == STAGE_START and left_wrist.y > left_shoulder.y:
                current_stage = STAGE_UP
                print("Pushing Up...")

            elif current_stage == STAGE_UP and left_wrist.y < left_shoulder.y:
                current_stage = STAGE_DOWN
                print("Lowering Down...")

            elif current_stage == STAGE_DOWN and left_wrist.y > left_shoulder.y:
                current_stage = STAGE_START
                total_reps += 1
                print(f"Bench Press Reps: {total_reps}")

        # Display rep count and stage
        cv2.putText(frame, f'Bench Press Reps: {total_reps}', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(frame, f'Stage: {current_stage}', (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)

    else:
        print("No pose detected")

    # Show video feed
    cv2.imshow('Bench Press Tracking', frame)

    # Exit on 'q' key press
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release resources
cap.release()
cv2.destroyAllWindows()
