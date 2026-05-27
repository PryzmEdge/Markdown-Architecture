# Tutorial: Run the Stage 1 Buildability Proof End-to-End

You'll start a Postgres database, apply the proof schema, run the workflow against the test fixture, and see a `PromptExecutionReceipt` land in two places (Postgres and the filesystem). End state: you've validated all four claims the proof makes, in under five minutes.

## What you'll need

- Docker (to run Postgres without installing it system-wide)
- Python 3.12+ with `pip`
- This repo, with the working directory at the repo root

If you don't have Docker, swap the `docker run` step for a local Postgres 15+ that exposes port 5432 and the `markdown_arch` database, then continue.

## Step 1: Start Postgres and install dependencies

```bash
docker run -d \
  --name ma-postgres \
  -e POSTGRES_PASSWORD=ma_dev \
  -e POSTGRES_USER=ma \
  -e POSTGRES_DB=markdown_arch \
  -p 5432:5432 \
  postgres:15

pip install -r proof/requirements.txt
```

The container takes 3-5 seconds to accept connections. If the next step errors with `could not connect`, wait two seconds and retry.

## Step 2: Apply the schema

```bash
psql postgresql://ma:ma_dev@localhost:5432/markdown_arch -f proof/schema.sql
```

Two tables get created: `workflow_events` (append-only step log) and `provenance_log` (one row per receipt). Re-running this step is safe — both `CREATE TABLE` statements use `IF NOT EXISTS`.

## Step 3: Run the workflow against the test fixture

```bash
python proof/workflow.py \
  --problem tests/fixtures/approved.md \
  --operator tutorial-user
```

You'll see three step-status lines, then a JSON summary. Successful output looks like:

```
[step 1/3] Ingesting artifact...
  hash: 8b3c4e2f1a9d5b6c...
  status: approved
  operator_approved: True
  ✓ Step 1 committed.
[step 2/3] Running gate_00 validation...
  ✓ Step 2 committed. Gate passed.
[step 3/3] Writing PromptExecutionReceipt...
  ✓ Receipt written: stages/00-intake/output/receipts/20260527T034512Z.json
  ✓ pg_receipt_hash:  9a2b1c8d7e6f5a4b...
  ✓ Step 3 committed.

[workflow] Complete. run_id=<uuid>

{
  "run_id": "...",
  "receipt_id": "...",
  "receipt_path": "stages/00-intake/output/receipts/20260527T034512Z.json",
  "pg_hash": "..."
}
```

That's the proof working. Each `✓ Step N committed.` line is a Postgres `COMMIT` that survives a process crash — Step 4 demonstrates it.

## Step 4 (optional): See the receipt in both places

```bash
# Filesystem
cat stages/00-intake/output/receipts/*.json | head -30

# Postgres
psql postgresql://ma:ma_dev@localhost:5432/markdown_arch \
  -c "SELECT receipt_id, stage_id, operator_id, pg_receipt_hash \
      FROM provenance_log ORDER BY created_at DESC LIMIT 1;"
```

Both show the same `receipt_id`. The `pg_receipt_hash` is `SHA-256(receipt_json)` — recompute it client-side if you want to verify the JSONB row hasn't drifted from the file.

## What you built

A working three-step durable workflow that:

- Reads a Markdown artifact and parses its YAML frontmatter (`proof/ingester.py`).
- Validates the `operator_approved: true` gate, mirroring `_config/stage-contract.py`'s `gate_00` (`assert_approved`).
- Emits a `PromptExecutionReceipt` to both Postgres (`provenance_log`) and the filesystem (`stages/00-intake/output/receipts/<ts>.json`).
- Commits each step in its own database transaction — kill the process between any two steps and the committed work survives. (Automatic resume from the last committed step is the planned next step but isn't wired yet — see `proof/explanation.md` § "The DBOS gap".) `proof/howto.md` walks through verifying durability.

Next:

- **`proof/howto.md`** — query the receipt log, verify crash recovery, run the workflow against an unapproved artifact (and watch the gate block it).
- **`proof/reference.md`** — full CLI / env-var / table / receipt-schema reference.
- **`proof/explanation.md`** — why each step is its own transaction, what's actually proven vs. what the README claims, the DBOS-package gap.

To tear down between runs:

```bash
docker rm -f ma-postgres
rm -rf stages/00-intake/output/receipts/
```
