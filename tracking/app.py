from flask import Flask, jsonify, send_from_directory
import subprocess
import threading
import traceback
from flask_cors import CORS

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app, resources={r"/*": {"origins": "http://localhost:8000"}})

jumping_jack_count = 0
tracking_process = None
is_tracking = False

def run_tracking_script():
    global jumping_jack_count, is_tracking
    try:
        print("Starting tracking script...")  # Debug print
        process = subprocess.Popen(['python', 'track.py'], stdout=subprocess.PIPE, universal_newlines=True)
        print("Tracking script started")  # Debug print
        for line in process.stdout:
            print(f"Received line: {line}")  # Debug print
            if line.startswith('jumping jack Count:'):
                jumping_jack_count = int(line.split(':')[1].strip())
                print(f"Updated count: {jumping_jack_count}")  # Debug print
        is_tracking = False
        print("Tracking stopped")  # Debug print
    except Exception as e:
        print(f"Error in run_tracking_script: {str(e)}")
        print(traceback.format_exc())
        is_tracking = False

@app.route('/')
def serve_dashboard():
    return send_from_directory('.', 'dashboard.html')

@app.route('/track/start-jumping-jacks', methods=['POST'])
def start_jumping_jacks():
    global tracking_process, is_tracking
    try:
        if not is_tracking:
            is_tracking = True
            tracking_process = threading.Thread(target=run_tracking_script)
            tracking_process.start()
            print("Tracking started")  # Debug print
            return jsonify({"status": "started"})
        return jsonify({"status": "already_running"})
    except Exception as e:
        print(f"Error in start_jumping_jacks: {str(e)}")
        print(traceback.format_exc())
        is_tracking = False
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/track/get-jumping-jack-count')
def get_jumping_jack_count():
    global jumping_jack_count, is_tracking
    print(f"Current count: {jumping_jack_count}, Status: {'running' if is_tracking else 'stopped'}")  # Debug print
    return jsonify({
        "count": jumping_jack_count,
        "status": "running" if is_tracking else "stopped"
    })

@app.route('/js/<path:path>')
def send_js(path):
    return send_from_directory('js', path)

@app.route('/css/<path:path>')
def send_css(path):
    return send_from_directory('css', path)

if __name__ == '__main__':
    print("Starting Flask app...")
    app.run(debug=True, port=5000)