import json
import os

import joblib
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import OneClassSVM
from sklearn.model_selection import GroupShuffleSplit, train_test_split

import features as F

MODELS_DIR = os.path.join(os.path.dirname(__file__), "models")
os.makedirs(MODELS_DIR, exist_ok=True)

def split_by_battery(df):

    gss = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
    tr, te = next(gss.split(df, groups=df["battery"]))
    return df.iloc[tr], df.iloc[te]

def split_telemetry(clean):

    return train_test_split(clean, test_size=0.2, random_state=42)

# Expected share of normal readings outside the learned boundary
ANOMALY_NU = 0.02

def make_temp_model():
    return HistGradientBoostingRegressor(
        max_iter=300,
        learning_rate=0.08,
        max_leaf_nodes=31,
        min_samples_leaf=200,
        monotonic_cst=F.TEMP_MONOTONIC,
        random_state=42,
    )

def main():
    print("Loading NASA charge cycles ...")
    df = F.load_charge()
    print(f"  {len(df):,} samples, {df.groupby(['battery', 'cycle']).ngroups} cycles, "
          f"ambients: {sorted(df['ambient'].unique())}")

    df_train, _ = split_by_battery(df)

    print("\n[1/2] Training temperature soft-sensor (charging, physics-constrained) ...")
    X, y = F.build_temp_table(df_train)
    temp_model = make_temp_model()
    temp_model.fit(X.values, y.values)
    joblib.dump(temp_model, os.path.join(MODELS_DIR, "temperature_regressor.pkl"))
    print(f"  features: {F.TEMP_FEATURES} -> temperature rise above ambient (C)")

    print("\n[2/2] Training anomaly detector (One-Class SVM, WPT telemetry) ...")
    clean, _ = F.load_telemetry()
    tel_train, _ = split_telemetry(clean)
    print(f"  {len(clean)} clean Simulink WPT readings from ThingSpeak, {len(tel_train)} for training")
    # One-Class SVM also flags values far outside the training range,
    # where an Isolation Forest only sees the edge of its last split
    anom_model = make_pipeline(StandardScaler(), OneClassSVM(nu=ANOMALY_NU, gamma=0.01))
    anom_model.fit(tel_train[F.ANOMALY_FEATURES].values)
    joblib.dump(anom_model, os.path.join(MODELS_DIR, "anomaly_detector.pkl"))
    print(f"  features: {F.ANOMALY_FEATURES} -> anomaly score")

    meta = {
        "temp_features": F.TEMP_FEATURES,
        "temp_target": "temperature rise above ambient (C)",
        "temp_monotonic": F.TEMP_MONOTONIC,
        "tau_fast_s": F.TAU_FAST,
        "tau_slow_s": F.TAU_SLOW,
        "anomaly_features": F.ANOMALY_FEATURES,
        "dataset": "NASA Li-ion Battery Aging - charge cycles (CC 1.5 A / CV 4.2 V), ambient 4/24/43 C",
        "anomaly_dataset": "Simulink WPT telemetry, ThingSpeak channel 3311497",
    }
    with open(os.path.join(MODELS_DIR, "metadata.json"), "w") as f:
        json.dump(meta, f, indent=2)

    print("\nSaved 2 models + metadata.json to ml/models/")

if __name__ == "__main__":
    main()
