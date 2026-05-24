# v9 Parts 12–23

*Continuation of `docs/v9.md` (which truncates after Part 11). All parts below are v9-canonical. For the corrected/updated versions of these sections, see `docs/v10-draft.md`.*

---

## Part 12 — Eg-walker, CodeCRDT, and Collaborative Editing Substrate

*(arXiv:2409.14252 — "Collaborative Text Editing with Eg-walker," Kleppmann et al., 2024)*

### The Eg-walker Algorithm

Eg-walker is a CRDT-compatible operational transformation algorithm that:
- Solves the "interleaving anomaly" that plagues naive OT implementations in multi-user concurrent editing
- Achieves O(log n) complexity per operation (vs. O(n²) for many earlier OT algorithms)
- Produces output identical to a correctly-implemented RGA or Yjs CRDT
- Is suitable as the underlying algorithm for **CodeCRDT** — collaborative code editing with structural awareness

### CodeCRDT: Structural Collaborative Editing

CodeCRDT extends Eg-walker with AST-level awareness:
- Edits are represented as operations on the AST, not raw character positions
- Conflicts at the AST level (e.g., two agents both renaming a function) are surfaced as structured merge conflicts rather than character-level overlaps
- **Relevance to this system:** any AI agent that collaboratively edits markdown or code artifacts with a human operator should use a CodeCRDT-compatible substrate to prevent silent data corruption on concurrent edits

### Integration point

In the v9/v10 architecture:
- CRDT documents (Automerge or Yjs, which implement Eg-walker-equivalent semantics) are stored as `bytea` blobs in Postgres (ADR-002)
- The Eg-walker algorithm governs merge semantics when two clients diverge
- AST-level conflict detection (CodeCRDT) is applied when editing `.md` files with structured frontmatter

---

## Part 12.5 — Continuity Layer / DTCM

*(arXiv:2604.17273 — "Distributed Transactional Context Memory," 2026)*

### The Problem: Context Discontinuity

In multi-turn and multi-agent workflows, context state is fragmented across:
- In-flight LLM context windows (ephemeral)
- Tool call results (partially persisted)
- Filesystem artifacts (persisted, but not transactionally linked to the session that produced them)
- External memory stores (Letta, Zep, Mem0)

This fragmentation creates **context discontinuity**: a resumed session cannot reconstruct the exact state of a prior session, making deterministic replay impossible and audit reconstruction unreliable.

### DTCM: Distributed Transactional Context Memory

DTCM addresses this with three primitives:

1. **Context snapshots:** a named, versioned, transactionally consistent capture of the full context state at a point in time — analogous to a database savepoint
2. **Context transactions:** a sequence of context mutations (tool calls, LLM turns, artifact writes) that either commit atomically or roll back — preventing partial context corruption
3. **Context lineage:** a directed acyclic graph (DAG) of context snapshot parents, enabling "git blame for context" — any output can be traced back to the exact context state that produced it

### Integration with v9/v10 architecture

| DTCM primitive | v9/v10 implementation |
|---|---|
| Context snapshot | `PromptExecutionReceipt` + `context_manifest` field (Part 11) |
| Context transaction | Temporal/DBOS workflow step (ADR-005) |
| Context lineage | Marten-style event log; each event references parent receipt_id |

**Design rule:** Every workflow step that modifies context state must:
1. Record a `PromptExecutionReceipt` before and after the step
2. Link the post-step receipt to the pre-step receipt via `parent_receipt_id`
3. Persist both receipts to the append-only event log before returning

---

## Part 13 — Context Anxiety, Compaction, and Tool-Result Clearing

### Context Anxiety: Empirical Characterization

Frontier models (Claude 3.5/4, GPT-4o, Gemini 2.5) exhibit **context anxiety** — a measurable tendency to:
- Truncate logical reasoning steps when the context window is >70% full
- Wrap up tasks with "I've done what I can" rather than requesting a compaction
- Silently omit later items in multi-item lists when context pressure increases
- Produce shorter, less-detailed outputs in the final 20% of the context window

This is an **emergent behavior**, not a documented model feature. It is reproducible in quant workflows when stage context files exceed ~6,000 tokens.

### Mitigations

**1. Compaction (`/compact`)**
- Lossy, whole-transcript operation
- Flattens conversation history into a condensed summary
- Resets the context window while preserving high-fidelity structural facts
- **Use when:** session history >50% of context window and the session is ongoing
- **Risk:** reasoning chains are lost; only facts survive. Do not compact before a RED/AMBER gate decision.

