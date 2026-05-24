# ADR-002 — Automerge/Yjs Bytea-Blob CRDT Pattern over Postgres

| Field | Value |
|---|---|
| ID | ADR-002 |
| Status | Accepted |
| Date | 2026-05-23 |
| Deciders | PryzmEdge |
| Supersedes | — |
| Superseded by | — |

---

## Context

The system requires local-first collaboration: multiple clients (desktop, mobile, remote) must be able to edit the same markdown documents concurrently and merge without conflicts. The canonical solution is CRDTs (Conflict-free Replicated Data Types).

Two approaches were evaluated:

1. **Row-level CRDTs in Postgres** — treat individual Postgres rows as CRDT elements, implementing merge logic in SQL triggers or application code.
2. **CRDT documents stored as blobs in Postgres, projected into queryable tables** — store Automerge or Yjs binary documents in `bytea` columns; run a projection layer that materializes CRDT state into normalized tables.

Approach 1 is an unsolved problem at the general level. `cr-sqlite` implements a similar pattern for SQLite but no published equivalent exists for Postgres rows. Implementing CRDT merge semantics in Postgres triggers for arbitrary document types is high-risk and high-maintenance.

---

## Decision

Use the **bytea-blob CRDT pattern**: store Automerge 3.0 (or Yjs) documents as opaque `bytea` values in Postgres, with a projection layer that materializes their content into queryable tables.

Concretely:

```sql
CREATE TABLE crdt_documents (
    doc_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    doc_type    TEXT NOT NULL,           -- 'note', 'analysis', 'config'
    blob        BYTEA NOT NULL,          -- Automerge/Yjs binary
    vector_clock JSONB,                  -- optional: logical clock for debugging
    created_at  TIMESTAMPTZ DEFAULT now(),
    updated_at  TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE crdt_projections (
    doc_id      UUID REFERENCES crdt_documents(doc_id),
    field_path  TEXT NOT NULL,           -- e.g. 'frontmatter.title'
    field_value JSONB,
    updated_at  TIMESTAMPTZ DEFAULT now(),
    PRIMARY KEY (doc_id, field_path)
);
```

A projection worker (triggered or scheduled) reads the CRDT blob, materializes its fields into `crdt_projections`, and updates any downstream Postgres indexes (full-text, pgvector embeddings, metadata tables).

Sync between clients uses an Automerge sync server or Yjs WebSocket provider; Postgres is the durable backing store, not the sync transport.

---

## Consequences

**Positive:**
- CRDT merge logic lives in a well-maintained library (Automerge 3.0: 10× memory reduction vs. v2; Yjs: production-proven at Notion/Linear scale).
- Postgres remains the durable, transactional store and query surface.
- Projections can be rebuilt from blobs at any time (replay semantics).
- No custom trigger logic for merge conflicts.

**Negative / risks:**
- Dual state: CRDT blob + projection tables must be kept in sync. Projection lag is possible.
- Querying CRDT state directly (without projection) requires deserializing the blob in application code.
- Projection worker is an additional operational component.
- Consistency seam: if projection worker fails, tables may lag behind blob state.

**Mitigation:** treat the `bytea` blob as the source of truth; projections are derived and can always be rebuilt. Run projection worker idempotently.

---

## Alternatives considered

| Alternative | Reason rejected |
|---|---|
| Row-level CRDTs in Postgres | Unsolved general problem; no published production implementation |
| cr-sqlite | SQLite only; not Postgres |
| Anytype / any-sync | Separate operational stack; rejects Postgres as substrate |
| Automerge with file-system storage only | No SQL queryability; no transactional provenance |

---

## References

- Automerge 3.0 — automerge.org/blog/automerge-3/ (July 2025)
- Yjs — yjs.dev
- cr-sqlite — vlcn.io
- Ink & Switch Patchwork — inkandswitch.com
