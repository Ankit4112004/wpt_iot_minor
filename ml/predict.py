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

def predict_temperature(i_cell, ambient, heat_fast, heat_slow):

    X = np.array([[i_cell, ambient, heat_fast, heat_slow]])
    rise = float(_temp.predict(X)[0])
    return round(ambient + rise, 3)

def detect_anomaly(voltage, current, power):

    X = np.array([[voltage, current, power]])
    label = int(_anom.predict(X)[0])
    score = float(_anom.score_samples(X)[0])
    return {"is_anomaly": label == -1, "score": round(score, 4)}
