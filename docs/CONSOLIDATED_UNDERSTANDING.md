# Markdown Architecture — Consolidated Understanding & Blueprint

**Version**: Understanding-1.0 | **Date**: 2026-05-29 | **Status**: Active
**Supersedes nothing; consolidates**: blueprint v2.0.0 + the conceptual model worked out in design discussion.

---

## Why this document exists

Every prior version of this project *argued* for the architecture. None of them wrote down the plain mental model of how the system actually works — and that gap is exactly what made the design easy to misread. The most natural first assumption about a project called "Markdown Scripting" is that the markdown itself is an executable: that a lead file reads the others, follows a tree of folders, and runs an automated process on its own. That assumption is wrong, but it is wrong in an instructive way, and correcting it is the whole point of the first half of this document.

So this file does two things in order. First it states, in prose, what the system *is* — the conceptual model, written so that someone arriving cold cannot make the executable-markdown mistake. Then it folds in the concrete blueprint: the repository layout, the four-stage pipeline, the contracts, the governance rules, and the honest list of what is built versus outstanding. The argument lives in the position papers; this document is the map and the build sheet, joined to the understanding that makes both legible.

---

## Part 1 — What this system actually is

### The thesis, stated plainly

Markdown is a human-readable orchestration substrate, not an execution environment. The files do not run. They are read. Everything that *does* anything in this system is something other than the markdown — a program, a model, or a person — and the markdown is simply the shared language all of them read and write. The bet of the project is that markdown is an unusually good medium for coordinating work across humans and machines, precisely because it is inert, version-controllable, and equally legible to a person and to a language model.

The reason this matters is practical. If you believe the markdown executes itself, you will look for automation that does not exist and you will misunderstand where the system's authority lives. The authority lives in the *readers*, not in the text. A `CONTEXT.md` that says "approval is required" has no power of its own; a separate program has to open that file, read the claim, and act on it. Delete the program and the file is just as true-sounding and just as powerless.

### The three executors

It helps to name the three things that can read the markdown and act, because keeping them distinct dissolves almost every confusion about the system.

The first executor is **deterministic Python** — the validator, the runner, the gateway. These programs do exactly and only what their code says, identically every time. The second executor is the **LLM agent** — a language model that has been placed in a loop and given tools, so that when it reads a `CONTEXT.md` it can act on those instructions the way an employee acts on a written brief. Unlike the Python, the agent is probabilistic; it will not behave identically on every run. The third executor is **the human operator** — the person who reads a draft, decides it is acceptable, sets `operator_approved: true`, and triggers the next command. The markdown is never any of these actors. It is the connective tissue between them.

A useful image is sheet music and a musician. The sheet music is precise, authoritative-looking, full of instructions — and it produces no sound. It needs a player. The markdown files are the sheet music; the three executors are the players; and "running the system" is the players reading the score and performing it.

### The two modes of running the workspace

There are two genuinely different ways to operate this workspace, and conflating them is the second great source of confusion.

**Mode one is the deterministic Python pipeline.** Here there is no map-reading and no tree-walking at all. A script such as `run_stage.py` calls each piece explicitly, by name, in a fixed order written out by hand: it calls the gateway, writes the output file, writes the receipt. Nothing navigates; the program does precisely what its lines say, like a vending machine. This is the mode the buildability prototype runs in.

**Mode two is the agentic harness.** Here you point a tool such as Claude Code at the repository. The harness automatically loads the lead file (`CLAUDE.md`) into the agent's context at startup, with no instruction from you, and then the agent — holding that map — uses its file-reading tools to walk into whichever stage folder the task points to. This is the "folders as prompt, agent follows a tree" experience: the task determines which single branch gets read, so the agent stays focused and cheap rather than loading the whole repository every turn.

The crucial subtlety is about direction. In mode two the folder tree does not *push* itself into the agent; the agent *pulls* it, by reading a map and choosing where to walk. `CLAUDE.md` is a directory board in a building lobby: it organizes everything and tells any visitor where to go, but it never carries anyone upstairs. The structure *guides*; it never *drives*. And the auto-loading that makes mode two feel effortless is not a property of the markdown — it is a handshake performed by the harness, which arrives at the front door looking for a file of a particular name.

---

## Part 2 — The three-layer model and why the system is model-agnostic

The cleanest way to reason about portability is to split the system into three layers and ask, of each, whether it is tied to any one AI vendor.

The **text layer** — the markdown files, the folder tree, the YAML frontmatter — is not tied to anything. It is characters on disk. Claude can read it; so can GPT, Gemini, a local open-source model, or a human with a text editor. This is not a happy accident but the entire reason the project chose markdown: a substrate that worked with only one model would falsify the central claim of universality.

