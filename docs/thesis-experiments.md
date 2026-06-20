---
title: "Thesis Experiments — Falsifiable Tests for the Core Architectural Claim"
status: "draft"
date: "2026-05-27"
operator_approved: false
risk_check_passed: false
---

# Thesis Experiments

A research program with four falsifiable experiments testing the core thesis stated in `CLAUDE.md` and `docs/v10-draft.md`:

> "The LLM is not the system. It is a probabilistic reasoning subsystem inside a deterministic operating environment. Orchestration, state, and tooling quality determine production reliability — not model capability alone."

Plus the related markdown-as-substrate claim:

> "Markdown is a human-readable orchestration substrate — not an execution environment. Its consumers (parsers, runtimes, LLM agents, Pandoc filters, notebook kernels) do the executing."

Each experiment is small enough to ship as a self-contained harness with code, fixtures, run script, and a README that records hypothesis → method → results → interpretation. Experiments are independent: any one can fail without invalidating the others, and the cheapest are deliberately first so a single round of work yields data even if the program never finishes.

---

## Experiment 01 — Fault-injection on `proof/workflow.py`

**Hypothesis.** A workflow built as "step-per-transaction durability around a deterministic gate" will leave the database in one of exactly four consistent states after a process kill at any timing: `{empty, ingest-committed, gate-committed, complete}`. There are no half-committed events. There are no partial receipts without an event log. There are no events without their corresponding side effects.

**Method.** Spawn `proof/workflow.py` as a subprocess, kill it (`kill -9`) at a randomized delay sampled from `0.1s` to `1.5s`, then inspect Postgres. Repeat N=100 times. Classify each run's terminal state by counting `workflow_events` rows for that `workflow_run_id` and joining against `provenance_log`. Tabulate the distribution.

**Falsifiable failure modes.**
- A run yields 1 event but the row's `status` is anything other than `passed` for `ingest`. (Impossible if commits are atomic.)
- A run yields a `provenance_log` row but the `workflow_events` table doesn't show `step_name=receipt, status=passed`. (Filesystem write succeeded but DB commit didn't.)
- A run yields more rows than the workflow ever issues for that ID. (Re-entrancy bug.)
- Any state outside `{0, 1, 2, complete}`.

**Success criteria.** 100/100 runs land in one of the four expected states; the distribution is bimodal toward "complete" and "empty" (long tails are unusual). Either of the failure modes above falsifies the thesis as implemented.

**Outputs.** `experiments/01-fault-injection/results.json` with run-by-run classification; `experiments/01-fault-injection/README.md` with the empirical distribution and a one-paragraph interpretation.

**Effort.** 1-2 hours.

---

## Experiment 02 — Replay-determinism test

**Hypothesis.** ADR-005 requires the workflow layer to be pure (no `datetime.now()`, no `uuid.uuid4()`, no network calls, no clocks). A replay of the event log from any committed run should produce *identical gate decisions* on any machine, any time.

**Method.** Record the full `workflow_events` log from a single completed run of `proof/workflow.py`. Build a `replay.py` harness that re-reads the events and re-derives each gate's verdict from the recorded payload (operator_approved, status, etc.). Compare the replayed verdicts against the original.

**Expected result (and the productive failure).** The current `proof/workflow.py` violates ADR-005's purity rules: it calls `datetime.now(timezone.utc)` and `uuid.uuid4()` inside the workflow body. **The replay test will fail today** because the receipt's `timestamp` and `receipt_id` are non-deterministic. We expect this failure. It empirically pins the gap that `proof/explanation.md` § "The DBOS gap" already named in prose. Closing the gap requires moving clocks and UUIDs into idempotent activity wrappers, which is the natural next step for the proof.

**Success criteria.** Replay reproduces every committed gate decision (`operator_approved`, `status_approved`, `contract_passed`) bit-identical. Receipt body fields that depend on wall-clock or randomness are explicitly flagged as non-deterministic and the experiment reports the exact diff between original and replay.

**Outputs.** `experiments/02-replay-determinism/results.json` (diff between original and replay); `README.md` with the verdict and concrete next-steps for closing the gap.

**Effort.** 2-3 hours.

---

## Experiment 03 — Model-swap insensitivity

**Hypothesis.** End-to-end pipeline reliability is dominated by gate quality, not by which LLM occupies the reasoning slot. Holding gates fixed and swapping the model should produce roughly flat metrics; holding the model fixed and varying gate strictness should produce sharply different metrics.

**Method.** This experiment requires a Stage 02 synthesis agent, which doesn't exist yet in this repo (only Stage 00 ingestion is implemented in `proof/`). The minimum-viable version:

