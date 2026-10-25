import threading
import time
from datetime import datetime, timezone

import requests
from sqlalchemy import select, delete, func

import config
import replay
from db import SessionLocal, Reading, Prediction, Alert
from inference import run_inference

_last_live_ts = 0.0
_last_feed_time = None
_alert_cooldown = {"over_temp": 0.0, "anomaly": 0.0}
_ALERT_GAP = 20.0

_charge_start_ts = None
_tick_lock = threading.Lock()
_refresh_lock = threading.Lock()
_last_refresh_request = 0.0

def _fetch_thingspeak():
    
    global _charge_start_ts
    if not (config.THINGSPEAK_CHANNEL and config.THINGSPEAK_READ_KEY):
        return None
    try:
        url = (f"https://api.thingspeak.com/channels/{config.THINGSPEAK_CHANNEL}"
               f"/feeds.json?api_key={config.THINGSPEAK_READ_KEY}&results=1")
        feed = requests.get(url, timeout=8).json()["feeds"][-1]
        voltage = float(feed.get("field3") or 0)
        current = float(feed.get("field2") or 0)
        soc = float(feed.get("field4") or 0)
        
        if current >= 0:
            _charge_start_ts = None
            time_in_cycle = 0.0
        else:
            now = time.time()
            if _charge_start_ts is None:
                _charge_start_ts = now
            time_in_cycle = now - _charge_start_ts

        reading = {
            "voltage": voltage,
            "current": current,
            "power": float(feed.get("field1") or voltage * current),
            "soc": soc,
            "time_in_cycle": time_in_cycle,
        }
        return reading, feed.get("created_at")
    except Exception:
        return None

def _resolve_source():
    
    global _last_live_ts, _last_feed_time
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

def _tick_once():
    
    resolved = _resolve_source()
    if resolved is None:
        return
    reading_dict, source = resolved

    if source == "live":
        infer_v = reading_dict["voltage"] / config.CELLS_IN_SERIES
        infer_i = reading_dict["current"] / config.CELLS_IN_PARALLEL
    else:
        infer_v, infer_i = reading_dict["voltage"], reading_dict["current"]

    session = SessionLocal()
    try:
        r = Reading(ts=datetime.now(timezone.utc),
                    voltage=reading_dict["voltage"], current=reading_dict["current"],
                    power=reading_dict["power"], soc=reading_dict["soc"], source=source)
        session.add(r)
        session.flush()

        pred = run_inference(infer_v, infer_i, reading_dict["time_in_cycle"])
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
