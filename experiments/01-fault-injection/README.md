# Experiment 01 — Fault Injection on `proof/workflow.py`

Tests the strict four-state invariant that follows from the workspace's core thesis (`docs/v10-draft.md`) and ADR-005 (workflow-activity discipline).

## Hypothesis

After a `kill -9` at any timing, the database lands in exactly one of four states:

- `empty` — no rows in `workflow_events`, no rows in `provenance_log`
- `ingest` — one event (`ingest, passed`), no receipt
- `gate` — two events (`ingest, passed`, `gate_00, passed`), no receipt
- `complete` — three events (`ingest, passed`, `gate_00, passed`, `receipt, passed`) and exactly one row in `provenance_log`

Any run that lands outside these four states falsifies the implementation. The thesis predicts: 0% UNEXPECTED.

## Method

`harness.py` spawns `proof/workflow.py` as a subprocess against `tests/fixtures/approved.md`, sleeps a uniformly-random delay sampled from a configurable range, then sends `SIGKILL`. After all iterations, the harness classifies the terminal state for each `workflow_run_id` against the four expected sequences.

```
spawn → sleep(Uniform[delay_min, delay_max]) → SIGKILL → wait → classify
```

The fixture (`tests/fixtures/approved.md`) is the standard approved Stage 00 artifact.

## Running

```bash
# Postgres must be reachable at DATABASE_URL (default: postgresql://ma:ma_dev@localhost:5432/markdown_arch)
# Schema must be applied (psql -f proof/schema.sql)

pip install --user psycopg2-binary

python3 experiments/01-fault-injection/harness.py \
  --iterations 200 --reset \
  --delay-min 0.050 --delay-max 0.200 \
  --seed 42
```

`--reset` truncates `workflow_events` and `provenance_log` first. `--seed` makes the delay distribution reproducible. Output JSON lands in `results/`.

## Calibrating the delay range

`proof/workflow.py` is roughly 125 ms end-to-end on a warm Postgres. Of that, about 50-80 ms is Python interpreter + import + connect overhead, before the first DB write. A `--delay-min` below 50 ms produces mostly `empty` runs (kill during startup); a `--delay-max` above 200 ms produces mostly `complete` runs (kill after the workflow has already finished).

To exercise all four states, target a delay range that brackets the 50-200 ms execution window. Push narrower if you want more mid-workflow samples; push wider if you want to characterize the natural distribution of where kills land.

## Results

Run: `seed=42`, `delay=[0.050s, 0.200s]`, `iterations=200`. Full JSON: [`results/fault-injection-final.json`](results/fault-injection-final.json).

| State | Count | % | Interpretation |
|---|---:|---:|---|
| `empty` | 74 | 37.0% | killed during Python startup, before any DB write |
| `ingest` | 4 | 2.0% | killed between Step 1 commit and Step 2 commit |
| `gate` | 2 | 1.0% | killed between Step 2 commit and Step 3 commit |
| `complete` | 120 | 60.0% | workflow finished cleanly before the kill landed |
| **UNEXPECTED** | **0** | **0.0%** | — |

## Verdict

**PASS.** 200/200 runs land in the expected four-state space. The four-state invariant holds across the full kill-timing distribution.

Specifically: no run produced an event with `status` other than `passed` (which would mean the workflow was somehow killed *during* the `INSERT INTO workflow_events ... VALUES (... 'passed' ...)` statement but Postgres still committed the row — this would be a Postgres atomicity failure, not a workflow bug). No run produced a `provenance_log` row without its matching `receipt, passed` event. No run produced more events than the workflow ever issues.

## What this proves and what it doesn't

**Proves:** The step-per-transaction discipline described in `proof/explanation.md` § "Why each step is its own database transaction" works as advertised. Database atomicity around each `conn.commit()` is sufficient for the four-state invariant.

**Does NOT prove:** Replay determinism (Experiment 02 tests this — and is expected to fail). The `complete` state subsumes any further structural issues with the receipt's body. Two `complete` runs can have differently-shaped receipts.

**Does NOT prove:** The proof recovers from a kill. There is no resume worker; this experiment only confirms the durability boundary. A resume worker that picked up after `ingest` and ran Steps 2-3 from there is the next piece of work, and `proof/explanation.md` § "The DBOS gap" describes the path.

## Caveats

- The fixture is trivial (a 10-line approved markdown file). Real Stage 00 artifacts will have longer ingest times, which shifts the distribution toward `ingest` and `gate` for the same delay range. This is a feature: it lets longer-running workflows be tested with the same harness by leaving `--delay-max` constant.
- Only one fixture (`tests/fixtures/approved.md`). Malformed YAML or missing files trigger different failure paths (Steps 1 or 2 raise IngesterError, which the workflow catches and writes a `failed` or `blocked` event for). Those paths aren't in the four-state space defined here because they end the run before reaching Step 3 — they're worth their own experiment.
- The harness assumes nothing else is writing to `workflow_events` concurrently. `--reset` clears the tables, and the harness tracks `baseline_id` so a fresh run is identifiable. Concurrent harnesses against the same DB will conflate runs.

## Files

| File | Purpose |
|---|---|
| `harness.py` | Subprocess runner + classifier + reporter |
| `README.md` | This file |
| `results/fault-injection-final.json` | Per-run classifications and distribution from the calibrated run |
