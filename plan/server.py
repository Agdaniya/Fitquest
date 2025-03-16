import os
import subprocess
import json
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Get the correct absolute path for tracker.py
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  
tracker_path = os.path.join(BASE_DIR, "tracker.py")  

# Store the currently running process
current_process = None

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


@app.after_request
def add_cors_headers(response):
    """Manually add CORS headers to responses."""
    response.headers.add("Access-Control-Allow-Origin", "*")  
    response.headers.add("Access-Control-Allow-Headers", "Content-Type,Authorization")
    response.headers.add("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
    return response

if __name__ == '__main__':
    print(f"Starting Flask server on port 5001")
    print(f"Tracker path: {tracker_path}")
    app.run(port=5001, debug=True)