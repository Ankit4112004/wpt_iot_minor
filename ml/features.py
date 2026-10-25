import os

import pandas as pd

HERE = os.path.dirname(__file__)
RAW_CSV = os.path.join(HERE, "data", "raw", "nasa_discharge.csv")

INSTANT_FEATURES = ["Voltage_measured", "Current_measured", "Power", "Time"]

def load_raw():
    
    df = pd.read_csv(RAW_CSV)
    df["Power"] = df["Voltage_measured"] * df["Current_measured"]
    return df

def build_instant_table(df):
    
    X = df[INSTANT_FEATURES].copy()
    y_temp = df["Temperature_measured"].copy()
    return X, y_temp
