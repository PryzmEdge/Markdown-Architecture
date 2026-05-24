# ADR-001 — PostgreSQL as State Kernel and Provenance Ledger

| Field | Value |
|---|---|
| ID | ADR-001 |
| Status | Accepted |
| Date | 2026-05-23 |
| Deciders | PryzmEdge |
| Supersedes | — |
| Superseded by | — |

---

## Context

The system needs a single durable, transactional, queryable store that acts as the source of truth for: document metadata, event history, provenance receipts, lattice label assignments, capability grants, and projection state. Multiple candidates exist: SQLite (local-only, no WAL streaming), DuckDB (analytics-first, no multi-writer), Postgres (relational, ACID, WAL, RLS, pgvector, extensions), DBOS (Postgres-native workflow engine), CockroachDB (distributed, Postgres-compatible).

Earlier versions of this document used the framing "PostgreSQL as OS kernel." That framing was rejected after critical review: Postgres is a user-space process that depends on Linux for scheduling, IPC (shared memory + semaphores), memory protection, and disk I/O. It has no preemptive task scheduler and no syscall interface. The corrected framing is **state kernel and provenance ledger**.

---

## Decision

Use **PostgreSQL** as the unified state kernel and provenance ledger for the PryzmEdge quant workspace.

Specifically:
- All document metadata, frontmatter indexes, and stage state are stored in Postgres tables.
- All workflow events (tool invocations, stage transitions, lattice label assignments, declassifications) are written to an append-only events table (Marten-style event sourcing).
- Projections (read models, context snapshots) are derived from the event log via `pg_ivm` or explicit projection workers.
- pgvector / pgvectorscale is the vector index for semantic retrieval at personal scale.
- LISTEN/NOTIFY is the IPC-style event bus for lightweight pub/sub between components.
- `pg_cron` or DBOS is the scheduler for periodic maintenance tasks.
- RLS provides coarse-grained tenant and cohort isolation (not capability enforcement — see ADR-004).

---

## Consequences

**Positive:**
- Single operational substrate: one system to back up, monitor, and query.
- WAL provides a durable append-only log suitable as the base for event sourcing.
- Rich extension ecosystem: pgvector, pgvectorscale, pg_ivm, pg_mentat, pg_cron, PostGIS.
- SQL is the query language for all structured access — no additional query DSL for basic reads.
- Production-proven at personal and small-team scale (Letta: 42 tables, block_history audit; DBOS; Supabase).

**Negative / risks:**
- Single-writer per row limits throughput under high concurrency; acceptable at personal scale, requires re-evaluation at multi-tenant SaaS scale.
- pgvector HNSW indexes require tuning (`m`, `ef_construction`, `ef_search`) for recall vs. latency trade-offs.
- Postgres is a user-space process — "deterministic" applies only to the SQL execution model, not to wall-clock scheduling.
- CRDTs cannot be implemented at the row level (unsolved problem); Automerge/Yjs documents are stored as `bytea` blobs and projected (see ADR-002).

**Out of scope for this ADR:**
- Multi-tenant SaaS scaling (RLS at 10K+ tenants, schema-per-tenant trade-offs).
- pgvector beyond ~10⁸ vectors (dedicated vector DB territory).

---

## Alternatives considered

| Alternative | Reason rejected |
|---|---|
| SQLite | No WAL streaming, no multi-process concurrent writes, no RLS, no pgvector |
| DuckDB | Analytics-first; no multi-writer OLTP; no event sourcing ecosystem |
| CockroachDB | Distributed overhead unnecessary at personal scale; Postgres compatibility not 100% |
| DBOS only | DBOS runs on Postgres; this ADR covers the Postgres layer beneath DBOS |
| EventStoreDB | Separate operational footprint; Postgres handles both relational and event-sourcing needs |

---

## References

- DBOS: Stonebraker, Zaharia, Madden (MIT/Stanford) — dbos.dev
- Letta / Amazon Aurora Postgres case study — aws.amazon.com
- Marten event sourcing on Postgres — martendb.io
- pgvectorscale — github.com/timescale/pgvectorscale
- pg_ivm — github.com/sraoss/pg_ivm
