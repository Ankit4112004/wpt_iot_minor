import os
import sys

ML_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ml"))
sys.path.insert(0, ML_DIR)
import predict as M  # type: ignore # noqa: E402

def run_inference(voltage, current, time_in_cycle):
    
    temp = M.predict_temperature(voltage, current, time_in_cycle)
    anom = M.detect_anomaly(voltage, current, temp)
    return {
        "predicted_temp": temp,
        "is_anomaly": anom["is_anomaly"],
        "anomaly_score": anom["score"],
    }

def models_ready():
    return M.MODELS_LOADED
