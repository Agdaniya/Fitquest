import cv2
import mediapipe as mp
import sys
import time

print("Squat Jump Tracker started")  # Debug print

# Initialize MediaPipe Pose
mp_pose = mp.solutions.pose
pose = mp_pose.Pose()

# Initialize MediaPipe drawing utils
mp_drawing = mp.solutions.drawing_utils

# Start video capture
print("Opening camera...")  # Debug print
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Error: Could not open camera.")
    sys.exit(1)

print("Camera opened successfully")

# Get screen resolution
cv2.namedWindow('Squat Jump Tracker', cv2.WINDOW_NORMAL)
screen = cv2.getWindowImageRect('Squat Jump Tracker')
screen_width, screen_height = screen[2], screen[3]

# Fullscreen window
cv2.setWindowProperty('Squat Jump Tracker', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

# Initialize variables
squatting = False
jumping = False
total_count = 0
start_time = time.time()
timeout_duration = 60  # 60 seconds timeout

confidence_threshold = 0.6  # Confidence level for visibility

print("Tracking initialized")  # Debug print

while cap.isOpened():
    if time.time() - start_time > timeout_duration:
        print("Timeout reached. Ending tracking.")
        break

    ret, frame = cap.read()
    if not ret:
        print("Failed to capture frame")  # Debug print
        continue

    # Resize and convert to RGB
    frame = cv2.resize(frame, (screen_width, screen_height))
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Process pose detection
    results = pose.process(rgb_frame)

    # Draw landmarks
    if results.pose_landmarks:
        mp_drawing.draw_landmarks(frame, results.pose_landmarks, mp_pose.POSE_CONNECTIONS,
                                  mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=2),
                                  mp_drawing.DrawingSpec(color=(0, 0, 255), thickness=2, circle_radius=2))

        # Extract key landmarks
        landmarks = results.pose_landmarks.landmark
        left_hip, right_hip = landmarks[mp_pose.PoseLandmark.LEFT_HIP], landmarks[mp_pose.PoseLandmark.RIGHT_HIP]
        left_knee, right_knee = landmarks[mp_pose.PoseLandmark.LEFT_KNEE], landmarks[mp_pose.PoseLandmark.RIGHT_KNEE]
        left_ankle, right_ankle = landmarks[mp_pose.PoseLandmark.LEFT_ANKLE], landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE]

        # Ensure landmarks are visible
        if (left_hip.visibility > confidence_threshold and right_hip.visibility > confidence_threshold and
                left_knee.visibility > confidence_threshold and right_knee.visibility > confidence_threshold and
                left_ankle.visibility > confidence_threshold and right_ankle.visibility > confidence_threshold):

            # Calculate average hip height and knee height
            avg_hip_y = (left_hip.y + right_hip.y) / 2
            avg_knee_y = (left_knee.y + right_knee.y) / 2
            avg_ankle_y = (left_ankle.y + right_ankle.y) / 2

            # Detect squat (hips lower than knees)
            if avg_hip_y > avg_knee_y and not squatting:
                squatting = True
                jumping = False
                print("Squat detected")  # Debug print

            # Detect jump (hips move significantly above knees and ankles)
            if avg_hip_y < avg_knee_y and avg_hip_y < avg_ankle_y and squatting:
                squatting = False
                jumping = True
                total_count += 1
                print(f"Squat Jump Count: {total_count}")  # Debug print
                sys.stdout.flush()
                start_time = time.time()  # Reset timeout

        # Display count
        cv2.putText(frame, f'Squat Jump Count: {total_count}', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)

    else:
        print("No pose detected")  # Debug print

    # Add exit instruction
    cv2.putText(frame, "Press 'q' to exit", (10, screen_height - 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)

    # Show frame
    cv2.imshow('Squat Jump Tracker', frame)

    # Exit loop on 'q' press
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release resources
cap.release()
cv2.destroyAllWindows()

print("Tracking script ended")  # Debug print

