from flask import Flask, request, jsonify
from flask_cors import CORS
import subprocess
import json

app = Flask(__name__)
CORS(app)  # Enable CORS

# ✅ New route to start the camera
@app.route('/start-camera', methods=['POST'])
def start_camera():
    try:
        # OpenCV-based tracking should be triggered here
        subprocess.Popen(["python", "tracker.py", "camera"])
        return jsonify({"message": "Camera started"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ✅ Existing route to start exercise tracking
@app.route('/start-exercise', methods=['POST'])
def start_exercise():
    try:
        data = request.json
        exercise_name = data.get("name")
        exercise_type = data.get("type")
        exercise_details = json.dumps(data.get("details"))

        if not exercise_name or not exercise_type:
            return jsonify({"error": "Missing exercise details"}), 400

        # Start tracker.py with exercise details
        subprocess.Popen(["python", "tracker.py", exercise_name, exercise_type, exercise_details])
        
        return jsonify({"message": f"Tracking started for {exercise_name}"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