**2. Tool-Result Clearing (`/clear-tool-results`)**
- Replaces `tool_result` content blocks with lightweight `<tool_result_cleared>` placeholders
- Preserves the `tool_use` block (reasoning trace) while dropping the payload (raw output)
- Reclaims up to 90% of active token space
- **Use when:** large tool responses (database dumps, full file reads) are no longer needed for ongoing reasoning
- Non-lossy for reasoning continuity; lossy for raw data access

**3. Proactive context budget enforcement**
- Set a session-level `max_context_tokens` threshold in the AI Gateway (Part 22)
- Trigger automatic compaction at 65% utilization
- Log compaction events as `PromptExecutionReceipt` entries with `compaction: true`

---

## Part 14 — Document Build Pipeline: Pinned Dependencies

### Pandoc

- **Pinned version:** `3.9.0.2`
- **Install:** `conda install -c conda-forge pandoc=3.9.0.2` or `cabal install pandoc-3.9.0.2`
- **Why pin:** Pandoc's Lua filter API and AST representation change between minor versions. Unpinned Pandoc in CI produces non-deterministic document builds.

### panflute

- **Pinned version:** `2.3.0`
- **Install:** `pip install panflute==2.3.0`
- **Why pin:** panflute's element API (e.g., `pf.RawInline`, `pf.Header`) can silently change between versions, breaking filters without errors.

### Codebraid

- Use with `--no-cache` in CI to ensure deterministic execution
- Pin the Python kernel version in `codebraid.yaml`

### Build command (canonical)

```bash
# Deterministic document build
pandoc \
  --from markdown \
  --to pdf \
  --filter panflute \
  --lua-filter filters/audit-stamp.lua \
  --metadata-file _config/doc-meta.yaml \
  --pdf-engine xelatex \
  -o output/report-$(date +%Y%m%d).pdf \
  docs/v10-draft.md
```

---

## Part 16 — Academic and Standards Lineage

### Correct Standards Citations

| Standard | Correct citation | Common error |
|---|---|---|
| IEEE documentation | ISO/IEC/IEEE 26514:2022 | "IEEE 26514" (missing ISO/IEC prefix) |
| NIST secure software | NIST SP 800-218A (SSDF Community Profile) | "NIST 800-218" (wrong document number) |
| AI risk management | NIST AI 600-1 (GenAI-specific, 2024) | Conflating with NIST AI RMF 1.0 (2023) |
| EU AI Act | Regulation (EU) 2024/1689 | "EU AI Act 2023" (wrong year; enacted 2024) |
| AI management system | ISO/IEC 42001:2023 | "ISO 42001" (missing IEC) |
| AI trustworthiness | ISO/IEC TR 24028:2020 | Rarely cited; relevant for bias documentation |

### Eg-walker Lineage

- **Direct predecessor:** Attiya et al., "Specification and Complexity of Collaborative Text Editing" (PODC 2016) — proved that any correct OT algorithm must handle the "interleaving problem"
- **CRDT lineage:** Shapiro et al., "A Comprehensive Study of Convergent and Commutative Replicated Data Types" (INRIA, 2011) — the canonical CRDT survey
- **Eg-walker:** Kleppmann et al. (arXiv:2409.14252, 2024) — unifies OT and CRDT, O(log n) per op

### NIST AI 600-1: 12 GenAI Risk Categories

1. CBRN Information (chemical, biological, radiological, nuclear)
2. Confabulation (hallucination)
3. Data Privacy
4. Data Provenance
5. Homogenization
6. Human-AI Configuration
7. Information Integrity
8. Information Security
9. Intellectual Property
10. Obscene/Abusive/Violent content
11. Sociotechnical Harms
12. Value Chain / Component Integration

---

## Part 17 — Production Readiness Checklist (v9)

### Gate 1: Document & Schema

- [ ] CLAUDE.md ≤800 tokens; structure-only, no behavioral rules
- [ ] All behavioral rules in `.claude/settings.json` hooks
- [ ] Pydantic v2 (≥2.13.4): `model_config`, `@field_validator`, `model_dump()`
- [ ] Pandoc pinned to 3.9.0.2; panflute pinned to 2.3.0
- [ ] All markdown files have valid YAML frontmatter (validated by `yamllint`)

