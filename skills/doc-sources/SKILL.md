---
name: doc-sources
description: Read brainstorming notes, design drafts, and system overviews; extract traceable ideas, constraints, conflicts, and open questions into docagent source notes.
---

Every document we author is human-readable first, including design pages, source summaries, brainstorming records, decisions, TODOs, working summaries, and help. State its purpose, provide the context needed to understand it, use plain language, and introduce ideas progressively. Keep essential meaning visible in the document body; metadata supports tools and must not be the only place a reader can find a task’s motivation, a decision’s status, or necessary context. Preserve original input files unchanged; machine runtime files are separate from authored documents.

Choose the format that makes the idea easiest to understand. Use concise, complete bullets for distinct ideas, short prose for explanations that need continuity, and tables for comparisons. Add a figure, diagram, or example when it clarifies structure, relationships, sequence, or behavior. Give figures clear labels and a short explanation of what the reader should notice; keep them at the page’s level of detail. Avoid dense paragraphs, fragmented bullet inventories, and decorative figures.

Register each input with `docagent source add "FILE_OR_URL"`, then use its returned ID and path. Local originals are copied byte-for-byte into `sources/files/`; never rewrite them. URL registration records a reference, not fetched content. Register related files individually. Use an available format-specific reader for PDF or office documents; if one is unavailable, report the unreadable portion rather than claiming extraction succeeded.

Read enough of the actual source to establish context. In its source note, organize ideas and constraints, contradictions and questions, and exact source locations. Preserve distinctions between what the author states, your interpretation, and a new proposal. Link extracted claims to headings, pages, or lines. Identify conflicting versions and unresolved terminology without silently choosing a winner. A source proposal is not automatically an accepted design decision.

Present a compact synthesis of roughly three to five main concepts, not an exhaustive inventory. Keep detailed extraction in the source note. Relate findings to existing modules and identify gaps for doc-design. Add actionable unresolved work to `TODO.md` through `docagent todo`; include motivation and source ID. Avoid duplicating existing tasks. When using retrieval, verify the original passages rather than treating snippets as sufficient evidence. Checkpoint saved notes; drafting design pages belongs to doc-write when requested as part of the task.
