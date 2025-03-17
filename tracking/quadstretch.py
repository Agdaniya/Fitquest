import cv2
import mediapipe as mp
import sys
import time
import numpy as np

print("Standing Quad Stretch Tracker started")  # Debug print

# Initialize MediaPipe pose solution
mp_pose = mp.solutions.pose
pose = mp_pose.Pose()

# Initialize MediaPipe drawing utils
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles

# Start video capture (0 for webcam, or provide a video file path)
print("Attempting to open camera...")  # Debug print
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Error: Could not open camera.")
    print("Available cameras:")
    for i in range(10):  # Check first 10 camera indices
        temp_cap = cv2.VideoCapture(i)
        if temp_cap.isOpened():
            print(f"Camera index {i} is available")
            temp_cap.release()
    sys.exit(1)

print("Camera opened successfully")
# Get the camera properties
frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
fps = int(cap.get(cv2.CAP_PROP_FPS))

print(f"Camera properties: {frame_width}x{frame_height} @ {fps}fps")  # Debug print

# Try to get a frame
ret, frame = cap.read()
if not ret:
    print("Failed to grab frame from camera")
    cap.release()
    sys.exit(1)

print("Successfully grabbed a frame from camera")  # Debug print

# Set up display window
cv2.namedWindow('Standing Quad Stretch Tracker', cv2.WINDOW_NORMAL)
screen = cv2.getWindowImageRect('Standing Quad Stretch Tracker')
screen_width = screen[2]
screen_height = screen[3]

print(f"Screen resolution: {screen_width}x{screen_height}")  # Debug print

