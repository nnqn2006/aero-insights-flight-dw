/* =============================================================================
   00_verify_bridge_status.sql — READ-ONLY verification of Bridge partitions
   Database: flight_dw_2025 · MySQL 8.0
   FlightKey ranges are copied from the STEP 30E3 checkpoint journal fingerprint
   (BridgeRunID 20261110_030433_504879). They are exact, not estimated.

   HOW TO RUN (MySQL Workbench):
     * Run ONE statement at a time (Ctrl+Enter with the cursor inside it).
     * Each statement scans only one month through the PRIMARY KEY; expect seconds
       to a few minutes each, never the 9-month join that timed out.
     * Preferred: the Python tool does all of this automatically:
         python 06_FW_TOOLS\fw_extract.py verify
   SELECT-only. Nothing is created, changed or deleted.
   ============================================================================= */
USE flight_dw_2025;
SET SESSION TRANSACTION READ ONLY;

/* Q0. Months 10–12 must be EMPTY (journal says not loaded). Expected: 0 */
SELECT COUNT(*) AS RowsMonth10to12
FROM bridge_flight_weather_exposure FORCE INDEX (PRIMARY)
WHERE FlightKey BETWEEN 5242922 AND 7001619;

/* Q01. Month 01: FlightKey 1..539,747 — expected 539,747 rows per ExposureType,
   MinFlightKey=1, MaxFlightKey=539747, WrongMonthRows=0, matched rows = NonNullWeatherKeys */
SELECT ExposureType, WeatherCoverageStatus,
       COUNT(*) AS BridgeRows, MIN(FlightKey) AS MinFlightKey, MAX(FlightKey) AS MaxFlightKey,
       SUM(SourceMonth <> '01') AS WrongMonthRows, SUM(SegmentSequence <> 1) AS NonSegment1Rows,
       SUM(WeatherKey IS NOT NULL) AS NonNullWeatherKeys
FROM bridge_flight_weather_exposure FORCE INDEX (PRIMARY)
WHERE FlightKey BETWEEN 1 AND 539747
GROUP BY ExposureType, WeatherCoverageStatus
ORDER BY ExposureType, WeatherCoverageStatus;

/* Q02. Month 02: FlightKey 539,748..1,044,631 — expected 504,884 rows per ExposureType,
   MinFlightKey=539748, MaxFlightKey=1044631, WrongMonthRows=0, matched rows = NonNullWeatherKeys */
SELECT ExposureType, WeatherCoverageStatus,
       COUNT(*) AS BridgeRows, MIN(FlightKey) AS MinFlightKey, MAX(FlightKey) AS MaxFlightKey,
       SUM(SourceMonth <> '02') AS WrongMonthRows, SUM(SegmentSequence <> 1) AS NonSegment1Rows,
       SUM(WeatherKey IS NOT NULL) AS NonNullWeatherKeys
FROM bridge_flight_weather_exposure FORCE INDEX (PRIMARY)
WHERE FlightKey BETWEEN 539748 AND 1044631
GROUP BY ExposureType, WeatherCoverageStatus
ORDER BY ExposureType, WeatherCoverageStatus;

/* Q03. Month 03: FlightKey 1,044,632..1,645,503 — expected 600,872 rows per ExposureType,
   MinFlightKey=1044632, MaxFlightKey=1645503, WrongMonthRows=0, matched rows = NonNullWeatherKeys */
SELECT ExposureType, WeatherCoverageStatus,
       COUNT(*) AS BridgeRows, MIN(FlightKey) AS MinFlightKey, MAX(FlightKey) AS MaxFlightKey,
       SUM(SourceMonth <> '03') AS WrongMonthRows, SUM(SegmentSequence <> 1) AS NonSegment1Rows,
       SUM(WeatherKey IS NOT NULL) AS NonNullWeatherKeys
FROM bridge_flight_weather_exposure FORCE INDEX (PRIMARY)
WHERE FlightKey BETWEEN 1044632 AND 1645503
GROUP BY ExposureType, WeatherCoverageStatus
ORDER BY ExposureType, WeatherCoverageStatus;

/* Q04. Month 04: FlightKey 1,645,504..2,229,453 — expected 583,950 rows per ExposureType,
   MinFlightKey=1645504, MaxFlightKey=2229453, WrongMonthRows=0, matched rows = NonNullWeatherKeys */
SELECT ExposureType, WeatherCoverageStatus,
       COUNT(*) AS BridgeRows, MIN(FlightKey) AS MinFlightKey, MAX(FlightKey) AS MaxFlightKey,
       SUM(SourceMonth <> '04') AS WrongMonthRows, SUM(SegmentSequence <> 1) AS NonSegment1Rows,
       SUM(WeatherKey IS NOT NULL) AS NonNullWeatherKeys
FROM bridge_flight_weather_exposure FORCE INDEX (PRIMARY)
WHERE FlightKey BETWEEN 1645504 AND 2229453
GROUP BY ExposureType, WeatherCoverageStatus
ORDER BY ExposureType, WeatherCoverageStatus;

