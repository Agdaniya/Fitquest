from flask import Flask, jsonify, send_from_directory
import subprocess
import threading
import traceback
import os
from flask_cors import CORS

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app, resources={r"/*": {"origins": "http://localhost:8000"}})

jumping_jack_count = 0
arm_raise_count = 0
arm_circle_count = 0
jumping_jack_tracking_process = None
arm_raise_tracking_process = None
arm_circle_tracking_process = None
is_jumping_jack_tracking = False
is_arm_raise_tracking = False
is_arm_circle_tracking = False

def run_tracking_script(script_name, count_variable):
    global is_jumping_jack_tracking, is_arm_raise_tracking,is_arm_circle_tracking
    try:
        print(f"Starting {script_name} tracking script...")
        script_path = os.path.join(os.path.dirname(__file__), f'{script_name}.py')
        print(f"Script path: {script_path}")
        
        process = subprocess.Popen(['python', script_path], 
                                   stdout=subprocess.PIPE, 
                                   stderr=subprocess.PIPE, 
                                   universal_newlines=True)
        print(f"Tracking process PID: {process.pid}")
        
        if script_name == 'jumpingjacks':
            is_jumping_jack_tracking = True
        elif script_name == 'armraises':
            is_arm_raise_tracking = True
        elif script_name == 'armcircle':
            is_arm_circle_tracking = True
        
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                print(f"Tracking output: {output.strip()}")
                if script_name == 'jumpingjacks' and output.startswith('jumping jack Count:'):
                    new_count = int(output.split(':')[1].strip())
                    globals()[count_variable] = new_count
                    print(f"Updated jumping jack count: {globals()[count_variable]}")
                elif script_name == 'armraises' and output.startswith('Arm Raises Count:'):
                    new_count = int(output.split(':')[1].strip())
                    globals()[count_variable] = new_count
                    print(f"Updated arm raise count: {globals()[count_variable]}")
                elif script_name == 'armcircle' and output.startswith('Arm circle Count:'):
                    new_count = int(output.split(':')[1].strip())
                    globals()[count_variable] = new_count
                    print(f"Updated arm circle count: {globals()[count_variable]}")
        
        rc = process.poll()
        if script_name == 'jumpingjacks':
            is_jumping_jack_tracking = False
        elif script_name == 'armraises':
            is_arm_raise_tracking = False
        elif script_name == 'armcircle':
            is_arm_circle_tracking = False
        print(f"Tracking stopped with return code {rc}")
        
        error_output = process.stderr.read()
        if error_output:
            print(f"Tracking script error: {error_output}")
    except Exception as e:
        print(f"Error in run_tracking_script: {str(e)}")
        print(traceback.format_exc())
        if script_name == 'jumpingjacks':
            is_jumping_jack_tracking = False
        elif script_name == 'armraises':
            is_arm_raise_tracking = False
        elif script_name == 'armcircle':
            is_arm_circle_tracking = False

@app.route('/track/start-jumping-jacks', methods=['POST'])
def start_jumping_jacks():
    global jumping_jack_tracking_process, is_jumping_jack_tracking
    try:
        if not is_jumping_jack_tracking:
            tracking_thread = threading.Thread(target=run_tracking_script, args=('jumpingjacks', 'jumping_jack_count'))
            tracking_thread.start()
            print("Jumping jacks tracking thread started")
            return jsonify({"status": "started"})
        return jsonify({"status": "already_running"})
    except Exception as e:
        print(f"Error in start_jumping_jacks: {str(e)}")
        print(traceback.format_exc())
        is_jumping_jack_tracking = False
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/track/start-arm-raises', methods=['POST'])
def start_arm_raises():
    global arm_raise_tracking_process, is_arm_raise_tracking
    try:
        if not is_arm_raise_tracking:
            tracking_thread = threading.Thread(target=run_tracking_script, args=('armraises', 'arm_raise_count'))
            tracking_thread.start()
            print("arm raises tracking thread started")
            return jsonify({"status": "started"})
        return jsonify({"status": "already_running"})
    except Exception as e:
        print(f"Error in start_arm_raises: {str(e)}")
        print(traceback.format_exc())
        is_arm_raise_tracking = False
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/track/start-arm-circle', methods=['POST'])
def start_arm_circle():
    global arm_circle_tracking_process, is_arm_circle_tracking
    try:
        if not is_arm_circle_tracking:
            tracking_thread = threading.Thread(target=run_tracking_script, args=('armcircle', 'arm_circle_count'))
            tracking_thread.start()
            print("arm circle tracking thread started")
            return jsonify({"status": "started"})
        return jsonify({"status": "already_running"})
    except Exception as e:
        print(f"Error in start_arm_circle: {str(e)}")
        print(traceback.format_exc())
        is_arm_circle_tracking = False
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/track/stop-jumping-jacks', methods=['POST'])
def stop_jumping_jacks():
    global is_jumping_jack_tracking
    is_jumping_jack_tracking = False
    return jsonify({"status": "stopped"})

@app.route('/track/stop-arm-raises', methods=['POST'])
def stop_arm_raises():
    global is_arm_raise_tracking
    is_arm_raise_tracking = False
    return jsonify({"status": "stopped"})

@app.route('/track/stop-arm-circle', methods=['POST'])
def stop_arm_circle():
    global is_arm_circle_tracking
    is_arm_circle_tracking = False
    return jsonify({"status": "stopped"})


@app.route('/track/get-jumping-jack-count')
def get_jumping_jack_count():
    global jumping_jack_count, is_jumping_jack_tracking
    return jsonify({
        "count": jumping_jack_count,
        "status": "running" if is_jumping_jack_tracking else "stopped"
    })

@app.route('/track/get-arm-raise-count')
def get_arm_raise_count():
    global arm_raise_count, is_arm_raise_tracking
    return jsonify({
        "count": arm_raise_count,
        "status": "running" if is_arm_raise_tracking else "stopped"
    })

@app.route('/track/get-arm-circle-count')
def get_arm_circle_count():
    global arm_circle_count, is_arm_circle_tracking
    return jsonify({
        "count": arm_circle_count,
        "status": "running" if is_arm_circle_tracking else "stopped"
    })

@app.route('/track/reset-jumping-jacks', methods=['POST'])
def reset_jumping_jacks():
    global jumping_jack_count
    jumping_jack_count = 0
    print("Jumping jack count reset to 0")
    return jsonify({"status": "reset"})

@app.route('/track/reset-arm-raises', methods=['POST'])
def resetl_arm_raises():
    global arm_raise_count
    arm_raise_count = 0
    print(" arm raise count reset to 0")
    return jsonify({"status": "reset"})

@app.route('/track/reset-arm-circle', methods=['POST'])
def reset_arm_circle():
    global arm_circle_count
    arm_circle_count = 0
    print("arm circle count reset to 0")
    return jsonify({"status": "reset"})

if __name__ == '__main__':
    print("Starting Flask app...")
    app.run(debug=True, port=5000)