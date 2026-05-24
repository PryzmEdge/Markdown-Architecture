# v9 → v10 Red-Pen Edit Plan

*Status: working document. Apply section by section to produce v10-draft.md.*

---

## 0. Frontmatter and Executive Summary

- **Rename kernel framing.**
  - Change all instances of "PostgreSQL-as-kernel" / "system kernel" → **"PostgreSQL as state kernel and provenance ledger."**
  - Wherever the text says "syscall", "kernel panic", "VM", "IPC bus", either delete or replace with the actual PG feature (WAL, LISTEN/NOTIFY, RLS).

- **Novelty paragraph.** Add to Executive Summary:
  > "Individually, these ideas have strong prior art (DBOS, Temporal, Denning/Sandhu lattices, FIDES, CaMeL, Patchwork/GAIOS, Marten). The contribution here is their combination for personal-scale governed AI on a Postgres-backed markdown stack."

---

## Part 1–2 — Mental model and stack diagram

- **Stack labels.** Keep the 5-layer stack, but replace any CPU/OS language with "state kernel + deterministic orchestration around probabilistic cores."
- **Add DBOS acknowledgement.**
  > "DBOS is the closest expression of 'OS on a database'; this paper targets personal-scale PKM rather than general OS replacement."
- **Intended use / out-of-scope.** Add under Out-of-Scope:
  > "High-frequency trading / OMS-grade systems have hard real-time and adversarial constraints we explicitly do not address here."

---

## Part 3 — Deterministic scaffolding around probabilistic cores

- **Name the prior art.** After the "probabilistic policy inside a deterministic harness" quote, add:
  > "This mirrors supervisory control of a stochastic plant (Ramadge–Wonham), Temporal/DBOS durable workflows (deterministic workflows, non-deterministic activities), and IFC-for-LLM work (FIDES, CaMeL, RTBAS)."
- **Explicitly map enforcement vocabulary:**
  - "validator gates" → FIDES/IFC
  - "capability tags" → CaMeL
  - "audit receipts" → Marten/Temporal-style event history

---

## Parts 4–6 — Memory hierarchy, CLAUDE.md, ICM

- These are mostly solid.
- **Context compiler tweak.** Where you talk about "context compiler" or "compiled views", add:
  > "Implementation could be via differential dataflow (Materialize/Feldera/DBSP) or Datalog (pg_mentat/Datalevin) for incremental maintenance."

---

## Parts 8–11 — MCP / Retrieval / Typed orchestration / Audit logging

- **MCP section.** Sharpen the warning:
  > "As of early 2026, security researchers found 1,862 MCP servers exposed without auth; MCP must be treated as pure transport, not security boundary."
- **Typed orchestration.** Add prior-art paragraph naming Meaning-Typed Prompting, DSPy, XGrammar/SGLang as the structured-output substrate.
- **PromptExecutionReceipt.** Explicitly tie to:
  - W3C PROV
  - Marten's event log + inline projections
  - Temporal's Event History

---

## New Part 12 — Authority Lattice (formalized)

- **Drop the metaphors:**
  - "Six-Band Authority Lattice" → "six-class label lattice"
  - "Double Tesseract" → "product lattice of multiple binary dimensions (see Part 12)" or delete
- **Insert Part 12 text.** See `docs/v10-part12-lattice.md` for the full draft.

---

## Trading analogies (scattered sections)

1. **Delete Medallion entirely.** Remove all references to Renaissance / Medallion / "RenTech-like".
2. **Soften OMS language.** "OMS-grade validator" → "OMS-inspired validator gate pattern: probabilistic recommendation, deterministic gate, kill-switch."
3. **Add caveat box once:**
   > "The similarity to trading systems is purely structural (control pattern). We do not claim OMS-level latency, adversarial hardness, or capital-markets regulation coverage."

---

## Obsidian / PKM positioning

- Rewrite "making Obsidian obsolete" as:
  > "Goal: Obsidian-compatible vault (plain markdown) with a Postgres-backed state kernel, governed AI, and event-sourced provenance — not to replace Obsidian's entire plugin ecosystem."
- Add competitors subsection: Obsidian Bases, Anytype, Patchwork/GAIOS, and differentiation (SQL state kernel + IFC).

---

## New short Part: "Scope and Scale"

- **Scope statement:**
  > "This design targets single-user and small-team 'personal-scale' systems. At this scale, PG-RLS, pgvector, recursive queries, and durable workflows behave well; multi-tenant SaaS constraints are explicitly out of scope."
- **Future-work note:** scaling to multi-tenant would require re-evaluating RLS vs schema-per-tenant, pgvector at 10⁸+ vectors, and more.

---

## Appendix / References

Add a clean "Selected prior art" appendix grouped as:

- **IFC and capabilities:** Denning 1976, Sandhu 1993, FIDES (arXiv:2505.23643), CaMeL (arXiv:2503.18813), RTBAS (arXiv:2502.08966), Miller/object-capabilities, Keyhive/GAIOS.
- **Workflow / event sourcing:** Temporal, DBOS, Marten (Jeremy Miller), EventStoreDB.
- **Local-first / CRDT:** Automerge 3.0, Yjs, Patchwork (Ink & Switch), GAIOS, cr-sqlite.
- **PKM / markdown:** Obsidian Bases, Anytype.

---

*Apply all edits above to `docs/v9.md` and save result as `docs/v10-draft.md`.*
