# How-To Guides for the Stage 1 Buildability Proof

Three tasks. Each one assumes you've completed `proof/tutorial.md` — Postgres is running, the schema is applied, and at least one workflow run has produced a receipt.

---

## How to query the provenance log

When you need to audit what ran, who approved it, or verify a receipt hash.

**Prerequisites:** Postgres reachable at `$DATABASE_URL` (default `postgresql://ma:ma_dev@localhost:5432/markdown_arch`). At least one receipt in `provenance_log`.

### Steps

1. List the last 10 receipts with the human-readable fields:

   ```bash
   psql "$DATABASE_URL" -c "
     SELECT
       to_char(created_at, 'YYYY-MM-DD HH24:MI:SS') AS at,
       stage_id,
       operator_id,
       left(pg_receipt_hash, 16) AS hash_prefix,
       receipt_id
     FROM provenance_log
     ORDER BY created_at DESC
     LIMIT 10;
   "
   ```

2. Inspect the full JSONB body of a specific receipt:

   ```bash
   psql "$DATABASE_URL" -c "
     SELECT jsonb_pretty(receipt_json)
     FROM provenance_log
     WHERE receipt_id = '<paste-receipt-id-here>';
   "
   ```

3. Re-verify the integrity hash against the stored JSON:

   ```bash
   psql "$DATABASE_URL" -tA -c "
     SELECT receipt_json::text
     FROM provenance_log
     WHERE receipt_id = '<receipt-id>';
   " | python3 -c "
   import sys, hashlib, json
   raw = sys.stdin.read()
   parsed = json.loads(raw)
   print(hashlib.sha256(json.dumps(parsed, indent=2).encode()).hexdigest())
   "
   ```

   Compare the output to the `pg_receipt_hash` column. They will match only if the JSON round-trip preserves the exact same indentation as `proof/workflow.py`'s `build_receipt` — see `proof/explanation.md` for the rationale and a known caveat.

### Verification

Step 1 returns at least one row. Step 2 returns a valid JSON object with the `receipt_id`, `timestamp`, `workflow_run_id`, `stage_id`, and `operator_signoff` fields populated.

### Troubleshooting

- **`relation "provenance_log" does not exist`** — schema isn't applied. Re-run `psql ... -f proof/schema.sql`.
- **`could not connect`** — Docker container is stopped. `docker start ma-postgres` then wait two seconds.
- **Hash mismatch in step 3** — almost always the JSON-indent caveat. The hash in `pg_receipt_hash` was computed from `json.dumps(receipt, indent=2)` at write time; if you reformat or re-dump with different `indent` / `sort_keys` settings you'll get a different SHA-256. Use the raw `receipt_json::text` only.

---

## How to verify crash recovery

When you need to confirm that a process crash between steps doesn't lose work or double-execute.

**Prerequisites:** Same as above. You'll need a second terminal.

### Steps

1. In terminal A, count the rows currently in `workflow_events`:

   ```bash
   psql "$DATABASE_URL" -tAc "SELECT count(*) FROM workflow_events;"
   ```

   Note the number. Call it `N`.

2. In terminal B, start a workflow run and immediately kill it after Step 1 commits:

   ```bash
   python proof/workflow.py \
     --problem tests/fixtures/approved.md \
     --operator crash-test &
   WORKFLOW_PID=$!
   sleep 0.5      # let Step 1 ingest and commit
   kill -9 $WORKFLOW_PID
   ```

3. In terminal A, re-check the row count and inspect the run state:

   ```bash
   psql "$DATABASE_URL" -c "
     SELECT step_name, status, payload
     FROM workflow_events
     ORDER BY id DESC
     LIMIT 3;
   "
   ```

   You should see exactly one new row: `step_name=ingest`, `status=passed`. Steps 2 and 3 never ran, but Step 1's commit survived the `kill -9`.

4. Inspect what's missing: no row for `gate_00`, no row for `receipt`, and no file in `stages/00-intake/output/receipts/` newer than the timestamp from step 2.

### Verification

`workflow_events` has exactly `N + 1` rows after the kill. `provenance_log` row count is unchanged. The receipt directory has no new files.

### Troubleshooting

- **Two new `workflow_events` rows instead of one** — `sleep 0.5` was too long; Step 2 also committed before the kill. Lower the sleep to `0.2` and retry.
- **Zero new rows** — the kill landed before Step 1's `commit()`. The transaction rolled back. Increase the sleep to `1.0` and retry.
- **The proof does not currently re-execute the workflow from the last committed step automatically.** Resume semantics are documented as the *next* step on the DBOS gap path; see `proof/explanation.md` § "The DBOS gap". The current proof demonstrates that each step's commit is durable; it does not yet wire up the resume worker.

---

## How to run against an unapproved artifact

When you need to confirm the gate blocks promotion.

**Prerequisites:** Same as above. Uses `tests/fixtures/unapproved.md`, which has `operator_approved: false`.

### Steps

1. Run the workflow against the unapproved fixture:

   ```bash
   python proof/workflow.py \
     --problem tests/fixtures/unapproved.md \
     --operator gate-test
   echo "exit=$?"
   ```

2. Confirm the gate blocked the run:

   ```bash
   psql "$DATABASE_URL" -c "
     SELECT step_name, status, payload->>'error' AS error
     FROM workflow_events
     WHERE step_name = 'gate_00'
     ORDER BY id DESC LIMIT 1;
   "
   ```

3. Confirm no receipt was written:

   ```bash
   psql "$DATABASE_URL" -tAc "
     SELECT count(*) FROM provenance_log
     WHERE operator_id = 'gate-test';
   "
   ```

### Verification

Step 1 prints `✗ Step 2 gate blocked: ...` and the shell shows `exit=1`. Step 2 returns a single row with `status=blocked` and an error mentioning `operator_approved`. Step 3 returns `0` — the receipt path never executed.

### Troubleshooting

- **Gate passes when it shouldn't** — the fixture was modified. Re-fetch from git: `git checkout tests/fixtures/unapproved.md`.
- **Step 1 fails before reaching the gate** — frontmatter is malformed (not the same as unapproved). Check `tests/fixtures/unapproved.md` parses as valid YAML between the `---` markers.
