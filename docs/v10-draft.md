---
title: "Markdown Files & Scripting: Version 10 — Engineering Position Paper"
version: "10.0.0"
date: "2026-05-23"
status: "draft"
authors:
  - "PryzmEdge (synthesizing editor)"
predecessor: "v9.0.0 (2026-05-23)"
changelog:
  - version: "10.0.0"
    date: "2026-05-23"
    fixes:
      - "PG framing corrected: state kernel + provenance ledger (not OS kernel)"
      - "Medallion/Renaissance references removed entirely"
      - "Novelty paragraph added: prior art named, synthesis claimed honestly"
      - "Prior art cited throughout: DBOS, Temporal, FIDES, CaMeL, Marten, Denning 1976, Sandhu 1993, Miller/ocap, Patchwork/GAIOS"
      - "Part 12: six-class label lattice formalized with join/meet/flow rules/declassification"
      - "Tier 2 architectural blocks integrated: Datalog, incremental MVs, CRDT-as-bytea, RLS+OPA, constrained decoding, Temporal/DBOS split"
      - "Obsidian framing corrected: Obsidian-compatible vault, not Obsidian replacement"
      - "Scope and Scale section added: personal-scale focus explicit"
      - "Trading analogy scoped: control-pattern only, not operational semantics"
      - "Selected prior art appendix added"
---

# Markdown Files & Scripting: Version 10 — Engineering Position Paper

*Revised May 23, 2026. Tenth iteration.*
*v10 = v9 + red-pen remediation from critical architecture review. All major metaphor-as-proof issues resolved; prior art named; lattice formalized; scope clarified.*

---

## Executive Summary

Markdown is a **human-readable orchestration substrate** — not an execution environment. Its consumers (parsers, runtimes, LLM agents, Pandoc filters, notebook kernels) do the executing. The emerging production architecture is best understood as **deterministic scaffolding around probabilistic reasoning cores**: a pattern where deterministic filesystems, schemas, hooks, and pipelines wrap a nondeterministic LLM reasoner.

> **Core architectural claim (calibrated):**
> *"The LLM is not the system. It is a probabilistic reasoning subsystem inside a deterministic operating environment. Orchestration, state, and tooling quality determine production reliability — not model capability alone."*

**Prior art acknowledgement.** Individually, the ideas in this paper have strong prior art: PostgreSQL-as-state-kernel (DBOS, Stonebraker/Zaharia; Letta/Aurora); deterministic governance of probabilistic engines (Temporal, LangGraph, DBOS; Ramadge–Wonham supervisory control; FIDES, CaMeL, RTBAS for IFC-on-LLMs); lattice-based authority (Denning 1976, Sandhu 1993); markdown-as-interface (Obsidian Bases, ICM/Van Clief); audit receipts (Marten event sourcing, W3C PROV, Temporal Event History); local-first collaboration (Automerge/Patchwork, GAIOS/Ink & Switch). **The contribution of this paper is their combination for personal-scale governed AI on a Postgres-backed markdown stack.** That specific synthesis has no prior shipping implementation.

**Risk classification (NIST AI RMF MAP-1.1 / EU AI Act):**

```yaml
risk_tier: HIGH
nist_rmf_category: MAP-1.1
eu_ai_act_class: "High-Risk candidate — Annex III §5(b), AI systems in financial services"
eu_ai_act_enforcement_date: "2026-08-02"
```

> **Regulatory note:** EU AI Act high-risk obligations apply from **2 August 2026** (Regulation (EU) 2024/1689). Article 99 penalty tiers: (1) €35M or 7% worldwide annual turnover for Article 5 prohibited-practice violations; (2) €15M or 3% for provider/deployer obligation breaches; (3) €7.5M or 1% for supplying incorrect information to authorities.

**Intended use:** Quant research, staged AI-assisted analysis pipelines, reproducible document workflows, personal-scale governed PKM.

**Out of scope:**
- Real-time high-frequency execution without human operator review
- Unilateral autonomous capital deployment
- OMS-grade systems with microsecond latency or adversarial capital-markets constraints
- Multi-tenant SaaS at scale (see Part 23: Scope and Scale)

**Operator role (NIST RMF GOVERN-1.2):** A named, credentialed person with authority to approve stage promotions and RED/AMBER gate escalations. The operator is not an LLM.

**Environment separation matrix (IEEE 3407-2025 §5.5):**

| Environment | Broker | Capital | Approval Required | Receipts | Auto-Rollback |
|---|---|---|---|---|---|
| Paper | Alpaca Paper | Simulated | No | Optional | No |
| Staging | Alpaca Paper | Simulated | Yes (operator) | Required | Yes |
| Production | Alpaca Live | Real | Yes (dual operator) | Required (WORM) | Yes |

---

