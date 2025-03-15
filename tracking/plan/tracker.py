import sys
import json
import time
import cv2
import mediapipe as mp
import numpy as np

# Initialize MediaPipe Pose Detection
mp_pose = mp.solutions.pose
pose = mp_pose.Pose()

# Function to track reps using pose estimation
def track_reps(exercise_name, details):
    reps = details.get("reps", 10)
    rest_time = details.get("rest", 30)
    sets = details.get("sets", 3)

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open camera")
        return

    rep_count = 0
    set_count = 0
    position = None

    while set_count < sets:
        success, frame = cap.read()
        if not success:
            continue

        # Convert to RGB
        image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(image_rgb)

        if results.pose_landmarks:
            landmarks = results.pose_landmarks.landmark
            left_shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER]
            left_hip = landmarks[mp_pose.PoseLandmark.LEFT_HIP]
            left_knee = landmarks[mp_pose.PoseLandmark.LEFT_KNEE]

            # Calculate angle for squats, push-ups, etc.
            angle = calculate_angle(left_shoulder, left_hip, left_knee)

            # Basic logic for detecting rep movements (adjust as needed)
            if angle > 160:  
                position = "up"
            if angle < 90 and position == "up":  
                position = "down"
                rep_count += 1
                print(f"Reps: {rep_count}/{reps}")

        # Show camera feed
        cv2.imshow("Exercise Tracker", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break  # Press 'q' to quit

        # Check if reps completed
        if rep_count >= reps:
            print(f"Set {set_count + 1} complete!")
            set_count += 1
            rep_count = 0  # Reset reps
            time.sleep(rest_time)  # Rest time

    cap.release()
    cv2.destroyAllWindows()
    print(f"Completed {exercise_name}")

# Function to track time-based exercises
def track_time(exercise_name, duration):
    print(f"Tracking {exercise_name} for {duration} seconds")
    time.sleep(duration)
    print(f"Completed {exercise_name}")

# Function to track hold-based exercises
def track_hold(exercise_name, hold_duration):
    print(f"Tracking hold {exercise_name} for {hold_duration} seconds")
    time.sleep(hold_duration)
    print(f"Hold complete for {exercise_name}")

# Function to calculate angle between three points
def calculate_angle(a, b, c):
    a = np.array([a.x, a.y])  
    b = np.array([b.x, b.y])  
    c = np.array([c.x, c.y])  

    ba = a - b
    bc = c - b

    cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
    angle = np.arccos(cosine_angle)
    return np.degrees(angle)

# Main execution
if __name__ == "__main__":
    exercise_name = sys.argv[1]
    exercise_type = sys.argv[2]
    exercise_details = json.loads(sys.argv[3])  

    if exercise_type == "reps":
        track_reps(exercise_name, exercise_details)
    elif exercise_type == "time":
        track_time(exercise_name, exercise_details.get("time", 30))
    elif exercise_type == "hold":
        track_hold(exercise_name, exercise_details.get("hold", 15))
    else:
        print("Unknown exercise type")
