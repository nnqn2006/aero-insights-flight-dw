# CHANGELOG — 02_PYTHON_SOURCE/app.py

Base: the app running on the user's machine (SHA256 `9e6e9640…`, identical to `app_flight_weather_integrated_candidate.py`).

## Unchanged (locked by `07_TESTS/protected_functions.json`)
- 44 of the 45 Gold-page functions shared with v2 (Overview, Airlines, Airports, Time): byte-identical.
- All 11 Weather-page functions: byte-identical.

## Bug fix in one Gold callback (approved change, recorded in protected_functions.json)
- `update_airline_charts`: the callback declares 11 outputs, but its "no airline selected" branch returned only 10 values.
  Clearing the airline selector therefore raised HTTP 500 (bug present since v2). It now returns 8 empty figures.
  This is a one-line change; non-empty selections behave exactly as before.

## Flight × Weather page
- Loads `flight_weather_manifest_2025.json` and checks both CSVs against the SHA256 in the manifest.
  The status banner shows: validated / no manifest / integrity failure.
- The scope label and the month dropdown come from the installed snapshot and manifest instead of a hard-coded "Jan–Sep".
- Country filter: a cleared multi-select (`[]`) now means "all countries". Previously it filtered everything out.
- Weather-match coverage KPI: the numerator now counts `MATCHED_WEATHER_HOUR` rows from the coverage export, the same source
  as the denominator. Rows excluded from impact therefore cannot distort coverage.
- CSVs are read with `SourceMonth` as text, which preserves the leading zero.
- Empty-state text points to the new tools (`fw_extract.py`, `fw_validate.py`).

## Deployment
- `server = app.server` (WSGI entry: `gunicorn --chdir 02_PYTHON_SOURCE app:server`).
- `GET /health` returns JSON with the Gold row counts, the Flight × Weather rows, the scope and the manifest integrity. No secrets are included.
- `python app.py` reads the `HOST` (default `127.0.0.1`) and `PORT` (default `8050`) environment variables, so local behaviour is unchanged.