## Part 1 — Corrected Mental Model: Layers of a Markdown-Orchestrated System

### The Five-Layer Stack

| Layer | Component | Role | Deterministic? |
|---|---|---|---|
| Interface | Markdown files | Declarative control surface | ✅ |
| Memory | Filesystem | Durable artifact state | ✅ |
| Config | YAML frontmatter | Metadata, routing, schema | ✅ |
| Tooling | MCP servers | Tool-invocation transport layer | ✅ (invocation) |
| Reasoning | LLM | Probabilistic inference engine | ❌ |

**Execution is never in the markdown.** It lives in Pandoc, panflute filters, Codebraid, shell wrappers, AI agent runtimes, YAML parsers, and MCP servers.

> This layered separation — inert artifacts, a model operating inside a surrounding software harness, and the execution substrate beneath — is the organizing frame of a 2026 survey from UIUC, Meta, and Stanford, *Code as Agent Harness* (Ning et al., arXiv:2605.18747). It defines an agent harness as “the software layer that surrounds an LLM with tools, APIs, sandboxes, memory, validators, permission boundaries, execution loops, and feedback channels, thereby turning a stateless model into a functional agent,” and organizes agentic systems into three layers — harness interface, harness mechanisms, and scaling the harness — that map onto the stack described here. The survey *frames* this view; it is a synthesis of existing systems, not an experimental result, and remains a non-peer-reviewed preprint.

**Closest prior work:** DBOS (Stonebraker, Zaharia, Madden — MIT/Stanford) is the most direct expression of "OS on a database"; it runs on Linux/Firecracker and provides durable workflow + native Postgres state + agent SDK integrations. This paper targets personal-scale PKM rather than general OS replacement. If you want a general-purpose durable-workflow-on-Postgres stack without the markdown/CRDT/governance legs, DBOS is the right starting point.

### Part 1.5 — Intended Use & Out-of-Scope Cases

*(ISO/IEC 42001:2023 §4; EU AI Act Annex IV §1(a))*

**Intended use cases:**
- Staged quant research pipelines with human-in-the-loop operator approval at every gate
- Reproducible document builds (Pandoc/panflute/Codebraid)
- AI-assisted analysis with schema-validated outputs
- Prompt provenance and audit logging for regulated environments
- Personal-scale governed PKM with local-first sync

**Out-of-scope / prohibited use cases:**
- Autonomous capital deployment without operator approval
- Real-time HFT execution (latency profile incompatible; use Compiled AI artifacts instead)
- High-frequency trading / OMS-grade systems with hard real-time and adversarial constraints
- Processing PHI without a signed BAA and HIPAA-eligible inference path
- Any use classified as prohibited under EU AI Act Article 5

### Part 1.6 — Operator Role Definition

*(NIST AI RMF GOVERN-1.2)*

An **operator** is a named person or named team who:
1. Has read and understood `domain-rules.md` and `execution-doctrine.md`
2. Has access credentials to the audit log and `execution_receipts/`
3. Is authorized to approve stage promotions (AMBER gates) and reject RED gate outputs
4. Is authorized to invoke the rollback runbook
5. Is **not** an LLM or automated script — approval requires a human identity token

### Artifact State vs. Execution State

| State Type | Where It Lives | Example |
|---|---|---|
| Artifact state | Filesystem (markdown, YAML, outputs) | Stage CONTEXT.md, analysis-config.yaml |
| Execution state | Agent runtime (transient) | In-flight tool calls, token attention, reasoning chain |

Git captures artifact state; it does not capture execution state. For complete execution-state capture, use `PromptExecutionReceipt` (Part 11).

---

## Part 2 — AI-Native DevOps: The Full Abstraction Stack

```
Markdown      = interface / control plane
Filesystem    = memory (deterministic, diffable, versionable)
YAML          = metadata / routing / schema contracts
LLM           = probabilistic reasoning subsystem (stochastic policy with tool-call side effects)
Pandoc        = document compiler
MCP           = tool-invocation transport (NOT a security boundary — see Part 8)
MCP tools     = device drivers (execution)
Tool schemas  = interface contracts
Agent runtime = scheduler / process manager
Git           = audit log + artifact version control (NOT execution-state log)
Postgres      = state kernel and provenance ledger (NOT OS kernel — see below)
```

> **PostgreSQL framing (corrected).** Postgres is the **deterministic state kernel and provenance ledger** of this system. It is durable, transactional, queryable, and WAL-audited. It is **not** an OS kernel: it is a user-space process that depends on Linux for scheduling, IPC (shared memory + semaphores), memory, and disk I/O. It has no preemptive task scheduler, no memory protection between sessions, and no syscall interface. Mapping it as "the kernel" is useful as a *state-kernel* metaphor; it is false as an *OS-kernel* isomorphism. For workflow scheduling, pair with DBOS or Temporal. For coarse access control, use RLS. For IPC-style events, use LISTEN/NOTIFY.

