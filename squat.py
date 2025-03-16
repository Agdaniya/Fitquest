import cv2
import mediapipe as mp
import sys
import time
import math

# Initialize MediaPipe pose solution
mp_pose = mp.solutions.pose
pose = mp_pose.Pose()

# Initialize MediaPipe drawing utils
mp_drawing = mp.solutions.drawing_utils

# Start video capture (0 for webcam)
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Error: Could not open camera.")
    sys.exit(1)

# Set fullscreen
cv2.namedWindow('Squat Tracker', cv2.WINDOW_NORMAL)
cv2.setWindowProperty('Squat Tracker', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

# Variables to track squat state and counts
squat_position = False  # True when the person is in the squat position
squat_count = 0
threshold_angle = 160  # Adjust based on the angle when standing vs squatting
standing_angle = 170  # Angle when person is standing (tuned as needed)
confidence_threshold = 0.6  # Pose confidence threshold

def calculate_angle(a, b, c):
    """Calculates the angle between three points: a, b, and c (in 2D)."""
    a = [a.x, a.y]
    b = [b.x, b.y]
    c = [c.x, c.y]
    radians = math.atan2(c[1] - b[1], c[0] - b[0]) - math.atan2(a[1] - b[1], a[0] - b[0])
    angle = abs(radians * 180.0 / math.pi)
    if angle > 180.0:
        angle = 360.0 - angle
    return angle

start_time = time.time()
timeout_duration = 60  # 60 seconds timeout

while cap.isOpened():
    if time.time() - start_time > timeout_duration:
        print("Timeout reached. Ending tracking.")
        break

    ret, frame = cap.read()
    if not ret:
        print("Failed to capture frame")
        continue

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = pose.process(rgb_frame)

    if results.pose_landmarks:
        mp_drawing.draw_landmarks(
            frame, results.pose_landmarks, mp_pose.POSE_CONNECTIONS,
            mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=2),
            mp_drawing.DrawingSpec(color=(0, 0, 255), thickness=2, circle_radius=2)
        )

        landmarks = results.pose_landmarks.landmark

        # Get landmarks for hips, knees, and ankles
        left_hip = landmarks[mp_pose.PoseLandmark.LEFT_HIP]
        left_knee = landmarks[mp_pose.PoseLandmark.LEFT_KNEE]
        left_ankle = landmarks[mp_pose.PoseLandmark.LEFT_ANKLE]
        right_hip = landmarks[mp_pose.PoseLandmark.RIGHT_HIP]
        right_knee = landmarks[mp_pose.PoseLandmark.RIGHT_KNEE]
        right_ankle = landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE]

        # Calculate knee angles
        left_knee_angle = calculate_angle(left_hip, left_knee, left_ankle)
        right_knee_angle = calculate_angle(right_hip, right_knee, right_ankle)

        # Check if person is squatting based on knee angles
        if left_knee_angle < threshold_angle and right_knee_angle < threshold_angle:
            if not squat_position:  # If transitioning into squat
                squat_position = True
                print("Squat down detected")
        elif left_knee_angle > standing_angle and right_knee_angle > standing_angle:
            if squat_position:  # If transitioning out of squat
                squat_position = False
                squat_count += 1
                print(f"Squat Count: {squat_count}")

        # Display squat count
        cv2.putText(frame, f'Squat Count: {squat_count}', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)

    # Add "Press 'q' to exit" text
    cv2.putText(frame, "Press 'q' to exit", (10, frame.shape[0] - 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)

    # Show the frame
    cv2.imshow('Squat Tracker', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
