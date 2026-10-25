from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy import select, desc
from sqlalchemy.orm import joinedload

import config
from db import SessionLocal, init_db, Channel, Reading, Prediction, Alert
from ingest import ensure_fresh, tick
from inference import models_ready

scheduler = BackgroundScheduler(daemon=True)

def _seconds_ago(ts: datetime) -> int:
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    return int((datetime.now(timezone.utc) - ts).total_seconds())

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    with SessionLocal() as s:
        if not s.scalar(select(Channel).limit(1)):
            s.add(Channel(name="Simulink WPT Channel",
                          thingspeak_channel=config.THINGSPEAK_CHANNEL,
                          read_key=config.THINGSPEAK_READ_KEY))
            s.commit()
    tick()
    scheduler.add_job(tick, "interval", seconds=config.TICK_SECONDS, id="ingest",
                      max_instances=1, coalesce=True)
    scheduler.start()
    yield
    scheduler.shutdown(wait=False)

app = FastAPI(title="EV WPT Monitor API", version="2.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)

@app.get("/health")
def health():
    return {"status": "ok", "models_loaded": models_ready(),
            "tick_seconds": config.TICK_SECONDS}

@app.get("/api/readings/latest")
def latest_reading():
    
    ensure_fresh()
    with SessionLocal() as s:
        r = s.scalar(select(Reading).options(joinedload(Reading.prediction)).order_by(desc(Reading.id)).limit(1))
        if not r:
            return {"available": False}
        p = r.prediction
        return {
            "available": True,
            "ts": r.ts.isoformat(),
            "last_updated_seconds": _seconds_ago(r.ts),
            "source": r.source,
            "voltage": round(r.voltage, 3), "current": round(r.current, 3),
            "power": round(r.power, 2), "soc": round(r.soc, 2),
            "predicted_temp": p.predicted_temp if p else None,
            "is_anomaly": p.is_anomaly if p else None,
        }

@app.get("/api/readings")
def readings(limit: int = 100):
    
    limit = max(1, min(limit, 500))
    with SessionLocal() as s:
        rows = s.scalars(select(Reading).options(joinedload(Reading.prediction)).order_by(desc(Reading.id)).limit(limit)).all()
        rows = list(reversed(rows))
        return [{
            "ts": r.ts.isoformat(),
            "voltage": round(r.voltage, 3), "current": round(r.current, 3),
            "power": round(r.power, 2), "soc": round(r.soc, 2),
            "predicted_temp": r.prediction.predicted_temp if r.prediction else None,
        } for r in rows]

@app.get("/api/alerts")
def alerts(limit: int = 20):
    with SessionLocal() as s:
        rows = s.scalars(select(Alert).order_by(desc(Alert.id)).limit(limit)).all()
        return [{
            "ts": a.ts.isoformat(), "seconds_ago": _seconds_ago(a.ts),
            "type": a.type, "severity": a.severity,
            "message": a.message, "value": round(a.value, 3),
        } for a in rows]

@app.get("/api/analytics/summary")
def summary():
    
    with SessionLocal() as s:
        latest = s.scalar(select(Reading).options(joinedload(Reading.prediction)).order_by(desc(Reading.id)).limit(1))
        recent = s.scalars(select(Reading).options(joinedload(Reading.prediction)).order_by(desc(Reading.id)).limit(100)).all()
        n_alerts = s.scalar(select(Alert).order_by(desc(Alert.id)).limit(1))
        temps = [r.prediction.predicted_temp for r in recent if r.prediction]
        powers = [r.power for r in recent]
        return {
            "current_soc": round(latest.soc, 1) if latest else None,
            "predicted_temp": latest.prediction.predicted_temp if latest and latest.prediction else None,
            "peak_temp_recent": round(max(temps), 2) if temps else None,
            "avg_power_recent": round(sum(powers) / len(powers), 2) if powers else None,
            "readings_window": len(recent),
            "has_active_alert": n_alerts is not None and _seconds_ago(n_alerts.ts) < 60,
        }
