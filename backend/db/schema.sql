-- NammaCity Database Schema
-- Run this in Supabase SQL Editor

-- Enable PostGIS
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ─────────────────────────────────────────
-- Core reference tables
-- ─────────────────────────────────────────

CREATE TABLE IF NOT EXISTS agencies (
    id             uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    name           varchar(100) NOT NULL UNIQUE,
    twitter_handle varchar(100),
    email_pattern  varchar(200),
    jurisdiction   text[] DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS ward_officers (
    id           uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    ward_number  int NOT NULL UNIQUE,
    officer_name varchar(200) NOT NULL,
    email        varchar(200),
    phone        varchar(20),
    agency_id    uuid REFERENCES agencies(id)
);

-- ─────────────────────────────────────────
-- Clusters (crowd-validation bundles)
-- ─────────────────────────────────────────

CREATE TABLE IF NOT EXISTS clusters (
    id                    uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    centroid_location     geometry(Point, 4326),
    member_count          int DEFAULT 1,
    issue_type            varchar(50),
    status                varchar(20) DEFAULT 'active',
    -- Notification suppression: tracks last milestone at which the cluster sent alerts
    last_notified_at_size int DEFAULT 0,
    last_notified_at      timestamptz,
    created_at            timestamptz DEFAULT now()
);

-- ─────────────────────────────────────────
-- Complaints
-- ─────────────────────────────────────────

CREATE TABLE IF NOT EXISTS complaints (
    id              uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    description     text NOT NULL,
    photo_url       text,
    voice_note_url  text,
    location        geometry(Point, 4326),
    ward_number     int,
    zone            varchar(50),
    agency_id       uuid REFERENCES agencies(id),
    issue_type      varchar(50),
    severity        int CHECK (severity BETWEEN 1 AND 5) DEFAULT 3,
    status          varchar(20) DEFAULT 'open',
    cluster_id      uuid REFERENCES clusters(id),
    created_at      timestamptz DEFAULT now(),
    updated_at      timestamptz DEFAULT now()
);

-- ─────────────────────────────────────────
-- Submissions (per-channel dispatch log)
-- ─────────────────────────────────────────

CREATE TABLE IF NOT EXISTS submissions (
    id           uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    complaint_id uuid REFERENCES complaints(id) ON DELETE CASCADE,
    cluster_id   uuid REFERENCES clusters(id) ON DELETE SET NULL,
    channel      varchar(30) NOT NULL,   -- twitter | email | whatsapp
    status       varchar(20) NOT NULL,   -- success | failed | skipped | suppressed
    reference_id text,                   -- tweet URL or email message-id
    error_message text,
    mode         varchar(10) DEFAULT 'live', -- live | stub
    submitted_at timestamptz DEFAULT now()
);

-- ─────────────────────────────────────────
-- Escalations (day 0/7/14/21/30 ladder)
-- ─────────────────────────────────────────

CREATE TABLE IF NOT EXISTS escalations (
    id               uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    complaint_id     uuid REFERENCES complaints(id) ON DELETE CASCADE,
    cluster_id       uuid REFERENCES clusters(id) ON DELETE SET NULL,
    day              int NOT NULL,         -- 0 | 7 | 14 | 21 | 30
    action           varchar(50) NOT NULL, -- initial | councillor_tag | rti | mla_media | pil
    status           varchar(20) DEFAULT 'pending',  -- pending | sent | skipped | failed
    draft_text       text,
    reference_id     text,
    idempotency_key  text UNIQUE,          -- prevents double-escalation
    scheduled_for    timestamptz NOT NULL,
    executed_at      timestamptz,
    created_at       timestamptz DEFAULT now()
);

-- ─────────────────────────────────────────
-- Indexes
-- ─────────────────────────────────────────

CREATE INDEX IF NOT EXISTS idx_complaints_location
    ON complaints USING GIST (location);

CREATE INDEX IF NOT EXISTS idx_clusters_centroid
    ON clusters USING GIST (centroid_location);

CREATE INDEX IF NOT EXISTS idx_complaints_ward
    ON complaints (ward_number);

CREATE INDEX IF NOT EXISTS idx_complaints_status
    ON complaints (status);

CREATE INDEX IF NOT EXISTS idx_complaints_issue_type
    ON complaints (issue_type);

CREATE INDEX IF NOT EXISTS idx_complaints_created_at
    ON complaints (created_at DESC);

CREATE INDEX IF NOT EXISTS idx_ward_officers_ward
    ON ward_officers (ward_number);

CREATE INDEX IF NOT EXISTS idx_submissions_complaint
    ON submissions (complaint_id);

CREATE INDEX IF NOT EXISTS idx_escalations_complaint
    ON escalations (complaint_id);

CREATE INDEX IF NOT EXISTS idx_escalations_scheduled
    ON escalations (scheduled_for);

CREATE INDEX IF NOT EXISTS idx_escalations_idempotency
    ON escalations (idempotency_key);

-- ─────────────────────────────────────────
-- PostGIS RPC: radius query
-- ─────────────────────────────────────────

CREATE OR REPLACE FUNCTION get_complaints_in_radius(
    lat double precision,
    lng double precision,
    radius_m double precision DEFAULT 500.0,
    filter_issue_type text DEFAULT NULL
)
RETURNS SETOF complaints
LANGUAGE sql STABLE
AS $$
    SELECT *
    FROM complaints
    WHERE ST_DWithin(
        location::geography,
        ST_SetSRID(ST_MakePoint(lng, lat), 4326)::geography,
        radius_m
    )
    AND (filter_issue_type IS NULL OR issue_type = filter_issue_type)
    ORDER BY created_at DESC;
$$;

-- ─────────────────────────────────────────
-- PostGIS RPC: dashboard map query
-- ─────────────────────────────────────────

CREATE OR REPLACE FUNCTION get_open_complaints_map()
RETURNS TABLE (
    id uuid, issue_type varchar, severity int,
    status varchar, ward_number int, zone varchar,
    lat double precision, lng double precision,
    cluster_id uuid, created_at timestamptz
)
LANGUAGE sql STABLE
AS $$
    SELECT
        id, issue_type, severity, status, ward_number, zone,
        ST_Y(location::geometry) AS lat,
        ST_X(location::geometry) AS lng,
        cluster_id, created_at
    FROM complaints
    WHERE location IS NOT NULL
    ORDER BY created_at DESC
    LIMIT 1000;
$$;
