# Explanation: Design Decisions in the Stage 1 Buildability Proof

Four decisions in this proof are non-obvious and load-bearing. Each one is a trade — naming the trade is the point of this document.

---

## Why each step is its own database transaction

### The problem

A workflow that wraps all three steps (ingest → gate → receipt) in one transaction has a clean failure model: any error rolls everything back, leaving no partial state. That's also its problem. A crash mid-Step-3 throws away the Step-1 ingestion and the Step-2 gate decision. Re-running the workflow re-executes everything, which means: re-reading the artifact, re-validating the gate, and — if the workflow had any side effects (LLM calls, MCP tool invocations, real money) — double-spending them.

### The approach

Each step opens, writes, and commits its own transaction. The transaction boundary is the durability boundary. A `kill -9` between Step 2's `commit()` and Step 3's `INSERT INTO provenance_log` leaves Step 2 permanently committed and Step 3 simply un-run. A resume worker (not yet implemented in this proof) can look at `workflow_events`, see the last `passed` step for a `workflow_run_id`, and restart from the next one without re-executing what's already done.

This is the *workflow-activity discipline* called out in ADR-005. Each step is, at minimum, idempotent at the database level: re-inserting the same `receipt_id` is a no-op thanks to `ON CONFLICT (receipt_id) DO NOTHING` on `provenance_log`.

### Trade-offs

- **Storage:** every step writes a row to `workflow_events`. A three-step workflow that processes 10K artifacts/day produces 30K rows/day in `workflow_events` alone. At 100 bytes/row that's 3 MB/day, ~1 GB/year — fine at personal scale, requires a retention policy at SaaS scale.
- **Atomicity is now your problem.** "All three steps succeeded or none did" is no longer a property the database guarantees. The reader of `workflow_events` is responsible for reconstructing logical run state.
- **Two crashes are bad.** A crash between Steps 1 and 2 followed by a crash between Steps 2 and 3 of the resume run is recoverable; a crash *during* Step 2's commit is the classic two-generals problem and the resume worker must handle the duplicate-key conflict on the receipt insert. ON CONFLICT covers Step 3; Step 2's gate is pure and re-executing it is safe.

### Alternatives considered

- **One large transaction.** Rejected for the reason above: loses all progress on any failure.
- **DBOS-managed durable execution.** This is what `dbos>=1.0.0` in `requirements.txt` was added for, and it would handle the resume-worker logic for us. The proof does not yet use it — see the next section.
- **Saga pattern with compensating actions.** Overkill at Stage 0 (the only side effects so far are the receipt writes themselves, and those are idempotent by key).

---

## The DBOS gap

### The problem

The repo's README and CLAUDE.md describe a "DBOS workflow" as the Stage 1 buildability proof. `requirements.txt` lists `dbos>=1.0.0`. A reader reasonably expects `workflow.py` to import `dbos` and use its `@workflow` / `@transaction` decorators.

It doesn't. `workflow.py` uses raw `psycopg2`, manages connections by hand, and commits transactions manually with `conn.commit()`. The word `dbos` appears nowhere in the source.

### The approach

The proof demonstrates *the pattern DBOS encodes* — step-as-transaction, durable event log, idempotent activity writes — using the lowest-friction substrate (`psycopg2` + raw SQL). The honest claim is: *this is what a DBOS workflow would look like at the SQL layer, and the same Postgres tables (`workflow_events`, `provenance_log`) are the substrate DBOS itself runs on top of.*

The gap matters because:

1. **Replay is not implemented.** DBOS's value-add is automatic resume from the last committed step. The proof commits durably, but there is no resume worker. A real `dbos`-based rewrite gets resume for free.
2. **Determinism is unenforced.** ADR-005 requires the workflow layer to be pure (no `datetime.now()`, no `uuid.uuid4()`, no network calls outside activities). `workflow.py` violates this — it calls `datetime.now(timezone.utc)` and `uuid.uuid4()` inside the workflow body. A `dbos`-based rewrite would put these inside `@step`-wrapped activities so they replay deterministically.
3. **Activity wrapping is missing.** Steps 1 and 3 do file I/O directly from workflow code rather than through an idempotent activity. A `dbos` rewrite would wrap `Path.read_text` and `Path.write_text` as activities with idempotency keys.

### Trade-offs

