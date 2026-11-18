from __future__ import annotations

import os
import uuid
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from dash import Dash, Input, Output, dcc, html, dash_table

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = Path(os.getenv("AERO_DATA_DIR", str(ROOT / "03_EXPORT_DATA")))
ASSETS_DIR = ROOT / "04_CSS"

# AERO INSIGHTS visual system
DARK = "#0B1220"
PANEL = "#111D2E"
PANEL_2 = "#17263A"
BORDER = "rgba(148, 163, 184, .15)"
TEXT = "#E8EEF7"
MUTED = "#91A4BA"
CYAN = "#31C5D8"
BLUE = "#648CFF"
AMBER = "#F3B45D"
RED = "#F07178"
GREEN = "#52C6A5"
VIOLET = "#A78BFA"
GRID = "rgba(148, 163, 184, .12)"

FILES = {
    "kpi": "vw_gold_flight_kpi.csv",
    "monthly": "vw_gold_monthly_summary.csv",
    "airline": "vw_gold_airline_performance.csv",
    "airport": "vw_gold_airport_role_performance.csv",
    "hour": "vw_gold_departure_hour_performance.csv",
    "monthly_airline": "vw_gold_monthly_airline_performance.csv",
    "weather_monthly": "weather_monthly_summary_2025.csv",
    "weather_airport": "weather_airport_profile_2025.csv",
}

REQUIRED_COLUMNS = {
    "kpi": ["CalendarYear", "TotalFlights", "CancelledFlights", "DivertedFlights",
            "EligibleDepartureFlights", "DelayedDepartureFlights", "DepartureDelayRatePct",
            "EligibleArrivalFlights", "DelayedArrivalFlights", "ArrivalDelayRatePct"],
    "monthly": ["MonthNumber", "MonthName", "TotalFlights", "CancelledFlights", "DivertedFlights",
                "EligibleDepartureFlights", "DelayedDepartureFlights", "DepartureDelayRatePct",
                "EligibleArrivalFlights", "DelayedArrivalFlights", "ArrivalDelayRatePct"],
    "airline": ["ReportingAirlineCode", "TotalFlights", "CancelledFlights", "DivertedFlights",
                "EligibleDepartureFlights", "DelayedDepartureFlights", "DepartureDelayRatePct",
                "EligibleArrivalFlights", "DelayedArrivalFlights", "ArrivalDelayRatePct"],
    "airport": ["AirportRole", "AirportName", "ScheduledFlights", "EligibleFlights", "DelayedFlights",
                "DelayRatePct", "AvgSignedDelayMinutes", "TotalPositiveDelayMinutes"],
    "hour": ["ScheduledDepartureHourLabel", "ScheduledFlights", "EligibleDepartureFlights",
             "DelayedDepartureFlights", "DepartureDelayRatePct", "AvgSignedDepartureDelayMinutes"],
    "monthly_airline": ["MonthNumber", "MonthName", "ReportingAirlineCode", "TotalFlights",
                         "DepartureDelayRatePct", "ArrivalDelayRatePct"],
    "weather_monthly": ["CalendarYear", "MonthNumber", "MonthName", "WeatherObservations",
                        "AirportsCovered", "AvgTemperature", "MinTemperature", "MaxTemperature",
                        "AvgRelativeHumidity", "AvgHourlyPrecipitation", "MaxHourlyPrecipitation",
                        "WetAirportHours", "WetAirportHourRate", "AvgWindSpeed", "MaxWindGust", "AvgCloudCover"],
    "weather_airport": ["AirportKey", "OurAirportsID", "AirportCode", "AirportName", "Municipality",
                        "ISOCountry", "AirportType", "WeatherObservations", "AvgTemperature",
                        "MinTemperature", "MaxTemperature", "AvgRelativeHumidity", "TotalPrecipitation",
                        "WetAirportHours", "WetAirportHourRate", "AvgWindSpeed", "MaxWindGust", "AvgCloudCover"],
}

NUMERIC_COLUMNS = {
    "kpi": ["CalendarYear", "FlightRows", "TotalFlights", "CancelledFlights", "DivertedFlights",
            "EligibleDepartureFlights", "DelayedDepartureFlights", "DepartureDelayRatePct",
            "EligibleArrivalFlights", "DelayedArrivalFlights", "ArrivalDelayRatePct",
            "AvgSignedDepartureDelayMinutes", "AvgSignedArrivalDelayMinutes"],
    "monthly": ["MonthNumber", "FlightRows", "TotalFlights", "CancelledFlights", "DivertedFlights",
                "EligibleDepartureFlights", "DelayedDepartureFlights", "DepartureDelayRatePct",
                "EligibleArrivalFlights", "DelayedArrivalFlights", "ArrivalDelayRatePct",
                "AvgSignedDepartureDelayMinutes", "AvgSignedArrivalDelayMinutes"],
    "airline": ["AirlineKey", "TotalFlights", "CancelledFlights", "DivertedFlights",
                "EligibleDepartureFlights", "DelayedDepartureFlights", "DepartureDelayRatePct",
                "EligibleArrivalFlights", "DelayedArrivalFlights", "ArrivalDelayRatePct",
                "AvgSignedDepartureDelayMinutes", "AvgSignedArrivalDelayMinutes"],
    "airport": ["AirportKey", "OurAirportsID", "ScheduledFlights", "EligibleFlights", "DelayedFlights",
                "DelayRatePct", "AvgSignedDelayMinutes", "TotalPositiveDelayMinutes"],
    "hour": ["ScheduledDepartureHour", "IsEndOfDay", "ScheduledFlights", "EligibleDepartureFlights",
             "DelayedDepartureFlights", "DepartureDelayRatePct", "AvgSignedDepartureDelayMinutes"],
    "monthly_airline": ["CalendarYear", "MonthNumber", "TotalFlights", "CancelledFlights", "DivertedFlights",
                         "EligibleDepartureFlights", "DelayedDepartureFlights", "DepartureDelayRatePct",
                         "EligibleArrivalFlights", "DelayedArrivalFlights", "ArrivalDelayRatePct"],
    "weather_monthly": ["CalendarYear", "MonthNumber", "WeatherObservations", "AirportsCovered",
                        "AvgTemperature", "MinTemperature", "MaxTemperature", "AvgRelativeHumidity",
                        "AvgHourlyPrecipitation", "MaxHourlyPrecipitation", "WetAirportHours",
                        "WetAirportHourRate", "AvgWindSpeed", "MaxWindGust", "AvgCloudCover"],
    "weather_airport": ["AirportKey", "OurAirportsID", "WeatherObservations", "AvgTemperature",
                        "MinTemperature", "MaxTemperature", "AvgRelativeHumidity", "TotalPrecipitation",
                        "WetAirportHours", "WetAirportHourRate", "AvgWindSpeed", "MaxWindGust", "AvgCloudCover"],
}


def load_data() -> dict[str, pd.DataFrame]:
    missing = [name for name in FILES.values() if not (DATA_DIR / name).exists()]
    if missing:
        raise FileNotFoundError(
            "Gold CSV exports are missing. Run export_gold_views.py first. Missing files:\n" +
            "\n".join(f"  - {name}" for name in missing)
        )
    data = {key: pd.read_csv(DATA_DIR / filename) for key, filename in FILES.items()}
    for key, required in REQUIRED_COLUMNS.items():
        absent = [column for column in required if column not in data[key].columns]
        if absent:
            raise ValueError(f"Unexpected schema in {FILES[key]}. Missing columns: {', '.join(absent)}")
    for key, columns in NUMERIC_COLUMNS.items():
        for column in columns:
            if column in data[key].columns:
                data[key][column] = pd.to_numeric(data[key][column], errors="coerce")
    for key in ("monthly", "monthly_airline"):
        if "MonthNumber" in data[key].columns:
            data[key] = data[key].sort_values("MonthNumber", kind="stable").reset_index(drop=True)
    for column in ("AirportRole", "ReportingAirlineCode", "IATAReportingAirlineCode", "IATACode", "Ident",
                   "AirportCode", "AirportName", "Municipality", "ISOCountry", "AirportType"):
        for frame in data.values():
            if column in frame.columns:
                frame[column] = frame[column].astype("string").str.strip()
    if "IsEndOfDay" in data["hour"].columns:
        data["hour"]["IsEndOfDay"] = pd.to_numeric(data["hour"]["IsEndOfDay"], errors="coerce").fillna(0).astype(int)
    return data


DATA = load_data()

FLIGHT_WEATHER_IMPACT_FILE = "flight_weather_impact_2025.csv"
FLIGHT_WEATHER_COVERAGE_FILE = "flight_weather_coverage_2025.csv"

FLIGHT_WEATHER_IMPACT_COLUMNS = [
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

FLIGHT_WEATHER_COVERAGE_COLUMNS = [
    "SourceMonth", "MonthNumber", "MonthName", "ExposureType", "AirportRole",
    "AirportKey", "AirportCode", "AirportName", "ISOCountry",
    "WeatherCoverageStatus", "BridgeExposureRows", "NonNullWeatherKeys",
    "MatchedStatusMissingKeyRows", "NonMatchedStatusHasKeyRows",
]


FLIGHT_WEATHER_MANIFEST_FILE = "flight_weather_manifest_2025.json"


def load_optional_snapshot(filename: str, required_columns: list[str]) -> pd.DataFrame:
    path = DATA_DIR / filename
    if not path.exists():
        return pd.DataFrame(columns=required_columns)
    frame = pd.read_csv(path, low_memory=False, dtype={"SourceMonth": str})
    absent = [c for c in required_columns if c not in frame.columns]
    if absent:
        raise ValueError(f"Unexpected schema in {filename}. Missing columns: {', '.join(absent)}")
    return frame


def load_flight_weather_manifest() -> dict[str, Any]:
    """Read the export manifest and confirm both CSVs are the exact files it describes."""
    import hashlib
    import json
    path = DATA_DIR / FLIGHT_WEATHER_MANIFEST_FILE
    if not path.exists():
        return {}
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"_integrity": "manifest unreadable"}
    problems = []
    for name in (FLIGHT_WEATHER_IMPACT_FILE, FLIGHT_WEATHER_COVERAGE_FILE):
        expected = manifest.get("Files", {}).get(name, {}).get("SHA256")
        file_path = DATA_DIR / name
        if not file_path.exists() or not expected:
            problems.append(f"{name} missing")
            continue
        digest = hashlib.sha256(file_path.read_bytes()).hexdigest()
        if digest != expected:
            problems.append(f"{name} differs from manifest")
    manifest["_integrity"] = "; ".join(problems) if problems else "OK"
    return manifest


DATA["flight_weather_impact"] = load_optional_snapshot(
    FLIGHT_WEATHER_IMPACT_FILE, FLIGHT_WEATHER_IMPACT_COLUMNS
)
DATA["flight_weather_coverage"] = load_optional_snapshot(
    FLIGHT_WEATHER_COVERAGE_FILE, FLIGHT_WEATHER_COVERAGE_COLUMNS
)
FW_MANIFEST = load_flight_weather_manifest()

FW_IMPACT_NUMERIC = [
    "MonthNumber", "AirportKey", "OurAirportsID", "PrecipitationBandSort",
    "WindSpeedBandSort", "MatchedExposureRows", "MatchedExposureFlights",
    "MatchedWeatherObservations", "CancelledFlights", "DivertedFlights",
    "EligibleFlights", "DelayedFlights", "DelayRatePct", "AvgSignedDelayMinutes",
    "TotalPositiveDelayMinutes", "AvgTemperature", "AvgRelativeHumidity",
    "AvgPrecipitation", "AvgWindSpeed", "AvgWindGust", "AvgCloudCover",
    "AvgMinutesAfterWeatherHour",
]
FW_COVERAGE_NUMERIC = [
    "MonthNumber", "AirportKey", "BridgeExposureRows", "NonNullWeatherKeys",
    "MatchedStatusMissingKeyRows", "NonMatchedStatusHasKeyRows",
]
for col in FW_IMPACT_NUMERIC:
    if col in DATA["flight_weather_impact"].columns:
        DATA["flight_weather_impact"][col] = pd.to_numeric(
            DATA["flight_weather_impact"][col], errors="coerce"
        )
for col in FW_COVERAGE_NUMERIC:
    if col in DATA["flight_weather_coverage"].columns:
        DATA["flight_weather_coverage"][col] = pd.to_numeric(
            DATA["flight_weather_coverage"][col], errors="coerce"
        )
for frame_key in ("flight_weather_impact", "flight_weather_coverage"):
    frame = DATA[frame_key]
    if "SourceMonth" in frame.columns:
        frame["SourceMonth"] = frame["SourceMonth"].astype("string").str.zfill(2)
    for col in ("ExposureType", "AirportRole", "AirportCode", "Ident", "AirportName", "Municipality",
                "ISOCountry", "PrecipitationBand", "WindSpeedBand", "WeatherCoverageStatus"):
        if col in frame.columns:
            frame[col] = frame[col].astype("string").str.strip()


def val(row: Any, key: str, default: Any = np.nan) -> Any:
    try:
        return row.get(key, default)
    except AttributeError:
        return default


def fmt_int(value: Any) -> str:
    if value is None or pd.isna(value):
        return "—"
    return f"{int(round(float(value))):,}"


def fmt_pct(value: Any) -> str:
    if value is None or pd.isna(value):
        return "—"
    return f"{float(value):.2f}%"


def fmt_min(value: Any) -> str:
    if value is None or pd.isna(value):
        return "—"
    return f"{float(value):+.1f} min"


def sum_col(frame: pd.DataFrame, column: str) -> float:
    if frame.empty or column not in frame.columns:
        return 0.0
    return float(pd.to_numeric(frame[column], errors="coerce").fillna(0).sum())


def weighted_rate(frame: pd.DataFrame, numerator: str, denominator: str) -> float:
    den = sum_col(frame, denominator)
    return (sum_col(frame, numerator) / den * 100.0) if den > 0 else np.nan


def rate_from_counts(numerator: Any, denominator: Any) -> float:
    try:
        d = float(denominator)
        return float(numerator) / d * 100.0 if d > 0 else np.nan
    except (TypeError, ValueError):
        return np.nan


def kpi_card(label: str, value: str, detail: str, accent: str, icon: str) -> html.Div:
    return html.Div([
        html.Div([html.Span(icon, className="kpi-icon", style={"color": accent}),
                  html.Span(label, className="kpi-label")], className="kpi-top"),
        html.Div(value, className="kpi-value"),
        html.Div(detail, className="kpi-detail"),
        html.Div(className="kpi-accent", style={"background": accent}),
    ], className="kpi-card")


def kpi_grid(cards: list[html.Div], class_name: str = "") -> html.Div:
    return html.Div(cards, className=f"kpi-grid {class_name}".strip())


def panel(title: str, subtitle: str, child: Any, class_name: str = "") -> html.Div:
    return html.Div([
        html.Div([html.Div(title, className="panel-title"), html.Div(subtitle, className="panel-subtitle")], className="panel-heading"),
        child,
    ], className=f"panel {class_name}".strip())


def graph(graph_id: str | None = None, figure: go.Figure | None = None, height: int = 360) -> dcc.Graph:
    # Dash 4.x requires every dcc.Graph to have a valid id.
    # Static graphs do not participate in callbacks, so assign a unique
    # generated id whenever a caller does not provide one.
    resolved_graph_id = graph_id or f"auto-graph-{uuid.uuid4().hex}"
    return dcc.Graph(
        id=resolved_graph_id,
        figure=figure,
        responsive=True,
        style={"height": f"{height}px", "width": "100%"},
        config={"displaylogo": False, "responsive": True, "modeBarButtonsToRemove": ["lasso2d", "select2d"]},
    )


