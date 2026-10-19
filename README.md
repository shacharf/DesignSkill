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

1. **Understand:** ask doc-sources to read your documents and extract ideas, constraints, and conflicts with source locations.
2. **Shape:** use doc-design to establish the main story in `design.md` and a few major modules.
3. **Explore:** use doc-brainstorm when a design choice needs alternatives and tradeoffs.
4. **Explain:** use doc-write to develop a selected module, repeating the same progression at each depth.
5. **Review:** after substantial drafting or revision, use doc-review to check readability, ambiguous interpretations, missing behavior, and consistency across affected modules. At major milestones, review the overall design. Record unresolved questions instead of inventing answers; small wording edits need no full review.

Use doc-help whenever you need guidance. Invoke skills as `$doc-design` in Codex or `/doc-design` in Claude, or request the task naturally. Skills are not a mandatory pipeline. They save meaningful progress and resume context so a later conversation can continue.

### Reading contract

Every document we author is human-readable first, including design pages, source summaries, brainstorming records, decisions, TODOs, working summaries, and help. State its purpose, provide the context needed to understand it, use plain language, and introduce ideas progressively. Keep essential meaning visible in the document body; metadata supports tools and must not be the only place a reader can find a task’s motivation, a decision’s status, or necessary context. Preserve original input files unchanged; machine runtime files are separate from authored documents.

Choose the format that makes the idea easiest to understand. Use concise, complete bullets for distinct ideas, short prose for explanations that need continuity, and tables for comparisons. Add a figure, diagram, or example when it clarifies structure, relationships, sequence, or behavior. Give figures clear labels and a short explanation of what the reader should notice; keep them at the page’s level of detail. Avoid dense paragraphs, fragmented bullet inventories, and decorative figures.

Start with purpose and the core idea, then essential context and interactions, a few internal parts, and deeper detail. Aim for three to five peer concepts. This is a guideline, not a rigid cap: regroup meaningfully and preserve necessary constraints. Modules repeat enough context to be understood independently. Upper pages tell a coherent story rather than merely listing links; leaves hold exact interfaces, algorithms, configuration, and edge cases.

Source proposals are not automatically accepted design decisions. Keep original material, alternative history, and rationale separate from the current design. Clearly mark unresolved choices.

## Direct commands

Run these in a normal terminal without AI inference. Hosts with direct shell mode may accept `!docagent ...`.

| Command | Result |
| --- | --- |
| `docagent help` | Workflow help, even outside a project |
| `docagent status` | Bounded working brief, current module, discussion resume, search freshness |
| `docagent tree` | Full design hierarchy |
| `docagent module create "Coordination" --parent root` | Create a module with a stable ID |
| `docagent module select m001` | Select module; clear a discussion from a different module |
| `docagent module show m001` | Read its saved content |
| `docagent module move m002 --parent m001` | Reparent safely; reject hierarchy cycles |
| `docagent discussion create "Assignment strategy" --module m001` | Create a discussion |
| `docagent discussion list` | List saved discussions |
| `docagent discussion select d001` | Select an open discussion and its module |
| `docagent discussion show d001` | Read its saved content |
| `docagent discussion state d001 closed` | Close; also supports open and obsolete |
| `docagent todo` | Pending and active tasks, in file order |
| `docagent todo "Clarify recovery" --why "Avoid duplicate work" --module m001` | Add a task with motivation |
| `docagent todo --start t001` | Retain task, mark active, create or resume its discussion |
| `docagent todo --done t001` | Preserve completed task in collapsed Done section |
| `docagent todo --delete t001` | Remove an unwanted task; preserve its discussion |
| `docagent todo --next` | First outstanding item in file order |
| `docagent todo --all` | Include completed tasks |
| `docagent source add /path/to/notes.md` | Copy original bytes and create a source note |
| `docagent source add https://example.org/design --title "External design"` | Register a URL without fetching it |
| `docagent source list` / `source show s001` | Inspect registered sources |
| `docagent search "assignment" --limit 5` | Bounded lexical retrieval |
| `docagent search "recovery strategy" --hybrid` | Hybrid retrieval; `--semantic` is also available |
| `docagent validate` | Check hierarchy, pointers, resumes, TODO records, and local file links |
| `docagent checkpoint` | Validate saved Markdown, update navigation, enqueue indexing |
| `docagent index status` / `index flush --lexical-only` | Inspect freshness or explicitly synchronize |

