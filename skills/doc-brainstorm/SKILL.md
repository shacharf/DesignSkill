---
name: doc-brainstorm
description: Explore a system-design question, compare alternatives, and preserve decisions and unresolved ideas in a docagent discussion without confusing proposals with accepted design.
---

Read the selected module, saved discussion, and relevant constraints. Establish one concrete question. Ask for missing constraints only when they change the alternatives. Begin with a small number of understandable approaches; deepen them as the conversation demands. Use scenarios to test mechanisms, dependencies, failure behavior, and tradeoffs rather than presenting abstract feature lists.

Separate source statements, assumptions, proposed alternatives, selected decisions, and open questions. Do not mark a suggestion accepted merely because it was discussed. Honor decisions or delegated decision authority already given by the user; do not repeatedly ask approval. If choosing under delegated authority, record the assumption and reasoning.

Save the question, alternatives, supporting evidence, tradeoffs, and accepted/rejected/deferred outcomes in `discussions/`. Use `discussion create "Question" --module ID` and select it when needed. Follow doc-design's save protocol to update the bounded resume and checkpoint. Add remaining work to TODO.md, linking the module and recording motivation. Keep the discussion exploratory; doc-write incorporates chosen outcomes into the coherent design. An unresolved choice may appear in a design page if clearly labeled and necessary to understand it.
