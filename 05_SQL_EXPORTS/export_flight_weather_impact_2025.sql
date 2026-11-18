/* =============================================================================
   AERO INSIGHTS | FLIGHT x WEATHER RELATIONAL SNAPSHOT EXPORT
   Database: flight_dw_2025 | Scope: completed Bridge months 01-09 of 2025

   RELATIONSHIP PATH:
     fact_flight.FlightKey
       -> bridge_flight_weather_exposure.FlightKey
       -> bridge.WeatherKey = fact_airport_weather_hourly.WeatherKey
     bridge.AirportKey + bridge.OurAirportsID -> dim_airport
     Departure exposure AirportKey must equal fact_flight.OriginAirportKey.
     Arrival exposure AirportKey must equal fact_flight.DestinationAirportKey.

   EVENT TIMING:
     Four exposure types are exported separately:
       SCHEDULED_DEPARTURE, ACTUAL_DEPARTURE,
       SCHEDULED_ARRIVAL, ACTUAL_ARRIVAL.
     Scheduled events are the primary view for delay association; actual events
     are descriptive conditions at the actual event time. Neither proves cause.

   QUERY 1 RESULT -> export as:
     03_EXPORT_DATA/flight_weather_impact_2025.csv
   QUERY 2 RESULT -> export as:
     03_EXPORT_DATA/flight_weather_coverage_2025.csv

   All statements are SELECT-only. No tables, indexes, ETL data or DW rows are
   created, updated or deleted.
   ============================================================================= */

USE flight_dw_2025;

/* -----------------------------------------------------------------------------
   QUERY 1: MATCHED FLIGHT x AIRPORT x WEATHER ANALYTICS
   Grain: SourceMonth x ExposureType x AirportKey x PrecipitationBand x WindSpeedBand
   Only rows with an approved, matched hourly WeatherKey are included.
   ----------------------------------------------------------------------------- */
