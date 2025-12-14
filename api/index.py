from flask import Flask, render_template, request, jsonify
import firebase_admin
from firebase_admin import credentials, db
import datetime
import os

app = Flask(__name__, template_folder='../templates', static_folder='../static')

# --- FIREBASE INITIALIZATION ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

if not firebase_admin._apps:
    cred_path = os.path.join(BASE_DIR, 'serviceAccountKey.json')
    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://iot-pakan-ayam-5ebc6-default-rtdb.asia-southeast1.firebasedatabase.app'
    })

# --- FIREBASE RTDB REFERENCES ---
status_ref = db.reference('/feeder/status')
control_ref = db.reference('/feeder/control')

# --- WEB ROUTES ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/status')
def status():
    try:
        status_data = status_ref.get() or {}
        control_data = control_ref.get() or {}
        
        return jsonify({
            "berat": round(status_data.get('berat', 0.0), 2),
            "mode": control_data.get('mode', 'MANUAL'),
            "interval": control_data.get('interval', 30),
            "last_feed": control_data.get('last_feed', 'Belum pernah'),
            "esp_connected": status_data.get('esp_connected', False)
        })
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({
            "berat": 0.0,
            "mode": "MANUAL",
            "interval": 30,
            "last_feed": "Belum pernah",
            "esp_connected": False
        })

@app.route('/set_mode/<mode>', methods=['POST'])
def set_mode(mode):
    try:
        control_ref.update({'mode': mode})
        return jsonify({"status": "ok", "mode": mode})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/set_interval/<int:interval>', methods=['POST'])
def set_interval(interval):
    try:
        if interval < 10:
            interval = 10
        if interval > 3600:
            interval = 3600
            
        control_ref.update({'interval': interval})
        return jsonify({"status": "ok", "interval": interval})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/manual_feed', methods=['POST'])
def manual_feed():
    try:
        control_ref.update({
            'command': 'FEED',
            'last_feed': datetime.datetime.now().strftime("%H:%M:%S")
        })
        return jsonify({"message": "Perintah Makan Dikirim!"})
    except Exception as e:
        return jsonify({"message": f"Gagal! {str(e)}"})

# --- ML PREDICTION (DISABLED) ---
@app.route('/predict', methods=['POST'])
def predict():
    return jsonify({
        "status": "error",
        "message": "Fitur ML tidak tersedia di versi cloud"
    })

app = app