### Gate 2: Retrieval & Memory

- [ ] `rank-bm25` replaced with `bm25s` (production) or Elasticsearch/OpenSearch (scale)
- [ ] All retrieval benchmarks cited with (dataset, metric, baseline, top-k, reranker)
- [ ] pgvector HNSW index tuned: `m=16`, `ef_construction=64`, `ef_search=40` minimum
- [ ] Context manifest recorded in every `PromptExecutionReceipt`

### Gate 3: Governance & Audit

- [ ] `PromptExecutionReceipt` emitted for every LLM call and tool invocation
- [ ] Receipts stored in append-only WORM store
- [ ] Receipt retention policy documented: 6 months (EU AI Act) or 6 years (FINRA)
- [ ] Operator registry (`_config/operator-registry.yaml`) current
- [ ] Kill-switch tested: verify RED gate blocks promotion end-to-end
- [ ] Model version and tokenizer version recorded in every receipt

### Gate 4: Cost & Budget

- [ ] Per-session token/USD budget cap configured in AI Gateway
- [ ] Daily reconciliation against Anthropic billing CSV scheduled
- [ ] Inference geo recorded (EU inference: 1.1× multiplier)
- [ ] Cache hit ratio monitored; alert if <30% on repeated workflows

### Gate 5: Model Migration

- [ ] Tokenizer version pinned and change-detected (Opus 4.6 → 4.7: up to 35% token increase)
- [ ] Regression test suite runs on model version change
- [ ] `context_manifest` git SHAs verified before replay

---

## Part 18 — KohakuRAG: Four-Level Retrieval Tree

*(KohakuRAG reference implementation, 2025)*

### Architecture

KohakuRAG organizes retrieval into a four-level tree to balance precision and recall:

```
Level 1: Document-level index    — metadata, title, tags, date
Level 2: Section-level index     — H2/H3 headings + paragraph summaries
Level 3: Chunk-level index       — 256-token overlapping chunks (50-token overlap)
Level 4: Sentence-level index    — individual sentences for precision re-ranking
```

Retrieval proceeds top-down: Level 1 filters documents, Level 2 filters sections, Level 3 retrieves chunks, Level 4 re-ranks sentences within winning chunks.

### NID Formula (Normalized Information Distance)

KohakuRAG uses NID for duplicate detection and near-duplicate filtering before indexing:

```
NID(x, y) = [max(K(x|y), K(y|x))] / max(K(x), K(y))
```

Where `K(x)` is the Kolmogorov complexity, approximated in practice by compressed file size (`len(zlib.compress(x))`). NID near 0 = near-identical; NID near 1 = unrelated.

**Practical use:** run NID on all vault documents before indexing; deduplicate any pair with NID < 0.15 to prevent retrieval pollution from near-duplicate notes.

### Production stack

| Component | Recommendation |
|---|---|
| BM25 index | `bm25s` (not `rank-bm25`) |
| Dense embeddings | `text-embedding-3-large` or `voyage-finance-2` for quant content |
| Reranker | Cohere Rerank v3 or `cross-encoder/ms-marco-MiniLM-L-6-v2` |
| Vector store | pgvector + pgvectorscale (personal scale); Qdrant/Pinecone (SaaS scale) |
| Deduplication | NID with zlib approximation, threshold 0.15 |

---

## Part 19 — AI Risk Register (ISO 42001 §6.1)

*Required under ISO/IEC 42001:2023 §6.1.2: "The organization shall identify risks and opportunities associated with the AI system."*

### Risk Register

