-- Phase 7 migration: Submission tracking + cluster notification state
-- Run in Supabase SQL Editor

ALTER TABLE clusters ADD COLUMN IF NOT EXISTS last_notified_at_size INTEGER DEFAULT 0;
ALTER TABLE clusters ADD COLUMN IF NOT EXISTS last_notified_at TIMESTAMPTZ;
ALTER TABLE clusters ADD COLUMN IF NOT EXISTS aggregated_description TEXT;

CREATE TABLE IF NOT EXISTS submissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    complaint_id UUID REFERENCES complaints(id),
    cluster_id UUID REFERENCES clusters(id),
    channel VARCHAR NOT NULL,
    status VARCHAR NOT NULL,
    reference_id TEXT,
    error_message TEXT,
    mode VARCHAR,
    submitted_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_submissions_complaint ON submissions(complaint_id);
CREATE INDEX IF NOT EXISTS idx_submissions_cluster ON submissions(cluster_id);

-- RLS policies for submissions table
CREATE POLICY "Allow all on submissions" ON submissions FOR ALL USING (true) WITH CHECK (true);
ALTER TABLE submissions ENABLE ROW LEVEL SECURITY;