WITH matched_exposure AS (
    SELECT
        b.SourceMonth,
        CAST(b.SourceMonth AS UNSIGNED) AS MonthNumber,
        ELT(CAST(b.SourceMonth AS UNSIGNED),
            'January','February','March','April','May','June',
            'July','August','September','October','November','December') AS MonthName,
        b.ExposureType,
        CASE
            WHEN b.ExposureType IN ('SCHEDULED_DEPARTURE','ACTUAL_DEPARTURE') THEN 'ORIGIN'
            ELSE 'DESTINATION'
        END AS AirportRole,
        b.AirportKey,
        b.OurAirportsID,
        COALESCE(NULLIF(a.IATACode,''), NULLIF(a.ICAOCode,''), a.Ident) AS AirportCode,
        a.Ident,
        a.AirportName,
        a.Municipality,
        a.ISOCountry,
        CASE
            WHEN w.Precipitation = 0 THEN 'Dry (0)'
            WHEN w.Precipitation <= 1 THEN 'Wet (0-1]'
            WHEN w.Precipitation <= 5 THEN 'Wet (1-5]'
            ELSE 'Wet (>5)'
        END AS PrecipitationBand,
        CASE
            WHEN w.Precipitation = 0 THEN 1
            WHEN w.Precipitation <= 1 THEN 2
            WHEN w.Precipitation <= 5 THEN 3
            ELSE 4
        END AS PrecipitationBandSort,
        CASE
            WHEN w.WindSpeed10m <= 10 THEN '0-10'
            WHEN w.WindSpeed10m <= 20 THEN '(10-20]'
            WHEN w.WindSpeed10m <= 40 THEN '(20-40]'
            ELSE '>40'
        END AS WindSpeedBand,
        CASE
            WHEN w.WindSpeed10m <= 10 THEN 1
            WHEN w.WindSpeed10m <= 20 THEN 2
            WHEN w.WindSpeed10m <= 40 THEN 3
            ELSE 4
        END AS WindSpeedBandSort,
        b.WeatherKey,
        b.MinutesAfterWeatherHour,
        f.FlightCount,
        f.Cancelled,
        f.Diverted,
        f.DepDel15,
        f.DepDelay,
        f.DepDelayMinutes,
        f.ArrDel15,
        f.ArrDelay,
        f.ArrDelayMinutes,
        w.Temperature2m,
        w.RelativeHumidity2m,
        w.Precipitation,
        w.WindSpeed10m,
        w.WindGusts10m,
        w.CloudCover
    FROM bridge_flight_weather_exposure AS b
    INNER JOIN fact_flight AS f
        ON f.FlightKey = b.FlightKey
       AND f.SourceMonth = b.SourceMonth
    INNER JOIN dim_airport AS a
        ON a.AirportKey = b.AirportKey
       AND a.OurAirportsID = b.OurAirportsID
    INNER JOIN fact_airport_weather_hourly AS w
        ON w.WeatherKey = b.WeatherKey
       AND w.OurAirportsID = b.OurAirportsID
       AND w.WeatherHourUTC = b.WeatherHourUTC
    WHERE b.SourceMonth BETWEEN '01' AND '09'
      AND b.ExposureType IN (
          'SCHEDULED_DEPARTURE', 'ACTUAL_DEPARTURE',
          'SCHEDULED_ARRIVAL', 'ACTUAL_ARRIVAL'
      )
      AND b.SegmentSequence = 1
      AND b.WeatherCoverageStatus = 'MATCHED_WEATHER_HOUR'
      AND b.WeatherKey IS NOT NULL
      AND (
          (b.ExposureType IN ('SCHEDULED_DEPARTURE','ACTUAL_DEPARTURE')
              AND b.AirportKey = f.OriginAirportKey)
          OR
          (b.ExposureType IN ('SCHEDULED_ARRIVAL','ACTUAL_ARRIVAL')
              AND b.AirportKey = f.DestinationAirportKey)
      )
)
SELECT
    SourceMonth,
    MonthNumber,
    MonthName,
    ExposureType,
    AirportRole,
    AirportKey,
    OurAirportsID,
    AirportCode,
    Ident,
    AirportName,
    Municipality,
    ISOCountry,
    PrecipitationBand,
    PrecipitationBandSort,
    WindSpeedBand,
    WindSpeedBandSort,

    COUNT(*) AS MatchedExposureRows,
    SUM(FlightCount) AS MatchedExposureFlights,
    COUNT(DISTINCT WeatherKey) AS MatchedWeatherObservations,
    SUM(CASE WHEN Cancelled = 1 THEN FlightCount ELSE 0 END) AS CancelledFlights,
    SUM(CASE WHEN Diverted = 1 THEN FlightCount ELSE 0 END) AS DivertedFlights,

    SUM(CASE
        WHEN ExposureType IN ('SCHEDULED_DEPARTURE','ACTUAL_DEPARTURE')
         AND Cancelled = 0 AND DepDel15 IS NOT NULL
        THEN FlightCount
        WHEN ExposureType IN ('SCHEDULED_ARRIVAL','ACTUAL_ARRIVAL')
         AND Cancelled = 0 AND Diverted = 0 AND ArrDel15 IS NOT NULL
        THEN FlightCount
        ELSE 0 END) AS EligibleFlights,

    SUM(CASE
        WHEN ExposureType IN ('SCHEDULED_DEPARTURE','ACTUAL_DEPARTURE')
         AND Cancelled = 0 AND DepDel15 = 1
        THEN FlightCount
        WHEN ExposureType IN ('SCHEDULED_ARRIVAL','ACTUAL_ARRIVAL')
         AND Cancelled = 0 AND Diverted = 0 AND ArrDel15 = 1
        THEN FlightCount
        ELSE 0 END) AS DelayedFlights,

    ROUND(100.0 * SUM(CASE
        WHEN ExposureType IN ('SCHEDULED_DEPARTURE','ACTUAL_DEPARTURE')
         AND Cancelled = 0 AND DepDel15 = 1
        THEN FlightCount
        WHEN ExposureType IN ('SCHEDULED_ARRIVAL','ACTUAL_ARRIVAL')
         AND Cancelled = 0 AND Diverted = 0 AND ArrDel15 = 1
        THEN FlightCount
        ELSE 0 END) / NULLIF(SUM(CASE
        WHEN ExposureType IN ('SCHEDULED_DEPARTURE','ACTUAL_DEPARTURE')
         AND Cancelled = 0 AND DepDel15 IS NOT NULL
        THEN FlightCount
        WHEN ExposureType IN ('SCHEDULED_ARRIVAL','ACTUAL_ARRIVAL')
         AND Cancelled = 0 AND Diverted = 0 AND ArrDel15 IS NOT NULL
        THEN FlightCount
        ELSE 0 END), 0), 2) AS DelayRatePct,

    ROUND(
        SUM(CASE
            WHEN ExposureType IN ('SCHEDULED_DEPARTURE','ACTUAL_DEPARTURE')
             AND Cancelled = 0 AND DepDelay IS NOT NULL
            THEN DepDelay * FlightCount
            WHEN ExposureType IN ('SCHEDULED_ARRIVAL','ACTUAL_ARRIVAL')
             AND Cancelled = 0 AND Diverted = 0 AND ArrDelay IS NOT NULL
            THEN ArrDelay * FlightCount
            ELSE 0 END)
        / NULLIF(SUM(CASE
            WHEN ExposureType IN ('SCHEDULED_DEPARTURE','ACTUAL_DEPARTURE')
             AND Cancelled = 0 AND DepDelay IS NOT NULL
            THEN FlightCount
            WHEN ExposureType IN ('SCHEDULED_ARRIVAL','ACTUAL_ARRIVAL')
             AND Cancelled = 0 AND Diverted = 0 AND ArrDelay IS NOT NULL
            THEN FlightCount
            ELSE 0 END), 0), 2
    ) AS AvgSignedDelayMinutes,

    SUM(CASE
        WHEN ExposureType IN ('SCHEDULED_DEPARTURE','ACTUAL_DEPARTURE')
         AND Cancelled = 0 AND DepDelayMinutes IS NOT NULL
        THEN DepDelayMinutes * FlightCount
        WHEN ExposureType IN ('SCHEDULED_ARRIVAL','ACTUAL_ARRIVAL')
         AND Cancelled = 0 AND Diverted = 0 AND ArrDelayMinutes IS NOT NULL
        THEN ArrDelayMinutes * FlightCount
        ELSE 0 END) AS TotalPositiveDelayMinutes,

    ROUND(AVG(Temperature2m), 2) AS AvgTemperature,
    ROUND(AVG(RelativeHumidity2m), 2) AS AvgRelativeHumidity,
    ROUND(AVG(Precipitation), 3) AS AvgPrecipitation,
    ROUND(AVG(WindSpeed10m), 2) AS AvgWindSpeed,
    ROUND(AVG(WindGusts10m), 2) AS AvgWindGust,
    ROUND(AVG(CloudCover), 2) AS AvgCloudCover,
    ROUND(AVG(MinutesAfterWeatherHour), 2) AS AvgMinutesAfterWeatherHour
