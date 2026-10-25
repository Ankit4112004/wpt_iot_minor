import csv
import config

with open(config.DEMO_CSV, newline="") as f:
    _ROWS = list(csv.DictReader(f))

_index = 0

def next_reading():
    
    global _index
    row = _ROWS[_index % len(_ROWS)]
    _index += 1
    return {
        "voltage": float(row["voltage"]),
        "current": float(row["current"]),
        "power": float(row["power"]),
        "soc": float(row["soc"]),
        "time_in_cycle": float(row["time_in_cycle"]),
    }
