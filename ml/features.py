import math
import os

import numpy as np
import pandas as pd

HERE = os.path.dirname(__file__)
CHARGE_CSV = os.path.join(HERE, "data", "nasa_charge_30s.csv.gz")

# Thermal time constants (s) of the two exponentially filtered I^2 heat terms
TAU_FAST = 300.0
TAU_SLOW = 1200.0

# Cell voltage is left out on purpose: the NASA cells (4.2 V full) and the Simulink pack
# (419 V / 105 = 3.99 V full) use different voltage windows, and it adds no accuracy.
TEMP_FEATURES = ["i_cell", "ambient", "heat_fast", "heat_slow"]
# Predicted temperature rise may only increase with current and accumulated heat
TEMP_MONOTONIC = [1, 0, 1, 1]

# "Is the battery heating more than it should for this charging current?"
ANOMALY_FEATURES = ["i_cell", "temp_rise"]

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