def base_figure(fig: go.Figure, height: int = 360, legend: bool = True) -> go.Figure:
    fig.update_layout(
        template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font={"family": "Inter, Segoe UI, sans-serif", "color": TEXT, "size": 11},
        margin={"l": 48, "r": 24, "t": 28, "b": 48}, height=height,
        hoverlabel={"bgcolor": PANEL_2, "bordercolor": BORDER, "font": {"color": TEXT}},
        legend={"orientation": "h", "y": 1.12, "x": 0, "font": {"color": MUTED}, "itemclick": "toggle"},
        autosize=True,
    )
    if not legend:
        fig.update_layout(showlegend=False)
    fig.update_xaxes(showgrid=False, zeroline=False, tickfont={"color": MUTED}, linecolor=BORDER, automargin=True)
    fig.update_yaxes(showgrid=True, gridcolor=GRID, zeroline=False, tickfont={"color": MUTED}, linecolor="rgba(0,0,0,0)", automargin=True)
    return fig


def empty_figure(message: str = "No data available", height: int = 340) -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(text=message, x=.5, y=.5, xref="paper", yref="paper", showarrow=False,
                       font={"color": MUTED, "size": 13})
    return base_figure(fig, height, legend=False)


def month_labels(frame: pd.DataFrame) -> list[str]:
    if "MonthName" in frame:
        return frame["MonthName"].fillna("").astype(str).tolist()
    if "MonthNumber" in frame:
        return frame["MonthNumber"].astype("Int64").astype(str).tolist()
    return []


def make_table(frame: pd.DataFrame, columns: list[tuple[str, str]], page_size: int = 12) -> dash_table.DataTable | html.Div:
    keep = [key for key, _ in columns if key in frame.columns]
    if frame.empty or not keep:
        return html.Div("No records match the current selection.", className="empty-state")
    display = frame[keep].copy().replace({np.nan: None})
    labels = [{"name": label, "id": key} for key, label in columns if key in keep]
    return dash_table.DataTable(
        data=display.to_dict("records"), columns=labels, page_size=page_size,
        sort_action="native", filter_action="native", page_action="native",
        style_table={"overflowX": "auto", "maxHeight": "520px", "overflowY": "auto"},
        style_header={"backgroundColor": PANEL_2, "color": TEXT, "fontWeight": "700", "border": f"1px solid {BORDER}", "padding": "11px", "whiteSpace": "normal"},
        style_cell={"backgroundColor": PANEL, "color": TEXT, "border": f"1px solid {BORDER}", "padding": "10px", "fontFamily": "Inter, Segoe UI, sans-serif", "fontSize": "11px", "textAlign": "left", "minWidth": "90px", "maxWidth": "250px", "whiteSpace": "normal", "height": "auto"},
        style_data_conditional=[{"if": {"row_index": "odd"}, "backgroundColor": "#142236"}],
        tooltip_duration=None,
    )


def insight_card(kicker: str, title: str, body: str, accent: str = CYAN) -> html.Div:
    return html.Div([
        html.Div(kicker.upper(), className="insight-kicker", style={"color": accent}),
        html.Div(title, className="insight-title"),
        html.Div(body, className="insight-body"),
        html.Div(className="insight-stripe", style={"background": accent}),
    ], className="insight-card")


def note(text: str, label: str = "READING THE METRIC") -> html.Div:
    return html.Div([html.Span(label, className="note-label"), html.Span(text, className="note-text")], className="method-note")


def sidebar(pathname: str) -> html.Aside:
    items = [
        ("Overview", "/", "◫", "nav-overview"),
        ("Airline intelligence", "/airlines", "✈", "nav-airlines"),
        ("Airport intelligence", "/airports", "⌖", "nav-airports"),
        ("Time intelligence", "/time", "◷", "nav-time"),
        ("Weather intelligence", "/weather", "☁", "nav-weather"),
        ("Flight × Weather", "/flight-weather", "⛈", "nav-flight-weather"),
    ]
    links = [dcc.Link([html.Span(symbol, className="nav-symbol"), html.Span(label, className="nav-label")],
                     href=href, id=item_id, className="nav-link active" if pathname == href else "nav-link")
             for label, href, symbol, item_id in items]
    return html.Aside([
        html.Div([html.Div("A", className="brand-mark"), html.Div([
            html.Div("AERO INSIGHTS", className="brand-name"),
            html.Div("FLIGHT DATA INTELLIGENCE", className="brand-caption")
        ])], className="brand-row"),
        html.Div("WORKSPACE", className="nav-section-label"),
        html.Nav(links, className="nav-group"),
        html.Div([html.Div(className="sidebar-status-dot"), html.Div([
            html.Div("DATA SNAPSHOT", className="status-title"),
            html.Div("Gold views · BTS 2025", className="status-subtitle")
        ])], className="sidebar-status"),
        html.Div("FLIGHT DW 2025  ·  ANALYTICS", className="sidebar-footer"),
    ], className="sidebar")


def header(title: str, subtitle: str, meta_note: str = "BTS reporting carrier scope") -> html.Div:
    return html.Div([
        html.Div([html.Div("FLIGHT DW 2025  /  ANALYTICS", className="eyebrow"), html.H1(title),
                  html.Div(subtitle, className="page-subtitle")]),
        html.Div([html.Div("REPORTING PERIOD", className="top-meta-label"),
                  html.Div("JAN — DEC 2025", className="period-pill"),
                  html.Div(meta_note, className="top-meta-note")], className="period-box"),
    ], className="page-header")


# ----------------------------- FIGURE BUILDERS -----------------------------
def make_monthly_operational(frame: pd.DataFrame) -> go.Figure:
    if frame.empty:
        return empty_figure()
    f = frame.sort_values("MonthNumber")
    x = month_labels(f)
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(x=x, y=f["TotalFlights"], name="Total flights", marker_color="rgba(49,197,216,.42)",
                         hovertemplate="%{x}<br>Total flights: %{y:,.0f}<extra></extra>"), secondary_y=False)
    fig.add_trace(go.Scatter(x=x, y=f["DepartureDelayRatePct"], name="Departure delay rate", mode="lines+markers",
                             line={"color": CYAN, "width": 3}, marker={"size": 7},
                             hovertemplate="%{x}<br>Departure delay: %{y:.2f}%<extra></extra>"), secondary_y=True)
    fig.add_trace(go.Scatter(x=x, y=f["ArrivalDelayRatePct"], name="Arrival delay rate", mode="lines+markers",
                             line={"color": AMBER, "width": 2.5}, marker={"size": 6},
                             hovertemplate="%{x}<br>Arrival delay: %{y:.2f}%<extra></extra>"), secondary_y=True)
    fig.update_yaxes(title_text="Flights", secondary_y=False, showgrid=True, gridcolor=GRID)
    fig.update_yaxes(title_text="Delay rate (%)", secondary_y=True, showgrid=False)
    return base_figure(fig, 390)


def make_monthly_delay_counts(frame: pd.DataFrame) -> go.Figure:
    if frame.empty:
        return empty_figure()
    f = frame.sort_values("MonthNumber")
    fig = go.Figure()
    fig.add_bar(x=month_labels(f), y=f["DelayedDepartureFlights"], name="Delayed departures", marker_color=CYAN)
    fig.add_bar(x=month_labels(f), y=f["DelayedArrivalFlights"], name="Delayed arrivals", marker_color=AMBER)
    fig.update_layout(barmode="group", yaxis_title="Delayed flights")
    return base_figure(fig, 350)


def make_disruption_trend(frame: pd.DataFrame) -> go.Figure:
    if frame.empty:
        return empty_figure()
    f = frame.sort_values("MonthNumber").copy()
    f["CancellationRatePct"] = f.apply(lambda r: rate_from_counts(r.get("CancelledFlights"), r.get("TotalFlights")), axis=1)
    f["DiversionRatePct"] = f.apply(lambda r: rate_from_counts(r.get("DivertedFlights"), r.get("TotalFlights")), axis=1)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=month_labels(f), y=f["CancellationRatePct"], name="Cancellation rate", mode="lines+markers",
                             line={"color": RED, "width": 2.7}, hovertemplate="%{x}<br>Cancellation: %{y:.2f}%<extra></extra>"))
    fig.add_trace(go.Scatter(x=month_labels(f), y=f["DiversionRatePct"], name="Diversion rate", mode="lines+markers",
                             line={"color": VIOLET, "width": 2.7}, hovertemplate="%{x}<br>Diversion: %{y:.2f}%<extra></extra>"))
    fig.update_layout(yaxis_title="Share of total flights (%)")
    return base_figure(fig, 350)


def make_airline_bubble(frame: pd.DataFrame) -> go.Figure:
    if frame.empty:
        return empty_figure()
    f = frame.copy()
    sizes = np.sqrt(pd.to_numeric(f["TotalFlights"], errors="coerce").fillna(0).clip(lower=0))
    sizes = (sizes / max(float(sizes.max()), 1.0) * 34 + 9).tolist()
    fig = go.Figure(go.Scatter(
        x=f["TotalFlights"], y=f["DepartureDelayRatePct"], mode="markers+text",
        text=f["ReportingAirlineCode"], textposition="top center", marker={
            "size": sizes, "color": f["ArrivalDelayRatePct"], "colorscale": [[0, CYAN], [.55, BLUE], [1, RED]],
            "showscale": True, "colorbar": {"title": "Arrival<br>delay %", "tickfont": {"color": MUTED}},
            "line": {"color": "rgba(255,255,255,.25)", "width": 1}, "opacity": .88,
        }, customdata=f[["CancelledFlights", "DivertedFlights", "DelayedDepartureFlights"]].to_numpy(),
        hovertemplate="Airline %{text}<br>Flights: %{x:,.0f}<br>Departure delay: %{y:.2f}%<br>Delayed departures: %{customdata[2]:,.0f}<br>Cancelled: %{customdata[0]:,.0f}<br>Diverted: %{customdata[1]:,.0f}<extra></extra>"))
    fig.update_layout(xaxis_title="Total flights", yaxis_title="Departure delay rate (%)")
    return base_figure(fig, 360, legend=False)


def make_airline_treemap(frame: pd.DataFrame) -> go.Figure:
    if frame.empty:
        return empty_figure()
    f = frame[pd.to_numeric(frame["TotalFlights"], errors="coerce").fillna(0) > 0].copy()
    if f.empty:
        return empty_figure()
    fig = go.Figure(go.Treemap(
        labels=f["ReportingAirlineCode"], parents=[""] * len(f), values=f["TotalFlights"],
        marker={"colors": f["DepartureDelayRatePct"], "colorscale": [[0, GREEN], [.5, BLUE], [1, RED]],
                "colorbar": {"title": "Dep. delay %"}, "line": {"color": DARK, "width": 2}},
        customdata=f[["DepartureDelayRatePct", "ArrivalDelayRatePct", "DelayedDepartureFlights"]].to_numpy(),
        texttemplate="<b>%{label}</b><br>%{value:,.0f} flights",
        hovertemplate="Airline %{label}<br>Flights: %{value:,.0f}<br>Departure delay: %{customdata[0]:.2f}%<br>Arrival delay: %{customdata[1]:.2f}%<br>Delayed departures: %{customdata[2]:,.0f}<extra></extra>"))
    return base_figure(fig, 360, legend=False)


def make_airline_rank(frame: pd.DataFrame, metric: str) -> go.Figure:
    if frame.empty or metric not in frame.columns:
        return empty_figure("No airlines match these filters")
    f = frame.dropna(subset=[metric]).sort_values(metric, ascending=True).tail(14)
    if f.empty:
        return empty_figure("No values available for this metric")
    labels = f["ReportingAirlineCode"].astype(str)
    color = [CYAN if v == f[metric].min() else (RED if v == f[metric].max() else BLUE) for v in f[metric]]
    fig = go.Figure(go.Bar(x=f[metric], y=labels, orientation="h", marker_color=color,
                           customdata=f[["TotalFlights", "DelayedDepartureFlights", "CancelledFlights"]].to_numpy(),
                           hovertemplate="Airline %{y}<br>Selected metric: %{x:,.2f}<br>Total flights: %{customdata[0]:,.0f}<br>Delayed departures: %{customdata[1]:,.0f}<br>Cancelled: %{customdata[2]:,.0f}<extra></extra>"))
    fig.update_layout(showlegend=False, xaxis_title=metric.replace("Pct", " (%)").replace("AvgSigned", "Average signed ").replace("Minutes", " min").replace("Rate", " rate"), yaxis_title="")
    return base_figure(fig, 390, legend=False)


def make_airline_rate_compare(frame: pd.DataFrame) -> go.Figure:
    if frame.empty:
        return empty_figure()
    f = frame.sort_values("TotalFlights", ascending=False)
    fig = go.Figure()
    fig.add_bar(x=f["ReportingAirlineCode"], y=f["DepartureDelayRatePct"], name="Departure delay", marker_color=CYAN)
    fig.add_bar(x=f["ReportingAirlineCode"], y=f["ArrivalDelayRatePct"], name="Arrival delay", marker_color=AMBER)
    fig.update_layout(barmode="group", yaxis_title="Delay rate (%)", xaxis_title="Reporting airline")
    return base_figure(fig, 350)


def make_airline_monthly(frame: pd.DataFrame) -> go.Figure:
    if frame.empty:
        return empty_figure("Select one or more airlines")
    fig = go.Figure()
    palette = [CYAN, AMBER, BLUE, GREEN, VIOLET, RED, "#8DD3C7", "#FDBA74", "#93C5FD", "#F9A8D4", "#A3E635", "#C4B5FD", "#FCA5A5", "#67E8F9"]
    for i, (code, group) in enumerate(frame.groupby("ReportingAirlineCode", sort=True)):
        group = group.sort_values("MonthNumber")
        color = palette[i % len(palette)]
        fig.add_trace(go.Scatter(x=month_labels(group), y=group["DepartureDelayRatePct"], mode="lines+markers",
                                 name=f"{code} · Dep", line={"width": 2.2, "color": color},
                                 hovertemplate=f"{code} · Departure<br>%{{x}}<br>%{{y:.2f}}%<extra></extra>"))
        fig.add_trace(go.Scatter(x=month_labels(group), y=group["ArrivalDelayRatePct"], mode="lines",
                                 name=f"{code} · Arr", line={"width": 1.5, "dash": "dot", "color": color}, opacity=.75,
                                 hovertemplate=f"{code} · Arrival<br>%{{x}}<br>%{{y:.2f}}%<extra></extra>"))
    fig.update_layout(yaxis_title="Delay rate (%)")
    return base_figure(fig, 390)


def make_airline_monthly_volume(frame: pd.DataFrame) -> go.Figure:
    if frame.empty:
        return empty_figure("No monthly carrier data")
    fig = go.Figure()
    palette = [CYAN, AMBER, BLUE, GREEN, VIOLET, RED, "#8DD3C7", "#FDBA74", "#93C5FD", "#F9A8D4", "#A3E635", "#C4B5FD", "#FCA5A5", "#67E8F9"]
    for i, (code, group) in enumerate(frame.groupby("ReportingAirlineCode", sort=True)):
        group = group.sort_values("MonthNumber")
        fig.add_trace(go.Scatter(x=month_labels(group), y=group["TotalFlights"], name=str(code),
                                 mode="lines+markers", line={"width": 2.3, "color": palette[i % len(palette)]},
                                 hovertemplate=f"{code}<br>%{{x}}<br>Flights: %{{y:,.0f}}<extra></extra>"))
    fig.update_layout(yaxis_title="Total flights")
    return base_figure(fig, 360)


