import threading
import time
from datetime import datetime, timezone

import requests
from sqlalchemy import select, delete, func

import config
import replay
import scenarios
from db import SessionLocal, Reading, Prediction, Alert
from inference import run_inference, HeatState

_last_live_ts = 0.0
_last_feed_time = None
_alert_cooldown = {"over_temp": 0.0, "anomaly": 0.0}
_ALERT_GAP = 20.0

# Exponentially filtered I^2 heat state, carried across ticks of the same source
_heat = HeatState()
_heat_source = None
_heat_last_ts = None
_tick_lock = threading.Lock()
_refresh_lock = threading.Lock()
_last_refresh_request = 0.0

def _fetch_thingspeak():

    if not (config.THINGSPEAK_CHANNEL and config.THINGSPEAK_READ_KEY):
        return None
    try:
        url = (f"https://api.thingspeak.com/channels/{config.THINGSPEAK_CHANNEL}"
               f"/feeds.json?api_key={config.THINGSPEAK_READ_KEY}&results=1")
        feed = requests.get(url, timeout=8).json()["feeds"][-1]
        voltage = float(feed.get("field3") or 0)
        current = float(feed.get("field2") or 0)
        soc = float(feed.get("field4") or 0)

        reading = {
            "voltage": voltage,
            "current": current,
            "power": float(feed.get("field1") or voltage * current),
            "soc": soc,
            "dt": None,
            "new_cycle": False,
        }
        return reading, feed.get("created_at")
    except Exception:
        return None

def _resolve_source():
    
    global _last_live_ts, _last_feed_time
    # A running demo scenario always plays on the recorded telemetry, so it is repeatable
    if scenarios.status() is not None:
        return replay.next_reading(), "demo"
    fetched = _fetch_thingspeak()
    if fetched is not None:
        reading, feed_time = fetched
        if _last_feed_time is None or (feed_time and feed_time > _last_feed_time):
            _last_feed_time = feed_time
            _last_live_ts = time.time()
            return reading, "live"

    live_configured = bool(config.THINGSPEAK_CHANNEL and config.THINGSPEAK_READ_KEY)
    if live_configured and (time.time() - _last_live_ts) < config.STALE_SECONDS:
        return None
    return replay.next_reading(), "replay"

def _maybe_alert(session, reading, pred):
    
    now = time.time()
    if pred["predicted_temp"] > config.OVER_TEMP_C and now - _alert_cooldown["over_temp"] > _ALERT_GAP:
        session.add(Alert(type="over_temp", severity="critical",
                          message=f"Predicted battery temperature {pred['predicted_temp']:.1f} C "
                                  f"exceeds safe limit {config.OVER_TEMP_C:.0f} C",
                          value=pred["predicted_temp"]))
        _alert_cooldown["over_temp"] = now
    if pred["is_anomaly"] and now - _alert_cooldown["anomaly"] > _ALERT_GAP:
        session.add(Alert(type="anomaly", severity="warning",
                          message="Abnormal operating point detected by anomaly model",
                          value=pred["anomaly_score"]))
        _alert_cooldown["anomaly"] = now

def _cell_features(reading, source):

    global _heat, _heat_source, _heat_last_ts
    # Simscape convention: negative pack current = charging. NASA charge current is positive.
    i_cell = max(0.0, -reading["current"] * config.CELL_CAPACITY_AH / config.PACK_CAPACITY_AH)

    now = time.time()
    if source != _heat_source or reading["new_cycle"]:
        _heat, _heat_source, _heat_last_ts = HeatState(), source, None
    if reading["dt"] is not None:
        dt = reading["dt"]
    else:
        dt = 0.0 if _heat_last_ts is None else now - _heat_last_ts
    _heat_last_ts = now
    heat_fast, heat_slow = _heat.update(i_cell, min(dt, config.MAX_GAP_SECONDS))
    return i_cell, heat_fast, heat_slow

def _tick_once():

    resolved = _resolve_source()
    if resolved is None:
        return
    reading_dict, source = resolved
    ambient = config.AMBIENT_C
    if source == "demo":
        reading_dict, ambient, _ = scenarios.apply(reading_dict, ambient)
    i_cell, heat_fast, heat_slow = _cell_features(reading_dict, source)

    session = SessionLocal()
    try:
        r = Reading(ts=datetime.now(timezone.utc),
                    voltage=reading_dict["voltage"], current=reading_dict["current"],
                    power=reading_dict["power"], soc=reading_dict["soc"], source=source)
        session.add(r)
        session.flush()

        pred = run_inference(reading_dict, i_cell, ambient, heat_fast, heat_slow)
        session.add(Prediction(reading_id=r.id, **pred))
        _maybe_alert(session, r, pred)

        count = session.scalar(select(func.count(Reading.id)))
        if count > config.MAX_READINGS:
            cutoff = session.scalar(
                select(Reading.id).order_by(Reading.id.desc())
                .offset(config.MAX_READINGS).limit(1))
            if cutoff:
                session.execute(delete(Prediction).where(Prediction.reading_id <= cutoff))
                session.execute(delete(Reading).where(Reading.id <= cutoff))

        session.commit()
    except Exception as e:
        session.rollback()
        print("ingest tick error:", e)
    finally:
        session.close()

def tick():
    
    with _tick_lock:
        return _tick_once()

def ensure_fresh():
    
    global _last_refresh_request
    now = time.monotonic()
    with _refresh_lock:
        if now - _last_refresh_request < max(1, config.TICK_SECONDS):
            return
        _last_refresh_request = now

    threading.Thread(target=tick, name="api-refresh", daemon=True).start()
