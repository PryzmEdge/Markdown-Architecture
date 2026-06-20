# Proof-Trio Reconciliation Proposal

**Status**: Proposal — no code landed | **Date**: 2026-06-08
**Scope**: How (and whether) to adopt the `_incoming/` Stage-1 buildability-proof
trio — `ai_gateway.py`, `receipt.py`, `run_stage.py` — into the committed tree.

This document is the gate the operator asked for: *before any proof-trio code
lands, lay the two frontmatter schemas and the two validator CLIs side by side,
recommend which wins, and state what the loser has to change to match.* It
makes a recommendation; it does not modify code.

---

## 0. Why a reconciliation is needed at all

The `_incoming/` set is an **earlier, simpler buildability proof** than the one
the repo actually shipped. The committed proof is the Postgres/DBOS workflow in
`proof/` (`workflow.py`, `ingester.py`, `schema.sql`). The trio is a *parallel*
answer to the same "show the loop runs" question, and it was never committed.

It cannot be dropped in as-is because it collides with the committed tree on
**three axes**, two of which the operator named (schema, validator CLI) and one
that follows from them (the receipt writer):

1. **Frontmatter schema** — `risk_tier`-tagged (prototype) vs `domain`-tagged (tree).
2. **Validator CLI** — single-file-path (prototype) vs `--stage` (tree).
3. **Receipt mechanism** — `audit/session_log.jsonl` (prototype) vs per-run
   `stages/<id>/output/receipts/<ts>.json` (tree, already implemented in
   `_config/skills/audit_logger.py`).

---

## 1. Frontmatter schema — side by side

| Dimension | Prototype (`_incoming`) | Tree (committed v2.3) |
|---|---|---|
| **Required fields** | `status`, `operator_approved`, `stage`, **`risk_tier`** | `status`, `operator_approved`, `stage`, **`domain`** |
| Source of truth | `REQUIRED_FIELDS` in `_config/stage-contract.py` | `REQUIRED_FRONTMATTER_BASE` in `_config/stage-contract.py` (+ `CLAUDE.md` spec) |
| `domain` | absent | **required** (added in commit *"add missing domain field"*) |
| `risk_tier` | required on **every** artifact | only meaningful on **`02-analysis/output/risk.md`**; not a base field |
| `risk_check_passed` | required iff `risk_tier ∈ {high, critical}` | required iff `risk_tier ∈ {High, High/Critical, Critical}` |
| Risk-tier casing | **lowercase** (`high`/`critical`) | **Capitalized** (`High`/`Critical`/`High/Critical`) |
| `status` value check | **must equal `approved`** | presence only — **value not enforced** by validator |
| `operator_approved` | must be boolean `True`; string `"true"` rejected | must be boolean `True` on every `output/*.md` |
| `sources_count` | not used | required on `01-research/output/sources.md`, cross-checked to table rows (≥3) |

**Net:** the two schemas share three fields (`status`, `operator_approved`,
`stage`) and diverge on the fourth (`risk_tier` vs `domain`) plus casing and the
`status`-value rule. A prototype artifact fed to the **tree** validator fails
for *missing `domain`*; a tree artifact fed to the **prototype** validator fails
for *missing `risk_tier`* (and possibly *status ≠ approved*).

---

## 2. Validator CLI — side by side

| Dimension | Prototype (`_incoming`) | Tree (committed v2.3) |
|---|---|---|
| Invocation | `stage-contract.py <artifact.md>` (positional path) | `stage-contract.py --stage <name>` / `--stage all` |
| Unit validated | **one file** | **one stage directory** (CONTEXT.md + required outputs + cross-checks) |
| Extra mode | none | `--assess-command "<cmd>"` → BLOCKED/WARN/OK shell-risk scan |
| Gate logic | flat field checks | `gate_00…gate_03` formulas, per-stage output requirements |
| Malformed frontmatter | **hard FAIL** (strict open/close `---`, must parse to mapping) | lenient — missing/bad YAML → `{}` → reported as missing fields |
| Exit codes | `0` pass / `1` fail / `2` usage | `0` pass / `1` fail |
| Lines | ~113 | ~276 |
| **Wired into** | nothing (never committed) | **CI** (`validate.yml`: `--stage all`), **Makefile** (`CONTRACT`), **tests** (`test_stage_contract.py` imports `validate_stage`/`assess_command`), **`.claude/settings.json`** hooks (`preCommit --stage all`, `preCommand --assess-command`) |