| ID | Risk | Likelihood | Impact | Inherent Score | Controls | Residual Score | Owner |
|---|---|---|---|---|---|---|---|
| R-001 | Hallucinated financial data in stage output | HIGH | HIGH | CRITICAL | PromptExecutionReceipt; schema validation; RED gate; operator review | MEDIUM | Operator |
| R-002 | Prompt injection via MCP tool response | MEDIUM | HIGH | HIGH | Tool response validation; MCP threat model (Part 8); FIDES label propagation | LOW | Engineering |
| R-003 | Context discontinuity causing replay failure | MEDIUM | MEDIUM | MEDIUM | DTCM (Part 12.5); context_manifest in receipts; Temporal replay | LOW | Engineering |
| R-004 | Model version change breaking tokenizer accounting | HIGH | MEDIUM | HIGH | tokenizer_version in receipts; regression suite on model change | MEDIUM | Engineering |
| R-005 | Cost overrun via denial-of-wallet loop | MEDIUM | MEDIUM | MEDIUM | AI Gateway budget caps; rate limits; daily billing reconciliation | LOW | Operator |
| R-006 | Unauthorized data exfiltration via MCP | LOW | CRITICAL | HIGH | Network egress controls; tool output validation; audit logging | LOW | Security |
| R-007 | EU AI Act non-compliance at 2026-08-02 | LOW | CRITICAL | HIGH | Receipt retention; operator registry; risk register; audit trail | LOW | Compliance |
| R-008 | CRDT merge conflict corrupting document state | LOW | HIGH | MEDIUM | Automerge/Yjs merge semantics; bytea blob projection; replay from blob | LOW | Engineering |
| R-009 | pgvector recall degradation at scale | LOW | MEDIUM | LOW | HNSW tuning; recall benchmarks; alert on recall@5 < 0.85 | LOW | Engineering |
| R-010 | Operator approval gate bypassed | LOW | CRITICAL | HIGH | Hook enforcement; dual-operator requirement in production | VERY LOW | Security |

### Risk appetite statement

This system accepts MEDIUM residual risk for engineering failure modes and LOW residual risk for compliance and security failure modes. Any control gap that raises residual score to HIGH or CRITICAL requires immediate remediation before production promotion.

---

## Part 20 — Incident Response & Rollback Runbook

*(NIST AI RMF MANAGE-3.2)*

### Incident Classification

| Severity | Definition | Response SLA |
|---|---|---|
| P0 — Critical | Real capital at risk; unauthorized execution; data breach | Immediate (operator paged within 5 min) |
| P1 — High | RED gate bypassed; hallucinated output promoted to staging; cost overrun >200% | 1 hour |
| P2 — Medium | AMBER gate unresolved >24h; receipt gap detected; model version mismatch | 4 hours |
| P3 — Low | Retrieval recall degradation; context anxiety event; minor cost anomaly | Next business day |

### Rollback Runbook

**Step 1: Identify the blast radius**
```bash
# Find all receipts after the incident start time
psql $PGCONN -c "
  SELECT receipt_id, stage_id, timestamp, output_hash
  FROM execution_receipts
  WHERE timestamp > '$INCIDENT_START'
  ORDER BY timestamp ASC;
"
```

**Step 2: Stop the workflow**
```bash
# Trigger kill-switch (Temporal / DBOS)
temporal workflow terminate --workflow-id $WORKFLOW_ID --reason "Incident $INCIDENT_ID"
# OR DBOS
dbos workflow cancel $WORKFLOW_ID
```

**Step 3: Quarantine affected artifacts**
```bash
git tag incident/$INCIDENT_ID/quarantine-start HEAD
# Move affected outputs to quarantine directory
mkdir -p quarantine/$INCIDENT_ID
mv stages/*/output/*.md quarantine/$INCIDENT_ID/
git add -A && git commit -m "quarantine: incident $INCIDENT_ID artifacts"
```

**Step 4: Replay from last known-good receipt**
```bash
# Identify last clean receipt
psql $PGCONN -c "
  SELECT receipt_id, timestamp FROM execution_receipts
  WHERE stage_id = '$STAGE_ID'
    AND timestamp < '$INCIDENT_START'
  ORDER BY timestamp DESC LIMIT 1;
"
# Replay projection from that receipt forward
python scripts/replay_from_receipt.py --from-receipt $CLEAN_RECEIPT_ID
```

**Step 5: Post-incident review**
- Document in `incidents/$INCIDENT_ID.md`: timeline, blast radius, root cause, control gap, corrective action
- Update risk register (Part 19) with adjusted likelihood/impact if warranted
- Update runbook with any new steps discovered during incident

### Kill-switch architecture

The kill-switch MUST be:
- In the **deterministic workflow layer** (not an activity) per ADR-005
- Invocable by any credentialed operator without LLM assistance
- Tested monthly: run a simulated RED gate and verify workflow terminates within 30 seconds

---

## Part 21 — Test Plan

*(IEEE 3407-2025 §5.2)*

### Coverage targets by stage

