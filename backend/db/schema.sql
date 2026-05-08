-- NammaCity Database Schema
-- Run this in Supabase SQL Editor

-- Enable PostGIS
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Agencies table
CREATE TABLE IF NOT EXISTS agencies (
    id          uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    name        varchar(100) NOT NULL UNIQUE,
    twitter_handle varchar(100),
    email_pattern  varchar(200),
    jurisdiction   text[] DEFAULT '{}'
);

-- Ward officers table
CREATE TABLE IF NOT EXISTS ward_officers (
    id           uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    ward_number  int NOT NULL,
    officer_name varchar(200) NOT NULL,
    email        varchar(200),
    phone        varchar(20),
    agency_id    uuid REFERENCES agencies(id)
);

-- Clusters table (crowd validation bundles)
CREATE TABLE IF NOT EXISTS clusters (
    id                uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    centroid_location geometry(Point, 4326),
    member_count      int DEFAULT 1,
    issue_type        varchar(50),
    status            varchar(20) DEFAULT 'active',
    created_at        timestamptz DEFAULT now()
);

-- Complaints table
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

-- Spatial indexes
CREATE INDEX IF NOT EXISTS idx_complaints_location
    ON complaints USING GIST (location);

CREATE INDEX IF NOT EXISTS idx_clusters_centroid
    ON clusters USING GIST (centroid_location);

-- Regular indexes
CREATE INDEX IF NOT EXISTS idx_complaints_ward
    ON complaints (ward_number);

CREATE INDEX IF NOT EXISTS idx_complaints_status
    ON complaints (status);

CREATE INDEX IF NOT EXISTS idx_complaints_issue_type
    ON complaints (issue_type);

CREATE INDEX IF NOT EXISTS idx_ward_officers_ward
    ON ward_officers (ward_number);

-- RPC function for radius queries (used by db/client.py)
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
