# Future plan: per-section edit protection for paper summaries

Status: **not implemented.** This is a design for a later change.

## Problem

`rsagent paper summary REF` replaces the whole managed summary block (`<!-- rs:summary:start/end -->`). A user who hand-edits any section (for example the Related work paragraph before pasting it into the manuscript, or a Key Q&A answer) loses the edit at the next save, switch, pause or close, because the agent rewrites the block from the conversation. Asking permission on every save would be annoying. The agent should not be trusted to remember which sections you changed.

No section is special; the same risk applies to every section of the summary.

## Design

The tool, not the agent, decides what is safe to overwrite.

1. **Section ownership by hash.** When `rsagent paper summary` saves, it splits the text into sections on `###` headings (`Main idea`, `Training setup`, `Key Q&A`, `Relevance to this research`, `Related work paragraph`, `Reading notes`; any heading counts). For each section it stores a hash of its normalized text in the note's frontmatter, as one map:

   ```yaml
   summary_hashes:
     main idea: 3f9a...
     key q&a: 91c0...
   ```

   Keys are lowercased heading text.
2. **Normalization.** Collapse all whitespace to single spaces and trim before hashing, so CRLF/LF changes, trailing spaces, line re-wrapping and Markdown formatters do not look like edits. The hash is of the text only, not of any Git state, so it survives commits, clones and branch switches unchanged.
3. **Comparison on every save.** For each section in the existing block, compare the current normalized text with its stored hash:
   - matches: the agent wrote it and nobody changed it, so it is replaced silently with the agent's new text;
   - differs: the user edited it, so the existing text is kept and the agent's version for that section is dropped;
   - no stored hash (note written before this feature, or section added by hand): treat as the user's and keep it.
4. **Partial updates.** The agent may send only the sections that changed. Sections it does not send are left untouched. Sections the user added that the agent never sends are always preserved, in place. The `_Last updated: ... · discussed in thread NNN_` line is tool-managed and always refreshed.
5. **Reporting, no prompt.** The command prints which sections it kept, for example `kept your edits: Key Q&A, Related work paragraph`. The tool never blocks or asks.
6. **Explicit refresh.** `rsagent paper summary REF --replace "Key Q&A"` (repeatable) replaces just the named section(s) even if edited; `--replace all` replaces everything. Replaced sections get fresh hashes.
7. **Merge conflicts and hash drift.** A Git merge conflict in the frontmatter, or any hash that no longer matches, is treated as "user edited". This is the safe direction: the section is kept until the user asks for a refresh.

## Agent behavior (skill changes)

Both `skills/rs-paper/SKILL.md` and `skills/rs-save/SKILL.md`:

- After saving, if the command reported kept sections and the new discussion would plausibly change them, add **one line** to the confirmation, for example: "Kept your edits to Related work; say 'update related work' to refresh." Do not ask again for the same section in the same session, and never block on a question.
- Accept explicit refresh requests in plain language ("update Key Q&A for paper 2", "refresh paper 2's summary", "rewrite related work from scratch") and in the skill (`/rs-paper 2 --related-work`, `$rs-paper 2 --related-work`), and run the command with `--replace SECTION`.
- When refreshing a section the user edited: read the user's current version first, keep their wording and structure where it is still correct, change only what the discussion made outdated or missing, and say in one line what changed. "From scratch" regenerates the section entirely.
- Send only changed sections when saving, to save tokens.

## Code changes

- `rs/sources.py`: extend `_set_block` / `set_summary` (today they replace the whole block) with section splitting, normalization, hash comparison and merge; keep `set_overview` unchanged unless the overview should be protected too (see open questions). Add a `replace` argument and return the list of kept sections.
- `rs/cli.py`: add repeatable `--replace SECTION` to `paper summary`; print the kept-sections line.
- Frontmatter: new optional `summary_hashes` (string map). `validate` should accept it and ignore unknown keys inside.
- Not needed in the installer; the change ships with the package and the updated skills (reinstall projects to refresh skills).

## Tests (write first, watch them fail)

- Saving a new summary stores hashes for every section.
- Unedited sections are replaced silently by a later save.
- A hand-edited section is kept, the others update, and the result names the kept section.
- Whitespace-only or line-wrap-only changes are not treated as edits (CRLF, trailing spaces, re-wrapped paragraph).
- Reverting an edit back to the original text makes the section replaceable again.
- Notes without `summary_hashes` keep every existing section (no overwrite on first use).
- Sections added by hand are preserved; sections the agent omits are untouched.
- `--replace "Key Q&A"` replaces only that section and refreshes its hash; `--replace all` replaces everything; an unknown section name is a clear error.
- A conflict-damaged or mismatched hash map is treated as edited.
- The `Last updated` line is always refreshed.
- Failure injection: a failed write leaves the old note (the existing transaction covers it).

## Small `rs-paper` wording fixes to fold in

- Step 3 word limit: say "excluding Reading notes and the Related work paragraph" (name the section exactly).
- Add a sentence: keep manual edits to any section unless asked to rewrite it (superseded by the tool-level protection once built, but keep as guidance).
- Remove the blank line after the `### Related work paragraph` heading in the format block, for consistency.
- Update the README "Paper summaries" text to describe edit protection and the `--replace` option.

## Open questions

- Should the **initial overview** block get the same protection? It is written once and rarely edited, so probably not at first; the same mechanism could be reused later.
- Heading renames by the user: a renamed section looks like a new, user-owned section and the old heading disappears from the agent's perspective. Acceptable, but the agent may then add a duplicate section; consider matching by position as a fallback.
- Whether to ever store the agent-written text (not only its hash) to enable a three-way merge. Not planned; the hash approach is enough unless users want automatic merging of their edits with new agent content.
