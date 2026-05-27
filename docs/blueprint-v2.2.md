# Markdown Architecture — Project Blueprint v2.2
**Repo**: [PryzmEdge/Markdown-Architecture](https://github.com/PryzmEdge/Markdown-Architecture)
**Version**: 2.2.0 | **Date**: 2026-05-24 | **Status**: Active
**Changes from v2.1**: Added five-layer context hierarchy, U-shaped human oversight rationale, sensitivity-ratchet vs FIDES comparison, CRDT compaction strategy, and a concrete risk register. Preserved ADR-005 split model and avoided DBOS-only framing.

---

## Glossary

| Term | Definition |
|---|---|
| **ICM** | Interpretable Context Methodology — folder structure as agentic architecture |
| **MWP** | Model Workspace Protocol — related term for filesystem-based agent orchestration |
| **CRDT** | Conflict-free Replicated Data Type — auto-merging concurrent edit model |
| **DBOS** | Database-Oriented Operating System — durable workflow runtime over PostgreSQL |
| **FIDES** | Information-flow control framework for LLM agents |
| **YAML frontmatter** | Structured metadata block at the top of a Markdown file |
| **ADR** | Architecture Decision Record |
| **Operator** | Named human approver; never an LLM |
| **PromptExecutionReceipt** | Immutable execution and provenance receipt |
| **WAL** | PostgreSQL Write-Ahead Log |
| **RPN** | Risk Priority Number = Severity × Occurrence × Detection |

---

## Identity & Thesis

**Markdown Architecture** is a research and AI-native DevOps workspace structured with the Interpretable Context Methodology (ICM).

> **Core thesis**: Markdown is a human-readable orchestration substrate — not an execution environment. Parsers, runtimes, agents, notebook kernels, and policy engines consume the Markdown; Markdown itself remains the explicit control surface.

### Why Markdown

- Human-readable by operators and agents
- Git-native for diff, blame, versioning, and promotion control
- Extensible through YAML frontmatter
- Broad parser ecosystem (Pandoc, remark, notebooks, static tooling)
- Native to LLM training distribution, reducing translation friction

### Target Audience

| Audience | How They Use This |
|---|---|
| Operator | Reviews gates, approves promotions, signs off risk |
| AI agents | Load context selectively, generate artifacts, obey contracts |
| Contributors | Follow repository structure, ADRs, and governance |
| Compliance reviewers | Audit receipts, frontmatter history, and lineage |

---

## Five-Layer Context Hierarchy

To prevent context rot, prompt injection, and token inflation, the workspace separates information into five layers. Agents load only the minimum required layer set for the active step.

| Layer | Representation | Purpose | Token Budget |
|---|---|---|---|
| **Layer 0: Identity** | `CLAUDE.md` | Workspace persona, navigation, command aliases | ≤ 800 tokens |
| **Layer 1: Routing** | Folder hierarchy | Maps task to stage directory | Directory-level |
| **Layer 2: Stage Contracts** | `CONTEXT.md` | Inputs, process, outputs, failure states | ≤ 1,500 tokens |
| **Layer 3: Reference Material** | `_config/`, templates, skills | Rules, style, static guidance | Load on demand |
| **Layer 4: Working Artifacts** | `output/` directories | Volatile run-specific artifacts | Dynamically bounded |

**Load order per turn**:
1. `CLAUDE.md`
2. Relevant section of stage `CONTEXT.md`
3. `_config/domain-rules.md § Constraints`
4. Skills if needed
5. Only the minimum necessary working artifacts

This separation prevents instructions from blending with untrusted input data and reduces injection exposure.

---

## Visual Pipeline

```text
Raw Idea
  ↓
00-intake ──fail──► blocked ──► operator review
  │ pass
  ▼
01-research ──fail──► insufficient-evidence ──► operator review
  │ pass
  ▼
02-analysis ──fail──► blocked / needs-operator-review ──► operator review
  │ pass
  ▼
03-output ──fail──► halt with named blocking stage
  │ pass
  ▼
final artifact + audit receipt
```

### Human Oversight Shape

Human interaction is intentionally highest at the pipeline boundaries: intake and final output. Mid-pipeline stages are more autonomous but remain contract-bound.

| Stage | Human Interaction Type | Illustrative Edit Frequency |
|---|---|---|
| 00 — Intake | Direction-setting | 92% |
| 01 — Research | Fact verification | 30% |
| 02 — Analysis | Risk evaluation | 30% |
| 03 — Output | Final alignment | 78% |

These figures are **illustrative**, not normative system guarantees.

---

## Repository Structure

```text
Markdown-Architecture/
├── CLAUDE.md
├── README.md
├── Makefile
├── CONTRIBUTING.md
├── LICENSE
├── docs/
│   ├── v10-draft.md
│   ├── blueprint-v2.2.md
│   └── adr/
│       ├── ADR-000-index.md
│       ├── ADR-001-postgres-state-kernel.md
│       ├── ADR-002-crdt-bytea-pattern.md
│       ├── ADR-003-datalog-lattice-traversal.md
│       ├── ADR-004-fides-product-lattice-authority.md
│       └── ADR-005-temporal-dbos-workflow-split.md
├── _config/
│   ├── domain-rules.md
│   ├── risk-register.md
│   └── stage-contract.py
├── stages/
│   ├── 00-intake/output/problem.md
│   ├── 01-research/output/{brief.md,sources.md,contradictions.md}
│   ├── 02-analysis/output/{synthesis.md,risk.md,ATTENTION.md}
│   └── 03-output/output/{<slug>.md,receipts/<timestamp>.json}
└── .claude/
    ├── settings.json
    └── hooks/
```

---

## Gate Logic

The validator is the canonical enforcement point. A stage may promote only if its deterministic gate evaluates true.

### Validation Function

\[
\mathcal{V}(a, s) \to \{0, 1\}
\]

Where `a` is an artifact and `s` is the stage-specific schema and policy set.

### Gate Boolean Formulas

```python
# Stage 00
gate_00 = (
    problem_md.yaml["operator_approved"] == True
)

# Stage 01
gate_01 = (
    problem_md.yaml["operator_approved"] == True
    and len(sources_md.citations) >= 3
    and stage_contract_validator_passes("01-research") == True
)

# Stage 02
gate_02 = (
    brief_md.yaml["operator_approved"] == True
    and risk_md.yaml["risk_tier"] is not None
    and (
        risk_md.yaml["risk_tier"] not in ["High", "Critical"]
        or risk_md.yaml["risk_check_passed"] == True
    )
    and stage_contract_validator_passes("02-analysis") == True
)

# Stage 03
gate_03 = (
    synthesis_md.yaml["operator_approved"] == True
    and risk_md.yaml["operator_approved"] == True
    and problem_md.yaml["operator_approved"] == True
    and audit_receipt_written == True
    and stage_contract_validator_passes("03-output") == True
)
```

### Status Transition Table

| From | To | Allowed? | Trigger |
|---|---|---|---|
| `draft` | `review` | ✅ | Agent completes stage output |
| `review` | `approved` | ✅ | Operator sets `operator_approved: true` |
| `review` | `needs-revision` | ✅ | Agent or operator flags issue |
| `review` | `blocked` | ✅ | Gate fails after retry limit |
| `needs-revision` | `review` | ✅ | Agent resubmits |
| `blocked` | `review` | ✅ | Operator resolves issue |
| `approved` | `blocked` | ✅ | Downstream rejection |
| `approved` | `draft` | ❌ | New version required |

---

## Risk Model

### Likelihood × Impact Matrix

|  | Impact 1 | Impact 2 | Impact 3 | Impact 4 |
|---|---|---|---|---|
| **Likelihood 1** | Low | Low | Medium | High |
| **Likelihood 2** | Low | Medium | High | High/Critical |
| **Likelihood 3** | Medium | High | Critical | Critical |

**Likelihood**: 1 = Rare, 2 = Possible, 3 = Likely  
**Impact**: 1 = Minor, 2 = Moderate, 3 = Major, 4 = Catastrophic

### RPN

\[
RPN = Severity \times Occurrence \times Detection
\]

Use RPN as a secondary prioritization score inside `risk.md`; the official gate still keys on the tier matrix above.

### Gate Mapping

| Tier | Gate Requirement |
|---|---|
| Low | None |
| Medium | Operator review |
| High | `risk_check_passed: true` |
| Critical | `risk_check_passed: true` + explicit operator sign-off + `ATTENTION.md` |

---

## FIDES and Sensitivity Ratchet

### FIDES Label Set

| Label | Confidentiality | Integrity |
|---|---|---|
| `PUBLIC_UNTRUSTED` | Public | Untrusted |
| `PUBLIC_TRUSTED` | Public | Trusted |
| `INTERNAL_UNTRUSTED` | Internal | Untrusted |
| `INTERNAL_TRUSTED` | Internal | Trusted |
| `RESTRICTED_UNTRUSTED` | Restricted | Untrusted |
| `RESTRICTED_TRUSTED` | Restricted | Trusted |

**Rule**: data may only flow to equal or higher confidentiality unless explicit redaction and operator approval occur.

### Comparison

| Feature | Sensitivity Ratchet | Dynamic Taint Tracking (FIDES) |
|---|---|---|
| Mechanism | Permanently narrows tool access after sensitive data exposure | Propagates security labels across data joins |
| Complexity | Low | Higher |
| Injection Protection | High | High |
| Flexibility | Restrictive | High |
| Best Use | Lightweight CLI or single-session agents | Multi-agent pipelines with mixed-trust data |

Use the ratchet in minimal environments; use FIDES in the full multi-stage workspace.

---

## Durable State and Orchestration

ADR-005 remains the governing decision: the architecture uses a **split model**, not a DBOS-only model.

| Role | System |
|---|---|
| Embedded, transaction-close workflow steps | DBOS |
| Long-running, distributed, durable orchestration | Temporal |

ADR-001 still governs provenance persistence in PostgreSQL. Stage 03 receipts are hashed and committed into append-only database storage.

---

## CRDT Storage Strategy

Concurrent edits by humans and agents use Automerge or Yjs patterns, but storage must avoid repeated in-place `BYTEA` rewrites.

### Storage Pattern

1. Append each incremental edit to `document_updates`
2. Keep periodic consolidated snapshots in `documents`
3. Trigger compaction after a threshold such as 100 updates
4. Merge updates into a new snapshot in one transaction
5. Delete compacted incremental rows

This keeps WAL growth and row-rewrite overhead bounded while preserving mergeability.

---

## Audit Receipt

Stage 03 writes a JSON `PromptExecutionReceipt` before promotion completes.

```json
{
  "audit_id": "<uuid>",
  "timestamp": "<ISO8601>",
  "stage_name": "03-output",
  "agent_id": "agent-output-v1.0",
  "input_artifacts": [
    {"path": "stages/00-intake/output/problem.md", "hash_sha256": "<hash>"}
  ],
  "output_artifacts": [
    {"path": "stages/03-output/output/<slug>.md", "hash_sha256": "<hash>", "fides_label": "INTERNAL_TRUSTED"}
  ],
  "yaml_frontmatter_snapshot": {
    "status": "approved",
    "operator_approved": true,
    "stage": "03-output"
  },
  "gate_check_results": {
    "all_upstream_approved": true,
    "audit_receipt_written": true,
    "contract_validator_passed": true
  },
  "llm_prompt_hash": "<sha256>",
  "llm_response_hash": "<sha256>",
  "operator_signoff": {
    "name": "<operator-name>",
    "timestamp": "<ISO8601>",
    "comment": "<optional note>"
  }
}
```

---

## Build and Hooks

### Make Targets

- `make all` — run all stages in dependency order
- `make stage-00-intake`
- `make stage-01-research`
- `make stage-02-analysis`
- `make stage-03-output`
- `make validate`
- `make clean`

### Hook Intent

- `pre-commit` — run `stage-contract.py` across affected stages
- `pre-command` — dry-run risk classification
- `post-edit` — write receipt metadata after agent edits

---

## Risk Register

This file should also exist as `_config/risk-register.md`.

| Risk Category | Hazard Vector | Severity Tier | Mitigation Strategy |
|---|---|---|---|
| Security | Prompt injection from untrusted external sources | Critical | FIDES labels, variable indirection, quarantined analysis |
| System | State drift from uncommitted files or manual edits | High | Git clean checks before promotion |
| Storage | CRDT binary bloat and row rewrite overhead | Medium | Append-only update rows + compaction |
| Operational | Stalled pipelines from missing operator approvals | Low | Local notifications and `ATTENTION.md` review trigger |

---

## Outstanding

| Item | Priority | Scope |
|---|---|---|
| `.claude/settings.json` | High | Hook definitions and enforcement wiring |
| `Makefile` | High | Target implementation and dependency chain |
| Stage 1 buildability proof | High | Minimal DBOS + Markdown + receipt demo |
| `CONTRIBUTING.md` | Medium | ADR workflow, PR rules, operator sign-off |
| `LICENSE` | Medium | Choose and add |
| `.github/workflows/` | Medium | CI validation on PRs |
| Incident runbook | Medium | Recovery steps and rollback ownership |

---

*Blueprint v2.2.0 — Markdown Architecture. 2026-05-24.*
