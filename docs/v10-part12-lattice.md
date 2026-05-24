# Part 12 — Authority Labels and Lattices (Formalized)

*Status: ready to insert into v10-draft.md as Part 12.*

---

## 12.1 Purpose and scope

This system uses **security labels** to describe how data may flow through tools, workflows, and users. Labels drive three things: which tools can see which data, which outputs can be written where, and when human approval is mandatory. The structure underneath is a **finite lattice** in the sense of Denning/Sandhu: a partially ordered set of labels where every pair has a well-defined join (least upper bound) and meet (greatest lower bound).

**Key references:** Denning, *Comm. ACM* 19(5):236–243, 1976; Sandhu, *IEEE Computer*, 1993; FIDES (Costa et al., arXiv:2505.23643); CaMeL (Debenedetti et al., arXiv:2503.18813).

---

## 12.2 The six-class label lattice

For v10 we use six composite labels, each combining a confidentiality dimension and an integrity dimension:

| Label | Confidentiality | Integrity |
|---|---|---|
| `PUBLIC_UNTRUSTED` | PUBLIC | UNTRUSTED |
| `PUBLIC_TRUSTED` | PUBLIC | TRUSTED |
| `INTERNAL_UNTRUSTED` | INTERNAL | UNTRUSTED |
| `INTERNAL_TRUSTED` | INTERNAL | TRUSTED |
| `RESTRICTED_UNTRUSTED` | RESTRICTED | UNTRUSTED |
| `RESTRICTED_TRUSTED` | RESTRICTED | TRUSTED |

The underlying dimensions order as:
- Confidentiality: `PUBLIC < INTERNAL < RESTRICTED`
- Integrity: `UNTRUSTED < TRUSTED`

---

## 12.3 Partial order, join, and meet

**Partial order.** Label `A ≤ B` if and only if:
- `A.confidentiality ≤ B.confidentiality`, and
- `A.integrity ≤ B.integrity`

So for example: `PUBLIC_UNTRUSTED ≤ INTERNAL_TRUSTED` (both dimensions go up), but `PUBLIC_TRUSTED` and `INTERNAL_UNTRUSTED` are **incomparable** (confidentiality goes up, integrity goes down).

**Bottom (⊥):** `PUBLIC_UNTRUSTED` — the least restrictive label. All labels are ≥ ⊥.

**Top (⊤):** `RESTRICTED_TRUSTED` — the most restrictive label. All labels are ≤ ⊤.

**Join** `a ∨ b` (least upper bound):
- `confidentiality = max(a.confidentiality, b.confidentiality)`
- `integrity = max(a.integrity, b.integrity)`

Intuition: reading from both `a` and `b` produces a result at the *more sensitive and more trusted* of the two.

**Meet** `a ∧ b` (greatest lower bound):
- `confidentiality = min(a.confidentiality, b.confidentiality)`
- `integrity = min(a.integrity, b.integrity)`

Intuition: the "overlap" is the *less sensitive and less trusted* of the two.

This is a proper finite lattice: unique join and meet for every pair, unique ⊥ and ⊤.

---

## 12.4 Flow rules and declassification

We follow the standard lattice-based information-flow pattern:

**Confidentiality rules:**
- **No-read-up:** a subject at label `L` may only read data `D` if `D.confidentiality ≤ L.confidentiality`.
- **No-write-down:** a subject at `L` may only write to sink `S` if `L.confidentiality ≤ S.confidentiality`. (Restricted data cannot flow into a less restricted sink.)

**Integrity rules:**
- **No-read-down:** high-integrity workflow stages must not blindly consume lower-integrity data without explicit validation.
- **No-write-up:** low-integrity components cannot directly overwrite high-integrity sinks; they can only *propose* changes gated by a higher-integrity validator.

**Declassification (explicit and typed):**
A dedicated declassifier workflow may lower confidentiality (e.g., `RESTRICTED_* → INTERNAL_*`) only if:
1. It runs at a label ≥ the source label.
2. It emits output constrained by a schema and validator appropriate to the target label.

No other flows may reduce confidentiality. Any attempt is blocked at the validator gate.

---

## 12.5 Relation to FIDES and CaMeL

This six-class lattice is deliberately aligned with FIDES:

- FIDES uses **confidentiality ∈ {public, private}** × **integrity ∈ {untrusted, trusted}** — a 2×2 product lattice with four elements.
- Our six labels extend this by adding an `INTERNAL` intermediate confidentiality tier, preserving the same product-lattice structure and flow rules.
- **Start with FIDES (2×2) for v0.1.** Only extend to six classes when the two-tier confidentiality model proves insufficient for your vault's needs.

CaMeL capability tags attach to **values at particular lattice points**:
- A capability grants the right to *use* a labelled value for a specific set of tool calls.
- The lattice governs information flow; the capability governs "who may act with this value."

FIDE's P-LLM / Q-LLM dual architecture is the reference for schema-typed declassification: the P-LLM (planner, untrusted tier) proposes; the Q-LLM (constrained-decoding, trusted tier) validates output against a typed schema before allowing declassification.

---

## 12.6 Practical enforcement points

Enforcement happens in three places:

**1. Tool call planner (before MCP invocation):**
- Check that the tool's declared label dominates the data label.
- Check that the caller's label is ≥ both data and tool requirements.
- Reject or escalate to operator if checks fail.

**2. Workflow validator gates:**
- Run at `RESTRICTED_TRUSTED` (or operator-specified level).
- Can accept, reject, or route to declassification workflow.
- All rejections are written to the audit log with labels, rule violated, and operator notified.

**3. Audit receipts (PromptExecutionReceipt):**
- Every tool call and workflow step records:
  - Input labels, output labels.
  - Whether any declassification occurred and under which rule.
  - Operator ID if approval was required.
- This makes label flow fully auditable in the immutable event log.

---

## 12.7 Vocabulary corrections (v9 → v10)

| v9 term | v10 replacement | Reason |
|---|---|---|
| "Six-Band Authority Lattice" | "six-class label lattice" | "Band" implies no formal structure; "class" matches Denning's terminology |
| "Double Tesseract Authority Model" | "product lattice of confidentiality × integrity dimensions" | Tesseract is a 4-cube; the structure here is a product lattice, not a geometric object |
| "ring enforcement" | "lattice-based information-flow control" or "validator gate" | "Ring" implies OS protection rings; the mechanism is IFC |
| "validator gates" | keep, but add: "(IFC enforcement point, cf. FIDES §3.2)" | Adds citation anchor |
