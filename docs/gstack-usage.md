---
title: "gstack in the Markdown Architecture Workspace"
status: "draft"
date: "2026-05-27"
upstream: "https://github.com/garrytan/gstack"
companion: "https://github.com/garrytan/gbrain"
---

# gstack in the Markdown Architecture Workspace

gstack is an opinionated Claude Code toolkit by Garry Tan: 50+ slash-command skills that turn Claude Code into a virtual engineering team (CEO, eng manager, designer, reviewer, QA lead, CSO, release engineer). It is installed into `~/.claude/skills/gstack/` and registers as a Claude Code skill set; nothing in this workspace's tree is modified by the install.

This doc records **how gstack is used in this workspace** — not what gstack is. For the full reference, see the upstream repo.

---

## Install

Local machine (one-time, persistent):

```bash
git clone --single-branch --depth 1 https://github.com/garrytan/gstack.git ~/.claude/skills/gstack \
  && cd ~/.claude/skills/gstack && ./setup
```

Web sessions (Claude Code on the web) are ephemeral — gstack must be reinstalled when the container is recycled. A SessionStart hook can automate this; see `_config/` if one is added.

Prerequisites: `git`, `bun ≥ 1.0`, Claude Code. Playwright Chromium is downloaded by `./setup` for the `/browse` skill.

---

## How gstack maps onto ICM stages

| Stage | Useful gstack skills |
|---|---|
| `00-intake` | `/office-hours`, `/learn` |
| `01-research` | `/scrape`, `/browse`, `/investigate` |
| `02-analysis` | `/plan-ceo-review`, `/plan-design-review`, `/plan-eng-review`, `/plan-devex-review`, `/autoplan` |
| `03-output` | `/review`, `/qa`, `/cso`, `/health`, `/ship`, `/land-and-deploy`, `/canary`, `/document-generate`, `/document-release`, `/make-pdf` |

These are *advisory bindings*. gstack skills are general-purpose and may be invoked outside this mapping; the table exists so an operator scanning a stage knows which power tools are available without leaving the stage's `CONTEXT.md`.

---

## Interaction with workspace constraints

- **YAML frontmatter (`CLAUDE.md`):** gstack skills do not produce ICM stage artifacts directly. When a skill writes a markdown file that should live under `stages/`, the operator is responsible for adding the required frontmatter (`status`, `operator_approved`, `risk_check_passed`, `stage`) before promotion.
- **`operator_approved` gate:** gstack's `/ship` and `/land-and-deploy` skills must not promote artifacts to the next stage's `output/` directory unless `operator_approved: true` is set. This is enforced by `.claude/hooks/`, not by gstack.
- **Schema contracts:** `python _config/stage-contract.py --stage <id>` still gates promotion. gstack's `/review` and `/qa` are *complements* to, not replacements for, the StageContract validator.
- **Token budget on `CLAUDE.md`:** the workspace `CLAUDE.md` is ≤800 tokens. Do not inline gstack documentation there; link to this file instead.

---

## gbrain companion

gbrain (`github.com/garrytan/gbrain`) is gstack's persistent-memory companion: a local PGLite or remote Postgres knowledge brain that gstack skills read and write. Install:

```bash
bun install -g github:garrytan/gbrain
gbrain init --pglite      # personal, no server
gbrain doctor             # verify
```

In this workspace, gbrain is a candidate substrate for the `audit-logger` skill referenced in `CLAUDE.md` — it provides the append-only knowledge surface that `PromptExecutionReceipt` events can be written to. No commitment has been made; see ADRs for decisions of record.

`/setup-gbrain` (a gstack skill) walks through full install + MCP registration + per-repo trust policy when ready.

---

## Pointers

- Upstream README: `~/.claude/skills/gstack/README.md`
- gstack + gbrain integration guide: `~/.claude/skills/gstack/USING_GBRAIN_WITH_GSTACK.md`
- Skill catalog: `~/.claude/skills/gstack/llms.txt`
- Architecture: `~/.claude/skills/gstack/ARCHITECTURE.md`
