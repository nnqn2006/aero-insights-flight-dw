"""AERO INSIGHTS | Flight x Weather read-only extractor (Flight DW 2025).

Sub-commands (run them in this order):
  verify   Read-only check of Bridge partitions in MySQL against the 30E3 journal + preview.
  explain  Show the execution plan (EXPLAIN) for one partition chunk.
  run      Export matched-impact + coverage aggregates partition by partition
           (SourceMonth x ExposureType), sequentially, with checkpoints.
  merge    Combine finished partitions into the two dashboard CSVs + manifest.
  status   Show which partitions are verified / exported.

Why it is fast where the 9-month query timed out
  * Every query is restricted by the Bridge PRIMARY KEY prefix (FlightKey BETWEEN a AND b),
    using exact month ranges from the 30E3 journal fingerprint. SourceMonth has no index.
  * Each month is processed in FlightKey chunks (default 50,000 flights); a chunk that hits
    MAX_EXECUTION_TIME is split in half automatically.
  * Rows are streamed and aggregated in pandas, so COUNT(DISTINCT), averages and weighted
    rates stay exact without a giant GROUP BY / temp table / filesort in MySQL.
  * Only one query runs at a time. Session is READ ONLY. No DDL/DML is ever sent.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fw_common as C  # noqa: E402

PARTIALS = C.WORK_DIR / "partials"
VERIFY_JSON = C.WORK_DIR / "bridge_verification.json"
VERIFY_TXT = C.WORK_DIR / "bridge_verification.txt"

# --------------------------------------------------------------------------- SQL (SELECT only)
VERIFY_SQL = """
SELECT /*+ MAX_EXECUTION_TIME({ms}) */
       b.ExposureType, b.WeatherCoverageStatus, b.SegmentSequence,
       COUNT(*)                                   AS BridgeRows,
       MIN(b.FlightKey)                           AS MinFlightKey,
       MAX(b.FlightKey)                           AS MaxFlightKey,
       SUM(b.SourceMonth <> %s)                   AS WrongMonthRows,
       SUM(b.WeatherKey IS NOT NULL)              AS NonNullWeatherKeys,
       SUM(b.WeatherCoverageStatus = 'MATCHED_WEATHER_HOUR'
           AND (b.WeatherKey IS NULL OR b.WeatherNaturalKey IS NULL)) AS MatchedStatusMissingKeyRows,
       SUM(b.WeatherCoverageStatus <> 'MATCHED_WEATHER_HOUR'
           AND b.WeatherKey IS NOT NULL)          AS NonMatchedStatusHasKeyRows
FROM bridge_flight_weather_exposure AS b FORCE INDEX (PRIMARY)
WHERE b.FlightKey BETWEEN %s AND %s
GROUP BY b.ExposureType, b.WeatherCoverageStatus, b.SegmentSequence
"""

COVERAGE_SQL = """
SELECT /*+ MAX_EXECUTION_TIME({ms}) */
       b.ExposureType, b.AirportKey, b.OurAirportsID, b.WeatherCoverageStatus,
       COUNT(*)                                   AS BridgeExposureRows,
       SUM(b.WeatherKey IS NOT NULL)              AS NonNullWeatherKeys,
       SUM(b.WeatherCoverageStatus = 'MATCHED_WEATHER_HOUR'
           AND (b.WeatherKey IS NULL OR b.WeatherNaturalKey IS NULL)) AS MatchedStatusMissingKeyRows,
       SUM(b.WeatherCoverageStatus <> 'MATCHED_WEATHER_HOUR'
           AND b.WeatherKey IS NOT NULL)          AS NonMatchedStatusHasKeyRows
FROM bridge_flight_weather_exposure AS b FORCE INDEX (PRIMARY)
WHERE b.FlightKey BETWEEN %s AND %s
  AND b.ExposureType IN ({exposures})
  AND b.SegmentSequence = 1
