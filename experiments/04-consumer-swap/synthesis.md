---
status: review
stage: "02-analysis"
operator_approved: false
risk_check_passed: false
risk_tier: "Medium"
domain: "architecture"
date: "2026-05-27"
---

# Synthesis: PostgreSQL as Personal-Scale AI Substrate

## Core claim

A single PostgreSQL instance can serve as state kernel, durable workflow engine, vector index, event log, and audit ledger for a personal-scale AI workspace — eliminating the Redis/Kafka/EventStore/Temporal/vector-DB sprawl that defines current production agent systems. The substitution is justified on consolidated operational footprint, single backup surface, and adequate per-component performance below the personal-scale ceiling (~10⁸ vectors, ~50K write-tx/s).

## Evidence map

| Sub-claim | Supporting | Refuting |
|---|---|---|
| Durable workflows | DBOS (Stonebraker et al., 2024) | — |
| Vector search at scale | pgvector + pgvectorscale (Timescale, 2024) | Yamashita et al. (2025) cliff at 1.2×10⁸ |
| Event sourcing | Marten production deployments | — |
| Agent memory + audit | Letta on Aurora (42 tables, `block_history`) | — |
| Throughput | — | Stonebraker (VLDB 2023): 50K write-tx/s single-node ceiling |

## Integrated findings

The four positive sources are independent of each other — different teams, different problem framings, different stacks — yet each demonstrates production-grade viability of one of the four capabilities the workspace requires. The convergence is the integrating signal: there's no theoretical reason these four capabilities should compose on the same substrate, but the empirical record shows they do at single-node scale.

The "Postgres for everything at personal scale" thesis is therefore not novel architecture — it's recognition that the per-component evidence already exists and was simply distributed across four communities. The contribution is the synthesis, not the components.

## Counter-argument

**Yamashita et al. (2025), "Vector Search at Scale: Why Postgres Falls Off the Cliff,"** SIGMOD 2025 documents a 97% query-latency regression in pgvector HNSW indexes beyond 1.2 × 10⁸ vectors. Specifically: 96 GB RAM / 32 vCPU commodity hardware regresses from sub-200 ms p99 to 4-7 second p99. Dedicated vector databases (Pinecone, Weaviate, Qdrant) maintain sub-200 ms throughout this range.

This is not a fatal counter-argument to the thesis as stated — the workspace explicitly bounds itself at personal scale, and 1.2 × 10⁸ vectors corresponds to roughly **2 million pages of text** per user. No personal workspace approaches this. But the cliff is sharp enough that the thesis must explicitly name the boundary: **the Postgres-as-everything substrate is correct below 10⁸ vectors and 50K write-tx/s, and incorrect above either threshold.**

Stonebraker's own VLDB 2023 keynote reinforces this. The 50K-write-tx/s single-node ceiling is irrelevant at personal scale (where peak load is ~10 tx/s) but disqualifying for multi-tenant SaaS deployments. The thesis remains scoped, not universal.

A weaker but still material counter-argument: CRDT-on-Postgres remains an unsolved problem at the row level. ADR-002 documents the workaround (CRDT documents as `bytea` blobs with application-layer merge logic) but this is genuinely outside Postgres' core competence. A workspace that prioritizes real-time multi-writer collaboration over the other four capabilities might choose a CRDT-native substrate (Automerge sync server, Liveblocks) and accept the operational fragmentation.

## Recommendations

1. **Adopt PostgreSQL as the unified substrate (ADR-001 stands).** The decision is well-supported by four independent production precedents.
2. **Encode the scale boundary as an explicit re-evaluation trigger.** Add to the risk register: "If indexed vectors approach 10⁷ (10% of the cliff), revisit the vector-DB decision before reaching 10⁸." Same for write-tx/s with a 5K trigger.
3. **Treat CRDT collaboration as out-of-scope for v0.1.** ADR-002 documents the workaround; real-time multi-writer is a future ADR if the workspace ever needs it.
4. **Set `risk_tier: Medium`.** The decision is reversible (a future migration to a polyglot stack is possible if scale demands it), but it has external dependencies on Postgres extensions (pgvector, pgvectorscale, pg_cron, optionally DBOS) that must be maintained.

---

*Stage 02 synthesis artifact. Operator must set `operator_approved: true` and supply `risk_check_passed: true` (if escalating to High) before this can advance to Stage 03.*
