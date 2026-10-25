import math
import os

import numpy as np
import pandas as pd

HERE = os.path.dirname(__file__)
CHARGE_CSV = os.path.join(HERE, "data", "nasa_charge_30s.csv.gz")
# Snapshot of the Simulink WPT telemetry logged to ThingSpeak channel 3311497
TELEMETRY_CSV = os.path.join(HERE, "data", "wpt_telemetry.csv")

# Thermal time constants (s) of the two exponentially filtered I^2 heat terms
TAU_FAST = 300.0
TAU_SLOW = 1200.0

# Cell voltage is left out on purpose: the NASA cells (4.2 V full) and the Simulink pack
# (419 V / 105 = 3.99 V full) use different voltage windows, and it adds no accuracy.
TEMP_FEATURES = ["i_cell", "ambient", "heat_fast", "heat_slow"]
# Predicted temperature rise may only increase with current and accumulated heat
TEMP_MONOTONIC = [1, 0, 1, 1]

# Normal electrical operating envelope of this charger, learned from its own telemetry.
# Temperature is left out: it is predicted from current, so it cannot reveal a fault.
ANOMALY_FEATURES = ["voltage", "current", "power"]

def ewma_step(prev, value, dt, tau):

    a = 1.0 - math.exp(-max(dt, 0.0) / tau)
    return prev + a * (value - prev)

class HeatState:

    def __init__(self):
        self.fast = 0.0
        self.slow = 0.0

    def update(self, i_cell, dt):
        i2 = i_cell * i_cell
        self.fast = ewma_step(self.fast, i2, dt, TAU_FAST)
        self.slow = ewma_step(self.slow, i2, dt, TAU_SLOW)
        return self.fast, self.slow

def add_heat_features(cycle):

    state = HeatState()
    fast, slow = [], []
    t_prev = None
    for t, i in zip(cycle["time"].values, cycle["i_cell"].values):
        dt = 0.0 if t_prev is None else t - t_prev
        t_prev = t
        f, s = state.update(i, dt)
        fast.append(f)
        slow.append(s)
    cycle = cycle.copy()
    cycle["heat_fast"] = fast
    cycle["heat_slow"] = slow
    return cycle

def load_charge():

    df = pd.read_csv(CHARGE_CSV)
    df["temp_rise"] = df["temperature"] - df["ambient"]
    return df

def build_temp_table(df):

    return df[TEMP_FEATURES].copy(), df["temp_rise"].copy()

def load_telemetry():

    df = pd.read_csv(TELEMETRY_CSV, parse_dates=["created_at"])
    # Charging readings with all fields present (Simscape: negative current = charging).
    # The rest are set-up/test writes and wrong-field glitches, kept for evaluation.
    valid = (df[["voltage", "current", "power", "soc"]].notna().all(axis=1)
             & (df["current"] < 0) & df["voltage"].between(300, 425) & (df["power"] > 100))
    return df[valid].reset_index(drop=True), df[~valid].reset_index(drop=True)
