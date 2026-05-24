# Critical Architecture Review: PryzmEdge v6.6 × Markdown/ICM v9 — A Stress-Test of the "PostgreSQL-as-Kernel + Lattice Authority + Probabilistic-Engines-Under-Deterministic-Governance" Thesis

## TL;DR

- **The core thesis is real but the document overclaims novelty.** The substantive ideas — Postgres as a unified state kernel, deterministic governance around probabilistic engines, lattice-based authority, markdown-as-interface, audit receipts — are each well-trodden territory with named prior art (DBOS/Stonebraker; Temporal/LangGraph; Denning 1976 / Sandhu 1993 / FIDES / CaMeL; Ink & Switch's Patchwork/GAIOS; Marten event-sourcing on Postgres). Your specific *synthesis* is genuinely uncommon and worth building, but it is not unprecedented and most of the named primitives ("Six-Band Authority Lattice," "Double Tesseract," "tensor allocation") are metaphors, not formal constructions yet.
- **PostgreSQL can credibly play the role you describe — at *personal-scale* — but the "system kernel" framing collapses under scrutiny.** It is a good *state kernel* (durable, transactional, queryable, WAL-audited). It is a poor *OS kernel* (no preemptive scheduler, no memory protection, no syscall interface, no IPC primitives beyond LISTEN/NOTIFY, single-writer per row). Stonebraker's DBOS is the honest version of the analogy you're reaching for, and even DBOS runs on Linux/Firecracker. The PG feature-mapping table needs to be rewritten as "state-kernel mapping," not "OS-kernel mapping."
- **The highest-leverage rewrites are: (1) make the lattice formal (Denning 1976 + Sandhu 1993 join/meet operators with explicit security labels), (2) adopt Microsoft Research's FIDES IFC model and Google DeepMind's CaMeL capability tags as the governance substrate instead of inventing new vocabulary, (3) use Marten or a similar Postgres-native event-sourcing layer for the WAL/provenance chain, (4) replace recursive-CTE lattice traversal with either Datalog (Datalevin/pg_mentat) or differential dataflow (Materialize/Feldera) for incrementally maintained "context compilation," and (5) drop the Renaissance-Medallion analogy — it is unsupported by any public source and weakens the document.**

---

## Key Findings

### 1. What is real and defensible in the document

- **"Deterministic governance wrapped around probabilistic engines" is a real and useful framing**, but it is the explicit research program of at least four established communities: supervisory control theory (Ramadge–Wonham, 1987 onwards), runtime verification, neurosymbolic AI, and — most directly relevant to you — the 2025 line of work on **information-flow control for LLM agents** (FIDES from Microsoft Research, CaMeL from Google DeepMind/ETH Zürich, RTBAS from CMU). The pattern "non-deterministic planner gated by deterministic enforcer" is the operative architecture of all three. You are not inventing this; you are rediscovering it. That is fine — but the document should cite it.
- **Postgres-as-state-kernel for personal knowledge is a defensible bet.** Per AWS's case study with the Letta team ("How Letta builds production-ready AI agents with Amazon Aurora PostgreSQL"), "Letta creates 42 tables to manage agents, memory, messages, and associated metadata," and the `letta/orm/block_history.py` module (confirmed via DeepWiki) provides an explicit "audit trail of all block modifications." DBOS (Stonebraker, Zaharia, Madden, MIT/Stanford) explicitly builds an OS-on-database pattern. Marten on Postgres demonstrates that document store + event sourcing + projections on PG is production-grade in .NET. So the architectural bet is sound; it just is not new.
- **The "audit receipts / provenance chain" idea is correct and well-motivated** but is the standard CQRS + Event Sourcing pattern, plus the W3C PROV data model. Marten's "inline projection" pattern and DBOS's "all OS state as tables, queryable for forensic SQL" are concrete realizations.
- **Markdown-as-interface over a structured kernel is the right call.** Obsidian's own Bases plugin (introduced 2025) is moving in exactly this direction — YAML frontmatter as machine-readable schema, markdown body as unstructured payload, queries as dynamic views — but Bases is single-vault, table-only, and has no governance or AI primitives. Your design beats Obsidian here on substrate, not on user model.

---

### 2. Where the document overreaches or uses metaphor as proof

#### 2a. "PostgreSQL as system kernel" — the analogy is half-right and half-rhetoric

The honest table is below. Where the analogy holds, it is because PG is a state kernel. Where it breaks, it is because an OS kernel mediates hardware, schedules CPUs, isolates processes, and provides syscalls — none of which Postgres does.

| Claimed mapping | Reality | Verdict |
|---|---|---|
| PG as "kernel" | PG is a user-space process that *itself depends on* an OS kernel for IPC (shared memory + semaphores per official docs), scheduling, memory, and disk I/O. | **Metaphor, not isomorphism.** |
| PG as "scheduler" | PG has a query planner and a per-backend connection model, but no preemptive task scheduler. For workflow scheduling you need Temporal, DBOS, or pg_cron. | **Half-true.** Pair with DBOS or Temporal. |
| PG as "VM" | No isolation between sessions beyond roles and RLS. No fault containment. | **False.** |
| WAL as "syscall trace" | WAL is a redo log, not a syscall log. It records page-level changes, not application-level intents. To get true syscall-trace semantics you must layer event sourcing on top (Marten-style). | **Needs event-sourcing layer.** |
| RLS as "ring enforcement" | RLS is row-level filtering with composable policies. It is **not** a capability system, has no delegation/revocation primitives, and degrades sharply at >10K tenants without composite `(tenant_id, ...)` indexes on every table. Multiple policies AND-compose, each evaluated per row. | **Partial.** Not equivalent to object-capabilities (Miller et al.) or seL4 capabilities. Layer OPA or Permit.io for attribute-based logic. |
| Materialized views as "context snapshots" | PG's native MVs are *non-incremental* — they fully refresh on `REFRESH MATERIALIZED VIEW`. For true incremental "context compilation" you want Materialize / Feldera / pg_ivm (the latter is "semi-working" per the IVM community), or Jane Street's Incremental library. | **Wrong tool.** See §3. |
| Recursive CTEs as "lattice traversal" | Recursive CTEs scale poorly past a few thousand nodes and do not memoize across queries. Per the Datalevin GitHub benchmark (math-bench Q4), "Datomic took 40 seconds to finish, whereas Datalevin took less than 40 milliseconds (more than 1000X faster), and Datascript ran out of memory" on recursive academic-ancestry traversal. | **Wrong tool for lattice queries.** |
| pgvector as "AI memory graph" | pgvector + pgvectorscale is production-ready up to hundreds of millions of vectors with reasonable concurrency. Beyond that, or at high QPS with multi-tenant isolation, dedicated vector DBs (Qdrant, Pinecone, Weaviate) win. For a personal knowledge system, pgvector is exactly right. For a multi-tenant SaaS at scale, it is the wrong choice. | **Right for your scope, wrong if you scale beyond personal/team.** |

The honest reframe: Postgres is your **deterministic state kernel and provenance ledger**, not your operating system. Drop "syscall," "kernel panic," "VM," "IPC bus" from the mapping unless you can name the concrete PG mechanism that delivers each semantic.

---

#### 2b. The "Six-Band Authority Lattice" and "Double Tesseract Authority Model" are not lattices (yet)

A lattice in Birkhoff's sense (Birkhoff, *Lattice Theory*, AMS Colloquium Publications XXV, 3rd ed., 1967) is a partially ordered set in which every pair of elements has a unique least upper bound (join, ∨) and greatest lower bound (meet, ∧). Denning's 1976 paper (*Comm. ACM* 19(5):236–243) operationalizes this for security as a tuple `(SC, →, ⊕)` of security classes, a flow relation `→`, and a class-combining operator `⊕`. Sandhu's 1993 *IEEE Computer* paper "Lattice-Based Access Control Models" generalizes it across BLP, Biba, Chinese Wall, etc.

To make your "Six-Band" and "Double Tesseract" formal, you need to specify:

1. **The set of labels** (the six bands as elements of `SC`).
2. **The partial order** `≤` between bands (which band dominates which, with explicit reflexivity, antisymmetry, transitivity).
3. **The join operator** `∨` (when an operation reads from band A and band B, what is the band of the result?) and the **meet** `∧`.
4. **The bottom (⊥) and top (⊤) elements.** Every finite lattice has them.
5. **A no-read-up / no-write-down rule** (BLP-style confidentiality) or **no-read-down / no-write-up** (Biba-style integrity), or both as a product lattice (FIDES does exactly this — a two-element confidentiality lattice crossed with a two-element integrity lattice).
6. **A declassification rule** — under what conditions can a value move down the lattice? Without this, your system locks up.

Until you can write those down, "Six-Band Authority Lattice" is a metaphor. The fix is mechanical: define the bands as a poset, check the join/meet axioms, and you have a real lattice. The "Double Tesseract" is harder to defend — a tesseract is a 4-cube with 16 vertices; if you mean a product of four binary lattices, just say "product lattice of four bits." If you mean something richer, write the axioms.

The 2025 Microsoft Research **FIDES** paper ("Securing AI Agents with Information-Flow Control," arXiv:2505.23643, Costa et al.) is the model to copy: explicit two-element confidentiality lattice × two-element integrity lattice, label propagation through tool calls, schema-typed declassification via a constrained-decoding Q-LLM. Google DeepMind/ETH Zürich's **CaMeL** ("Defeating Prompt Injections by Design," arXiv:2503.18813, Debenedetti et al.) attaches capability tags to every variable in a custom Python interpreter and enforces policies on tool invocations. CMU's **RTBAS** (arXiv:2502.08966) does the same with an attention-based "dependency screener" to manage label creep. Use these as the formal substrate. The vocabulary already exists.

---

#### 2c. The "isomorphism" between trading and AI orchestration is structural, not deep

The shared structure is real: both domains have (a) a probabilistic generator (alpha signal / LLM), (b) a deterministic governor (OMS validator gates / MCP+IFC), (c) a state-of-record (PostgreSQL authority / context store), (d) a kill-switch (trading halt / agent abort), and (e) a capacity/budget governor (position limits / token+tool budget). This pattern is recognizable as **supervisory control of a stochastic plant** (Ramadge–Wonham 1987) or, in the AI-safety vocabulary, **runtime verification of a learned controller**. It is also the pattern in modern durable-workflow engines: Temporal's deterministic workflow + non-deterministic activities, LangGraph's checkpointer + tool nodes, DBOS's transactional workflow + agent calls.

Where the isomorphism *fails*:

- **Trading has hard real-time constraints** (microseconds matter; FPGAs at Jane Street; co-location). Personal-knowledge AI does not. Your latency budget is 3–4 orders of magnitude larger. The architectures that win in HFT (kernel-bypass networking, lock-free ring buffers, OCaml/C++ on co-located hardware) are wildly over-engineered for PKM and would make your system unbuildable.
- **Trading is adversarial, with externally observable outcomes** (P&L). An OMS must reject orders in microseconds and recover from partial fills atomically. Your AI workflow has no equivalent atomicity requirement; "the user can re-run the prompt" is acceptable failure semantics. Equating "validator gate" with "OMS" inflates the engineering burden.
- **Trading's "sleeves" and "capacity governance" are about risk allocation across uncorrelated alpha sources** — fundamentally a portfolio-theory concept (Markowitz, Kelly criterion). AI "context compilation" has no analogue of correlation between context fragments, no analogue of variance, no portfolio optimization problem. Re-using the trading vocabulary here is metaphor inflation.

The isomorphism is at the level of *control patterns*, not *operational semantics*. Keep the pattern; drop the trading-specific language for the PKM build.

---

#### 2d. The Renaissance/Medallion analogy is the weakest claim in the document and should be removed

There is **no published architecture paper** for Renaissance Technologies' Medallion fund. The only on-record technical discussion is CEO Peter Brown's September 2023 Goldman Sachs *Exchanges* podcast appearance, in which he describes the firm's *philosophy* (scientists, collaboration, infrastructure investment, single-pot compensation, employee retention) but discloses **zero** technical specifics — no database choices, no languages, no scheduling architecture. Gregory Zuckerman's 2019 book *The Man Who Solved the Market* describes 1990s-era Sun workstations and custom Linux clusters, but says nothing about the current stack.

Public knowledge of Medallion's edge is, by consensus of Cornell (2020, "Medallion Fund: The Ultimate Counterexample?") and other observers, attributable to: (a) ~50.75% win rate on millions of small trades, (b) extreme leverage (10×–20×), (c) market-neutral pairs, (d) employee-only capital base capped near $10B, (e) cultural retention. None of these is an *architectural* property; they are *strategic* and *organizational* properties. Claiming "Medallion-like tensor allocation" or comparing your design to Medallion's infrastructure has no factual basis you can cite, and any reviewer with finance background will mark it down. Remove the comparison; keep the philosophical lesson ("small edge × massive throughput × ruthless validation") if you want.

---

#### 2e. "Very few people are thinking at this layer" — substantially false

The layer you describe — durable governed orchestration of probabilistic AI on a unified state kernel with audit and capability flow control — is one of the most actively populated research and product areas of 2025–2026. A non-exhaustive map:

- **Durable AI workflow engines:** Temporal (per Temporal's own blog, "As of March 23rd, 2026, the integration between the OpenAI Agents SDK and Temporal's Python SDK is now Generally Available"), LangGraph (1.0 + Postgres checkpointer), DBOS (Stonebraker/Zaharia, Postgres-native), Restate, Inngest, Trigger.dev, Dagster, Prefect.
- **Governed inference / IFC for LLMs:** FIDES (Microsoft Research, now shipped in Microsoft Agent Framework as an experimental feature behind `agent_framework.security`), CaMeL (Google DeepMind), RTBAS (CMU), Spotlighting + Prompt Shields (Azure AI Foundry), f-secure (UCSB), NeuroTaint (2026). This is a *fast-moving* sub-field, not an empty niche.
- **Agent memory with audit:** Letta (Postgres + 42-table schema, `block_history` audit), Zep/Graphiti (bitemporal knowledge graph with four timestamps per fact, arXiv:2501.13956), Mem0 (four-scope provenance), Cognee (vector+graph+relational), LangMem.
- **Local-first + governance + AI:** Ink & Switch's **Patchwork** (Automerge CRDT + markdown + branching for AI collaboration, Litt/van Hardenberg) and **GAIOS** (UK ARIA Safeguarded AI Programme, with Keyhive capability-based access control + ZK proofs). This is the project closest to your synthesis, and it is funded.
- **Postgres-as-AI-substrate:** ParadeDB (BM25 + analytics in PG, YC S23), Supabase AI, Neon (serverless PG with branching), pgvectorscale (Timescale), pg_mentat (Datomic-style Datalog inside PG).
- **Deterministic simulation/replay testing:** TigerBeetle (VOPR), Antithesis (hypervisor-level DST, ex-FoundationDB team), FoundationDB itself, WarpStream, Polar Signals.

You are not alone at this layer. You are crowded.

---

#### 2f. The novelty claim that survives: the *specific synthesis* of all five legs

What the prior-art survey does **not** find is a single shipping project that combines:

1. PostgreSQL as the unified state kernel and provenance ledger;
2. LLM as governed coprocessor with IFC-style label propagation;
3. Markdown as the canonical human interface;
4. CRDT-based local-first collaboration;
5. Lattice-formal authority + capability-based access control + audit receipts.

DBOS hits (1) and (2) and partial (5), but lacks (3) and (4). Ink & Switch's GAIOS hits (2), (3), (4), (5), but **explicitly rejects** Postgres in favor of Automerge persistence. Letta hits (1) and (2) but not (3), (4), (5). Anytype hits (3), (4), (5) but uses any-sync, not Postgres. ParadeDB and Supabase hit (1) only.

So: the *combination* is a genuine architectural gap. Whether it is a gap worth filling, or a gap that exists because the constraints are mutually hostile (CRDTs over Postgres rows is a known-hard problem; cr-sqlite is the closest published attempt), is the real question. The honest critic would say: **the gap is real but might be a tar pit, and Ink & Switch chose Automerge over Postgres for good reason.**

---

### 3. State-of-the-art positioning

#### 3a. Orchestration engines (what to learn from them, what they get right)

- **Temporal**: durable execution as a separate concern from agent logic. Workflow code must be deterministic; non-determinism (clocks, RNG, network) is fenced into Activities. Event History is the canonical replay log. Your "WAL provenance chain" should mirror this — *events are the source of truth, projections are the derived state*. Adopt the Temporal discipline even if you don't adopt Temporal.
- **LangGraph + Postgres checkpointer**: state-as-graph with explicit node boundaries. Checkpointers protect application-level failures; Temporal-style replay protects infrastructure-level failures. Production deployments often need both. Your "validator gates" map cleanly to LangGraph's `should_continue` edges, but you should be explicit that LangGraph checkpointers do not save state *inside* a node.
- **DBOS**: the closest direct competitor to your "PG kernel" framing. *"All operating system state should be represented uniformly as database tables."* DBOS provides durable workflow + native Postgres state + Pydantic AI / OpenAI Agents SDK integrations. If you are not building on DBOS, you owe the reader a paragraph explaining why not. (Plausible answers: you want local-first; you want CRDT collaboration; you want markdown UX. DBOS does none of these.)
- **What they get right that the document doesn't yet emphasize:** the separation between *replayable workflow logic* (must be deterministic) and *side-effecting activities* (wrapped, retried, idempotent). Your "kill-switches" and "validator gates" need to live in the deterministic layer; your LLM calls and tool invocations need to live in the activity layer.

#### 3b. AI control planes and governance primitives

- **MCP (Model Context Protocol)** — donated to the Linux Foundation's Agentic AI Foundation in December 2025; spec version 2025-11-25. **What it offers:** standardized tool discovery, OAuth (added March 2025 as opt-in, not required), URL-based client registration, asynchronous operations, server identity, official registry. **What it lacks:** lattice IFC primitives, formal capability semantics, sandbox enforcement. Per Knostic security researchers (reported by CSO Online), "Their methodical internet-wide reconnaissance unearthed 1,862 MCP servers nakedly exposed to public access. When they manually verified a sample of 119 instances… every single server permitted unauthenticated access." MCP is a transport spec, not a governance system. Your "MCP controls" need to wrap MCP with FIDES-style label propagation; MCP alone does not give you that.
- **CaMeL / FIDES / RTBAS** — these are the references your document should cite for "validator gates" and "capability tags." All three operationalize lattice IFC for LLM agents in 2025. FIDES is shipped in Microsoft Agent Framework as `agent_framework.security` (experimental).
- **DSPy, Outlines, SGLang, XGrammar, llguidance** — these are how "deterministic execution" actually happens at the LLM boundary. Per the XGrammar project (integrated into SGLang Nov 2024, vLLM Dec 2024, TensorRT-LLM Jan 2025) and the ChatForest 2026 review, "XGrammar enforces JSON schema, regex, or EBNF grammar constraints on generation with under 40 microseconds of overhead per token." SGLang's compressed FSM decoder is the canonical reference for "compiled AI execution." If your design issues structured outputs from LLMs, name the constrained-decoding stack.
- **DSPy** is the closest analogue to your "context compiler" — programs of prompts that *compile* to optimized prompts/few-shot demonstrations against a metric. If your "compiled AI execution" means anything beyond runtime templating, DSPy is the published prior art.

#### 3c. Personal-knowledge-management competitors

- **Obsidian (2025–2026 state):** Plain-markdown vault on local filesystem. Bases (1.9, 2025) brings YAML-frontmatter-as-DB with table/list/card views, Bases API (1.10) lets plugins add views. Limitations confirmed by community: tables only at launch, no inline-property support, no images-in-cells, Sync is E2EE but not CRDT, plugin sandboxing is weak (plugins run with full Node access), no native multi-user collab, no governance, no provenance, AI integrations are plugin-tier. **Structural weaknesses:** filesystem is the primary index, so queries are O(vault size); no transactionality; no audit; no fine-grained permissions; no schema enforcement beyond YAML linting.
- **Anytype:** any-sync protocol with CRDTs, end-to-end encryption, IPFS file storage, ACL via consensus node, object/type model. Strong on (3),(4),(5); weak on (1) and (2). Not Postgres; not SQL-queryable in the way your design wants.
- **Logseq:** outline-first, plain-text, Datascript-backed graph queries in-memory, weak on governance and AI.
- **Tana / Reflect / Capacities / Heptabase / Mem:** closed-source; published architecture details thin; none claim Postgres backend or lattice governance.
- **Notion / AppFlowy / Affine:** block-based; AppFlowy and Affine are open-source; none use Postgres-as-kernel.

**Where your design would actually beat them:** for a *power user* who wants (a) machine-readable structure (YAML/JSON in markdown), (b) governed AI co-author with audit, (c) deterministic replay of any "compilation" of context, (d) local-first sync with conflict-free merge — the combined offer is novel. Obsidian Bases is moving in your direction but is single-vault and table-only. Anytype has the CRDT and governance legs but not the SQL/AI-orchestration leg. The honest pitch is "Obsidian + DBOS + Patchwork in one shell," not "make Obsidian obsolete." Obsidian's plugin ecosystem (Templater, Dataview, Excalidraw, Canvas) is a massive moat and will not be displaced by architectural elegance alone.

#### 3d. Local-first / CRDT systems

- **Automerge 3.0** (Ink & Switch, July 2025) — per automerge.org/blog/automerge-3/, "we've cut that down memory usage by over 10x, sometimes dramatically more"; pasting Moby Dick into an Automerge 2 document consumes 700 MB of memory while in Automerge 3 it consumes 1.3 MB.
- **Yjs** — production-proven (Notion, Linear, Figma-tier collab tools); generally faster and lighter than Automerge for plain text.
- **Jazz / Liveblocks** — productized CRDT layers with sync servers.
- **cr-sqlite** — turns ordinary SQLite tables into CRDTs. The closest "CRDT-over-SQL" published primitive.
- **Loro, Y-CRDT (Rust port), Diamond Types** — newer high-performance options.

**Honest assessment of your CRDT claim:** running CRDTs *over Postgres rows* (as opposed to over JSON documents stored in PG) is an unsolved problem. The straightforward path is: store CRDT documents (Automerge/Yjs binary blobs) in PG `bytea` columns, run sync at the application layer, project CRDT state into queryable PG tables for SQL access. This is what cr-sqlite does for SQLite; no published Postgres equivalent exists. Be honest in the document that "CRDT collaboration" in this architecture means *CRDTs stored in PG*, not *PG rows that are themselves CRDTs*.

#### 3e. Event sourcing / CQRS

- **Marten on Postgres** (Jeremy Miller, .NET): production-grade event sourcing on PG, with inline and async projections, partitioning of hot/cold streams via `UseArchivedStreamPartitioning`, `EventAppendMode.Quick`, and CQRS handlers via Wolverine. **This is the most mature implementation of your "WAL/event sourcing provenance chain" on Postgres.** If you are building on .NET, use Marten. If not, port the patterns.
- **EventStoreDB / Kurrent, Axon** — language-specific alternatives.
- **Temporal's Event History** — the reference for "replay rebuilds state, side effects are fenced."

Your "audit receipts" should be Marten-style: immutable event log + queryable projections + inline projections for invariants. Do not invent new vocabulary.

#### 3f. Capability-based security vs RLS

Mark Miller's object-capability model (KeyKOS, EROS, seL4, Capsicum) gives you: unforgeable references, transferability under explicit delegation, revocation, confinement (no ambient authority). Postgres RLS gives you: per-row predicate evaluation. These are *not* equivalent.

For "ring enforcement" to be a real capability system you would need:

- Unforgeable handles (UUIDs alone are not enough — they leak via logs).
- Explicit delegation primitives (you grant a capability to another principal *by passing the handle*, not by editing a role).
- Revocation via membrane / proxy pattern (Miller).
- Confinement: a principal cannot accumulate authority beyond what it received.

**Ink & Switch's Keyhive** (in GAIOS, 2025–2026) is the published local-first capability system; the GAIOS team explicitly says "make capability management feel familiar — more like adding a collaborator in Google Docs, less like managing cryptographic keys." If you want a real capability layer, Keyhive is the reference. RLS is for tenant isolation and coarse-grained row filtering, nothing more.

#### 3g. Deterministic simulation and replay

If you want the determinism you claim, the model is **TigerBeetle's VOPR / FoundationDB's simulation testing / Antithesis** (the latter founded by ex-FoundationDB engineers, hypervisor-level DST). The core discipline:

1. **Inject all sources of non-determinism** (clock, RNG, network, disk I/O, thread scheduling).
2. **Run the system on a single OS thread with a deterministic scheduler** (FoundationDB's Flow, TigerBeetle's actor system).
3. **Reproduce any bug from a seed + git SHA.**

This is incompatible with Postgres-as-state-kernel as currently designed, because Postgres backend processes are preemptively scheduled by Linux and use real-time clocks. If you want VOPR-grade determinism, you either (a) accept that determinism applies only to the *workflow layer above PG* (the Temporal model — workflow code deterministic, activities not), or (b) you build a simulator that replays a recorded event log against a known PG state, which is the Marten "rebuild projection" pattern. **Be explicit about which kind of determinism you mean.** "Deterministic governance" is achievable; "deterministic Postgres" is not without an outer simulation harness.

#### 3h. Knowledge graphs and the right query substrate

- **Recursive CTEs**: ok for shallow recursion; degrade badly past ~10⁴ nodes; no memoization across queries.
- **Datalog (Datalevin, Datomic, Soufflé, pg_mentat, XTDB)**: native recursive-rule semantics; Datalevin's own math-bench reports the recursive academic-ancestry query Q4 at 2.9 ms where "Datomic took 40 seconds to finish… and Datascript ran out of memory." **For lattice traversal queries, Datalog is the right substrate.** pg_mentat embeds Datomic-compatible Datalog inside PostgreSQL — directly relevant to your design.
- **Property graphs (Neo4j, Memgraph)** or **RDF/SPARQL (Apache Jena, GraphDB)**: more expressive than CTEs but a separate operational footprint. For a personal-scale system, embedding Datalog in PG via pg_mentat or Datalevin is the right move.
- **Differential dataflow / Materialize / Feldera**: the right tool for incrementally maintained materialized views (your "context snapshots"). Materialize transforms SQL into differential dataflows that update with work proportional to the input delta, not the full dataset. For "context compilation that stays fresh as the vault changes," this is the literature.

---

### 4. What is genuinely novel in your design — and what is renamed

| Concept | Your name | Established name | Verdict |
|---|---|---|---|
| Probabilistic generator + deterministic gate | "Deterministic governance wrapped around probabilistic engines" | Supervisory control (Ramadge–Wonham); IFC for LLM agents (FIDES, CaMeL, RTBAS); neurosymbolic verification | **Renamed.** |
| Lattice of authority labels | "Six-Band Authority Lattice" | Denning lattice model; Sandhu LBAC; product lattice (BLP × Biba) | **Renamed (and not yet formal).** |
| Capability flow through tools | "Ring enforcement" / "validator gates" | Object-capability model (Miller); CaMeL capability tags | **Renamed.** |
| Append-only event log + projections | "WAL provenance chain" / "audit receipts" | Event Sourcing + CQRS (Greg Young); Marten; Temporal Event History; W3C PROV | **Renamed.** |
| Replayable deterministic workflows around non-deterministic activities | "Deterministic execution governance" | Temporal / DBOS / LangGraph durable execution | **Renamed.** |
| Incrementally maintained context views | "Context compiler" | Differential dataflow / Materialize / DBSP / DSPy compilation | **Renamed.** |
| Capability-based local-first ACL with CRDT | "DTCM reconstruction" | Keyhive (Ink & Switch); any-sync (Anytype) | **Renamed.** |
| Markdown frontmatter as structured kernel index | (your design) | Obsidian Bases; YAML-as-schema discipline | **Renamed (Bases got there first in 2025).** |
| The specific 5-leg synthesis | (your design) | **No known prior project** | **Genuinely novel as a combination.** |

The honest read: nearly every individual primitive in your design has an established name and a body of literature. The combination is your contribution. Lean into that.

---

### 5. The engineering-cost honest critique

The blueprint-to-reality gap is large. An honest critic would point out:

- **CRDTs over Postgres is unsolved at the row level.** You will end up storing Automerge/Yjs blobs in `bytea` columns and projecting them into queryable tables — duplicating state and creating consistency seams.
- **IFC label propagation across every tool call and LLM call is heavy.** FIDES achieves it via a P-LLM/Q-LLM dual-model architecture; that doubles inference cost. CaMeL achieves it via a custom Python interpreter that the LLM emits programs into; that requires you to constrain code generation to that interpreter's subset. Both impose real ergonomic cost.
- **Datalog-in-Postgres (pg_mentat, etc.) is a small ecosystem.** You will own debugging it.
- **Deterministic simulation testing requires the whole codebase to be designed for it from day one.** TigerBeetle and FoundationDB succeeded because they built single-threaded actor systems from scratch. Retrofitting determinism onto an existing Postgres-based application is hard.
- **The Obsidian plugin ecosystem is a moat.** Templater + Dataview + Excalidraw + Canvas + Bases is ~10 person-years of community work. Any "make Obsidian obsolete" plan needs an answer for "how do I support these workflows."
- **The "personal" framing is the right one.** All of this is buildable for a single-user-with-occasional-collaboration vault. None of it scales to a multi-tenant SaaS without re-architecture (RLS at 10K+ tenants, pgvector beyond ~10⁸ vectors, single-writer Postgres backpressure).

Realistic build estimate for a credible v0.1 (Postgres + Marten-style event sourcing + Letta-style memory + Automerge-in-bytea + FIDES-style label propagation + Obsidian-style markdown UX + basic Datalog views via pg_mentat or recursive CTEs): **6–12 months of focused work for one strong engineer**, assuming you adopt DBOS or Temporal rather than rebuild the durable-workflow layer. For a v1.0 that meaningfully beats Obsidian+plugins for your own daily use: **18–24 months**. The "make Obsidian obsolete for the world" version is a multi-year, multi-person project and the existence of Ink & Switch's GAIOS and Patchwork suggests the right move is to *contribute to* or *fork from* that ecosystem rather than build from scratch.

---

## Details — Specific Recommendations Ranked by Leverage

### Tier 1 — Adopt these names and references; rewrite the document around them

1. **Cite Denning 1976, Sandhu 1993, and Birkhoff 1967** and write the lattice down formally. Six bands → poset; define `≤`, `∨`, `∧`, `⊥`, `⊤`. If you cannot, drop the word "lattice" and use "ordered classification."
2. **Adopt FIDES (Costa et al., arXiv:2505.23643) as the IFC reference.** Two-element confidentiality × two-element integrity product lattice. Label propagation through tool calls. Schema-typed declassification via constrained-decoding Q-LLM. This is your "validator gates," already published, with code at github.com/microsoft/fides.
3. **Adopt CaMeL (Debenedetti et al., arXiv:2503.18813) as the capability-tag reference.** Capabilities as variable-level tags with reader-set and provenance. Custom interpreter for deterministic enforcement.
4. **Adopt Marten (Jeremy Miller) as the event-sourcing reference for Postgres** even if you are not on .NET. Inline projection for invariants, async projection for read models, `UseArchivedStreamPartitioning` for hot/cold, optimistic concurrency for conflicts.
5. **Adopt Temporal's discipline** (deterministic workflows + fenced activities) even if you don't use Temporal. State the rule explicitly: "Workflow code is replayable. LLM calls and tool calls are activities."
6. **Drop the Renaissance/Medallion comparison entirely.** It has no public-source backing.
7. **Reframe "PG as kernel" as "PG as state kernel and provenance ledger."** Drop the "syscall," "kernel-panic," "VM," "IPC bus" mappings or replace them with named PG features (LISTEN/NOTIFY for IPC-like events; WAL for durable log; RLS for coarse access control; `pg_cron` or DBOS for scheduling).

### Tier 2 — Architectural rewrites

1. **Replace recursive CTEs with Datalog** (pg_mentat for in-PG, or Datalevin as a standalone) for lattice traversal and any transitive-closure query.
2. **Replace native materialized views with either pg_ivm, Materialize, or Feldera** for "context snapshots" if you want them to stay fresh incrementally. Otherwise call them "compiled views" and refresh them explicitly.
3. **Store CRDT documents (Automerge 3 or Yjs) as `bytea` blobs in PG**, with a projection layer that materializes their content into queryable tables. Do not attempt row-level CRDTs.
4. **Pair RLS with an attribute-based policy engine (OPA, Cedar, Permit.io)** for anything beyond tenant isolation. Capability-style delegation belongs in application logic backed by an unforgeable handle (signed token) — not in RLS.
5. **Pin the LLM boundary with constrained decoding (XGrammar / Outlines / SGLang).** Any structured-output path through the system should be grammar-constrained. This is the only way to make "compiled AI execution" mean something concrete.
6. **Adopt the Temporal/DBOS split for durable workflows.** Your validator gates, kill-switches, capacity governors live in the deterministic workflow layer. Your LLM and tool calls live in the activity layer (idempotent, retried, logged).

---

*Document status: deep research input — not yet incorporated into v9.0.0. Intended for integration into v10 rewrite.*