---

## Part 3 — Deterministic Scaffolding Around Probabilistic Cores

This is the dominant production architecture pattern in 2026.

> Chaining model calls in sequence degrades reliability: each step conditions on the previous step’s output, so errors are inherited rather than cancelled. As a first-order idealization, if each of N steps succeeds independently with probability p, end-to-end success is p^N — a ten-step chain at 95% per-step accuracy yields roughly 60% end-to-end (0.95¹⁰ ≈ 0.599). This independent-error model is a lower-bound intuition, not a measurement. Sinha et al. (arXiv:2509.09677, ICLR 2026) document *self-conditioning*, in which per-step accuracy falls as a trajectory lengthens, so real errors are positively correlated and decay can exceed what p^N predicts; conversely, retries and verification gates raise the effective per-step reliability. METR (arXiv:2503.14499) gives the empirical task-horizon picture, and Cemri et al. (MAST, arXiv:2503.13657) find that multi-step agent failures are driven more by system design and inter-agent misalignment than by base-model quality. The architectural response is to insert deterministic steps — contracts, finite-state checks, hard-coded policies — that halt the compounding loss: a deterministic gate at a critical step resets reliability for that checkpoint.

**Prior art for this pattern.** This mirrors:
- **Supervisory control of a stochastic plant** (Ramadge–Wonham, 1987): deterministic supervisor gates a non-deterministic plant.
  - A 2026 control-theoretic treatment makes this lineage explicit: Eslami & Yu (arXiv:2603.10779) model an agentic system as embedded within a feedback control loop and formalize “agency as hierarchical decision authority over the control architecture,” giving an augmented closed-loop representation and explicit design constraints for safety-critical settings. This is the formal complement to the supervisory-control analogy already invoked here — the deterministic gate is a feedback element, not merely a checkpoint.
- **Temporal / DBOS durable workflows:** deterministic workflow code; non-deterministic activities (LLM calls, tool invocations) are fenced, retried, and logged.
- **IFC for LLM agents:** FIDES (Microsoft Research, arXiv:2505.23643), CaMeL (Google DeepMind/ETH Zürich, arXiv:2503.18813), RTBAS (CMU, arXiv:2502.08966). All three implement "non-deterministic planner gated by deterministic enforcer" with formal lattice labels.
  - The principle that the artifact-producing step and the verifying step must not share authority has direct primary-source support beyond the IFC work cited above: Reflexion (Shinn et al., NeurIPS 2023, arXiv:2303.11366) separates Actor, Evaluator, and Self-Reflection roles, and CodeAct (Wang et al., ICML 2024, arXiv:2402.01030) grounds agent actions in executable code checked by the runtime rather than by the model’s own assertion. The *Code as Agent Harness* survey attributes the anti-pattern these avoid — an agent’s biased tests passing its own buggy code — to “circular reasoning” and “mode-collapse” (§4.1.1).

> **Vocabulary alignment:**
> - "Validator gates" in this paper → IFC enforcement points (cf. FIDES §3.2)
> - "Capability tags" → CaMeL-style variable-level capability annotations
> - "Audit receipts" → Marten-style immutable event log + projections (cf. Part 11)

> **Trading analogy scope.** The similarity between this architecture and OMS/trading systems is **structural only** (control pattern): probabilistic generator, deterministic gate, state-of-record, kill-switch, budget governor. We do **not** claim OMS-level latency, adversarial hardness, or capital-markets regulatory coverage. Trading has microsecond real-time constraints and adversarial P&L outcomes; this system does not. The pattern is borrowed; the operational semantics are not.

### Workflow determinism vs. activities (Temporal/DBOS discipline)

- **Workflow layer (deterministic):** pure functions over state, replayable from the event log. All validator gates, kill-switch logic, capacity checks, and lattice policy decisions live here.
- **Activity layer (non-deterministic):** LLM calls, MCP tool invocations, network I/O. Wrapped for idempotence, retried by policy, logged as events.

**Design rule:** *Workflows decide; activities act.* Any safety-critical guardrail belongs in deterministic workflow code.

### Compiled AI: Zero-Token Deterministic Execution

*(arXiv:2604.05150)*

LLMs are leveraged exclusively during a compile-time generation phase to emit static, executable code artifacts. Deployed workflows execute deterministically as native code without further API calls — measured transaction-stage latency: 4.5ms (450× improvement over direct LLM runtimes).

