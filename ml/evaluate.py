import os
import json

import joblib
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_absolute_error

import features as F

REPORTS = os.path.join(os.path.dirname(__file__), "reports")
MODELS_DIR = os.path.join(os.path.dirname(__file__), "models")
os.makedirs(REPORTS, exist_ok=True)

def evaluate_temperature(df):
    X, y = F.build_instant_table(df)
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, random_state=42)
    m = joblib.load(os.path.join(MODELS_DIR, "temperature_regressor.pkl"))
    pred = m.predict(Xte)
    res = {"r2": round(float(r2_score(yte, pred)), 4),
           "mae_celsius": round(float(mean_absolute_error(yte, pred)), 4)}
    return res

def evaluate_anomaly(df):
    feats = ["Voltage_measured", "Current_measured", "Power", "Temperature_measured"]
    m = joblib.load(os.path.join(MODELS_DIR, "anomaly_detector.pkl"))
    _, df_test = train_test_split(df, test_size=0.2, random_state=42)
    flags = m.predict(df_test[feats])
    return {"flagged_rate": round(float((flags == -1).mean()), 4),
            "contamination_setting": 0.02}

def main():
    df = F.load_raw()
    metrics = {
        "temperature_soft_sensor": evaluate_temperature(df),
        "anomaly_detector": evaluate_anomaly(df),
    }
    with open(os.path.join(REPORTS, "metrics.json"), "w") as f:
        json.dump(metrics, f, indent=2)
    print(json.dumps(metrics, indent=2))
    print(f"\nMetrics saved to ml/reports/metrics.json")

if __name__ == "__main__":
    main()