/* Q05. Month 05: FlightKey 2,229,454..2,835,101 — expected 605,648 rows per ExposureType,
   MinFlightKey=2229454, MaxFlightKey=2835101, WrongMonthRows=0, matched rows = NonNullWeatherKeys */
SELECT ExposureType, WeatherCoverageStatus,
       COUNT(*) AS BridgeRows, MIN(FlightKey) AS MinFlightKey, MAX(FlightKey) AS MaxFlightKey,
       SUM(SourceMonth <> '05') AS WrongMonthRows, SUM(SegmentSequence <> 1) AS NonSegment1Rows,
       SUM(WeatherKey IS NOT NULL) AS NonNullWeatherKeys
FROM bridge_flight_weather_exposure FORCE INDEX (PRIMARY)
WHERE FlightKey BETWEEN 2229454 AND 2835101
GROUP BY ExposureType, WeatherCoverageStatus
ORDER BY ExposureType, WeatherCoverageStatus;

/* Q06. Month 06: FlightKey 2,835,102..3,446,676 — expected 611,575 rows per ExposureType,
   MinFlightKey=2835102, MaxFlightKey=3446676, WrongMonthRows=0, matched rows = NonNullWeatherKeys */
SELECT ExposureType, WeatherCoverageStatus,
       COUNT(*) AS BridgeRows, MIN(FlightKey) AS MinFlightKey, MAX(FlightKey) AS MaxFlightKey,
       SUM(SourceMonth <> '06') AS WrongMonthRows, SUM(SegmentSequence <> 1) AS NonSegment1Rows,
       SUM(WeatherKey IS NOT NULL) AS NonNullWeatherKeys
FROM bridge_flight_weather_exposure FORCE INDEX (PRIMARY)
WHERE FlightKey BETWEEN 2835102 AND 3446676
GROUP BY ExposureType, WeatherCoverageStatus
ORDER BY ExposureType, WeatherCoverageStatus;

/* Q07. Month 07: FlightKey 3,446,677..4,078,104 — expected 631,428 rows per ExposureType,
   MinFlightKey=3446677, MaxFlightKey=4078104, WrongMonthRows=0, matched rows = NonNullWeatherKeys */
SELECT ExposureType, WeatherCoverageStatus,
       COUNT(*) AS BridgeRows, MIN(FlightKey) AS MinFlightKey, MAX(FlightKey) AS MaxFlightKey,
       SUM(SourceMonth <> '07') AS WrongMonthRows, SUM(SegmentSequence <> 1) AS NonSegment1Rows,
       SUM(WeatherKey IS NOT NULL) AS NonNullWeatherKeys
FROM bridge_flight_weather_exposure FORCE INDEX (PRIMARY)
WHERE FlightKey BETWEEN 3446677 AND 4078104
GROUP BY ExposureType, WeatherCoverageStatus
ORDER BY ExposureType, WeatherCoverageStatus;

/* Q08. Month 08: FlightKey 4,078,105..4,680,482 — expected 602,378 rows per ExposureType,
   MinFlightKey=4078105, MaxFlightKey=4680482, WrongMonthRows=0, matched rows = NonNullWeatherKeys */
SELECT ExposureType, WeatherCoverageStatus,
       COUNT(*) AS BridgeRows, MIN(FlightKey) AS MinFlightKey, MAX(FlightKey) AS MaxFlightKey,
       SUM(SourceMonth <> '08') AS WrongMonthRows, SUM(SegmentSequence <> 1) AS NonSegment1Rows,
       SUM(WeatherKey IS NOT NULL) AS NonNullWeatherKeys
FROM bridge_flight_weather_exposure FORCE INDEX (PRIMARY)
WHERE FlightKey BETWEEN 4078105 AND 4680482
GROUP BY ExposureType, WeatherCoverageStatus
ORDER BY ExposureType, WeatherCoverageStatus;

/* Q09. Month 09: FlightKey 4,680,483..5,242,921 — expected 562,439 rows per ExposureType,
   MinFlightKey=4680483, MaxFlightKey=5242921, WrongMonthRows=0, matched rows = NonNullWeatherKeys */
SELECT ExposureType, WeatherCoverageStatus,
       COUNT(*) AS BridgeRows, MIN(FlightKey) AS MinFlightKey, MAX(FlightKey) AS MaxFlightKey,
       SUM(SourceMonth <> '09') AS WrongMonthRows, SUM(SegmentSequence <> 1) AS NonSegment1Rows,
       SUM(WeatherKey IS NOT NULL) AS NonNullWeatherKeys
FROM bridge_flight_weather_exposure FORCE INDEX (PRIMARY)
WHERE FlightKey BETWEEN 4680483 AND 5242921
GROUP BY ExposureType, WeatherCoverageStatus
ORDER BY ExposureType, WeatherCoverageStatus;