The **reader layer** is a model running inside a harness. Three words keep this precise. A *model* is the raw brain (Claude Opus, GPT, a local Llama). An *agent* is a model placed in a loop and given tools so it can take multi-step action. A *harness* (also called a runtime or agent framework) is the container that turns a model into an agent and feeds it the files — Claude Code is one such harness; there are others. The model is the brain, the harness is the body and the room, and the agent is the two running together.

The **harness layer** is that surrounding program, and it is the only layer with any vendor-specific naming at the seam where it meets the text — namely, which filename it goes looking for at startup.

Putting these together gives the system's true identity: **it is model-agnostic by design, with exactly two thin adapters.** The first adapter is the *filename the harness loads*. The name `CLAUDE.md` is a convention of the Claude Code harness; a different harness looks for a different name (some read `AGENTS.md`, others read their own rules files). Swapping harnesses therefore means renaming that one file, or keeping a thin file under the new name that simply imports the real map. The map is universal; only the name on the mailbox is harness-specific.

The second adapter is the *one place in the code that calls a model*: the function `call_llm` inside `ai_gateway.py`. That function does `import anthropic` and calls Anthropic's API, so that line genuinely is Claude-specific. But because every model call in the system is routed through this single chokepoint, replacing Claude with another model — OpenAI, or a local model served through something like Ollama — is a rewrite of the inside of one function. Nothing else changes: not the stages, not the contract validator, not the receipts. Isolating the vendor call behind one door is exactly what a gateway is for, and it quarantines the only meaningful coupling to roughly fifteen lines.

One honest nuance separates a tidy claim from a true one. "Can any model *read* the files" and "will any model *follow* them equally well" are different questions. Every capable model can read the markdown; that is near-total portability. But instruction-following *fidelity* varies between models — context windows differ, training conventions differ, and a `CLAUDE.md` is delivered to the model as context, not as enforced configuration, so even a strong model only *attempts* to comply. Swap in a weaker model and it may skim the map or wander into the wrong folder. This is precisely why the system leans on the deterministic Python gate: the contract validator does not care which model produced an artifact: it checks the result identically every time. The governance layer is what makes the whole system robust to *which* brain you plugged in.

---

## Part 3 — Repository structure

```
Markdown-Architecture/
├── CLAUDE.md                  ← Navigation & identity map (≤800 tokens); the file the harness auto-loads
├── README.md                  ← Project overview
├── docs/
│   ├── v10-draft.md           ← Canonical engineering position paper (the argument)
│   └── adr/                    ← Architecture Decision Records (ADR-001 … ADR-005)
├── _config/
│   ├── domain-rules.md         ← Universal + domain constraints (load § Constraints only)
│   └── stage-contract.py       ← Deterministic validator: exits 0 (pass) / 1 (fail)
├── ai_gateway.py               ← The single model-call chokepoint (vendor adapter lives here)
├── stages/
│   ├── 00-intake/    CONTEXT.md + output/problem.md
│   ├── 01-research/  CONTEXT.md + output/{brief,sources,contradictions}.md
│   ├── 02-analysis/  CONTEXT.md + output/{synthesis,risk}.md
│   └── 03-output/    CONTEXT.md + output/<slug>.md + receipts/<timestamp>.md
└── .claude/
    └── settings.json + hooks/  ← Hard constraints (outstanding)
```

The two adapters from Part 2 are visible here: `CLAUDE.md` (the harness handshake) and `ai_gateway.py` (the vendor call). Everything else is either inert text or model-agnostic Python.

---

## Part 4 — The ICM pipeline: four stages

The work moves through four stages, each a folder with its own `CONTEXT.md` (the brief an agent reads) and an `output/` directory. Promotion from one stage to the next is gated; nothing advances until its gate passes. The stages are deliberately separate so that production and approval never collapse into a single step — an agent produces a draft, and only a human can approve it.

**Stage 00 — Intake.** A Problem Qualification Agent restates a raw idea in one falsifiable or actionable sentence, assigns a domain tag, and writes a two-sentence scope exclusion stating what the work will *not* address. The gate is `operator_approved: true`. After two failed refinement attempts the stage sets `status: blocked` and the pipeline halts.

**Stage 01 — Research.** A Research and Evidence Agent gathers and scores evidence, producing `brief.md` (problem restatement plus top findings and solution directions), `sources.md` (a table scoring each source as Primary, Secondary, or Anecdotal), and `contradictions.md` (disconfirming evidence, never suppressed even when empty). The gate requires at least three scored sources and a passing contract check; fewer than three relevant sources sets `status: insufficient-evidence`.

**Stage 02 — Analysis.** A Synthesis and Risk Agent integrates the findings into a structured argument, builds the strongest possible counter-argument from `contradictions.md`, and assigns a risk tier in `risk.md`. Risk tiers are AI-suggested but operator-validated; High and Critical are never auto-approved. A Critical risk without operator sign-off is a hard stop.

**Stage 03 — Output.** An Output Assembly Agent produces the only externally shareable artifact, named by a `<domain>-<keyword>-<date>` slug, in one of several formats (paper, brief, spec, adr, runbook). The gate requires every upstream stage approved, an audit receipt written, a passing contract, and the operator's final sign-off.

