"""Shared helpers for the Flight x Weather export tools (AERO INSIGHTS, Flight DW 2025).

Everything in this package is READ-ONLY against MySQL:
  * every connection runs `SET SESSION TRANSACTION READ ONLY`;
  * only SELECT / EXPLAIN statements are issued;
  * no table, index, view or row in flight_dw_2025 is created, changed or deleted.

Scope and FlightKey ranges are taken from the STEP 30E3 append-only checkpoint
journal (the only checkpoint the 30E3 loader writes). They are never guessed.
"""
from __future__ import annotations

import getpass
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

TOOL_VERSION = "fw-export-1.0.0"

TOOLS_DIR = Path(__file__).resolve().parent
DASHBOARD_DIR = TOOLS_DIR.parent                      # ...\09_FINAL_HANDOFF\03_DASHBOARD
DEFAULT_PROJECT_ROOT = Path(os.getenv("FLIGHT_DW_ROOT", str(DASHBOARD_DIR.parents[1])))
EXPORT_DIR = Path(os.getenv("AERO_DATA_DIR", str(DASHBOARD_DIR / "03_EXPORT_DATA")))
WORK_DIR = DASHBOARD_DIR / "_fw_work"

EXPOSURES = ("SCHEDULED_DEPARTURE", "SCHEDULED_ARRIVAL", "ACTUAL_DEPARTURE", "ACTUAL_ARRIVAL")
DEPARTURE_EXPOSURES = ("SCHEDULED_DEPARTURE", "ACTUAL_DEPARTURE")
MONTH_NAMES = {
    "01": "January", "02": "February", "03": "March", "04": "April", "05": "May", "06": "June",
    "07": "July", "08": "August", "09": "September", "10": "October", "11": "November", "12": "December",
}
MATCHED = "MATCHED_WEATHER_HOUR"

IMPACT_FILE = "flight_weather_impact_2025.csv"
COVERAGE_FILE = "flight_weather_coverage_2025.csv"
MANIFEST_FILE = "flight_weather_manifest_2025.json"

# Data contract consumed by 02_PYTHON_SOURCE/app.py (unchanged from the integrated candidate).
IMPACT_COLUMNS = [
    "SourceMonth", "MonthNumber", "MonthName", "ExposureType", "AirportRole",
    "AirportKey", "OurAirportsID", "AirportCode", "Ident", "AirportName",
    "Municipality", "ISOCountry", "PrecipitationBand", "PrecipitationBandSort",
    "WindSpeedBand", "WindSpeedBandSort", "MatchedExposureRows",
    "MatchedExposureFlights", "MatchedWeatherObservations", "CancelledFlights",
    "DivertedFlights", "EligibleFlights", "DelayedFlights", "DelayRatePct",
    "AvgSignedDelayMinutes", "TotalPositiveDelayMinutes", "AvgTemperature",
    "AvgRelativeHumidity", "AvgPrecipitation", "AvgWindSpeed", "AvgWindGust",
    "AvgCloudCover", "AvgMinutesAfterWeatherHour",
]
COVERAGE_COLUMNS = [
    "SourceMonth", "MonthNumber", "MonthName", "ExposureType", "AirportRole",
    "AirportKey", "AirportCode", "AirportName", "ISOCountry",
    "WeatherCoverageStatus", "BridgeExposureRows", "NonNullWeatherKeys",
    "MatchedStatusMissingKeyRows", "NonMatchedStatusHasKeyRows",
]
PRECIP_BANDS = {1: "Dry (0)", 2: "Wet (0-1]", 3: "Wet (1-5]", 4: "Wet (>5)"}
WIND_BANDS = {1: "0-10", 2: "(10-20]", 3: "(20-40]", 4: ">40"}


