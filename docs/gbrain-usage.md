---
title: "gbrain in the Markdown Architecture Workspace"
status: "draft"
date: "2026-05-27"
upstream: "https://github.com/garrytan/gbrain"
companion: "https://github.com/garrytan/gstack"
---

# gbrain in the Markdown Architecture Workspace

gbrain is a persistent knowledge base for AI coding agents: a local PGLite or remote Postgres database, exposed via the `gbrain` CLI and an MCP server. Pages are markdown; search is keyword + semantic (RRF + query expansion); ingest is from markdown directories, git repos, or other gbrain "sources" via federation.

This doc records **how gbrain is intended to be used in this workspace**. The actual `/setup-gbrain` ceremony is local-Mac only — it modifies `~/.gbrain/`, `~/.claude.json`, and `~/.gstack/`, none of which persist in Claude Code on the web. Run the skill on your own machine.

---

## Install

Local machine (one-time, persistent):

```bash
bun install -g github:garrytan/gbrain
gbrain init --pglite      # Path 3: zero accounts, ~30 seconds, this Mac only
gbrain doctor             # verify; expects status=ok or warnings
```

Prerequisites: `bun ≥ 1.0`. For Path 2 (Supabase) you also need a Supabase account and either an existing pooler URL or a Personal Access Token.

For the full ceremony — engine choice, MCP registration with Claude Code, per-repo trust policy, gstack-artifacts sync, transcript ingest — run the gstack skill:

```bash
/setup-gbrain
```

It detects current state, asks at most three questions, and is idempotent: re-run it any time gbrain feels off.

---

## The four engine paths

| Path | When | Trade |
|---|---|---|
| **1 — Supabase, existing URL** | Cloud agent already provisioned a brain; you want your local Mac to share it | Paste Session Pooler URL (`Settings → Database → Connection Pooler → Session`). Grants local agent full r/w on every page the cloud agent can see. |
| **2a — Supabase, auto-provision** | Fresh Supabase account, want zero clicking | Paste a Supabase PAT. Skill creates a project, polls until healthy, fetches pooler URL. ~90 seconds. PAT grants account-wide access; revoke after setup. |
| **2b — Supabase, manual** | Prefer the web UI to a PAT | Click through supabase.com yourself; paste the URL back. |
| **3 — PGLite local** | Try-first / private to this Mac | No accounts, no cloud, no sharing. ~30 seconds. Brain at `~/.gbrain/brain.pglite`. |
| **4 — Remote gbrain MCP** | Brain runs on another machine (Tailscale, internal LAN, teammate's server) | Paste MCP URL + bearer token; no local DB or install. |

In this workspace, **Path 3 (PGLite local)** is the recommended default for solo work — it has no dependencies and matches the workspace's "personal-scale focus" (see `docs/v10-draft.md`). Promote to Path 1 or 2 when collaboration starts.

---

## Interaction with workspace constraints

- **Audit-logger substrate.** `CLAUDE.md` lists `audit-logger` as a workspace skill that writes `PromptExecutionReceipt` to an append-only log. gbrain is a candidate substrate: `gbrain put <slug>` appends a markdown page; the page is searchable; `~/.gbrain/audit/` already exists in this container. **No commitment has been made** — an ADR is needed before wiring it in.
- **Per-repo trust policy.** `/setup-gbrain` asks how this repo's `origin` remote should interact with gbrain. The four tiers are `read-write` (search + write new pages), `read-only`, `deny`, or `skip-for-now`. For a research workspace publishing intermediate artifacts, **`read-write`** is the natural choice. Stored at `~/.gbrain/repo-policy.json`.
- **Artifacts sync.** If you opt into gstack-artifacts sync (Step 7 of the skill), gstack pushes `~/.gstack/` (CEO plans, designs, retros — none of which this workspace currently produces) to a private repo named `gstack-artifacts-$USER`. gbrain federates from that repo. **Skip for now** unless you start generating gstack artifacts.
- **CLAUDE.md token budget.** The skill's Step 8 writes a `## GBrain Configuration` block (~80-100 tokens) into `CLAUDE.md`. With current `CLAUDE.md` at ~670 tokens, that's within budget. If you grow `CLAUDE.md` further, prune before promoting Path 3 → Path 1/2 since the Configuration block grows with mode.

---

## Useful commands

```bash
# Pages
gbrain put <slug> [< file.md]        # write/update; reads stdin or argv
gbrain get <slug>                    # read
gbrain list [--type T] [--tag T]     # filter

# Search
gbrain search "<terms>"              # tsvector keyword
gbrain query "<question>"            # hybrid (RRF + query expansion)
gbrain ask "<question>"              # alias for query

# Code (when a gbrain code source is registered for this repo)
gbrain code-def <symbol>
gbrain code-refs <symbol>
gbrain code-callers <symbol>
gbrain code-callees <symbol>

# Ingest
gbrain import <dir> [--no-embed]     # markdown directory → pages
gbrain sync --watch                  # continuous git → brain
gbrain export --dir ./out/           # brain → markdown

# Sources (federation)
gbrain sources list
gbrain sources add --path <dir> --federated

# MCP server
gbrain serve                         # stdio MCP (for Claude Code, Cursor)
gbrain serve --http                  # HTTP MCP with OAuth + dashboard

# Health
gbrain doctor [--fast] [--json]
```

---

## Relation to graphify

Both tools index repo content for agent retrieval, but with different strengths:

| Concern | graphify | gbrain |
|---|---|---|
| Substrate | NetworkX graph in `graphify-out/graph.json` | Postgres / PGLite pages |
| Extraction | AST (tree-sitter, no API key) or semantic (LLM, key required) | Embedding-based (Voyage / OpenAI / etc.) |
| Best at | "What calls X?", "What does Y depend on?", community/architecture views | "What did we decide about X?", semantic page lookup, cross-machine memory |
| Persistence | Rebuilds from source; `graphify-out/` is gitignored | Long-lived database; backups via `gbrain export` |
| MCP server | No (CLI-only, despite older skill assumptions) | Yes (`gbrain serve`) |

They are complementary. The PreToolUse hook installed by `graphify claude install` nudges toward `graphify query` for grep-style code questions; gbrain handles semantic and memory queries. See `docs/graphify-usage.md` for graphify specifics.

---

## Pointers

- Upstream README: https://github.com/garrytan/gbrain/blob/master/README.md
- Companion guide: `~/.claude/skills/gstack/USING_GBRAIN_WITH_GSTACK.md`
- Setup skill source: `~/.claude/skills/gstack/setup-gbrain/SKILL.md`
- Workspace companion docs: `docs/gstack-usage.md`, `docs/graphify-usage.md`
