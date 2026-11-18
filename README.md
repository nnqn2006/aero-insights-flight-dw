# AERO INSIGHTS | Flight DW 2025

Interactive Dash dashboard over the Flight Data Warehouse 2025 (BTS on-time performance + Open-Meteo hourly weather).
It runs in **snapshot mode**: it reads the CSV files in `03_EXPORT_DATA/` and never connects to a database.

## Pages
Overview Â· Airline intelligence Â· Airport intelligence Â· Time intelligence Â· Weather intelligence Â· **Flight x Weather**

## Scope and honest limits
- Flight x Weather covers **January-September 2025 only** (Bridge partitions 01-09 verified; months 10-12 are not loaded).
- Counts are *exposure events* (scheduled/actual departure/arrival); they are never added across exposure types.
- All weather associations are **descriptive, not causal**.
- Integrity of the two Flight x Weather CSVs is checked at start-up against `flight_weather_manifest_2025.json` (SHA256).

## Layout
| Path | Purpose |
|---|---|
| `02_PYTHON_SOURCE/app.py` | Dash application (`app:server` for gunicorn) |
| `03_EXPORT_DATA/` | Gold + weather + Flight x Weather snapshots, manifest, QA report |
| `04_CSS/` | Dash assets (styles) |
| `05_SQL_EXPORTS/` | Optional read-only verification SQL |
| `06_FW_TOOLS/` | Extractor / validator used on the machine that has the MySQL warehouse (not needed to run the dashboard) |
| `07_TESTS/` | `test_dashboard.py` - routes, callbacks, protected-function fingerprints |
| `docs/` | Step-by-step guide and change log |

## Run locally
```
pip install -r requirements.txt
python 02_PYTHON_SOURCE/app.py          # http://127.0.0.1:8050
python 07_TESTS/test_dashboard.py       # expects: RESULT: PASS
```

## Deploy
`Procfile` and `Dockerfile` are included (gunicorn, `PORT` env var, health check at `/health`).
No secrets are required. Never commit database passwords; `.gitignore` already excludes `.env` files.

## Data sources
- U.S. DOT Bureau of Transportation Statistics (BTS) on-time performance data.
- Weather data by [Open-Meteo.com](https://open-meteo.com/) (CC BY 4.0).
