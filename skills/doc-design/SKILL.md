---
name: doc-design
description: Organize rough system documents into a hierarchical design; guide module-focused work, maintain TODOs, and save or resume design discussions in a docagent project.
---

Run `docagent status --json` once to recover the saved working brief, selected module, and discussion resume. Read named excerpts deliberately. Start with the user's goal and sources; help shape `design.md` before elaborating individual modules. Use [the reading contract](references/reading-contract.md) when shaping or changing the hierarchy.

## Focus and navigation
Use `docagent tree` to understand the hierarchy and `module show ID` for a known module. Create modules with `module create "Title" --parent ID`; select with `module select ID`. Keep one immediate design question in focus. Save conversation-only reasoning before switching. Direct selection changes pointers only and cannot summarize chat. Starting a new project does not require an invented discussion if there is nothing yet to preserve.

Use doc-sources for extracting inputs, doc-brainstorm for alternatives, doc-write for design prose, doc-review for readability and consistency, and doc-help for guidance. Do not force all skills through every small task. Ask only questions whose answers materially affect the design; continue independent work where possible.

## Work tracking
`TODO.md` is the authoritative backlog. Add concrete questions or tasks with `docagent todo "Task" --why "Motivation" --module ID`. Preserve user ordering; do not silently reprioritize. Starting with `todo --start ID` retains the item, marks it active, and opens or resumes its discussion. `todo --done ID` preserves it in Done; use only when the outcome and required design edits are saved. Other skills may add unresolved work. Show a few current items, not the entire backlog, unless asked. Use `--all` for completed items. Explain source origins in the motivation or linked discussion when relevant.

## Save and resume
At meaningful conclusions and before switching or ending, save accepted, rejected, deferred, and uncertain ideas with reasons in the current `discussions/` record. Create one using `discussion create "Question" --module ID` and select it if needed. Keep working history out of the reader-facing design. Preserve examples, constraints, source locations, and changed understanding; do not append repetitive transcripts.

Update the managed resume block: Question, Current understanding, Immediate focus, Next step, Supporting material. Maximum 5000 characters. Update the managed working brief in `WORK.md` when shared goals or constraints change; maximum 3000 characters. These operational bounds do not constrain leaf specifications. Keep the active module/discussion pointers consistent. Run `docagent checkpoint`; correct relevant failures, then report the saved focus and next step. Mention pending or failed indexing without treating it as lost Markdown. Do not report an unsaved conversation as checkpointed.

Markdown is authoritative. Search unknown locations with `docagent search "phrase"`, optionally `--hybrid`; read exact passages before relying on them. Search may lag edits, and a miss is not proof of absence. Use `index status` and explicit `index flush` for recovery. Do not use answer-generation search, unrelated collections, or automatic Git operations.