# Set the window to fullscreen
cv2.setWindowProperty('Standing Quad Stretch Tracker', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

# Initialize variables to track the state and counts
quad_stretch_active = False
left_count = 0
right_count = 0
total_count = 0

# Set a confidence threshold for pose detection
confidence_threshold = 0.5  # Adjust this as needed

# Timer variables
stretch_start_time = 0
time_in_position = 0
required_time = 20  # 20 seconds required to count as a complete stretch
current_stretch_leg = "none"  # "left", "right", or "none"

print("Standing Quad Stretch Tracker initialized")  # Debug print

# Custom connection list for legs and hips only
leg_connections = [
    (mp_pose.PoseLandmark.LEFT_HIP, mp_pose.PoseLandmark.LEFT_KNEE),
    (mp_pose.PoseLandmark.LEFT_KNEE, mp_pose.PoseLandmark.LEFT_ANKLE),
    (mp_pose.PoseLandmark.LEFT_ANKLE, mp_pose.PoseLandmark.LEFT_FOOT_INDEX),
    (mp_pose.PoseLandmark.LEFT_ANKLE, mp_pose.PoseLandmark.LEFT_HEEL),
    (mp_pose.PoseLandmark.LEFT_HEEL, mp_pose.PoseLandmark.LEFT_FOOT_INDEX),
    (mp_pose.PoseLandmark.RIGHT_HIP, mp_pose.PoseLandmark.RIGHT_KNEE),
    (mp_pose.PoseLandmark.RIGHT_KNEE, mp_pose.PoseLandmark.RIGHT_ANKLE),
    (mp_pose.PoseLandmark.RIGHT_ANKLE, mp_pose.PoseLandmark.RIGHT_FOOT_INDEX),
    (mp_pose.PoseLandmark.RIGHT_ANKLE, mp_pose.PoseLandmark.RIGHT_HEEL),
    (mp_pose.PoseLandmark.RIGHT_HEEL, mp_pose.PoseLandmark.RIGHT_FOOT_INDEX),
    (mp_pose.PoseLandmark.LEFT_HIP, mp_pose.PoseLandmark.RIGHT_HIP)
]

# Set of leg and hip landmarks to show
leg_landmarks = {
    mp_pose.PoseLandmark.LEFT_HIP,
    mp_pose.PoseLandmark.LEFT_KNEE,
    mp_pose.PoseLandmark.LEFT_ANKLE,
    mp_pose.PoseLandmark.LEFT_HEEL,
    mp_pose.PoseLandmark.LEFT_FOOT_INDEX,
    mp_pose.PoseLandmark.RIGHT_HIP,
    mp_pose.PoseLandmark.RIGHT_KNEE,
    mp_pose.PoseLandmark.RIGHT_ANKLE,
    mp_pose.PoseLandmark.RIGHT_HEEL,
    mp_pose.PoseLandmark.RIGHT_FOOT_INDEX
}

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        print("Failed to capture frame")  # Debug print
        continue  # Try to capture the next frame instead of breaking

    # Get the current time
    current_time = time.time()
    
    # Resize the frame to fit the screen
    frame = cv2.resize(frame, (screen_width, screen_height))

    # Convert the frame to RGB
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Process the frame to detect the pose
    results = pose.process(rgb_frame)

    # Create a blank image for drawing leg landmarks only
    if results.pose_landmarks:
        # Draw only selected landmarks and connections
        annotated_frame = frame.copy()
        
        # Draw only leg connections
        connections_to_draw = [(p1, p2) for p1, p2 in leg_connections]
        
        # Draw connections
        for connection in connections_to_draw:
            start_point = results.pose_landmarks.landmark[connection[0]]
            end_point = results.pose_landmarks.landmark[connection[1]]
            
            # Check if the landmarks are visible
            if (start_point.visibility > confidence_threshold and 
                end_point.visibility > confidence_threshold):
                
                # Convert normalized coordinates to pixel coordinates
                start_x = int(start_point.x * frame.shape[1])
                start_y = int(start_point.y * frame.shape[0])
                end_x = int(end_point.x * frame.shape[1])
                end_y = int(end_point.y * frame.shape[0])
                
                # Draw the line
                cv2.line(annotated_frame, (start_x, start_y), (end_x, end_y), (0, 0, 255), 2)
        
        # Draw landmarks
        for landmark_id in leg_landmarks:
            landmark = results.pose_landmarks.landmark[landmark_id]
            if landmark.visibility > confidence_threshold:
                x = int(landmark.x * frame.shape[1])
                y = int(landmark.y * frame.shape[0])
                cv2.circle(annotated_frame, (x, y), 5, (0, 255, 0), -1)
        
        frame = annotated_frame
        
        # Get the landmarks for hips, knees, ankles, and feet
        landmarks = results.pose_landmarks.landmark
        left_hip = landmarks[mp_pose.PoseLandmark.LEFT_HIP]
        right_hip = landmarks[mp_pose.PoseLandmark.RIGHT_HIP]
        left_knee = landmarks[mp_pose.PoseLandmark.LEFT_KNEE]
        right_knee = landmarks[mp_pose.PoseLandmark.RIGHT_KNEE]
        left_ankle = landmarks[mp_pose.PoseLandmark.LEFT_ANKLE]
        right_ankle = landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE]
        left_foot_index = landmarks[mp_pose.PoseLandmark.LEFT_FOOT_INDEX]
        right_foot_index = landmarks[mp_pose.PoseLandmark.RIGHT_FOOT_INDEX]
        
        # Check if key points are visible with sufficient confidence
        left_leg_visible = (left_hip.visibility > confidence_threshold and 
                           left_knee.visibility > confidence_threshold and 
                           left_ankle.visibility > confidence_threshold)
        
        right_leg_visible = (right_hip.visibility > confidence_threshold and 
                            right_knee.visibility > confidence_threshold and 
                            right_ankle.visibility > confidence_threshold)
        
        if left_leg_visible and right_leg_visible:
            # Calculate distances between feet and hips
            # For quad stretch, one foot should be close to the hip
            left_foot_to_hip_distance = np.sqrt(
                (left_foot_index.x - left_hip.x)**2 + 
                (left_foot_index.y - left_hip.y)**2
            )
            
            right_foot_to_hip_distance = np.sqrt(
                (right_foot_index.x - right_hip.x)**2 + 
                (right_foot_index.y - right_hip.y)**2
            )
            
            # Threshold for detecting foot near hip
            foot_hip_threshold = 0.2  # Adjust as needed
            
            # LEFT QUAD STRETCH: Right foot near ground, left foot near hip
            left_quad_stretch = (
                left_foot_to_hip_distance < foot_hip_threshold and
                right_foot_index.y > right_knee.y  # Right foot below knee (standing)
            )
            
            # RIGHT QUAD STRETCH: Left foot near ground, right foot near hip
            right_quad_stretch = (
                right_foot_to_hip_distance < foot_hip_threshold and
                left_foot_index.y > left_knee.y  # Left foot below knee (standing)
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
                if time_in_position >= required_time:
                    left_count += 1
                    total_count += 1
                    print(f"Left Quad Stretch completed: {left_count}, Total: {total_count}")
                    # Reset the timer for the next count
                    stretch_start_time = current_time
                
            elif right_quad_stretch and not left_quad_stretch:
                if current_stretch_leg != "right":
                    current_stretch_leg = "right"
                    stretch_start_time = current_time
                    quad_stretch_active = True
                    print("Right quad stretch position detected")
                
                # Update time in position
                time_in_position = current_time - stretch_start_time
                
                # Check if we've held the position long enough
                if time_in_position >= required_time:
                    right_count += 1
                    total_count += 1
                    print(f"Right Quad Stretch completed: {right_count}, Total: {total_count}")
                    # Reset the timer for the next count
                    stretch_start_time = current_time
            
            else:
                if quad_stretch_active:
                    print("Quad stretch position lost")
                quad_stretch_active = False
                current_stretch_leg = "none"
                time_in_position = 0
        
        else:
            if quad_stretch_active:
                print("Leg visibility lost")
            quad_stretch_active = False
            current_stretch_leg = "none"
            time_in_position = 0
        
        # Display the status on the frame
        font_scale = 0.7
        text_thickness = 2
        
        # Display time held in position
        if current_stretch_leg != "none":
            time_text = f"Hold Time: {time_in_position:.1f} / {required_time} seconds"
            cv2.putText(frame, time_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, font_scale, (255, 255, 255), text_thickness, cv2.LINE_AA)
            
            # Add a progress bar
            progress = min(time_in_position / required_time, 1.0)
            bar_width = int(200 * progress)
            cv2.rectangle(frame, (10, 40), (210, 60), (50, 50, 50), -1)
            cv2.rectangle(frame, (10, 40), (10 + bar_width, 60), (0, 255, 0), -1)
        
        # Display which leg is active
        if current_stretch_leg == "left":
            cv2.putText(frame, "Left Quad Stretch Active", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, font_scale, (0, 255, 255), text_thickness, cv2.LINE_AA)
        elif current_stretch_leg == "right":
            cv2.putText(frame, "Right Quad Stretch Active", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, font_scale, (0, 255, 255), text_thickness, cv2.LINE_AA)
        else:
            cv2.putText(frame, "No Stretch Detected", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, font_scale, (0, 255, 255), text_thickness, cv2.LINE_AA)
        
        # Display counts
        cv2.putText(frame, f'Left Stretches: {left_count}', (10, 120), cv2.FONT_HERSHEY_SIMPLEX, font_scale, (255, 255, 255), text_thickness, cv2.LINE_AA)
        cv2.putText(frame, f'Right Stretches: {right_count}', (10, 150), cv2.FONT_HERSHEY_SIMPLEX, font_scale, (255, 255, 255), text_thickness, cv2.LINE_AA)
        cv2.putText(frame, f'Total Completed: {total_count}', (10, 180), cv2.FONT_HERSHEY_SIMPLEX, font_scale, (255, 255, 255), text_thickness, cv2.LINE_AA)
    
    else:
        print("No pose detected")  # Debug print
    
    # Add "Press 'q' to exit" text
    cv2.putText(frame, "Press 'q' to exit", (10, screen_height - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)
        
    # Display the frame
    cv2.imshow('Standing Quad Stretch Tracker', frame)

    # Break the loop on 'q' key press
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release the capture and close the window
cap.release()
cv2.destroyAllWindows()

print("Standing Quad Stretch Tracker ended")  # Debug print