def say(msg: str) -> None:
    print(msg, flush=True)


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def atomic_write_csv(frame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    frame.to_csv(tmp, index=False, encoding="utf-8", lineterminator="\n")
    os.replace(tmp, path)


def role_of(exposure: str) -> str:
    return "ORIGIN" if exposure in DEPARTURE_EXPOSURES else "DESTINATION"


# ----------------------------------------------------------------------------- evidence files
def default_journal_path(root: Path) -> Path:
    return root / "06_DW_DESIGN" / "02_PHYSICAL_MODEL" / "_checkpoints" / "30E3_flight_weather_bridge_checkpoint_journal.jsonl"


def default_preview_path(root: Path) -> Path | None:
    folder = root / "06_DW_DESIGN" / "02_PHYSICAL_MODEL"
    candidates = sorted(folder.glob("30E3_flight_weather_bridge_preview_*.json"))
    return candidates[-1] if candidates else None


def read_journal(path: Path) -> dict[str, Any]:
    """Return fingerprint ranges + latest valid snapshot from the append-only journal."""
    if not path.is_file():
        raise FileNotFoundError(f"STEP 30E3 journal not found: {path}")
    last = None
    fingerprints = set()
    lines = 0
    with path.open("r", encoding="utf-8-sig") as fh:
        for line in fh:
            if not line.strip():
                continue
            try:
                state = json.loads(line)
            except json.JSONDecodeError:
                continue  # a torn final line is ignored, same rule as the loader
            lines += 1
            fingerprints.add(json.dumps(state.get("Fingerprint"), sort_keys=True))
            last = state
    if last is None:
        raise ValueError(f"No valid snapshot in journal: {path}")
    if len(fingerprints) != 1:
        raise ValueError(f"Journal contains {len(fingerprints)} different fingerprints; investigate before export.")
    fp = last["Fingerprint"]
    partitions = {}
    for key, meta in fp["Partitions"].items():
        month, exposure = key.split("|")
        state = last["Partitions"].get(key, {})
        complete = (int(state.get("CompletedSourceRows", 0)) == int(meta["Rows"])
                    and state.get("DatabaseValidation") == "PASS")
        partitions[key] = {
            "SourceMonth": month, "ExposureType": exposure,
            "ExpectedRows": int(meta["Rows"]),
            "FirstFlightKey": int(meta["FirstFlightKey"]), "LastFlightKey": int(meta["LastFlightKey"]),
            "JournalCompletedRows": int(state.get("CompletedSourceRows", 0)),
            "JournalDatabaseValidation": state.get("DatabaseValidation"),
            "JournalComplete": complete,
        }
    return {
        "Path": str(path), "SHA256": sha256_file(path), "Lines": lines,
        "BridgeRunID": fp.get("BridgeRunID"), "Partitions": partitions,
    }


def read_preview(path: Path | None) -> dict[str, Any] | None:
    if path is None or not path.is_file():
        return None
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if data.get("Step") != "30E3" or data.get("Result") != "PASS":
        raise ValueError(f"Unexpected preview file (not a 30E3 PASS preview): {path}")
    per = {f"{x['SourceMonth']}|{x['ExposureType']}": x for x in data["FileSummaries"]}
    return {"Path": str(path), "BridgeRunID": data.get("BridgeRunID"), "Partitions": per}


def month_ranges(journal: dict[str, Any]) -> dict[str, tuple[int, int]]:
    out: dict[str, tuple[int, int]] = {}
    for p in journal["Partitions"].values():
        rng = (p["FirstFlightKey"], p["LastFlightKey"])
        prev = out.setdefault(p["SourceMonth"], rng)
        if prev != rng:
            raise ValueError(f"Inconsistent FlightKey range for month {p['SourceMonth']}")
    return dict(sorted(out.items()))


def chunks(first: int, last: int, size: int):
    start = first
    while start <= last:
        end = min(start + size - 1, last)
        yield start, end
        start = end + 1


# ----------------------------------------------------------------------------- MySQL (read-only)
def connect_readonly(args):
    try:
        import mysql.connector  # type: ignore
    except ImportError:
        sys.exit("mysql-connector-python is not installed. Run: python -m pip install -r 06_FW_TOOLS\\requirements_tools.txt")
    host = args.host or os.getenv("FLIGHT_DW_DB_HOST", "127.0.0.1")
    port = int(args.port or os.getenv("FLIGHT_DW_DB_PORT", "3306"))
    database = args.database or os.getenv("FLIGHT_DW_DB_NAME", "flight_dw_2025")
    user = args.user or os.getenv("FLIGHT_DW_DB_USER") or input("MySQL user: ").strip()
    password = os.getenv("FLIGHT_DW_DB_PASSWORD")
    if password is None:
        password = getpass.getpass("MySQL password (hidden): ")
    conn = mysql.connector.connect(
        host=host, port=port, database=database, user=user, password=password,
        autocommit=True, connection_timeout=30, charset="utf8mb4", use_unicode=True,
    )
    cur = conn.cursor()
    cur.execute("SET SESSION TRANSACTION READ ONLY")
    cur.execute("SELECT @@transaction_read_only, VERSION(), DATABASE()")
    ro, version, db = cur.fetchone()
    cur.close()
    if int(ro) != 1:
        conn.close()
        sys.exit("Could not put the session into READ ONLY mode; aborting.")
    say(f"[DB] Connected read-only to {db} on {host}:{port} (MySQL {version}).")
    return conn


def add_db_args(parser) -> None:
    parser.add_argument("--host")
    parser.add_argument("--port")
    parser.add_argument("--database")
    parser.add_argument("--user")


def add_path_args(parser) -> None:
    parser.add_argument("--project-root", type=Path, default=DEFAULT_PROJECT_ROOT,
                        help="D:\\DATA_WAREHOUSE (default derived from tool location or FLIGHT_DW_ROOT)")
    parser.add_argument("--journal", type=Path, help="Override path to 30E3 checkpoint journal .jsonl")
    parser.add_argument("--preview", type=Path, help="Override path to 30E3 preview .json")


def resolve_evidence(args) -> tuple[dict[str, Any], dict[str, Any] | None]:
    journal_path = args.journal or default_journal_path(args.project_root)
    preview_path = args.preview or default_preview_path(args.project_root)
    journal = read_journal(journal_path)
    preview = read_preview(preview_path)
    if preview and preview["BridgeRunID"] != journal["BridgeRunID"]:
        raise ValueError("Preview BridgeRunID differs from journal BridgeRunID")
    if preview:
        for key, p in journal["Partitions"].items():
            pv = preview["Partitions"].get(key)
            if pv is None or int(pv["RowsValidated"]) != p["ExpectedRows"]:
                raise ValueError(f"Preview/journal row mismatch for {key}")
    return journal, preview
