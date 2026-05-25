# Stage 1 Buildability Proof

This directory contains the minimal working prototype that validates the core
claims of the Markdown Architecture pipeline.

## What it proves

1. A DBOS workflow can ingest a Markdown artifact from `stages/00-intake/output/`
2. `stage-contract.py` gate logic runs inside a durable transaction
3. A `PromptExecutionReceipt` is written to Postgres and to `stages/03-output/output/receipts/`
4. A crash mid-workflow recovers automatically from the last completed step

## Stack

- Python 3.12+
- DBOS Transact (`dbos`)
- PostgreSQL 15+ (local or Docker)
- PyYAML

## Setup

```bash
cd proof/
pip install -r requirements.txt

# Start Postgres (Docker)
docker run -d \
  --name ma-postgres \
  -e POSTGRES_PASSWORD=ma_dev \
  -e POSTGRES_USER=ma \
  -e POSTGRES_DB=markdown_arch \
  -p 5432:5432 \
  postgres:15

# Apply schema
psql postgresql://ma:ma_dev@localhost:5432/markdown_arch -f schema.sql

# Run the workflow
python workflow.py --problem stages/00-intake/output/problem.md --operator operator
```

## Files

| File | Purpose |
|---|---|
| `schema.sql` | Postgres tables: `workflow_events`, `provenance_log` |
| `workflow.py` | DBOS workflow: ingest → validate → emit receipt |
| `ingester.py` | Markdown artifact reader and frontmatter parser |
| `requirements.txt` | Python dependencies |
