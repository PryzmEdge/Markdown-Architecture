# Contributing to Markdown Architecture

Thank you for contributing. This document defines the rules for proposing changes, submitting ADRs, and getting work merged.

---

## Core Rules

1. **No agent merges.** Agents may open pull requests and push branches, but only a named human operator may merge into `main`.
2. **No direct pushes to `main`.** All changes go through a pull request.
3. **Every PR must pass `stage-contract.py`.** The CI workflow runs `make validate` automatically; a failing check blocks merge.
4. **Operator sign-off is mandatory.** No PR is merged without explicit approval from the operator.
5. **Append-only ADRs.** Once an ADR is merged, its content is frozen. Supersede it with a new ADR.
6. **Linear versioning for position papers.** `v9.md` → `v10.md`; archive old versions in `docs/`.

---

## Proposing an Architecture Decision Record (ADR)

1. Open a GitHub issue describing the decision needed and context.
2. Create a branch: `adr/NNN-short-description`.
3. Write `docs/adr/ADR-NNN-<slug>.md` using this template:

```markdown
---
status: proposed
date: YYYY-MM-DD
deciders: [operator-name]
---

# ADR-NNN: Title

## Context
...

## Decision
...

## Consequences
...
```

4. Open a pull request. Operator reviews and approves.
5. On merge, update `status: accepted` and add the ADR to `docs/adr/ADR-000-index.md`.
6. To supersede: set `status: superseded`, add `superseded_by: ADR-NNN`, and write the replacement ADR.

---

## Pull Request Conventions

- **Branch naming**: `feat/<slug>`, `fix/<slug>`, `chore/<slug>`, `adr/<NNN>-<slug>`, `docs/<slug>`
- **Commit messages**: `<type>: <short description>` (e.g. `config: add stage-contract validation for 02-analysis`)
- **PR description**: include the stage affected, what changed, and whether operator approval has been given
- **Draft PRs**: use for work in progress; convert to ready when CI passes

---

## Stage Artifact Conventions

- Every `.md` file in a stage `output/` directory **must** have valid YAML frontmatter.
- `operator_approved: true` may only be set by a named human operator, never by an agent.
- `risk_check_passed: true` is required for any artifact with `risk_tier: High`, `High/Critical`, or `Critical`.
- Never delete or suppress `contradictions.md`, even if it is empty.

---

## Local Setup

```bash
git clone https://github.com/PryzmEdge/Markdown-Architecture.git
cd Markdown-Architecture
pip install pyyaml pytest                       # stage-contract + tests
pip install -r proof/requirements.txt           # Stage 1 buildability proof
make validate                                   # confirm all stage contracts pass
python -m pytest                                # run the full test suite
```

To run the Stage 1 buildability proof end-to-end (Docker Postgres + receipt round-trip), see [`proof/tutorial.md`](proof/tutorial.md).

---

## Questions

Open a GitHub issue with the label `question`.
