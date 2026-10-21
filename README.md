# Design collaboration with docagent

Turn rough brainstorming notes and system overviews into a clear, progressively detailed design. Start with one main ideas page; develop a few modules at a time; place precise specifications at the leaves. Each module should be understandable on its own.

**Skills understand and write. `docagent` performs fast deterministic operations. Markdown is authoritative.** Listing TODOs, selecting a module, and inspecting the hierarchy require no model call. Search uses GNO; hybrid and semantic search may use its local retrieval models, never an agent-generated answer.

## Install

Requires Python 3.10+ and uv. From this checkout:

```bash
uv tool install .
uv tool update-shell
uv run python scripts/install_project.py --engine codex --project /path/to/design
# Optional second host, sharing the same records:
uv run python scripts/install_project.py --engine claude --project /path/to/design
```

Install GNO on PATH for project-scoped retrieval. Its adapter is inherited from the repository's GNO 1.5.1 integration. Use `--skip-gno` on the installer for work without configured retrieval. Core record commands work without GNO. Search and explicit index flush require it.

The installer preserves manually modified installed assets, reports conflicts, and installs only the selected host's skills. Codex uses `.agents/skills`; Claude uses `.claude/skills`. The existing Claude settings integration is retained: conflicting settings remain unchanged and the installer prints a launch command using a project-local settings file. Confirm that the host loads project AGENTS.md.

For records and viewer only, without installing host skills:

```bash
docagent init /path/to/design --skip-gno
cd /path/to/design
docagent help
```

After editing this toolkit, reinstall the command with `uv tool install --reinstall .` and rerun the host installer. Fresh design projects are supported; existing `.rs` projects are deliberately left untouched. There is no automatic migration or `rsagent` compatibility alias.

## Typical workflow

The examples below use Codex skill syntax (`$doc-brainstorm`). In Claude use `/doc-brainstorm`, or make the same request in ordinary language. Run shell commands in the project directory. Use the task IDs returned by your commands; the IDs below are examples.

### 1. Resume and understand the inputs

```bash
cd /path/to/design
docagent status
```

Ask: **“$doc-sources Read these documents and summarize the main ideas, constraints, and open questions.”** Then use doc-design/doc-write to establish the main explanation in `design.md`. Source originals remain unchanged.

### 2. Prepare the agenda with stronger reasoning

Ask: **“$doc-brainstorm Organize these ideas into top-level topics. Plan only the first topic in detail, using the current design and prior outcomes.”**

There is no limit on task count. Future topics have only a purpose and known dependencies; their subtopics do not exist yet. The agent starts the current topic, creates its focused subtopics, and fills their linked briefs with context, watch points, evidence, expected outcomes, and model recommendations.

```bash
docagent todo
docagent todo --start t001
```

For example, the agent can add a current subtopic with `docagent todo "Clarify retry behavior" --parent t001 --why "Avoid duplicate work after restart"`. Each subtopic gets a discussion file for its brief and later outcome. Adding a future top-level topic does not create its discussion or subtopics.

### 3. Discuss one subtopic in a fresh session

```bash
docagent todo --next
docagent todo --start t003
docagent todo --show t003
```

Use a suitable lower-cost model when the question is bounded. The agent suggests a model/effort change only when helpful; you select it in the host and open a fresh chat in the same project. Ask: **“$doc-brainstorm Continue topic t003 using its saved brief, current planning summary, and relevant sources.”** The brief must be prepared before handoff. Significant architectural questions or conflicting evidence need stronger reasoning.

### 4. Save the outcome and finish the current topic

Ask: **“Save the result and rationale. Update the design where agreed, review substantial changes, and add or update TODOs for unresolved old and new questions.”** The agent writes the discussion's Outcome and handoff block before marking the subtopic done.

```bash
docagent todo --done t003
```

Before closing the parent, every child must be completed, explicitly dropped with a reason, or deferred with an open linked follow-up. Save the parent outcome and update WORK.md's cumulative planning summary with the important decisions and reasons, constraints, open questions, implications for later work, and a link to the parent outcome. Also update the Key decisions at a glance section of `design.md` for every requirement or decision whose status changed.

