-- THE WARDEN — Backend Database Schema
-- PostgreSQL 15+

-- ─────────────────────────────────────────────────────────────────────────────
-- NPC relationship state
-- Tracks the player's relationship level with each NPC, per save slot.
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS npc_relationships (
    id              SERIAL PRIMARY KEY,
    save_slot       INTEGER     NOT NULL DEFAULT 1,
    npc_id          VARCHAR(16) NOT NULL,
    relationship    INTEGER     NOT NULL DEFAULT 0 CHECK (relationship BETWEEN 0 AND 4),
    last_spoken_day INTEGER     NOT NULL DEFAULT 0,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (save_slot, npc_id)
);

-- ─────────────────────────────────────────────────────────────────────────────
-- Conversation memory
-- Stores the rolling conversation history injected into each NPC's context.
-- Older entries are pruned by memory_service once the window exceeds the limit.
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS conversation_memory (
    id              BIGSERIAL PRIMARY KEY,
    save_slot       INTEGER     NOT NULL DEFAULT 1,
    npc_id          VARCHAR(16) NOT NULL,
    role            VARCHAR(16) NOT NULL CHECK (role IN ('player', 'npc')),
    content         TEXT        NOT NULL,
    game_day        INTEGER     NOT NULL,
    game_time       REAL        NOT NULL,  -- 0.0–24.0 in-game hours
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_conv_memory_lookup
    ON conversation_memory (save_slot, npc_id, created_at DESC);

-- ─────────────────────────────────────────────────────────────────────────────
-- World state snapshot
-- One row per save slot. Updated by the world tick.
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS world_state (
    save_slot               INTEGER PRIMARY KEY DEFAULT 1,
    current_day             INTEGER NOT NULL DEFAULT 1,
    current_time_of_day     REAL    NOT NULL DEFAULT 8.0,  -- 0.0–24.0
    weather_state           INTEGER NOT NULL DEFAULT 0,    -- 0=Overcast 1=Rain 2=Clearing 3=Clear
    mystery_layer           INTEGER NOT NULL DEFAULT 0,    -- 0–5
    binding_degradation     REAL    NOT NULL DEFAULT 0.0,  -- 0.0–100.0 %
    council_awareness       INTEGER NOT NULL DEFAULT 0,    -- 0–100
    voice_patience          REAL    NOT NULL DEFAULT 1.0,  -- 0.0–1.0
    collected_evidence      TEXT[]  NOT NULL DEFAULT '{}',
    active_spells           TEXT[]  NOT NULL DEFAULT '{}',
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Seed a default save slot
INSERT INTO world_state (save_slot) VALUES (1) ON CONFLICT DO NOTHING;

-- ─────────────────────────────────────────────────────────────────────────────
-- Evidence log
-- Immutable record of when each piece of evidence was collected.
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS evidence_log (
    id              BIGSERIAL PRIMARY KEY,
    save_slot       INTEGER     NOT NULL DEFAULT 1,
    evidence_id     VARCHAR(8)  NOT NULL,
    game_day        INTEGER     NOT NULL,
    game_time       REAL        NOT NULL,
    collected_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (save_slot, evidence_id)
);

-- ─────────────────────────────────────────────────────────────────────────────
-- Spell use log
-- Records every Dominion spell cast. Used for Council awareness calculation.
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS spell_log (
    id              BIGSERIAL PRIMARY KEY,
    save_slot       INTEGER     NOT NULL DEFAULT 1,
    spell_name      VARCHAR(64) NOT NULL,
    zone            VARCHAR(64) NOT NULL,
    game_day        INTEGER     NOT NULL,
    game_time       REAL        NOT NULL,
    cast_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
