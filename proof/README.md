# Stage 1 Buildability Proof

A minimal working prototype that validates the core claims of the Markdown Architecture pipeline: a durable, step-per-transaction workflow that ingests a Markdown artifact, runs a gate validation, and emits a `PromptExecutionReceipt` to both Postgres and the filesystem.

## What it proves

1. The database substrate (Postgres + `workflow_events` + `provenance_log`) supports step-per-transaction durability end-to-end.
2. Gate validation (`operator_approved: true`) runs inside a durable transaction and writes a `blocked` event when it fails.
3. A `PromptExecutionReceipt` is dual-written to Postgres (`provenance_log`) and the filesystem (`stages/<stage>/output/receipts/<ts>.json`) with a `SHA-256` integrity anchor.
4. A crash between any two committed steps leaves the database in a consistent partial state from which a resume worker *could* re-run the missing steps. The resume worker itself is not yet wired — see `explanation.md` § "The DBOS gap".

## Documentation (Diataxis)

| Doc | Audience | When to read |
|---|---|---|
| [`tutorial.md`](tutorial.md) | First-time operator | You want to run the proof end-to-end and see a green receipt in ≤5 minutes. |
| [`howto.md`](howto.md) | Operator with the proof already running | You want to query the receipt log, verify crash recovery, or watch the gate block an unapproved artifact. |
| [`reference.md`](reference.md) | Anyone building on the proof | Complete CLI / env-var / Python-API / SQL-schema / receipt-schema surface. |
| [`explanation.md`](explanation.md) | Architect / reviewer | Why each step is its own transaction, the gap between "DBOS workflow" claim and the raw-`psycopg2` implementation, why receipts are dual-written, why gate logic is duplicated. |

## Files

| File | Purpose |
|---|---|
| `schema.sql` | Postgres tables: `workflow_events`, `provenance_log` |
| `workflow.py` | Three-step durable workflow: ingest → validate → emit receipt |
| `ingester.py` | Markdown artifact reader and frontmatter parser |
| `requirements.txt` | Python dependencies (`dbos` listed but not yet used — see `explanation.md`) |

## Stack

Python 3.12+, `psycopg2-binary`, `pyyaml`, PostgreSQL 15+ (Docker recipe in `tutorial.md`). `dbos>=1.0.0` is listed in requirements for the planned next step but is not yet imported.

## Related ADRs

- [ADR-001](../docs/adr/ADR-001-postgres-state-kernel.md) — PostgreSQL as state kernel and provenance ledger. Fully demonstrated by this proof.
- [ADR-005](../docs/adr/ADR-005-temporal-dbos-workflow-split.md) — Temporal/DBOS workflow-activity split. Discipline encoded by hand; engine not yet wired.
