-- 001_initial_schema.sql

CREATE TABLE IF NOT EXISTS links (
    id SERIAL PRIMARY KEY,
    short_code VARCHAR(10) UNIQUE NOT NULL,
    original_url TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_links_short_code ON links(short_code);

-- Analytics partition table logic ensures massive tables query fast.
CREATE TABLE IF NOT EXISTS click_events (
    id BIGSERIAL,
    short_code VARCHAR(10) NOT NULL REFERENCES links(short_code),
    ip_address VARCHAR(45),
    country VARCHAR(2),
    user_agent TEXT,
    device_type VARCHAR(50),
    clicked_at TIMESTAMP WITH TIME ZONE NOT NULL,
    PRIMARY KEY (id, clicked_at)
) PARTITION BY RANGE (clicked_at);

-- Create initial partitions
CREATE TABLE IF NOT EXISTS click_events_y2026m04 PARTITION OF click_events
    FOR VALUES FROM ('2026-04-01') TO ('2026-05-01');

CREATE TABLE IF NOT EXISTS click_events_y2026m05 PARTITION OF click_events
    FOR VALUES FROM ('2026-05-01') TO ('2026-06-01');

CREATE INDEX idx_click_events_short_code_time ON click_events(short_code, clicked_at);