def make_airline_heatmap(frame: pd.DataFrame, metric: str) -> go.Figure:
    if frame.empty or metric not in frame.columns:
        return empty_figure("No airline-month values for this metric")
    f = frame.copy()
    f["MonthNumber"] = pd.to_numeric(f["MonthNumber"], errors="coerce")
    f = f.dropna(subset=["MonthNumber", metric, "ReportingAirlineCode"])
    if f.empty:
        return empty_figure("No airline-month values for this metric")
    f["MonthLabel"] = f["MonthName"].fillna(f["MonthNumber"].astype(int).astype(str))
    f = f.sort_values("MonthNumber")
    matrix = f.pivot_table(index="ReportingAirlineCode", columns="MonthLabel", values=metric, aggfunc="first")
    month_order = f[["MonthNumber", "MonthLabel"]].drop_duplicates().sort_values("MonthNumber")["MonthLabel"].tolist()
    matrix = matrix.reindex(columns=month_order)
    fig = go.Figure(go.Heatmap(
        z=matrix.to_numpy(), x=matrix.columns.tolist(), y=matrix.index.tolist(),
        colorscale=[[0, "#153B4A"], [.45, BLUE], [.72, AMBER], [1, RED]],
        colorbar={"title": "Delay<br>rate (%)", "tickfont": {"color": MUTED}},
        hovertemplate="Airline: %{y}<br>Month: %{x}<br>Delay rate: %{z:.2f}%<extra></extra>",
        xgap=2, ygap=2, zsmooth=False
    ))
    fig.update_layout(xaxis_title="Month", yaxis_title="Reporting airline")
    return base_figure(fig, max(360, 26 * len(matrix.index) + 100), legend=False)


def make_airline_disruptions(frame: pd.DataFrame) -> go.Figure:
    if frame.empty:
        return empty_figure()
    f = frame.copy()
    f["CancellationRatePct"] = f.apply(lambda r: rate_from_counts(r.get("CancelledFlights"), r.get("TotalFlights")), axis=1)
    f["DiversionRatePct"] = f.apply(lambda r: rate_from_counts(r.get("DivertedFlights"), r.get("TotalFlights")), axis=1)
    f = f.sort_values("CancellationRatePct", ascending=False)
    fig = go.Figure()
    fig.add_bar(x=f["ReportingAirlineCode"], y=f["CancellationRatePct"], name="Cancellation rate", marker_color=RED)
    fig.add_bar(x=f["ReportingAirlineCode"], y=f["DiversionRatePct"], name="Diversion rate", marker_color=VIOLET)
    fig.update_layout(barmode="group", yaxis_title="Share of total flights (%)", xaxis_title="Reporting airline")
    return base_figure(fig, 340)


def make_airport_rank(frame: pd.DataFrame, metric: str) -> go.Figure:
    if frame.empty or metric not in frame.columns:
        return empty_figure("No airports match the current filters")
    f = frame.dropna(subset=[metric]).sort_values(metric, ascending=True).tail(15)
    f = f.sort_values(metric, ascending=True)
    labels = f.apply(lambda r: f"{r.get('IATACode') if pd.notna(r.get('IATACode')) else r.get('Ident')} · {str(r.get('AirportName'))[:27]}", axis=1)
    fig = go.Figure(go.Bar(x=f[metric], y=labels, orientation="h",
                           marker_color=[RED if x >= f[metric].quantile(.8) else AMBER for x in f[metric]],
                           customdata=f[["ScheduledFlights", "EligibleFlights", "DelayedFlights"]].to_numpy(),
                           hovertemplate="%{y}<br>Metric: %{x:,.2f}<br>Scheduled: %{customdata[0]:,.0f}<br>Eligible: %{customdata[1]:,.0f}<br>Delayed: %{customdata[2]:,.0f}<extra></extra>"))
    fig.update_layout(showlegend=False, xaxis_title=metric.replace("Pct", " (%)").replace("Minutes", " min"), yaxis_title="")
    return base_figure(fig, 440, legend=False)


def make_airport_scatter(frame: pd.DataFrame) -> go.Figure:
    if frame.empty:
        return empty_figure()
    f = frame.copy()
    sizes = np.sqrt(pd.to_numeric(f["DelayedFlights"], errors="coerce").fillna(0).clip(lower=0))
    sizes = (sizes / max(float(sizes.max()), 1.0) * 32 + 7).tolist()
    labels = f.apply(lambda r: r.get("IATACode") if pd.notna(r.get("IATACode")) else r.get("Ident"), axis=1)
    fig = go.Figure(go.Scatter(
        x=f["ScheduledFlights"], y=f["DelayRatePct"], mode="markers",
        marker={"size": sizes, "color": f["AvgSignedDelayMinutes"], "colorscale": [[0, GREEN], [.5, BLUE], [1, RED]],
                "showscale": True, "colorbar": {"title": "Avg signed<br>min"}, "opacity": .78,
                "line": {"color": "rgba(255,255,255,.25)", "width": .6}},
        text=labels, customdata=f[["AirportName", "AirportRole", "EligibleFlights", "DelayedFlights", "TotalPositiveDelayMinutes"]].to_numpy(),
        hovertemplate="Airport %{text}<br>%{customdata[0]}<br>Role: %{customdata[1]}<br>Scheduled: %{x:,.0f}<br>Delay rate: %{y:.2f}%<br>Eligible: %{customdata[2]:,.0f}<br>Delayed: %{customdata[3]:,.0f}<br>Positive delay burden: %{customdata[4]:,.0f} min<extra></extra>"))
    fig.update_layout(xaxis_title="Scheduled flights", yaxis_title="Eligible-flight delay rate (%)")
    return base_figure(fig, 390, legend=False)


def make_airport_role_compare(frame: pd.DataFrame) -> go.Figure:
    if frame.empty:
        return empty_figure()
    g = frame.groupby("AirportRole", dropna=False).agg(
        ScheduledFlights=("ScheduledFlights", "sum"), EligibleFlights=("EligibleFlights", "sum"),
        DelayedFlights=("DelayedFlights", "sum"), TotalPositiveDelayMinutes=("TotalPositiveDelayMinutes", "sum")
    ).reset_index()
    g["WeightedDelayRatePct"] = g.apply(lambda r: rate_from_counts(r["DelayedFlights"], r["EligibleFlights"]), axis=1)
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(x=g["AirportRole"], y=g["ScheduledFlights"], name="Scheduled flights", marker_color="rgba(100,140,255,.55)"), secondary_y=False)
    fig.add_trace(go.Scatter(x=g["AirportRole"], y=g["WeightedDelayRatePct"], name="Weighted delay rate", mode="lines+markers",
                             line={"color": CYAN, "width": 3}, marker={"size": 9}), secondary_y=True)
    fig.update_yaxes(title_text="Scheduled flights", secondary_y=False, gridcolor=GRID)
    fig.update_yaxes(title_text="Weighted delay rate (%)", secondary_y=True, showgrid=False)
    return base_figure(fig, 350)


def make_airport_histogram(frame: pd.DataFrame) -> go.Figure:
    if frame.empty:
        return empty_figure()
    fig = go.Figure(go.Histogram(x=frame["DelayRatePct"], nbinsx=24, marker_color="rgba(49,197,216,.72)",
                                 hovertemplate="Delay-rate band: %{x:.1f}%<br>Airport-role rows: %{y}<extra></extra>"))
    fig.update_layout(xaxis_title="Delay rate (%)", yaxis_title="Number of airport-role records", bargap=.08)
    return base_figure(fig, 350, legend=False)


def ordered_hours(frame: pd.DataFrame) -> pd.DataFrame:
    f = frame.copy()
    f["_is_unknown"] = f["ScheduledDepartureHourLabel"].fillna("Unknown").astype(str).str.lower().eq("unknown")
    if "IsEndOfDay" not in f.columns:
        f["IsEndOfDay"] = 0
    if "ScheduledDepartureHour" not in f.columns:
        f["ScheduledDepartureHour"] = np.nan
    return f.sort_values(["_is_unknown", "IsEndOfDay", "ScheduledDepartureHour"], ascending=[True, True, True], na_position="last")


def make_hour_volume_rate(frame: pd.DataFrame) -> go.Figure:
    if frame.empty:
        return empty_figure()
    f = ordered_hours(frame)
    x = f["ScheduledDepartureHourLabel"].fillna("Unknown").astype(str)
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(x=x, y=f["ScheduledFlights"], name="Scheduled flights", marker_color="rgba(100,140,255,.52)"), secondary_y=False)
    fig.add_trace(go.Scatter(x=x, y=f["DepartureDelayRatePct"], name="Departure delay rate", mode="lines+markers",
                             line={"color": CYAN, "width": 3}, marker={"size": 6}), secondary_y=True)
    fig.update_yaxes(title_text="Scheduled flights", secondary_y=False, gridcolor=GRID)
    fig.update_yaxes(title_text="Delay rate (%)", secondary_y=True, showgrid=False)
    return base_figure(fig, 390)


def make_hour_delay_burden(frame: pd.DataFrame) -> go.Figure:
    if frame.empty:
        return empty_figure()
    f = ordered_hours(frame)
    x = f["ScheduledDepartureHourLabel"].fillna("Unknown").astype(str)
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(x=x, y=f["DelayedDepartureFlights"], name="Delayed departures", marker_color=AMBER), secondary_y=False)
    fig.add_trace(go.Scatter(x=x, y=f["AvgSignedDepartureDelayMinutes"], name="Average signed delay", mode="lines+markers",
                             line={"color": VIOLET, "width": 2.5}, marker={"size": 6}), secondary_y=True)
    fig.add_hline(y=0, line_dash="dot", line_color=MUTED, opacity=.5)
    fig.update_yaxes(title_text="Delayed flights", secondary_y=False, gridcolor=GRID)
    fig.update_yaxes(title_text="Average signed minutes", secondary_y=True, showgrid=False)
    return base_figure(fig, 360)


def make_hour_scatter(frame: pd.DataFrame) -> go.Figure:
    if frame.empty:
        return empty_figure()
    f = frame.copy()
    labels = f["ScheduledDepartureHourLabel"].fillna("Unknown").astype(str)
    fig = go.Figure(go.Scatter(x=f["ScheduledFlights"], y=f["DepartureDelayRatePct"], mode="markers+text",
                               text=labels, textposition="top center",
                               marker={"size": 12, "color": f["AvgSignedDepartureDelayMinutes"],
                                       "colorscale": [[0, GREEN], [.5, BLUE], [1, RED]], "showscale": True,
                                       "colorbar": {"title": "Avg signed<br>min"}},
                               customdata=f[["EligibleDepartureFlights", "DelayedDepartureFlights"]].to_numpy(),
                               hovertemplate="Hour %{text}<br>Scheduled: %{x:,.0f}<br>Delay rate: %{y:.2f}%<br>Eligible: %{customdata[0]:,.0f}<br>Delayed: %{customdata[1]:,.0f}<extra></extra>"))
    fig.update_layout(xaxis_title="Scheduled flights", yaxis_title="Departure delay rate (%)")
    return base_figure(fig, 350, legend=False)


def make_monthly_delay_profile(frame: pd.DataFrame) -> go.Figure:
    if frame.empty:
        return empty_figure()
    f = frame.sort_values("MonthNumber")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=month_labels(f), y=f["AvgSignedDepartureDelayMinutes"], name="Departure · signed average",
                             mode="lines+markers", line={"color": VIOLET, "width": 2.8}, marker={"size": 7}))
    fig.add_trace(go.Scatter(x=month_labels(f), y=f["AvgSignedArrivalDelayMinutes"], name="Arrival · signed average",
                             mode="lines+markers", line={"color": AMBER, "width": 2.5}, marker={"size": 6}))
    fig.add_hline(y=0, line_dash="dot", line_color=MUTED, opacity=.5)
    fig.update_layout(yaxis_title="Average signed delay (minutes)")
    return base_figure(fig, 350)


# ----------------------------- WEATHER FIGURES ------------------------------
def make_weather_temperature(frame: pd.DataFrame) -> go.Figure:
    if frame.empty:
        return empty_figure()
    f = frame.sort_values("MonthNumber")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=month_labels(f), y=f["AvgTemperature"], name="Average temperature",
                             mode="lines+markers", line={"color": CYAN, "width": 3}, marker={"size": 7}))
    fig.add_trace(go.Scatter(x=month_labels(f), y=f["MaxTemperature"], name="Monthly maximum",
                             mode="lines", line={"color": RED, "width": 1.8, "dash": "dot"}))
    fig.add_trace(go.Scatter(x=month_labels(f), y=f["MinTemperature"], name="Monthly minimum",
                             mode="lines", line={"color": BLUE, "width": 1.8, "dash": "dot"}))
    fig.update_layout(yaxis_title="Temperature (dataset unit)")
    return base_figure(fig, 360)


def make_weather_precipitation(frame: pd.DataFrame) -> go.Figure:
    if frame.empty:
        return empty_figure()
    f = frame.sort_values("MonthNumber")
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(x=month_labels(f), y=f["AvgHourlyPrecipitation"], name="Average hourly precipitation",
                         marker_color="rgba(49,197,216,.48)"), secondary_y=False)
    fig.add_trace(go.Scatter(x=month_labels(f), y=f["WetAirportHourRate"], name="Wet airport-hour rate",
                             mode="lines+markers", line={"color": AMBER, "width": 2.8}, marker={"size": 7}), secondary_y=True)
    fig.update_yaxes(title_text="Precipitation (dataset unit)", secondary_y=False)
    fig.update_yaxes(title_text="Wet airport-hours (%)", secondary_y=True, showgrid=False)
    return base_figure(fig, 360)


def make_weather_wind(frame: pd.DataFrame) -> go.Figure:
    if frame.empty:
        return empty_figure()
    f = frame.sort_values("MonthNumber")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=month_labels(f), y=f["AvgWindSpeed"], name="Average wind speed",
                             mode="lines+markers", line={"color": GREEN, "width": 2.8}, marker={"size": 7}))
    fig.add_trace(go.Scatter(x=month_labels(f), y=f["MaxWindGust"], name="Maximum gust observed",
                             mode="lines+markers", line={"color": RED, "width": 2, "dash": "dot"}, marker={"size": 6}))
    fig.update_layout(yaxis_title="Wind (dataset unit)")
    return base_figure(fig, 340)


def make_weather_cloud(frame: pd.DataFrame) -> go.Figure:
    if frame.empty:
        return empty_figure()
    f = frame.sort_values("MonthNumber")
    fig = go.Figure(go.Bar(x=month_labels(f), y=f["AvgCloudCover"], name="Average cloud cover",
                           marker_color="rgba(167,139,250,.62)"))
    fig.update_layout(yaxis_title="Cloud cover (%)", yaxis={"range": [0, 100]})
    return base_figure(fig, 340, legend=False)


def make_weather_airport_rank(frame: pd.DataFrame, metric: str) -> go.Figure:
    if frame.empty or metric not in frame.columns:
        return empty_figure("No airport weather records match these filters")
    f = frame.dropna(subset=[metric]).sort_values(metric, ascending=True).tail(15).copy()
    if f.empty:
        return empty_figure("No values available for this metric")
    f = f.sort_values(metric, ascending=True)
    labels = f.apply(lambda r: f"{r['AirportCode']} · {str(r['Municipality'])[:22]}", axis=1)
    fig = go.Figure(go.Bar(
        x=f[metric], y=labels, orientation="h",
        marker_color=[RED if x >= f[metric].quantile(.8) else CYAN for x in f[metric]],
        customdata=f[["AirportName", "ISOCountry", "WeatherObservations", "WetAirportHourRate", "TotalPrecipitation"]].to_numpy(),
        hovertemplate=("%{y}<br>%{customdata[0]}<br>Country: %{customdata[1]}<br>Selected metric: %{x:,.2f}"
                       "<br>Observations: %{customdata[2]:,.0f}<br>Wet airport-hour rate: %{customdata[3]:.2f}%"
                       "<br>Total precipitation: %{customdata[4]:,.2f}<extra></extra>")))
    fig.update_layout(showlegend=False, xaxis_title=metric.replace("Pct", " (%)"), yaxis_title="")
    return base_figure(fig, 470, legend=False)


