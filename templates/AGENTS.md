# Design collaboration

Use `docagent status` to resume saved focus. Markdown is authoritative. `design.md` explains the main ideas; modules form a hierarchy of progressively deeper explanations. Each module should make sense independently with minimal context. Aim for three to five peer concepts; keep exhaustive detail at the leaves without losing constraints.

Use doc-design to guide/save/resume, doc-sources to extract inputs, doc-brainstorm to explore choices, doc-write to explain the design, doc-review to assess it, and doc-help for guidance. Direct CLI commands perform bookkeeping without inference. Source notes, working discussions, and reader-facing design pages have distinct purposes. Clearly distinguish source statements, assumptions, proposals, and accepted decisions.

Maintain pending/active/done work in TODO.md. Preserve motivations and user ordering. Save reasoning and bounded resumes at meaningful checkpoints and before switching or ending. Run `docagent checkpoint` after manual changes. A direct selection cannot summarize unsaved conversation. Search is project-scoped and may lag saved files; use `index status` and `index flush` for recovery. Do not overwrite source originals, manual edits, or silently migrate research projects. Do not run automatic Git operations. See DOC_WORKFLOW.md for commands and recovery.
