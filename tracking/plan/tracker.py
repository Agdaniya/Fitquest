import cv2
import mediapipe as mp
import numpy as np
import time
from flask import Flask, request, jsonify, Response
import threading
import json

# MediaPipe pose solution setup
mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose

# Global variables to track exercise state
current_exercise = None
current_set = 0
current_rep = 0
total_sets = 0
total_reps = 0
rest_time = 0
exercise_state = "waiting"  # waiting, active, resting, completed
exercise_queue = []

# Camera setup
cap = None
camera_active = False
camera_thread = None
stop_camera_event = threading.Event()

def initialize_camera():
    global cap
    cap = cv2.VideoCapture(0)
    return cap.isOpened()

def release_camera():
    global cap, camera_active
    if cap:
        cap.release()
    camera_active = False
    cv2.destroyAllWindows()

def count_repetitions(pose_landmarks, exercise_name):
    """
    Count repetitions based on exercise type and pose landmarks
    Returns True when a rep is completed
    """
    global current_rep
    
    if exercise_name.lower() == "jumping jacks":
        # Get wrist and ankle landmarks
        left_wrist = pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_WRIST]
        right_wrist = pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_WRIST]
        left_ankle = pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_ANKLE]
        right_ankle = pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_ANKLE]
        
        # Calculate distances for arm and leg spread
        wrist_distance = np.sqrt((left_wrist.x - right_wrist.x)**2 + (left_wrist.y - right_wrist.y)**2)
        ankle_distance = np.sqrt((left_ankle.x - right_ankle.x)**2 + (left_ankle.y - right_ankle.y)**2)
        
        # Simple state machine for jumping jack
        if not hasattr(count_repetitions, "jack_state"):
            count_repetitions.jack_state = "down"
            
        if count_repetitions.jack_state == "down" and wrist_distance > 0.4 and ankle_distance > 0.3:
            count_repetitions.jack_state = "up"
        elif count_repetitions.jack_state == "up" and wrist_distance < 0.2 and ankle_distance < 0.2:
            count_repetitions.jack_state = "down"
            return True  # Count a rep
            
    elif exercise_name.lower() == "march in place":
        # Get knee landmarks
        left_knee = pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_KNEE]
        right_knee = pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_KNEE]
        left_hip = pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_HIP]
        right_hip = pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_HIP]
        
        # Check knee height relative to hip
        if not hasattr(count_repetitions, "march_state"):
            count_repetitions.march_state = "neutral"
            count_repetitions.last_knee = "none"
            
        # Check if left knee is raised
        if count_repetitions.march_state == "neutral" and left_knee.y < left_hip.y - 0.1 and count_repetitions.last_knee != "left":
            count_repetitions.march_state = "left_up"
            count_repetitions.last_knee = "left"
            return True  # Count a rep
        # Check if right knee is raised
        elif count_repetitions.march_state == "neutral" and right_knee.y < right_hip.y - 0.1 and count_repetitions.last_knee != "right":
            count_repetitions.march_state = "right_up"
            count_repetitions.last_knee = "right"
            return True  # Count a rep
        # Reset state when both knees are down
        elif (left_knee.y > left_hip.y - 0.05) and (right_knee.y > right_hip.y - 0.05):
            count_repetitions.march_state = "neutral"
            
    # Default case - no rep counted
    return False