1. **Synthesis agent** (`experiments/03-model-swap/synthesize.py`) — takes a `brief.md` + `sources.md` + `contradictions.md` as input, calls an LLM, emits `synthesis.md` with the required Stage 02 frontmatter and sections.
2. **Gate validator** — reuse `_config/stage-contract.py --stage 02-analysis` unchanged.
3. **Two axes.** Axis A holds gates fixed and swaps the model across `claude-haiku-4-5`, `claude-sonnet-4-6`, `claude-opus-4-8`. Axis B holds the model fixed (Sonnet) and varies gate strictness: strict (`risk_check_passed` required, ≥5 sources), normal (current rules), permissive (gates disabled).
4. **Metrics.** Gate-pass rate, contradiction-detection rate (does the synthesis correctly identify a salted contradiction in the test fixture?), operator-override frequency over a 20-run sample per cell.

**Falsification.** If Axis A metrics correlate strongly with model size (Opus dominates Haiku by a wide margin), the thesis is weaker than claimed.

**Container limitation.** No `ANTHROPIC_API_KEY` in this remote container. The harness lands as code + mock LLM + run script. The user runs it on their Mac with a real key.

**Outputs.** `experiments/03-model-swap/results.csv` (or `.json`) with 6 cells of 20 runs each; `README.md` with the two correlation analyses.

**Effort.** 1-2 days + LLM API costs (~$20-40 depending on model mix and prompt size).

---

## Experiment 04 — Consumer-swap test

**Hypothesis.** A Stage 02 `synthesis.md` produced by the pipeline can be consumed unchanged by at least three independent runtimes: Pandoc (→ PDF), an LLM (→ summary), and Obsidian (→ vault). The markdown-as-substrate claim predicts this; if any consumer requires source modification, the artifact is secretly consumer-coupled.

**Method.**

1. Take a hand-written reference `synthesis.md` that satisfies the Stage 02 schema (or generate one via Experiment 03 if it lands first).
2. **Consumer A — Pandoc → PDF.** `pandoc synthesis.md -o synthesis.pdf --pdf-engine=xelatex`. Verify the PDF renders all sections; no missing references; YAML frontmatter is consumed correctly.
3. **Consumer B — LLM → 200-word summary.** Pipe the raw bytes to an LLM with a "summarize this synthesis" prompt; verify the summary names the core claim, the strongest counter-argument, and the risk tier.
4. **Consumer C — Obsidian → vault.** Drop the file into an Obsidian vault; verify the YAML frontmatter parses, internal `[[wikilinks]]` resolve (or non-Obsidian markdown links are gracefully ignored).

**Falsification.** Any consumer requires modification to the source file. (Implicit dependency on consumer-specific rendering quirks.)

**Container limitations.** Pandoc → PDF can run here if `pandoc + texlive` install. LLM consumer needs an API key. Obsidian is desktop-only. Harnesses land as code; user runs the desktop and LLM consumers on their Mac.

**Outputs.** `experiments/04-consumer-swap/results/` with the generated PDF, the LLM summary, and an Obsidian-vault verification log; `README.md` with a per-consumer verdict.

**Effort.** Half a day.

---

## Sequencing

Run order is cheapest-and-most-productive-first. Each experiment is independent; the program can stop after any of them and still yield data:

1. **01 (fault-injection)** — cheapest, exercises the Docker+Postgres infrastructure all four experiments share, and produces a real reliability baseline for the proof.
2. **02 (replay-determinism)** — productive falsification. We expect failure; the failure pins the ADR-005 gap.
3. **03 (model-swap)** — biggest lift; requires building the missing Stage 02 synthesis agent. Harness ships ready-to-run; user provides the API key.
4. **04 (consumer-swap)** — half a day; depends on having a real `synthesis.md` from experiment 03 (or a hand-written fixture).

## What's *not* in scope

- This program does not test the thesis's broader claims about provenance, lattice-based authority (ADR-004), or CRDT collaboration (ADR-002). Those need their own experiments.
- Experiment 03 cannot test against arbitrary LLMs — only those with stable APIs and consistent prompt formatting. Models that hallucinate frontmatter syntax aren't a thesis-falsifying signal; they're a prompt-engineering problem.
- Experiment 04 cannot test all consumers exhaustively. Three independent consumers is the minimum to argue substrate-portability; more would strengthen the claim but at diminishing returns.

## Pointers

- Position paper: `docs/v10-draft.md`
- The proof this builds on: `proof/`
- ADR-001 (Postgres substrate): `docs/adr/ADR-001-postgres-state-kernel.md`
- ADR-005 (Temporal/DBOS split): `docs/adr/ADR-005-temporal-dbos-workflow-split.md`
- The DBOS gap that Experiment 02 will quantify: `proof/explanation.md` § "The DBOS gap"