| Stage | Unit coverage | Integration coverage | E2E coverage | Replay test |
|---|---|---|---|---|
| Schema validation | 100% | 90% | — | — |
| Retrieval pipeline | 90% | 85% | 70% | Required |
| LLM output validation | 95% (schema) | 80% | 60% | Required |
| Stage gate logic | 100% | 95% | 80% | Required |
| Audit receipt emission | 100% | 100% | 100% | Required |
| Rollback runbook | — | — | 100% | Monthly drill |

### Test categories

**1. Schema contract tests**
- Every Pydantic model has a test suite covering: valid inputs, invalid inputs (each field), boundary conditions, and Literal enum exhaustion
- Run on every commit

**2. Retrieval recall tests**
- Benchmark suite: 50 representative queries against the vault
- Assert `recall@5 >= 0.85` for hybrid retrieval
- Assert `recall@5 >= 0.60` for BM25-only fallback
- Run nightly

**3. Stage gate determinism tests**
- For every validator gate: given identical input + context, assert identical GREEN/AMBER/RED decision
- Run on model version change

**4. Replay tests**
- Take a production receipt; replay the workflow from that receipt against the recorded context_manifest
- Assert: same stage gate decision, same output_hash (for deterministic steps), receipt_id chain intact
- Run weekly

**5. Kill-switch test**
- Inject a synthetic RED condition at stage gate
- Assert: workflow terminates, quarantine directory created, incident receipt emitted, operator notification sent
- Run monthly

**6. Cost regression tests**
- Assert per-workflow USD cost within 20% of baseline after model version change
- Alert if cache hit ratio drops below 30%

---

## Part 22 — AI Gateway & Cost Governance

### Why an AI Gateway

Direct LLM API calls from agent code create:
- No per-session or per-stage budget enforcement
- No centralized rate limiting
- No unified audit logging across providers
- No model routing (fallback to a cheaper model when primary is rate-limited)
- No latency/cost observability

An AI Gateway sits between your agent code and the LLM API, providing all of the above.

### Gateway capabilities required

| Capability | Implementation |
|---|---|
| Per-session token budget | Hard limit; reject calls exceeding session budget |
| Per-stage USD budget | Soft limit (alert) + hard limit (block) |
| Rate limiting | Token bucket per model per operator |
| Audit logging | Every call logged with model, tokens, cost, latency, stage_id |
| Model routing | Primary → fallback on 429/500 |
| Cache passthrough | Preserve Anthropic prompt cache headers |
| Geo routing | Route to EU endpoints when `inference_geo=eu` required |

### Recommended implementations

- **Self-hosted:** LiteLLM Proxy (Apache 2.0; supports 100+ providers; Redis-backed rate limiting)
- **Cloud-managed:** Portkey.ai, Braintrust Proxy, Azure AI Gateway
- **Postgres-native:** DBOS can wrap LLM calls as transactional activities with budget enforcement

### Cost governance schema

```python
class CostGovernancePolicy(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    policy_id: str
    stage_id: str
    max_tokens_per_call: int = 100_000
    max_usd_per_session: float = 5.00
    max_usd_per_stage: float = 1.00
    max_usd_per_day: float = 20.00
    alert_threshold_ratio: float = 0.80   # alert at 80% of limit
    hard_stop_on_exceed: bool = True
    fallback_model: str = "claude-haiku-4-5"
    require_operator_above_usd: float = 2.00
```

### RLS and capability governance

**RLS is tenant isolation, not capabilities.** See ADR-004 for the FIDES-based capability substrate. For this part:

- RLS policies enforce: which operator can see which stage receipts; which agent role can call which tools
- Capability delegation (granting an agent access to a specific tool for a specific session) lives in application code backed by signed tokens
- OPA or Cedar for attribute-based policy evaluation when RLS predicates become insufficient

---

## Part 23 — Operational Concerns

### Evals as Code

Evaluations must be version-controlled, reproducible, and tied to specific model versions:

```python
# evals/stage_gate_eval.py
from pydantic import BaseModel
from typing import Literal

class EvalCase(BaseModel):
    case_id: str
    input_context: str
    expected_decision: Literal["GREEN", "AMBER", "RED"]
    model_version: str    # Eval is pinned to a model version
    tokenizer_version: str

# Eval suite is a list[EvalCase] committed to version control
# Run on every model version change; assert pass rate >= 95%
```

**Key discipline:** evals are not tests of the LLM's general capability — they are tests of your specific workflow's stage gate behavior on your specific domain inputs. An eval suite should cover: representative GREEN cases, boundary AMBER cases, clear RED cases, and adversarial injection cases.