```bash
docagent todo --done t001
docagent checkpoint
```

`checkpoint` checks already-saved files; the agent must summarize the conversation first. Reassess the remaining agenda before starting and expanding the next parent. Replan immediately if discoveries invalidate the current plan; useful work and explicit follow-ups remain recorded.

### 5. View the agenda and design

```bash
python3 -m http.server 8000
```

Open **http://localhost:8000**. The README links to the main design; the sidebar's **TODO** entry opens the two-level agenda with visible motivations, statuses, model recommendations, and discussion links. Completed topic records remain available under Done.

### Reading contract

Every document we author is human-readable first, including design pages, source summaries, brainstorming records, decisions, TODOs, working summaries, and help. State its purpose, provide the context needed to understand it, use plain language, and introduce ideas progressively. Keep essential meaning visible in the document body; metadata supports tools and must not be the only place a reader can find a task’s motivation, a decision’s status, or necessary context. Preserve original input files unchanged; machine runtime files are separate from authored documents.

Choose the format that makes the idea easiest to understand. Use concise, complete bullets for distinct ideas, short prose for explanations that need continuity, and tables for comparisons. Add a figure, diagram, or example when it clarifies structure, relationships, sequence, or behavior. Give figures clear labels and a short explanation of what the reader should notice; keep them at the page’s level of detail. Avoid dense paragraphs, fragmented bullet inventories, and decorative figures.

Start with purpose and the core idea, then essential context and interactions, a few internal parts, and deeper detail. Aim for three to five peer concepts. This is a guideline, not a rigid cap: regroup meaningfully and preserve necessary constraints. Modules repeat enough context to be understood independently. Upper pages tell a coherent story rather than merely listing links; leaves hold exact interfaces, algorithms, configuration, and edge cases.

`design.md` opens with a short **Key decisions at a glance** section: one line per requirement or decision, grouped by system component, tagged Req, Decided, Direction or Open, and linked to its discussion or TODO. It is the quick overview during requirements work and the starting module list for component design.

Source proposals are not automatically accepted design decisions. Keep original material, alternative history, and rationale separate from the current design. Clearly mark unresolved choices.

## Delegation and cost

The project instructions request selective delegation for substantial independent work. The host agent spawns workers; `docagent` continues to handle deterministic operations directly. No additional skill or AI service is required.

| Task | Default assignment |
| --- | --- |
| TODOs, navigation, structural validation | Direct `docagent` command |
| Explicit source extraction or a substantial wording edit | Lower-cost worker, low effort |
| Independent ambiguity or missing-explanation review of one module | Lower-cost worker, medium effort |
| Architecture, conflicting evidence, hierarchy changes, final integration | Main agent |

On Codex, the skills explicitly request `gpt-6-luna` for delegated work, with `low` or `medium` effort as above. User settings take precedence. Other hosts may use an explicitly available lower-cost equivalent; if suitable model selection is unavailable, the main agent does the work and briefly reports the fallback. These are task defaults, not a guarantee of price or account availability.

Start with one worker and use at most two concurrently for independent assignments. Provide a fresh task context with the required sources, reading rules, constraints, and expected output. Avoid inheriting the entire chat. Default to read-only findings or proposed text; delegated edits must have non-overlapping file ownership. Workers report uncertainties, source locations, and checks, and do not spawn more workers or modify shared TODOs, active pointers, navigation, or checkpoints.

The main agent verifies consequential claims and meaning, integrates accepted results, updates shared work records, and checkpoints. Conflicts or missing information return to the main agent for judgment. Small tasks stay in the main thread. Additional workers consume resources: judge the benefit against briefing and integration overhead rather than assuming parallel work is cheaper.

## More help

Use `docagent help` for the full command reference, or ask `$doc-help` for workflow guidance. Direct commands run without an AI turn; hosts with direct shell mode may accept `!docagent ...`. `--json` and `--project /path/to/design` are available for automation. Model recommendations are saved text, not automatic model switches.

## Files and editing

