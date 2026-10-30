CREATE TABLE IF NOT EXISTS accepted_events (
    event_id UUID PRIMARY KEY,
    accepted_at TIMESTAMPTZ NOT NULL DEFAULT now()
);