**Constrained decoding at the LLM boundary.** Wherever the system expects structured output from an LLM, a constrained-decoding layer enforces the schema at generation time:
- **Grammar-based decoding:** XGrammar (integrated in SGLang, vLLM, TensorRT-LLM) enforces JSON Schema / EBNF with <40 µs overhead per token.
- **Library-mediated schemas:** Outlines, `llguidance`, DSPy.

**Design rule:** "Compiled AI execution" always implies grammar-constrained decoding at the LLM boundary. Model outputs are typed data, not untrusted free text.

### The Three Enforcement Layers

| Enforcement Type | Mechanism | Reliability |
|---|---|---|
| CLAUDE.md instructions | Advisory context (user-message tier) | Probabilistic |
| Schemas (Pydantic/JSON Schema + constrained decoding) | Structured output constraints | High |
| Hooks (.claude/settings.json) | PreToolUse/PostToolUse callbacks | Deterministic |

### Reliability Is a Property of the Gates, Not the Model

The consequence of the compounding argument above is the claim this paper stakes: end-to-end reliability is dominated by the quality of the gates, not by which model occupies the reasoning slot. A gate that blocks promotion until a deterministic contract passes interrupts error inheritance — it prevents a downstream stage from treating an upstream stage’s mistake as a verified premise. The *Code as Agent Harness* survey (arXiv:2605.18747, §4.1.1) corroborates the mechanism from deployed systems: it describes a test executor that “is a deterministic Python script (not an LLM) which cleanly separates reasoning from execution and grounds the feedback signal in objective program behavior.”

This is a falsifiable claim, and it is designed to be tested directly. Experiment 03 in `docs/thesis-experiments.md` holds the gates fixed and swaps the model across tiers (Axis A), then holds the model fixed and varies gate strictness (Axis B); the thesis predicts roughly flat metrics on Axis A and sharply varying metrics on Axis B, and is falsified if Axis A metrics correlate strongly with model size. That experiment is **designed but not yet run** — it requires a Stage 02 synthesis agent the current prototype does not implement (only Stage 00 ingestion exists). The claim is stated here as a prediction with a specified falsification test, not as a demonstrated result.

---

## Part 4 — The Memory Hierarchy: LLM Context as Cost-Tier Cache

*(arXiv:2603.09023 — "The Missing Memory Hierarchy: Demand Paging for LLM Context Windows," Tony Mason, March 2026)*

Key measurement: across 857 production sessions and 4.45 million effective input tokens, **21.8% was structural waste**. The Pichay demand-paging system reduced context consumption by up to 93% in production.

> Keeping the active context small is a correctness measure, not only a cost measure. The canonical result (Liu et al., “Lost in the Middle,” TACL 2024) shows a U-shaped accuracy curve in which information placed in the middle of a long context is used least reliably, even by models built for long contexts; stricter follow-ups (NoLiMa, ICML 2025) show many models claiming 128K-token windows dropping below half their short-context accuracy by 32K tokens. Loading only the relevant stage folder, and only the constraints section of the rules, keeps the working context inside the reliable regime.

### The Full Memory Hierarchy

| Level | OS Analogy | Persistence | Source |
|---|---|---|---|
| L1 — Generation Window | CPU L1 cache | Turn lifetime | arXiv:2603.09023 |
| L2 — Working Set | CPU L2 / RAM | Session lifetime | arXiv:2603.09023 |
| L3 — Session History | Swap partition | Session lifetime | arXiv:2603.09023 |
| L4 — Persistent Memory | Local storage | Permanent | arXiv:2603.09023 |
| L5 — Git History † | Archival | Permanent | **Extended by author** |

> † Author extension. L5 is not in Mason's original hierarchy.

### Incremental Context Snapshots

PostgreSQL's native materialized views fully recompute on `REFRESH MATERIALIZED VIEW`. For incrementally maintained "context snapshots":
- **In-Postgres:** `pg_ivm` for incremental view maintenance.
- **Differential dataflow:** Materialize or Feldera — compile SQL into dataflows that update proportional to input delta, not full dataset.

**Design rule:** "Compiled context view" means **incrementally maintained view over the Postgres state kernel**, not a naive full refresh.

### Pichay: Virtual Memory Demand Paging for LLMs

- **Context Eviction:** stale files/tool outputs evicted from L1; lightweight retrieval handle written in their place.
- **Page Fault Detection:** proxy intercepts references to paged-out content and re-fetches on demand.
- **Inverted Cost Model:** for LLMs, keeping tokens in context is expensive (quadratic self-attention); re-fetching is cheap. Aggressive eviction is optimal.

---

## Part 5 — Jake Van Clief: Correctly Calibrated

**arXiv:2603.16021v2** — *Interpretable Context Methodology: Folder Structure as Agentic Architecture* (Van Clief + McDermott, March 2026)

