---
name: doc-help
description: Explain the docagent workflow, skills, direct commands, file locations, saving, TODO tracking, and recovery; use for design-workflow help rather than document synthesis.
---

Every document we author is human-readable first, including design pages, source summaries, brainstorming records, decisions, TODOs, working summaries, and help. State its purpose, provide the context needed to understand it, use plain language, and introduce ideas progressively. Keep essential meaning visible in the document body; metadata supports tools and must not be the only place a reader can find a task’s motivation, a decision’s status, or necessary context. Preserve original input files unchanged; machine runtime files are separate from authored documents.

Choose the format that makes the idea easiest to understand. Use concise, complete bullets for distinct ideas, short prose for explanations that need continuity, and tables for comparisons. Add a figure, diagram, or example when it clarifies structure, relationships, sequence, or behavior. Give figures clear labels and a short explanation of what the reader should notice; keep them at the page’s level of detail. Avoid dense paragraphs, fragmented bullet inventories, and decorative figures.

Use `docagent help` for an immediate workflow and command reference; it works outside a project and does not invoke a model. Use `docagent COMMAND --help` for exact arguments. Read `DOC_WORKFLOW.md` for examples and recovery. Answer the user's particular question briefly; inspect project state only when needed for a project-specific answer.

Explain the division: skills understand and write; docagent performs deterministic local bookkeeping; Markdown remains authoritative. Typical flow: doc-sources understands inputs, doc-design shapes the main story and selects a module, doc-brainstorm resolves questions, doc-write builds the explanation, and doc-review checks it. This is a flexible workflow, not a mandatory pipeline.

Files: `design.md` is the reader entry point; `modules/` holds the hierarchy; `sources/` holds original references and extraction notes; `discussions/` holds reasoning; `TODO.md` holds pending/active/done work; `WORK.md` holds the brief and active pointers. `.docagent/` contains generated configuration, journals, installation records, and search state.

Direct commands do not summarize conversation. Skill-assisted switching saves first; direct module selection only changes focus and clears a discussion belonging to a different module. TODO start retains the task and opens/resumes a discussion. TODO done archives it in a collapsed section. Saved Markdown can be current while search is pending. `index status` diagnoses freshness; `index flush` retries explicitly. Never imply a checkpoint recovered conversation-only material or that URL registration downloaded a source.
