import cv2
import mediapipe as mp
import time

# Initialize MediaPipe Pose
mp_pose = mp.solutions.pose
pose = mp_pose.Pose()
mp_drawing = mp.solutions.drawing_utils

# Start Video Capture
cap = cv2.VideoCapture(0)

# Set Fixed Screen Size (Same as Jumping Jacks)
cv2.namedWindow("Standing Crunches Tracker", cv2.WINDOW_NORMAL)
cv2.resizeWindow("Standing Crunches Tracker", 640, 480)

# Initialize Variables
crunch_position = False
total_count = 0
timeout_duration = 60  # Stop after 60 seconds
start_time = time.time()

while cap.isOpened():
    if time.time() - start_time > timeout_duration:
        print("Timeout reached. Ending tracking.")
        break

    ret, frame = cap.read()
    if not ret:
        continue

    frame = cv2.resize(frame, (640, 480))
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    results = pose.process(rgb_frame)

    if results.pose_landmarks:
        mp_drawing.draw_landmarks(
            frame, results.pose_landmarks, mp_pose.POSE_CONNECTIONS
        )

        landmarks = results.pose_landmarks.landmark
        left_knee = landmarks[mp_pose.PoseLandmark.LEFT_KNEE]
        right_knee = landmarks[mp_pose.PoseLandmark.RIGHT_KNEE]
        left_elbow = landmarks[mp_pose.PoseLandmark.LEFT_ELBOW]
        right_elbow = landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW]
        left_hip = landmarks[mp_pose.PoseLandmark.LEFT_HIP]
        right_hip = landmarks[mp_pose.PoseLandmark.RIGHT_HIP]

        # Detect if the elbow and knee are close (Crunch Position)
        crunch_detected = (
            abs(left_elbow.y - left_knee.y) < 0.05 or
            abs(right_elbow.y - right_knee.y) < 0.05
        )

        # Check if Crunch Position is detected
        if crunch_detected and not crunch_position:
            crunch_position = True

        # Check if user returned to standing position
        if crunch_position and left_knee.y > left_hip.y and right_knee.y > right_hip.y:
            total_count += 1  # Count rep when returning to standing
            crunch_position = False  # Reset position for next rep
            print(f"Standing Crunches Count: {total_count}")

        # Display Count
        cv2.putText(frame, f'Standing Crunches Count: {total_count}', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

    cv2.imshow("Standing Crunches Tracker", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