def make_weather_airport_scatter(frame: pd.DataFrame) -> go.Figure:
    if frame.empty:
        return empty_figure("No airport weather records match these filters")
    f = frame.copy()
    sizes = np.sqrt(pd.to_numeric(f["WetAirportHours"], errors="coerce").fillna(0).clip(lower=0))
    sizes = (sizes / max(float(sizes.max()), 1.0) * 30 + 7).tolist()
    fig = go.Figure(go.Scatter(
        x=f["AvgTemperature"], y=f["WetAirportHourRate"], mode="markers",
        marker={"size": sizes, "color": f["TotalPrecipitation"],
                "colorscale": [[0, BLUE], [.55, CYAN], [1, AMBER]], "showscale": True,
                "colorbar": {"title": "Total<br>precipitation"}, "opacity": .82},
        text=f["AirportCode"],
        customdata=f[["AirportName", "Municipality", "ISOCountry", "TotalPrecipitation", "AvgWindSpeed"]].to_numpy(),
        hovertemplate=("Airport %{text}<br>%{customdata[0]}<br>%{customdata[1]}, %{customdata[2]}"
                       "<br>Average temperature: %{x:.2f}<br>Wet airport-hour rate: %{y:.2f}%"
                       "<br>Total precipitation: %{customdata[3]:,.2f}<br>Average wind speed: %{customdata[4]:.2f}<extra></extra>")))
    fig.update_layout(xaxis_title="Average temperature (dataset unit)", yaxis_title="Wet airport-hour rate (%)")
    return base_figure(fig, 390, legend=False)


# -------------------------------- PAGE LAYOUTS -----------------------------
def overview_insights() -> list[html.Div]:
    m = DATA["monthly"].dropna(subset=["DepartureDelayRatePct"]).copy()
    a = DATA["airline"].dropna(subset=["DepartureDelayRatePct"]).copy()
    cards: list[html.Div] = []
    if not m.empty:
        worst = m.loc[m["DepartureDelayRatePct"].idxmax()]
        best = m.loc[m["DepartureDelayRatePct"].idxmin()]
        peak = m.loc[m["TotalFlights"].idxmax()]
        cards.extend([
            insight_card("Monthly pressure", f"{worst['MonthName']} had the highest departure delay rate",
                         f"{fmt_pct(worst['DepartureDelayRatePct'])} across {fmt_int(worst['EligibleDepartureFlights'])} eligible departures. This is a descriptive peak, not an explanation of cause.", RED),
            insight_card("Lowest monthly rate", f"{best['MonthName']} recorded the lowest departure delay rate",
                         f"{fmt_pct(best['DepartureDelayRatePct'])} across {fmt_int(best['EligibleDepartureFlights'])} eligible departures.", GREEN),
            insight_card("Traffic concentration", f"{peak['MonthName']} had the largest monthly flight volume",
                         f"{fmt_int(peak['TotalFlights'])} flights in the monthly summary.", BLUE),
        ])
    if not a.empty:
        high_volume = a.sort_values("TotalFlights", ascending=False).iloc[0]
        high_rate = a.sort_values("DepartureDelayRatePct", ascending=False).iloc[0]
        cards.extend([
            insight_card("Largest carrier by volume", str(high_volume["ReportingAirlineCode"]),
                         f"{fmt_int(high_volume['TotalFlights'])} flights; departure delay rate {fmt_pct(high_volume['DepartureDelayRatePct'])}.", CYAN),
            insight_card("Highest carrier delay rate", str(high_rate["ReportingAirlineCode"]),
                         f"{fmt_pct(high_rate['DepartureDelayRatePct'])} among {fmt_int(high_rate['EligibleDepartureFlights'])} eligible departures.", AMBER),
        ])
    return cards


def overview_page() -> html.Div:
    k = DATA["kpi"].iloc[0] if not DATA["kpi"].empty else {}
    cards = kpi_grid([
        kpi_card("TOTAL FLIGHTS", fmt_int(val(k, "TotalFlights")), "BTS reporting carrier scope", CYAN, "✈"),
        kpi_card("DEPARTURE DELAY RATE", fmt_pct(val(k, "DepartureDelayRatePct")),
                 f"{fmt_int(val(k, 'DelayedDepartureFlights'))} delayed / {fmt_int(val(k, 'EligibleDepartureFlights'))} eligible", AMBER, "↗"),
        kpi_card("ARRIVAL DELAY RATE", fmt_pct(val(k, "ArrivalDelayRatePct")),
                 f"{fmt_int(val(k, 'DelayedArrivalFlights'))} delayed / {fmt_int(val(k, 'EligibleArrivalFlights'))} eligible", BLUE, "◷"),
        kpi_card("CANCELLED FLIGHTS", fmt_int(val(k, "CancelledFlights")),
                 f"Cancellation share {fmt_pct(rate_from_counts(val(k, 'CancelledFlights'), val(k, 'TotalFlights')))}", RED, "×"),
        kpi_card("DIVERTED FLIGHTS", fmt_int(val(k, "DivertedFlights")),
                 f"Diversion share {fmt_pct(rate_from_counts(val(k, 'DivertedFlights'), val(k, 'TotalFlights')))}", VIOLET, "⇢"),
        kpi_card("DELAYED DEPARTURES", fmt_int(val(k, "DelayedDepartureFlights")),
                 f"Eligible: {fmt_int(val(k, 'EligibleDepartureFlights'))}", AMBER, "↗"),
        kpi_card("DELAYED ARRIVALS", fmt_int(val(k, "DelayedArrivalFlights")),
                 f"Eligible: {fmt_int(val(k, 'EligibleArrivalFlights'))}", BLUE, "◷"),
        kpi_card("AVG SIGNED DEP. DELAY", fmt_min(val(k, "AvgSignedDepartureDelayMinutes")),
                 "Negative values indicate early departures", GREEN, "±"),
    ], "kpi-grid-4")
    monthly = DATA["monthly"].copy()
    airline = DATA["airline"].copy()
    return html.Div([
        cards,
        html.Div([
            panel("Operational pulse", "Monthly flight volume with departure and arrival delay rates", graph(figure=make_monthly_operational(monthly), height=390), "panel-wide"),
            panel("Carrier footprint", "Tile size = total flights · color = departure delay rate", graph(figure=make_airline_treemap(airline), height=390)),
        ], className="content-grid main-grid"),
        html.Div([
            panel("Delay burden by month", "Counts of delayed departures and delayed arrivals; populations follow their respective eligibility rules", graph(figure=make_monthly_delay_counts(monthly), height=350)),
            panel("Disruption trend", "Cancellation and diversion shares of total monthly flights", graph(figure=make_disruption_trend(monthly), height=350)),
        ], className="content-grid"),
        panel("What stands out in 2025", "Descriptive insights calculated from the annual and monthly Gold Views", html.Div(overview_insights(), className="insight-grid")),
        panel("Monthly operating detail", "Sortable table for monthly volume, delay, cancellation and diversion", make_table(monthly.sort_values("MonthNumber"), [
            ("MonthName", "Month"), ("TotalFlights", "Total flights"), ("EligibleDepartureFlights", "Eligible departures"),
            ("DelayedDepartureFlights", "Delayed departures"), ("DepartureDelayRatePct", "Departure delay rate (%)"),
            ("EligibleArrivalFlights", "Eligible arrivals"), ("DelayedArrivalFlights", "Delayed arrivals"),
            ("ArrivalDelayRatePct", "Arrival delay rate (%)"), ("CancelledFlights", "Cancelled"), ("DivertedFlights", "Diverted")], 12)),
        note("Departure and arrival delay rates use their own eligible-flight denominators. Cancellation/diversion shares use total flights as denominator. Average signed delay retains negative values for early operations; it is not the same as total delay burden."),
        html.Div("Source: MySQL Gold Views · local snapshot exported from Flight DW 2025", className="source-line"),
    ])


