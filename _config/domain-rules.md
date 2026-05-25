---
version: "1.0.0"
scope: "all stages"
load_instruction: "Load ## Constraints section only — do not load full file"
---

# Domain Rules

> **Load instruction**: agents should load only the `## Constraints` section per the CLAUDE.md navigation rules.

---

## Constraints

### Universal (apply to every stage)
- Never write to a stage's `output/` directory until `operator_approved: true` is confirmed.
- Never suppress contradictions or disconfirming evidence — log them.
- Never claim novelty without citing prior art.
- Every artifact must have valid YAML frontmatter with `status`, `operator_approved`, `risk_check_passed`, and `stage`.
- Do not load full files when a section is sufficient.

### Risk Tier Definitions
| Tier | Definition | Gate Required |
|---|---|---|
| Low | Reversible, no external dependency | None |
| Medium | Reversible, external dependency exists | Operator review |
| High | Partially irreversible or high-cost to undo | `risk_check_passed: true` |
| Critical | Irreversible, public, or financial consequence | `risk_check_passed: true` + explicit operator sign-off |

### Domain-Specific (quant / research)
- Claims must be grounded in citations or formal models — not analogy alone.
- Hypotheses must be stated in falsifiable form.
- Every output that will be shared externally must pass the counter-argument check in Stage 02.

---

## Escalation Path
1. Agent flags issue with `status: blocked` or `status: needs-revision`.
2. Operator reviews and either resolves or accepts risk.
3. Operator sets `operator_approved: true` to unblock.
4. Agent resumes from the blocked stage — does not restart pipeline.
