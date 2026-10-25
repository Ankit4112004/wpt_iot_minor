import os
import sys

ML_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ml"))
sys.path.insert(0, ML_DIR)
import predict as M  # type: ignore # noqa: E402
from features import HeatState  # type: ignore # noqa: E402,F401

def run_inference(i_cell, ambient, heat_fast, heat_slow):

    temp = M.predict_temperature(i_cell, ambient, heat_fast, heat_slow)
    anom = M.detect_anomaly(i_cell, temp - ambient)
    return {
        "predicted_temp": temp,
        "is_anomaly": anom["is_anomaly"],
        "anomaly_score": anom["score"],
    }

def models_ready():
    return M.MODELS_LOADED
