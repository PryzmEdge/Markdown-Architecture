---
status: draft
operator_approved: false
risk_check_passed: false
stage: "02-analysis"
---

# Stage 02 — Analysis

## Purpose
Synthesize research findings into a structured argument, model, or decision. Identify gaps, risks, and the strongest counter-argument.

---

## Inputs
| Input | Source | Format | Required |
|---|---|---|---|
| Research brief | `stages/01-research/output/brief.md` | Markdown | ✅ |
| Source log | `stages/01-research/output/sources.md` | Markdown table | ✅ |
| Contradictions log | `stages/01-research/output/contradictions.md` | Markdown list | ✅ |
| Domain constraints | `_config/domain-rules.md` § Constraints | Markdown section | ✅ |

---

## Process
1. Restate the core claim from the problem statement.
2. Map each top finding to: supports / refutes / neutral.
3. Build the strongest possible counter-argument using only the contradictions log.
4. Assess risk tier: Low / Medium / High / Critical (per `_config/domain-rules.md`).
5. If risk tier is High or Critical → `risk_check_passed` must be set by operator before promotion.
6. Write synthesis to output.
7. Run `python _config/stage-contract.py --stage 02-analysis`.

---

## Outputs
| Output | Path | Format |
|---|---|---|
| Analysis synthesis | `stages/02-analysis/output/synthesis.md` | Markdown |
| Risk assessment | `stages/02-analysis/output/risk.md` | Markdown (tier + rationale) |
| Counter-argument | Inside `synthesis.md` § Counter-Argument | Markdown section |

---

## Inter-Stage Contract (01 → 02)
The `brief.md` from Stage 01 must contain:
```yaml
status: approved
operator_approved: true
```
Source log must have ≥3 rows. Contradictions log must exist.

---

## Acceptance Criteria
- [ ] Every top finding mapped (supports / refutes / neutral)
- [ ] Counter-argument section present
- [ ] Risk tier assigned and documented
- [ ] `risk_check_passed: true` if tier is High or Critical
- [ ] `stage-contract.py` passes
- [ ] `operator_approved: true`

---

## Failure / Rollback
- If risk tier is Critical and operator has not set `risk_check_passed: true` → hard stop, do not write to `03-output/`.
- If synthesis contradicts the problem statement without explanation → flag `status: needs-revision`.
