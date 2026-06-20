# v10 Citations — Staged Insertions  ·  SUPERSEDED

> **Status — SUPERSEDED (retained for provenance; do not re-apply).** Superseded 2026-06-20.
> This was the staged citation feeder for `docs/v10-draft.md`. Its contents have landed; it is kept only as the provenance trail.
> - **Body insertions (Blocks A–F):** landed at `ec2c4dc`.
> - **Appendix reference groups + Experiment-03 fix:** landed at `50ec6c2` / `df7cefb`.
> - **Block C here was superseded by `block_C_reconciled.md` before merge** — do not apply the original single-subsection Block C below.
> - **Corrections C1 / C2 were preventive and proved moot:** the claims they guard against were never present in `docs/v10-draft.md` (verified by grep at `ec2c4dc`). Nothing was applied; they remain as guard-rails only.
> Anchors are given by **Part / heading** (stable), not line number — line numbers drift, and the assembly map's were already stale at HEAD.

**Disposition**:

| Block | Source(s) | Landed — body anchor | Appendix group | Commit |
|---|---|---|---|---|
| A | Ning et al., *Code as Agent Harness* (2605.18747) | Part 1 — The Five-Layer Stack | Agent reliability & long-horizon execution | body `ec2c4dc` · appx `50ec6c2` |
| B | Eslami & Yu (2603.10779) | Part 3 — beside Ramadge–Wonham | Agent reliability & long-horizon execution | body `ec2c4dc` · appx `50ec6c2` |
| C (reconciled) | Sinha (2509.09677) · METR (2503.14499) · Cemri/MAST (2503.13657) | Part 3 — compounding math + subsection "Reliability Is a Property of the Gates, Not the Model" | Agent reliability & long-horizon execution | body `ec2c4dc` · appx `50ec6c2` |
| D | Liu/*Lost in the Middle* (2307.03172) · Modarressi/NoLiMa (2502.05167) | Part 4 — The Memory Hierarchy | Long-context behavior | body `ec2c4dc` · appx `50ec6c2` |
| E | Stanford DEL token study · Anthropic multi-agent blog | Part 22 — AI Gateway & Cost Governance | Agent token economics | body `ec2c4dc` · appx `50ec6c2` |
| F | Shinn/Reflexion (2303.11366) · Wang/CodeAct (2402.01030) | Part 3/10 — beside FIDES/CaMeL | Agent reliability & long-horizon execution (folded) | body `ec2c4dc` · appx `50ec6c2` |
| [CORRECTION] C1 | inverted Anthropic orchestrator claim | not present in draft (grep `ec2c4dc`) → **no-op, moot** | — (do not introduce) | n/a |
| [CORRECTION] C2 | DeepMind/Kim counts (Kim et al., 2512.08296) | "260 configs / six benchmarks" not present → **no-op, moot** | Kim **uncited → no Appendix entry** (no-orphan); 17.2× citable with 180 configs / 4 benchmarks *if* added | n/a |
| [FIX] Exp-03 | `claude-opus-4-7 → claude-opus-4-8` (Axis A) | `docs/thesis-experiments.md`, Exp 03 — spec only, not yet run | — | `df7cefb` |

**Provenance note (updated).** Every reference below was verified against its primary source at staging time. Open item: the Sinha author list landed in the draft as a literal `[TODO: complete author list]` and still needs completing against the arXiv record before the bibliography is final.

---

*Original feeder content retained below, unchanged, as the provenance record. Do not re-apply.*

-----

## Block A — Part 1 (Five-Layer Stack): harness survey as the architecture anchor

**Target**: Part 1, “The Five-Layer Stack” (v10-draft.md L74).
**Sits beside**: currently uncited; this is the layer model’s primary external grounding.

**Proposed insertion** (after the stack is introduced):

> This layered separation — inert artifacts, a model operating inside a surrounding software harness, and the execution substrate beneath — is the organizing frame of a 2026 survey from UIUC, Meta, and Stanford, *Code as Agent Harness* (Ning et al., arXiv:2605.18747). It defines an agent harness as “the software layer that surrounds an LLM with tools, APIs, sandboxes, memory, validators, permission boundaries, execution loops, and feedback channels, thereby turning a stateless model into a functional agent,” and organizes agentic systems into three layers — harness interface, harness mechanisms, and scaling the harness — that map onto the stack described here. The survey *frames* this view; it is a synthesis of existing systems, not an experimental result, and remains a non-peer-reviewed preprint.

**Caveat baked in**: “frames … not an experimental result … preprint” — prevents overstating a survey as proof.

**Reference**: Ning, X., Tieu, K., Fu, D., Wei, T., Li, Z., Bei, Y., et al. (2026). *Code as Agent Harness: Toward Executable, Verifiable, and Stateful Agent Systems.* arXiv:2605.18747.

-----

## Block B — Part 3 (reinforce): control-theory anchor beside Ramadge–Wonham

**Target**: Part 3, “Deterministic Scaffolding Around Probabilistic Cores,” at the existing supervisory-control reference (v10-draft.md L31 region / redpen line citing Ramadge–Wonham).
**Sits beside**: the existing “supervisory control of a stochastic plant (Ramadge–Wonham)” citation.

**Proposed insertion** (appended to the existing supervisory-control sentence):

> A 2026 control-theoretic treatment makes this lineage explicit: Eslami & Yu (arXiv:2603.10779) model an agentic system as embedded within a feedback control loop and formalize “agency as hierarchical decision authority over the control architecture,” giving an augmented closed-loop representation and explicit design constraints for safety-critical settings. This is the formal complement to the supervisory-control analogy already invoked here — the deterministic gate is a feedback element, not merely a checkpoint.

**Caveat baked in**: framed as “the formal complement” to what’s already cited, so it reinforces rather than duplicates; preprint status noted in the reference.

**Reference**: Eslami, A. & Yu, J. (2026). *A Control-Theoretic Foundation for Agentic Systems.* arXiv:2603.10779 (preprint).

-----

## Block C — Part 3 (extend): new subsection

**Target**: Part 3, as a new subsection parallel to “The Three Enforcement Layers” (after v10-draft.md L187 region).

**Proposed new subsection** (verbatim):

> ### Reliability Is a Property of the Gates, Not the Model
> 
> The reason the pipeline is gated, rather than run as one open-ended loop, is that reliability degrades across chained steps. As an idealization, if each of N steps succeeds independently with probability p, end-to-end success is p^N — ten steps at 95% each fall to roughly 60%. That independent-error model is only a lower-bound intuition. The real literature sharpens it in both directions: Sinha et al. (arXiv:2509.09677, ICLR 2026) document *self-conditioning*, where per-step accuracy degrades as a trajectory lengthens, meaning errors are positively correlated and decay can be worse than p^N predicts; while retries and verification gates raise the effective per-step reliability. METR (arXiv:2503.14499) gives the empirical horizon picture, and Cemri et al. (MAST, arXiv:2503.13657) show that multi-agent failures are dominated by system design and inter-agent misalignment rather than base-model quality.
> 
> The architectural consequence is the claim this paper stakes: end-to-end reliability is dominated by the quality of the gates, not by which model occupies the reasoning slot. A gate that blocks promotion until a deterministic contract passes interrupts error inheritance — it prevents a downstream stage from treating an upstream stage’s mistake as a verified premise. The *Code as Agent Harness* survey (arXiv:2605.18747, §4.1.1) corroborates the mechanism from real systems: it describes a test executor that “is a deterministic Python script (not an LLM) which cleanly separates reasoning from execution and grounds the feedback signal in objective program behavior.”
> 
> This is a falsifiable claim, and it is designed to be tested directly. Experiment 03 in `docs/thesis-experiments.md` holds the gates fixed and swaps the model across tiers (Axis A), then holds the model fixed and varies gate strictness (Axis B); the thesis predicts roughly flat metrics on Axis A and sharply varying metrics on Axis B, and is falsified if Axis A metrics correlate strongly with model size. That experiment is **designed but not yet run** — it requires a Stage 02 synthesis agent that the current prototype does not implement (only Stage 00 ingestion exists). The claim is therefore stated here as a prediction with a specified falsification test, not as a demonstrated result.

**Caveat baked in**: p^N explicitly demoted to “lower-bound intuition”; the harness survey quoted accurately and attributed as corroboration; Experiment 03 flagged “designed but not yet run” with its blocking dependency named.

**References**:

- Sinha, A., Arun, … & Goel (2026). *The Illusion of Diminishing Returns: Measuring Long-Horizon Execution in LLMs.* arXiv:2509.09677 (ICLR 2026).
- METR (2025). *Measuring AI Ability to Complete Long Tasks.* arXiv:2503.14499.
- Cemri, M. et al. (2025). *Why Do Multi-Agent LLM Systems Fail?* (MAST) arXiv:2503.13657.

-----

## Block D — Part 4 or Part 9: long-context degradation grounding

**Target**: Part 4, “The Memory Hierarchy” (L197) — preferred — or Part 9 retrieval benchmarks (L293). Recommended: Part 4, beside the cost-tier-cache framing.
**Sits beside**: the existing arXiv:2603.09023 memory-hierarchy citation.

**Proposed insertion**:

> Keeping the active context small is a correctness measure, not only a cost measure. The canonical result (Liu et al., “Lost in the Middle,” TACL 2024) shows a U-shaped accuracy curve in which information placed in the middle of a long context is used least reliably, even by models built for long contexts; stricter follow-ups (NoLiMa, ICML 2025) show many models claiming 128K-token windows dropping below half their short-context accuracy by 32K tokens. Loading only the relevant stage folder, and only the constraints section of the rules, keeps the working context inside the reliable regime.

**Caveat baked in**: cites the peer-reviewed phenomenon (Liu; NoLiMa) rather than the industry coinage “context rot.”

**References**:

- Liu, N.F. et al. (2024). *Lost in the Middle: How Language Models Use Long Contexts.* TACL 12:157–173. arXiv:2307.03172.
- Modarressi, A. et al. (2025). *NoLiMa: Long-Context Evaluation Beyond Literal Matching.* ICML 2025. arXiv:2502.05167.

-----

## Block E — Part 22 (AI Gateway & Cost Governance): token-cost grounding

**Target**: Part 22, “Budget governance” (v10-draft.md L492).
**Sits beside**: the existing budget-governance discussion.

**Proposed insertion**:

> The cost case for a chokepoint with hard budget bounds is grounded in measured agent economics. The Stanford Digital Economy Lab’s analysis of agentic coding found agentic tasks consuming on the order of 1000× the tokens of plain chat in a controlled setting, with up to 30× variance on identical runs, driven mainly by input (re-sent context) rather than output. The 1000× figure is the controlled-study extreme; the production multiplier is smaller — Anthropic reports multi-agent systems using roughly 15× chat tokens, and practitioner estimates cluster around 5–30× — so the gateway’s budget ceiling should be sized to the production range, with the controlled figure as the worst case it must survive.

**Caveat baked in**: 1000× explicitly framed as controlled-study extreme vs. 5–30× production; avoids citing the inflated number as typical.

**References**:

- Stanford Digital Economy Lab (2025). *How Do AI Agents Spend Your Money? Analyzing and Predicting Token Consumption in Agentic Coding Tasks.*
- Anthropic (2025). *How we built our multi-agent research system.* (engineering blog; ~15× chat-token figure.)

-----

## Block F — Proposer/verifier separation: primary-source backup

**Target**: wherever Part 3 or Part 10 argues that the producing agent and the checking gate must be independent.
**Sits beside**: the existing FIDES/CaMeL “non-deterministic planner gated by deterministic enforcer” framing (L159).

**Proposed insertion**:

> The principle that the artifact-producing step and the verifying step must not share authority has direct primary-source support beyond the IFC work cited above: Reflexion (Shinn et al., NeurIPS 2023, arXiv:2303.11366) separates Actor, Evaluator, and Self-Reflection roles, and CodeAct (Wang et al., ICML 2024, arXiv:2402.01030) grounds agent actions in executable code checked by the runtime rather than by the model’s own assertion. The *Code as Agent Harness* survey attributes the anti-pattern these avoid — an agent’s biased tests passing its own buggy code — to “circular reasoning” and “mode-collapse” (§4.1.1).

**Caveat baked in**: leans on peer-reviewed primaries (Reflexion, CodeAct) so the point does not rest on a preprint survey alone.

**References**:

- Shinn, N. et al. (2023). *Reflexion: Language Agents with Verbal Reinforcement Learning.* NeurIPS 2023. arXiv:2303.11366.
- Wang, X. et al. (2024). *Executable Code Actions Elicit Better LLM Agents.* (CodeAct) ICML 2024. arXiv:2402.01030.

-----

## [CORRECTION] C1 — Inverted Anthropic mixed-model claim

A claim circulating in external summaries states that a *lower*-capability orchestrator with *higher*-capability subagents wins (figures “0.42 vs 0.32 / 31%”). This is **inverted and unsupported**: the figures appear in no Anthropic source, and Anthropic’s actual finding is the opposite architecture — a *stronger* lead (Opus) directing *cheaper* subagents (Sonnet) outperformed single-agent Opus by 90.2% on their internal research eval. **Action**: do not cite the original anywhere. If the orchestrator point is wanted, use the corrected architecture, or cite “Can Small Agents Collaborate to Beat a Single Large Language Model?” (arXiv:2601.11327), which finds system performance is driven primarily by orchestrator capacity.

-----

## [CORRECTION] C2 — DeepMind scaling-paper specifics

The paper *Towards a Science of Scaling Agent Systems* (Kim et al., arXiv:2512.08296) is real, and its headline figure — independent agents amplifying errors 17.2× vs 4.4× under centralized coordination — is verbatim and citable. But external summaries garbled the setup: it used **180 configurations and four benchmarks** (Finance-Agent, BrowseComp-Plus, PlanCraft, Workbench), not “260 configurations / six benchmarks.” **Action**: cite the 17.2× figure freely; fix the config/benchmark counts wherever they appear.

-----

## [FIX] Experiment 03 model list — Opus 4.7 → 4.8

`docs/thesis-experiments.md`, Experiment 03, Axis A lists models as `claude-haiku-4-5, claude-sonnet-4-6, claude-opus-4-7`. Opus 4.8 (`claude-opus-4-8`) is now the current Opus release. **Action**: update `claude-opus-4-7` → `claude-opus-4-8` in the Axis A model list so the experiment, when run, swaps across current tiers.

-----

## Cross-reference note (for the editor merging this)

Blocks A, C, and F all touch the harness/verification argument; Block C is the load-bearing one and should be merged last, after A (which establishes the harness frame) and B (which establishes the formal loop), so the new subsection rests on grounding already in place. Block C’s honesty about Experiment 03’s “not yet run” status is required, not optional — removing it would convert a defensible prediction into an unsupported empirical claim.