| Attribute | Status |
|---|---|
| Publication venue | arXiv preprint (not peer-reviewed journal) |
| Peer review | None at time of writing |
| Core ideas | Credible, applicable, consistent with ecosystem trends |
| Correct description | "An emerging methodology" |
| Incorrect description | "The dominant architecture" or "canonical standard" |

**Defensible strong claim:** *"ICM reframes orchestration around interpretable filesystem state rather than opaque agent graphs."*

---

## Part 6 — CLAUDE.md: Corrected Behavior Model

CLAUDE.md content is delivered as a **user-message after the system prompt** (not forced system config). For guaranteed execution, use hooks. For hard constraints, use `.claude/settings.json`.

### Behavioral Category Reliability

| Category | Enforcement | Use Instead |
|---|---|---|
| Structural (file paths, build commands) | High | CLAUDE.md fine |
| Behavioral ("Never touch production") | Probabilistic | Use hooks |
| Hard constraints ("Block this Bash command") | Hooks only | settings.json |

---

## Part 7 — SKILL.md: Convention, Not Standard

Current status: a **convention** — not an RFC, formal spec, or interoperable standard. No conformance testing. Behavior varies across Claude Desktop, Claude Code, Cursor, Cline, OpenCode, RooCode, Aider.

Token discipline: CLAUDE.md ≤800 tokens (every-turn cost). SKILL.md ≤200 lines (loaded on demand).

---

## Part 8 — MCP: The Tool-Invocation Transport (Correctly Framed)

MCP standardizes invocation semantics. It does **not** provide lattice IFC primitives, formal capability semantics, or sandbox enforcement.

> ⚠️ **MCP is not a security boundary.** Per Knostic security researchers (2026): 1,862 MCP servers found exposed to public access without authentication. Per the MCP specification (2025-11-25): *"Tools represent arbitrary code execution and must be treated with appropriate caution."* Treat MCP tool responses as untrusted input requiring explicit validation. Your "MCP controls" need to wrap MCP with FIDES-style label propagation; MCP alone does not give you that.

### MCP Threat Model

*(arXiv:2504.03767, MCP Safety Audit, 2025)*

| Threat Vector | Mitigation |
|---|---|
| Prompt injection | Validate every tool response before execution decisions |
| Tool shadowing / server impersonation | Pin server URLs; verify schemas at session start |
| Overprivileged tokens | Least-privilege token scoping per tool |
| Denial-of-wallet loops | Rate limits in AI Gateway; budget caps per session |
| Unauthorized data exfiltration | Output validation; network egress controls |

**Hard rule:** Log every MCP tool invocation as part of `PromptExecutionReceipt` (Part 11).

---

## Part 9 — Filesystem vs. Vector Retrieval

### Retrieval Benchmarks (fully cited)

**Finance/RAG:** T2-RAGBench (23,088 queries), metric = Number Match:
- BM25: Recall@5 = 0.644 | Dense: 0.587 | Hybrid RRF: 0.695 | Hybrid + Cohere reranker: 0.816
*(arXiv:2604.01733, Table I)*

**Rule:** For every retrieval claim, attach (dataset, metric, baseline, top-k, reranker on/off).

### Production Retrieval

> ⚠️ **`rank-bm25` is pedagogy-only** (last release 2022; no preprocessing). Production: `bm25s` (Xing Han Lu, 2024) in-process, or Elasticsearch/OpenSearch at scale.

---

## Part 10 — Typed Orchestration / Schema-Constrained Output

All Pydantic code uses v2 patterns (pinned ≥2.13.4). The schema IS the prompt — field descriptions become instructions to the model (arXiv:2410.18146, Meaning Typed Prompting).

**Prior art for structured-output substrate:** DSPy (compiles prompt programs against a metric), XGrammar/SGLang/Outlines (grammar-constrained decoding), `llguidance` (MSFT).

```python
from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Literal

class StageOutput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    artifact_id: str = Field(description="Unique identifier, kebab-case")
    status: Literal["pass", "fail", "needs-review"]
    confidence: float = Field(ge=0.0, le=1.0)
    constraint_status: Literal["GREEN", "AMBER", "RED"]
    rationale: str = Field(max_length=200)
    operator_approval_required: bool
```

---

## Part 11 — Prompt Provenance & AI Audit Logging

### Why Git Is Insufficient

Git captures artifact state. It does not capture: which prompt generated which output; which model/tokenizer version was active; what context was loaded; what tool calls were made; what it cost.

### Prior art

- **W3C PROV data model:** standard vocabulary for provenance entities, activities, agents.
- **Marten on Postgres:** immutable event log + inline projections for invariants + async projections for read models. The "audit receipt" pattern is Marten's event stream, applied to LLM sessions.
- **Temporal Event History:** replay rebuilds state; side effects are fenced in activities.

### Regulatory requirements

