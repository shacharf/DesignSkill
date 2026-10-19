# Reading contract

Every document we author is human-readable first, including design pages, source summaries, brainstorming records, decisions, TODOs, working summaries, and help. State its purpose, provide the context needed to understand it, use plain language, and introduce ideas progressively. Keep essential meaning visible in the document body; metadata supports tools and must not be the only place a reader can find a task’s motivation, a decision’s status, or necessary context. Preserve original input files unchanged; machine runtime files are separate from authored documents.

Choose the format that makes the idea easiest to understand. Use concise, complete bullets for distinct ideas, short prose for explanations that need continuity, and tables for comparisons. Add a figure, diagram, or example when it clarifies structure, relationships, sequence, or behavior. Give figures clear labels and a short explanation of what the reader should notice; keep them at the page’s level of detail. Avoid dense paragraphs, fragmented bullet inventories, and decorative figures.

The design is for humans understanding a complex system. `design.md` explains its main ideas as a coherent story. Every module and submodule repeats the same progression at its own scale: purpose, core idea, essential context and interactions, a few parts, then links to deeper detail. This is an explanatory contract, not a compulsory set of five headings.

Aim for three to five peer concepts at a time. Introduce ideas gradually, with the minimum context needed at that level. More than five children is a review signal, not a hard structural limit. Regroup only when the grouping has meaning; never hide a constraint or invent modules solely to satisfy a count.

A reader opening a module directly should understand what it does, why it exists, what it receives or produces, and how it relates to its surroundings. Repeat minimal context deliberately; link to a canonical explanation for deeper shared concepts. Dependency links may cross the hierarchy; they do not create additional parents.

Upper levels explain mechanisms and responsibilities. Leaf pages carry exact interfaces, algorithms, configurations, edge cases, and other necessary implementation detail. Depth is driven by comprehension, not a fixed number of levels. A short module can be a leaf. Keep detailed specifications complete, using meaningful sections and tables when appropriate.

Design pages express the current design, including clearly marked unresolved choices. Original sources, competing alternatives, and historical rationale belong in source notes and discussions. Source content is evidence of what was written, not proof it was adopted. Never promote a proposal into a decision implicitly.

A main ideas page must tell the story even if the reader follows no links. A page containing only child links does not satisfy the contract.