**Net:** same filename, **non-overlapping invocation contracts**. `run_stage.py`
ends by calling `python _config/stage-contract.py <OUTPUT_PATH>` — a positional
path the **tree** validator does not accept, so the prototype's final step
breaks against the committed validator.

---

## 3. Receipt mechanism — the follow-on conflict

`receipt.py` (prototype) writes a Pydantic-v2 `PromptExecutionReceipt` as a line
to `audit/session_log.jsonl` and computes `cost_usd` from placeholder rates. The
tree **already has** `_config/skills/audit_logger.py::write_receipt()`, which
writes a per-run `<timestamp>.json` to `stages/<stage_id>/output/receipts/` and
returns a `pg_receipt_hash`. The `03-output` gate even checks that
`output/receipts/*.json` exists. Adopting `receipt.py` would create a **second,
divergent** receipt format and location.

---

## 4. Recommendation

**The tree wins on all three axes. The proof trio adapts to the tree.**

Rationale — the tree side is not merely newer, it is *load-bearing*:

- It is the version CI runs, the Makefile references, the tests import, and the
  hooks invoke. The prototype validator is wired into nothing.
- It is strictly more capable (stage-aware multi-file gates, `gate_00…03`,
  command-risk assessment) and the `domain` field is canonical per `CLAUDE.md`
  and a deliberate recent commit.
- A receipt writer + per-stage receipts directory already exist and a gate
  depends on them.

Adopting the prototype's schema/CLI/receipt would regress all of that. So the
direction is fixed: **keep the tree's `domain`-tagged schema, the `--stage` CLI,
and `audit_logger.write_receipt`.**

### What the proof trio must change to match

| File | Required change |
|---|---|
| `run_stage.py` | (a) Frontmatter template: add `domain: "<tag>"`, drop `risk_tier` as a base field, keep `operator_approved: false`. (b) Canonical `01-research` outputs are `brief.md` + `sources.md` (≥3 scored rows, `sources_count` matching) + `contradictions.md`, **not** `research.md` — either produce those three or accept that `--stage 01-research` cannot validate a lone `research.md`. (c) Replace the final `stage-contract.py <path>` call with `--stage 01-research`. |
| `receipt.py` | Retire in favour of `_config/skills/audit_logger.write_receipt()`, **or** keep only the `cost_usd`/token-accounting helper and route persistence through `audit_logger` so there is one receipt format and location. |
| `ai_gateway.py` | Closest to compatible. Confirm `MODEL_BY_TIER` IDs against `CLAUDE.md`; keep it as the single vendor chokepoint. Verify the `anthropic` SDK call signature and per-1K pricing on first real run (both flagged as placeholders). |

### Pragmatic augmentation (optional, recommended)

The prototype's **single-file validation** — "check this one freshly-written
artifact" — is genuinely useful and is the whole hinge of the demo. Rather than
discard it, **extend the tree validator with a single-file mode** that coexists
with `--stage`: if the argument is a path to an existing file, run the flat
field checks on that file; otherwise dispatch to stage mode. This is additive,
keeps CI/tests/hooks untouched, and gives `run_stage.py` a contract call that
works without first materialising all three `01-research` outputs.

---

## 5. Decision required from the operator

1. **Confirm the direction**: tree schema + `--stage` CLI + `audit_logger` win,
   trio adapts. (Recommended.)
2. **Single-file mode**: add it to the tree validator (recommended), or require
   the trio to always go through full `--stage` validation?
3. **Trio scope**: adopt all three files (with the changes above), adopt only
   `ai_gateway.py` as the canonical chokepoint, or leave the trio in `_incoming`
   as a reference and not adopt it at all?

No code lands until these are answered.
