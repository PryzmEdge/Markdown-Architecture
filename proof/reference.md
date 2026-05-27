# Reference: Stage 1 Buildability Proof

Complete surface description. For end-to-end usage start with `proof/tutorial.md`; for task recipes see `proof/howto.md`; for design rationale see `proof/explanation.md`.

---

## CLI: `proof/workflow.py`

```
python proof/workflow.py [--problem PATH] [--operator NAME]
```

| Argument | Type | Default | Description |
|---|---|---|---|
| `--problem` | path | `stages/00-intake/output/problem.md` | Markdown artifact to ingest. Must exist, must have YAML frontmatter, must parse as UTF-8. |
| `--operator` | string | `operator` | Named human operator. Written verbatim into `provenance_log.operator_id` and the receipt's `operator_signoff.name` field. No validation. |

### Environment variables

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `postgresql://ma:ma_dev@localhost:5432/markdown_arch` | psycopg2-compatible Postgres DSN. Schema must be applied before the first run. |

### Exit codes

| Code | Meaning |
|---|---|
| `0` | All three steps committed; receipt written to Postgres and filesystem. |
| `1` | Any step failed. The failure is logged to `workflow_events` with `status=failed` (Steps 1/3) or `status=blocked` (Step 2 gate). Earlier steps remain committed. |

### Stdout contract

On success, the script prints (in order):
1. A header block with `run_id`, `artifact`, `operator`.
2. Three `[step N/3] ...` blocks, each ending with `✓ Step N committed.`
3. A `[workflow] Complete. run_id=<uuid>` line.
4. A JSON object with `run_id`, `receipt_id`, `receipt_path`, `pg_hash`.

On failure, the script prints the failed step's `✗ Step N ...` line and exits non-zero before reaching the JSON summary.

---

## Python API: `proof/ingester.py`

### `ingest(artifact_path: str) -> dict`

Read a Markdown file, parse YAML frontmatter, return a structured dict.

**Returns:**

```python
{
    "path":        str,    # the artifact_path argument, verbatim
    "hash_sha256": str,    # 64-char hex SHA-256 of the raw UTF-8 file bytes
    "frontmatter": dict,   # parsed YAML between the leading --- markers; {} if absent
    "body":        str,    # everything after the second ---, with leading/trailing whitespace stripped
}
```

**Raises** `IngesterError` if the file does not exist, frontmatter is opened with `---` but has no closing `---`, or the YAML is malformed.

**Permissive:** a file with no frontmatter at all (no leading `---`) returns `frontmatter={}` and the full content as `body`. Ingestion never enforces gate logic — that's `assert_approved`'s job.

### `assert_approved(artifact: dict) -> None`

Raise `IngesterError` if the ingested artifact is not operator-approved.

**Mirrors** `_config/stage-contract.py`'s `gate_00`. The two implementations must stay aligned; see `proof/explanation.md` § "Why gate logic is duplicated".

**Raises** `IngesterError` if `frontmatter["operator_approved"] is not True` (strict identity check — `1` or `"true"` do not pass) or `frontmatter["status"] != "approved"`.

### `class IngesterError(Exception)`

Raised by both `ingest` and `assert_approved`. Caught by `workflow.py` and logged as a `workflow_events` row with `status=failed` or `status=blocked` before the process exits non-zero.

---

## Postgres schema: `proof/schema.sql`

### Table: `workflow_events`

Append-only log of every step transition. Inserted by every step of `workflow.py`, regardless of outcome.

| Column | Type | Description |
|---|---|---|
| `id` | `BIGSERIAL PRIMARY KEY` | Monotonic insertion order. |
| `event_id` | `UUID DEFAULT gen_random_uuid()` | Stable identifier for this event row. |
| `workflow_run_id` | `TEXT NOT NULL` | UUID generated at the top of `run_workflow`; identical across all rows from one run. |
| `stage_id` | `TEXT NOT NULL` | Always `00-intake` in the current proof. |
| `step_name` | `TEXT NOT NULL` | One of `ingest`, `gate_00`, `receipt`. |
| `status` | `TEXT NOT NULL` | One of `started`, `passed`, `failed`, `blocked`. The proof writes `passed`, `failed`, `blocked` — `started` is reserved for a future pre-step write. |
| `payload` | `JSONB` | Step-specific data. `ingest`: `{path, hash}`. `gate_00`: gate-results dict or `{error, contract_passed}`. `receipt`: `{receipt_id, pg_hash}` or `{error}`. |
| `created_at` | `TIMESTAMPTZ DEFAULT now()` | Server-side wall-clock time at INSERT. |

