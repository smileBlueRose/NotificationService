TRUNCATE recipients CASCADE;

INSERT INTO recipients (recipient_id, email, email_enabled, push_enabled)
SELECT
    n,
    'user' || n || '@example.com',
    n % 2 = 0,
    n % 5 <> 0
FROM generate_series(1, 1000) AS n;

INSERT INTO recipient_devices (device_token, recipient_id, platform)
SELECT
    'device-' || n || '-1',
    n,
    CASE WHEN n % 3 = 0 THEN 'ios' ELSE 'android' END
FROM generate_series(1, 1000) AS n
WHERE n % 5 <> 0
UNION ALL
SELECT
    'device-' || n || '-2',
    n,
    CASE WHEN n % 3 = 0 THEN 'android' ELSE 'ios' END
FROM generate_series(1, 1000) AS n
WHERE n % 5 <> 0 AND n % 2 = 1;