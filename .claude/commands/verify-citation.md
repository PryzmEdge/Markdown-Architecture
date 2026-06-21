---
description: Check a citation against the verified corpus in docs/v10-citations.md, tag provenance, and never vouch for a source from memory. Surfaces any [CORRECTION]/[FIX] attached to it.
argument-hint: <arXiv-id | author-year | title-substring>
allowed-tools: Read, Bash(grep:*), Bash(git show:*)
disable-model-invocation: true
---

You are checking whether a citation is safe to use in `docs/v10-draft.md`. The verified citation corpus is `docs/v10-citations.md`, and this command must keep that path: the per-source caveats and the [CORRECTION]/[FIX] flags live nowhere else, so repointing it elsewhere would silently drop them. That file — read fresh, right now — is the only authority for what has been verified. Your memory of a prior read is not. Re-ground against the file, not your priors.

## Corpus map (fresh read)

Block headers, correction/fix flags, and every arXiv ID currently in the corpus:

!`grep -nE "^## |\[CORRECTION\]|\[FIX\]|arXiv:" docs/v10-citations.md`

## The citation to check

$ARGUMENTS

## What to do

1. Locate `$ARGUMENTS` in the map above — match on arXiv ID, author, or title. Only what the grep returned counts; do not match from memory.
2. Resolve to exactly one of these and report it plainly:

   - **VERIFIED [TREE]** — the source sits in a normal block (A–F) with a full reference. Read that block in full and surface its **"Caveat baked in"** line verbatim. Cite it in the form the block gives, not a looser paraphrase.

   - **DO NOT CITE AS-IS [TREE]** — the source is under a `[CORRECTION]` or `[FIX]` heading. Quote the corpus's **Action:** line, state exactly what must change (inverted claim / wrong config or benchmark counts / stale model ID), and give the corrected form. The original form is forbidden.

   - **NOT IN CORPUS [UNVERIFIED]** — `$ARGUMENTS` does not appear. Say so directly. Do not vouch for it from memory and do not imply it is verified. It must be checked against its primary source before it can be cited; until then it carries no provenance in this repo.

3. Keep it to the verdict, the provenance tag, and the attached caveat/correction. Do not restate the rest of the corpus.

Direct answer first; caveats after.