GROUP BY b.ExposureType, b.AirportKey, b.OurAirportsID, b.WeatherCoverageStatus
"""

# Row stream of matched exposures. Band thresholds are evaluated in MySQL on the exact DECIMAL
# values; integrity checks are returned as 0/1 flags so bad rows are counted, never hidden.
IMPACT_SQL = """
SELECT /*+ MAX_EXECUTION_TIME({ms}) */
       b.ExposureType, b.AirportKey, b.OurAirportsID, b.WeatherKey,
       b.MinutesAfterWeatherHour,
       f.FlightCount, f.Cancelled, f.Diverted,
       f.DepDel15, f.DepDelay, f.DepDelayMinutes,
       f.ArrDel15, f.ArrDelay, f.ArrDelayMinutes,
       CASE WHEN w.Precipitation = 0 THEN 1 WHEN w.Precipitation <= 1 THEN 2
            WHEN w.Precipitation <= 5 THEN 3 ELSE 4 END              AS PrecipitationBandSort,
       CASE WHEN w.WindSpeed10m <= 10 THEN 1 WHEN w.WindSpeed10m <= 20 THEN 2
            WHEN w.WindSpeed10m <= 40 THEN 3 ELSE 4 END              AS WindSpeedBandSort,
       CAST(w.Temperature2m AS DOUBLE)      AS Temperature2m,
       CAST(w.RelativeHumidity2m AS DOUBLE) AS RelativeHumidity2m,
       CAST(w.Precipitation AS DOUBLE)      AS Precipitation,
       CAST(w.WindSpeed10m AS DOUBLE)       AS WindSpeed10m,
       CAST(w.WindGusts10m AS DOUBLE)       AS WindGusts10m,
       CAST(w.CloudCover AS DOUBLE)         AS CloudCover,
       (f.FlightKey IS NULL)                                         AS FlagMissingFlight,
       (f.FlightKey IS NOT NULL AND f.SourceMonth <> b.SourceMonth)  AS FlagFlightMonthMismatch,
       (b.SourceMonth <> %s)                                         AS FlagBridgeMonthMismatch,
       (w.WeatherKey IS NULL)                                        AS FlagMissingWeather,
       (w.WeatherKey IS NOT NULL AND (w.OurAirportsID <> b.OurAirportsID
                                      OR w.WeatherHourUTC <> b.WeatherHourUTC)) AS FlagNaturalKeyMismatch,
       (f.FlightKey IS NOT NULL AND CASE
            WHEN b.ExposureType IN ('SCHEDULED_DEPARTURE','ACTUAL_DEPARTURE')
                 THEN b.AirportKey <> f.OriginAirportKey
            ELSE b.AirportKey <> f.DestinationAirportKey END)        AS FlagRoleMismatch
FROM bridge_flight_weather_exposure AS b FORCE INDEX (PRIMARY)
LEFT JOIN fact_flight AS f ON f.FlightKey = b.FlightKey
LEFT JOIN fact_airport_weather_hourly AS w ON w.WeatherKey = b.WeatherKey
WHERE b.FlightKey BETWEEN %s AND %s
  AND b.ExposureType IN ({exposures})
  AND b.SegmentSequence = 1
  AND b.WeatherCoverageStatus = 'MATCHED_WEATHER_HOUR'
"""
IMPACT_FIELDS = [
    "ExposureType", "AirportKey", "OurAirportsID", "WeatherKey", "MinutesAfterWeatherHour",
    "FlightCount", "Cancelled", "Diverted", "DepDel15", "DepDelay", "DepDelayMinutes",
    "ArrDel15", "ArrDelay", "ArrDelayMinutes", "PrecipitationBandSort", "WindSpeedBandSort",
    "Temperature2m", "RelativeHumidity2m", "Precipitation", "WindSpeed10m", "WindGusts10m", "CloudCover",
    "FlagMissingFlight", "FlagFlightMonthMismatch", "FlagBridgeMonthMismatch", "FlagMissingWeather",
    "FlagNaturalKeyMismatch", "FlagRoleMismatch",
]
FLAGS = [f for f in IMPACT_FIELDS if f.startswith("Flag")]

DIM_SQL = """
SELECT AirportKey, OurAirportsID,
       COALESCE(NULLIF(IATACode,''), NULLIF(ICAOCode,''), Ident) AS AirportCode,
       Ident, AirportName, Municipality, ISOCountry
