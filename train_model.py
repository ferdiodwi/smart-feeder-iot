"""
Script untuk membuat model prediksi konsumsi pakan ayam
menggunakan Random Forest Regression

Input:
- jumlah_ayam: jumlah ayam yang dipelihara
- umur_minggu: umur ayam dalam minggu
- pakan_saat_ini_kg: jumlah pakan tersedia saat ini (kg)

Output:
- prediksi_pakan_minggu_depan: prediksi kebutuhan pakan minggu depan (kg)
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
import pickle

# =========================================
# GENERATE DATA TRAINING (Simulasi)
# =========================================
# Data berdasarkan standar konsumsi ayam:
# - Ayam umur 1-4 minggu: ~15-50g/hari
# - Ayam umur 5-8 minggu: ~50-100g/hari  
# - Ayam dewasa 8+ minggu: ~100-150g/hari

np.random.seed(42)
n_samples = 1000

# Generate random data
jumlah_ayam = np.random.randint(10, 500, n_samples)  # 10 - 500 ekor
umur_minggu = np.random.randint(1, 20, n_samples)     # 1 - 20 minggu
pakan_saat_ini = np.random.uniform(5, 100, n_samples) # 5 - 100 kg

# Hitung konsumsi per ekor berdasarkan umur (gram/hari)
def konsumsi_per_ekor_per_hari(umur):
    if umur <= 1:
        return 15
    elif umur <= 2:
        return 25
    elif umur <= 3:
        return 35
    elif umur <= 4:
        return 50
    elif umur <= 5:
        return 65
    elif umur <= 6:
        return 80
    elif umur <= 7:
        return 95
    elif umur <= 8:
        return 110
    else:
        return 120 + (umur - 8) * 3  # Naik perlahan setelah 8 minggu

# Hitung kebutuhan pakan minggu depan (kg)
def hitung_kebutuhan_minggu_depan(jumlah, umur, pakan_sekarang):
    konsumsi_harian_per_ekor = konsumsi_per_ekor_per_hari(umur + 1)  # Umur minggu depan
    konsumsi_harian_total = jumlah * konsumsi_harian_per_ekor / 1000  # Konversi ke kg
    kebutuhan_mingguan = konsumsi_harian_total * 7  # 7 hari
    
    # Tambahkan sedikit noise untuk variasi
    noise = np.random.uniform(-0.1, 0.1) * kebutuhan_mingguan
    kebutuhan = kebutuhan_mingguan + noise
    
    # Minimal kebutuhan adalah 0
    return max(0, kebutuhan)

# Generate target
prediksi_pakan = np.array([
    hitung_kebutuhan_minggu_depan(j, u, p) 
    for j, u, p in zip(jumlah_ayam, umur_minggu, pakan_saat_ini)
])

# Buat DataFrame
data = pd.DataFrame({
    'jumlah_ayam': jumlah_ayam,
    'umur_minggu': umur_minggu,
    'pakan_saat_ini_kg': pakan_saat_ini,
    'kebutuhan_pakan_kg': prediksi_pakan
})

print("=== Data Sample ===")
print(data.head(10))
print(f"\nTotal samples: {len(data)}")

# =========================================
# TRAINING MODEL
# =========================================
X = data[['jumlah_ayam', 'umur_minggu', 'pakan_saat_ini_kg']]
y = data['kebutuhan_pakan_kg']

# Split data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train Random Forest
print("\n=== Training Model ===")
model = RandomForestRegressor(
    n_estimators=100,
    max_depth=10,
    random_state=42,
    n_jobs=-1
)
model.fit(X_train, y_train)

# Evaluate
y_pred = model.predict(X_test)
mae = mean_absolute_error(y_test, y_pred)
r2 = r2_score(y_test, y_pred)

print(f"Mean Absolute Error: {mae:.2f} kg")
print(f"R² Score: {r2:.4f}")

# Feature importance
print("\n=== Feature Importance ===")
for name, importance in zip(X.columns, model.feature_importances_):
    print(f"{name}: {importance:.4f}")

# =========================================
# SAVE MODEL
# =========================================
model_path = 'model_pakan.pkl'
with open(model_path, 'wb') as f:
    pickle.dump(model, f)

print(f"\n✅ Model saved to {model_path}")

# =========================================
# TEST PREDICTION
# =========================================
print("\n=== Test Predictions ===")
test_cases = [
    {'jumlah_ayam': 50, 'umur_minggu': 4, 'pakan_saat_ini_kg': 20},
    {'jumlah_ayam': 100, 'umur_minggu': 8, 'pakan_saat_ini_kg': 50},
    {'jumlah_ayam': 200, 'umur_minggu': 12, 'pakan_saat_ini_kg': 80},
]

for test in test_cases:
    input_data = pd.DataFrame([test])
    prediction = model.predict(input_data)[0]
    print(f"Input: {test}")
    print(f"Prediksi kebutuhan minggu depan: {prediction:.2f} kg")
    print()
