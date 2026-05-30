# Consumer C — Obsidian Vault (manual verification)

Obsidian is a desktop app; there's no headless mode and no CI-friendly way to verify rendering automatically. This file documents the exact verification procedure to run on a machine with Obsidian installed.

## Verification procedure

1. Open Obsidian, create a new empty vault (`File → New vault`), or use an existing one with a `experiments/` folder.
2. Drop `experiments/04-consumer-swap/synthesis.md` directly into the vault folder via Finder/Explorer. **Do not modify the source file.**
3. Open the file in Obsidian.

## What to verify

### 1. YAML frontmatter parses

Obsidian's Properties pane (top of the editor when frontmatter is present) should show:

| Property | Value |
|---|---|
| `status` | `review` |
| `stage` | `02-analysis` |
| `operator_approved` | `false` |
| `risk_check_passed` | `false` |
| `risk_tier` | `Medium` |
| `domain` | `architecture` |
| `date` | `2026-05-27` |

If Obsidian shows the `---` markers in the body instead of a Properties pane, the frontmatter failed to parse — this would be a substrate-portability failure.

### 2. Headings render correctly

The five `## ` section headings render as h2:
- Core claim
- Evidence map
- Integrated findings
- Counter-argument
- Recommendations

The single `# ` heading at the top renders as h1: "Synthesis: PostgreSQL as Personal-Scale AI Substrate".

### 3. Tables render

Two tables (the Evidence map subclaim table and the Properties pane) should both render with column borders and aligned cells. Test that header rows are visually distinct.

### 4. Footnote-style emphasis

The italic note at the bottom ("Stage 02 synthesis artifact...") renders italic, not as raw `*` characters.

### 5. NO `[[wikilinks]]` are present

`synthesis.md` deliberately uses no Obsidian-specific syntax (no `[[wikilinks]]`, no `![[embeds]]`, no `%%comments%%`). The file is portable plain markdown. If Obsidian shows broken-link styling anywhere, something was added unintentionally.

### 6. Graph view works (optional)

Switch to Graph view (`Ctrl+G` / `Cmd+G`). The file appears as a single node with no connections. (No connections is the expected outcome — the file links to nothing else, and nothing links to it.)

## Verdict format

After verification, record the result in `results/obsidian-verification.md`:

```markdown
# Obsidian consumer verification

- Date: YYYY-MM-DD
- Obsidian version:
- Operator: <name>

Checklist:
- [ ] YAML frontmatter parsed (Properties pane shows all 7 fields correctly)
- [ ] All 5 ## section headings render as h2
- [ ] # heading at top renders as h1
- [ ] Both tables render with borders
- [ ] Italic note at bottom renders italic
- [ ] No broken wikilinks
- [ ] Graph view shows isolated node

Verdict: PASS / PARTIAL / FAIL

Notes: <any anomalies, version mismatches, plugin interactions, etc.>
```

## Why this consumer matters

Pandoc and an LLM are both "code that consumes markdown bytes." Obsidian is "a human-facing application built around a markdown-vault metaphor" — a fundamentally different consumer profile. If `synthesis.md` renders well in all three, the markdown-as-substrate claim is materially strengthened: the bytes survive both programmatic and human consumption paths without modification.

If Obsidian fails — e.g., the YAML doesn't parse because it uses unquoted strings Obsidian's lenient parser rejects, or Obsidian's Live Preview can't render the GitHub-style tables — that's a real signal worth investigating, not a portability failure of the thesis. Obsidian-compatibility is in scope for ADR-002's "Obsidian-compatible vault" framing.

## Plugins to avoid for this test

Disable plugins that auto-modify files (Templater, Auto Note Mover, periodic-notes, etc.) before dropping the file in. Otherwise the test is contaminated by sidecar mutations and can't distinguish substrate-portability from plugin behavior.
