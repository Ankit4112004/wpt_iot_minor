import csv
import config

with open(config.DEMO_CSV, newline="") as f:
    _ROWS = list(csv.DictReader(f))

_index = 0

def next_reading():

    global _index
    row = _ROWS[_index % len(_ROWS)]
    prev = _ROWS[(_index - 1) % len(_ROWS)] if _index > 0 else None
    _index += 1
    t = float(row["time_in_cycle"])
    t_prev = float(prev["time_in_cycle"]) if prev else None
    new_cycle = t_prev is None or t < t_prev
    return {
        "voltage": float(row["voltage"]),
        "current": float(row["current"]),
        "power": float(row["power"]),
        "soc": float(row["soc"]),
        "dt": 0.0 if new_cycle else t - t_prev,
        "new_cycle": new_cycle,
    }
