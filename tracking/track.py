import cv2
import mediapipe as mp

# Initialize MediaPipe pose solution
mp_pose = mp.solutions.pose
pose = mp_pose.Pose()

# Initialize MediaPipe drawing utils
mp_drawing = mp.solutions.drawing_utils

# Start video capture (0 for webcam, or provide a video file path)
cap = cv2.VideoCapture(0)

# Initialize variables to track the state and counts
hands_up = False
hands_down = True
hand_cycle_count = 0

legs_apart = False
legs_together = True
leg_cycle_count = 0

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
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

        if hands_up and not hands_up_detected:
            if not hands_down:
                hand_cycle_count += 1
                hands_up = False
                hands_down = True

        # Leg Cycle Detection (legs apart and together)
        legs_apart_detected = (
            (left_knee.x < left_hip.x) and (right_knee.x > right_hip.x) and
            (left_ankle.x < left_knee.x) and (right_ankle.x > right_knee.x)
        )

        if legs_apart_detected:
            if legs_together:
                legs_apart = True
                legs_together = False

        if legs_apart and not legs_apart_detected:
            if not legs_together:
                leg_cycle_count += 1
                legs_apart = False
                legs_together = True

        # Display the cycle counts on the frame
        cv2.putText(frame, f'Hand Cycle Count: {hand_cycle_count}', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(frame, f'Leg Cycle Count: {leg_cycle_count}', (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)

    # Display the frame
    cv2.imshow('Body Tracking', frame)

    # Break the loop on 'q' key press
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release the capture and close the window
cap.release()
cv2.destroyAllWindows()
