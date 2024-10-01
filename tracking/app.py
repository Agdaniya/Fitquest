from flask import Flask, jsonify, send_from_directory
import subprocess
import threading
import traceback
import os
from flask_cors import CORS

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app, resources={r"/*": {"origins": "http://localhost:8000"}})

jumping_jack_count = 0
tracking_process = None
is_tracking = False

def run_tracking_script():
    global jumping_jack_count, is_tracking, tracking_process
    try:
        print("Starting tracking script...")  # Debug print
        script_path = os.path.join(os.path.dirname(__file__), 'track.py')
        print(f"Script path: {script_path}")  # Debug print
        
        tracking_process = subprocess.Popen(['python', script_path], 
                                            stdout=subprocess.PIPE, 
                                            stderr=subprocess.PIPE, 
                                            universal_newlines=True)
        print(f"Tracking process PID: {tracking_process.pid}")  # Debug print
        
        is_tracking = True
        
        while True:
            output = tracking_process.stdout.readline()
            if output == '' and tracking_process.poll() is not None:
                break
            if output:
                print(f"Tracking output: {output.strip()}")  # Debug print
                if output.startswith('jumping jack Count:'):
                    jumping_jack_count = int(output.split(':')[1].strip())
                    print(f"Updated count: {jumping_jack_count}")  # Debug print
        
        rc = tracking_process.poll()
        is_tracking = False
        print(f"Tracking stopped with return code {rc}")  # Debug print
        
        # Check for any errors
        error_output = tracking_process.stderr.read()
        if error_output:
            print(f"Tracking script error: {error_output}")  # Debug print
    except Exception as e:
        print(f"Error in run_tracking_script: {str(e)}")
        print(traceback.format_exc())
        is_tracking = False

@app.route('/track/start-jumping-jacks', methods=['POST'])
def start_jumping_jacks():
    global tracking_process, is_tracking
    try:
        if not is_tracking:
            tracking_thread = threading.Thread(target=run_tracking_script)
            tracking_thread.start()
            print("Tracking thread started")  # Debug print
            return jsonify({"status": "started"})
        return jsonify({"status": "already_running"})
    except Exception as e:
        print(f"Error in start_jumping_jacks: {str(e)}")
        print(traceback.format_exc())
        is_tracking = False
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/track/get-jumping-jack-count')
def get_jumping_jack_count():
    global jumping_jack_count, is_tracking, tracking_process
    if tracking_process:
        print(f"Tracking process status: {tracking_process.poll()}")  # Debug print
    print(f"Current count: {jumping_jack_count}, Status: {'running' if is_tracking else 'stopped'}")  # Debug print
    return jsonify({
        "count": jumping_jack_count,
        "status": "running" if is_tracking else "stopped"
    })

# ... (rest of the code remains the same)

if __name__ == '__main__':
    print("Starting Flask app...")
    app.run(debug=True, port=5000)