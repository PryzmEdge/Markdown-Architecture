# ADR-004 — FIDES Two-Element Product Lattice as Authority Substrate

| Field | Value |
|---|---|
| ID | ADR-004 |
| Status | Accepted |
| Date | 2026-05-23 |
| Deciders | PryzmEdge |
| Supersedes | — |
| Superseded by | — |

---

## Context

The system requires an information-flow control (IFC) model that governs how data may move between LLM components, tools, and users. Earlier versions of this document used the terms "Six-Band Authority Lattice" and "Double Tesseract Authority Model" without formal definition. The critical architecture review identified these as metaphors rather than formal constructions.

Three IFC models were evaluated:

1. **Ad-hoc label system** — custom labels without formal lattice semantics.
2. **FIDES product lattice** (Costa et al., Microsoft Research, arXiv:2505.23643) — explicit 2×2 product lattice: `confidentiality ∈ {public, private}` × `integrity ∈ {untrusted, trusted}`.
3. **CaMeL capability tags** (Debenedetti et al., Google DeepMind/ETH Zürich, arXiv:2503.18813) — capability tags on variables in a custom Python interpreter.
4. **Full six-class label lattice** (v10-draft.md Part 12) — extends FIDES with an `INTERNAL` intermediate confidentiality tier.

---

## Decision

Adopt the **FIDES two-element product lattice** as the authority substrate for v0.1, with a defined upgrade path to the six-class lattice.

**v0.1 lattice (FIDES-aligned):**

```
confidentiality ∈ {public, private}    (public < private)
integrity       ∈ {untrusted, trusted}  (untrusted < trusted)

Labels (4 elements):
  ⊥ = (public,  untrusted)   -- bottom
      (public,  trusted)
      (private, untrusted)
  ⊤ = (private, trusted)     -- top

Flow rules:
  No-read-up (confidentiality):  subject at L reads D only if D.conf ≤ L.conf
  No-write-down (confidentiality): subject at L writes S only if L.conf ≤ S.conf
  No-read-down (integrity):       high-integrity stages validate before consuming untrusted data
  No-write-up (integrity):        untrusted components propose; trusted validator gates
```

**Upgrade to six-class lattice** (v10-draft.md Part 12) when the two-tier confidentiality model proves insufficient — specifically when the system needs to distinguish `INTERNAL` data (team-visible but not public) from both `PUBLIC` and `RESTRICTED` data.

**CaMeL integration:** capability tags from CaMeL attach to values at specific lattice points. The lattice governs flow; capabilities govern "who may act with this value." Both models are complementary and should be used together at enforcement points.

**Enforcement points (all three must be implemented before production):**
1. Tool call planner: label check before every MCP invocation.
2. Workflow validator gates: run at `(private, trusted)`; accept/reject/declassify.
3. Audit receipts: record input/output labels and any declassification events per `PromptExecutionReceipt`.

**Postgres implementation:** every event row in the event log carries `confidentiality` and `integrity` label columns. Every tool invocation in `PromptExecutionReceipt` records input and output labels.

---

## Consequences

**Positive:**
- FIDES is published, cited, and has reference code (github.com/microsoft/fides).
- The 2×2 lattice is easy to reason about; every engineer on the team can hold it in their head.
- Starting simple reduces implementation risk; upgrade path to six-class is defined.
- Aligns with the broader IFC-for-LLMs research community (FIDES, CaMeL, RTBAS all use similar lattice structures).

**Negative / risks:**
- FIDES is experimental (`agent_framework.security` behind a feature flag in Microsoft Agent Framework as of May 2026). Production stability not guaranteed.
- The 2×2 lattice may be too coarse for some use cases (e.g., distinguishing team-internal data from public data).
- IFC label propagation across every tool call adds engineering overhead.

**Mitigation:** implement labels as nullable columns initially; enforce IFC checks in the workflow layer before enforcing at the storage layer.

---

## Alternatives considered

| Alternative | Reason rejected |
|---|---|
| Ad-hoc label system | No formal semantics; non-composable; not auditable |
| Six-class lattice from day one | Higher complexity; FIDES 2×2 is sufficient for v0.1 |
| BLP (Bell-LaPadula) only | Confidentiality-only; no integrity dimension |
| Biba only | Integrity-only; no confidentiality dimension |
| RLS as capability system | RLS has no unforgeable handles, delegation, or revocation (see ADR-001) |

---

## References

- Costa et al. (2025). *FIDES: Securing AI Agents with Information-Flow Control.* arXiv:2505.23643.
- Debenedetti et al. (2025). *CaMeL: Defeating Prompt Injections by Design.* arXiv:2503.18813.
- Evertz et al. (2025). *RTBAS.* arXiv:2502.08966.
- Denning, D.E. (1976). *A lattice model of secure information flow.* Comm. ACM 19(5):236–243.
- Sandhu, R.S. (1993). *Lattice-based access control models.* IEEE Computer 26(11):9–19.
- Bell, D.E. & LaPadula, L.J. (1973). *Secure computer systems: mathematical foundations.*
- Biba, K.J. (1977). *Integrity considerations for secure computer systems.*
