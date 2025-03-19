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
        # Get landmarks needed for tracking
        left_hip = landmarks[mp_pose.PoseLandmark.LEFT_HIP.value]
        right_hip = landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value]
        left_knee = landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value]
        right_knee = landmarks[mp_pose.PoseLandmark.RIGHT_KNEE.value]
        left_ankle = landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value]
        right_ankle = landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE.value]
        
        # Calculate the horizontal distance between hip and ankle for each leg
        left_hip_ankle_distance = abs(left_ankle.x - left_hip.x)
        right_hip_ankle_distance = abs(right_ankle.x - right_hip.x)
        
        # Check if knees are relatively straight during the lift (not bent)
        left_knee_straight = abs(left_knee.y - ((left_hip.y + left_ankle.y) / 2)) < 0.05
        right_knee_straight = abs(right_knee.y - ((right_hip.y + right_ankle.y) / 2)) < 0.05
        
        # Create a combined metric for leg lift detection
        # If left leg is lifted properly, return a positive value
        # If right leg is lifted properly, return a negative value
        # If no lift is detected, return a value close to zero
        leg_lift_threshold = 0.15
        
        if left_hip_ankle_distance > leg_lift_threshold and left_knee_straight and right_hip_ankle_distance <= leg_lift_threshold:
            return left_hip_ankle_distance  # Positive value for left leg lift
        elif right_hip_ankle_distance > leg_lift_threshold and right_knee_straight and left_hip_ankle_distance <= leg_lift_threshold:
            return -right_hip_ankle_distance  # Negative value for right leg lift
        else:
            return 0.0 
    
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
        # Get landmarks needed for tracking
        left_hip = landmarks[mp_pose.PoseLandmark.LEFT_HIP.value]
        right_hip = landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value]
        
        # Calculate the midpoint between hips
        hip_midpoint_x = (left_hip.x + right_hip.x) / 2
        
        # Return the horizontal position of hip midpoint
        # This value changes significantly during side steps
        return hip_midpoint_x  # Position value that changes during side-to-side movement
        
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
   elif exercise_type.lower() in ["quad stretch", "quadstretch"]:
        # Get required landmarks
        left_hip = landmarks[mp_pose.PoseLandmark.LEFT_HIP.value]
        right_hip = landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value]
        left_knee = landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value]
        right_knee = landmarks[mp_pose.PoseLandmark.RIGHT_KNEE.value]
        left_foot_index = landmarks[mp_pose.PoseLandmark.LEFT_FOOT_INDEX.value]
        right_foot_index = landmarks[mp_pose.PoseLandmark.RIGHT_FOOT_INDEX.value]
        
        # Calculate distances between feet and hips for quad stretch detection
        left_foot_to_hip_distance = ((left_foot_index.x - left_hip.x)**2 + 
                                    (left_foot_index.y - left_hip.y)**2)**0.5
        
        right_foot_to_hip_distance = ((right_foot_index.x - right_hip.x)**2 + 
                                     (right_foot_index.y - right_hip.y)**2)**0.5
        
        # Create a dictionary with the necessary values for state tracking
        return {
            "left_foot_to_hip": left_foot_to_hip_distance,
            "right_foot_to_hip": right_foot_to_hip_distance,
            "left_foot_y": left_foot_index.y,
            "right_foot_y": right_foot_index.y,
            "left_knee_y": left_knee.y,
            "right_knee_y": right_knee.y
        }
    
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

    if exercise_name.lower() in ["quad stretch", "quadstretch"]:
    quad_stretch_active = False
    current_stretch_leg = "none"  # "left", "right", or "none"
    foot_hip_threshold = 0.2  # Threshold for foot-to-hip distance
    left_count = 0
    right_count = 0
    
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
                    elif workout_type == "reps" and exercise_name.lower() in ["quad stretch", "quadstretch"]:
                        # Get the data from count_reps
                        stretch_data = count_reps(landmarks, exercise_name)
                        
                        # Check for left quad stretch: Right foot near ground, left foot near hip
                        left_quad_stretch = (
                            stretch_data["left_foot_to_hip"] < foot_hip_threshold and
                            stretch_data["right_foot_y"] > stretch_data["right_knee_y"]  # Right foot below knee (standing)
                        )
                        
                        # Check for right quad stretch: Left foot near ground, right foot near hip
                        right_quad_stretch = (
                            stretch_data["right_foot_to_hip"] < foot_hip_threshold and
                            stretch_data["left_foot_y"] > stretch_data["left_knee_y"]  # Left foot below knee (standing)
                        )
                        
                        # Process the quad stretch detection
                        if left_quad_stretch and not right_quad_stretch:
                            if current_stretch_leg != "left":
                                current_stretch_leg = "left"
                                stretch_start_time = current_time
                                quad_stretch_active = True
                                print("Left quad stretch position detected")
                            
                            # Update time in position
                            time_in_position = current_time - stretch_start_time
                            
                            # Check if we've held the position long enough
                            if time_in_position >= duration:  # Use the duration as the required hold time
                                left_count += 1
                                current_rep += 0.5  # Count each side as half a rep
                                print(f"Left Quad Stretch completed: {left_count}")
                                # Reset the timer for the next count
                                stretch_start_time = current_time
                                current_stretch_leg = "none"  # Reset to detect a new stretch
                                
                        elif right_quad_stretch and not left_quad_stretch:
                            if current_stretch_leg != "right":
                                current_stretch_leg = "right"
                                stretch_start_time = current_time
                                quad_stretch_active = True
                                print("Right quad stretch position detected")
                            
                            # Update time in position
                            time_in_position = current_time - stretch_start_time
                            
                            # Check if we've held the position long enough
                            if time_in_position >= duration:  # Use the duration as the required hold time
                                right_count += 1
                                current_rep += 0.5  # Count each side as half a rep
                                print(f"Right Quad Stretch completed: {right_count}")
                                # Reset the timer for the next count
                                stretch_start_time = current_time
                                current_stretch_leg = "none"  # Reset to detect a new stretch
                    
                        else:
                            if quad_stretch_active:
                                print("Quad stretch position lost")
                            quad_stretch_active = False
                            current_stretch_leg = "none"
                        
                        # Display additional information for quad stretch
                        if current_stretch_leg != "none":
                            cv2.putText(frame, f"Hold Time: {time_in_position:.1f}/{duration}s", 
                                    (50, 300), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                            
                            # Add a progress bar
                            progress = min(time_in_position / duration, 1.0)
                            bar_width = int(200 * progress)
                            cv2.rectangle(frame, (50, 310), (250, 330), (50, 50, 50), -1)
                            cv2.rectangle(frame, (50, 310), (50 + bar_width, 330), (0, 255, 0), -1)
                        
                        cv2.putText(frame, f"Left: {left_count}, Right: {right_count}", (50, 350), 
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

                    # Add inside the start_tracking function where other exercise-specific logic is handled
                    elif exercise_name.lower() in ["side steps"]:
                        # Define thresholds for side step detection
                        center_position = None  # Will be set on first frame
                        side_step_threshold = 0.05  # Threshold for detecting a side step
                        in_step = False
                        step_direction = None
                        
                        # In the main tracking loop where landmarks are processed
                        if results.pose_landmarks:
                            landmarks = results.pose_landmarks.landmark
                            current_position = count_reps(landmarks, exercise_name)
                            
                            # Initialize center position if not set
                            if center_position is None:
                                center_position = current_position
                                print("Center position initialized")
                            
                            # Calculate position relative to center
                            relative_position = current_position - center_position
                            
                            # Step detection logic
                            if not in_step:
                                # Check if person has moved significantly to start a step
                                if abs(relative_position) > side_step_threshold:
                                    in_step = True
                                    step_direction = "right" if relative_position > 0 else "left"
                                    print(f"Starting step to the {step_direction}")
                            else:
                                # Check if person has moved back to center or to the opposite side
                                returned_to_center = abs(relative_position) < side_step_threshold / 2
                                opposite_direction = (step_direction == "right" and relative_position < -side_step_threshold) or \
                                                    (step_direction == "left" and relative_position > side_step_threshold)
                                
                                if returned_to_center or opposite_direction:
                                    in_step = False
                                    current_rep += 1
                                    print(f"Side step completed: {current_rep}")
                                    step_direction = None
                    # Inside the start_tracking function where the exercise-specific logic is handled
                    elif exercise_name.lower() in ["standing side leg lifts"]:
                        # Define thresholds for side leg lift detection
                        leg_lift_threshold = 0.15  # Threshold for detecting a leg lift
                        
                        # State tracking for leg lifts
                        if current_position > leg_lift_threshold and not rep_direction_up:
                            # Left leg is lifted and previously was down
                            rep_direction_up = True
                            print("Left leg lift detected")
                        elif current_position < -leg_lift_threshold and not rep_direction_up:
                            # Right leg is lifted and previously was down
                            rep_direction_up = True
                            print("Right leg lift detected")
                        elif abs(current_position) < 0.05 and rep_direction_up:
                            # Legs returned to normal position after being lifted
                            rep_direction_up = False
                            current_rep += 0.5  # Count each leg as half a rep
                            print(f"Leg lift completed - Current count: {current_rep}")
                            
                        # Additional display info can be added
                        leg_status = "Left leg up" if current_position > leg_lift_threshold else "Right leg up" if current_position < -leg_lift_threshold else "Standing"
                        cv2.putText(frame, f"Status: {leg_status}", (50, 350), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
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