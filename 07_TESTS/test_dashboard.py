"""End-to-end test for the AERO INSIGHTS dashboard (no browser, no database).

Run from the dashboard folder:
    python 07_TESTS\\test_dashboard.py
Optional: set AERO_DATA_DIR to test against another data folder.

What it checks
  1. Gold-page and Weather-page functions are byte-identical to the protected fingerprints.
  2. All six pages + /health + Dash internals return HTTP 200.
  3. Every callback is executed through /_dash-update-component exactly as a browser would,
     first with page defaults, then with every option of every dropdown/radio input,
     plus edge cases for Flight × Weather (cleared country list, airport search, each month).
  4. Flight × Weather never shows numbers when its snapshot is absent.
Exit code 0 = all pass.
"""
from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import sys
import traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
APP_PATH = HERE.parent / "02_PYTHON_SOURCE" / "app.py"
FAILURES: list[str] = []
PASSES = 0


def ok(cond: bool, label: str) -> None:
    global PASSES
    if cond:
        PASSES += 1
    else:
        FAILURES.append(label)
        print(f"  FAIL  {label}")


def source_fingerprints(path: Path) -> dict[str, str]:
    src = path.read_text(encoding="utf-8-sig")
    tree = ast.parse(src)
    return {n.name: hashlib.sha256("\n".join(l.rstrip() for l in ast.get_source_segment(src, n).replace("\r", "").split("\n")).encode()).hexdigest()
            for n in tree.body if isinstance(n, ast.FunctionDef)}


def walk(component, found: dict) -> None:
    """Collect id -> props of every component in a rendered layout."""
    if isinstance(component, (list, tuple)):
        for c in component:
            walk(c, found)
        return
    if not hasattr(component, "to_plotly_json"):
        return
    js = component.to_plotly_json()
    props = js.get("props", {})
    cid = props.get("id")
    if isinstance(cid, str):
        found[cid] = {"type": js.get("type"), **props}
    walk(props.get("children"), found)


def main() -> int:
    print("1) Protected functions (Gold pages + Weather page)")
    lock = json.loads((HERE / "protected_functions.json").read_text(encoding="utf-8"))
    current = source_fingerprints(APP_PATH)
    for group in ("gold_v2_unchanged", "weather_page"):
        for name, digest in lock[group].items():
            ok(current.get(name) == digest, f"{group}: {name} changed or missing")

    print("2) Import app and request every route")
    spec = importlib.util.spec_from_file_location("aero_app", APP_PATH)
    app_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(app_mod)
    client = app_mod.app.server.test_client()
    pages = ["/", "/airlines", "/airports", "/time", "/weather", "/flight-weather"]
    for path in pages + ["/health", "/_dash-layout", "/_dash-dependencies"]:
        ok(client.get(path).status_code == 200, f"GET {path} != 200")
    health = client.get("/health").get_json()
    ok(health.get("status") == "ok", "/health status")
    print(f"   /health -> {json.dumps(health['flight_weather'])}")

    print("3) Execute every callback through the Dash HTTP endpoint")
    deps = client.get("/_dash-dependencies").get_json()
    layouts: dict[str, dict] = {}
    for p in pages:
        found: dict = {}
        walk(app_mod.render_page(p), found)
        layouts[p] = found
    walk(app_mod.app.layout, layouts.setdefault("_shell", {}))

    def page_for(input_ids: list[str]) -> str | None:
        for p, comps in layouts.items():
            if all(i in comps for i in input_ids):
                return p
        return None

    calls = 0
    for dep in deps:
        inputs = dep["inputs"]
        ids = [i["id"] for i in inputs]
        page = page_for(ids)
        if page is None:
            ok(False, f"no page provides inputs {ids}")
            continue
        comps = layouts[page]
        base = {i["id"]: comps[i["id"]].get(i["property"]) for i in inputs}
        if "url" in base:
            variants = [{"url": p} for p in pages]
        else:
            variants = [dict(base)]
            for cid in ids:
                options = comps[cid].get("options") or []
                values = [o["value"] if isinstance(o, dict) else o for o in options][:40]
                multi = comps[cid].get("multi")
                for v in values:
                    variants.append({**base, cid: [v] if multi else v})
                if multi:
                    variants.append({**base, cid: []})       # cleared multi-select
                    variants.append({**base, cid: None})
                if comps[cid].get("type") == "Input":
                    for text in ("atl", "zzzz-no-match", "", None):
                        variants.append({**base, cid: text})
        for v in variants:
            payload = {
                "output": dep["output"],
                "outputs": [{"id": o.split(".")[0], "property": o.split(".")[1]} for o in dep["output"].strip(".").split("...")]
                if dep["output"].startswith("..") else {"id": dep["output"].split(".")[0], "property": dep["output"].split(".")[1]},
                "inputs": [{"id": i["id"], "property": i["property"], "value": v[i["id"]] if i["id"] != "url" else v["url"]} for i in inputs],
                "changedPropIds": [f"{i['id']}.{i['property']}" for i in inputs],
                "state": [],
            }
            r = client.post("/_dash-update-component", json=payload)
            calls += 1
            if r.status_code not in (200, 204):
                ok(False, f"callback {dep['output'][:60]} with {v} -> HTTP {r.status_code}")
            else:
                ok(True, "")
    print(f"   {calls} callback executions")

    print("4) Flight × Weather empty-state honesty")
    impact = app_mod.DATA.get("flight_weather_impact")
    out = app_mod.update_flight_weather_charts("SCHEDULED_DEPARTURE", "ALL", None, None)
    text = json.dumps(out[0].to_plotly_json(), default=str, ensure_ascii=False)
    if impact is None or impact.empty:
        ok("—" in text, "KPI cards must show '—' (no numbers) when snapshot is missing")
    else:
        ok("—" not in text or "MATCHED" in text, "KPI cards populated when snapshot is present")
        all_c = app_mod.update_flight_weather_charts("SCHEDULED_DEPARTURE", "ALL", None, None)
        cleared = app_mod.update_flight_weather_charts("SCHEDULED_DEPARTURE", "ALL", [], None)
        ok(json.dumps(all_c[0].to_plotly_json(), default=str) == json.dumps(cleared[0].to_plotly_json(), default=str),
           "cleared country filter must equal 'all countries'")

    print(f"\nRESULT: {'PASS' if not FAILURES else 'FAIL'} — {PASSES} checks passed, {len(FAILURES)} failed")
    return 0 if not FAILURES else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        traceback.print_exc()
        sys.exit(1)
