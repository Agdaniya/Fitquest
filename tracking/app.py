from flask import Flask, jsonify, request
import subprocess
import threading
import traceback
import os
from flask_cors import CORS
import joblib
import numpy as np
from sklearn.preprocessing import StandardScaler

base_dir = os.path.dirname(os.path.abspath(__file__))

model_path = os.path.join(base_dir, '..', 'ml', 'models', 'best_fitness_model.pkl')
scaler_path = os.path.join(base_dir, '..', 'ml', 'models', 'scaler.pkl')

model = joblib.load(model_path)
scaler = joblib.load(scaler_path)

app = Flask(__name__)
CORS(app, resources={
    r"/*": {
        "origins": ["http://localhost:8000", "http://127.0.0.1:8000"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', 'http://localhost:8000')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response

# Exercise tracking variables
exercise_counts = {
    "jumping_jacks": 0,
    "arm_raises": 0,
    "arm_circles": 0,
    "deadlifts": 0,
    "bench_press": 0,
    "bridges": 0
}

exercise_tracking_status = {key: False for key in exercise_counts}

def run_tracking_script(script_name):
    global exercise_tracking_status
    try:
        script_path = os.path.join(os.path.dirname(__file__), f'{script_name}.py')
        process = subprocess.Popen(['python', script_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        
        exercise_tracking_status[script_name] = True
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output and output.startswith(f'{script_name} Count:'):
                new_count = int(output.split(':')[1].strip())
                exercise_counts[script_name] = new_count
                print(f"Updated {script_name} count: {exercise_counts[script_name]}")
        
        exercise_tracking_status[script_name] = False
        error_output = process.stderr.read()
        if error_output:
            print(f"{script_name} script error: {error_output}")
    except Exception as e:
        print(f"Error in run_tracking_script ({script_name}): {str(e)}")
        print(traceback.format_exc())
        exercise_tracking_status[script_name] = False

# Route for starting and stopping exercise tracking
@app.route('/track/<action>/<exercise>', methods=['POST', 'OPTIONS'])
def track_exercise(action, exercise):
    if request.method == 'OPTIONS':
        return '', 204
    
    if exercise in exercise_counts:
        if action == "start" and not exercise_tracking_status[exercise]:
            tracking_thread = threading.Thread(target=run_tracking_script, args=(exercise,))
            tracking_thread.start()
            return jsonify({"status": "started"})
        elif action == "stop":
            exercise_tracking_status[exercise] = False
            return jsonify({"status": "stopped"})
        
    return jsonify({"status": "invalid_action_or_exercise"})

# Route for getting and resetting exercise counts
@app.route('/track/<action>/<exercise>', methods=['GET', 'POST', 'OPTIONS'])
def manage_exercise_count(action, exercise):
    if request.method == 'OPTIONS':
        return '', 204
    
    if exercise in exercise_counts:
        if action == "get":
            return jsonify({
                "count": exercise_counts[exercise],
                "status": "running" if exercise_tracking_status[exercise] else "stopped"
            })
        elif action == "reset":
            exercise_counts[exercise] = 0
            return jsonify({"status": "reset"})
    
    return jsonify({"status": "invalid_action_or_exercise"})

@app.route('/predict-fitness-level', methods=['POST', 'OPTIONS'])
def predict_fitness_level():
    if request.method == 'OPTIONS':
        return '', 204
    
    try:
        if not request.is_json:
            return jsonify({'error': 'Request must be JSON'}), 400
            
        data = request.json
        required_keys = ['age', 'height', 'weight', 'activityLevel', 'gender']
        for key in required_keys:
            if key not in data:
                return jsonify({'error': f'Missing required key: {key}'}), 400
                
        age = int(data['age'])
        height = float(data['height'])
        weight = float(data['weight'])
        activity_level = float(data['activityLevel'])
        gender = data['gender']
        
        height_meters = height / 100
        bmi = weight / (height_meters ** 2)
        
        gender_numeric = 1 if gender == 'Male' else 0

        features = np.array([[age, bmi, activity_level, gender_numeric]])
        features_scaled = scaler.transform(features)

        prediction = model.predict(features_scaled)
        fitness_level = ["Beginner", "Intermediate", "Advanced"][prediction[0]]
        
        return jsonify({'fitness_level': fitness_level})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