- EU AI Act Art. 26(6): deployers retain logs minimum 6 months.
- FINRA-regulated workflows: 6 years.
- Storage class: WORM or equivalent append-only immutable store.

### Production Prompt Provenance Schema (Pydantic v2)

```python
from pydantic import BaseModel, ConfigDict
from datetime import datetime, timezone
import hashlib, uuid

class CostFields(BaseModel):
    tokens_in_uncached: int = 0
    tokens_in_cached: int = 0
    tokens_out: int = 0
    usd_estimated: float = 0.0
    cache_hit_ratio: float = 0.0

class PromptExecutionReceipt(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    receipt_id: str
    timestamp: str
    model_id: str
    model_version: str
    tokenizer_version: str
    inference_geo: str
    cache_hit: bool = False
    prompt_hash: str
    context_manifest: list[str]
    tool_invocations: list[dict]  # includes label at each invocation
    output_hash: str
    input_labels: list[str]       # lattice labels on inputs (Part 12)
    output_label: str             # lattice label on output
    declassification_occurred: bool = False
    operator_id: str | None
    stage_id: str
    cost: CostFields = CostFields()
```

> **Signing:** Sign receipts with Ed25519 for repudiation resistance. Persist in append-only store. Run daily reconciliation against billing CSV.

---

## Part 12 — Authority Labels and Lattices (Formalized)

### 12.1 Purpose

Security labels describe how data may flow through tools, workflows, and users. The structure is a **finite lattice** (Denning, *Comm. ACM* 19(5):236–243, 1976; Sandhu, *IEEE Computer*, 1993): a partially ordered set where every pair has a well-defined join (∨) and meet (∧).

### 12.2 The six-class label lattice

| Label | Confidentiality | Integrity |
|---|---|---|
| `PUBLIC_UNTRUSTED` | PUBLIC | UNTRUSTED |
| `PUBLIC_TRUSTED` | PUBLIC | TRUSTED |
| `INTERNAL_UNTRUSTED` | INTERNAL | UNTRUSTED |
| `INTERNAL_TRUSTED` | INTERNAL | TRUSTED |
| `RESTRICTED_UNTRUSTED` | RESTRICTED | UNTRUSTED |
| `RESTRICTED_TRUSTED` | RESTRICTED | TRUSTED |

Dimensions order as: `PUBLIC < INTERNAL < RESTRICTED` and `UNTRUSTED < TRUSTED`.

### 12.3 Partial order, join, meet

**Partial order.** `A ≤ B` iff `A.confidentiality ≤ B.confidentiality` AND `A.integrity ≤ B.integrity`.

**Bottom (⊥):** `PUBLIC_UNTRUSTED`. **Top (⊤):** `RESTRICTED_TRUSTED`.

**Join** `a ∨ b`: `max(confidentiality)` × `max(integrity)` — reading from both produces the more sensitive, more trusted result.

**Meet** `a ∧ b`: `min(confidentiality)` × `min(integrity)` — the overlap is the less sensitive, less trusted of the two.

Note: `PUBLIC_TRUSTED` and `INTERNAL_UNTRUSTED` are **incomparable** (confidentiality goes up, integrity goes down). This is correct and expected in a product lattice.

### 12.4 Flow rules and declassification

**Confidentiality:**
- No-read-up: subject at `L` may only read data `D` where `D.confidentiality ≤ L.confidentiality`.
- No-write-down: subject at `L` may only write to sink `S` where `L.confidentiality ≤ S.confidentiality`.

**Integrity:**
- No-read-down: high-integrity stages must not blindly consume lower-integrity data without validation.
- No-write-up: low-integrity components may only *propose* writes to high-integrity sinks, gated by a validator.

**Declassification:** A dedicated declassifier workflow may lower confidentiality only if:
1. It runs at a label ≥ source label.
2. Output is constrained by a schema appropriate to the target label.

### 12.5 Relation to FIDES and CaMeL

- **FIDES** (Costa et al., arXiv:2505.23643) uses a 2×2 product lattice: `confidentiality ∈ {public, private}` × `integrity ∈ {untrusted, trusted}`. Our six-class lattice adds an `INTERNAL` intermediate tier. **Start with FIDES 2×2 for v0.1; extend to six classes only when needed.**
- **CaMeL** (Debenedetti et al., arXiv:2503.18813): capability tags attach to values at lattice points. Lattice governs flow; capability governs "who may act with this value."

### 12.6 Enforcement points

1. **Tool call planner:** checks data label vs. tool declared label before every MCP invocation.
2. **Workflow validator gates:** run at `RESTRICTED_TRUSTED`; can accept, reject, or route to declassification.
3. **Audit receipts:** every step records input labels, output label, declassification events, operator ID.

### 12.7 Vocabulary corrections (v9 → v10)

