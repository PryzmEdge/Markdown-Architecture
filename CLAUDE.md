---
version: "10.0.0"
tokens: "≤800"
scope: "navigation, structure, identity"
do_not_use_for: "hard constraints, behavioral enforcement"
---

# Markdown Architecture — CLAUDE.md

> **Scope**: Structural navigation and identity only. Hard constraints live in hooks. Schema contracts live in `_config/stage-contract.py`. See `docs/v10-draft.md` for the current engineering position paper.

---

## Workspace Identity

This is the **Markdown Architecture** workspace — a research and AI-native DevOps environment structured with the Interpretable Context Methodology (ICM). The thesis: Markdown is a human-readable orchestration substrate, not an execution environment. Every stage is a self-contained unit with explicit Inputs, Process, and Outputs declared in a `CONTEXT.md` file.

---

## Folder Structure

```
Markdown-Architecture/
├── CLAUDE.md                        ← This file (≤800 tokens, navigation only)
├── README.md, CONTRIBUTING.md, LICENSE, Makefile
├── docs/
│   ├── v10-draft.md                 ← Current canonical engineering position paper
│   ├── adr/                         ← ADR-000 index through ADR-005
│   ├── gstack-usage.md, gbrain-usage.md, graphify-usage.md  ← External tooling companions
│   └── [blueprint-v2.x, v8, v9 archived; ip-disclosure.md]
├── _config/
│   ├── domain-rules.md              ← Constraints applied at every stage
│   ├── risk-register.md             ← Project risk register
│   ├── stage-contract.py            ← StageContract validator
│   └── skills/                      ← audit_logger.py, graphify_query.py
├── stages/                          ← 00-intake / 01-research / 02-analysis / 03-output, each with CONTEXT.md
├── proof/                           ← Stage 1 buildability proof (workflow.py, ingester.py, schema.sql) + Diataxis docs
├── tests/                           ← pytest suite + fixtures/
└── .claude/
    ├── settings.json                ← Hooks (hard constraints, deterministic enforcement)
    └── hooks/validate-mcp-response.py
```

---

## Navigation Rules

- **Load stage context by section, not full file.** Reference only the section you need from a `CONTEXT.md` (Inputs, Process, or Outputs).
- **Never load full `domain-rules.md`.** Load the `## Constraints` section only.
- **Stage promotion requires `operator_approved: true`** in the stage's YAML frontmatter before writing to the next stage's `output/` directory.
- **Do not write to `output/`** of any stage until the current stage's acceptance criteria are GREEN.

---

## Required YAML Frontmatter (every .md artifact)

```yaml
---
status: draft | review | approved
operator_approved: false
risk_check_passed: false
stage: "00-intake" | "01-research" | "02-analysis" | "03-output"
---
```

---

## What Belongs Here vs. Elsewhere

| Concern | Location |
|---|---|
| File paths, build commands | CLAUDE.md (here) ✅ |
| Schema field definitions | `_config/stage-contract.py` ✅ |
| Hard constraints | `.claude/settings.json` hooks ✅ |
| Domain-specific constraints | `_config/domain-rules.md` ✅ |
| Behavioral rules | **Not here** — use hooks ❌ |

---

## Build Commands

```bash
# Parallel build (required — sequential is slow)
make -j$(nproc) all

# Single stage
make stage=02-analysis

# Validate a stage output before promotion
python _config/stage-contract.py --stage 02-analysis
```

---

## Skills

Load on demand — do not load all skills on every turn:

- `domain-validator` — validate stage artifacts against `domain-rules.md`
- `context-compiler` — assemble token-budgeted context from stage inputs
- `audit-logger` — write `PromptExecutionReceipt` to the append-only log
- `gstack` / `gbrain` (external) — see `docs/gstack-usage.md`, `docs/gbrain-usage.md`

---

*Token budget: this file must remain ≤800 tokens. Trim before adding.*

## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

Rules:
- For codebase questions, first run `graphify query "<question>"` when graphify-out/graph.json exists. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).
