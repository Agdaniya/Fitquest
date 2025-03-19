import sys
import json
import cv2
import mediapipe as mp
import time
import requests
from datetime import datetime

# Initialize MediaPipe Pose
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils
pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)

# Server endpoint for reporting completion
SERVER_URL = "http://localhost:5001"

def open_camera():
    """Opens the camera for testing with pose detection."""
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Camera could not be opened.")
        return
    cv2.namedWindow('Squat Tracker', cv2.WINDOW_NORMAL)
    cv2.setWindowProperty('Squat Tracker', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
    print("Camera opened. Press 'q' to exit camera test mode.")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Failed to capture frame.")
            break
        
        # Convert to RGB for MediaPipe
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(rgb_frame)
        
        # Draw pose landmarks
        if results.pose_landmarks:
            mp_drawing.draw_landmarks(
                frame, 
                results.pose_landmarks, 
                mp_pose.POSE_CONNECTIONS,
                mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=2),
                mp_drawing.DrawingSpec(color=(245, 66, 230), thickness=2)
            )
        
        # Display instruction text
        cv2.putText(frame, "Camera Test Mode - Press 'q' to exit", (20, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        
        cv2.imshow("Camera Test", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
            
    cap.release()
    cv2.destroyAllWindows()
    print("Camera test ended.")

def count_reps(landmarks, exercise_type):
    """
    Basic implementation of rep counting based on specific joint movements.
    This would need to be customized for each exercise type.
    """
    # Example for squat: track hip movement up and down
    if exercise_type.lower() == "squat":
        # Get hip landmark (e.g., hip point)
        hip = landmarks[mp_pose.PoseLandmark.LEFT_HIP.value]
        return hip.y  # Return y-position for threshold checking
    
    # Example for push-up: track shoulder movement
    elif exercise_type.lower() in ["pushup", "push-up", "push up"]:
        shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value]
        return shoulder.y
    
    # Default case: track movement of wrist for generic exercises
    else:
        wrist = landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value]
        return wrist.y

def report_exercise_completed(exercise_data):
    """Reports to the server that an exercise has been completed."""
    try:
        response = requests.post(
            f"{SERVER_URL}/exercise-completed", 
            json=exercise_data,
            headers={"Content-Type": "application/json"}
        )
        print(f"Exercise completion reported: {response.status_code} - {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error reporting exercise completion: {e}")
        return False

def start_tracking(exercise_name, exercise_type, exercise_details):
    """Tracks exercise movements based on the given type and details."""
    print(f"Tracking {exercise_name} (Type: {exercise_type}) with details: {exercise_details}")
    
    # Parse details
    details = exercise_details if isinstance(exercise_details, dict) else {}
    workout_type = exercise_type.lower()  # Use the specified exercise type
    sets = int(details.get("sets", 1))
    rest_time = int(details.get("rest", 30))
    
    # Type-specific parameters
    # Handle the specific exercise types from your app
    if workout_type == "reps":
        reps = int(details.get("reps", 10))
        duration = 0
    elif workout_type == "time":
        reps = 0
        duration = int(details.get("time", 30))
    elif workout_type == "hold":
        reps = 0
        duration = int(details.get("hold", 30))
    else:
        # Default case
        reps = int(details.get("reps", 10))
        duration = int(details.get("time", 30))
    
    print(f"Exercise configuration: {workout_type} - Sets: {sets}, Rest: {rest_time}s")
    if workout_type == "reps":
        print(f"Target reps: {reps}")
    elif workout_type in ["time", "hold"]:
        print(f"Target duration: {duration}s")
    
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Camera could not be opened for tracking.")
        return
    
    # Tracking variables
    current_set = 1
    current_rep = 0
    state = "exercise"  # can be "exercise" or "rest"
    start_time = time.time()
    last_rep_position = 0
    rep_threshold = 0.05  # Threshold for detecting a rep
    rep_direction_up = True  # Track rep movement direction
    exercise_completed = False
    
    print(f"Starting exercise: {exercise_name}, Set 1 of {sets}")
    
    while current_set <= sets:
        ret, frame = cap.read()
        if not ret:
            print("Error: Failed to capture frame.")
            break

        # Current time elapsed
        current_time = time.time()
        elapsed = current_time - start_time
        
        # Convert to RGB for MediaPipe
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(rgb_frame)
        
        # Draw landmarks
        if results.pose_landmarks:
            mp_drawing.draw_landmarks(
                frame, 
                results.pose_landmarks, 
                mp_pose.POSE_CONNECTIONS,
                mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=2),
                mp_drawing.DrawingSpec(color=(245, 66, 230), thickness=2)
            )
            
            # Process based on exercise type
            if state == "exercise":
                if workout_type == "reps":
                    # Rep counting logic
                    landmarks = results.pose_landmarks.landmark
                    current_position = count_reps(landmarks, exercise_name)
                    
                    # Simple rep detection based on position change
                    if rep_direction_up and last_rep_position - current_position > rep_threshold:
                        rep_direction_up = False
                    elif not rep_direction_up and current_position - last_rep_position > rep_threshold:
                        rep_direction_up = True
                        current_rep += 1
                        print(f"Rep {current_rep} completed")
                    
                    last_rep_position = current_position
                    
                    # Display rep count
                    cv2.putText(frame, f"Reps: {current_rep}/{reps}", (50, 100), 
                               cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    
                    # Check if all reps are done
                    if current_rep >= reps:
                        if current_set < sets:
                            state = "rest"
                            start_time = current_time
                            current_rep = 0
                            print(f"Set {current_set} completed. Starting rest period of {rest_time}s")
                        else:
                            print(f"Exercise {exercise_name} completed!")
                            exercise_completed = True
                            break
                            
                elif workout_type in ["time", "hold"]:
                    # Timer countdown
                    remaining = max(0, duration - elapsed)
                    cv2.putText(frame, f"Time: {int(remaining)}s", (50, 100), 
                               cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    
                    # Check if time is up
                    if elapsed >= duration:
                        if current_set < sets:
                            state = "rest"
                            start_time = current_time
                            print(f"Set {current_set} completed. Starting rest period of {rest_time}s")
                        else:
                            print(f"Exercise {exercise_name} completed!")
                            exercise_completed = True
                            break
            
            elif state == "rest":
                # Rest countdown
                remaining = max(0, rest_time - elapsed)
                cv2.putText(frame, f"REST: {int(remaining)}s", (50, 100), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                
                # Check if rest is over
                if elapsed >= rest_time:
                    state = "exercise"
                    start_time = current_time
                    current_set += 1
                    print(f"Starting Set {current_set} of {sets}")
        
        # Display exercise info
        cv2.putText(frame, f"Exercise: {exercise_name}", (50, 50), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(frame, f"Set: {current_set}/{sets}", (50, 150), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(frame, f"State: {state.upper()}", (50, 200), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(frame, "Press 'q' to quit", (50, 250), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        cv2.imshow("Exercise Tracking", frame)
        key = cv2.waitKey(1) & 0xFF
        
        # Allow manual completion with 'c' key (for testing)
        if key == ord('c'):
            print("Exercise manually marked as completed")
            exercise_completed = True
            break
        # Or quit with 'q' key
        elif key == ord('q'):
            print("Exercise tracking stopped by user")
            break

    cap.release()
    cv2.destroyAllWindows()
    
    # Report completion to server if exercise was completed
    if exercise_completed:
        report_exercise_completed({
            "name": exercise_name,
            "type": exercise_type,
            "details": details,
            "category": details.get("category", "")
        })
    
    print(f"Finished tracking {exercise_name}")

if __name__ == "__main__":
    print("Arguments received:", sys.argv)  # Debugging

    if len(sys.argv) > 1 and sys.argv[1] == "camera":
        print("Running in camera test mode...")
        open_camera()
    elif len(sys.argv) > 3:
        exercise_name = sys.argv[1]
        exercise_type = sys.argv[2]
        try:
            exercise_details = json.loads(sys.argv[3])  # Parse JSON data
        except json.JSONDecodeError as e:
            print(f"Error parsing exercise details JSON: {e}")
            print(f"Received string: {sys.argv[3]}")
            exercise_details = {}
        start_tracking(exercise_name, exercise_type, exercise_details)
    else:
        print("Error: Invalid arguments. Expected 'camera' or exercise details.")
        print("Usage:")
        print("  python tracker.py camera")
        print("  python tracker.py <exercise_name> <exercise_type> <exercise_details_json>")