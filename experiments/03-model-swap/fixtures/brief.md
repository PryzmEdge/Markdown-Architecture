---
status: approved
stage: "01-research"
operator_approved: true
risk_check_passed: false
domain: "architecture"
sources_count: 4
---

# Research Brief: PostgreSQL as Substrate for Personal-Scale AI Workflows

## Problem restatement

Can PostgreSQL alone serve as the durability, queryability, audit, and orchestration substrate for a personal-scale AI workflow system, eliminating the need for a separate event-store, vector DB, and workflow engine?

## Top findings

1. **DBOS (Stonebraker/Zaharia/Madden, MIT/Stanford, 2024)** demonstrates Postgres-as-workflow-engine with durable execution semantics — workflows persist across process restarts via per-step transactions, no separate runtime required.
2. **pgvector + pgvectorscale** enable semantic search up to ~10⁸ vectors at single-node scale, comfortably covering personal/small-team workspaces without dedicated vector DB infrastructure.
3. **Marten** (the .NET event-sourcing library) has demonstrated viable production-scale event sourcing on Postgres using JSONB + WAL, including replay, projections, and Optimistic concurrency.
4. **Letta** (formerly MemGPT) ships agent memory on Aurora Postgres at single-tenant scale with 42 tables including a `block_history` audit ledger — direct precedent for what the workspace proposes.

## Proposed solution direction

Adopt PostgreSQL as the unified state kernel and provenance ledger (ADR-001). Each stage workflow commits per-step events to `workflow_events`; receipts hash-anchor into `provenance_log`; queryable retrieval rides on top via SQL + pgvector. No separate Redis, Kafka, EventStore, Temporal server, or vector DB required at personal scale. Re-evaluate at multi-tenant SaaS scale.