- **What's proven:** the *database substrate* (Postgres + the two tables + the receipt schema) works end-to-end with step-level durability. That's the load-bearing claim for ADR-001.
- **What's not yet proven:** the *workflow engine* (DBOS-managed replay, deterministic workflow layer, idempotent activity wrappers). That's the load-bearing claim for ADR-005 and remains TODO.

The right next step is to port `workflow.py` to use `dbos` decorators. That's a contained refactor (~50 lines) that turns the proof into a real implementation of both ADRs.

---

## Why dual-write the receipt (Postgres + filesystem)

### The problem

A receipt has two audiences. Operators read it as part of normal git review — they expect markdown/JSON files in the worktree, diffable, blameable, reviewable in a PR. Auditors and downstream tooling read it as queryable structured data — they expect `SELECT ... FROM provenance_log WHERE ...`. Picking one writes off the other.

### The approach

Write both. Postgres holds the integrity anchor (`pg_receipt_hash`) and the queryable JSONB body. The filesystem holds the human-readable artifact at a deterministic path (`stages/<stage>/output/receipts/<ts>.json`).

The two writes happen in the same Step 3 transaction. If the filesystem write fails (disk full, permission denied), the transaction commits anyway because filesystem writes can't participate in the database transaction. The receipt-in-Postgres is the source of truth; the filesystem copy is a derived artifact. A future `gbrain export` or a simple `psql -c 'SELECT receipt_json FROM provenance_log...' > <path>` can rebuild the filesystem copy from Postgres at any time.

### Trade-offs

- **Storage:** every receipt exists twice. At Stage 0 receipt size (~1 KB) this is negligible.
- **Drift risk:** a future hand-edit of the filesystem JSON won't update Postgres. The `pg_receipt_hash` won't notice (it was computed at write time). Operators must treat filesystem receipts as read-only — and CI should re-derive them from Postgres to detect drift. Not yet implemented.
- **Atomicity:** as noted, filesystem and Postgres are not jointly atomic. A crash between the `write_text` and the `conn.commit()` leaves a receipt file with no Postgres row. The resume worker would need to either (a) re-write the file with the same content (idempotent thanks to the deterministic timestamp path) or (b) reconcile orphan files via `find`. Neither is wired.

---

## Why gate logic is duplicated in `ingester.assert_approved` and `_config/stage-contract.py`

### The problem

`_config/stage-contract.py` is the canonical gate validator for the whole pipeline. It's also a large file with imports that pull in YAML schemas, frontmatter validators, and helper code for every stage. The buildability proof needs to run standalone — `cd proof/ && python workflow.py` — without coupling to the rest of the repo.

Importing `stage-contract.py` from `proof/` would either require (a) `sys.path` gymnastics that hurt the standalone story, or (b) a build step that copies the relevant chunk into `proof/`. Both are worse than the alternative.

### The approach

Duplicate the *gate_00* check (`operator_approved is True AND status == "approved"`) as a six-line function in `proof/ingester.py`. Document the duplication. Make staying-aligned a review-time check, not a runtime check.

### Trade-offs

- **Drift risk is real.** If `stage-contract.py` adds a new field to gate_00 (e.g., requiring a `risk_check_passed` field even for Stage 0), `ingester.assert_approved` will silently let it pass. The proof keeps committing receipts that wouldn't pass the real gate.
- **Mitigation:** `tests/test_ingester.py` and `tests/test_stage_contract.py` should share fixtures (they already do — both use `tests/fixtures/approved.md` and `unapproved.md` via `conftest.py`). When stage-contract's gate_00 changes, a fixture update breaks both test files; the proof's failure is the early signal.
- **Better long-term fix:** extract the gate-check predicate into a tiny zero-dependency module (e.g., `_config/gates.py`) that both `stage-contract.py` and `proof/ingester.py` import. ~30 lines of refactor; not yet done.

---

## What you should take away

- The proof is honest about what it proves: the *substrate* (Postgres tables, transaction-per-step, receipt schema) works. The *workflow engine* (DBOS-managed replay, deterministic-workflow / idempotent-activity discipline) is the next step.
- Every design decision in `workflow.py` has a documented next-step that closes the gap. None of them are blocked on architectural ambiguity — they're scheduled work.
- The two ADRs this proof targets — ADR-001 (Postgres as state kernel) and ADR-005 (Temporal/DBOS workflow-activity split) — get partial credit. ADR-001 is fully demonstrated; ADR-005 has its discipline encoded by hand but not enforced by an engine.
