import threading
import time

# Demo scenarios applied on top of the replayed Simulink telemetry. Each one changes the
# inputs only; the temperature and anomaly models react to them as they would to real data.
# "ramp_s" is how long the change takes to reach full strength.
SCENARIOS = {
    "heat_wave": {
        "label": "Heat wave",
        "description": "Ambient temperature rises from 25 to 42 °C",
        "ambient": 42.0, "current_scale": 1.0, "power_scale": 1.0, "ramp_s": 90,
    },
    "misaligned_pad": {
        "label": "Pad misaligned",
        "description": "Coupling loss: charging current and power drop to about a quarter",
        "ambient": None, "current_scale": 0.23, "power_scale": 0.23, "ramp_s": 15,
    },
    "overcurrent": {
        "label": "Overcurrent fault",
        "description": "Charging current and power more than double",
        "ambient": None, "current_scale": 2.3, "power_scale": 2.3, "ramp_s": 15,
    },
    "sensor_glitch": {
        "label": "Sensor glitch",
        "description": "Power sensor reads zero while current keeps flowing",
        "ambient": None, "current_scale": 1.0, "power_scale": 0.0, "ramp_s": 0,
    },
}

DURATION_S = 300

_lock = threading.Lock()
_active = None
_started = 0.0

def start(name):

    global _active, _started
    if name not in SCENARIOS:
        raise KeyError(name)
    with _lock:
        _active, _started = name, time.time()

def stop():

    global _active
    with _lock:
        _active = None

def status():

    with _lock:
        name, started = _active, _started
    if name is None:
        return None
    elapsed = time.time() - started
    if elapsed > DURATION_S:
        stop()
        return None
    s = SCENARIOS[name]
    progress = 1.0 if s["ramp_s"] <= 0 else min(1.0, elapsed / s["ramp_s"])
    return {"name": name, "label": s["label"], "description": s["description"],
            "progress": round(progress, 3), "seconds_left": int(DURATION_S - elapsed)}

def apply(reading, base_ambient):

    st = status()
    if st is None:
        return reading, base_ambient, None
    s, k = SCENARIOS[st["name"]], st["progress"]
    reading = dict(reading)
    reading["current"] *= 1 + k * (s["current_scale"] - 1)
    reading["power"] *= 1 + k * (s["power_scale"] - 1)
    ambient = base_ambient if s["ambient"] is None else base_ambient + k * (s["ambient"] - base_ambient)
    return reading, ambient, st["name"]

def catalogue():

    return [{"name": n, "label": s["label"], "description": s["description"]} for n, s in SCENARIOS.items()]
