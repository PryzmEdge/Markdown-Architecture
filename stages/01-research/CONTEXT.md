---
status: draft
operator_approved: false
risk_check_passed: false
stage: "01-research"
domain: ""
sources_count: 0
---

# Stage 01 — Research

## Purpose
Gather, evaluate, and structure evidence relevant to the qualified problem. Produce a research brief that the analysis stage can act on directly.

---

## Inputs
| Input | Source | Format | Required |
|---|---|---|---|
| Qualified problem statement | `stages/00-intake/output/problem.md` | Markdown | ✅ |
| Domain constraints | `_config/domain-rules.md` § Constraints | Markdown section | ✅ |
| Prior art refs | Intake output or operator | List | ❌ |

---

## Process
1. Load only the `## Constraints` section from `_config/domain-rules.md` (do not load full file).
2. Run literature / source search scoped to the problem domain.
3. For each source: record claim, evidence quality (primary / secondary / anecdotal), and relevance score (High / Med / Low).
4. Identify top 3–5 findings directly relevant to the problem statement.
5. Flag any finding that contradicts the problem hypothesis — do not suppress it.
6. Write research brief to output path.
7. Run `python _config/stage-contract.py --stage 01-research` — must pass before promotion.

---

## Outputs
| Output | Path | Format |
|---|---|---|
| Research brief | `stages/01-research/output/brief.md` | Markdown with YAML frontmatter |
| Source log | `stages/01-research/output/sources.md` | Table: source, claim, quality, relevance |
| Contradictions log | `stages/01-research/output/contradictions.md` | Markdown list (may be empty) |

---

## Inter-Stage Contract (00 → 01)
The `problem.md` from Stage 00 must contain:
```yaml
status: approved
operator_approved: true
domain: <string>
```
If any field is missing or `operator_approved: false`, halt and return to Stage 00.

---

## Acceptance Criteria
- [ ] ≥3 sources evaluated with quality and relevance scored
- [ ] `sources_count` in frontmatter matches actual table row count
- [ ] Contradictions log exists (even if empty)
- [ ] `stage-contract.py` validation passes
- [ ] `operator_approved: true` set by operator

---

## Failure / Rollback
- If fewer than 3 relevant sources found → mark `status: insufficient-evidence`, surface to operator.
- If contract validation fails → fix fields, re-run validator, do not promote.
