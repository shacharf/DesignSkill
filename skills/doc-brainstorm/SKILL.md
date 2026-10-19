---
name: doc-brainstorm
description: Explore a system-design question, compare alternatives, and preserve decisions and unresolved ideas in a docagent discussion without confusing proposals with accepted design.
---

Every document we author is human-readable first, including design pages, source summaries, brainstorming records, decisions, TODOs, working summaries, and help. State its purpose, provide the context needed to understand it, use plain language, and introduce ideas progressively. Keep essential meaning visible in the document body; metadata supports tools and must not be the only place a reader can find a task’s motivation, a decision’s status, or necessary context. Preserve original input files unchanged; machine runtime files are separate from authored documents.

Choose the format that makes the idea easiest to understand. Use concise, complete bullets for distinct ideas, short prose for explanations that need continuity, and tables for comparisons. Add a figure, diagram, or example when it clarifies structure, relationships, sequence, or behavior. Give figures clear labels and a short explanation of what the reader should notice; keep them at the page’s level of detail. Avoid dense paragraphs, fragmented bullet inventories, and decorative figures.

Read the selected module, saved discussion, and relevant constraints. Establish one concrete question. Ask for missing constraints only when they change the alternatives. Begin with a small number of understandable approaches; deepen them as the conversation demands. Use scenarios to test mechanisms, dependencies, failure behavior, and tradeoffs rather than presenting abstract feature lists.

Separate source statements, assumptions, proposed alternatives, selected decisions, and open questions. Do not mark a suggestion accepted merely because it was discussed. Honor decisions or delegated decision authority already given by the user; do not repeatedly ask approval. If choosing under delegated authority, record the assumption and reasoning.

Save the question, alternatives, supporting evidence, tradeoffs, and accepted/rejected/deferred outcomes in `discussions/`. Use `discussion create "Question" --module ID` and select it when needed. Follow doc-design's save protocol to update the bounded resume and checkpoint. Add remaining work to TODO.md, linking the module and recording motivation. Keep the discussion exploratory; doc-write incorporates chosen outcomes into the coherent design. An unresolved choice may appear in a design page if clearly labeled and necessary to understand it.
