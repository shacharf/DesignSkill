---
name: doc-review
description: Review hierarchical system-design documents for readability, progressive explanation, standalone module context, ambiguities, missing behavior, and consistency with sources and decisions.
---

Use this review after substantial drafting or revision, focusing on the changed pages and affected connections; at major milestones, also review cross-module consistency. Small wording changes do not require a full pass.

Read [the reading contract](references/reading-contract.md). Review the main story or requested module as a first-time reader, then trace its deeper pages and relevant source/decision records. Run `docagent validate` for structural diagnostics, but do not equate a successful check with a clear or correct design.

Check whether purpose precedes mechanism, new concepts build on earlier explanations, and each module makes sense when entered directly. Flag excessive peer concepts, premature implementation detail, unexplained terms, artificial grouping, and summaries that merely list links. At the leaves, check that simplification has not lost important constraints or failure behavior.

Check for ambiguity: identify wording that admits materially different interpretations, and state those interpretations. Walk through relevant scenarios to find behavior that is missing, including failure and recovery when applicable. Check whether module responsibilities, inputs and outputs, and assumptions agree across boundaries. Identify unsettled choices presented as decisions. Distinguish a deliberate link to deeper detail from a genuine omission; do not demand leaf-level specifications in an overview.

Review source notes, discussions, TODOs, and working summaries for readability when they are in scope. Essential context, motivations, and decision status must be visible without inspecting hidden metadata. Bullets, prose, tables, and figures are all valid; assess whether they help the reader. Check that figures agree with the explanation and do not introduce unexplained concepts.

Compare parent summaries, child responsibilities, and neighboring interfaces. Distinguish contradictions, missing decisions, unsupported assertions, and stylistic improvements. Ground findings in specific passages or missing scenarios, explain their impact, and formulate a concrete clarification question or correction. Never fill a gap with an invented design decision. Lead with a few high-impact findings; keep the complete actionable backlog in TODO.md when requested or part of ongoing design work. Do not silently accept proposals or change architecture during a review. During an authorized drafting/revision task, fix clear editorial issues within scope, then recheck affected findings. Otherwise report proposed corrections. Record unresolved design questions in TODO.md when part of ongoing work. Do not recursively restart a full review after each correction; checkpoint once the scoped work is saved.
