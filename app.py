from flask import Flask, render_template, request, jsonify
import firebase_admin
from firebase_admin import credentials, db
import datetime
import pickle
import numpy as np

app = Flask(__name__)

# --- FIREBASE INITIALIZATION ---
cred = credentials.Certificate('serviceAccountKey.json')
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://iot-pakan-ayam-5ebc6-default-rtdb.asia-southeast1.firebasedatabase.app'
})

# --- LOAD ML MODEL ---
try:
    with open('model_pakan.pkl', 'rb') as f:
        ml_model = pickle.load(f)
    print("✅ ML Model loaded successfully")
except Exception as e:
    ml_model = None
    print(f"⚠️ ML Model not found: {e}")

# --- FIREBASE RTDB REFERENCES ---
status_ref = db.reference('/feeder/status')
control_ref = db.reference('/feeder/control')

# --- INITIALIZE RTDB DATA ---
def init_rtdb():
    try:
        status_data = status_ref.get()
        if status_data is None:
            status_ref.set({
                'berat': 0.0,
                'esp_connected': False
            })
        
        control_data = control_ref.get()
        if control_data is None:
            control_ref.set({
                'mode': 'MANUAL',
                'command': '',
                'interval': 30,  # Default 30 detik
                'last_feed': 'Belum pernah'
            })
    except Exception as e:
        print(f"Error initializing RTDB: {e}")

init_rtdb()

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
        # Validasi interval (minimum 10 detik, maksimum 3600 detik / 1 jam)
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

# --- ML PREDICTION ENDPOINT ---
@app.route('/predict', methods=['POST'])
def predict():
    if ml_model is None:
        return jsonify({
            "status": "error",
            "message": "Model ML tidak tersedia"
        })
    
    try:
        data = request.get_json()
        
        jumlah_ayam = int(data.get('jumlah_ayam', 0))
        umur_minggu = int(data.get('umur_minggu', 0))
        pakan_saat_ini = float(data.get('pakan_saat_ini', 0))
        
        # Validasi input
        if jumlah_ayam <= 0 or umur_minggu <= 0:
            return jsonify({
                "status": "error",
                "message": "Input tidak valid"
            })
        
        # Predict
        input_data = np.array([[jumlah_ayam, umur_minggu, pakan_saat_ini]])
        prediction = ml_model.predict(input_data)[0]
        
        return jsonify({
            "status": "ok",
            "prediksi_kg": round(prediction, 2),
            "input": {
                "jumlah_ayam": jumlah_ayam,
                "umur_minggu": umur_minggu,
                "pakan_saat_ini_kg": pakan_saat_ini
            }
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)