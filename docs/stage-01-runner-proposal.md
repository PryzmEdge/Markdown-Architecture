# Canonical `01-research` Runner — Design Proposal

**Status**: Proposal — no runner code landed | **Date**: 2026-06-13
**Depends on**: the `ai_gateway.call_llm` chokepoint (landed) and
`_config/skills/audit_logger.write_receipt` (already in tree).

This note specifies what a canonical Stage-01 runner must do to satisfy the
**tree's real `01-research` output contract**, as decided in
`docs/proof-trio-reconciliation.md` (tree schema + `--stage` CLI +
`audit_logger` win; the proof trio adapts). It is a design, not an
implementation — `run_stage.py` does not land until this shape is approved.

The earlier `_incoming/` prototype `run_stage.py` wrote a single `research.md`
with `risk_tier`-tagged frontmatter and called the contract validator on that
one file. That is **not** the tree's contract. The differences are the whole
point of this note.

---

## The chokepoint seam

The runner calls exactly one model entry point — the canonical gateway at repo
root:

```
call_llm(prompt, *, stage_id, tier="haiku", max_tokens=1024) -> LLMResult
    LLMResult = (text, model_id, input_tokens, output_tokens)
```

Nothing vendor-specific lives in the runner; swapping the model behind a tier
is a one-line change in `ai_gateway.MODEL_BY_TIER`. The runner depends only on
this signature, so it is testable with a stub gateway and never imports the
Anthropic SDK directly.

---

## The six-step shape

```
run_stage_01(problem_path, *, operator_id):

 1. INGEST   Read stages/00-intake/output/problem.md and assert the 00->01
             contract: status: approved, operator_approved: true, domain set.
             Halt with a clear message if any fails. Carry `domain` forward.
             Load only the `## Constraints` section of _config/domain-rules.md.

 2. CALL     prompt = build_research_prompt(problem, constraints)
             result = call_llm(prompt, stage_id="01-research", tier="haiku")

 3. PARSE    Split result.text into:
               - brief body (restatement + top findings + solution directions)
               - a sources table, >= 3 rows, each scored Primary/Secondary/Anecdotal
               - a contradictions list (may be empty)

 4. WRITE    stages/01-research/output/{brief,sources,contradictions}.md
             - every file: base frontmatter [status, operator_approved, stage, domain]
             - operator_approved: FALSE   (fresh draft; production != approval)
             - sources.md: stamp `sources_count` = counted table rows
             - contradictions.md: written even when empty (never suppressed)

 5. RECEIPT  audit_logger.write_receipt({
                 "stage_id": "01-research",
                 "agent_id": "research-agent",
                 "operator_id": operator_id,
                 "input_artifacts":  [{"path": "stages/00-intake/output/problem.md"}],
                 "output_artifacts": [{"path": ".../brief.md"},
                                      {"path": ".../sources.md"},
                                      {"path": ".../contradictions.md"}],
                 "llm_prompt": prompt,        # hashed, not stored
                 "llm_response": result.text, # hashed, not stored
                 "frontmatter_snapshot": {...},
                 "gate_check_results": {...},
             })
             -> stages/01-research/output/receipts/<ts>.json

 6. STOP     Print the operator handoff:
             "review the three drafts, set operator_approved: true on each,
              then run:  python _config/stage-contract.py --stage 01-research"
```

---

## Contract obligations the runner must meet (all [TREE])

| Obligation | Source |
|---|---|
| Outputs are `brief.md` + `sources.md` + `contradictions.md` (not `research.md`) | `STAGE_OUTPUT_REQUIREMENTS["01-research"]` |
| Each output carries `[status, operator_approved, stage, domain]` | `REQUIRED_FRONTMATTER_BASE` |
| `sources.md` frontmatter `sources_count` matches the table row count, count >= 3 | `validate_stage` 01-research cross-check |
| `contradictions.md` exists even if empty | governance: never suppress contradictions |
| A receipt JSON lands under `stages/01-research/output/receipts/` | `audit_logger.write_receipt` |
| The contract is checked with `--stage 01-research`, run AFTER human approval | production/approval split |

`operator_approved` is written **false**; the runner stops before the gate. A
human reviews, flips the three flags, then runs `--stage 01-research`. The
single-artifact mode added to the validator (`stage-contract.py <file>`) is
available for spot-checking one draft, but stage promotion still goes through
`--stage`.

---

## Deltas from the `_incoming/` prototype

- 1 output file -> **3** output files.
- `risk_tier` base field -> **`domain`** base field.
- adds the `sources_count` / >=3-rows obligation the prototype had no notion of.
- receipt via `audit_logger.write_receipt` (per-run JSON under the stage's
  `receipts/`) -> **not** the prototype's `audit/session_log.jsonl`.
- final check `stage-contract.py <path>` -> `stage-contract.py --stage 01-research`.

---

## Open implementation choices (resolve at build time, not here)

1. **Input source**: read `00-intake/output/problem.md` (canonical) vs. accept a
   `--problem <path>` for demo runs. Recommend supporting both: default to the
   intake output, allow an override path.
2. **Parsing robustness**: how strictly to parse the model's sources table.
   Recommend a structured prompt that asks for a fenced table in a fixed column
   order, then a tolerant row counter that matches `count_sources_in_table`.
3. **Tier**: `haiku` per the stage CONTEXT; revisit only if research quality
   demands `sonnet`.

No runner code lands until this shape is approved.