### Model Migration Protocol

When migrating from one model version to another (e.g., Claude Opus 4.6 → 4.7):

1. **Tokenizer change audit:** run the full context_manifest for all active workflows through both tokenizers; record the token delta. Opus 4.6 → 4.7 showed up to 35% token increase for the same input.
2. **Budget recalibration:** update `max_tokens_per_call` and `max_usd_per_stage` in `CostGovernancePolicy` to account for the new token counts.
3. **Eval regression:** run the full eval suite on the new model version before promoting any workflow to production.
4. **Receipt version bump:** update `tokenizer_version` in all new `PromptExecutionReceipt` instances. Old receipts remain immutable.
5. **Replay validation:** replay 5 recent production workflows against the new model; assert stage gate decisions are unchanged or document deliberate behavioral changes.

### Secrets Management

- **Never** store API keys, broker credentials, or operator tokens in markdown files, YAML frontmatter, or git-tracked files
- Use: 1Password CLI (`op run --`), HashiCorp Vault, AWS Secrets Manager, or `direnv` + `.envrc` (git-ignored)
- PostToolUse hook scans every Write operation for secret patterns (Part 3 settings.json example)
- Rotate API keys on any suspected exposure; log rotation event in the incident register

### Observability Stack

| Signal | Tool | Retention |
|---|---|---|
| LLM call traces | LiteLLM Proxy → OpenTelemetry → Jaeger/Tempo | 30 days |
| Cost metrics | Prometheus + Grafana dashboard | 90 days |
| Audit receipts | Postgres append-only table (WORM semantics) | 6 years (FINRA) |
| Model performance | MLflow or W&B (eval results per model version) | Indefinite |
| Infrastructure | Standard Postgres monitoring (pg_stat_statements, pgBadger) | 30 days |

### HIPAA Path (if applicable)

If any workflow processes ePHI:
1. Sign a BAA with Anthropic (available for Claude API enterprise tiers)
2. Pin `inference_geo=us` (or `eu` as appropriate for data residency)
3. Enable audit logging at the PHI-field level (not just session level)
4. HIPAA §164.312(b) audit controls: log every read/write access to ePHI fields
5. Review whether prompt content constitutes ePHI; err on the side of inclusion

---

## CHANGELOG.md Reference Block

*(EU AI Act Annex IV §1(f): "a description of the changes made to the AI system and its performance throughout its lifetime")*

This block is maintained in `CHANGELOG.md` at repo root. Current entry:

```markdown
## [9.0.0] — 2026-05-23
### Added
- Part 12: Eg-walker + CodeCRDT collaborative editing substrate
- Part 12.5: DTCM (Distributed Transactional Context Memory)
- Part 13: Context anxiety / compaction / tool-result clearing
- Part 19: AI Risk Register (ISO 42001 §6.1)
- Part 20: Incident Response & Rollback Runbook (NIST RMF MANAGE-3.2)
- Part 21: Test Plan with per-stage coverage targets (IEEE 3407-2025 §5.2)
- Part 22: AI Gateway & Cost Governance
- Part 23: Operational Concerns (evals-as-code, model migration, secrets, observability)
- docs/adr/: ADR-001 through ADR-005

### Changed
- Part 3: MCP syscall analogy formally scoped with threat model
- Part 3: LLM-as-CPU analogy replaced with calibrated stochastic-policy framing
- Part 3: Compiled AI paradigm (arXiv:2604.05150) integrated
- Part 4: Memory hierarchy cost-tier framing; Pichay mechanics specified
- Part 9: rank-bm25 downgraded to pedagogy-only; bm25s recommended
- Part 10: All Pydantic code migrated to v2 (≥2.13.4)
- Part 11: PromptExecutionReceipt extended with cost/model/cache/geo fields

### Fixed
- Regulatory: EU AI Act Article 99 penalty tiers corrected (7%, not 6%)
- Standards: IEEE 26514 → ISO/IEC/IEEE 26514:2022; NIST 800-218A framed as SSDF Community Profile
- Retrieval: All benchmarks now attach (dataset, metric, baseline, top-k, reranker)
- Lost in the Middle: upgraded to Liu et al. TACL 2024 (DOI 10.1162/tacl_a_00638)
```

---

*End of v9 Parts 12–23. For v10 corrections and updates, see `docs/v10-draft.md`.*
