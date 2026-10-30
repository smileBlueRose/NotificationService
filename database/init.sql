CREATE TABLE IF NOT EXISTS accepted_events (
    event_id UUID PRIMARY KEY,
    accepted_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS recipients (
    recipient_id BIGINT PRIMARY KEY,
    email TEXT,
    email_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    push_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    locale TEXT NOT NULL DEFAULT 'en'
);

CREATE TABLE IF NOT EXISTS recipient_devices (
    device_token TEXT PRIMARY KEY,
    recipient_id BIGINT NOT NULL REFERENCES recipients (recipient_id) ON DELETE CASCADE,
    platform TEXT NOT NULL CHECK (platform IN ('ios', 'android'))
);

CREATE INDEX IF NOT EXISTS recipient_devices_recipient_id_idx ON recipient_devices (recipient_id);

CREATE TABLE IF NOT EXISTS notifications (
    notification_id UUID PRIMARY KEY,
    event_id UUID NOT NULL,
    channel TEXT NOT NULL CHECK (channel IN ('email', 'push')),
    target TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('PENDING', 'RETRYING', 'SENT', 'FAILED')),
    attempts INT NOT NULL DEFAULT 0,
    last_error TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    sent_at TIMESTAMPTZ
);