---

## Part 5 — Inter-stage contracts

The contract validator, `_config/stage-contract.py`, is the deterministic gate between stages and the clearest demonstration that authority lives in the readers, not the text. It opens an artifact, parses the YAML frontmatter, and answers one question — is this allowed to proceed — by exiting `0` for pass or `1` for fail. That exit code *is* the contract: a Makefile, a git hook, or a CI step can branch on it without reading any prose.

Every artifact carries frontmatter of this shape:

```yaml
---
status: approved          # draft | review | approved | blocked | needs-revision
operator_approved: true   # false until a human explicitly sets it true
risk_check_passed: true   # required when risk tier is High or Critical
stage: "01-research"
domain: "architecture"
---
```

Promotion is blocked if any required field is missing or if `operator_approved` is not the boolean `true`. The validator deliberately treats the string `"true"` as a failure, catching a common YAML mistake. Because this check is pure Python, it behaves identically regardless of which model — or which vendor — produced the artifact it is judging.

---

## Part 6 — Governance and risk

The universal constraints are few and absolute: never write to `output/` until `operator_approved: true`; never suppress contradictions (the file must exist even when empty); never claim novelty without citing prior art; every artifact must carry valid frontmatter; never load the full `domain-rules.md` (load only its `## Constraints` section, to stay within the context budget).

Risk is tiered, and the tier determines the gate:

| Tier | Definition | Gate |
|---|---|---|
| **Low** | Reversible, no external dependency | None |
| **Medium** | Reversible, external dependency exists | Operator review |
| **High** | Partially irreversible or costly to undo | `risk_check_passed: true` |
| **Critical** | Irreversible, public, or financial consequence | `risk_check_passed: true` + explicit operator sign-off |

When a stage blocks, the operator reviews the stage's output directory, either fixes the issue or accepts the risk, and the agent resumes *from the blocked stage* rather than restarting the pipeline. State lives in the filesystem, so nothing is lost between blocking and resuming.

---

## Part 7 — Architecture Decision Records

Five decisions are recorded and accepted: PostgreSQL as the state kernel and provenance ledger (ADR-001); an Automerge/Yjs CRDT-as-bytea-blob pattern over Postgres for collaboration (ADR-002); Datalog as the policy and query engine (ADR-003); a FIDES information-flow label lattice (ADR-004); and a Temporal/DBOS workflow split for durable governance (ADR-005). ADRs are append-only; a superseded record is marked as such and linked to its replacement rather than deleted.

---

## Part 8 — What is built versus outstanding

This is the honest status, and it matters because it marks the real frontier of the project — the line between what has actually run and what is still argument.

**Built and demonstrated.** A minimal buildability prototype now runs the core loop end to end for a single stage. The deterministic contract validator was executed live and behaves correctly in three cases: it fails an artifact whose `operator_approved` is still `false`, passes the same artifact once a human sets it `true`, and rejects malformed frontmatter — three deterministic exit codes, with no model involved. The gateway, receipt writer (including the v8 cost fields), and stage runner are written and wired.

**Stubbed in the prototype.** The live model call was not executed in the build environment (no network access there), so the prompt-to-output half of the loop is written but unrun; the Anthropic SDK call signature should be confirmed against the current docs on first real run; and the per-token pricing and model IDs are placeholders to be set to real values.

**Outstanding (from blueprint v2).** The high-priority items are the `.claude/settings.json` hooks (pre-commit contract run, risk assessment, receipt logging), a `Makefile` that chains the stages into the automated flow people imagine, and a fuller buildability proof wiring Postgres, a markdown ingester, and a receipt emitter through one workflow. Medium-priority items include `CONTRIBUTING.md`, a `LICENSE`, CI that runs the contract on every pull request, a tiered risk register, and an incident runbook.

The "automated process" that a newcomer pictures — point it at a question and watch the pipeline flow on its own — is precisely this outstanding tier. It is not yet built, and naming that plainly is more useful than implying otherwise. The markdown was never going to automate anything by itself; automation is the executors wired around it.

---

## Part 9 — Where this leaves the project

The project now has a defensible, concrete identity rather than a vague aspiration: it is a **model-agnostic markdown orchestration substrate with a deterministic governance spine and two thin vendor adapters**, demonstrated by a running single-stage proof and specified in full by the blueprint above. That identity is enough to choose a direction deliberately. Toward a *running system*, the next move is the second stage and a Makefile, so that promotion-gating becomes something you watch happen rather than assert. Toward a *written account*, the architecture can now be stated precisely enough that the paper largely writes itself. Either path is legitimate; the difference is no longer being decided in the dark.

---

*Consolidated Understanding 1.0 — Markdown Architecture. Joins blueprint v2.0.0 to the conceptual model. Generated 2026-05-29.*
