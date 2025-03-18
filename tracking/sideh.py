import cv2
import mediapipe as mp
import sys
import time

print("Side Hops Tracking script started")  # Debug print

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

# Get screen resolution
cv2.namedWindow('Side Hops Tracking', cv2.WINDOW_NORMAL)
cv2.setWindowProperty('Side Hops Tracking', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

# Initialize variables
left_hop = False
right_hop = True
hop_count = 0
confidence_threshold = 0.6  # Adjust as needed

# Timeout settings
start_time = time.time()
timeout_duration = 60  # Run for 60 seconds

while cap.isOpened():
    if time.time() - start_time > timeout_duration:
        print("Timeout reached. Ending tracking.")
        break

    ret, frame = cap.read()
    if not ret:
        print("Failed to capture frame")
        continue

    frame = cv2.flip(frame, 1)  # Flip for better alignment with user movement
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = pose.process(rgb_frame)

    if results.pose_landmarks:
        mp_drawing.draw_landmarks(
            frame, results.pose_landmarks, mp_pose.POSE_CONNECTIONS,
            mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=2),
            mp_drawing.DrawingSpec(color=(0, 0, 255), thickness=2, circle_radius=2)
        )
        
        # Get the landmarks for tracking
        landmarks = results.pose_landmarks.landmark
        left_ankle = landmarks[mp_pose.PoseLandmark.LEFT_ANKLE]
        right_ankle = landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE]
        left_hip = landmarks[mp_pose.PoseLandmark.LEFT_HIP]
        right_hip = landmarks[mp_pose.PoseLandmark.RIGHT_HIP]
        
        # Check visibility confidence
        left_visible = left_ankle.visibility > confidence_threshold
        right_visible = right_ankle.visibility > confidence_threshold

        if left_visible and right_visible:
            # Detect side hop based on ankle lateral movement
            left_hop_detected = left_ankle.x > left_hip.x and right_ankle.x > right_hip.x
            right_hop_detected = left_ankle.x < left_hip.x and right_ankle.x < right_hip.x

            if left_hop_detected and right_hop:
                left_hop = True
                right_hop = False
            
            if right_hop_detected and left_hop:
                left_hop = False
                right_hop = True
                hop_count += 1
                print(f"Side Hop Count: {hop_count}")
                start_time = time.time()  # Reset timeout

    cv2.putText(frame, f'Side Hop Count: {hop_count}', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
    cv2.putText(frame, "Press 'q' to exit", (10, 450), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
    cv2.imshow('Side Hops Tracking', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

print("Side Hops Tracking script ended")  # Debug print
