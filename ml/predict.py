import json
import os

import joblib
import numpy as np

MODELS_DIR = os.path.join(os.path.dirname(__file__), "models")

def _load(name):
    return joblib.load(os.path.join(MODELS_DIR, name))

try:
    _temp = _load("temperature_regressor.pkl")
    _anom = _load("anomaly_detector.pkl")
    with open(os.path.join(MODELS_DIR, "metadata.json")) as f:
        META = json.load(f)
    MODELS_LOADED = True
except FileNotFoundError:
    _temp = _anom = None
    META = {}
    MODELS_LOADED = False

def predict_temperature(voltage, current, time_in_cycle=0.0):
    
    power = voltage * current
    X = np.array([[voltage, current, power, time_in_cycle]])
    return round(float(_temp.predict(X)[0]), 3)

def detect_anomaly(voltage, current, temperature):
    
    power = voltage * current
    X = np.array([[voltage, current, power, temperature]])
    label = int(_anom.predict(X)[0])
    score = float(_anom.score_samples(X)[0])
    return {"is_anomaly": label == -1, "score": round(score, 4)}
