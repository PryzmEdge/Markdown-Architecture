---
status: draft
operator_approved: false
risk_check_passed: false
stage: "03-output"
---

# Stage 03 — Output

## Purpose
Assemble the final deliverable from approved analysis. This is the only stage that produces externally shareable artifacts.

---

## Inputs
| Input | Source | Format | Required |
|---|---|---|---|
| Analysis synthesis | `stages/02-analysis/output/synthesis.md` | Markdown | ✅ |
| Risk assessment | `stages/02-analysis/output/risk.md` | Markdown | ✅ |
| Original problem statement | `stages/00-intake/output/problem.md` | Markdown | ✅ |

---

## Process
1. Confirm all upstream stages have `operator_approved: true` and `status: approved`.
2. Select output format: `paper` | `brief` | `spec` | `adr` | `runbook`.
3. Assemble deliverable — include: problem restatement, key findings, counter-argument, risk tier, recommendations.
4. Write `PromptExecutionReceipt` entry to audit log.
5. Run `python _config/stage-contract.py --stage 03-output`.
6. Set `status: review` — operator does final approval before external share.

---

## Outputs
| Output | Path | Format |
|---|---|---|
| Final deliverable | `stages/03-output/output/<slug>.md` | Markdown with full YAML frontmatter |
| Audit receipt | `stages/03-output/output/receipts/<timestamp>.md` | PromptExecutionReceipt format |

---

## Inter-Stage Contract (02 → 03)
Both `synthesis.md` and `risk.md` must have:
```yaml
status: approved
operator_approved: true
risk_check_passed: true  # required if risk tier was High or Critical
```

---

## Acceptance Criteria
- [ ] All upstream stages approved
- [ ] Deliverable includes all 5 required sections
- [ ] Audit receipt written
- [ ] `stage-contract.py` passes
- [ ] `operator_approved: true` (final gate)

---

## Failure / Rollback
- If any upstream stage is not `approved` → halt, surface which stage is blocking.
- If audit receipt write fails → do not mark output as approved, alert operator.
