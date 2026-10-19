---
name: doc-review
description: Review hierarchical system-design documents for readability, progressive explanation, standalone module context, completeness, and consistency with sources and decisions.
---

Read [the reading contract](references/reading-contract.md). Review the main story or requested module as a first-time reader, then trace its deeper pages and relevant source/decision records. Run `docagent validate` for structural diagnostics, but do not equate a successful check with a clear or correct design.

Check whether purpose precedes mechanism, new concepts build on earlier explanations, and each module makes sense when entered directly. Flag excessive peer concepts, premature implementation detail, unexplained terms, artificial grouping, and summaries that merely list links. At the leaves, check that simplification has not lost important constraints or failure behavior.

Compare parent summaries, child responsibilities, and neighboring interfaces. Distinguish contradictions, missing decisions, unsupported assertions, and stylistic improvements. Ground findings in specific passages and explain their reader impact. Lead with a few high-impact findings; keep the complete actionable backlog in TODO.md when requested or part of ongoing design work. Do not silently accept proposals or change architecture during a review. If asked to fix issues, revise within scope using doc-write and checkpoint the result.