`--json` and `--project /path/to/design` work before or after commands. Use `COMMAND --help` for arguments. Read commands do not rebuild indexes. `validate` returns exit code 1 for diagnostics; invalid operations return 2. More than five children produces a review warning rather than a hard failure.

## Files and editing

| Location | Purpose |
| --- | --- |
| `design.md`, `modules/` | Reader-facing design; module parent IDs define the hierarchy |
| `sources/`, `sources/files/` | Extraction notes and byte-preserved local originals |
| `discussions/` | Brainstorming, alternatives, decisions, and compact resumes |
| `TODO.md`, `WORK.md` | Work queue, shared working brief, and active pointers |
| `.docagent/` | Runtime configuration, transaction journal, installation records, and search state |

IDs are stable (`root`, `m001`, `d001`, `s001`, `t001`). Module files are flat on disk; parent metadata defines the reading hierarchy, so moving a module does not break links. Shared dependencies use normal cross-links rather than multiple parents. Edit Markdown directly, preserving frontmatter and managed marker pairs. `checkpoint` updates generated child links and sidebar navigation while retaining surrounding prose.

TODO records are Markdown checkboxes with a metadata comment containing status, module, motivation, originating discussion, and working discussion. Directly edit task text and ordering; use CLI commands for lifecycle changes. Default command output lists outstanding work; skill conversations show only a few relevant items. `--start` is retryable and does not remove the task. Mark done when its outcome and needed design edits are saved; the CLI obeys your instruction and cannot judge semantic completion.

Local source registration deduplicates by content hash and copies any file format. Reading and text extraction are skill responsibilities; GNO configuration indexes Markdown and PDF, so other formats need readable extraction notes for retrieval. URL registration neither downloads content nor claims it has been read.

## Saving, recovery, and viewing

The AI writes the discussion and compact resume; `checkpoint` validates files already saved. Direct selection cannot preserve conversation-only material. WORK.md's brief is bounded to 3000 characters and discussion resumes to 5000; oversized reads show an explicit excerpt, and checkpoints require shortening the saved resume. Detailed reasoning belongs outside those blocks.

Multi-file content changes use a roll-forward journal. The next mutation retries an interrupted transaction. Failed indexing retains a durable queue and does not undo saved Markdown. Check `index status`, then retry with `index flush`. Manual edits require a checkpoint or flush; there is no watcher. `.docagent/gno.yaml` and caches scope search to this project. `DOCAGENT_GNO_EMBED_MODEL=file:/absolute/path/model.gguf` can reuse a local model. `DOCAGENT_DISABLE_WORKER=1` disables background workers, useful in tests. Semantic retrieval depends on an available local GNO runtime and models.

Serve the project to read it:

```bash
python3 -m http.server 8000
# Open http://localhost:8000
```

The Docsify viewer opens `design.md`, shows hierarchical navigation, hides frontmatter, and supports Mermaid diagrams. CDN assets require network access; the Markdown remains directly readable offline. Existing custom viewers are preserved by the installer. No publication or hosting is performed.

Structural validation checks local file targets, not Markdown anchors, prose correctness, or every possible Markdown link syntax. doc-review provides the human-readability and semantic checks.

## Development

```bash
uv run --with pytest python -m pytest -q
```

Set `DOCAGENT_TEST_GNO=1` to opt into the installed GNO integration test. The six skill definitions live in `skills/`; the reading-contract copies are kept identical by a test so each installed writing/review skill remains self-contained. No automatic Git operations are part of the installed workflow.
