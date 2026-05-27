# Markdown Architecture

A research and AI-native DevOps workspace structured with the Interpretable Context Methodology (ICM).

**Thesis**: Markdown is a human-readable orchestration substrate — not an execution environment.

## Structure

- `docs/v10-draft.md` — Canonical engineering position paper (v10)
- `docs/adr/` — Architecture Decision Records (ADR-001 through ADR-005)
- `docs/ip-disclosure.md` — Timestamped prior-art ledger (append-only)
- `docs/gstack-usage.md`, `docs/gbrain-usage.md`, `docs/graphify-usage.md` — Companion docs for external Claude Code tooling installed in this workspace
- `stages/` — ICM pipeline: 00-intake → 01-research → 02-analysis → 03-output
- `_config/` — Domain rules, stage contract validator, risk register, agent skills (audit logger, graphify CLI wrapper)
- `proof/` — Stage 1 buildability proof (DBOS-style durable workflow + Postgres + receipts). See [`proof/README.md`](proof/README.md) for the Diataxis docs (tutorial / how-to / reference / explanation).
- `tests/` — pytest suite (stage contract, ingester, audit logger, graphify query). Shared fixtures in `tests/fixtures/`.
- `.claude/` — Hooks and hard constraints
- `CONTRIBUTING.md` — Operator and contributor rules (PR conventions, ADR process, stage artifact conventions)

## Quick Start

```bash
# Install deps for stage validation + tests + the proof
pip install pyyaml pytest -r proof/requirements.txt

# Validate a stage
python _config/stage-contract.py --stage 01-research

# Run the test suite
python -m pytest

# Run the Stage 1 buildability proof end-to-end
# (see proof/tutorial.md for the Docker Postgres recipe)
python proof/workflow.py --problem tests/fixtures/approved.md --operator you

# Parallel build
make -j$(nproc) all
```

## Paper

See [`docs/v10-draft.md`](docs/v10-draft.md) for the full engineering position paper.
See [`docs/adr/`](docs/adr/) for all architectural decision records.
