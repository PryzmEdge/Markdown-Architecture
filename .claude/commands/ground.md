---
description: Re-read the relevant artifact at HEAD and answer a claim or question with provenance tags. Forbids answering from memory — a recollection of a prior read is not a read.
argument-hint: <claim-or-question about the repo's current state>
allowed-tools: Read, Grep, Glob, Bash(git rev-parse:*), Bash(git log:*), Bash(git status:*), Bash(git show:*)
disable-model-invocation: true
---

You are grounding a claim about the repo's current state before answering it. The rule: "present" is not "correct," and a memory of a prior read is not a fresh read. Open the artifact this turn and answer from what you read — not from your priors.

## Where HEAD is right now

!`git log -1 --format='HEAD %h — %s'`
!`git status --short`

## The claim or question

$ARGUMENTS

## Hard rule

You are forbidden from answering this from memory. If you have not opened the relevant artifact **this turn**, you do not know it — say so and go read it. A recollection of how a file looked is not a read of how it looks now. Locate the file (Grep/Glob), read it (Read), then answer.

## What to do

1. Identify which artifact(s) in the tree bear on `$ARGUMENTS`. Find them — do not assume their path or contents from memory.
2. Read the deciding section fresh. If the claim itself contains an artifact citation (e.g. "file X, block Y, says Z"), re-resolve the pointer: confirm location X actually says Z. Re-ground the citation, not just the proposition.
3. Return one verdict with its evidence:

   - **CONFIRMED [TREE]** — the tree supports it. Give file:line and the deciding span (quote it, kept short).
   - **CONTRADICTED [TREE]** — the tree says otherwise. Give file:line and what it actually says.
   - **PARTIAL [TREE]** — true in part. Separate the supported part from the unsupported.
   - **NOT FOUND [UNGROUNDED]** — no artifact in the tree speaks to it. Say so plainly. Do not fill the gap from memory or inference.

4. State the provenance tag and that this was read fresh this turn. If the working tree differs from HEAD for the file you read, say which one you grounded against.

Direct answer first; caveats after. Minimal — no restating the input back.