FROM matched_exposure
GROUP BY
    SourceMonth, MonthNumber, MonthName, ExposureType, AirportRole,
    AirportKey, OurAirportsID, AirportCode, Ident, AirportName, Municipality,
    ISOCountry, PrecipitationBand, PrecipitationBandSort, WindSpeedBand, WindSpeedBandSort
ORDER BY
    MonthNumber, ExposureType, AirportCode, PrecipitationBandSort, WindSpeedBandSort;

/* -----------------------------------------------------------------------------
   QUERY 2: BRIDGE MATCH-COVERAGE DETAIL
   Grain: SourceMonth x ExposureType x AirportKey x WeatherCoverageStatus
   Includes matched and separate-handling/unresolved statuses.
   ----------------------------------------------------------------------------- */
SELECT
    b.SourceMonth,
    CAST(b.SourceMonth AS UNSIGNED) AS MonthNumber,
    ELT(CAST(b.SourceMonth AS UNSIGNED),
        'January','February','March','April','May','June',
        'July','August','September','October','November','December') AS MonthName,
    b.ExposureType,
    CASE
        WHEN b.ExposureType IN ('SCHEDULED_DEPARTURE','ACTUAL_DEPARTURE') THEN 'ORIGIN'
        ELSE 'DESTINATION'
    END AS AirportRole,
    b.AirportKey,
    COALESCE(NULLIF(a.IATACode,''), NULLIF(a.ICAOCode,''), a.Ident) AS AirportCode,
    a.AirportName,
    a.ISOCountry,
    b.WeatherCoverageStatus,
    COUNT(*) AS BridgeExposureRows,
    SUM(b.WeatherKey IS NOT NULL) AS NonNullWeatherKeys,
    SUM(CASE
        WHEN b.WeatherCoverageStatus = 'MATCHED_WEATHER_HOUR'
         AND (b.WeatherKey IS NULL OR b.WeatherNaturalKey IS NULL)
        THEN 1 ELSE 0 END) AS MatchedStatusMissingKeyRows,
    SUM(CASE
        WHEN b.WeatherCoverageStatus <> 'MATCHED_WEATHER_HOUR'
         AND b.WeatherKey IS NOT NULL
        THEN 1 ELSE 0 END) AS NonMatchedStatusHasKeyRows
FROM bridge_flight_weather_exposure AS b
INNER JOIN dim_airport AS a
    ON a.AirportKey = b.AirportKey
   AND a.OurAirportsID = b.OurAirportsID
WHERE b.SourceMonth BETWEEN '01' AND '09'
  AND b.ExposureType IN (
      'SCHEDULED_DEPARTURE', 'ACTUAL_DEPARTURE',
      'SCHEDULED_ARRIVAL', 'ACTUAL_ARRIVAL'
  )
  AND b.SegmentSequence = 1
GROUP BY
    b.SourceMonth, b.ExposureType, b.AirportKey,
    AirportRole, AirportCode, a.AirportName, a.ISOCountry,
    b.WeatherCoverageStatus
ORDER BY
    MonthNumber, b.ExposureType, AirportCode, b.WeatherCoverageStatus;
