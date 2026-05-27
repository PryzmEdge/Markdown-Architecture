# Experiment 04 — Consumer-Swap Test

Tests the markdown-as-substrate half of the thesis: a Stage 02 `synthesis.md` should be consumable, unchanged, by at least three independent runtimes.

## Hypothesis

The thesis claim is:

> "Markdown is a human-readable orchestration substrate — not an execution environment. Its consumers (parsers, runtimes, LLM agents, Pandoc filters, notebook kernels) do the executing."

If `synthesis.md` is genuinely substrate-portable, three independent consumers should produce coherent outputs from the **same exact bytes**. If any consumer requires modification to the source, the artifact was secretly consumer-coupled.

## Method

Three consumers, three verification rules, one fixture:

| Consumer | Output | Verification | Container-runnable? |
|---|---|---|---|
| **A. Pandoc** | HTML + PDF | All 5 section headings render; YAML frontmatter title becomes `<title>`; no missing references | ✅ yes |
| **B. LLM (Anthropic)** | 200-word summary | Summary names the core claim, the Yamashita 2025 counter-argument, and the assigned risk_tier | mock yes, real needs `$ANTHROPIC_API_KEY` |
| **C. Obsidian** | Vault entry | Properties pane shows 7 frontmatter fields, all 5 sections render, tables render, no broken wikilinks | ❌ desktop only |

The fixture is a hand-written `synthesis.md` that satisfies the Stage 02 schema. It uses **no Obsidian-specific syntax** (no `[[wikilinks]]`, no `![[embeds]]`) to keep it neutral across consumers.

## Running

### Consumer A — Pandoc → HTML and PDF

```bash
# Install pandoc if you don't have it
sudo apt install pandoc            # or: brew install pandoc

# HTML (works without LaTeX)
pandoc experiments/04-consumer-swap/synthesis.md \
  -o experiments/04-consumer-swap/results/synthesis.html \
  --standalone --metadata title="Stage 02 Synthesis"

# PDF (needs a PDF engine; weasyprint is lightweight)
pip install --user weasyprint
pandoc experiments/04-consumer-swap/synthesis.md \
  -o experiments/04-consumer-swap/results/synthesis.pdf \
  --pdf-engine=weasyprint
```

### Consumer B — LLM summary

Mock (smoke test, runs anywhere):

```bash
python3 experiments/04-consumer-swap/consume_llm.py \
  --synthesis experiments/04-consumer-swap/synthesis.md \
  --out experiments/04-consumer-swap/results/summary-mock.txt \
  --backend mock
```

Real (needs `$ANTHROPIC_API_KEY`):

```bash
pip install --user anthropic
export ANTHROPIC_API_KEY=sk-ant-...
python3 experiments/04-consumer-swap/consume_llm.py \
  --synthesis experiments/04-consumer-swap/synthesis.md \
  --out experiments/04-consumer-swap/results/summary-claude.txt \
  --backend claude --model claude-sonnet-4-6
```

The harness checks the summary for three anchors:
- `core_claim` — mentions PostgreSQL + substrate/kernel/ledger
- `counter_argument_yamashita` — names Yamashita
- `risk_tier_medium` — mentions Medium

Verdict `PASS` if all 3 anchors are present.

### Consumer C — Obsidian

Manual. See `consume_obsidian.md` for the step-by-step verification procedure. Record the result in `results/obsidian-verification.md`.

## Results

### Consumer A — Pandoc

**PASS.** Ran in container.

- HTML: 9 KB; all 5 section headings present (`Core claim`, `Evidence map`, `Integrated findings`, `Counter-argument`, `Recommendations`); `<title>Stage 02 Synthesis</title>` from YAML metadata.
- PDF: 30 KB via weasyprint. Two CSS warnings (`overflow-x: auto`, `gap: min(4vw, 1.5em)` — both Pandoc's default-template artifacts, not from `synthesis.md`); content rendered fine.

Source file unchanged.

### Consumer B — LLM (mock)

**PASS.** Ran in container.

- All 3 anchors detected in the mock summary.
- Real-LLM run is the user's job. The mock summary is a fixed string that names the anchors; it does NOT prove that a real LLM would do the same. It only proves the verification logic works.

### Consumer C — Obsidian

**DEFERRED.** Run on your Mac per `consume_obsidian.md`.

## What the real result will tell us

If all three consumers produce coherent outputs from the same `synthesis.md` bytes:
- The markdown-as-substrate claim holds for this artifact class.
- Stage 02 artifacts can be consumed by humans (Obsidian), by automated rendering (Pandoc → PDF for distribution), and by AI agents (LLM → summary for downstream consumption) without per-consumer adaptation.

If any consumer requires modification:
- Identify which feature of the source broke it (frontmatter syntax? table layout? unquoted YAML?) and either patch the source to be neutral OR document a per-consumer transformation step.
- The thesis is weakened in proportion to how much per-consumer adaptation is needed.

## Caveats

- **One artifact, one class.** This experiment tests a Stage 02 `synthesis.md`. Other stage artifacts (`problem.md`, `risk.md`, the PromptExecutionReceipt JSON) have different shapes and may behave differently. A complete consumer-swap test runs the same harness against every artifact class in the pipeline.
- **Three consumers is the minimum.** More consumers (Marp slides, Quarto reports, Jupyter notebooks, GitHub-rendered markdown, mdBook) would strengthen the result. Each adds one runtime to the "this byte stream can be consumed unchanged" claim.
- **Obsidian is desktop-only.** A CI-friendly substitute would be `marked` or `markdown-it` (the parsers Obsidian's renderer is built on) but those don't test the Properties-pane parsing, which is the most distinctive Obsidian-specific behavior.
- **The mock LLM is not the real LLM.** Mock-mode results validate the harness, not the thesis. A real LLM may compress or omit details that the mock retains.

## Files

| File | Purpose |
|---|---|
| `synthesis.md` | Hand-written Stage 02 fixture — the bytes under test |
| `consume_llm.py` | Consumer B harness (mock + Anthropic) |
| `consume_obsidian.md` | Consumer C manual verification procedure |
| `results/synthesis.html` | Pandoc → HTML output (in-container run) |
| `results/synthesis.pdf` | Pandoc → PDF output via weasyprint (in-container run) |
| `results/summary-mock.txt` | Mock LLM summary output |
| `README.md` | This file |
