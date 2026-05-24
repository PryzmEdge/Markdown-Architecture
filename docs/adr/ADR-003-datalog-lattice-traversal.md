# ADR-003 — Datalog (pg_mentat) for Lattice Traversal over Recursive CTEs

| Field | Value |
|---|---|
| ID | ADR-003 |
| Status | Accepted |
| Date | 2026-05-23 |
| Deciders | PryzmEdge |
| Supersedes | — |
| Superseded by | — |

---

## Context

The authority lattice (Part 12 of v10-draft.md) requires queries that traverse transitive-closure relationships: "which labels dominate label X?", "what is the join of labels A and B?", "which principals have read access to document D given label propagation rules?"

Two query substrates were evaluated:

1. **Recursive CTEs in PostgreSQL** — standard SQL feature, no additional dependency.
2. **Datalog** — logic-programming query language natively suited to recursive rules and transitive closure.

Recursive CTEs in Postgres work correctly but have known limitations: they do not memoize results across queries, they fully re-execute on each call, and community benchmarks show they degrade sharply beyond ~10⁴ nodes. The Datalevin benchmark (math-bench Q4, academic ancestry traversal) reports: Datalevin 2.9ms, Datomic 40s, Datascript OOM.

---

## Decision

Use **Datalog** as the preferred substrate for all lattice traversal and transitive-closure queries.

**Primary implementation:** `pg_mentat` — a Datomic-compatible Datalog extension for PostgreSQL that keeps lattice rules and facts in the same state kernel (ADR-001). This avoids a separate operational footprint.

**Fallback / sidecar:** Datalevin as a standalone Datalog engine treating Postgres as storage, for cases where `pg_mentat` is insufficient.

**Recursive CTEs remain acceptable for:**
- Prototypes
- Shallow hierarchies (≤6 levels)
- One-off queries where installing pg_mentat is not warranted

**Example Datalog rules for lattice dominance:**

```datalog
;; Base: direct ordering
(dominates ?a ?b) :- (directly-above ?a ?b).

;; Recursive: transitive closure
(dominates ?a ?c) :- (dominates ?a ?b), (dominates ?b ?c).

;; Join: least upper bound
(join ?a ?b ?j) :- (dominates ?j ?a), (dominates ?j ?b),
                   (not (exists ?k (dominates ?k ?j),
                                   (dominates ?k ?a),
                                   (dominates ?k ?b))).
```

---

## Consequences

**Positive:**
- Datalog natively expresses recursive rules; no manual memoization.
- pg_mentat keeps lattice data and rules co-located with Postgres state.
- Datalevin benchmark shows 1000×+ speedup over Datomic on recursive queries.
- Lattice rules are declarative and auditable.

**Negative / risks:**
- pg_mentat is a small ecosystem; limited community support.
- Datalog syntax is unfamiliar to SQL-only engineers.
- Debugging Datalog rules requires tooling that may not be mature.

**Mitigation:** maintain a parallel recursive CTE implementation for debugging and cross-validation. Treat Datalog as the production path, CTEs as the reference implementation.

---

## Alternatives considered

| Alternative | Reason rejected |
|---|---|
| Recursive CTEs only | Performance degradation at scale; no memoization |
| Neo4j / Memgraph (property graph) | Separate operational footprint; Cypher is less composable with SQL |
| SPARQL / RDF | Heavyweight; semantic web stack incompatible with Postgres-first design |
| Datomic | Closed-source; JVM dependency; 40s on benchmark query pg_mentat does in 2.9ms |
| Materialize / Feldera | Differential dataflow is right for incremental MVs (ADR-001), not for rule-based lattice traversal |

---

## References

- pg_mentat — github.com/mozilla/mentat (Datomic-style Datalog in Rust, embeddable)
- Datalevin math-bench Q4 — github.com/juji-io/datalevin/blob/master/benchmarks
- Birkhoff, G. (1967). *Lattice Theory.* AMS Colloquium Publications XXV, 3rd ed.
- Denning, D.E. (1976). *A lattice model of secure information flow.* Comm. ACM 19(5):236–243.
