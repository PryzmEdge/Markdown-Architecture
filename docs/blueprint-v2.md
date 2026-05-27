# Markdown Architecture — Project Blueprint v2.0
**Repo**: [PryzmEdge/Markdown-Architecture](https://github.com/PryzmEdge/Markdown-Architecture)
**Version**: 2.0.0 | **Date**: 2026-05-24 | **Status**: Active

---

## Glossary

| Term | Definition |
|---|---|
| **ICM** | Interpretable Context Methodology — folder structure as agentic architecture (arXiv:2603.16021v2) |
| **CRDT** | Conflict-free Replicated Data Type — data structure that auto-merges concurrent edits without conflicts |
| **DBOS** | Database-Oriented Operating System — Stonebraker/Zaharia durable workflow runtime on Postgres |
| **FIDES** | Information-flow control framework for LLM agents (Microsoft Research, arXiv:2505.23643) |
| **YAML frontmatter** | Structured metadata block at the top of a Markdown file, delimited by `---`, parsed as YAML |
| **IFC** | Information-Flow Control — lattice-based security model governing how data moves between components |
| **MCP** | Model Context Protocol — standard for tool-invocation transport between agents and external tools |
| **ADR** | Architecture Decision Record — a document capturing a significant architectural decision and its rationale |
| **Operator** | A named human with authority to approve stage promotions and sign off on risk gates. Never an LLM. |
| **PromptExecutionReceipt** | Immutable audit artifact capturing what prompt ran, which model, what context, what tools, what it cost |
| **WAL** | Write-Ahead Log — Postgres durability mechanism; also the basis for audit/provenance in this system |

---

## Identity & Thesis

**Markdown Architecture** is a research and AI-native DevOps workspace structured with the Interpretable Context Methodology (ICM).

> **Core thesis**: Markdown is a human-readable orchestration substrate — not an execution environment. Its consumers (parsers, runtimes, LLM agents, Pandoc filters, notebook kernels) do the executing.

### Why Markdown as Orchestration Substrate

- **Human-readable**: Humans and AI agents read the same file — no translation layer
- **Version-control-native**: Git diffs, branches, and blame work natively on `.md` files
- **YAML frontmatter extensibility**: Structured metadata lives inline with content, no separate schema file required
- **Broad parser ecosystem**: Pandoc, panflute, Codebraid, Obsidian, remark — any runtime can consume it
- **AI lingua franca**: LLMs are trained on Markdown at high volume; it is the most reliable structured output format

### Target Audience

| Audience | How They Use This |
|---|---|
| **Operator (you)** | Reviews gates, sets `operator_approved: true`, runs rollback |
| **AI agents** | Navigate via CLAUDE.md, load stage CONTEXT.md sections, produce artifacts |
| **External contributors** | Understand structure, constraints, and ADR rationale |
| **Compliance reviewers** | Audit trail via PromptExecutionReceipt + risk.md + ADRs |

---

## Visual Pipeline

```
┌─────────────────────────────────────────────────────────────────────┐
│                    MARKDOWN ARCHITECTURE PIPELINE                   │
└─────────────────────────────────────────────────────────────────────┘

  Raw Idea / Question
        │
        ▼
┌───────────────┐   FAIL: status: blocked
│  00 — INTAKE  │──────────────────────────► Operator reviews ◄──┐
│               │                                                  │
│ Qualify the   │   PASS: operator_approved: true                  │
│ problem       │──────────────────────────────────────────────┐   │
└───────────────┘                                              │   │
                                                               │   │
        ▼                                                      │   │
┌───────────────┐   FAIL: insufficient-evidence                │   │
│ 01 — RESEARCH │──────────────────────────────────────────────┼───┘
│               │                                              │
│ Evidence +    │   PASS: ≥3 sources, contract valid           │
│ sources +     │──────────────────────────────────────────────┤
│ contradictions│                                              │
└───────────────┘                                              │
                                                               │
        ▼                                                      │
┌───────────────┐   FAIL: Critical risk, no operator sign-off  │
│ 02 — ANALYSIS │──────────────────────────────────────────────┘
│               │
│ Synthesis +   │   PASS: risk tier assigned, contract valid
│ risk tier +   │───────────────────────────────────────────────►
│ counter-arg   │
└───────────────┘
        │
        ▼
┌───────────────┐   FAIL: upstream not approved ──────────────► Operator
│  03 — OUTPUT  │
│               │   PASS: all upstream approved
│ Final         │───────────────────────────────────────────────►
│ deliverable + │                                        Final artifact
│ audit receipt │                                        + audit receipt
└───────────────┘
```

---

## Repository Structure

```
Markdown-Architecture/
├── CLAUDE.md                            ← Navigation & identity (≤800 tokens)
├── README.md                            ← Project overview
├── Makefile                             ← Build automation (outstanding)
├── CONTRIBUTING.md                      ← Contribution guidelines (outstanding)
├── LICENSE                              ← License (outstanding)
├── docs/
│   ├── v10-draft.md                     ← Canonical engineering position paper (v10)
│   ├── blueprint-v2.md                  ← This file
│   ├── adr/
│   │   ├── ADR-000-index.md
│   │   ├── ADR-001-postgres-state-kernel.md       ← Use PostgreSQL as state kernel
│   │   ├── ADR-002-crdt-bytea-pattern.md          ← Automerge/Yjs as bytea blobs
│   │   ├── ADR-003-datalog-lattice-traversal.md   ← Datalog (pg_mentat) for lattice traversal over recursive CTEs
│   │   ├── ADR-004-fides-product-lattice-authority.md ← FIDES two-element product lattice as authority substrate
│   │   └── ADR-005-temporal-dbos-workflow-split.md ← Temporal/DBOS workflow split
│   └── [v8.md, v9.md — archived]
├── _config/
│   ├── domain-rules.md                  ← Constraints (load § Constraints only)
│   └── stage-contract.py               ← CLI validator: exits 0 (pass) / 1 (fail)
├── stages/
│   ├── 00-intake/
│   │   ├── CONTEXT.md
│   │   └── output/
│   │       └── problem.md
│   ├── 01-research/
│   │   ├── CONTEXT.md
│   │   └── output/
│   │       ├── brief.md
│   │       ├── sources.md
│   │       └── contradictions.md
│   ├── 02-analysis/
│   │   ├── CONTEXT.md
│   │   └── output/
│   │       ├── synthesis.md
│   │       └── risk.md
│   └── 03-output/
│       ├── CONTEXT.md
│       └── output/
│           ├── <slug>.md
│           └── receipts/<timestamp>.md
└── .claude/
    ├── settings.json                    ← Hard constraints (hooks — outstanding)
    └── hooks/validate-mcp-response.py
```

### Versioning Strategy

| Item | Policy |
|---|---|
| Position paper | Linear version bump (`v8 → v9 → v10`); prior versions archived in `docs/` |
| Blueprint | Semantic versioning (`v1.0.0 → v2.0.0`); breaking changes = major bump |
| ADRs | Append-only; superseded ADRs get `status: superseded` + link to replacement |
| Git branching | `main` = canonical; feature work on named branches; merge via PR with operator review |

---

## ICM Pipeline — 4 Stages

### Stage 00 — Intake
**Agent Role**: Problem Qualification Agent

| Field | Detail |
|---|---|
| **Inputs** | Raw problem statement, domain tag, scope exclusion (2 sentences min) |
| **Output** | `stages/00-intake/output/problem.md` |
| **Gate** | `operator_approved: true` — operator confirms problem is falsifiable, scoped, domain-tagged |
| **Failure path** | After 2 failed refinements → `status: blocked`; halt |

**Input → Problem Statement process:**
1. Restate in one sentence, falsifiable or actionable form
2. Assign domain tag (`research` · `architecture` · `devops` · `governance` · `quant` · `documentation`)
3. Write 2-sentence scope exclusion
4. Operator reviews: clarity, specificity, alignment with project goals

---

### Stage 01 — Research
**Agent Role**: Research & Evidence Agent

| Field | Detail |
|---|---|
| **Inputs** | `problem.md` (`status: approved, operator_approved: true`) |
| **Outputs** | `brief.md`, `sources.md`, `contradictions.md` |
| **Gate** | ≥3 sources scored; `python _config/stage-contract.py --stage 01-research` passes |
| **Failure path** | `status: insufficient-evidence` if <3 relevant sources |

**Output structure:**
- `brief.md`: Problem restatement + top 3–5 findings + proposed solution directions
- `sources.md`: Table — source, claim, quality (Primary/Secondary/Anecdotal), relevance (High/Med/Low), citation
- `contradictions.md`: Disconfirming findings — never suppressed, may be empty

---

### Stage 02 — Analysis
**Agent Role**: Synthesis & Risk Agent

| Field | Detail |
|---|---|
| **Inputs** | `brief.md` + `sources.md` + `contradictions.md` (all `approved`) |
| **Outputs** | `synthesis.md`, `risk.md` |
| **Gate** | Risk tier assigned; `risk_check_passed: true` if High/Critical; contract passes |
| **Failure path** | Hard stop if Critical risk without operator sign-off |

**Output structure:**
- `synthesis.md`: Core claim → evidence map (supports/refutes/neutral) → integrated findings → **counter-argument** → recommendations
- `risk.md`: Risk tier + justification + mitigations + operator sign-off flag

---

### Stage 03 — Output
**Agent Role**: Output Assembly Agent

| Field | Detail |
|---|---|
| **Inputs** | All upstream stage outputs (`approved`) |
| **Outputs** | `<slug>.md` + `receipts/<timestamp>.md` |
| **Gate** | All upstream approved; audit receipt written; operator final sign-off |
| **Failure path** | Halt with named blocking stage if any upstream not `approved` |

**Slug format**: `<domain>-<keyword>-<YYYY-MM-DD>` (e.g. `architecture-datalog-policy-2026-05-24`)

**Output formats**: `paper` · `brief` · `spec` · `adr` · `runbook`

**PromptExecutionReceipt fields**: `receipt_id`, `timestamp`, `model_id`, `prompt_hash`, `context_manifest`, `tool_invocations`, `output_hash`, `input_labels`, `output_label`, `operator_id`, `stage_id`, `cost` (tokens + USD)

---

## Inter-Stage Contracts

`_config/stage-contract.py` is the **primary enforcement tool**.

```bash
python _config/stage-contract.py --stage 01-research
# PASS — stage 'research' contract valid.
```

**Full YAML frontmatter (every artifact):**

```yaml
---
status: approved               # draft | review | approved | blocked | needs-revision
operator_approved: true        # false until human operator explicitly sets true
risk_check_passed: true        # required if risk tier is High or Critical
stage: "01-research"
domain: "architecture"
sources_count: 5               # stage-01 specific
---
```

---

## Governance Rules

### Universal Constraints

| Constraint | Enforcement |
|---|---|
| Never write to `output/` until `operator_approved: true` | `stage-contract.py` validates before promotion |
| Never suppress contradictions | `contradictions.md` required output (may be empty) |
| Never claim novelty without citing prior art | Stage 02 counter-argument check + ADR review |
| Every artifact must have valid YAML frontmatter | `stage-contract.py` parses and validates |

### Risk Tier Definitions

| Tier | Definition | Gate | Example |
|---|---|---|---|
| **Low** | Reversible, no external dependency | None | Documentation fix, rename local variable |
| **Medium** | Reversible, external dependency | Operator review | New microservice feature, minor schema addition |
| **High** | Partially irreversible | `risk_check_passed: true` | Major architectural change, core DB migration |
| **Critical** | Irreversible, public, or financial | `risk_check_passed: true` + sign-off | Production data deletion, public API breaking change |

### Escalation Path

1. Agent flags `status: blocked` or `status: needs-revision`
2. Operator reviews stage output directory
3. Operator resolves or accepts risk; sets `operator_approved: true`
4. Agent **resumes from blocked stage** — no pipeline restart, no context loss

---

## Architecture Decision Records

### ADR Lifecycle
1. **Propose** — open GitHub issue
2. **Draft** — write `ADR-NNN.md` with `status: proposed`
3. **Review** — operator reviews via PR
4. **Accept** — merge to `main`, set `status: accepted`
5. **Supersede** — set `status: superseded`, link to replacement ADR

### Current ADRs

| ADR | Decision | Status | Enforced In |
|---|---|---|---|
| ADR-001 | PostgreSQL as state kernel and provenance ledger | Accepted | Stage 03 receipts |
| ADR-002 | Automerge/Yjs bytea-blob CRDT over Postgres | Accepted | Collaboration layer |
| ADR-003 | Datalog (pg_mentat) for lattice traversal over recursive CTEs | Accepted | Stage 02, Part 12.8 |
| ADR-004 | FIDES two-element product lattice as authority substrate | Accepted | Stage 03 receipts, IFC |
| ADR-005 | Temporal/DBOS workflow split | Accepted | Pipeline orchestration |

---

## AI Agent Integration

**Agent context load order (every turn):**
1. `CLAUDE.md` — workspace identity (≤800 tokens)
2. Relevant **section** of current stage `CONTEXT.md` (Inputs, Process, or Outputs only)
3. `_config/domain-rules.md § Constraints` — never full file
4. Skill, if needed

### Skills — API Definition

| Skill | Inputs | Outputs |
|---|---|---|
| `domain-validator` | `artifact_path: str` | `{ "isValid": bool, "errors": list[str] }` |
| `context-compiler` | `stage: str, token_budget: int` | `{ "compiledContext": str, "tokens_used": int }` |
| `audit-logger` | `audit_data: dict` | `{ "auditId": str, "timestamp": str, "receipt_path": str }` |

Skills are Python modules loaded on demand — not at every turn, not separate microservices.

---

## Build Commands

```bash
# Validate a stage
python _config/stage-contract.py --stage 01-research

# Parallel build
make -j$(nproc) all

# Single stage (runs + validates)
make stage=02-analysis

# Validate only
make validate

# Clean non-approved artifacts
make clean
```

### Makefile Target Map

| Target | Action |
|---|---|
| `make all` | All stages in dependency order |
| `make stage-00-intake` | Run Stage 00 |
| `make stage-01-research` | Run Stage 01 |
| `make stage-02-analysis` | Run Stage 02 |
| `make stage-03-output` | Assemble final output |
| `make validate` | `stage-contract.py` on all stages |
| `make clean` | Remove non-approved artifacts |

---

## What's Complete vs. Outstanding

### Complete ✅
- `docs/v10-draft.md` — Engineering position paper
- `docs/adr/ADR-001` through `ADR-005` — Full ADR bodies
- All 4 stage `CONTEXT.md` files
- `_config/domain-rules.md` + `_config/stage-contract.py`
- `CLAUDE.md` + `README.md` + `ADR-000-index.md`

### Outstanding 🔲

| Item | Priority | Scope |
|---|---|---|
| `.claude/settings.json` hooks | **High** | `pre-commit`, `pre-command`, `post-edit` |
| `Makefile` | **High** | Full target map above |
| Stage 1 buildability proof | **High** | Postgres events table + markdown ingester + receipt emitter |
| `CONTRIBUTING.md` | **Medium** | ADR proposal process, PR conventions |
| `LICENSE` | **Medium** | Choose and add |
| `.github/workflows/` CI | **Medium** | Run `stage-contract.py` on every PR |
| Risk register (Part 24) | **Medium** | Tiered risk per module |
| Incident runbook (Part 25) | **Medium** | Rollback steps, ownership |
| IP disclosure log | **Low** | Timestamped prior art record |

---

*Blueprint v2.0.0 — Markdown Architecture. 2026-05-24.*
