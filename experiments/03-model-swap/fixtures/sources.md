---
status: approved
stage: "01-research"
operator_approved: true
risk_check_passed: false
sources_count: 4
---

# Sources

| Source | Claim | Quality | Relevance | Citation |
|---|---|---|---|---|
| DBOS docs | Postgres-native durable workflows; per-step transactions; replay from event log | Primary | High | Stonebraker, Zaharia, Madden (2024). DBOS: A Database-Oriented Operating System. dbos.dev |
| pgvector benchmarks (Timescale, 2024) | HNSW indexes scale to 10⁸ vectors with sub-100 ms query latency on a single Postgres node | Secondary | High | Timescale Labs (2024). pgvectorscale benchmarks. github.com/timescale/pgvectorscale |
| Marten docs | Event sourcing on Postgres JSONB; production-tested at single-tenant scale | Secondary | Medium | Marten DB (2024). Event sourcing patterns. martendb.io |
| Letta architecture deep-dive | Agent memory on Aurora Postgres; 42 tables; `block_history` audit ledger; production multi-tenant | Secondary | High | Letta (formerly MemGPT) on Amazon Aurora (2024). aws.amazon.com case study |
