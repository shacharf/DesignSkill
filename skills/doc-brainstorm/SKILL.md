---
name: doc-brainstorm
description: Prepare a progressive brainstorming agenda or discuss one saved topic; capture ideas, plan only current subtopics, and preserve decisions and follow-up work for fresh sessions.
---

Every document we author is human-readable first, including design pages, source summaries, brainstorming records, decisions, TODOs, working summaries, and help. State its purpose, provide the context needed to understand it, use plain language, and introduce ideas progressively. Keep essential meaning visible in the document body; metadata supports tools and must not be the only place a reader can find a task’s motivation, a decision’s status, or necessary context. Preserve original input files unchanged; machine runtime files are separate from authored documents.

Choose the format that makes the idea easiest to understand. Use concise, complete bullets for distinct ideas, short prose for explanations that need continuity, and tables for comparisons. Add a figure, diagram, or example when it clarifies structure, relationships, sequence, or behavior. Give figures clear labels and a short explanation of what the reader should notice; keep them at the page’s level of detail. Avoid dense paragraphs, fragmented bullet inventories, and decorative figures.

## Choose the working mode

Use **prepare the agenda** when the user asks to organize ideas, generate topics, plan the next topic, or replan after a discovery. Use **work through a topic** when continuing a saved question or comparing approaches. A small standalone question can be discussed directly; an agenda is not mandatory for every conversation.

Start with `docagent status`, then read the cumulative planning summary in WORK.md and the relevant module and source passages. For an agenda item, use `docagent todo --show ID` to read its full brief and linked parent discussion; the compact resume alone is not the assignment.

## Prepare the agenda

Use stronger reasoning for agenda synthesis, dependencies, conflicting evidence, and planning the current topic. If the current model is unsuitable or a fresh context would help, save progress and recommend a model/effort change with a brief reason. The user selects the model in the host; neither this skill nor docagent can switch the active chat or clear its history.

1. Preserve the brainstorm in a discussion record. Separate source statements, assumptions, proposals, selected decisions, and open questions. An idea being mentioned does not make it accepted.
2. Build the necessary top-level topics with `docagent todo "Topic" --why "Purpose and known dependencies" --module ID`. Inspect existing TODOs first; update or reuse them rather than creating duplicates. There is no limit on agenda or task count. The design's three-to-five-concepts guideline does not limit the work backlog. Propose ordering when planning is requested, preserve explicit user priorities, and explain meaningful changes.
3. Leave future topics as titles, purposes, and known dependencies. Do not generate their subtopics, detailed briefs, or placeholder discussions. Start only the current topic with `docagent todo --start ID`.
4. Read the current design, WORK.md, and relevant prior outcomes before expanding it. Add its necessary subtopics with `docagent todo "Question" --parent TOPIC_ID --why "Why it matters" --model "Recommended model / effort — reason"`. The command creates a linked discussion skeleton for each current subtopic; fill its Topic brief and Compact resume before handing it off.
5. Each brief explains the question and purpose; starting decisions, assumptions, and unknowns; key constraints, tradeoffs, and scenarios; exact source and module links and dependencies; and the expected outcome plus model/effort recommendation. Phrase watch points neutrally, without prescribing a preferred answer. Keep the brief useful to a reader entering directly.

Only two planning levels are supported. If a subtopic is too broad, split it into focused siblings or propose a new top-level topic. Do not expand future topics merely to record a follow-up. New information can invalidate the current plan at any time: revise it promptly, keep useful reasoning, and retire superseded work with an explanation rather than deleting it silently.

## Work through a topic

Use `docagent todo --next` to find the current topic's next subtopic or a planning/closure action; it does not automatically advance to the next parent. Start an explicit item using `docagent todo --start ID`, then read `docagent todo --show ID`, the parent discussion, and relevant sources. Verify that the brief is prepared and its assumptions are still current before beginning. A cheaper model can be the main agent in this fresh chat; worker restrictions from a separate delegation do not apply to a new main session.

Keep one concrete question in focus. Ask for missing constraints only when they affect the alternatives. Develop a few understandable approaches using concrete scenarios, dependencies, and failure/recovery behavior. Honor decisions and delegated authority already given by the user. Record assumptions and reasons; never convert a suggestion into a decision implicitly. Flag significant architectural uncertainty, conflicting evidence, or stale assumptions for stronger reasoning rather than forcing a conclusion.

When the next item would benefit from a different model or fresh context, provide a short handoff: task ID, recommended model/effort and reason, and a ready-to-use prompt such as “Continue topic t003 using doc-brainstorm and its saved brief.” Avoid repeated switch suggestions when the current model is suitable. Fresh chats read saved files rather than requiring the original transcript. Do not claim the switch or chat creation happened automatically.

## Outcomes, follow-ups, and handoff

At meaningful stopping points, save reasoning, alternatives, and evidence locations in the discussion and update its managed Compact resume. Use doc-write for agreed design changes and doc-review for substantial changes and affected connections. Do not repeat a full review after each small edit.

Before completing an item, revisit both its original questions and newly discovered issues. Write the meaningful result and its rationale, changes to design or assumptions, open/deferred questions, and consequences for later work in the discussion's managed Outcome and handoff block. A nonempty block is only a structural check; the agent must judge whether the result and next-step context are adequate.

For each unresolved old or new question, reuse/update an existing open TODO or create one with a visible motivation and relevant module. Use `--follow-up-for OLD_ID` when creating a task, or `docagent todo --link EXISTING_ID --follow-up-for OLD_ID` to reuse an open task and preserve lineage. Place a follow-up under the current topic if it must be addressed now, or create a brief top-level topic for future planning. Preserve stable IDs and do not duplicate known questions. To retire the original while keeping its uncertainty tracked, first create/link an open successor, then use `docagent todo --defer ID --reason "Why this is deferred"`. To drop obsolete work, use `--drop ID --reason "Why it no longer applies"`. Record why any original question no longer needs action. Deferred and dropped work remains in history.

Complete a subtopic with `docagent todo --done ID` only after saving its outcome and necessary edits. To close a parent, first finish, defer with an open follow-up, or explicitly drop every unfinished child. Update WORK.md's managed brief with the cumulative current direction, important decisions and reasons, constraints, outstanding questions, and implications for the next topic. Include a relative link to the parent's discussion outcome. Keep this snapshot within 3000 characters; detailed rationale remains in linked discussions. Then complete the parent and checkpoint. Completion never plans or starts the next topic automatically.

Reassess the remaining agenda after closing a parent, using its outcome and the updated cumulative summary. It is acceptable to finish with explicitly tracked open questions; it is not acceptable to lose them. Confirm the saved outcome, follow-up IDs, and next planning step briefly.