| Location | Purpose |
| --- | --- |
| `README.md` | Project introduction and links to the design, tasks, and workflow |
| `design.md`, `modules/` | Reader-facing design; module parent IDs define the hierarchy |
| `sources/`, `sources/files/` | Extraction notes and byte-preserved local originals |
| `discussions/` | Brainstorming, alternatives, decisions, and compact resumes |
| `TODO.md`, `WORK.md` | Two-level agenda, cumulative planning summary, and current work pointers |
| `.docagent/` | Runtime configuration, transaction journal, installation records, and search state |

IDs are stable (`root`, `m001`, `d001`, `s001`, `t001`). Module files are flat on disk; parent metadata defines the reading hierarchy, so moving a module does not break links. Shared dependencies use normal cross-links rather than multiple parents. Edit Markdown directly, preserving frontmatter and managed marker pairs. `checkpoint` updates generated child links and sidebar navigation while retaining surrounding prose.

TODO records have stable IDs and optional parent IDs; old flat tasks remain top-level topics. The first TODO mutation upgrades old records to the readable agenda layout while preserving IDs, ordering, surrounding prose, and existing discussion links. Only the current topic can acquire subtopics, and finishing it never expands or starts the next topic automatically. There is no task-count limit.

Task fields and navigation are managed by docagent. Preserve its marker pairs. Keep detailed briefs, watch points, evidence, and outcomes in the linked discussions; add free-form agenda notes inside each task's notes markers. Such notes and surrounding custom prose survive regeneration. Generated task fields should be changed through their record metadata and then checkpointed; use lifecycle commands for status changes. `--delete` is a compatibility alias for dropping work with a reason, preserving history.

Completing work checks for a saved outcome; the skill judges whether it is meaningful and carries open questions forward. `--defer` requires a reason and an open successor linked with `--follow-up-for`. Existing unfinished questions should be reused or updated rather than duplicated; the full CLI help includes a link operation for reusing an open successor. Future follow-ups remain brief top-level items until their turn. WORK.md's bounded cumulative summary links detailed outcomes; it is not the complete historical record.

Local source registration deduplicates by content hash and copies any file format. Reading and text extraction are skill responsibilities; GNO configuration indexes Markdown and PDF, so other formats need readable extraction notes for retrieval. URL registration neither downloads content nor claims it has been read.

## Saving, recovery, and viewing

The AI writes the discussion and compact resume; `checkpoint` validates files already saved. Direct selection cannot preserve conversation-only material. WORK.md's brief is bounded to 3000 characters and discussion resumes to 5000; oversized reads show an explicit excerpt, and checkpoints require shortening the saved resume. Detailed reasoning belongs outside those blocks.

Multi-file content changes use a roll-forward journal. The next mutation retries an interrupted transaction. Failed indexing retains a durable queue and does not undo saved Markdown. Check `index status`, then retry with `index flush`. Manual edits require a checkpoint or flush; there is no watcher. `.docagent/gno.yaml` and caches scope search to this project. `DOCAGENT_GNO_EMBED_MODEL=file:/absolute/path/model.gguf` can reuse a local model. `DOCAGENT_DISABLE_WORKER=1` disables background workers, useful in tests. Semantic retrieval depends on an available local GNO runtime and models.

Serve the project to read it:

```bash
python3 -m http.server 8000
# Open http://localhost:8000
```

The Docsify viewer opens `README.md`, which introduces the project and links to `design.md` for the main design ideas. The sidebar includes project home and the design hierarchy. The viewer hides frontmatter and supports Mermaid diagrams. CDN assets require network access; the Markdown remains directly readable offline. Existing custom viewers are preserved by the installer. No publication or hosting is performed.

Structural validation checks local file targets, not Markdown anchors, prose correctness, or every possible Markdown link syntax. doc-review provides the human-readability and semantic checks.

## Development

```bash
uv run --with pytest python -m pytest -q
```

Set `DOCAGENT_TEST_GNO=1` to opt into the installed GNO integration test. The six skill definitions live in `skills/`; the reading-contract copies are kept identical by a test so each installed writing/review skill remains self-contained. No automatic Git operations are part of the installed workflow.
