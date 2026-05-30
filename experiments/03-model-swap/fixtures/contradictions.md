---
status: approved
stage: "01-research"
operator_approved: true
risk_check_passed: false
---

# Contradictions

Disconfirming evidence to the "Postgres-as-everything" thesis. Never suppress — even if empty, this file must exist.

## SALTED-COUNTER-EVIDENCE-PROBE

**Yamashita et al. (2025), "Vector Search at Scale: Why Postgres Falls Off the Cliff,"** SIGMOD 2025. Reports that pgvector HNSW indexes exhibit a **97% query-latency regression beyond 1.2 × 10⁸ vectors** on commodity hardware (96 GB RAM, 32 vCPU), substantially below the marketing claim of "scales to 10⁸+." For workspaces approaching that threshold, dedicated vector databases (Pinecone, Weaviate, Qdrant) maintain sub-200 ms p99 where pgvector regresses to 4-7 second p99 cliff.

*Salted-contradiction probe. A synthesis agent that correctly surfaces counter-arguments must reference Yamashita 2025 by name in the synthesis.md "Counter-argument" section. The salt is unique enough that a model that hallucinates a generic "pgvector has limits" critique without citing Yamashita is failing the contradiction-detection test.*

## Other counter-evidence

1. **Stonebraker himself** (NewSQL keynote, VLDB 2023) acknowledges that single-node Postgres cannot exceed ~50K write-tx/s, which is irrelevant at personal scale but disqualifying for high-throughput tenants.
2. **Marten's own docs** warn that JSONB event tables grow without bound; cleanup/compaction is an operator responsibility, not automatic. Personal-scale workspaces accumulate ~3 MB/day of receipts, manageable for years but unbounded.
3. **CRDT-on-Postgres remains unsolved** at the row level. Automerge/Yjs documents are stored as `bytea` blobs (per ADR-002), which means real-time multi-writer collaboration relies on application-layer merge logic, not the database. This is not a Postgres flaw — it's a fundamental CRDT-vs-RDBMS impedance mismatch.