def airline_page() -> html.Div:
    airlines = DATA["airline"].copy()
    codes = sorted(airlines["ReportingAirlineCode"].dropna().astype(str).unique())
    max_flights = max(1, int(pd.to_numeric(airlines["TotalFlights"], errors="coerce").max() or 1))
    slider_step = max(1, max_flights // 100)
    return html.Div([
        html.Div([
            html.Div([html.Div("COMPARE AIRLINES", className="filter-label"), dcc.Dropdown(
                id="airline-select", options=[{"label": c, "value": c} for c in codes], value=codes,
                multi=True, placeholder="Select airlines", className="dark-dropdown")]),
            html.Div([html.Div("RANKING METRIC", className="filter-label"), dcc.Dropdown(
                id="airline-metric", options=[
                    {"label": "Departure delay rate", "value": "DepartureDelayRatePct"},
                    {"label": "Arrival delay rate", "value": "ArrivalDelayRatePct"},
                    {"label": "Average signed departure delay", "value": "AvgSignedDepartureDelayMinutes"},
                    {"label": "Average signed arrival delay", "value": "AvgSignedArrivalDelayMinutes"},
                    {"label": "Cancellation rate", "value": "CancellationRatePct"},
                    {"label": "Delayed departure count", "value": "DelayedDepartureFlights"},
                    {"label": "Total flight volume", "value": "TotalFlights"},
                ], value="DepartureDelayRatePct", clearable=False, className="dark-dropdown")]),
            html.Div([html.Div("MINIMUM FLIGHT VOLUME", className="filter-label"), dcc.Slider(
                id="airline-min-flights", min=0, max=max_flights, step=slider_step, value=0,
                marks={0: "0", max_flights: fmt_int(max_flights)}, tooltip={"placement": "bottom", "always_visible": False})]),
        ], className="filter-bar filter-grid-3"),
        html.Div(id="airline-kpis"),
        html.Div(id="airline-insights", className="insight-grid"),
        html.Div([
            panel("Airline leaderboard", "Selected ranking metric · higher delay metrics indicate greater operational pressure", graph("airline-ranking", height=410), "panel-wide"),
            panel("Departure vs arrival reliability", "Side-by-side eligible-flight delay rates by carrier", graph("airline-rate-compare", height=360)),
        ], className="content-grid main-grid"),
        html.Div([
            panel("Monthly carrier trajectory", "Solid lines = departure delay · dotted lines = arrival delay; select fewer carriers for readability", graph("airline-monthly", height=420), "panel-wide"),
            panel("Cancellation and diversion profile", "Shares of each carrier's total flights", graph("airline-disruptions", height=360)),
        ], className="content-grid main-grid"),
        panel("Scale versus delay exposure", "Bubble size reflects flight volume; color reflects arrival delay rate", graph("airline-bubble", height=360)),
        panel("Monthly flight volume by carrier", "Compare each selected carrier's monthly operating scale", graph("airline-monthly-volume", height=370)),
        html.Div([
            panel("Departure delay heatmap", "Carrier × month; darker-to-warmer cells indicate higher departure delay rate", graph("airline-heatmap-dep", height=430)),
            panel("Arrival delay heatmap", "Carrier × month; compare monthly arrival delay-rate patterns", graph("airline-heatmap-arr", height=430)),
        ], className="content-grid"),
        panel("Carrier performance detail", "Sortable and filterable annual carrier metrics", html.Div(id="airline-table-wrap")),
        note("Delay rates are recomputed as total delayed flights divided by total eligible flights for the selected carriers. Do not take an unweighted average of carrier percentages. Average signed-delay fields are carrier-level means and are not pooled across carriers in the KPI cards."),
    ])


def airport_page() -> html.Div:
    airport = DATA["airport"].copy()
    roles = sorted(airport["AirportRole"].dropna().astype(str).unique().tolist())
    max_eligible = max(1, int(pd.to_numeric(airport["EligibleFlights"], errors="coerce").max() or 1))
    default_threshold = min(1000, max_eligible)
    step = max(1, max_eligible // 100)
    return html.Div([
        html.Div([
            html.Div([html.Div("AIRPORT ROLE", className="filter-label"), dcc.Dropdown(
                id="airport-role", options=[{"label": "All roles", "value": "ALL"}] + [{"label": r.title(), "value": r} for r in roles],
                value="ALL", clearable=False, className="dark-dropdown")]),
            html.Div([html.Div("SEARCH AIRPORT", className="filter-label"), dcc.Input(
                id="airport-search", type="text", placeholder="IATA, ident, airport name, municipality or country", debounce=True, className="dark-input")]),
            html.Div([html.Div("RANKING METRIC", className="filter-label"), dcc.Dropdown(
                id="airport-metric", options=[
                    {"label": "Eligible-flight delay rate", "value": "DelayRatePct"},
                    {"label": "Average signed delay (minutes)", "value": "AvgSignedDelayMinutes"},
                    {"label": "Total positive delay minutes", "value": "TotalPositiveDelayMinutes"},
                    {"label": "Scheduled flight volume", "value": "ScheduledFlights"},
                ], value="DelayRatePct", clearable=False, className="dark-dropdown")]),
            html.Div([html.Div("MINIMUM ELIGIBLE FLIGHTS", className="filter-label"), dcc.Slider(
                id="airport-min-eligible", min=0, max=max_eligible, step=step, value=default_threshold,
                marks={0: "0", max_eligible: fmt_int(max_eligible)}, tooltip={"placement": "bottom", "always_visible": False})]),
        ], className="filter-bar filter-grid-4"),
        html.Div(id="airport-kpis"),
        html.Div(id="airport-insights", className="insight-grid"),
        html.Div([
            panel("Airport performance leaderboard", "Top 15 airport-role rows under the chosen metric and minimum eligible-flight threshold", graph("airport-ranking", height=470), "panel-wide"),
            panel("Activity versus delay exposure", "Each bubble is one airport-role record; size reflects delayed-flight count", graph("airport-scatter", height=420)),
        ], className="content-grid main-grid"),
        html.Div([
            panel("Origin versus destination role", "Weighted delay rate uses sum of delayed flights / sum of eligible flights", graph("airport-role-compare", height=350)),
            panel("Distribution of airport delay rates", "Frequency across filtered airport-role records; not a geographic map", graph("airport-histogram", height=350)),
        ], className="content-grid"),
        panel("Airport detail explorer", "Annual airport-role metrics. The same physical airport may appear once as Origin and once as Destination.", html.Div(id="airport-table-wrap")),
        note("This Gold View is annual by airport and AirportRole. When both roles are selected, a flight may contribute once at its origin and once at its destination; airport-role scheduled-flight totals are therefore not a unique system-wide flight count. The View has no Month, latitude or longitude, so this page does not claim monthly airport trends or geographic mapping. The minimum eligible-flight threshold helps avoid ranking very small denominators."),
    ])


def time_page() -> html.Div:
    max_eligible = max(1, int(pd.to_numeric(DATA["hour"]["EligibleDepartureFlights"], errors="coerce").max() or 1))
    step = max(1, max_eligible // 100)
    return html.Div([
        html.Div([
            html.Div([html.Div("HOUR SCOPE", className="filter-label"), dcc.Dropdown(
                id="hour-scope", options=[{"label": "All buckets", "value": "ALL"},
                                      {"label": "Exclude Unknown time", "value": "KNOWN"}],
                value="KNOWN", clearable=False, className="dark-dropdown")]),
            html.Div([html.Div("MINIMUM ELIGIBLE FLIGHTS FOR PEAK INSIGHTS", className="filter-label"), dcc.Slider(
                id="hour-min-eligible", min=0, max=max_eligible, step=step, value=min(10000, max_eligible),
                marks={0: "0", max_eligible: fmt_int(max_eligible)}, tooltip={"placement": "bottom", "always_visible": False})]),
        ], className="filter-bar filter-grid-2"),
        html.Div(id="time-kpis"),
        html.Div(id="time-insights", className="insight-grid"),
        panel("Departure profile across the operating day", "Scheduled flight volume and eligible-flight delay rate; the 24:00 sentinel is retained as its own bucket", graph("hour-volume-rate", height=410)),
        html.Div([
            panel("Delay count and signed delay intensity", "Delayed departure count with average signed departure delay", graph("hour-delay-burden", height=360)),
            panel("Volume versus delay rate", "Hour buckets with higher volume and higher delay exposure", graph("hour-scatter", height=360)),
        ], className="content-grid"),
        panel("Monthly signed-delay profile", "Monthly mean signed departure and arrival delay; negative values indicate early operations", graph(figure=make_monthly_delay_profile(DATA["monthly"]), height=350)),
        panel("Hourly operating detail", "Sortable hourly buckets including a separately retained 24:00 sentinel", html.Div(id="hour-table-wrap")),
        note("This Gold View provides scheduled departure hour, not day-of-week or route. Unknown times can be excluded from the main hourly comparison, while the end-of-day 24:00 sentinel remains visible and is not recoded as 00:00."),
    ])


def weather_month_icon(row: pd.Series) -> tuple[str, str]:
    """A visual seasonal cue inferred from monthly historical aggregates (not a forecast)."""
    wet = float(row.get("WetAirportHourRate", 0) or 0)
    cloud = float(row.get("AvgCloudCover", 0) or 0)
    temp = float(row.get("AvgTemperature", 0) or 0)
    if wet >= 16:
        return "🌧️", "Rainier"
    if cloud >= 58:
        return "☁️", "Cloudier"
    if temp >= 20 and wet < 14:
        return "☀️", "Warmer"
    return "⛅", "Mixed"


def weather_spotlight_content(code: str | None) -> html.Div:
    airport = DATA["weather_airport"]
    if airport.empty:
        return html.Div("No airport weather profile available.", className="empty-state")
    selected = airport[airport["AirportCode"].astype(str) == str(code)].head(1)
    if selected.empty:
        selected = airport.head(1)
    r = selected.iloc[0]
    return html.Div([
        html.Div([
            html.Div(str(r["AirportCode"]), className="weather-spot-code"),
            html.Div(str(r["AirportName"]), className="weather-spot-name"),
            html.Div(f"{r['Municipality']}, {r['ISOCountry']}", className="weather-spot-location"),
            html.Div("2025 annual airport profile · 8,760 hourly observations", className="weather-spot-meta"),
        ], className="weather-spot-heading"),
        html.Div([
            html.Div([html.Div(f"{float(r['AvgTemperature']):.1f}°", className="weather-spot-temp"),
                      html.Div("AVERAGE TEMPERATURE", className="weather-spot-label")], className="weather-spot-primary"),
            html.Div([
                html.Div([html.Span("💧", className="weather-spot-icon"), html.Div([html.Div(f"{float(r['AvgRelativeHumidity']):.1f}%", className="weather-spot-value"), html.Div("Humidity", className="weather-spot-label")])], className="weather-spot-metric"),
                html.Div([html.Span("🌧️", className="weather-spot-icon"), html.Div([html.Div(f"{float(r['WetAirportHourRate']):.1f}%", className="weather-spot-value"), html.Div("Wet hours", className="weather-spot-label")])], className="weather-spot-metric"),
                html.Div([html.Span("💨", className="weather-spot-icon"), html.Div([html.Div(f"{float(r['AvgWindSpeed']):.1f}", className="weather-spot-value"), html.Div("Avg wind · source unit", className="weather-spot-label")])], className="weather-spot-metric"),
                html.Div([html.Span("☁️", className="weather-spot-icon"), html.Div([html.Div(f"{float(r['AvgCloudCover']):.1f}%", className="weather-spot-value"), html.Div("Cloud cover", className="weather-spot-label")])], className="weather-spot-metric"),
            ], className="weather-spot-metrics"),
        ], className="weather-spot-body"),
        html.Div([
            html.Span(f"Annual precipitation: {float(r['TotalPrecipitation']):,.1f} · source unit", className="weather-spot-foot-item"),
            html.Span(f"Peak gust: {float(r['MaxWindGust']):,.1f} · source unit", className="weather-spot-foot-item"),
        ], className="weather-spot-footer"),
    ], className="weather-spotlight-card")


def weather_page() -> html.Div:
    monthly = DATA["weather_monthly"].sort_values("MonthNumber").copy()
    airport = DATA["weather_airport"].copy()
    observations = int(monthly["WeatherObservations"].sum())
    airport_count = int(airport["AirportCode"].nunique())
    hours_per_airport = int(airport["WeatherObservations"].min()) if not airport.empty else 0
    avg_temp = float(np.average(monthly["AvgTemperature"], weights=monthly["WeatherObservations"])) if observations else np.nan
    wet_hours = int(monthly["WetAirportHours"].sum())
    wet_rate = wet_hours / observations * 100 if observations else np.nan
    max_gust = float(airport["MaxWindGust"].max()) if not airport.empty else np.nan

    warmest = monthly.loc[monthly["AvgTemperature"].idxmax()]
    coolest = monthly.loc[monthly["AvgTemperature"].idxmin()]
    wettest_month = monthly.loc[monthly["WetAirportHourRate"].idxmax()]
    wettest_airport = airport.loc[airport["TotalPrecipitation"].idxmax()]
    countries = sorted(airport["ISOCountry"].dropna().astype(str).unique().tolist())
    airport_codes = sorted(airport["AirportCode"].dropna().astype(str).unique().tolist())
    default_airport = "ATL" if "ATL" in airport_codes else (airport_codes[0] if airport_codes else None)

    month_cards = []
    for _, r in monthly.iterrows():
        icon, condition = weather_month_icon(r)
        month_cards.append(html.Div([
            html.Div([html.Span(icon, className="weather-month-icon"),
                      html.Span(str(r["MonthName"])[:3].upper(), className="weather-month-name")], className="weather-month-top"),
            html.Div(f"{float(r['AvgTemperature']):.1f}°", className="weather-month-temp"),
            html.Div(condition, className="weather-month-condition"),
            html.Div([html.Span("RAIN"), html.Strong(f"{float(r['WetAirportHourRate']):.1f}%")], className="weather-month-rain"),
        ], className="weather-month-card"))

    return html.Div([
        html.Div([
            html.Div([
                html.Div([html.Span("✦", className="weather-eyebrow-icon"), html.Span("AERO WEATHER DESK · 2025 HISTORICAL")], className="weather-eyebrow"),
                html.H2("Weather, through every season", className="weather-hero-title"),
                html.P("A year-long view of airport weather conditions across the network. Explore seasonal patterns, rainfall, wind and local airport profiles.", className="weather-hero-copy"),
                html.Div([
                    html.Div([html.Div(f"{avg_temp:.1f}°" if pd.notna(avg_temp) else "—", className="weather-hero-temp"),
                              html.Div([html.Div("NETWORK AVERAGE", className="weather-hero-temp-label"),
                                        html.Div("Weighted by hourly observations", className="weather-hero-temp-note")])], className="weather-hero-temp-wrap"),
                    html.Div([
                        html.Div([html.Span("☀", className="weather-mini-icon"), html.Div([html.Div(str(warmest["MonthName"]), className="weather-mini-value"), html.Div("Warmest month", className="weather-mini-label")])], className="weather-mini-stat"),
                        html.Div([html.Span("❄", className="weather-mini-icon cool"), html.Div([html.Div(str(coolest["MonthName"]), className="weather-mini-value"), html.Div("Coolest month", className="weather-mini-label")])], className="weather-mini-stat"),
                        html.Div([html.Span("🌧", className="weather-mini-icon rain"), html.Div([html.Div(str(wettest_month["MonthName"]), className="weather-mini-value"), html.Div("Highest wet-hour rate", className="weather-mini-label")])], className="weather-mini-stat"),
                    ], className="weather-mini-stats"),
                ], className="weather-hero-bottom"),
            ], className="weather-hero-main"),
            html.Div([
                html.Div("YEAR AT A GLANCE", className="weather-glance-kicker"),
                html.Div("🌤️", className="weather-glance-art"),
                html.Div("2025", className="weather-glance-year"),
                html.Div("FULL-YEAR WEATHER RECORD", className="weather-glance-label"),
                html.Div([
                    html.Div([html.Strong(fmt_int(observations)), html.Span("hourly observations")], className="weather-glance-row"),
                    html.Div([html.Strong(fmt_int(airport_count)), html.Span("airports monitored")], className="weather-glance-row"),
                    html.Div([html.Strong("12 / 12"), html.Span("months complete")], className="weather-glance-row"),
                ], className="weather-glance-facts"),
            ], className="weather-glance-card"),
        ], className="weather-hero"),

        html.Div([
            html.Div([html.Div("THE YEAR IN WEATHER", className="weather-section-kicker"),
                      html.H3("Month-by-month atmosphere", className="weather-section-title"),
                      html.P("Historical monthly averages · not a future forecast", className="weather-section-subtitle")]),
            html.Div(month_cards, className="weather-month-grid"),
            html.Div("Monthly icons are illustrative cues derived from wet-hour rate, cloud cover and average temperature; they are not observed WMO weather-condition codes.", className="weather-interpretation-note"),
        ], className="weather-forecast-section"),

        html.Div([
            html.Div([html.Div("WEATHER SIGNALS", className="weather-section-kicker"),
                      html.H3("Read the seasonal pattern", className="weather-section-title"),
                      html.P("Temperature, precipitation and wind behaviour across 352 airport sites.", className="weather-section-subtitle")]),
            html.Div([
                panel("Temperature rhythm", "Monthly mean with observed monthly minimum and maximum · source temperature unit", graph(figure=make_weather_temperature(monthly), height=360)),
                panel("Rainfall & wet-hour frequency", "Average precipitation per airport-hour and share of hours with precipitation > 0", graph(figure=make_weather_precipitation(monthly), height=360)),
            ], className="content-grid main-grid weather-graphs"),
            html.Div([
                panel("Wind across the year", "Monthly average wind speed and maximum airport-level gust · source units", graph(figure=make_weather_wind(monthly), height=330)),
                panel("Cloud cover", "Monthly average cloud-cover percentage", graph(figure=make_weather_cloud(monthly), height=330)),
            ], className="content-grid weather-graphs"),
        ], className="weather-analysis-section"),

        html.Div([
            html.Div([html.Div("LOCAL AIRPORT CONDITIONS", className="weather-section-kicker"),
                      html.H3("Airport weather spotlight", className="weather-section-title"),
                      html.P("Select an airport to explore its 2025 annual weather profile.", className="weather-section-subtitle")]),
            html.Div([
                html.Div("CHOOSE AIRPORT", className="filter-label"),
                dcc.Dropdown(id="weather-airport-select", options=[{"label": c, "value": c} for c in airport_codes],
                             value=default_airport, clearable=False, searchable=True, className="dark-dropdown"),
            ], className="weather-airport-picker"),
            html.Div(id="weather-airport-spotlight", children=weather_spotlight_content(default_airport)),
        ], className="weather-spotlight-section"),

        html.Div([
            html.Div([html.Div("AIRPORT COMPARISON", className="weather-section-kicker"),
                      html.H3("Explore weather by airport", className="weather-section-title"),
                      html.P("Filter the airport network and rank sites by selected weather indicators.", className="weather-section-subtitle")]),
            html.Div([
                html.Div([html.Div("COUNTRY FILTER", className="filter-label"), dcc.Dropdown(
                    id="weather-country", options=[{"label": c, "value": c} for c in countries],
                    value=countries, multi=True, placeholder="Select countries", className="dark-dropdown")]),
                html.Div([html.Div("AIRPORT RANKING METRIC", className="filter-label"), dcc.Dropdown(
                    id="weather-metric", options=[
                        {"label": "Total precipitation", "value": "TotalPrecipitation"},
                        {"label": "Wet airport-hour rate", "value": "WetAirportHourRate"},
                        {"label": "Average temperature", "value": "AvgTemperature"},
                        {"label": "Average relative humidity", "value": "AvgRelativeHumidity"},
                        {"label": "Average wind speed", "value": "AvgWindSpeed"},
                        {"label": "Maximum wind gust", "value": "MaxWindGust"},
                        {"label": "Average cloud cover", "value": "AvgCloudCover"},
                    ], value="TotalPrecipitation", clearable=False, className="dark-dropdown")]),
                html.Div([html.Div("SEARCH AIRPORT", className="filter-label"), dcc.Input(
                    id="weather-search", type="text", placeholder="Airport code, name or municipality",
                    debounce=True, className="dark-input")]),
            ], className="filter-bar filter-grid-3"),
            html.Div([
                panel("Weather leaderboard", "Top 15 airports under the selected metric and country filter", graph("weather-airport-ranking", height=450), "panel-wide"),
                panel("Temperature vs wet-hour exposure", "Bubble size = wet airport-hours · colour = annual precipitation", graph("weather-airport-scatter", height=390)),
            ], className="content-grid main-grid"),
            panel("Airport weather detail", "Annual profile · one row per airport · sortable and searchable table", html.Div(id="weather-airport-table")),
        ], className="weather-airport-analysis"),

        html.Div([
            html.Strong("DATA SCOPE"),
            html.Span(" Weather Fact: full-year January–December 2025, 3,083,520 observations across 352 airports, with 8,760 hours per airport. Weather–Flight Exposure is a separate scope and currently has completed Bridge partitions only for January–September 2025. Weather associations are descriptive and do not establish causation. Units follow the STEP28C/Open-Meteo source configuration."),
        ], className="weather-scope-banner"),
        html.Div("Source: Fact_Airport_Weather_Hourly · dim_airport · validated 2025 weather snapshots", className="source-line"),
    ], className="weather-page")


# -------------------------- FLIGHT x WEATHER RELATION ------------------------
FW_EXPOSURE_OPTIONS = [
    {"label": "Departure · scheduled at origin", "value": "SCHEDULED_DEPARTURE"},
    {"label": "Departure · actual at origin", "value": "ACTUAL_DEPARTURE"},
    {"label": "Arrival · scheduled at destination", "value": "SCHEDULED_ARRIVAL"},
    {"label": "Arrival · actual at destination", "value": "ACTUAL_ARRIVAL"},
]
FW_EXPOSURE_LABELS = {x["value"]: x["label"] for x in FW_EXPOSURE_OPTIONS}
FW_MONTH_NAMES = {
    "01": "January", "02": "February", "03": "March", "04": "April",
    "05": "May", "06": "June", "07": "July", "08": "August", "09": "September",
    "10": "October", "11": "November", "12": "December",
}


def fw_available_months() -> list[str]:
    """Months actually present in the installed snapshot (never assumed)."""
    frame = DATA.get("flight_weather_coverage", pd.DataFrame())
    if frame.empty or "SourceMonth" not in frame.columns:
        return []
    return sorted(m for m in frame["SourceMonth"].dropna().astype(str).str.zfill(2).unique() if m in FW_MONTH_NAMES)


def fw_scope_label() -> str:
    label = FW_MANIFEST.get("ScopeLabel") if FW_MANIFEST else None
    if label:
        return label
    months = fw_available_months()
    if not months:
        return "snapshot not installed"
    return f"{FW_MONTH_NAMES[months[0]]}–{FW_MONTH_NAMES[months[-1]]} 2025"


def fw_empty(message: str = "Run the Flight × Weather SQL export to populate this view.") -> go.Figure:
    return empty_figure(message, 350)


def fw_band_summary(frame: pd.DataFrame, band_col: str, sort_col: str) -> pd.DataFrame:
    if frame.empty or band_col not in frame.columns:
        return pd.DataFrame()
    work = frame.copy()
    work["EligibleFlights"] = pd.to_numeric(work["EligibleFlights"], errors="coerce").fillna(0)
    work["DelayedFlights"] = pd.to_numeric(work["DelayedFlights"], errors="coerce").fillna(0)
    group = work.groupby([sort_col, band_col], dropna=False).agg(
        EligibleFlights=("EligibleFlights", "sum"),
        DelayedFlights=("DelayedFlights", "sum"),
        MatchedExposureFlights=("MatchedExposureFlights", "sum"),
    ).reset_index().sort_values(sort_col)
    group["DelayRatePct"] = np.where(
        group["EligibleFlights"] > 0,
        group["DelayedFlights"] / group["EligibleFlights"] * 100.0,
        np.nan,
    )
    return group


def fw_make_band_chart(frame: pd.DataFrame, band_col: str, sort_col: str, title: str) -> go.Figure:
    summary = fw_band_summary(frame, band_col, sort_col)
    if summary.empty or summary["EligibleFlights"].sum() <= 0:
        return fw_empty("No eligible flight observations for the selected condition.")
    fig = go.Figure()
    fig.add_bar(
        x=summary[band_col].astype(str), y=summary["DelayRatePct"],
        marker_color=[CYAN, BLUE, AMBER, RED][:len(summary)],
        customdata=summary[["EligibleFlights", "DelayedFlights", "MatchedExposureFlights"]].to_numpy(),
        hovertemplate=("%{x}<br>Delay rate: %{y:.2f}%<br>Eligible: %{customdata[0]:,.0f}"
                       "<br>Delayed: %{customdata[1]:,.0f}<br>Matched exposures: %{customdata[2]:,.0f}<extra></extra>"),
    )
    fig.update_layout(title=None, xaxis_title=title, yaxis_title="Delay rate among eligible flights (%)")
    return base_figure(fig, 350, legend=False)


def fw_make_monthly_chart(frame: pd.DataFrame) -> go.Figure:
    if frame.empty:
        return fw_empty()
    g = frame.groupby(["MonthNumber", "MonthName"], dropna=False).agg(
        EligibleFlights=("EligibleFlights", "sum"),
        DelayedFlights=("DelayedFlights", "sum"),
    ).reset_index().sort_values("MonthNumber")
    g["DelayRatePct"] = np.where(g["EligibleFlights"] > 0,
                                 g["DelayedFlights"] / g["EligibleFlights"] * 100.0, np.nan)
    if g["EligibleFlights"].sum() <= 0:
        return fw_empty("No eligible flight observations for the selected months.")
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=g["MonthName"], y=g["DelayRatePct"], mode="lines+markers", name="Weather-linked delay rate",
        line={"color": CYAN, "width": 3}, marker={"size": 8},
        customdata=g[["EligibleFlights", "DelayedFlights"]].to_numpy(),
        hovertemplate=("%{x}<br>Delay rate: %{y:.2f}%<br>Eligible: %{customdata[0]:,.0f}"
                       "<br>Delayed: %{customdata[1]:,.0f}<extra></extra>"),
    ))
    fig.update_layout(xaxis_title="Source month", yaxis_title="Delay rate among eligible flights (%)")
    return base_figure(fig, 350, legend=False)


def fw_airport_rollup(frame: pd.DataFrame) -> pd.DataFrame:
    """Vectorised airport roll-up (same maths as the former per-group loop, ~100x faster)."""
    if frame.empty:
        return pd.DataFrame()
    keys = ["AirportKey", "AirportCode", "AirportName", "Municipality", "ISOCountry", "AirportRole"]
    avg_cols = ["AvgTemperature", "AvgRelativeHumidity", "AvgPrecipitation", "AvgWindSpeed", "AvgWindGust", "AvgCloudCover"]
    work = frame[keys].copy()
    for col in ("MatchedExposureFlights", "EligibleFlights", "DelayedFlights"):
        work[col] = pd.to_numeric(frame[col], errors="coerce").fillna(0.0)
    weight = work["MatchedExposureFlights"].clip(lower=0)
    for col in avg_cols:
        values = pd.to_numeric(frame[col], errors="coerce")
        valid = values.notna() & weight.gt(0)
        work[f"_w_{col}"] = weight.where(valid, 0.0)
        work[f"_wv_{col}"] = (values.where(valid, 0.0)) * work[f"_w_{col}"]
    grouped = work.groupby(keys, dropna=False, sort=False).sum(numeric_only=True).reset_index()
    grouped["DelayRatePct"] = np.where(grouped["EligibleFlights"] > 0,
                                       grouped["DelayedFlights"] / grouped["EligibleFlights"].where(grouped["EligibleFlights"] > 0, 1) * 100.0,
                                       np.nan)
    for col in avg_cols:
        w = grouped[f"_w_{col}"]
        grouped[col] = np.where(w > 0, grouped[f"_wv_{col}"] / w.where(w > 0, 1), np.nan)
    return grouped[keys + ["MatchedExposureFlights", "EligibleFlights", "DelayedFlights", "DelayRatePct"] + avg_cols]


def fw_make_airport_scatter(frame: pd.DataFrame, airports: pd.DataFrame | None = None) -> go.Figure:
    airports = fw_airport_rollup(frame) if airports is None else airports
    airports = airports.dropna(subset=["AvgPrecipitation", "DelayRatePct"])
    airports = airports[airports["EligibleFlights"] > 0]
    if airports.empty:
        return fw_empty("Airport-level matched weather and eligible delay records are not available.")
    sizes = np.sqrt(airports["EligibleFlights"].clip(lower=0))
    sizes = (sizes / max(float(sizes.max()), 1.0) * 34 + 8).tolist()
    fig = go.Figure(go.Scatter(
        x=airports["AvgPrecipitation"], y=airports["DelayRatePct"], mode="markers",
        marker={"size": sizes, "color": airports["AvgWindSpeed"],
                "colorscale": [[0, GREEN], [.5, BLUE], [1, RED]], "showscale": True,
                "colorbar": {"title": "Avg wind<br>(source unit)"}, "opacity": .82,
                "line": {"color": "rgba(255,255,255,.25)", "width": .7}},
        text=airports["AirportCode"],
        customdata=airports[["AirportName", "ISOCountry", "EligibleFlights", "DelayedFlights", "MatchedExposureFlights"]].to_numpy(),
        hovertemplate=("%{text} · %{customdata[0]}<br>Country: %{customdata[1]}"
                       "<br>Avg precipitation: %{x:.3f} (source unit)<br>Delay rate: %{y:.2f}%"
                       "<br>Eligible: %{customdata[2]:,.0f}<br>Delayed: %{customdata[3]:,.0f}"
                       "<br>Matched exposure flights: %{customdata[4]:,.0f}<extra></extra>"),
    ))
    fig.update_layout(xaxis_title="Average precipitation at matched exposure (source unit)",
                      yaxis_title="Delay rate among eligible flights (%)")
    return base_figure(fig, 390, legend=False)


def fw_make_coverage_chart(coverage: pd.DataFrame) -> go.Figure:
    if coverage.empty:
        return fw_empty("Coverage export has not been loaded yet.")
    g = coverage.groupby("WeatherCoverageStatus", dropna=False)["BridgeExposureRows"].sum().sort_values(ascending=False)
    if g.empty:
        return fw_empty("No Bridge coverage statuses are available.")
    fig = go.Figure(go.Bar(
        x=g.index.astype(str), y=g.values,
        marker_color=[GREEN if "MATCHED" in str(x) else AMBER if "UNRESOLVED" in str(x) else BLUE for x in g.index],
        hovertemplate="%{x}<br>Bridge exposure rows: %{y:,.0f}<extra></extra>",
    ))
    fig.update_layout(xaxis_title="Bridge weather coverage status", yaxis_title="Exposure rows")
    return base_figure(fig, 330, legend=False)


def flight_weather_page() -> html.Div:
    impact = DATA.get("flight_weather_impact", pd.DataFrame())
    coverage = DATA.get("flight_weather_coverage", pd.DataFrame())
    countries = sorted(impact["ISOCountry"].dropna().astype(str).unique().tolist()) if not impact.empty else []
    has_snapshot = not impact.empty and not coverage.empty
    months = fw_available_months()
    scope = fw_scope_label()
    integrity = FW_MANIFEST.get("_integrity") if FW_MANIFEST else None
    if not has_snapshot:
        status_text = ("The joined analysis snapshot is not installed yet. Run 06_FW_TOOLS/fw_extract.py "
                       "(verify → run → merge) and fw_validate.py, which write both CSVs to 03_EXPORT_DATA.")
    elif integrity and integrity != "OK":
        status_text = f"Snapshot loaded, but integrity check failed: {integrity}. Re-run fw_extract.py merge and fw_validate.py."
    elif not FW_MANIFEST:
        status_text = f"Snapshot loaded ({scope}) without a manifest — provenance cannot be confirmed."
    else:
        status_text = (f"Validated snapshot loaded · scope {scope} · BridgeRunID {FW_MANIFEST.get('BridgeRunID', '—')} "
                       f"· exported {FW_MANIFEST.get('GeneratedAtUTC', '—')}.")
    return html.Div([
        html.Div([
            html.Div([html.Div("RELATIONAL ANALYTICS · FLIGHT DW 2025", className="fw-hero-kicker"),
                      html.H2("Flight × Weather Impact", className="fw-hero-title"),
                      html.P("Trace each flight exposure to the airport and the hourly weather observation, then compare eligible delay rates across rain and wind conditions.", className="fw-hero-copy")]),
            html.Div([html.Div("RELATIONSHIP", className="fw-hero-chip-label"),
                      html.Div("FACT_FLIGHT  →  BRIDGE  →  WEATHER FACT", className="fw-hero-chip-main"),
                      html.Div("Bridge AirportKey → dim_airport · WeatherKey → hourly weather", className="fw-hero-chip-note")]),
        ], className="fw-hero"),
        html.Div(status_text, className="fw-status-banner"),
        html.Div([
            html.Div([html.Div("EXPOSURE EVENT", className="filter-label"), dcc.Dropdown(
                id="fw-exposure-type", options=FW_EXPOSURE_OPTIONS, value="SCHEDULED_DEPARTURE",
                clearable=False, className="dark-dropdown")]),
            html.Div([html.Div("SOURCE MONTH", className="filter-label"), dcc.Dropdown(
                id="fw-month", options=[{"label": "All available months", "value": "ALL"}] +
                [{"label": f"{m} · {FW_MONTH_NAMES[m]}", "value": m} for m in months],
                value="ALL", clearable=False, className="dark-dropdown")]),
            html.Div([html.Div("AIRPORT COUNTRY", className="filter-label"), dcc.Dropdown(
                id="fw-country", options=[{"label": c, "value": c} for c in countries],
                value=countries, multi=True, placeholder="All countries", className="dark-dropdown")]),
            html.Div([html.Div("FIND AIRPORT", className="filter-label"), dcc.Input(
                id="fw-airport-search", type="text", placeholder="Airport code, name or city",
                debounce=True, className="dark-input")]),
        ], className="filter-bar filter-grid-4 fw-filter-bar"),
        html.Div(id="fw-kpis"),
        html.Div(id="fw-insights", className="insight-grid"),
        html.Div([
            panel("Delay rate by precipitation", "Weighted delayed / eligible flights · buckets use stored source units", graph("fw-rain-delay", height=350)),
            panel("Delay rate by wind speed", "Weighted delayed / eligible flights · compare exposure-hour wind bands", graph("fw-wind-delay", height=350)),
        ], className="content-grid main-grid"),
        html.Div([
            panel("Weather-linked delay trend", "Monthly weighted delay rate for the selected exposure type and airport scope", graph("fw-monthly-trend", height=350)),
            panel("Airport conditions vs delay rate", "Each bubble is one airport; size = eligible flights, colour = average wind speed", graph("fw-airport-scatter", height=390)),
        ], className="content-grid main-grid"),
        html.Div([
            panel("Bridge weather-match coverage", "All Bridge statuses for the selected exposure event and airport filters", graph("fw-coverage-status", height=330)),
            panel("Coverage status detail", "Status reconciliation from Bridge_Flight_Weather_Exposure", html.Div(id="fw-coverage-table")),
        ], className="content-grid"),
        panel("Airport-level Flight × Weather detail", "Weighted delay metrics by airport under the selected filters", html.Div(id="fw-airport-table")),
        html.Div([
            html.Strong("JOIN & METHOD"),
            html.Span(" FlightKey joins Fact_Flight to Bridge. Bridge AirportKey + OurAirportsID joins dim_airport; Bridge WeatherKey joins Fact_Airport_Weather_Hourly, with OurAirportsID + WeatherHourUTC checked again. Departure exposures are validated against OriginAirportKey; arrival exposures against DestinationAirportKey. Departure eligibility follows Gold logic: Cancelled = 0 and DepDel15 is not NULL. Arrival eligibility additionally requires Diverted = 0 and ArrDel15 is not NULL. Delay rates are weighted delayed / eligible, never an unweighted average of airport percentages. Scheduled exposures are the primary association view; actual exposures describe conditions at actual event time and are not causal evidence."),
        ], className="fw-method-banner"),
        html.Div(f"Scope: {scope} only · verified Bridge partitions (SourceMonth × ExposureType) listed in "
                 f"{FLIGHT_WEATHER_MANIFEST_FILE} · matched rows only for weather-condition analysis · "
                 "counts are exposure events; do not add them across exposure types.", className="fw-scope-line"),
    ], className="flight-weather-page")


# -------------------------------- DASH APP ----------------------------------
app = Dash(__name__, title="AERO INSIGHTS | Flight DW 2025", assets_folder=str(ASSETS_DIR), suppress_callback_exceptions=True)
app.layout = html.Div([
    dcc.Location(id="url", refresh=False),
    html.Div(id="shell", children=[
        sidebar("/"), html.Main([html.Div(id="page-content", className="page-content")], className="main-content")
    ], className="app-shell"),
], className="app-root")

# WSGI entry point for production servers: gunicorn --chdir 02_PYTHON_SOURCE app:server
server = app.server


@server.route("/health")
def health():
    """Liveness/readiness probe for the hosting platform. Reports data status, never secrets."""
    from flask import jsonify
    impact = DATA.get("flight_weather_impact", pd.DataFrame())
    coverage = DATA.get("flight_weather_coverage", pd.DataFrame())
    return jsonify({
        "status": "ok",
        "gold_tables": {key: int(len(DATA[key])) for key in FILES},
        "flight_weather": {
            "impact_rows": int(len(impact)),
            "coverage_rows": int(len(coverage)),
            "scope": fw_scope_label(),
            "manifest_integrity": FW_MANIFEST.get("_integrity") if FW_MANIFEST else "no manifest",
        },
    })


@app.callback(
    Output("nav-overview", "className"), Output("nav-airlines", "className"),
    Output("nav-airports", "className"), Output("nav-time", "className"),
    Output("nav-weather", "className"), Output("nav-flight-weather", "className"),
    Input("url", "pathname"),
)
def update_navigation(pathname: str | None) -> tuple[str, str, str, str, str, str]:
    path = pathname or "/"
    paths = ["/", "/airlines", "/airports", "/time", "/weather", "/flight-weather"]
    return tuple("nav-link active" if path == p else "nav-link" for p in paths)


@app.callback(Output("page-content", "children"), Input("url", "pathname"))
def render_page(pathname: str | None) -> html.Div:
    path = pathname or "/"
    meta_note = "BTS reporting carrier scope"
    if path == "/airlines":
        title, subtitle, page = "Airline intelligence", "Carrier scale, reliability, disruption profile and month-by-month performance.", airline_page()
    elif path == "/airports":
        title, subtitle, page = "Airport intelligence", "Compare annual airport-role activity, delay exposure and positive-delay burden.", airport_page()
    elif path == "/time":
        title, subtitle, page = "Time intelligence", "Identify operating-hour patterns without collapsing the 24:00 end-of-day sentinel.", time_page()
    elif path == "/weather":
        title, subtitle, page = "Weather intelligence", "Full-year hourly weather patterns across 352 airports, with a separate and explicitly scoped flight-exposure preview.", weather_page()
        meta_note = "Open-Meteo hourly snapshot · 352 airports"
    elif path == "/flight-weather":
        title, subtitle, page = "Flight × Weather impact", "Relational analysis across Flight, Airport and hourly Weather facts using the validated exposure Bridge.", flight_weather_page()
        meta_note = f"Bridge-linked Flight × Airport × Weather · {fw_scope_label()}"
    else:
        title, subtitle, page = "Flight operations overview", "A high-level view of U.S. flight activity, delay patterns and operational disruptions in 2025.", overview_page()
    return html.Div([header(title, subtitle, meta_note), page])


# Airline tab: selected carriers, threshold and metric drive all views.
@app.callback(
    Output("airline-kpis", "children"), Output("airline-insights", "children"),
    Output("airline-ranking", "figure"), Output("airline-rate-compare", "figure"),
    Output("airline-monthly", "figure"), Output("airline-disruptions", "figure"),
    Output("airline-bubble", "figure"), Output("airline-monthly-volume", "figure"),
    Output("airline-heatmap-dep", "figure"), Output("airline-heatmap-arr", "figure"),
    Output("airline-table-wrap", "children"),
    Input("airline-select", "value"), Input("airline-metric", "value"), Input("airline-min-flights", "value"),
)
def update_airline_charts(selected: list[str] | None, metric: str, min_flights: int | None):
    all_frame = DATA["airline"].copy()
    frame = all_frame[all_frame["ReportingAirlineCode"].astype(str).isin(selected or [])].copy()
    min_flights = float(min_flights or 0)
    frame = frame[pd.to_numeric(frame["TotalFlights"], errors="coerce").fillna(0) >= min_flights].copy()
    monthly = DATA["monthly_airline"].copy()
    monthly = monthly[monthly["ReportingAirlineCode"].astype(str).isin(frame["ReportingAirlineCode"].astype(str).tolist())].copy()
    if frame.empty:
        empty = empty_figure("Choose airlines and/or reduce the minimum volume threshold")
        # 11 outputs: kpis, insights, 8 figures, table. (v2 returned only 7 figures here -> HTTP 500 when all airlines were cleared.)
        return html.Div("No airline records match these filters.", className="empty-state"), [], empty, empty, empty, empty, empty, empty, empty, empty, html.Div("No records.", className="empty-state")

    frame["CancellationRatePct"] = frame.apply(lambda r: rate_from_counts(r.get("CancelledFlights"), r.get("TotalFlights")), axis=1)
    dep_rate = weighted_rate(frame, "DelayedDepartureFlights", "EligibleDepartureFlights")
    arr_rate = weighted_rate(frame, "DelayedArrivalFlights", "EligibleArrivalFlights")
    total_flights = sum_col(frame, "TotalFlights")
    total_scope = sum_col(all_frame, "TotalFlights")
    share = total_flights / total_scope * 100 if total_scope > 0 else np.nan
    cards = kpi_grid([
        kpi_card("SELECTED CARRIERS", fmt_int(frame["ReportingAirlineCode"].nunique()), "After selected filters", CYAN, "✈"),
        kpi_card("SELECTED FLIGHTS", fmt_int(total_flights), f"{fmt_pct(share)} of annual carrier-scope volume", BLUE, "▰"),
        kpi_card("WEIGHTED DEP. DELAY", fmt_pct(dep_rate), f"{fmt_int(sum_col(frame, 'DelayedDepartureFlights'))} / {fmt_int(sum_col(frame, 'EligibleDepartureFlights'))} eligible", AMBER, "↗"),
        kpi_card("WEIGHTED ARR. DELAY", fmt_pct(arr_rate), f"{fmt_int(sum_col(frame, 'DelayedArrivalFlights'))} / {fmt_int(sum_col(frame, 'EligibleArrivalFlights'))} eligible", RED, "◷"),
        kpi_card("CANCELLED", fmt_int(sum_col(frame, "CancelledFlights")), f"{fmt_pct(rate_from_counts(sum_col(frame, 'CancelledFlights'), total_flights))} of selected flights", RED, "×"),
        kpi_card("DIVERTED", fmt_int(sum_col(frame, "DivertedFlights")), f"{fmt_pct(rate_from_counts(sum_col(frame, 'DivertedFlights'), total_flights))} of selected flights", VIOLET, "⇢"),
        kpi_card("DELAYED DEPARTURES", fmt_int(sum_col(frame, "DelayedDepartureFlights")), "Across selected carriers", AMBER, "↗"),
        kpi_card("DELAYED ARRIVALS", fmt_int(sum_col(frame, "DelayedArrivalFlights")), "Across selected carriers", BLUE, "◷"),
    ], "kpi-grid-4")

    metric = metric if metric in frame.columns or metric == "CancellationRatePct" else "DepartureDelayRatePct"
    if metric == "CancellationRatePct" and metric not in frame.columns:
        frame[metric] = frame.apply(lambda r: rate_from_counts(r.get("CancelledFlights"), r.get("TotalFlights")), axis=1)
    rank = make_airline_rank(frame, metric)
    compare = make_airline_rate_compare(frame)
    trend = make_airline_monthly(monthly)
    disruptions = make_airline_disruptions(frame)
    bubble = make_airline_bubble(frame)
    monthly_volume = make_airline_monthly_volume(monthly)
    heatmap_dep = make_airline_heatmap(monthly, "DepartureDelayRatePct")
    heatmap_arr = make_airline_heatmap(monthly, "ArrivalDelayRatePct")

    best = frame.sort_values("DepartureDelayRatePct", ascending=True).iloc[0]
    worst = frame.sort_values("DepartureDelayRatePct", ascending=False).iloc[0]
    most_delayed = frame.sort_values("DelayedDepartureFlights", ascending=False).iloc[0]
    insights = [
        insight_card("Lowest departure delay rate", str(best["ReportingAirlineCode"]), f"{fmt_pct(best['DepartureDelayRatePct'])} among {fmt_int(best['EligibleDepartureFlights'])} eligible departures.", GREEN),
        insight_card("Highest departure delay rate", str(worst["ReportingAirlineCode"]), f"{fmt_pct(worst['DepartureDelayRatePct'])} among {fmt_int(worst['EligibleDepartureFlights'])} eligible departures.", RED),
        insight_card("Largest delayed-departure count", str(most_delayed["ReportingAirlineCode"]), f"{fmt_int(most_delayed['DelayedDepartureFlights'])} delayed departures. A high count can reflect a larger operation, not only a higher rate.", AMBER),
    ]
    table_cols = [("ReportingAirlineCode", "Carrier"), ("IATAReportingAirlineCode", "IATA"), ("TotalFlights", "Total flights"),
                  ("CancelledFlights", "Cancelled"), ("DivertedFlights", "Diverted"), ("EligibleDepartureFlights", "Eligible dep."),
                  ("DelayedDepartureFlights", "Delayed dep."), ("DepartureDelayRatePct", "Dep. delay (%)"),
                  ("EligibleArrivalFlights", "Eligible arr."), ("DelayedArrivalFlights", "Delayed arr."),
                  ("ArrivalDelayRatePct", "Arr. delay (%)"), ("AvgSignedDepartureDelayMinutes", "Avg signed dep. min"),
                  ("AvgSignedArrivalDelayMinutes", "Avg signed arr. min")]
    table = make_table(frame.sort_values("DepartureDelayRatePct", ascending=False), table_cols, 14)
    return cards, insights, rank, compare, trend, disruptions, bubble, monthly_volume, heatmap_dep, heatmap_arr, table


# Airport tab: annual airport-role dataset only; no monthly/geospatial claims.
@app.callback(
    Output("airport-kpis", "children"), Output("airport-insights", "children"),
    Output("airport-ranking", "figure"), Output("airport-scatter", "figure"),
    Output("airport-role-compare", "figure"), Output("airport-histogram", "figure"),
    Output("airport-table-wrap", "children"),
    Input("airport-role", "value"), Input("airport-search", "value"),
    Input("airport-metric", "value"), Input("airport-min-eligible", "value"),
)
def update_airport_charts(role: str, search: str | None, metric: str, min_eligible: int | None):
    all_frame = DATA["airport"].copy()
    role_frame = all_frame.copy()
    if role and role != "ALL":
        role_frame = role_frame[role_frame["AirportRole"].astype(str) == role]
    if search and search.strip():
        q = search.strip().lower()
        cols = [c for c in ["IATACode", "Ident", "AirportName", "Municipality", "ISOCountry"] if c in role_frame.columns]
        mask = pd.Series(False, index=role_frame.index)
        for col in cols:
            mask |= role_frame[col].fillna("").astype(str).str.lower().str.contains(q, regex=False)
        role_frame = role_frame[mask]
    threshold_frame = role_frame[pd.to_numeric(role_frame["EligibleFlights"], errors="coerce").fillna(0) >= float(min_eligible or 0)].copy()
    if threshold_frame.empty:
        empty = empty_figure("No airport-role records match these filters")
        return html.Div("No records match. Reduce the minimum eligible-flight threshold or clear search.", className="empty-state"), [], empty, empty, empty, empty, html.Div("No records.", className="empty-state")

    frame = threshold_frame
    total_scheduled = sum_col(frame, "ScheduledFlights")
    eligible = sum_col(frame, "EligibleFlights")
    delayed = sum_col(frame, "DelayedFlights")
    delay_rate = weighted_rate(frame, "DelayedFlights", "EligibleFlights")
    positive_burden = sum_col(frame, "TotalPositiveDelayMinutes")
    cards = kpi_grid([
        kpi_card("AIRPORT-ROLE RECORDS", fmt_int(len(frame)), "One row per airport and operating role", CYAN, "⌖"),
        kpi_card("SCHEDULED FLIGHTS", fmt_int(total_scheduled), "Within current role/search/threshold", BLUE, "✈"),
        kpi_card("ELIGIBLE FLIGHTS", fmt_int(eligible), "Delay-rate denominator", CYAN, "✓"),
        kpi_card("WEIGHTED DELAY RATE", fmt_pct(delay_rate), f"{fmt_int(delayed)} delayed / {fmt_int(eligible)} eligible", AMBER, "↗"),
        kpi_card("POSITIVE DELAY BURDEN", fmt_int(positive_burden), "Sum of positive delay minutes", RED, "◷"),
        kpi_card("AIRPORTS", fmt_int(frame["AirportKey"].nunique()), "Distinct airport keys in filtered view", VIOLET, "⌖"),
        kpi_card("AVERAGE SIGNED DELAY", fmt_min(frame["AvgSignedDelayMinutes"].mean()), "Unweighted mean of airport-role averages", GREEN, "±"),
        kpi_card("FILTERED ROLE(S)", fmt_int(frame["AirportRole"].nunique()), ", ".join(sorted(frame["AirportRole"].dropna().unique().tolist())), BLUE, "⇄"),
    ], "kpi-grid-4")

    rank_metric = metric if metric in frame.columns else "DelayRatePct"
    ranking = make_airport_rank(frame, rank_metric)
    scatter = make_airport_scatter(frame)
    role_compare = make_airport_role_compare(frame)
    hist = make_airport_histogram(frame)

    worst = frame.sort_values("DelayRatePct", ascending=False).iloc[0]
    burden = frame.sort_values("TotalPositiveDelayMinutes", ascending=False).iloc[0]
    role_rows = []
    for role_name, group in frame.groupby("AirportRole", dropna=False):
        role_rows.append({
            "AirportRole": str(role_name),
            "rate": weighted_rate(group, "DelayedFlights", "EligibleFlights"),
            "eligible": sum_col(group, "EligibleFlights"),
        })
    role_summary = pd.DataFrame(role_rows).set_index("AirportRole") if role_rows else pd.DataFrame()
    role_text = "; ".join(f"{r}: {fmt_pct(row['rate'])} (eligible {fmt_int(row['eligible'])})" for r, row in role_summary.iterrows()) if not role_summary.empty else "No role summary available."
    insights = [
        insight_card("Highest delay-rate record", f"{worst.get('IATACode') if pd.notna(worst.get('IATACode')) else worst.get('Ident')} · {worst['AirportRole']}", f"{fmt_pct(worst['DelayRatePct'])} from {fmt_int(worst['EligibleFlights'])} eligible flights. Interpret alongside the minimum-volume filter.", RED),
        insight_card("Largest positive-delay burden", f"{burden.get('IATACode') if pd.notna(burden.get('IATACode')) else burden.get('Ident')} · {burden['AirportRole']}", f"{fmt_int(burden['TotalPositiveDelayMinutes'])} accumulated positive delay minutes in this airport-role aggregate.", AMBER),
        insight_card("Role-level weighted rates", "Origin / Destination comparison", role_text or "No role summary available.", CYAN),
    ]
    table_cols = [("IATACode", "IATA"), ("Ident", "Airport ident"), ("AirportName", "Airport"),
                  ("Municipality", "Municipality"), ("ISOCountry", "Country"), ("AirportRole", "Role"),
                  ("ScheduledFlights", "Scheduled flights"), ("EligibleFlights", "Eligible flights"),
                  ("DelayedFlights", "Delayed flights"), ("DelayRatePct", "Delay rate (%)"),
                  ("AvgSignedDelayMinutes", "Avg signed delay (min)"), ("TotalPositiveDelayMinutes", "Positive delay (min)")]
    table = make_table(frame.sort_values("DelayRatePct", ascending=False), table_cols, 15)
    return cards, insights, ranking, scatter, role_compare, hist, table


# Time tab: hourly aggregates; 24:00 is kept distinct from 00:00.
@app.callback(
    Output("time-kpis", "children"), Output("time-insights", "children"),
    Output("hour-volume-rate", "figure"), Output("hour-delay-burden", "figure"),
    Output("hour-scatter", "figure"), Output("hour-table-wrap", "children"),
    Input("hour-scope", "value"), Input("hour-min-eligible", "value"),
)
def update_time_charts(scope: str, min_eligible: int | None):
    all_hours = DATA["hour"].copy()
    frame = all_hours.copy()
    if scope == "KNOWN":
        frame = frame[~frame["ScheduledDepartureHourLabel"].fillna("Unknown").astype(str).str.lower().eq("unknown")].copy()
    frame = ordered_hours(frame)
    if frame.empty:
        empty = empty_figure("No hourly records match this scope")
        return html.Div("No hourly data.", className="empty-state"), [], empty, empty, empty, html.Div("No records.", className="empty-state")

    scheduled = sum_col(frame, "ScheduledFlights")
    eligible = sum_col(frame, "EligibleDepartureFlights")
    delayed = sum_col(frame, "DelayedDepartureFlights")
    rate = weighted_rate(frame, "DelayedDepartureFlights", "EligibleDepartureFlights")
    candidates = frame[pd.to_numeric(frame["EligibleDepartureFlights"], errors="coerce").fillna(0) >= float(min_eligible or 0)].dropna(subset=["DepartureDelayRatePct"])
    if candidates.empty:
        candidates = frame.dropna(subset=["DepartureDelayRatePct"])
    peak_volume = frame.sort_values("ScheduledFlights", ascending=False).iloc[0]
    peak_delay = candidates.sort_values("DepartureDelayRatePct", ascending=False).iloc[0] if not candidates.empty else None
    lowest_delay = candidates.sort_values("DepartureDelayRatePct", ascending=True).iloc[0] if not candidates.empty else None
    cards = kpi_grid([
        kpi_card("SCHEDULED FLIGHTS", fmt_int(scheduled), "Across visible hour buckets", BLUE, "✈"),
        kpi_card("WEIGHTED DELAY RATE", fmt_pct(rate), f"{fmt_int(delayed)} delayed / {fmt_int(eligible)} eligible", AMBER, "↗"),
        kpi_card("HIGHEST-VOLUME HOUR", str(peak_volume["ScheduledDepartureHourLabel"]), f"{fmt_int(peak_volume['ScheduledFlights'])} scheduled flights", CYAN, "◷"),
        kpi_card("HOURS / BUCKETS", fmt_int(len(frame)), "Includes 24:00 when present", VIOLET, "▦"),
    ], "kpi-grid-4")
    insights: list[html.Div] = [insight_card("Peak scheduled volume", str(peak_volume["ScheduledDepartureHourLabel"]), f"{fmt_int(peak_volume['ScheduledFlights'])} scheduled flights in this hour bucket.", BLUE)]
    if peak_delay is not None:
        insights.append(insight_card("Highest delay-rate hour", str(peak_delay["ScheduledDepartureHourLabel"]), f"{fmt_pct(peak_delay['DepartureDelayRatePct'])} across {fmt_int(peak_delay['EligibleDepartureFlights'])} eligible departures; threshold {fmt_int(min_eligible or 0)}.", RED))
    if lowest_delay is not None:
        insights.append(insight_card("Lowest delay-rate hour", str(lowest_delay["ScheduledDepartureHourLabel"]), f"{fmt_pct(lowest_delay['DepartureDelayRatePct'])} across {fmt_int(lowest_delay['EligibleDepartureFlights'])} eligible departures.", GREEN))
    insights.append(insight_card("Interpretation", "Association, not causation", "The hourly profile identifies when delays are more frequent in this dataset. It does not by itself establish why those delays occur.", AMBER))

    table_cols = [("ScheduledDepartureHourLabel", "Scheduled hour"), ("IsEndOfDay", "24:00 sentinel"),
                  ("ScheduledFlights", "Scheduled flights"), ("EligibleDepartureFlights", "Eligible departures"),
                  ("DelayedDepartureFlights", "Delayed departures"), ("DepartureDelayRatePct", "Delay rate (%)"),
                  ("AvgSignedDepartureDelayMinutes", "Avg signed delay (min)")]
    table = make_table(frame, table_cols, 30)
    return cards, insights, make_hour_volume_rate(frame), make_hour_delay_burden(frame), make_hour_scatter(frame), table


# Weather tab: full-year Weather Fact snapshots; country, metric and text filters are client-side.
@app.callback(
    Output("weather-airport-ranking", "figure"),
    Output("weather-airport-scatter", "figure"),
    Output("weather-airport-table", "children"),
    Input("weather-country", "value"),
    Input("weather-metric", "value"),
    Input("weather-search", "value"),
)
def update_weather_charts(countries: list[str] | None, metric: str, search: str | None):
    frame = DATA["weather_airport"].copy()
    if countries is not None:
        frame = frame[frame["ISOCountry"].astype(str).isin(countries)].copy()
    if search and search.strip():
        q = search.strip().lower()
        cols = ["AirportCode", "AirportName", "Municipality", "ISOCountry"]
        mask = pd.Series(False, index=frame.index)
        for col in cols:
            mask |= frame[col].fillna("").astype(str).str.lower().str.contains(q, regex=False)
        frame = frame[mask].copy()
    allowed_metrics = {"TotalPrecipitation", "WetAirportHourRate", "AvgTemperature", "AvgRelativeHumidity",
                       "AvgWindSpeed", "MaxWindGust", "AvgCloudCover"}
    rank_metric = metric if metric in allowed_metrics else "TotalPrecipitation"
    if frame.empty:
        empty = empty_figure("No airport weather records match these filters")
        return empty, empty, html.Div("No airport records match the selected filters.", className="empty-state")
    ranking = make_weather_airport_rank(frame, rank_metric)
    scatter = make_weather_airport_scatter(frame)
    table_cols = [
        ("AirportCode", "Code"), ("AirportName", "Airport"), ("Municipality", "Municipality"),
        ("ISOCountry", "Country"), ("AirportType", "Airport type"),
        ("WeatherObservations", "Observations"), ("AvgTemperature", "Avg temperature"),
        ("AvgRelativeHumidity", "Avg humidity (%)"), ("TotalPrecipitation", "Total precipitation"),
        ("WetAirportHourRate", "Wet airport-hours (%)"), ("AvgWindSpeed", "Avg wind speed"),
        ("MaxWindGust", "Max wind gust"), ("AvgCloudCover", "Avg cloud cover (%)"),
    ]
    table = make_table(frame.sort_values(rank_metric, ascending=False), table_cols, 15)
    return ranking, scatter, table


@app.callback(
    Output("weather-airport-spotlight", "children"),
    Input("weather-airport-select", "value"),
)
def update_weather_airport_spotlight(code: str | None):
    return weather_spotlight_content(code)


# Flight × Weather: all charts are computed from the joined SQL snapshot.
@app.callback(
    Output("fw-kpis", "children"), Output("fw-insights", "children"),
    Output("fw-rain-delay", "figure"), Output("fw-wind-delay", "figure"),
    Output("fw-monthly-trend", "figure"), Output("fw-airport-scatter", "figure"),
    Output("fw-coverage-status", "figure"), Output("fw-coverage-table", "children"),
    Output("fw-airport-table", "children"),
    Input("fw-exposure-type", "value"), Input("fw-month", "value"),
    Input("fw-country", "value"), Input("fw-airport-search", "value"),
)
def update_flight_weather_charts(exposure_type: str, month: str, countries: list[str] | None, search: str | None):
    impact_all = DATA.get("flight_weather_impact", pd.DataFrame()).copy()
    coverage_all = DATA.get("flight_weather_coverage", pd.DataFrame()).copy()
    empty = fw_empty()
    if impact_all.empty or coverage_all.empty:
        cards = kpi_grid([
            kpi_card("MATCHED EXPOSURES", "—", "Awaiting joined SQL snapshot", CYAN, "⇄"),
            kpi_card("ELIGIBLE FLIGHTS", "—", "Gold eligibility rules", BLUE, "✓"),
            kpi_card("DELAY RATE", "—", "Requires matched Flight × Weather rows", AMBER, "↗"),
            kpi_card("WEATHER MATCH COVERAGE", "—", "Requires Bridge status export", GREEN, "☁"),
        ], "kpi-grid-4")
        return cards, [insight_card("Snapshot required", "Relational data not loaded yet", "Run 06_FW_TOOLS/fw_extract.py (verify → run → merge), then fw_validate.py. Both CSVs and the manifest are written to 03_EXPORT_DATA.", AMBER)], empty, empty, empty, empty, empty, html.Div("No coverage snapshot loaded.", className="empty-state"), html.Div("No joined impact snapshot loaded.", className="empty-state")

    exposure_type = exposure_type if exposure_type in FW_EXPOSURE_LABELS else "SCHEDULED_DEPARTURE"
    impact = impact_all[impact_all["ExposureType"].astype(str) == exposure_type].copy()
    coverage = coverage_all[coverage_all["ExposureType"].astype(str) == exposure_type].copy()
    if month and month != "ALL":
        impact = impact[impact["SourceMonth"].astype(str) == str(month)]
        coverage = coverage[coverage["SourceMonth"].astype(str) == str(month)]
    if countries:  # None or [] (cleared dropdown) both mean "all countries"
        impact = impact[impact["ISOCountry"].astype(str).isin(countries)]
        coverage = coverage[coverage["ISOCountry"].astype(str).isin(countries)]
    if search and search.strip():
        q = search.strip().lower()
        for frame_name, frame in (("impact", impact), ("coverage", coverage)):
            cols = [c for c in ("AirportCode", "AirportName", "Municipality") if c in frame.columns]
            mask = pd.Series(False, index=frame.index)
            for col in cols:
                mask |= frame[col].fillna("").astype(str).str.lower().str.contains(q, regex=False)
            if frame_name == "impact":
                impact = frame[mask].copy()
            else:
                coverage = frame[mask].copy()

    matched_rows = float(pd.to_numeric(impact.get("MatchedExposureRows", pd.Series(dtype=float)), errors="coerce").fillna(0).sum())
    matched_exposures = float(pd.to_numeric(impact.get("MatchedExposureFlights", pd.Series(dtype=float)), errors="coerce").fillna(0).sum())
    eligible = float(pd.to_numeric(impact.get("EligibleFlights", pd.Series(dtype=float)), errors="coerce").fillna(0).sum())
    delayed = float(pd.to_numeric(impact.get("DelayedFlights", pd.Series(dtype=float)), errors="coerce").fillna(0).sum())
    rate = delayed / eligible * 100.0 if eligible > 0 else np.nan
    total_bridge = float(pd.to_numeric(coverage.get("BridgeExposureRows", pd.Series(dtype=float)), errors="coerce").fillna(0).sum())
    # Coverage numerator and denominator both come from the Bridge status export (same filters),
    # so rows excluded from the impact dataset can never silently inflate or deflate coverage.
    coverage_matched = float(pd.to_numeric(
        coverage.loc[coverage["WeatherCoverageStatus"].astype(str) == "MATCHED_WEATHER_HOUR", "BridgeExposureRows"],
        errors="coerce").fillna(0).sum()) if not coverage.empty else 0.0
    coverage_pct = coverage_matched / total_bridge * 100.0 if total_bridge > 0 else np.nan
    airport_count = int(impact["AirportKey"].nunique()) if not impact.empty else 0
    cards = kpi_grid([
        kpi_card("MATCHED EXPOSURE EVENTS", fmt_int(matched_exposures), f"{fmt_int(matched_rows)} matched Bridge rows", CYAN, "⇄"),
        kpi_card("ELIGIBLE FLIGHTS", fmt_int(eligible), "After cancellation / diversion / delay-flag rules", BLUE, "✓"),
        kpi_card("WEATHER-LINKED DELAY RATE", fmt_pct(rate), f"{fmt_int(delayed)} delayed / {fmt_int(eligible)} eligible", AMBER, "↗"),
        kpi_card("WEATHER MATCH COVERAGE", fmt_pct(coverage_pct), f"{fmt_int(coverage_matched)} matched / {fmt_int(total_bridge)} Bridge rows", GREEN, "☁"),
        kpi_card("AIRPORTS IN VIEW", fmt_int(airport_count), "AirportKey matched through dim_airport", VIOLET, "⌖"),
    ], "kpi-grid-4")

    airport_rollup = fw_airport_rollup(impact)
    insights = []
    rain = fw_band_summary(impact, "PrecipitationBand", "PrecipitationBandSort")
    if not rain.empty:
        dry = rain[rain["PrecipitationBand"].astype(str).str.startswith("Dry")]
        wet = rain[~rain["PrecipitationBand"].astype(str).str.startswith("Dry")]
        if not dry.empty and not wet.empty and dry.iloc[0]["EligibleFlights"] > 0 and wet["EligibleFlights"].sum() > 0:
            wet_rate = wet["DelayedFlights"].sum() / wet["EligibleFlights"].sum() * 100.0
            dry_rate = dry.iloc[0]["DelayRatePct"]
            diff = wet_rate - dry_rate
            insights.append(insight_card(
                "Rain association", f"Wet vs dry: {diff:+.2f} percentage points",
                f"Wet conditions: {wet_rate:.2f}% across {fmt_int(wet['EligibleFlights'].sum())} eligible flights; dry: {dry_rate:.2f}% across {fmt_int(dry.iloc[0]['EligibleFlights'])}. Descriptive association only.",
                RED if diff > 0 else GREEN,
            ))
    if not impact.empty:
        top_airport = airport_rollup.sort_values("DelayRatePct", ascending=False).head(1)
        if not top_airport.empty and pd.notna(top_airport.iloc[0]["DelayRatePct"]):
            r = top_airport.iloc[0]
            insights.append(insight_card(
                "Highest airport rate in current view", f"{r['AirportCode']} · {r['AirportName']}",
                f"{fmt_pct(r['DelayRatePct'])} from {fmt_int(r['EligibleFlights'])} eligible flights. Interpret with its sample size.", RED,
            ))
    if not insights:
        insights.append(insight_card("Interpretation", "No eligible matched delay observations", "Change the exposure event, month or airport filter to inspect another subset.", AMBER))

    rain_fig = fw_make_band_chart(impact, "PrecipitationBand", "PrecipitationBandSort", "Precipitation band · source unit")
    wind_fig = fw_make_band_chart(impact, "WindSpeedBand", "WindSpeedBandSort", "Wind speed band · source unit")
    month_fig = fw_make_monthly_chart(impact)
    scatter_fig = fw_make_airport_scatter(impact, airport_rollup)
    coverage_fig = fw_make_coverage_chart(coverage)

    status_cols = [("WeatherCoverageStatus", "Bridge coverage status"), ("BridgeExposureRows", "Exposure rows"),
                   ("NonNullWeatherKeys", "Non-null WeatherKey"), ("MatchedStatusMissingKeyRows", "Matched without key"),
                   ("NonMatchedStatusHasKeyRows", "Non-matched with key")]
    cov_table = make_table(
        coverage.groupby("WeatherCoverageStatus", dropna=False).agg(
            BridgeExposureRows=("BridgeExposureRows", "sum"),
            NonNullWeatherKeys=("NonNullWeatherKeys", "sum"),
            MatchedStatusMissingKeyRows=("MatchedStatusMissingKeyRows", "sum"),
            NonMatchedStatusHasKeyRows=("NonMatchedStatusHasKeyRows", "sum"),
        ).reset_index().sort_values("BridgeExposureRows", ascending=False), status_cols, 10
    ) if not coverage.empty else html.Div("No coverage rows match the current filters.", className="empty-state")

    airport_cols = [("AirportCode", "Code"), ("AirportName", "Airport"), ("Municipality", "Municipality"),
                    ("ISOCountry", "Country"), ("AirportRole", "Role"),
                    ("MatchedExposureFlights", "Matched exposures"), ("EligibleFlights", "Eligible flights"),
                    ("DelayedFlights", "Delayed flights"), ("DelayRatePct", "Delay rate (%)"),
                    ("AvgTemperature", "Avg temperature"), ("AvgPrecipitation", "Avg precipitation"),
                    ("AvgWindSpeed", "Avg wind speed"), ("AvgRelativeHumidity", "Avg humidity (%)")]
    airport_table = make_table(airport_rollup.sort_values("DelayRatePct", ascending=False).round({"DelayRatePct": 2, "AvgTemperature": 2, "AvgPrecipitation": 3, "AvgWindSpeed": 2, "AvgRelativeHumidity": 1}), airport_cols, 15) if not airport_rollup.empty else html.Div("No airport impact rows match the current filters.", className="empty-state")
    return cards, insights, rain_fig, wind_fig, month_fig, scatter_fig, coverage_fig, cov_table, airport_table


def main() -> None:
    print("\nAERO INSIGHTS | FLIGHT DW 2025 — ENHANCED ANALYTICS")
    print(f"Data directory: {DATA_DIR}")
    print("Gold + full-year Weather CSV snapshots loaded successfully.")
    print(f"Flight x Weather joined snapshot: {len(DATA.get('flight_weather_impact', pd.DataFrame())):,} rows loaded · scope: {fw_scope_label()}"
          f" · manifest: {FW_MANIFEST.get('_integrity') if FW_MANIFEST else 'not found'}")
    # Local default stays 127.0.0.1:8050. Hosting platforms set PORT (and HOST=0.0.0.0).
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8050"))
    print(f"Open http://{'127.0.0.1' if host in ('0.0.0.0', '127.0.0.1') else host}:{port} in your browser. Press Ctrl+C to stop.\n")
    app.run(host=host, port=port, debug=False)


if __name__ == "__main__":
    main()