FROM dim_airport WHERE AirportKey IN ({keys})
"""

TIMEOUT_ERRNO = {3024}            # ER_QUERY_TIMEOUT (MAX_EXECUTION_TIME exceeded)
LOST_CONN_ERRNO = {2006, 2013, 2055}


# --------------------------------------------------------------------------- execution helpers
class Session:
    """Holds one read-only connection; reconnects on lost connection."""

    def __init__(self, args):
        self.args = args
        self.conn = C.connect_readonly(args)

    def reconnect(self):
        try:
            self.conn.close()
        except Exception:
            pass
        C.say("[DB] Reconnecting (read-only)...")
        self.conn = C.connect_readonly(self.args)

    def fetch(self, sql: str, params: tuple, stream: bool = False) -> list[tuple]:
        cur = self.conn.cursor(buffered=not stream)
        try:
            cur.execute(sql, params)
            if not stream:
                return cur.fetchall()
            rows: list[tuple] = []
            while True:
                part = cur.fetchmany(50_000)
                if not part:
                    break
                rows.extend(part)
            return rows
        finally:
            cur.close()

    def close(self):
        try:
            self.conn.close()
        except Exception:
            pass


def run_chunked(session: Session, sql_template: str, ranges: list[tuple[int, int]], params_fn,
                ms: int, stream: bool, label: str, min_chunk: int = 5_000, consumer=None) -> list[tuple]:
    """Execute a range query over FlightKey chunks; split a chunk on timeout, retry on lost connection."""
    import mysql.connector  # type: ignore
    out: list[tuple] = []
    queue = list(ranges)
    while queue:
        lo, hi = queue.pop(0)
        attempts = 0
        while True:
            t0 = time.perf_counter()
            try:
                rows = session.fetch(sql_template.format(ms=ms), params_fn(lo, hi), stream=stream)
                if consumer is not None:
                    consumer(rows)          # aggregate this chunk now; raw rows are released
                else:
                    out.extend(rows)
                C.say(f"      {label} FlightKey {lo:,}..{hi:,}: {len(rows):,} rows in {time.perf_counter() - t0:,.1f}s")
                break
            except mysql.connector.Error as exc:
                errno = getattr(exc, "errno", None)
                if errno in TIMEOUT_ERRNO and hi - lo + 1 > min_chunk:
                    mid = (lo + hi) // 2
                    C.say(f"      {label} chunk {lo:,}..{hi:,} hit MAX_EXECUTION_TIME; splitting in half.")
                    queue[0:0] = [(lo, mid), (mid + 1, hi)]
                    break
                if errno in LOST_CONN_ERRNO and attempts < 2:
                    attempts += 1
                    session.reconnect()
                    continue
                raise
    return out


# --------------------------------------------------------------------------- VERIFY
def cmd_verify(args) -> int:
    journal, preview = C.resolve_evidence(args)
    ranges = C.month_ranges(journal)
    C.say(f"[EVIDENCE] Journal {journal['Path']} ({journal['Lines']:,} snapshots, BridgeRunID {journal['BridgeRunID']})")
    C.say(f"[EVIDENCE] Preview {preview['Path'] if preview else 'NOT FOUND (matched-count check skipped)'}")
    session = Session(args)
    results: dict[str, Any] = {}
    try:
        for month, (first, last) in ranges.items():
            C.say(f"[VERIFY] Month {month}: FlightKey {first:,}..{last:,}")
            rows = run_chunked(session, VERIFY_SQL, list(C.chunks(first, last, args.chunk_size)),
                               lambda lo, hi, m=month: (m, lo, hi), args.max_exec_ms, False, f"verify {month}")
            agg: dict[str, dict[str, Any]] = {}
            for exp, status, seg, n, mn, mx, wrong, nonnull, mk, nk in rows:
                a = agg.setdefault(exp, {"BridgeRows": 0, "MinFlightKey": None, "MaxFlightKey": None,
                                         "WrongMonthRows": 0, "NonSegment1Rows": 0, "NonNullWeatherKeys": 0,
                                         "MatchedStatusMissingKeyRows": 0, "NonMatchedStatusHasKeyRows": 0,
                                         "StatusCounts": {}})
                a["BridgeRows"] += int(n)
                a["MinFlightKey"] = int(mn) if a["MinFlightKey"] is None else min(a["MinFlightKey"], int(mn))
                a["MaxFlightKey"] = int(mx) if a["MaxFlightKey"] is None else max(a["MaxFlightKey"], int(mx))
                a["WrongMonthRows"] += int(wrong or 0)
                a["NonSegment1Rows"] += int(n) if int(seg) != 1 else 0
                a["NonNullWeatherKeys"] += int(nonnull or 0)
                a["MatchedStatusMissingKeyRows"] += int(mk or 0)
                a["NonMatchedStatusHasKeyRows"] += int(nk or 0)
                a["StatusCounts"][status] = a["StatusCounts"].get(status, 0) + int(n)
            unexpected = sorted(set(agg) - set(C.EXPOSURES))
            if unexpected:
                raise RuntimeError(f"Unexpected ExposureType values in month {month}: {unexpected}")
            for exp in C.EXPOSURES:
                key = f"{month}|{exp}"
                jp = journal["Partitions"][key]
                db = agg.get(exp, {"BridgeRows": 0, "StatusCounts": {}})
                matched = db["StatusCounts"].get(C.MATCHED, 0)
                pv = preview["Partitions"].get(key) if preview else None
                checks = {}
                if db["BridgeRows"] == 0:
                    verdict = "NOT_LOADED" if not jp["JournalComplete"] else "FAIL_JOURNAL_SAYS_LOADED_BUT_DB_EMPTY"
                else:
                    checks = {
                        "JournalComplete": jp["JournalComplete"],
                        "RowsEqualExpected": db["BridgeRows"] == jp["ExpectedRows"],
                        "MinKeyOK": db["MinFlightKey"] == jp["FirstFlightKey"],
                        "MaxKeyOK": db["MaxFlightKey"] == jp["LastFlightKey"],
                        "NoWrongMonthRows": db["WrongMonthRows"] == 0,
                        "OnlySegment1": db["NonSegment1Rows"] == 0,
                        "MatchedHaveKeys": db["NonNullWeatherKeys"] == matched and db["MatchedStatusMissingKeyRows"] == 0,
                        "NonMatchedHaveNoKey": db["NonMatchedStatusHasKeyRows"] == 0,
                        "MatchedEqualsPreview": (pv is None) or matched == int(pv["MatchedRows"]),
                    }
                    if all(checks.values()):
                        verdict = "VERIFIED"
                    elif not jp["JournalComplete"]:
                        verdict = "PARTIAL_IN_DB_DO_NOT_USE"
                    else:
                        verdict = "FAIL"
                results[key] = {**jp, "DB": db, "PreviewMatchedRows": int(pv["MatchedRows"]) if pv else None,
                                "Checks": checks, "Verdict": verdict}
                C.say(f"      {key:<24} DB rows {db['BridgeRows']:>9,} / expected {jp['ExpectedRows']:>9,}  -> {verdict}")
    finally:
        session.close()

    verified = [k for k, v in results.items() if v["Verdict"] == "VERIFIED"]
    failed = [k for k, v in results.items() if v["Verdict"].startswith("FAIL")]
    partial = [k for k, v in results.items() if v["Verdict"].startswith("PARTIAL")]
    report = {
        "Tool": C.TOOL_VERSION, "GeneratedAtUTC": C.now_utc(),
        "Journal": {k: journal[k] for k in ("Path", "SHA256", "Lines", "BridgeRunID")},
        "Preview": preview["Path"] if preview else None,
        "VerifiedPartitions": verified, "FailedPartitions": failed, "PartialPartitions": partial,
        "NotLoadedPartitions": [k for k, v in results.items() if v["Verdict"] == "NOT_LOADED"],
        "VerifiedRows": sum(results[k]["DB"]["BridgeRows"] for k in verified),
        "Partitions": results,
        "Result": "FAIL" if (failed or not verified) else ("PASS_WITH_WARNINGS" if partial else "PASS"),
    }
    C.atomic_write_text(VERIFY_JSON, json.dumps(report, indent=2, ensure_ascii=False))
    lines = [
        "BRIDGE VERIFICATION (read-only) — Flight DW 2025",
        f"Generated UTC : {report['GeneratedAtUTC']}",
        f"Journal       : {journal['Path']}",
        f"Result        : {report['Result']}",
        f"Verified      : {len(verified)} partitions, {report['VerifiedRows']:,} Bridge rows",
        f"Not loaded    : {len(report['NotLoadedPartitions'])} partitions",
        f"Failed        : {len(failed)} {failed}",
        f"Partial (WARN): {len(partial)} {partial}  <- rows exist in DB for a partition the journal never completed; excluded",
        "",
        f"{'Partition':<26}{'DB rows':>12}{'Expected':>12}{'Matched':>12}{'Preview':>12}  Verdict",
    ]
    for key, v in results.items():
        lines.append(f"{key:<26}{v['DB']['BridgeRows']:>12,}{v['ExpectedRows']:>12,}"
                     f"{v['DB']['StatusCounts'].get(C.MATCHED, 0):>12,}"
                     f"{(v['PreviewMatchedRows'] if v['PreviewMatchedRows'] is not None else 0):>12,}  {v['Verdict']}")
    C.atomic_write_text(VERIFY_TXT, "\n".join(lines) + "\n")
    C.say("\n" + "\n".join(lines[:8]))
    C.say(f"\nReport: {VERIFY_TXT}")
    return 2 if report["Result"] == "FAIL" else 0


def load_verification() -> dict[str, Any]:
    if not VERIFY_JSON.is_file():
        sys.exit("Run `python 06_FW_TOOLS\\fw_extract.py verify` first (no verification report found).")
    return json.loads(VERIFY_JSON.read_text(encoding="utf-8"))


# --------------------------------------------------------------------------- AGGREGATION
def _round_half_away(values: pd.Series, digits: int) -> pd.Series:
    factor = 10 ** digits
    arr = values.to_numpy(dtype="float64")
    return pd.Series(np.sign(arr) * np.floor(np.abs(arr) * factor + 0.5 + 1e-9) / factor, index=values.index)


KEYS = ["ExposureType", "AirportKey", "OurAirportsID", "PrecipitationBandSort", "WindSpeedBandSort"]
WEATHER_COLS = {"Temperature2m": "AvgTemperature", "RelativeHumidity2m": "AvgRelativeHumidity",
                "Precipitation": "AvgPrecipitation", "WindSpeed10m": "AvgWindSpeed", "WindGusts10m": "AvgWindGust",
                "CloudCover": "AvgCloudCover", "MinutesAfterWeatherHour": "AvgMinutesAfterWeatherHour"}
ROUNDING = {"AvgTemperature": 2, "AvgRelativeHumidity": 2, "AvgPrecipitation": 3, "AvgWindSpeed": 2,
            "AvgWindGust": 2, "AvgCloudCover": 2, "AvgMinutesAfterWeatherHour": 2}


class ImpactAccumulator:
    """Chunk-by-chunk exact aggregation. Every stored measure is additive (sums and counts);
    DISTINCT WeatherKey is kept exact via de-duplicated (group, WeatherKey) pairs."""

    def __init__(self):
        self.partials: list[pd.DataFrame] = []
        self.pairs: list[pd.DataFrame] = []
        self.flags: dict[str, dict[str, int]] = {}

    def add(self, rows: list[tuple]) -> None:
        if not rows:
            return
        raw = pd.DataFrame(rows, columns=IMPACT_FIELDS)
        for col in FLAGS:
            raw[col] = pd.to_numeric(raw[col], errors="coerce").fillna(0).astype("int64")
        for exp, grp in raw.groupby("ExposureType"):
            acc = self.flags.setdefault(exp, {f: 0 for f in FLAGS} | {"ExcludedRows": 0})
            for col in FLAGS:
                acc[col] += int(grp[col].sum())
            acc["ExcludedRows"] += int((grp[FLAGS].sum(axis=1) > 0).sum())
        d = raw.loc[raw[FLAGS].sum(axis=1) == 0].copy()
        del raw
        if d.empty:
            return
        d["AirportKey"] = d["AirportKey"].astype("int64")
        d["OurAirportsID"] = d["OurAirportsID"].astype("int64")
        d["PrecipitationBandSort"] = d["PrecipitationBandSort"].astype("int64")
        d["WindSpeedBandSort"] = d["WindSpeedBandSort"].astype("int64")
        for col in ["FlightCount", "Cancelled", "Diverted", "DepDel15", "DepDelay", "DepDelayMinutes",
                    "ArrDel15", "ArrDelay", "ArrDelayMinutes", *WEATHER_COLS]:
            d[col] = pd.to_numeric(d[col], errors="coerce").astype("float64")
        fc = d["FlightCount"]
        dep = d["ExposureType"].isin(C.DEPARTURE_EXPOSURES)
        not_cx = d["Cancelled"].eq(0)
        arr_ok = not_cx & d["Diverted"].eq(0)
        elig = np.where(dep, not_cx & d["DepDel15"].notna(), arr_ok & d["ArrDel15"].notna())
        dly = np.where(dep, not_cx & d["DepDel15"].eq(1), arr_ok & d["ArrDel15"].eq(1))
        sd_ok = np.where(dep, not_cx & d["DepDelay"].notna(), arr_ok & d["ArrDelay"].notna())
        sd_val = np.where(dep, d["DepDelay"], d["ArrDelay"])
        pos_ok = np.where(dep, not_cx & d["DepDelayMinutes"].notna(), arr_ok & d["ArrDelayMinutes"].notna())
        pos_val = np.where(dep, d["DepDelayMinutes"], d["ArrDelayMinutes"])
        m = pd.DataFrame({k: d[k] for k in KEYS})
        m["MatchedExposureRows"] = 1
        m["MatchedExposureFlights"] = fc
        m["CancelledFlights"] = np.where(d["Cancelled"].eq(1), fc, 0)
        m["DivertedFlights"] = np.where(d["Diverted"].eq(1), fc, 0)
        m["EligibleFlights"] = np.where(elig, fc, 0)
        m["DelayedFlights"] = np.where(dly, fc, 0)
        m["_sd_num"] = np.where(sd_ok, np.nan_to_num(sd_val) * fc, 0.0)
        m["_sd_den"] = np.where(sd_ok, fc, 0)
        m["TotalPositiveDelayMinutes"] = np.where(pos_ok, np.nan_to_num(pos_val) * fc, 0.0)
        for col in WEATHER_COLS:
            m[f"_sum_{col}"] = d[col].fillna(0.0)
            m[f"_cnt_{col}"] = d[col].notna().astype("int64")
        self.partials.append(m.groupby(KEYS, sort=False).sum().reset_index())
        pairs = d[KEYS + ["WeatherKey"]].drop_duplicates()
        pairs["WeatherKey"] = pairs["WeatherKey"].astype("int64")
        self.pairs.append(pairs)

    def finalize(self, exposure: str) -> tuple[pd.DataFrame, dict[str, int]]:
        flags = self.flags.get(exposure, {f: 0 for f in FLAGS} | {"ExcludedRows": 0})
        parts = [p[p["ExposureType"] == exposure] for p in self.partials]
        parts = [p for p in parts if not p.empty]
        if not parts:
            return pd.DataFrame(), flags
        out = pd.concat(parts, ignore_index=True).groupby(KEYS, sort=True).sum().reset_index()
        pairs = pd.concat([p[p["ExposureType"] == exposure] for p in self.pairs], ignore_index=True).drop_duplicates()
        distinct = pairs.groupby(KEYS).size().rename("MatchedWeatherObservations").reset_index()
        out = out.merge(distinct, on=KEYS, how="left", validate="one_to_one")
        for col in ("MatchedExposureRows", "MatchedExposureFlights", "MatchedWeatherObservations", "CancelledFlights",
                    "DivertedFlights", "EligibleFlights", "DelayedFlights", "TotalPositiveDelayMinutes"):
            out[col] = out[col].round().astype("int64")
        elig = out["EligibleFlights"].where(out["EligibleFlights"] > 0)
        out["DelayRatePct"] = _round_half_away(100.0 * out["DelayedFlights"] / elig, 2)
        out["AvgSignedDelayMinutes"] = _round_half_away(out["_sd_num"] / out["_sd_den"].where(out["_sd_den"] > 0), 2)
        for col, name in WEATHER_COLS.items():
            out[name] = _round_half_away(out[f"_sum_{col}"] / out[f"_cnt_{col}"].where(out[f"_cnt_{col}"] > 0), ROUNDING[name])
        out["PrecipitationBand"] = out["PrecipitationBandSort"].map(C.PRECIP_BANDS)
        out["WindSpeedBand"] = out["WindSpeedBandSort"].map(C.WIND_BANDS)
        out = out[[c for c in out.columns if not c.startswith("_")]]
        return out, flags


def attach_dims(frame: pd.DataFrame, dims: pd.DataFrame, month: str, cols: list[str]) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=cols)
    m = frame.merge(dims, on=["AirportKey", "OurAirportsID"], how="left", validate="many_to_one")
    if m["AirportCode"].isna().any():
        raise RuntimeError("Some Bridge AirportKey/OurAirportsID pairs were not found in dim_airport.")
    m["SourceMonth"] = month
    m["MonthNumber"] = int(month)
    m["MonthName"] = C.MONTH_NAMES[month]
    m["AirportRole"] = m["ExposureType"].map(C.role_of)
    return m[cols]


def fetch_dims(session: Session, keys: list[int]) -> pd.DataFrame:
    keys = sorted({int(k) for k in keys})
    if not keys:
        return pd.DataFrame(columns=["AirportKey", "OurAirportsID", "AirportCode", "Ident", "AirportName", "Municipality", "ISOCountry"])
    rows = session.fetch(DIM_SQL.format(keys=",".join(["%s"] * len(keys))), tuple(keys))
    dims = pd.DataFrame(rows, columns=["AirportKey", "OurAirportsID", "AirportCode", "Ident", "AirportName", "Municipality", "ISOCountry"])
    dims["AirportKey"] = dims["AirportKey"].astype("int64")
    dims["OurAirportsID"] = dims["OurAirportsID"].astype("int64")
    return dims


# --------------------------------------------------------------------------- RUN
def parse_selection(args, verification) -> dict[str, list[str]]:
    verified = set(verification["VerifiedPartitions"])
    months = sorted({k.split("|")[0] for k in verified}) if not args.months else [m.zfill(2) for m in args.months.split(",")]
    exposures = list(C.EXPOSURES) if not args.exposures else [e.strip().upper() for e in args.exposures.split(",")]
    bad = [e for e in exposures if e not in C.EXPOSURES]
    if bad:
        sys.exit(f"Unknown exposure type(s): {bad}")
    plan: dict[str, list[str]] = {}
    for m in months:
        for e in exposures:
            key = f"{m}|{e}"
            if key not in verified:
                C.say(f"[SKIP] {key}: not VERIFIED in bridge_verification.json — not exported.")
                continue
            if not args.force and (PARTIALS / f"qa_{m}_{e}.json").is_file():
                C.say(f"[SKIP] {key}: already exported (use --force to redo).")
                continue
            plan.setdefault(m, []).append(e)
    return plan


def cmd_run(args) -> int:
    verification = load_verification()
    journal, preview = C.resolve_evidence(args)
    if journal["SHA256"] != verification["Journal"]["SHA256"]:
        sys.exit("Journal changed since `verify`; run verify again.")
    plan = parse_selection(args, verification)
    if not plan:
        C.say("Nothing to export.")
        return 0
    ranges = C.month_ranges(journal)
    session = Session(args)
    status = 0
    try:
        for month, exposures in plan.items():
            first, last = ranges[month]
            exp_sql = ",".join(["%s"] * len(exposures))
            C.say(f"\n[RUN] Month {month} · {', '.join(exposures)} · FlightKey {first:,}..{last:,}")
            t0 = time.perf_counter()
            chunk_list = list(C.chunks(first, last, args.chunk_size))
            cov_rows = run_chunked(session, COVERAGE_SQL.replace("{exposures}", exp_sql), chunk_list,
                                   lambda lo, hi: (lo, hi, *exposures), args.max_exec_ms, False, "coverage")
            accumulator = ImpactAccumulator()
            run_chunked(session, IMPACT_SQL.replace("{exposures}", exp_sql), chunk_list,
                        lambda lo, hi, m=month: (m, lo, hi, *exposures), args.max_exec_ms, True, "impact",
                        consumer=accumulator.add)
            cov = pd.DataFrame(cov_rows, columns=["ExposureType", "AirportKey", "OurAirportsID", "WeatherCoverageStatus",
                                                  "BridgeExposureRows", "NonNullWeatherKeys",
                                                  "MatchedStatusMissingKeyRows", "NonMatchedStatusHasKeyRows"])
            for col in ("AirportKey", "OurAirportsID", "BridgeExposureRows", "NonNullWeatherKeys",
                        "MatchedStatusMissingKeyRows", "NonMatchedStatusHasKeyRows"):
                cov[col] = pd.to_numeric(cov[col]).astype("int64")
            cov = cov.groupby(["ExposureType", "AirportKey", "OurAirportsID", "WeatherCoverageStatus"], as_index=False).sum()
            impact_keys = [int(k) for p in accumulator.partials for k in p["AirportKey"].unique()]
            dims = fetch_dims(session, list(cov["AirportKey"].unique()) + impact_keys)
            for exp in exposures:
                key = f"{month}|{exp}"
                agg, qa = accumulator.finalize(exp)
                impact = attach_dims(agg, dims, month, C.IMPACT_COLUMNS)
                cov_e = cov[cov["ExposureType"] == exp]
                coverage = attach_dims(cov_e, dims, month, C.COVERAGE_COLUMNS)
                jp = journal["Partitions"][key]
                pv = preview["Partitions"].get(key) if preview else None
                cov_total = int(coverage["BridgeExposureRows"].sum())
                cov_matched = int(coverage.loc[coverage["WeatherCoverageStatus"] == C.MATCHED, "BridgeExposureRows"].sum())
                imp_rows_n = int(impact["MatchedExposureRows"].sum()) if not impact.empty else 0
                checks = {
                    "CoverageRowsEqualExpected": cov_total == jp["ExpectedRows"],
                    "CoverageMatchedEqualsPreview": pv is None or cov_matched == int(pv["MatchedRows"]),
                    "ImpactRowsPlusExcludedEqualMatched": imp_rows_n + qa.get("ExcludedRows", 0) == cov_matched,
                    "NoIntegrityFlags": all(qa[f] == 0 for f in FLAGS),
                    "CoverageKeyRulesClean": int(coverage["MatchedStatusMissingKeyRows"].sum()) == 0
                                             and int(coverage["NonMatchedStatusHasKeyRows"].sum()) == 0,
                    "EligibleLEFlights": impact.empty or bool((impact["EligibleFlights"] <= impact["MatchedExposureFlights"]).all()),
                    "DelayedLEEligible": impact.empty or bool((impact["DelayedFlights"] <= impact["EligibleFlights"]).all()),
                    "DistinctWeatherLERows": impact.empty or bool((impact["MatchedWeatherObservations"] <= impact["MatchedExposureRows"]).all()),
                }
                result = "PASS" if all(checks.values()) else "FAIL"
                PARTIALS.mkdir(parents=True, exist_ok=True)
                C.atomic_write_csv(impact, PARTIALS / f"impact_{month}_{exp}.csv")
                C.atomic_write_csv(coverage, PARTIALS / f"coverage_{month}_{exp}.csv")
                qa_doc = {
                    "Partition": key, "Result": result, "Checks": checks, "IntegrityFlags": qa,
                    "ExpectedRows": jp["ExpectedRows"], "CoverageRows": cov_total, "CoverageMatchedRows": cov_matched,
                    "PreviewMatchedRows": int(pv["MatchedRows"]) if pv else None, "ImpactMatchedRows": imp_rows_n,
                    "ImpactGroups": int(len(impact)), "CoverageGroups": int(len(coverage)),
                    "EligibleFlights": int(impact["EligibleFlights"].sum()) if not impact.empty else 0,
                    "DelayedFlights": int(impact["DelayedFlights"].sum()) if not impact.empty else 0,
                    "FlightKeyRange": [jp["FirstFlightKey"], jp["LastFlightKey"]],
                    "ChunkSize": args.chunk_size, "Tool": C.TOOL_VERSION, "JournalSHA256": journal["SHA256"],
                    "ExportedAtUTC": C.now_utc(),
                }
                C.atomic_write_text(PARTIALS / f"qa_{month}_{exp}.json", json.dumps(qa_doc, indent=2))
                C.say(f"   [{result}] {key}: coverage {cov_total:,} rows (matched {cov_matched:,}); "
                      f"impact {imp_rows_n:,} matched rows -> {len(impact):,} groups; flags {qa}")
                if result != "PASS":
                    status = 2
                    C.say(f"   !! QA FAIL for {key}: {[k for k, v in checks.items() if not v]}")
            C.say(f"[RUN] Month {month} finished in {time.perf_counter() - t0:,.1f}s")
    finally:
        session.close()
    return status


# --------------------------------------------------------------------------- MERGE
def cmd_merge(args) -> int:
    verification = load_verification()
    journal, _ = C.resolve_evidence(args)
    qa_files = sorted(PARTIALS.glob("qa_*.json"))
    if not qa_files:
        sys.exit("No exported partitions found. Run `fw_extract.py run` first.")
    impacts, coverages, parts = [], [], []
    for qf in qa_files:
        qa = json.loads(qf.read_text(encoding="utf-8"))
        key = qa["Partition"]
        if qa["Result"] != "PASS":
            sys.exit(f"Partition {key} has QA result {qa['Result']}; fix before merging.")
        if key not in verification["VerifiedPartitions"]:
            sys.exit(f"Partition {key} is not VERIFIED in the current verification report.")
        if qa["JournalSHA256"] != journal["SHA256"]:
            sys.exit(f"Partition {key} was exported against a different journal; re-run it.")
        month, exp = key.split("|")
        impacts.append(pd.read_csv(PARTIALS / f"impact_{month}_{exp}.csv", dtype={"SourceMonth": str}))
        coverages.append(pd.read_csv(PARTIALS / f"coverage_{month}_{exp}.csv", dtype={"SourceMonth": str}))
        parts.append(qa)
    impact = pd.concat(impacts, ignore_index=True)[C.IMPACT_COLUMNS]
    coverage = pd.concat(coverages, ignore_index=True)[C.COVERAGE_COLUMNS]
    impact = impact.sort_values(["MonthNumber", "ExposureType", "AirportCode", "PrecipitationBandSort", "WindSpeedBandSort"], kind="stable")
    coverage = coverage.sort_values(["MonthNumber", "ExposureType", "AirportCode", "WeatherCoverageStatus"], kind="stable")
    out_dir = Path(args.output_dir)
    C.atomic_write_csv(impact, out_dir / C.IMPACT_FILE)
    C.atomic_write_csv(coverage, out_dir / C.COVERAGE_FILE)
    scope: dict[str, list[str]] = {}
    for p in parts:
        m, e = p["Partition"].split("|")
        scope.setdefault(e, []).append(m)
    all_months = sorted({p["Partition"].split("|")[0] for p in parts})
    manifest = {
        "Dataset": "Flight x Weather snapshot — Flight DW 2025",
        "Tool": C.TOOL_VERSION, "GeneratedAtUTC": C.now_utc(),
        "BridgeRunID": journal["BridgeRunID"], "JournalSHA256": journal["SHA256"],
        "ScopeMonths": all_months,
        "ScopeLabel": ("" if not all_months else f"{C.MONTH_NAMES[all_months[0]]} 2025" if len(all_months) == 1
                       else f"{C.MONTH_NAMES[all_months[0]]}–{C.MONTH_NAMES[all_months[-1]]} 2025"),
        "MonthsByExposure": {e: sorted(v) for e, v in scope.items()},
        "Partitions": parts,
        "Files": {
            C.IMPACT_FILE: {"Rows": int(len(impact)), "SHA256": C.sha256_file(out_dir / C.IMPACT_FILE)},
            C.COVERAGE_FILE: {"Rows": int(len(coverage)), "SHA256": C.sha256_file(out_dir / C.COVERAGE_FILE)},
        },
        "Notes": [
            "Impact = MATCHED_WEATHER_HOUR rows only; coverage = every WeatherCoverageStatus.",
            "Counts are exposure events; one flight appears once per ExposureType. Do not sum across ExposureType.",
            "Bands are exploratory groupings in Open-Meteo source units (mm, km/h), not hazard scales.",
            "Descriptive association only; not causal inference.",
        ],
    }
    C.atomic_write_text(out_dir / C.MANIFEST_FILE, json.dumps(manifest, indent=2, ensure_ascii=False))
    C.say(f"[MERGE] {len(parts)} partitions -> {C.IMPACT_FILE} ({len(impact):,} rows), "
          f"{C.COVERAGE_FILE} ({len(coverage):,} rows), {C.MANIFEST_FILE}")
    C.say(f"[MERGE] Scope: {manifest['ScopeLabel']} | written to {out_dir}")
    return 0


# --------------------------------------------------------------------------- EXPLAIN / STATUS
def cmd_explain(args) -> int:
    journal, _ = C.resolve_evidence(args)
    month, exp = args.partition.split(":")
    month = month.zfill(2)
    first, last = C.month_ranges(journal)[month]
    hi = min(first + args.chunk_size - 1, last)
    session = Session(args)
    try:
        for name, sql, params in (
            ("COVERAGE", COVERAGE_SQL.replace("{exposures}", "%s"), (first, hi, exp)),
            ("IMPACT", IMPACT_SQL.replace("{exposures}", "%s"), (month, first, hi, exp)),
        ):
            C.say(f"\n=== EXPLAIN {name} · {month}|{exp} · FlightKey {first:,}..{hi:,} ===")
            for row in session.fetch("EXPLAIN FORMAT=TREE " + sql.format(ms=args.max_exec_ms), params):
                C.say(row[0])
    finally:
        session.close()
    C.say("\nExpected: bridge accessed by 'Index range scan on b using PRIMARY', fact_flight and weather by "
          "'Single-row index lookup ... using PRIMARY'. No full table scan on bridge.")
    return 0


def cmd_status(args) -> int:
    v = load_verification()
    C.say(f"Verification {v['Result']} at {v['GeneratedAtUTC']}: {len(v['VerifiedPartitions'])} verified, "
          f"{len(v['NotLoadedPartitions'])} not loaded, failed {v['FailedPartitions']}")
    for key in v["VerifiedPartitions"]:
        m, e = key.split("|")
        qf = PARTIALS / f"qa_{m}_{e}.json"
        state = json.loads(qf.read_text(encoding="utf-8"))["Result"] if qf.is_file() else "pending"
        C.say(f"  {key:<26} export: {state}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("verify", "explain", "run", "merge", "status"):
        sp = sub.add_parser(name)
        C.add_path_args(sp)
        C.add_db_args(sp)
        sp.add_argument("--chunk-size", type=int, default=50_000, help="FlightKeys per query chunk (default 50,000)")
        sp.add_argument("--max-exec-ms", type=int, default=240_000, help="MAX_EXECUTION_TIME per query (default 240 s)")
        if name == "run":
            sp.add_argument("--months", help="e.g. 09 or 01,02,03 (default: all verified)")
            sp.add_argument("--exposures", help="e.g. ACTUAL_ARRIVAL (default: all four)")
            sp.add_argument("--force", action="store_true", help="Re-export partitions already exported")
        if name == "explain":
            sp.add_argument("--partition", default="09:ACTUAL_ARRIVAL")
        if name == "merge":
            sp.add_argument("--output-dir", default=str(C.EXPORT_DIR))
    args = ap.parse_args()
    return {"verify": cmd_verify, "run": cmd_run, "merge": cmd_merge,
            "explain": cmd_explain, "status": cmd_status}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
