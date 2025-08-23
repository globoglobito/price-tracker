-- Migration: 002_status_columns.sql
-- Description: Add status and lifecycle columns to listings for incremental tracking

BEGIN;

ALTER TABLE price_tracker.listings
  ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE,
  ADD COLUMN IF NOT EXISTS first_seen_at TIMESTAMP,
  ADD COLUMN IF NOT EXISTS last_seen_at TIMESTAMP,
  ADD COLUMN IF NOT EXISTS ended_at TIMESTAMP;

-- Backfill first_seen_at and last_seen_at from scraped_at for existing rows
UPDATE price_tracker.listings
SET first_seen_at = COALESCE(first_seen_at, scraped_at),
    last_seen_at = COALESCE(last_seen_at, scraped_at)
WHERE TRUE;

COMMIT;