def camera_loop():
    global current_exercise, current_set, current_rep, exercise_state, total_sets, total_reps, rest_time, camera_active, exercise_queue
    
    camera_active = True
    
    # Set up MediaPipe Pose
    with mp_pose.Pose(
        min_detection_confidence=0.7,
        min_tracking_confidence=0.7) as pose:
        
        last_rep_time = time.time()
        rest_start_time = None
        
        while not stop_camera_event.is_set() and camera_active:
            # If no exercise is set, wait
            if not current_exercise:
                time.sleep(0.1)
                continue
                
            # Check camera status
            if not cap.isOpened():
                if not initialize_camera():
                    print("Failed to open camera")
                    camera_active = False
                    break
            
            # Read frame
            success, image = cap.read()
            if not success:
                print("Failed to read frame")
                continue
                
            # Convert image and process with MediaPipe
            image = cv2.flip(image, 1)  # Mirror image for better UX
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            results = pose.process(image_rgb)
            
            # Draw pose landmarks on the image
            if results.pose_landmarks:
                mp_drawing.draw_landmarks(
                    image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
                
                # State machine for exercise tracking
                if exercise_state == "active":
                    # Count reps or track time based on exercise type
                    if current_exercise.get("type") == "Time":
                        # Time-based exercise
                        elapsed_time = time.time() - last_rep_time
                        # Display remaining time
                        time_left = int(float(current_exercise.get("time", 30)) - elapsed_time)
                        cv2.putText(image, f"Time left: {time_left}s", (50, 50), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                        
                        # Check if time is up
                        if elapsed_time >= float(current_exercise.get("time", 30)):
                            current_set += 1
                            if current_set >= int(current_exercise.get("sets", 1)):
                                # Exercise completed
                                print(f"Exercise {current_exercise['name']} completed!")
                                exercise_state = "completed"
                                # Move to next exercise if available
                                if exercise_queue:
                                    current_exercise = exercise_queue.pop(0)
                                    current_set = 0
                                    current_rep = 0
                                    total_sets = int(current_exercise.get("sets", 1))
                                    total_reps = int(current_exercise.get("reps", 10))
                                    rest_time = int(current_exercise.get("rest", 0))
                                    exercise_state = "active"
                                    last_rep_time = time.time()
                                else:
                                    current_exercise = None
                            else:
                                # Set completed, start rest
                                print(f"Set {current_set}/{total_sets} completed. Resting...")
                                exercise_state = "resting"
                                rest_start_time = time.time()
                    else:
                        # Rep-based exercise
                        if count_repetitions(results.pose_landmarks, current_exercise.get("name", "")):
                            current_rep += 1
                            print(f"Rep {current_rep}/{total_reps} completed")
                            
                            # Check if set is completed
                            if current_rep >= total_reps:
                                current_set += 1
                                current_rep = 0
                                
                                # Check if exercise is completed
                                if current_set >= total_sets:
                                    print(f"Exercise {current_exercise['name']} completed!")
                                    exercise_state = "completed"
                                    # Move to next exercise if available
                                    if exercise_queue:
                                        current_exercise = exercise_queue.pop(0)
                                        current_set = 0
                                        current_rep = 0
                                        total_sets = int(current_exercise.get("sets", 1))
                                        total_reps = int(current_exercise.get("reps", 10))
                                        rest_time = int(current_exercise.get("rest", 0))
                                        exercise_state = "active"
                                    else:
                                        current_exercise = None
                                else:
                                    # Set completed, start rest
                                    print(f"Set {current_set}/{total_sets} completed. Resting...")
                                    exercise_state = "resting"
                                    rest_start_time = time.time()
                
                elif exercise_state == "resting":
                    # Display rest countdown
                    elapsed_rest = time.time() - rest_start_time
                    rest_left = max(0, int(rest_time - elapsed_rest))
                    cv2.putText(image, f"Rest: {rest_left}s", (50, 50), 
                               cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                    
                    # Check if rest is over
                    if elapsed_rest >= rest_time:
                        exercise_state = "active"
                        last_rep_time = time.time()
                
                elif exercise_state == "completed":
                    cv2.putText(image, "Exercise completed!", (50, 50), 
                               cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    
            # Display exercise info on frame
            if current_exercise:
                cv2.putText(image, f"Exercise: {current_exercise.get('name', '')}", (10, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                cv2.putText(image, f"Set: {current_set + 1}/{total_sets}", (10, 60), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                cv2.putText(image, f"Rep: {current_rep}/{total_reps}", (10, 90), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                cv2.putText(image, f"State: {exercise_state}", (10, 120), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            # Show image
            cv2.imshow('MediaPipe Pose', image)
            if cv2.waitKey(5) & 0xFF == 27:  # ESC key to terminate
                break
                
    release_camera()

# API endpoints to control tracking
def start_tracking(exercise_list):
    global current_exercise, camera_thread, camera_active, stop_camera_event, exercise_queue, current_set, current_rep, total_sets, total_reps, rest_time, exercise_state
    
    if not exercise_list:
        return {"status": "error", "message": "No exercises provided"}
    
    # Initialize first exercise
    current_exercise = exercise_list[0]
    exercise_queue = exercise_list[1:] if len(exercise_list) > 1 else []
    
    # Set up exercise tracking variables
    current_set = 0
    current_rep = 0
    total_sets = int(current_exercise.get("sets", 1))
    total_reps = int(current_exercise.get("reps", 10))
    rest_time = int(current_exercise.get("rest", 0))
    exercise_state = "active"
    
    # Start camera if not already running
    if not camera_active:
        if not initialize_camera():
            return {"status": "error", "message": "Failed to initialize camera"}
            
        stop_camera_event.clear()
        camera_thread = threading.Thread(target=camera_loop)
        camera_thread.daemon = True
        camera_thread.start()
    
    return {"status": "started", "exercise": current_exercise.get("name", "")}

def stop_tracking():
    global current_exercise, camera_active, stop_camera_event
    
    # Stop the camera loop
    stop_camera_event.set()
    
    # Clear current exercise
    current_exercise = None
    exercise_state = "waiting"
    
    return {"status": "stopped"}

def get_progress():
    if not current_exercise:
        return {"status": "inactive"}
        
    total_exercises = len(exercise_queue) + 1
    completed_exercises = 0
    
    # Calculate progress within current exercise
    if exercise_state == "completed":
        current_progress = 1.0
    else:
        # Set progress
        set_progress = current_set / total_sets
        
        # Rep progress within the current set
        rep_progress = 0
        if total_reps > 0 and exercise_state == "active":
            rep_progress = (current_rep / total_reps) * (1.0 / total_sets)
        
        current_progress = set_progress + rep_progress
    
    return {
        "status": exercise_state,
        "current_exercise": current_exercise.get("name", "") if current_exercise else None,
        "set": current_set + 1,
        "total_sets": total_sets,
        "rep": current_rep,
        "total_reps": total_reps,
        "progress": current_progress,
        "remaining_exercises": len(exercise_queue),
        "exercise_state": exercise_state
    }

# These functions will be imported by the Flask server