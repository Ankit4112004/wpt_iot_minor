import glob
import json
import io
import os
import sys
import urllib.request
import zipfile

import numpy as np
import pandas as pd

import features as F

HERE = os.path.dirname(__file__)
RAW_DIR = os.path.join(HERE, "data", "raw")
URL = "https://phm-datasets.s3.amazonaws.com/NASA/5.+Battery+Data+Set.zip"
ZIP_PATH = os.path.join(RAW_DIR, "nasa_battery_data_set.zip")
MAT_DIR = os.path.join(RAW_DIR, "mat")

RESAMPLE_S = 30
# A charge cycle is kept only if the cell starts within this many degrees of ambient,
# so the temperature rise comes from charging, not from heat left over by the last discharge.
MAX_START_EXCESS_C = 3.0
MIN_CYCLE_S = 1800

def download_and_extract():

    os.makedirs(MAT_DIR, exist_ok=True)
    if glob.glob(os.path.join(MAT_DIR, "B00*.mat")):
        return
    if not os.path.exists(ZIP_PATH):
        print(f"Downloading NASA battery archive -> {ZIP_PATH}")
        urllib.request.urlretrieve(URL, ZIP_PATH)
    with zipfile.ZipFile(ZIP_PATH) as outer:
        for name in outer.namelist():
            if name.endswith(".zip"):
                with zipfile.ZipFile(io.BytesIO(outer.read(name))) as inner:
                    for member in inner.namelist():
                        if member.endswith(".mat"):
                            with open(os.path.join(MAT_DIR, os.path.basename(member)), "wb") as f:
                                f.write(inner.read(member))

def clean_cycle(battery, k, ambient, d):

    c = pd.DataFrame({
        "time": np.asarray(d["Time"], float),
        "v_cell": np.asarray(d["Voltage_measured"], float),
        "i_cell": np.asarray(d["Current_measured"], float),
        "temperature": np.asarray(d["Temperature_measured"], float),
    })
    ok = (c.v_cell.between(2.5, 4.3) & c.i_cell.between(-0.05, 1.6)
          & c.temperature.between(ambient - 5, ambient + 30))
    c = c[ok].sort_values("time")
    if len(c) < 20 or c.time.iloc[-1] - c.time.iloc[0] < MIN_CYCLE_S:
        return None
    if abs(c.temperature.iloc[0] - ambient) >= MAX_START_EXCESS_C:
        return None
    c["time"] -= c.time.iloc[0]
    c = F.add_heat_features(c)
    c = c.groupby((c.time // RESAMPLE_S).astype(int)).last().reset_index(drop=True)
    c.insert(0, "cycle", k)
    c.insert(0, "battery", battery)
    c["ambient"] = ambient
    return c

def build_charge_csv():
    from scipy.io import loadmat

    parts = []
    for path in sorted(glob.glob(os.path.join(MAT_DIR, "B00*.mat"))):
        battery = os.path.basename(path)[:-4]
        cycles = loadmat(path, simplify_cells=True)[battery]["cycle"]
        k = 0
        for cyc in cycles:
            if cyc["type"] != "charge":
                continue
            try:
                c = clean_cycle(battery, k, float(cyc["ambient_temperature"]), cyc["data"])
            except (KeyError, TypeError, ValueError):
                c = None
            if c is not None:
                parts.append(c)
                k += 1
    df = pd.concat(parts, ignore_index=True)
    df = df[["battery", "cycle", "ambient", "time", "v_cell", "i_cell",
             "heat_fast", "heat_slow", "temperature"]].round(4)
    os.makedirs(os.path.dirname(F.CHARGE_CSV), exist_ok=True)
    df.to_csv(F.CHARGE_CSV, index=False)
    print(f"Wrote {len(df):,} samples from {df.groupby(['battery', 'cycle']).ngroups} charge cycles "
          f"-> {F.CHARGE_CSV}")

DEMO_CSV = os.path.join(HERE, "..", "webdev", "backend", "data", "demo_cycles.csv")
# Readings further apart than this belong to different simulation runs
SESSION_GAP_S = 600

def fetch_telemetry():

    channel = os.environ["THINGSPEAK_CHANNEL"]
    key = os.environ["THINGSPEAK_READ_KEY"]
    url = f"https://api.thingspeak.com/channels/{channel}/feeds.json?api_key={key}&results=8000"
    with urllib.request.urlopen(url, timeout=30) as r:
        feeds = pd.DataFrame(json.load(r)["feeds"])
    feeds = feeds.rename(columns={"field1": "power", "field2": "current",
                                  "field3": "voltage", "field4": "soc"})
    feeds[["created_at", "voltage", "current", "power", "soc"]].to_csv(F.TELEMETRY_CSV, index=False)
    print(f"Wrote {len(feeds)} ThingSpeak readings -> {F.TELEMETRY_CSV}")

def build_demo_replay():

    clean, _ = F.load_telemetry()
    t = (clean.created_at - clean.created_at.iloc[0]).dt.total_seconds()
    new_session = t.diff().fillna(SESSION_GAP_S + 1) > SESSION_GAP_S
    session = new_session.cumsum() - 1
    start = t.groupby(session).transform("first")
    demo = pd.DataFrame({
        "seq": range(len(clean)),
        "voltage": clean.voltage,
        "current": clean.current,
        "power": clean.power,
        "time_in_cycle": t - start,
        "soc": clean.soc,
        "cycle_index": session,
    }).round(4)
    demo.to_csv(DEMO_CSV, index=False)
    print(f"Wrote {len(demo)} replay rows from {session.max() + 1} recorded Simulink runs -> {DEMO_CSV}")

def main():
    if "--telemetry" in sys.argv:
        fetch_telemetry()
        return
    if "--demo" in sys.argv:
        build_demo_replay()
        return
    if os.path.exists(F.CHARGE_CSV) and "--rebuild" not in sys.argv:
        print(f"Already present: {F.CHARGE_CSV}")
        return
    download_and_extract()
    build_charge_csv()

if __name__ == "__main__":
    main()