| v9 term | v10 replacement |
|---|---|
| "Six-Band Authority Lattice" | "six-class label lattice" |
| "Double Tesseract Authority Model" | "product lattice of confidentiality × integrity dimensions" |
| "ring enforcement" | "lattice-based information-flow control" / "validator gate" |

### 12.8 Lattice query substrate

**Datalog is the preferred substrate for lattice traversal queries**, not recursive CTEs.

- Recursive CTEs degrade past ~10⁴ nodes; no memoization across queries.
- `pg_mentat` embeds Datomic-compatible Datalog inside PostgreSQL — keeps lattice rules and facts in the same state kernel.
- Datalevin (standalone) is orders of magnitude faster than Datomic on recursive queries.

**Design rule:** lattice traversal queries SHOULD be implemented as Datalog rule sets. Recursive CTEs are acceptable only for prototypes or shallow hierarchies (≤6 levels).

---

## Part 13 — Context Anxiety, Compaction, Tool-Result Clearing

Frontier models may wrap up tasks prematurely when sensing context limit approach.

**Mitigations:**
- **Compaction (`/compact`):** lossy, whole-transcript operation. Resets context window while preserving structural facts.
- **Tool-Result Clearing (`/clear-tool-results`):** replaces large `tool_result` blocks with lightweight placeholders. Reclaims up to 90% of active token space while preserving reasoning continuity.

---

## Part 14 — Document Build Pipeline

- pandoc pinned to **3.9.0.2**
- panflute pinned to **2.3.0**

---

## Part 22 — AI Gateway & Cost Governance

### Capability and access control

**RLS is tenant isolation, not capabilities.**

RLS provides coarse-grained row filtering. It is not a capability system: no unforgeable handles, no delegation primitives, no revocation. For capability-style delegation:
- Capabilities = signed tokens (not UUIDs alone; they leak via logs).
- Attribute-based policy engine (OPA, Cedar, or equivalent) for fine-grained rules.
- **Ink & Switch Keyhive** (in GAIOS) is the published local-first capability reference.

**Design rule:** RLS protects table slices. Capability delegation and IFC constraints live in the application and policy layer.

### Budget governance

- Per-session and per-stage token/USD budget caps enforced at the workflow layer (deterministic).
- Daily reconciliation against Anthropic billing CSV.
- Alert when `usd_estimated` exceeds stage budget by >10%.
- WORM receipt storage for audit.

> The cost case for a chokepoint with hard budget bounds is grounded in measured agent economics. The Stanford Digital Economy Lab’s analysis of agentic coding found agentic tasks consuming on the order of 1000× the tokens of plain chat in a controlled setting, with up to 30× variance on identical runs, driven mainly by input (re-sent context) rather than output. The 1000× figure is the controlled-study extreme; the production multiplier is smaller — Anthropic reports multi-agent systems using roughly 15× chat tokens, and practitioner estimates cluster around 5–30× — so the gateway’s budget ceiling should be sized to the production range, with the controlled figure as the worst case it must survive.

---

## Part 23 — Scope and Scale

**This design is explicitly personal-scale.** At single-user and small-team scale:
- PG-RLS works well (no 10K+ tenant pathologies).
- pgvector + pgvectorscale is production-ready to hundreds of millions of vectors.
- Datalog and recursive queries are fast enough.
- Durable workflows (DBOS/Temporal) are low-overhead.

**Scaling to multi-tenant SaaS would require re-evaluating:**
- RLS vs. schema-per-tenant (Propelius reports schema-per-tenant winning at large tenant counts with composite indexing).
- pgvector beyond ~10⁸ vectors (dedicated vector DB territory).
- Single-writer Postgres backpressure under high concurrency.

**CRDT collaboration:** CRDTs are stored as Automerge/Yjs `bytea` blobs in Postgres, projected into queryable tables. This is **not** row-level CRDTs (an unsolved problem). The pattern mirrors cr-sqlite applied to Postgres.

**Obsidian compatibility:** the goal is an **Obsidian-compatible vault** (plain markdown files on disk) with a Postgres-backed state kernel, governed AI, and event-sourced provenance. This is **not** "replace Obsidian's plugin ecosystem" — Templater, Dataview, Excalidraw, Canvas, Bases represent ~10 person-years of community work. The design adds what Obsidian cannot: transactionality, audit, IFC governance, and AI co-authoring with provenance.

**Competitors snapshot:**

| System | Postgres kernel | IFC/governance | CRDT collab | Markdown-native | SQL-queryable |
|---|---|---|---|---|---|
| Obsidian + Bases | ❌ | ❌ | ❌ | ✅ | Partial |
| Anytype | ❌ | ❌ | ✅ | ❌ | ❌ |
| DBOS | ✅ | Partial | ❌ | ❌ | ✅ |
| Letta | ✅ | ❌ | ❌ | ❌ | ✅ |
| Patchwork/GAIOS | ❌ | ✅ | ✅ | ✅ | ❌ |
| **This design** | ✅ | ✅ | ✅ (bytea) | ✅ | ✅ |

