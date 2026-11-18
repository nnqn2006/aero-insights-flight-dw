/* =============================================================================
   01_benchmark_september_actual_arrival.sql — READ-ONLY plan check + small benchmark
   Partition: SourceMonth 09 × ACTUAL_ARRIVAL · FlightKey 4,680,483..5,242,921
   Known evidence: 558,318 MATCHED_WEATHER_HOUR rows in this partition.
   SELECT / EXPLAIN only.
   ============================================================================= */
USE flight_dw_2025;
SET SESSION TRANSACTION READ ONLY;

/* B1. Plan for the first 100,000 flights of September.
   Expected: "Index range scan on b using PRIMARY" + "Single-row index lookup ... PRIMARY"
   for fact_flight (f) and fact_airport_weather_hourly (w). No "Table scan on b". */
EXPLAIN FORMAT=TREE
SELECT b.AirportKey, f.Cancelled, f.ArrDel15, w.Precipitation, w.WindSpeed10m
FROM bridge_flight_weather_exposure AS b FORCE INDEX (PRIMARY)
LEFT JOIN fact_flight AS f ON f.FlightKey = b.FlightKey
LEFT JOIN fact_airport_weather_hourly AS w ON w.WeatherKey = b.WeatherKey
WHERE b.FlightKey BETWEEN 4680483 AND 4780482
  AND b.ExposureType = 'ACTUAL_ARRIVAL'
  AND b.SegmentSequence = 1
  AND b.WeatherCoverageStatus = 'MATCHED_WEATHER_HOUR';

/* B2. Timed count for the same 100,000-flight chunk (look at Workbench "Duration").
   Multiply by ~5.6 to estimate one full September partition. */
SELECT /*+ MAX_EXECUTION_TIME(240000) */
       COUNT(*) AS MatchedRows,
       SUM(w.WeatherKey IS NULL) AS MissingWeather,
       SUM(f.FlightKey IS NULL) AS MissingFlight,
       SUM(b.AirportKey <> f.DestinationAirportKey) AS RoleMismatch
FROM bridge_flight_weather_exposure AS b FORCE INDEX (PRIMARY)
LEFT JOIN fact_flight AS f ON f.FlightKey = b.FlightKey
LEFT JOIN fact_airport_weather_hourly AS w ON w.WeatherKey = b.WeatherKey
WHERE b.FlightKey BETWEEN 4680483 AND 4780482
  AND b.ExposureType = 'ACTUAL_ARRIVAL'
  AND b.SegmentSequence = 1
  AND b.WeatherCoverageStatus = 'MATCHED_WEATHER_HOUR';

/* B3. (optional) Buffer pool size. If it is the 128 MB default, queries are disk-bound;
   reading only, no change is made here. */
SELECT @@innodb_buffer_pool_size / 1024 / 1024 AS BufferPoolMB;
