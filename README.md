# EV Wireless Power Transfer (WPT) Monitor

A full-stack, real-time telemetry dashboard for wireless power transfer EV charging. The system ingests voltage, current, power, and state-of-charge data from ThingSpeak when configured, runs two production machine-learning models, stores readings in PostgreSQL, and presents the results in a React dashboard.

## Active architecture

```mermaid
flowchart LR
    A[MATLAB / Simulink] -->|Optional live feed| B(ThingSpeak)
    B -->|Ingest worker| C{FastAPI backend}
    C -->|Store| D[(PostgreSQL)]
    C <-->|ML inference| E[Temperature + Anomaly models]
    C -->|REST / JSON| F[React frontend]
    C -->|Fallback| G[demo_cycles.csv replay]
```

The backend uses a three-tier source resolver. It first accepts genuinely new ThingSpeak data, falls back to the recorded `webdev/backend/data/demo_cycles.csv` stream when no live source is configured or available, and preserves the last stored reading when a configured live source has temporarily stopped producing new data. The dashboard indicates freshness and source status without connecting to ThingSpeak directly.

## Machine-learning models

| Model | Type | Input | Dashboard use |
|---|---|---|---|
| Temperature soft-sensor | Physics-constrained gradient boosting (monotonic in current and heat) | Equivalent cell charging current, ambient temperature, and two exponentially filtered I² heat terms (τ = 300 s and 1200 s) | Temperature gauge and over-temperature alerts |
| Anomaly detector | Unsupervised One-Class SVM (standardised features) | Pack voltage, current and power | Anomaly status and alerts |

The temperature soft-sensor is trained on **charge** cycles of the NASA Li-ion Battery Aging dataset (CC 1.5 A to 4.2 V, then CV; ambient 4, 24 and 43 °C). Only cycles that start within 3 °C of ambient are used, so the temperature rise comes from charging rather than heat left over from a previous discharge. It predicts the rise above ambient and is evaluated on batteries held out from training (MAE ≈ 0.58 °C).

The anomaly detector learns the charger's normal electrical operating envelope from `ml/data/wpt_telemetry.csv`, a snapshot of the Simulink WPT telemetry on ThingSpeak channel 3311497. It does not use temperature, because the predicted temperature is derived from current and could never reveal a fault. On held-out normal readings it raises no false alarms, and it flags all 71 real glitch readings in the channel and four hand-made fault cases (coupling loss, overcurrent, voltage sag, power sensor mismatch); see `ml/reports/metrics.json`. Refresh the snapshot with `THINGSPEAK_CHANNEL=… THINGSPEAK_READ_KEY=… python ml/get_data.py --telemetry`.

Pack readings are mapped to an equivalent NASA cell at the same C-rate: `i_cell = -I_pack × CELL_CAPACITY_AH / PACK_CAPACITY_AH` (Simscape uses negative current for charging). The processed dataset `ml/data/nasa_charge_30s.csv.gz` is committed, so the Render build only trains the models. To rebuild it from the original NASA archive, run `python ml/get_data.py --rebuild` (needs `scipy`). The replay stream `webdev/backend/data/demo_cycles.csv` is the clean part of the telemetry snapshot, regenerated with `python ml/get_data.py --demo`.

## Repository layout

| Path | Purpose |
|---|---|
| `ml/` | Dataset download, feature preparation, model training, and runtime inference |
| `webdev/backend/` | FastAPI service, scheduled ingestion, replay fallback, database models, and alerts |
| `webdev/frontend/` | Vite/React dashboard for telemetry, charts, model information, and architecture |

