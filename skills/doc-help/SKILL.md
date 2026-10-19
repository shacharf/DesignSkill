---
name: doc-help
description: Explain the docagent workflow, skills, direct commands, file locations, saving, TODO tracking, and recovery; use for design-workflow help rather than document synthesis.
---

Use `docagent help` for an immediate workflow and command reference; it works outside a project and does not invoke a model. Use `docagent COMMAND --help` for exact arguments. Read `DOC_WORKFLOW.md` for examples and recovery. Answer the user's particular question briefly; inspect project state only when needed for a project-specific answer.

Explain the division: skills understand and write; docagent performs deterministic local bookkeeping; Markdown remains authoritative. Typical flow: doc-sources understands inputs, doc-design shapes the main story and selects a module, doc-brainstorm resolves questions, doc-write builds the explanation, and doc-review checks it. This is a flexible workflow, not a mandatory pipeline.

Files: `design.md` is the reader entry point; `modules/` holds the hierarchy; `sources/` holds original references and extraction notes; `discussions/` holds reasoning; `TODO.md` holds pending/active/done work; `WORK.md` holds the brief and active pointers. `.docagent/` contains generated configuration, journals, installation records, and search state.

Direct commands do not summarize conversation. Skill-assisted switching saves first; direct module selection only changes focus and clears a discussion belonging to a different module. TODO start retains the task and opens/resumes a discussion. TODO done archives it in a collapsed section. Saved Markdown can be current while search is pending. `index status` diagnoses freshness; `index flush` retries explicitly. Never imply a checkpoint recovered conversation-only material or that URL registration downloaded a source.
