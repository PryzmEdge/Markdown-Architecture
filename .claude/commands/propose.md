---
description: Draft a single-file, propose-first change. Produces the target file, the exact diff, rationale with provenance tags, and the commit's session trailer — then stops without writing or committing. Lane B discipline.
argument-hint: <change description>
allowed-tools: Read, Grep, Glob, Bash(git status:*), Bash(git diff:*), Bash(git log:*), Bash(git branch:*)
disable-model-invocation: true
---

You are drafting a change under Lane B / propose-first. You do **not** apply it. You produce a proposal; the operator reviews, then commits separately. The commit decision is a separate decision from this one.

## Where HEAD is right now

!`git branch --show-current`
!`git status --short`

## The change requested

$ARGUMENTS

## Rules — do not relax these

- **One file.** Scope the proposal to a single file. If it genuinely needs more than one, stop and say so — name the files, recommend a split, and propose only the first (or ask which to start with). Do not bundle.
- **Read at HEAD before proposing.** Read the target file fresh. Do not propose against your memory of how it looked. Tag the current contents you relied on as [TREE].
- **Never weaken a test to make something pass.** A green suite is not the goal; correct behaviour is. If the change touches a test, flag it and explain why the test still earns its keep. If passing would require loosening an assertion, refuse and say what the failure is actually telling you.
- **Provenance on claims.** Tag every factual assertion: [TREE] (read from the working tree), [DOC] (project knowledge), [UPLOAD] (pasted this session). "Present" is not "correct."
- **Withhold execution.** Output the proposal and stop. Do not call Edit or Write. Do not commit. End by asking for approval.

## Output format

1. **Target file** — the one path this touches, and why it's the right (and only) one.
2. **Diff** — the exact change as a fenced diff, ready to apply verbatim.
3. **Rationale** — one short paragraph: what it does, what it deliberately leaves out.
4. **Risk / test note** — anything touching execution, schema, risk, or tests; or "none."
5. **Session trailer** — Append the Claude session URL as the commit trailer: https://claude.ai/code/<current-session-id>
6. **Approval gate** — end with exactly: "Proposed, not applied. Approve to land, or tell me what to change."

Direct answer first; caveats after. Minimal context — do not restate the request back.
