-- Markdown Architecture — Stage 1 Buildability Proof
-- Schema v1.0

-- workflow_events: append-only log of every step transition.
-- DBOS uses this table internally for durable execution.
-- We also write our own stage events here for auditability.
CREATE TABLE IF NOT EXISTS workflow_events (
    id              BIGSERIAL PRIMARY KEY,
    event_id        UUID        NOT NULL DEFAULT gen_random_uuid(),
    workflow_run_id TEXT        NOT NULL,
    stage_id        TEXT        NOT NULL,
    step_name       TEXT        NOT NULL,
    status          TEXT        NOT NULL,  -- started | passed | failed | blocked
    payload         JSONB,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_workflow_events_run
    ON workflow_events (workflow_run_id, created_at);

-- provenance_log: immutable receipt hash ledger (ADR-001).
-- One row per PromptExecutionReceipt.
-- receipt_json is stored for queryability; pg_receipt_hash is the integrity anchor.
CREATE TABLE IF NOT EXISTS provenance_log (
    id                  BIGSERIAL PRIMARY KEY,
    receipt_id          UUID        NOT NULL UNIQUE,
    workflow_run_id     TEXT        NOT NULL,
    stage_id            TEXT        NOT NULL,
    operator_id         TEXT        NOT NULL,
    pg_receipt_hash     TEXT        NOT NULL,  -- SHA-256 of the full receipt JSON
    receipt_json        JSONB       NOT NULL,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_provenance_log_stage
    ON provenance_log (stage_id, created_at);

COMMENT ON TABLE provenance_log IS
    'Append-only receipt ledger. Never UPDATE or DELETE rows. ADR-001.';
