USE flight_dw_2025;

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
