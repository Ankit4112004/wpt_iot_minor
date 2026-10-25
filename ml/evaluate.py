import os
import json

import joblib
import numpy as np
from sklearn.metrics import r2_score, mean_absolute_error

import features as F
from train import split_by_battery, split_telemetry, ANOMALY_NU

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

# Hand-made fault cases around the normal operating point (390 V, -13 A, 5.3 kW)
FAULT_CASES = {
    "coupling loss (misaligned pad)": (390.0, -3.0, 1170.0),
    "overcurrent": (390.5, -30.0, 11700.0),
    "pack voltage sag": (360.0, -13.0, 4680.0),
    "power sensor mismatch": (390.0, -13.0, 9000.0),
}

def evaluate_anomaly():
    m = joblib.load(os.path.join(MODELS_DIR, "anomaly_detector.pkl"))
    clean, glitches = F.load_telemetry()
    _, tel_test = split_telemetry(clean)
    normal_flags = m.predict(tel_test[F.ANOMALY_FEATURES].values) == -1
    # The backend reads missing ThingSpeak fields as 0, so evaluate glitches the same way
    glitch_flags = m.predict(glitches[F.ANOMALY_FEATURES].fillna(0).values) == -1
    faults = {name: bool(m.predict(np.array([x]))[0] == -1) for name, x in FAULT_CASES.items()}
    return {"false_alarm_rate_on_held_out_normal": round(float(normal_flags.mean()), 4),
            "real_glitches_detected": f"{int(glitch_flags.sum())}/{len(glitches)}",
            "fault_cases_detected": faults,
            "nu_setting": ANOMALY_NU}

def main():
    df = F.load_charge()
    _, df_test = split_by_battery(df)
    metrics = {
        "temperature_soft_sensor": evaluate_temperature(df_test),
        "steady_state_temp_vs_charge_current": current_sensitivity(),
        "anomaly_detector": evaluate_anomaly(),
    }
    with open(os.path.join(REPORTS, "metrics.json"), "w") as f:
        json.dump(metrics, f, indent=2)
    print(json.dumps(metrics, indent=2))
    print(f"\nMetrics saved to ml/reports/metrics.json")

if __name__ == "__main__":
    main()