**Index:** `idx_workflow_events_run` on `(workflow_run_id, created_at)` — supports per-run event timelines.

### Table: `provenance_log`

One row per `PromptExecutionReceipt`. Append-only by convention — never `UPDATE` or `DELETE` (enforced by reviewer discipline, not by trigger).

| Column | Type | Description |
|---|---|---|
| `id` | `BIGSERIAL PRIMARY KEY` | Monotonic insertion order. |
| `receipt_id` | `UUID NOT NULL UNIQUE` | The receipt's own UUID. The `UNIQUE` constraint + `ON CONFLICT DO NOTHING` makes re-runs idempotent. |
| `workflow_run_id` | `TEXT NOT NULL` | Joins back to `workflow_events.workflow_run_id`. |
| `stage_id` | `TEXT NOT NULL` | Stage the receipt was emitted for. |
| `operator_id` | `TEXT NOT NULL` | The `--operator` CLI argument from the run. |
| `pg_receipt_hash` | `TEXT NOT NULL` | `SHA-256(json.dumps(receipt, indent=2))`. Integrity anchor. |
| `receipt_json` | `JSONB NOT NULL` | Full receipt body, queryable. Storage cost ~2x but enables `WHERE receipt_json->>'agent_id' = ...` queries. |
| `created_at` | `TIMESTAMPTZ DEFAULT now()` | Server-side wall-clock time at INSERT. |

**Index:** `idx_provenance_log_stage` on `(stage_id, created_at)` — supports per-stage receipt timelines.

**Comment:** `'Append-only receipt ledger. Never UPDATE or DELETE rows. ADR-001.'`

---

## Receipt schema

The JSON object written to both `provenance_log.receipt_json` and `stages/<stage>/output/receipts/<ts>.json`.

```yaml
receipt_id:       str              # UUID4, also indexed in provenance_log.receipt_id
timestamp:        str              # ISO-8601 UTC, e.g. "2026-05-27T03:45:12.345678Z"
workflow_run_id:  str              # matches workflow_events.workflow_run_id
stage_id:         str              # e.g. "00-intake"
agent_id:         str              # currently hard-coded "buildability-proof-v1.0"
input_artifacts:                   # list of files this run consumed
  - path:         str
    hash_sha256:  str              # 64-char hex
output_artifacts: list             # currently always [] for Stage 00 proof
yaml_frontmatter_snapshot: dict    # the input artifact's frontmatter, verbatim
gate_check_results:                # populated by Step 2
  operator_approved: bool
  status_approved:   bool
  contract_passed:   bool
  # on failure: {"error": str, "contract_passed": False}
llm_prompt_hash:   str             # currently "" — wired but unused; Stage 00 has no LLM call
llm_response_hash: str             # currently "" — same
operator_signoff:
  name:      str                   # the --operator CLI argument
  timestamp: str                   # same ISO-8601 as the top-level timestamp
  comment:   str                   # hard-coded "Buildability proof — Stage 00 gate validated."
cost:
  tokens_in_uncached: int          # 0 for this proof
  tokens_out:         int          # 0
  usd_estimated:      float        # 0.0
```

### Filesystem path

`stages/<stage_id>/output/receipts/<ts_clean>.json` where `<ts_clean>` is the receipt's `timestamp` with `-` and `:` stripped. Example: `stages/00-intake/output/receipts/20260527T034512Z.json`. The directory is created with `mkdir(parents=True, exist_ok=True)` on first write.

---

## Dependencies

From `proof/requirements.txt`:

| Package | Version | Why |
|---|---|---|
| `dbos` | `>=1.0.0` | Listed for the intended pattern; **not currently imported** by `workflow.py`. See `proof/explanation.md` § "The DBOS gap". |
| `psycopg2-binary` | `>=2.9` | Postgres driver actually used by `workflow.py`. |
| `pyyaml` | `>=6.0` | YAML frontmatter parsing in `ingester.py`. |
