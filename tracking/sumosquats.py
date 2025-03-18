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
cv2.namedWindow("Sumo Squat Tracker", cv2.WINDOW_NORMAL)
cv2.resizeWindow("Sumo Squat Tracker", 640, 480)

# Initialize Variables
squat_down = False
squat_up = True
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
        left_hip = landmarks[mp_pose.PoseLandmark.LEFT_HIP]
        right_hip = landmarks[mp_pose.PoseLandmark.RIGHT_HIP]
        left_ankle = landmarks[mp_pose.PoseLandmark.LEFT_ANKLE]
        right_ankle = landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE]

        # Check if knees are bent properly for sumo squat down
        sumo_squat_down_detected = (
            (left_knee.y > left_hip.y and left_ankle.y > left_knee.y) and
            (right_knee.y > right_hip.y and right_ankle.y > right_knee.y)
        )

        if sumo_squat_down_detected and not squat_down:
            squat_down = True
            squat_up = False

        # Check if user returned to standing position
        sumo_squat_up_detected = (
            (left_knee.y < left_hip.y and right_knee.y < right_hip.y)
        )

        if squat_down and sumo_squat_up_detected:
            total_count += 1
            squat_down = False
            squat_up = True
            print(f"Sumo Squats Count: {total_count}")

        # Display Count
        cv2.putText(frame, f'Sumo Squats Count: {total_count}', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    
    cv2.imshow("Sumo Squat Tracker", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
