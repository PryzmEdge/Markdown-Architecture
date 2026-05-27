# Experiment 03 — Model-Swap Insensitivity

Tests whether end-to-end pipeline reliability is dominated by **gate quality** (orchestration) or by **model capability** (reasoning slot). The thesis predicts orchestration dominates.

## Hypothesis

Holding gates fixed and swapping the LLM (Haiku → Sonnet → Opus) should produce roughly flat metrics. Holding the LLM fixed and varying gate strictness (permissive → normal → strict) should produce sharply different metrics.

If the gradient on Axis A (model) exceeds Axis B (gate strictness), the thesis is falsified.

## Method

A Stage 02 synthesis agent (`synthesize.py`) reads three Stage 01 fixtures (`brief.md`, `sources.md`, `contradictions.md`), prompts the LLM, and writes `synthesis.md`. The harness (`harness.py`) runs N iterations across a 3×3 grid of model × gate strictness, then measures three per-output metrics:

| Metric | What it measures |
|---|---|
| `gate_pass_rate` | Does the gate validator accept the artifact? |
| `contradiction_detection_rate` | Does the synthesis surface the **salted** counter-evidence (Yamashita et al. 2025) from `contradictions.md`? |
| `operator_override_rate` | Did the model assign `risk_tier: High`/`Critical`, requiring sign-off? |

The **salted contradiction** is a key design move: `contradictions.md` contains a fictitious-but-plausibly-formatted citation (Yamashita 2025) that a faithful synthesis agent must name in its Counter-argument section. Models that hallucinate a generic "pgvector has limits" critique without citing Yamashita fail the contradiction-detection probe. The salt is unique enough that false positives are extremely unlikely.

Three gate strictness levels:

- **Permissive** — frontmatter must parse as YAML; that's it.
- **Normal** — matches `_config/stage-contract.py --stage 02-analysis` exactly: requires `status`, `stage`, `operator_approved`, `risk_check_passed`, `risk_tier`; `stage` must be `02-analysis`; `risk_tier` must be one of {Low, Medium, High, Critical}.
- **Strict** — Normal + all five required sections present (`## Core claim`, `## Evidence map`, `## Integrated findings`, `## Counter-argument`, `## Recommendations`) + Counter-argument body ≥ 80 chars.

## Running

### Mock mode (runs anywhere, no API key)

Mock mode does NOT exercise the real thesis. It validates the harness wiring: three deterministic fake "models" with pre-baked behaviors (`good`, `forgetful`, `broken`) prove that the metrics catch the differences they're supposed to catch.

```bash
pip install --user pyyaml

python3 experiments/03-model-swap/harness.py --mode mock --iterations 5
```

Default mock-behaviors are deliberately wrong-headed (`haiku=good`, `sonnet=good`, `opus=forgetful`) to demonstrate what a non-flat Axis A would look like in the result table.

### Real mode (needs `$ANTHROPIC_API_KEY`)

```bash
pip install --user anthropic pyyaml
export ANTHROPIC_API_KEY=sk-ant-...

python3 experiments/03-model-swap/harness.py \
  --mode claude --iterations 20 \
  --models claude-haiku-4-5 claude-sonnet-4-6 claude-opus-4-7
```

Expected wall-clock: ~20-30 minutes for 9 cells × 20 iterations = 180 API calls. Expected cost: ~$15-40 depending on prompt size and the Opus column's share. Outputs land in `results/outputs/`; summary in `results/model-swap-results.json`.

## Mock-mode smoke result (5 iterations × 9 cells = 45 runs)

| model | gate | pass | contradiction | override |
|---|---|---:|---:|---:|
| claude-haiku-4-5 (mock=good) | permissive | 1.00 | 1.00 | 0.00 |
| claude-haiku-4-5 (mock=good) | normal | 1.00 | 1.00 | 0.00 |
| claude-haiku-4-5 (mock=good) | strict | 1.00 | 1.00 | 0.00 |
| claude-sonnet-4-6 (mock=good) | permissive | 1.00 | 1.00 | 0.00 |
| claude-sonnet-4-6 (mock=good) | normal | 1.00 | 1.00 | 0.00 |
| claude-sonnet-4-6 (mock=good) | strict | 1.00 | 1.00 | 0.00 |
| claude-opus-4-7 (mock=forgetful) | permissive | 1.00 | 0.00 | 0.00 |
| claude-opus-4-7 (mock=forgetful) | normal | 1.00 | 0.00 | 0.00 |
| claude-opus-4-7 (mock=forgetful) | strict | 1.00 | 0.00 | 0.00 |

Interpretation (mock data ONLY — not the real thesis result):
- Contradiction-detection dropped to 0% in the forgetful cells, proving the salted-Yamashita probe fires correctly.
- Gate-pass rate stayed at 100% across all cells because the mock outputs all pass even the strict gate. To exercise gate failures, set `--mock-behaviors good good broken` — the `broken` behavior omits `risk_tier` from frontmatter and should fail normal+strict gates.

## What the real result will tell us

| Observed pattern (real LLM data) | Interpretation |
|---|---|
| Axis A flat (Haiku ≈ Sonnet ≈ Opus on all 3 metrics) AND Axis B steep (permissive >> normal >> strict on gate-pass) | **Thesis supported.** Gate quality dominates. Operator can choose the cheapest model. |
| Axis A steep (clear gradient by model size) AND Axis B flat | **Thesis falsified.** Model capability dominates. Operator must pay for the biggest model. |
| Both flat | **Inconclusive.** Either the gates are too easy to fail or the metric is the wrong proxy. |
| Both steep | **Thesis partially supported.** Both axes matter; the cheaper-model-with-strong-gates strategy still wins as long as the gradients aren't equal-magnitude. |

The contradiction-detection metric is particularly sharp. Surfacing a named-and-cited contradiction is harder than producing a generically-shaped synthesis. If a model can do that reliably, the gates can be lighter; if it can't, the gates must catch the omission downstream.

## Caveats and limitations

- **Single fixture.** One brief/sources/contradictions triple. To generalize, swap in 10-20 different topics with different salted-contradiction probes and report the distribution.
- **One salted probe per fixture.** A model that detects half of two contradictions is not measurable here. Multi-probe contradictions would refine the metric.
- **Cost calibration.** Opus is ~10× the input-token cost of Haiku and ~3-5× Sonnet. A naive 20-runs-per-cell sample weights toward Opus expense; if budget is tight, run Opus at 5 iterations and Haiku/Sonnet at 30.
- **Prompt sensitivity.** A different prompt template might produce a different Axis A gradient. The thesis claim is about gate quality vs *adequately-prompted* models. Adversarial prompts on the small model would distort the result.

## Files

| File | Purpose |
|---|---|
| `synthesize.py` | Stage 02 synthesis agent (mock + Anthropic backends) |
| `harness.py` | 3×3 grid runner + metric computer + summary writer |
| `fixtures/brief.md`, `fixtures/sources.md`, `fixtures/contradictions.md` | Stage 01 input artifacts; `contradictions.md` contains the salted Yamashita 2025 probe |
| `results/outputs/` | Per-cell synthesis.md outputs (one per iteration) |
| `results/model-swap-results.json` | Tabulated per-cell rates + Axis A/B summaries |
| `README.md` | This file |
