import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(__file__)

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable must be set (Postgres required).")

TICK_SECONDS = int(os.getenv("TICK_SECONDS", "3"))

STALE_SECONDS = int(os.getenv("STALE_SECONDS", "60"))

OVER_TEMP_C = float(os.getenv("OVER_TEMP_C", "38"))

MAX_READINGS = int(os.getenv("MAX_READINGS", "5000"))

THINGSPEAK_CHANNEL = os.getenv("THINGSPEAK_CHANNEL", "")
THINGSPEAK_READ_KEY = os.getenv("THINGSPEAK_READ_KEY", "")

CELLS_IN_SERIES = int(os.getenv("CELLS_IN_SERIES", "105"))
CELLS_IN_PARALLEL = int(os.getenv("CELLS_IN_PARALLEL", "5"))

DEMO_CSV = os.path.join(BASE_DIR, "data", "demo_cycles.csv")
