# Queries note 

See table
SELECT TABLE_NAME
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_TYPE = 'BASE TABLE'
ORDER BY TABLE_NAME;

Check row numbers
SELECT 'agency' AS table_name, COUNT(*) AS row_count FROM agency
UNION ALL
SELECT 'calendar', COUNT(*) FROM calendar
UNION ALL
SELECT 'calendar_dates', COUNT(*) FROM calendar_dates
UNION ALL
SELECT 'routes', COUNT(*) FROM routes
UNION ALL
SELECT 'stops', COUNT(*) FROM stops
UNION ALL
SELECT 'stop_times', COUNT(*) FROM stop_times
UNION ALL
SELECT 'trips', COUNT(*) FROM trips;

