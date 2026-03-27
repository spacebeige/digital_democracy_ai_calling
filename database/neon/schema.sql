-- ============================================================
-- Government Schemes Schema for Neon (PostgreSQL)
-- File: database/neon/schema.sql
-- Run this ONCE in Neon SQL editor before running scraper
-- ============================================================

CREATE TABLE IF NOT EXISTS schemes (
    id                   SERIAL PRIMARY KEY,
    slug                 TEXT UNIQUE NOT NULL,
    name                 TEXT NOT NULL,
    short_title          TEXT,
    level                TEXT,              -- central / state / local
    state                TEXT,
    ministry             TEXT,
    department           TEXT,
    implementing_agency  TEXT,
    categories           JSONB DEFAULT '[]',
    subcategories        JSONB DEFAULT '[]',
    target_group         TEXT,
    tags                 JSONB DEFAULT '[]',
    brief_description    TEXT,
    detailed_description TEXT,
    eligibility          TEXT,
    benefits             TEXT,
    how_to_apply         TEXT,
    documents            JSONB DEFAULT '[]',
    references           JSONB DEFAULT '[]',
    source_url           TEXT,
    scraped_at           TIMESTAMPTZ DEFAULT NOW()
);

-- Full-text search index using PostgreSQL tsvector
-- Covers name, description, eligibility, benefits, tags
ALTER TABLE schemes
    ADD COLUMN IF NOT EXISTS search_vector TSVECTOR
    GENERATED ALWAYS AS (
        setweight(to_tsvector('english', coalesce(name, '')), 'A') ||
        setweight(to_tsvector('english', coalesce(brief_description, '')), 'B') ||
        setweight(to_tsvector('english', coalesce(eligibility, '')), 'C') ||
        setweight(to_tsvector('english', coalesce(benefits, '')), 'C') ||
        setweight(to_tsvector('english', coalesce(detailed_description, '')), 'D')
    ) STORED;

CREATE INDEX IF NOT EXISTS idx_schemes_search ON schemes USING GIN(search_vector);
CREATE INDEX IF NOT EXISTS idx_schemes_slug   ON schemes(slug);
CREATE INDEX IF NOT EXISTS idx_schemes_level  ON schemes(level);
CREATE INDEX IF NOT EXISTS idx_schemes_state  ON schemes(state);
CREATE INDEX IF NOT EXISTS idx_schemes_tags   ON schemes USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_schemes_cats   ON schemes USING GIN(categories);

-- ============================================================
-- Quick test after running schema:
-- SELECT COUNT(*) FROM schemes;
-- SELECT name, level FROM schemes LIMIT 5;
-- ============================================================