---

## Appendix — Selected Prior Art

### IFC and capabilities
- Denning, D.E. (1976). *A lattice model of secure information flow.* Comm. ACM 19(5):236–243.
- Sandhu, R.S. (1993). *Lattice-based access control models.* IEEE Computer 26(11):9–19.
- Costa et al. (2025). *FIDES: Securing AI Agents with Information-Flow Control.* arXiv:2505.23643.
- Debenedetti et al. (2025). *CaMeL: Defeating Prompt Injections by Design.* arXiv:2503.18813.
- Evertz et al. (2025). *RTBAS.* arXiv:2502.08966.
- Miller, M. (2006). *Robust Composition: Towards a Unified Approach to Access Control and Concurrency Control.* (object-capability model)
- Ink & Switch. (2025–2026). *GAIOS / Keyhive.* UK ARIA Safeguarded AI Programme.

### Workflow / event sourcing
- Temporal (temporal.io) — durable workflow engine; deterministic workflows + fenced activities.
- DBOS (dbos.dev) — Stonebraker/Zaharia; OS-on-database pattern on Postgres.
- Miller, J. *Marten* (martendb.io) — production event sourcing + CQRS on Postgres (.NET).
- EventStoreDB / Kurrent — language-agnostic event store.
- W3C PROV — standard provenance data model.

### Local-first / CRDT
- Automerge 3.0 (automerge.org, July 2025) — CRDT; 10× memory reduction vs. v2.
- Yjs (yjs.dev) — production-proven CRDT; Notion, Linear.
- Litt, G. & van Hardenberg, P. (2025). *Patchwork.* Ink & Switch.
- cr-sqlite (vlcn.io) — CRDT over SQLite; closest published SQL-CRDT primitive.

### PKM / markdown
- Obsidian Bases (obsidian.md, v1.9, 2025) — YAML-frontmatter-as-DB with table views.
- Anytype (anytype.io) — CRDT + E2EE + IPFS; strong on collab, weak on SQL.
- Van Clief, J. & McDermott (2026). *ICM: Interpretable Context Methodology.* arXiv:2603.16021v2.

### Query substrate
- Datalevin (github.com/juji-io/datalevin) — Datomic-compatible Datalog; Q4 benchmark: 2.9ms vs. Datomic 40s.
- pg_mentat — Datomic-style Datalog inside PostgreSQL.
- Materialize / Feldera — differential dataflow; incremental SQL maintenance.
- Mason, T. (2026). *The Missing Memory Hierarchy.* arXiv:2603.09023.

### Agent reliability and long-horizon execution
- Ning, X., Tieu, K., Fu, D., Wei, T., Li, Z., Bei, Y., et al. (2026). *Code as Agent Harness: Toward Executable, Verifiable, and Stateful Agent Systems.* arXiv:2605.18747.
- Eslami, A. & Yu, J. (2026). *A Control-Theoretic Foundation for Agentic Systems.* arXiv:2603.10779.
- Sinha, A., Arun, [TODO: complete author list], & Goel (2026). *The Illusion of Diminishing Returns: Measuring Long-Horizon Execution in LLMs.* arXiv:2509.09677 (ICLR 2026).
- METR (2025). *Measuring AI Ability to Complete Long Tasks.* arXiv:2503.14499.
- Cemri, M. et al. (2025). *Why Do Multi-Agent LLM Systems Fail?* (MAST) arXiv:2503.13657.
- Shinn, N. et al. (2023). *Reflexion: Language Agents with Verbal Reinforcement Learning.* NeurIPS 2023. arXiv:2303.11366.
- Wang, X. et al. (2024). *Executable Code Actions Elicit Better LLM Agents.* (CodeAct) ICML 2024. arXiv:2402.01030.

### Long-context behavior
- Liu, N.F. et al. (2024). *Lost in the Middle: How Language Models Use Long Contexts.* TACL 12:157–173. arXiv:2307.03172.
- Modarressi, A. et al. (2025). *NoLiMa: Long-Context Evaluation Beyond Literal Matching.* ICML 2025. arXiv:2502.05167.

### Agent token economics
- Stanford Digital Economy Lab (2025). *How Do AI Agents Spend Your Money? Analyzing and Predicting Token Consumption in Agentic Coding Tasks.*
- Anthropic (2025). *How we built our multi-agent research system.* (engineering blog.)

---

*v10-draft.md — apply ADR-001 through ADR-005 for architectural decision rationale. See docs/adr/.*
