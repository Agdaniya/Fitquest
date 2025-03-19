import os
import subprocess
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
import threading
import time

app = Flask(__name__)
CORS(app)  # This already adds CORS headers to all responses

# Get the correct absolute path for tracker.py
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  
tracker_path = os.path.join(BASE_DIR, "tracker.py")  

# Store the currently running process
current_process = None

# Store event listeners for SSE
exercise_completed_callbacks = []

@app.route('/start-camera', methods=['POST'])
def start_camera():
    """Starts the camera in test mode (no tracking)."""
    global current_process
    try:
        # Kill any existing process
        if current_process and current_process.poll() is None:
            current_process.terminate()
            print("Terminated existing process")
        
        print(f"Starting tracker.py at {tracker_path} in camera mode...")

        # Try to use the system's default Python interpreter first
        try:
            current_process = subprocess.Popen(
                ["python", tracker_path, "camera"], 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE
            )
        except FileNotFoundError:
            # If default "python" command isn't found, try using the specific path
            python_exe = "C:/Users/niyaa/AppData/Local/Programs/Python/Python311/python.exe"
            print(f"Using specific Python interpreter: {python_exe}")
            current_process = subprocess.Popen(
                [python_exe, tracker_path, "camera"], 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE
            )

        return jsonify({"message": "Camera process started"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/start-exercise', methods=['POST'])
def start_exercise():
    """Starts the tracking of a specific exercise."""
    global current_process
    try:
        # Kill any existing process
        if current_process and current_process.poll() is None:
            current_process.terminate()
            print("Terminated existing process")
            
        data = request.get_json()
        exercise_name = data.get("name")
        exercise_type = data.get("type")
        exercise_details = json.dumps(data.get("details", {}))

        if not exercise_name or not exercise_type:
            return jsonify({"error": "Missing exercise details"}), 400

        print(f"Starting tracker for {exercise_name} ({exercise_type})...")
        print(f"Details: {exercise_details}")
        
        # Try to use the system's default Python interpreter first
        try:
            current_process = subprocess.Popen(
                ["python", tracker_path, exercise_name, exercise_type, exercise_details], 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE
            )
        except FileNotFoundError:
            # If default "python" command isn't found, try using the specific path
            python_exe = "C:/Users/niyaa/AppData/Local/Programs/Python/Python311/python.exe"
            current_process = subprocess.Popen(
                [python_exe, tracker_path, exercise_name, exercise_type, exercise_details], 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE
            )

        return jsonify({"message": f"Tracking started for {exercise_name}"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/stop-tracking', methods=['POST'])
def stop_tracking():
    """Stops any currently running tracking process."""
    global current_process
    try:
        if current_process and current_process.poll() is None:
            current_process.terminate()
            print("Tracking process terminated")
            return jsonify({"message": "Tracking stopped"}), 200
        else:
            return jsonify({"message": "No active tracking to stop"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/exercise-completed', methods=['POST'])
def exercise_completed():
    """Endpoint to receive notification when an exercise is completed."""
    try:
        data = request.get_json()
        exercise_name = data.get("name")
        exercise_type = data.get("type")
        exercise_details = data.get("details", {})
        category = data.get("category", "")
        
        print(f"Exercise completed: {exercise_name} ({exercise_type})")
        
        # Format the exercise data
        exercise_data = {
            "exercise": exercise_name,
            "type": exercise_type,
            "category": category,
            "completed": True
        }
        
        # Add any additional details
        for key, value in exercise_details.items():
            if key not in exercise_data:
                exercise_data[key] = value
        
        # Send event to any connected clients
        for callback in exercise_completed_callbacks:
            try:
                callback(exercise_data)
            except Exception as e:
                print(f"Error in callback: {e}")
        
        return jsonify({"message": "Exercise completion recorded"}), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/events', methods=['GET'])
def events():
    """SSE endpoint for real-time updates."""
    def generate():
        # Create a new queue for this client
        queue = []
        
        def callback(data):
            queue.append(data)
        
        # Register callback
        exercise_completed_callbacks.append(callback)
        
        try:
            while True:
                # If we have data, send it
                if queue:
                    data = queue.pop(0)
                    yield f"data: {json.dumps(data)}\n\n"
                else:
                    # Send a heartbeat every 10 seconds
                    yield f"data: {json.dumps({'type': 'heartbeat'})}\n\n"
                
                # Sleep for a bit to avoid spinning
                time.sleep(0.5)
        finally:
            # Remove callback when client disconnects
            if callback in exercise_completed_callbacks:
                exercise_completed_callbacks.remove(callback)
    
    return app.response_class(
        generate(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive'
            # CORS headers are handled by Flask-CORS, don't add them manually here
        }
    )

# Remove this decorator as Flask-CORS already handles CORS
# @app.after_request
# def add_cors_headers(response):
#     """Manually add CORS headers to responses."""
#     response.headers.add("Access-Control-Allow-Origin", "*")  
#     response.headers.add("Access-Control-Allow-Headers", "Content-Type,Authorization")
#     response.headers.add("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
#     return response


if __name__ == '__main__':
    print(f"Starting Flask server on port 5001")
    print(f"Tracker path: {tracker_path}")
    app.run(port=5001, debug=True)