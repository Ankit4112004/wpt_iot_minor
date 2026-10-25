import os
import json

import joblib
import numpy as np
from sklearn.metrics import r2_score, mean_absolute_error

import features as F
from train import split_by_battery

REPORTS = os.path.join(os.path.dirname(__file__), "reports")
MODELS_DIR = os.path.join(os.path.dirname(__file__), "models")
os.makedirs(REPORTS, exist_ok=True)

def evaluate_temperature(df_test):
    X, y = F.build_temp_table(df_test)
    m = joblib.load(os.path.join(MODELS_DIR, "temperature_regressor.pkl"))
    pred = m.predict(X.values)
    temp_true = y + df_test["ambient"]
    temp_pred = pred + df_test["ambient"]
    return {"r2_temperature": round(float(r2_score(temp_true, temp_pred)), 4),
            "r2_temperature_rise": round(float(r2_score(y, pred)), 4),
            "mae_celsius": round(float(mean_absolute_error(temp_true, temp_pred)), 4),
            "test_batteries": sorted(df_test["battery"].unique().tolist())}

def current_sensitivity(ambient=25.0):

    m = joblib.load(os.path.join(MODELS_DIR, "temperature_regressor.pkl"))
    out = {}
    for pct in (100, 80, 60, 40, 20, 0):
        i = 1.5 * pct / 100
        h = i * i  # heat terms at steady state
        out[f"{pct}%"] = round(float(ambient + m.predict(np.array([[i, ambient, h, h]]))[0]), 3)
    return out

def evaluate_anomaly(df_test):
    m = joblib.load(os.path.join(MODELS_DIR, "anomaly_detector.pkl"))
    flags = m.predict(df_test[F.ANOMALY_FEATURES].values)
    return {"flagged_rate": round(float((flags == -1).mean()), 4),
            "contamination_setting": 0.02}

def main():
    df = F.load_charge()
    _, df_test = split_by_battery(df)
    metrics = {
        "temperature_soft_sensor": evaluate_temperature(df_test),
        "steady_state_temp_vs_charge_current": current_sensitivity(),
        "anomaly_detector": evaluate_anomaly(df_test),
    }
    with open(os.path.join(REPORTS, "metrics.json"), "w") as f:
        json.dump(metrics, f, indent=2)
    print(json.dumps(metrics, indent=2))
    print(f"\nMetrics saved to ml/reports/metrics.json")

if __name__ == "__main__":
    main()
