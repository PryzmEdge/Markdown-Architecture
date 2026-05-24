# v10 Tier 2 Architectural Rewrite Blocks

*Status: ready-to-paste text for each Tier 2 change. Drop each block into the relevant section of v10-draft.md.*

---

## 2.1 Replace recursive CTEs with Datalog (lattice traversal)

*Drop into the lattice/authority section.*

> **Query substrate choice.** For all lattice-shaped queries (authority propagation, label reachability, "who can see what"), this design treats **Datalog** as the preferred substrate and recursive CTEs as an acceptable but inferior fallback. Recursive CTEs in PostgreSQL work well at small depths, but they do not memoize across queries and degrade sharply beyond a few thousand nodes. In contrast, Datalog engines are explicitly designed for recursive rules and incremental maintenance.
>
> **Implementation options:**
> - **In-Postgres:** `pg_mentat` embeds a Datomic-style Datalog inside PostgreSQL, keeping lattice rules and facts in the same state kernel.
> - **Sidecar:** a separate Datalog engine (e.g., Datalevin) treats Postgres as storage and maintains lattice-derived facts in its own index.
>
> **Design rule:** Any query that walks the authority lattice or other transitive-closure graphs **SHOULD** be implemented as a Datalog rule set, with recursive CTEs reserved for prototypes or shallow hierarchies.

---

## 2.2 Replace native MVs with incremental "context snapshots"

*Drop into the context compiler / memory-hierarchy section.*

> **Incremental context snapshots.** PostgreSQL's native materialized views fully recompute on `REFRESH MATERIALIZED VIEW`, which is acceptable for small vaults but does not scale as a general "context compiler." For incrementally maintained "context snapshots" the intended substrate is:
> - **Incremental view maintenance:** `pg_ivm` when staying pure-Postgres.
> - **Differential dataflow:** external engines like Materialize or Feldera, which compile SQL into dataflows that update in time proportional to the input delta rather than the full dataset.
>
> **Design rule:** when this paper says "compiled context view" it means **"incrementally maintained view over the Postgres state kernel"**, implemented via pg_ivm or a differential-dataflow engine, not a naive full refresh.

---

## 2.3 Store CRDT docs as blobs in Postgres (not row-CRDT)

*Drop into the collaboration/CRDT section.*

> **CRDT over Postgres: honest substrate choice.** This design does **not** attempt to make individual Postgres rows behave as CRDTs. Instead, it treats CRDT documents (Automerge, Yjs, etc.) as opaque binary values stored in Postgres and projects them into queryable tables.
>
> Concretely:
> - Each collaborative document is an Automerge/Yjs document stored as a `bytea` column (plus metadata).
> - A projection process (triggered or scheduled) reads CRDT state and materializes it into normalized Postgres tables for search and analytics.
>
> This mirrors the pattern of `cr-sqlite` for SQLite: the CRDT logic lives at the application layer, and the relational engine is the durable backing store and indexing surface. "CRDT collaboration" in this architecture therefore means **"CRDTs stored in Postgres, projected into relational views,"** not "Postgres rows that are themselves CRDTs."

---

## 2.4 Pair RLS with an attribute-based policy engine

*Drop into the security/governance / RLS section.*

> **RLS is tenant isolation, not capabilities.** PostgreSQL Row-Level Security is used here for coarse-grained tenant isolation and row filtering, but it is **not** treated as a full capability system. RLS predicates do not give you unforgeable capabilities, explicit delegation, or revocation semantics.
>
> **Capability and attribute policy layer.** Fine-grained authority and delegation live in an application-level policy engine:
> - Capabilities are represented as signed handles (tokens) that can be passed and revoked.
> - Attribute-based rules are expressed in a dedicated engine (e.g., OPA, Cedar, or an equivalent library), evaluated alongside lattice labels.
>
> **Design rule:** RLS protects table slices (tenants, coarse cohorts). Capability-style delegation and lattice-based information-flow constraints live in the application and policy layer, not inside RLS policies.

---

## 2.5 Pin the LLM boundary with constrained decoding

*Drop into the typed orchestration / compiled-AI section.*

> **Constrained decoding as the LLM boundary.** Wherever this system expects structured output from an LLM (JSON, enums, grammars), it assumes a constrained-decoding layer at the boundary, rather than relying on free-form text plus regexes.
>
> Recommended implementations:
> - **Grammar-based decoding:** XGrammar or equivalent, as integrated in modern inference stacks (SGLang, vLLM, TensorRT-LLM), to enforce JSON Schema, regex, or EBNF constraints during generation.
> - **Library-mediated schemas:** libraries like Outlines, `llguidance`, or DSPy that expose the same idea as "schema-constrained generation."
>
> **Design rule:** "Compiled AI execution" in this paper always implies **grammar-constrained decoding at the LLM boundary**, so that the deterministic harness can treat model outputs as typed data, not untrusted free text.

---

## 2.6 Adopt the Temporal/DBOS split for durable workflows

*Drop into the orchestration / governance section.*

> **Workflow determinism vs activities.** This architecture adopts the Temporal/DBOS discipline for durable workflows:
>
> - **Workflow layer (deterministic):** pure functions over state that must be replayable from the event log. All "validator gates," kill-switch logic, capacity checks, and lattice policy decisions live here.
> - **Activity layer (non-deterministic):** side-effecting operations such as LLM calls, MCP tool invocations, network I/O. Activities are wrapped for idempotence, retried by policy, and logged.
>
> **Design rule:** *Workflows decide; activities act.* Any logic that cannot be replayed deterministically from events belongs in an activity. Any safety-critical guardrail (validator gate, budget check, kill-switch) belongs in deterministic workflow code.
