-- CloudWiseAI PostgreSQL schema
-- Run with:  psql "$DATABASE_URL" -f src/backend/db/schema.sql

CREATE TABLE IF NOT EXISTS users (
    id            SERIAL PRIMARY KEY,
    username      VARCHAR(60)  NOT NULL,
    email         VARCHAR(255) NOT NULL UNIQUE,
    password_hash TEXT         NOT NULL,
    created_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- One row per resource per day. Mirrors dataset/raw/cloudwise_billing.csv.
CREATE TABLE IF NOT EXISTS cost_records (
    id                  BIGSERIAL PRIMARY KEY,
    date                DATE          NOT NULL,
    billing_period      CHAR(7)       NOT NULL,          -- 'YYYY-MM'
    service             VARCHAR(40)   NOT NULL,
    region              VARCHAR(30)   NOT NULL,
    resource_id         VARCHAR(80)   NOT NULL,
    usage_hours         NUMERIC(8,2)  NOT NULL DEFAULT 0,
    storage_gb          NUMERIC(12,1) NOT NULL DEFAULT 0,
    avg_cpu_utilization NUMERIC(5,1)  NOT NULL DEFAULT 0,
    cost                NUMERIC(12,4) NOT NULL,
    UNIQUE (date, resource_id)
);

CREATE INDEX IF NOT EXISTS idx_cost_date          ON cost_records (date);
CREATE INDEX IF NOT EXISTS idx_cost_service_date  ON cost_records (service, date);
CREATE INDEX IF NOT EXISTS idx_cost_period        ON cost_records (billing_period);

-- Output of the anomaly detector. Fields match the frontend AnomalyCard props.
CREATE TABLE IF NOT EXISTS anomalies (
    id            SERIAL PRIMARY KEY,
    service       VARCHAR(40)   NOT NULL,
    resource_id   VARCHAR(80),
    date          DATE          NOT NULL,
    expected_cost NUMERIC(12,2) NOT NULL,
    actual_cost   NUMERIC(12,2) NOT NULL,
    deviation     NUMERIC(8,1)  NOT NULL,                -- percent above expected
    severity      VARCHAR(10)   NOT NULL CHECK (severity IN ('Low','Medium','High','Critical')),
    note          TEXT,
    detected_at   TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

-- Output of the recommendation engine. Fields match the frontend RecommendationCard props.
CREATE TABLE IF NOT EXISTS recommendations (
    id                SERIAL PRIMARY KEY,
    title             TEXT          NOT NULL,
    service           VARCHAR(40)   NOT NULL,
    category          VARCHAR(40)   NOT NULL,
    description       TEXT          NOT NULL,
    potential_savings NUMERIC(12,2) NOT NULL,            -- per month
    effort            VARCHAR(10)   NOT NULL CHECK (effort IN ('Low','Medium','High')),
    status            VARCHAR(12)   NOT NULL DEFAULT 'open',
    created_at        TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);
