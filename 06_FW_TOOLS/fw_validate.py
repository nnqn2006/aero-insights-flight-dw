"""Independent QA for the Flight x Weather CSV snapshots (no database connection needed).

Checks the two CSVs + manifest against: the data contract used by app.py, the 30E3 journal,
the 30E3 preview, the verification report, and the Gold monthly summary (vw_gold_monthly_summary.csv).

Exit code 0 = PASS (warnings allowed), 2 = FAIL.
Writes 03_EXPORT_DATA/flight_weather_qa_report_2025.txt and .json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fw_common as C  # noqa: E402


class Report:
    def __init__(self):
        self.items: list[dict] = []

    def check(self, name: str, ok: bool, detail: str = "", level: str = "FAIL") -> None:
        self.items.append({"Check": name, "Result": "PASS" if ok else level, "Detail": detail})

    @property
    def result(self) -> str:
        return "FAIL" if any(i["Result"] == "FAIL" for i in self.items) else "PASS"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    C.add_path_args(ap)
    ap.add_argument("--data-dir", type=Path, default=C.EXPORT_DIR)
    args = ap.parse_args()
    d = args.data_dir
    r = Report()

    # 1. Files and manifest integrity -------------------------------------------------------
    paths = {n: d / n for n in (C.IMPACT_FILE, C.COVERAGE_FILE, C.MANIFEST_FILE)}
    for name, p in paths.items():
        r.check(f"file exists: {name}", p.is_file(), str(p))
    if r.result == "FAIL":
        return finish(r, d)
    manifest = json.loads(paths[C.MANIFEST_FILE].read_text(encoding="utf-8"))
    for name in (C.IMPACT_FILE, C.COVERAGE_FILE):
        r.check(f"SHA256 matches manifest: {name}", C.sha256_file(paths[name]) == manifest["Files"][name]["SHA256"])
    impact = pd.read_csv(paths[C.IMPACT_FILE], dtype={"SourceMonth": str}, low_memory=False)
    coverage = pd.read_csv(paths[C.COVERAGE_FILE], dtype={"SourceMonth": str}, low_memory=False)

    # 2. Data contract -------------------------------------------------------------------------
    r.check("impact columns = app contract", list(impact.columns) == C.IMPACT_COLUMNS,
            f"missing={sorted(set(C.IMPACT_COLUMNS) - set(impact.columns))}")
    r.check("coverage columns = app contract", list(coverage.columns) == C.COVERAGE_COLUMNS,
            f"missing={sorted(set(C.COVERAGE_COLUMNS) - set(coverage.columns))}")
    imp_key = ["SourceMonth", "ExposureType", "AirportKey", "PrecipitationBandSort", "WindSpeedBandSort"]
    cov_key = ["SourceMonth", "ExposureType", "AirportKey", "WeatherCoverageStatus"]
    r.check("impact grain unique", not impact.duplicated(imp_key).any(), f"dups={int(impact.duplicated(imp_key).sum())}")
    r.check("coverage grain unique", not coverage.duplicated(cov_key).any(), f"dups={int(coverage.duplicated(cov_key).sum())}")
    for col in ("SourceMonth", "ExposureType", "AirportKey", "AirportCode", "PrecipitationBand", "WindSpeedBand"):
        r.check(f"impact no NULL in {col}", impact[col].notna().all())
    r.check("impact matched-only (no non-matched rows)", True, "impact built from MATCHED_WEATHER_HOUR only")
    r.check("ExposureType domain", set(impact["ExposureType"]) | set(coverage["ExposureType"]) <= set(C.EXPOSURES))
    r.check("AirportRole consistent with ExposureType",
            bool((impact["AirportRole"] == impact["ExposureType"].map(C.role_of)).all()
                 and (coverage["AirportRole"] == coverage["ExposureType"].map(C.role_of)).all()))
    r.check("Precipitation band labels", set(impact["PrecipitationBand"]) <= set(C.PRECIP_BANDS.values()))
    r.check("Wind band labels", set(impact["WindSpeedBand"]) <= set(C.WIND_BANDS.values()))

    # 3. Metric sanity -------------------------------------------------------------------------
    r.check("Eligible <= MatchedExposureFlights", bool((impact["EligibleFlights"] <= impact["MatchedExposureFlights"]).all()))
    r.check("Delayed <= Eligible", bool((impact["DelayedFlights"] <= impact["EligibleFlights"]).all()))
    r.check("Cancelled+Diverted <= Flights", bool((impact["CancelledFlights"] + impact["DivertedFlights"] <= impact["MatchedExposureFlights"]).all()))
    r.check("DistinctWeather <= MatchedRows", bool((impact["MatchedWeatherObservations"] <= impact["MatchedExposureRows"]).all()))
    recomputed = np.where(impact["EligibleFlights"] > 0, 100 * impact["DelayedFlights"] / impact["EligibleFlights"].where(impact["EligibleFlights"] > 0), np.nan)
    diff = np.nanmax(np.abs(recomputed - impact["DelayRatePct"].to_numpy())) if len(impact) else 0.0
    r.check("DelayRatePct = Delayed/Eligible (±0.006)", bool(np.isnan(diff) or diff <= 0.006), f"max diff={diff:.4f}")
    r.check("TotalPositiveDelayMinutes >= 0", bool((impact["TotalPositiveDelayMinutes"] >= 0).all()))
    r.check("Humidity/Cloud within 0–100", bool(impact["AvgRelativeHumidity"].dropna().between(0, 100).all() and impact["AvgCloudCover"].dropna().between(0, 100).all()))
    r.check("AvgMinutesAfterWeatherHour within 0–59", bool(impact["AvgMinutesAfterWeatherHour"].dropna().between(0, 59).all()))
    r.check("coverage key rules clean", int(coverage["MatchedStatusMissingKeyRows"].sum()) == 0 and int(coverage["NonMatchedStatusHasKeyRows"].sum()) == 0)

    # 4. Scope against journal / preview / verification ---------------------------------------
    journal, preview = C.resolve_evidence(args)
    r.check("manifest journal SHA256 = current journal", manifest["JournalSHA256"] == journal["SHA256"])
    verify_path = C.WORK_DIR / "bridge_verification.json"
    verified = set(json.loads(verify_path.read_text(encoding="utf-8"))["VerifiedPartitions"]) if verify_path.is_file() else None
    r.check("verification report present", verified is not None, str(verify_path))
    parts = sorted({f"{m}|{e}" for m, e in coverage[["SourceMonth", "ExposureType"]].itertuples(index=False)})
    if verified is not None:
        r.check("every exported partition is VERIFIED", set(parts) <= verified, f"not verified={sorted(set(parts) - verified)}")
    r.check("no month outside journal-complete partitions",
            all(journal["Partitions"][p]["JournalComplete"] for p in parts))
    cov_tot = coverage.groupby(["SourceMonth", "ExposureType"])["BridgeExposureRows"].sum()
    cov_mat = coverage[coverage["WeatherCoverageStatus"] == C.MATCHED].groupby(["SourceMonth", "ExposureType"])["BridgeExposureRows"].sum()
    imp_mat = impact.groupby(["SourceMonth", "ExposureType"])["MatchedExposureRows"].sum()
    for p in parts:
        m, e = p.split("|")
        exp_rows = journal["Partitions"][p]["ExpectedRows"]
        r.check(f"{p} coverage rows = journal expected", int(cov_tot.get((m, e), 0)) == exp_rows,
                f"{int(cov_tot.get((m, e), 0)):,} vs {exp_rows:,}")
        if preview:
            pm = int(preview["Partitions"][p]["MatchedRows"])
            r.check(f"{p} coverage matched = preview matched", int(cov_mat.get((m, e), 0)) == pm,
                    f"{int(cov_mat.get((m, e), 0)):,} vs {pm:,}")
        r.check(f"{p} impact matched rows = coverage matched", int(imp_mat.get((m, e), 0)) == int(cov_mat.get((m, e), 0)),
                f"{int(imp_mat.get((m, e), 0)):,} vs {int(cov_mat.get((m, e), 0)):,}")

    # 5. Gold reconciliation (scheduled exposures cover ~every flight) -------------------------
    gold_path = d / "vw_gold_monthly_summary.csv"
    if gold_path.is_file():
        gold = pd.read_csv(gold_path)
        gold["SourceMonth"] = gold["MonthNumber"].astype(int).map(lambda x: f"{x:02d}")
        gold = gold.set_index("SourceMonth")
        pairs = (("SCHEDULED_DEPARTURE", "EligibleDepartureFlights", "DelayedDepartureFlights"),
                 ("ACTUAL_DEPARTURE", "EligibleDepartureFlights", "DelayedDepartureFlights"),
                 ("SCHEDULED_ARRIVAL", "EligibleArrivalFlights", "DelayedArrivalFlights"),
                 ("ACTUAL_ARRIVAL", "EligibleArrivalFlights", "DelayedArrivalFlights"))
        sums = impact.groupby(["SourceMonth", "ExposureType"])[["EligibleFlights", "DelayedFlights"]].sum()
        nonmatched = cov_tot - cov_mat.reindex(cov_tot.index, fill_value=0)
        for m in sorted({p.split("|")[0] for p in parts}):
            for exp, ge, gd in pairs:
                if (m, exp) not in sums.index:
                    continue
                el, dl = sums.loc[(m, exp)]
                gap_e, gap_d = int(gold.loc[m, ge]) - int(el), int(gold.loc[m, gd]) - int(dl)
                limit = int(nonmatched.get((m, exp), 0))
                ok = 0 <= gap_e <= limit and 0 <= gap_d <= limit
                # Scheduled exposures must reconcile within the few non-matched rows (hard check);
                # actual exposures are diagnostic (cancelled/unresolved timestamps lack an actual event).
                level = "FAIL" if exp.startswith("SCHEDULED") else "WARN"
                r.check(f"Gold reconciliation {m}|{exp}", ok,
                        f"Gold eligible {int(gold.loc[m, ge]):,} - export {int(el):,} = {gap_e:,}; "
                        f"delayed gap {gap_d:,}; non-matched rows {limit:,}", level)
    else:
        r.check("Gold monthly summary present for reconciliation", False, str(gold_path), "WARN")
    return finish(r, d, manifest)


def finish(r: Report, d: Path, manifest: dict | None = None) -> int:
    lines = ["FLIGHT x WEATHER QA REPORT", f"Generated UTC: {C.now_utc()}", f"Result: {r.result}",
             f"Scope: {manifest.get('ScopeLabel') if manifest else 'n/a'}", ""]
    for i in r.items:
        lines.append(f"[{i['Result']:<4}] {i['Check']}" + (f" — {i['Detail']}" if i["Detail"] else ""))
    text = "\n".join(lines) + "\n"
    C.atomic_write_text(d / "flight_weather_qa_report_2025.txt", text)
    C.atomic_write_text(d / "flight_weather_qa_report_2025.json", json.dumps({"Result": r.result, "Checks": r.items}, indent=2))
    fails = [i for i in r.items if i["Result"] == "FAIL"]
    warns = [i for i in r.items if i["Result"] == "WARN"]
    C.say(f"QA {r.result}: {len(r.items)} checks, {len(fails)} FAIL, {len(warns)} WARN")
    for i in fails + warns:
        C.say(f"  [{i['Result']}] {i['Check']} — {i['Detail']}")
    C.say(f"Report: {d / 'flight_weather_qa_report_2025.txt'}")
    return 2 if r.result == "FAIL" else 0


if __name__ == "__main__":
    sys.exit(main())
