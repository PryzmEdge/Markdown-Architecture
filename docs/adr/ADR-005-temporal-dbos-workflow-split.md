# ADR-005 — Temporal/DBOS Workflow-Activity Split for Durable Governance

| Field | Value |
|---|---|
| ID | ADR-005 |
| Status | Accepted |
| Date | 2026-05-23 |
| Deciders | PryzmEdge |
| Supersedes | — |
| Superseded by | — |

---

## Context

The system requires durable, auditable orchestration of multi-step AI workflows where individual steps may fail, be retried, or require human approval. Two failure modes must be handled:

1. **Infrastructure failure** (process crash, OOM, network partition): the workflow must resume from the last committed checkpoint without re-executing completed steps.
2. **Application failure** (LLM returns invalid output, tool call fails, lattice policy violation): the workflow must route to a validator gate or kill-switch rather than silently continuing.

Earlier versions of this document did not distinguish between deterministic workflow logic and non-deterministic side effects. The critical architecture review identified this as a gap: without the deterministic/activity split, replay semantics are undefined and audit receipts cannot guarantee completeness.

---

## Decision

Adopt the **Temporal/DBOS workflow-activity discipline** for all multi-step AI workflows:

**Workflow layer (deterministic — must be replayable):**
- Pure functions over event-log state.
- Validator gates, kill-switch logic, capacity checks, lattice policy enforcement.
- Stage transitions and approval gates.
- No direct I/O; no clocks; no RNG; no network calls.
- Must produce identical results when replayed from the same event log.

**Activity layer (non-deterministic — wrapped, idempotent, retried):**
- LLM API calls.
- MCP tool invocations.
- External network I/O (data feeds, broker APIs).
- File system writes (markdown artifact outputs).
- Each activity is:
  - Wrapped with an idempotency key.
  - Retried with exponential backoff up to a configured limit.
  - Logged as an immutable event on completion or failure.

**Design rule:** *Workflows decide; activities act.*

**Implementation options (in order of preference):**
1. **DBOS** (dbos.dev) — Postgres-native durable workflow; aligns directly with ADR-001.
2. **Temporal** (temporal.io) — battle-tested durable workflow; requires separate Temporal server (Postgres or MySQL backend).
3. **LangGraph + Postgres checkpointer** — suitable for simpler agent graphs; checkpointers protect application-level failures (not infrastructure-level); combine with Temporal for full durability.

**Recommended for v0.1:** LangGraph + Postgres checkpointer for the agent layer, with DBOS or Temporal added when infrastructure-level replay is required.

---

## Consequences

**Positive:**
- Deterministic workflow layer makes validator gates and kill-switches formally auditable.
- Activity wrapping ensures every LLM call and tool invocation is logged and retryable.
- Event-log replay can reconstruct any workflow state from scratch (Marten-style).
- Aligns with the broader durable-workflow ecosystem (Temporal GA with OpenAI Agents SDK, March 2026).

**Negative / risks:**
- Workflow code must be strictly deterministic: no `datetime.now()`, no `random`, no direct network calls. Requires discipline and code review.
- DBOS is young (founded 2024); production stability should be re-assessed in 12 months.
- Temporal requires a separate server process (unless using Temporal Cloud).
- LangGraph checkpointers do not save state *inside* a node — only at node boundaries. Coarse granularity may miss mid-node failures.

**Mitigation:** enforce determinism via linting rules (no stdlib `random`, no `datetime.now()` outside activities). Use DBOS or Temporal for any workflow that crosses a stage gate or touches real capital.

---

## Enforcement checklist (before production)

- [ ] All validator gates live in workflow code (deterministic layer).
- [ ] All LLM calls are wrapped as activities with idempotency keys.
- [ ] All MCP tool invocations are wrapped as activities.
- [ ] All activities emit a `PromptExecutionReceipt` event on completion.
- [ ] Kill-switch can be triggered from workflow layer without executing further activities.
- [ ] Replay test: replay the event log of any production run and verify identical stage-gate decisions.

---

## Alternatives considered

| Alternative | Reason rejected |
|---|---|
| No workflow engine (raw async Python) | No replay semantics; no infrastructure-failure recovery; audit receipts not guaranteed |
| Celery / RQ | Task queues without replay semantics; no deterministic workflow layer |
| Prefect / Dagster | Strong for data pipelines; weaker on LLM-specific activity wrapping and Postgres-native state |
| Airflow | DAG-centric; not suited to dynamic agent graphs |
| Rebuild from scratch | TigerBeetle/FoundationDB-style DST requires single-threaded actor design from day one; too costly for v0.1 |

---

## References

- DBOS — dbos.dev; Stonebraker, Zaharia, Madden (MIT/Stanford)
- Temporal — temporal.io; OpenAI Agents SDK integration GA March 2026
- LangGraph 1.0 + Postgres checkpointer — github.com/langchain-ai/langgraph
- TigerBeetle VOPR — github.com/tigerbeetle/tigerbeetle
- FoundationDB simulation testing — foundationdb.org
- Antithesis — antithesis.com (ex-FoundationDB team; hypervisor-level DST)
