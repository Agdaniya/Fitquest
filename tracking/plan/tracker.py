import sys
import json
import cv2
import mediapipe as mp
import time
import requests
from datetime import datetime
import math

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

def count_reps(landmarks, exercise_type):
    """
    Implementation of rep counting based on specific joint movements for different exercises.
    Each exercise has custom tracking based on appropriate body landmarks.
    """
    # Squats tracking - track hip movement relative to knees
    if exercise_type.lower() in ["squats"]:
        # Get landmarks for hips, knees, and ankles
        left_hip = landmarks[mp_pose.PoseLandmark.LEFT_HIP.value]
        left_knee = landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value]
        left_ankle = landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value]
        right_hip = landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value]
        right_knee = landmarks[mp_pose.PoseLandmark.RIGHT_KNEE.value]
        right_ankle = landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE.value]
        
        # Calculate knee angles
        left_knee_angle = calculate_angle(left_hip, left_knee, left_ankle)
        right_knee_angle = calculate_angle(right_hip, right_knee, right_ankle)
        
        # Return the average of both knee angles (smaller angle = deeper squat)
        return (left_knee_angle + right_knee_angle) / 2
    
    # Leg raises tracking - track ankle movement
    elif exercise_type.lower() in ["leg raises"]:
        ankle = landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value]
        hip = landmarks[mp_pose.PoseLandmark.LEFT_HIP.value]
        # Measure how high the ankle is raised relative to hip
        return hip.y - ankle.y  # Larger value = higher leg raise
    
     # Sumo Squats tracking - track hip movement relative to knees
    elif exercise_type.lower() in ["sumo squats"]:
        ankle = landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value]
        hip = landmarks[mp_pose.PoseLandmark.LEFT_HIP.value]
        # Measure how high the ankle is raised relative to hip
        return hip.y - ankle.y  # Larger value = higher leg raise
    
    # Standing side leg lifts - track ankle horizontal movement
    elif exercise_type.lower() in ["standing side leg lifts"]:
        left_ankle = landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value]
        right_ankle = landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE.value]
        # Track separation between ankles
        return abs(left_ankle.x - right_ankle.x)  # Larger value = wider lift
    
    # Hand/arm raises tracking - track wrist height
    elif exercise_type.lower() in ["hand raises", "lateral arm raises"]:
        # Get landmarks needed for tracking
        left_wrist = landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value]
        right_wrist = landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value]
        left_shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value]
        right_shoulder = landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value]
        
        # Calculate normalized positions - how high wrists are relative to shoulders
        # A positive value means wrists are above shoulders
        left_arm_raised = left_shoulder.y - left_wrist.y
        right_arm_raised = right_shoulder.y - right_wrist.y
        
        # Calculate average arm position (higher value = arms raised higher)
        avg_arm_position = (left_arm_raised + right_arm_raised) / 2
        
        # Need to return a clear metric that changes significantly between 
        # arms down and arms raised positions
        return avg_arm_position
    
    elif exercise_type.lower() in ["arm circles"]:
        wrist = landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value]
        shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value]
        # Measure wrist height relative to shoulder
        return shoulder.y - wrist.y  # Positive when hand is above shoulder
    
    # Jumping jacks - track hand and feet separation
    # Jumping jacks - track hand and feet separation
    elif exercise_type.lower() in ["jumping jacks"]:
        # Get all relevant landmarks for jumping jacks
        left_wrist = landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value]
        right_wrist = landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value]
        left_elbow = landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value]
        right_elbow = landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value]
        left_shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value]
        right_shoulder = landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value]
        left_knee = landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value]
        right_knee = landmarks[mp_pose.PoseLandmark.RIGHT_KNEE.value]
        left_hip = landmarks[mp_pose.PoseLandmark.LEFT_HIP.value]
        right_hip = landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value]
        left_ankle = landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value]
        right_ankle = landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE.value]
        
        # Specific detection for each part of the jumping jack
        # 1. Hands up detection (both hands must be above shoulders)
        hands_up_detected = (
            (left_wrist.y < left_elbow.y < left_shoulder.y and left_wrist.y < left_shoulder.y) and
            (right_wrist.y < right_elbow.y < right_shoulder.y and right_wrist.y < right_shoulder.y)
        )
        
        # 2. Legs apart detection (knees and ankles are outside of hips)
        legs_apart_detected = (
            (left_knee.x < left_hip.x) and (right_knee.x > right_hip.x) and
            (left_ankle.x < left_knee.x) and (right_ankle.x > right_knee.x)
        )
        
        # 3. Legs together detection (knees and ankles are inside of hips)
        legs_together_detected = (
            (left_knee.x > left_hip.x and right_knee.x < right_hip.x) and
            (left_ankle.x > left_knee.x and right_ankle.x < right_knee.x)
        )
        
        # Create a state value that will only be high when both conditions are met
        # for a proper jumping jack (hands up AND legs apart)
        if hands_up_detected and legs_apart_detected:
            return 1.0  # Full jumping jack position
        elif not hands_up_detected and legs_together_detected:
            return 0.0  # Rest position
        else:
            return 0.5  # Transition state
        
    # Side steps tracking - track feet separation horizontally
    elif exercise_type.lower() in ["side steps"]:
        left_ankle = landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value]
        right_ankle = landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE.value]
        # Track separation between feet
        return abs(left_ankle.x - right_ankle.x)  # Larger value = wider step
    
    # Standing crunches - track knee and elbow proximity
    elif exercise_type.lower() in ["standing-crunches"]:
        knee = landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value]
        elbow = landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value]
        # Measure distance between knee and elbow (smaller = crunch position)
        dx = knee.x - elbow.x
        dy = knee.y - elbow.y
        return (dx**2 + dy**2)**0.5  # Distance between knee and elbow
    
    # Side to side jabs - track horizontal wrist movement
    elif exercise_type.lower() in ["side to side jabs"]:
        wrist = landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value]
        shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value]
        # Track how far the wrist extends from shoulder horizontally
        return abs(wrist.x - shoulder.x)  # Larger value = extended jab
    
    # Knee hugs - track knee and elbow proximity
    elif exercise_type.lower() in ["knee hugs"]:
        knee = landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value]
        elbow = landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value]
        # Measure distance between knee and elbow (smaller = hug position)
        dx = knee.x - elbow.x
        dy = knee.y - elbow.y
        return (dx**2 + dy**2)**0.5  # Distance between knee and elbow
    
    # Bridge - track hip elevation
    elif exercise_type.lower() in ["bridge", "glute bridges"]:
        hip = landmarks[mp_pose.PoseLandmark.LEFT_HIP.value]
        shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value]
        ankle = landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value]
        # In bridge position, hips should be elevated (creating a straight line from shoulders to knees)
        return shoulder.y - hip.y + ankle.y - hip.y  # Larger values when hip is elevated
    
    # Side Hops - track vertical movement and horizontal position
    elif exercise_type.lower() in ["side hops"]:
        ankle = landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value]
        hip = landmarks[mp_pose.PoseLandmark.LEFT_HIP.value]
        # Track both height (for hop) and horizontal position (for side movement)
        vertical = hip.y - ankle.y  # Larger when hopping
        horizontal = ankle.x  # Position changes during side-to-side movement
        return vertical + abs(horizontal)  # Combined measure
    
    # Squat jumps - track combined squat posture and elevation
    elif exercise_type.lower() in ["squat jumps"]:
        hip = landmarks[mp_pose.PoseLandmark.LEFT_HIP.value]
        ankle = landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value]
        knee = landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value]
        # Combine squat form and jump height
        squat_depth = hip.y - knee.y  # Squat position
        jump_height = ankle.y  # Lower value when feet leave ground
        return squat_depth + (1 - jump_height)  # Combined measure
    
    # Skipping - similar to jumping jacks but focus on ankle height from ground
    elif exercise_type.lower() in ["skipping"]:
        ankle = landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value]
        # Track ankle height (lower y value = higher position)
        return -ankle.y  # Negative because lower y value means higher position in image
    
    # Default fallback for any unspecified exercises - track general body movement
    else:
        # Use a comprehensive approach combining multiple landmarks for general exercise detection
        nose = landmarks[mp_pose.PoseLandmark.NOSE.value]
        left_wrist = landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value]
        right_wrist = landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value]
        left_ankle = landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value]
        right_ankle = landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE.value]
        
        # Combine values to detect general body movement
        movement = (nose.y + left_wrist.y + right_wrist.y + left_ankle.y + right_ankle.y) / 5
        return movement  # Average position - will change with general movement

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
    threshold_angle = 160  # Adjust based on the angle when standing vs squatting
    standing_angle = 170  # Angle when person is standing
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
                    
                    # Special rep detection for squats based on knee angle
                    if exercise_name.lower() in ["squats"]:
                        if current_position < threshold_angle and rep_direction_up:
                            # Person is in squat position
                            rep_direction_up = False
                            print("Squat position detected")
                        elif current_position > standing_angle and not rep_direction_up:
                            # Person has stood up from squat
                            rep_direction_up = True
                            current_rep += 1
                            print(f"Rep {current_rep} completed")
                    elif exercise_name.lower() in ["hand raises", "lateral arm raises"]:
                        # Define thresholds for arm positions
                        arms_raised_threshold = 0.15  # Arms are significantly above shoulders
                        arms_lowered_threshold = 0.05  # Arms are near or below shoulders
                        
                        if current_position > arms_raised_threshold and rep_direction_up:
                            # Arms have been raised high enough
                            rep_direction_up = False
                            print("Arms raised position detected")
                        elif current_position < arms_lowered_threshold and not rep_direction_up:
                            # Arms have been lowered
                            rep_direction_up = True
                            current_rep += 1
                            print(f"Rep {current_rep} completed")
                    elif exercise_name.lower() in ["jumping jacks"]:
                        # Define thresholds for jumping jack positions
                        jj_up_threshold = 0.9    # Threshold for the full jumping jack position
                        jj_down_threshold = 0.1  # Threshold for the rest position
                        
                        if current_position >= jj_up_threshold and rep_direction_up:
                            # Person is in full jumping jack position (arms up, legs spread)
                            rep_direction_up = False
                            print("Jumping jack up position detected")
                        elif current_position <= jj_down_threshold and not rep_direction_up:
                            # Person has returned to rest position
                            rep_direction_up = True
                            current_rep += 1
                            print(f"Jumping jack rep {current_rep} completed")
                    else:
                        # Keep original rep detection for other exercises
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