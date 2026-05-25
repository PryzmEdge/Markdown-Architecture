---
status: draft
operator_approved: false
risk_check_passed: false
stage: "00-intake"
---

# Stage 00 — Intake

## Purpose
Capture and qualify a raw idea, question, or problem statement. Nothing proceeds until the intake artifact is operator-approved.

---

## Inputs
| Input | Source | Format | Required |
|---|---|---|---|
| Raw problem statement | Operator (you) | Plain text or markdown | ✅ |
| Domain tag | Operator | String (e.g. `quant`, `devops`, `research`) | ✅ |
| Scope boundary | Operator | 1–3 sentences: what this is NOT | ✅ |
| Prior art refs (optional) | Operator or agent | List of URLs / citations | ❌ |

---

## Process
1. Restate the problem in one sentence — falsifiable or actionable form only.
2. Assign a `domain` tag from `_config/domain-rules.md`.
3. Write a 2-sentence scope exclusion (what this will not address).
4. Check: does a `stages/01-research/` artifact already exist for this problem? If yes, link it and stop.
5. Set `operator_approved: false` — do not promote until operator reviews.

---

## Outputs
| Output | Path | Format |
|---|---|---|
| Qualified problem statement | `stages/00-intake/output/problem.md` | Markdown with YAML frontmatter |
| Domain tag | YAML frontmatter field `domain` | String |
| Scope exclusion | `stages/00-intake/output/problem.md` § Scope | Markdown section |

---

## Acceptance Criteria (all must be GREEN before promotion)
- [ ] Problem is stated in one sentence, falsifiable or actionable
- [ ] `domain` field populated
- [ ] Scope exclusion written (≥2 sentences)
- [ ] `operator_approved: true` set by operator

---

## Failure / Rollback
- If problem statement is ambiguous after 2 refinement attempts → flag as `status: blocked`, notify operator, halt.
- Do not write to `01-research/` until all criteria are GREEN.
