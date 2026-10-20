---
name: vfw-validation
description: Write or edit MAIT/CNO Validation Framework (VFW) checks for Teamcenter - the EXPANSION/PROPERTY/CHECK/QUERY/JOB/TASK plain-text datasets. Use when asked to add, change, or debug a VFW/CNO_VFW validation, check, or rule, or when editing files named *_EXPANSION.txt, *_PROPERTY.txt, *_CHECK.txt, *_QUERY.txt, *_JOB.txt, or *_TASK.txt.
---

# VFW validation authoring

MAIT/CNO Validation Framework (VFW) is a config-driven, no-source-published
Teamcenter add-on. Its syntax lives in `reference/` alongside this file,
distilled from the admin manual — load only the file(s) you actually need:

- [reference/expansion.md](reference/expansion.md) — object/relation traversal
- [reference/property.md](reference/property.md) — property extraction
- [reference/check.md](reference/check.md) — check-line syntax, scope, reuse, common recipes
- [reference/keywords.md](reference/keywords.md) — compare/value keyword tables, bracket tokens, message-severity prefixes
- [reference/query-job-task.md](reference/query-job-task.md) — QUERY sub-filters, JOB wiring, TASK post-actions

## Workflow

1. **Learn the project's own conventions before writing anything.** The
   manual documents the engine's full feature surface; any given deployment
   uses a subset with its own vocabulary (status codes, § byte encoding,
   preferred relations, naming style). Find the target JOB dataset, read
   its `EXPANSION=`/`PROPERTY=`/`CHECK=`/`QUERY=` values, and skim those
   files plus one or two sibling `*_CHECK.txt` files in the same directory
   for precedent before inventing syntax from the reference docs alone.
2. **Decide where new lines go:**
   - New EXPANSION lines → append to the JOB's existing (single) EXPANSION
     dataset. A JOB can only reference **one** EXPANSION and **one** QUERY
     dataset — never split these into a new file added via comma.
   - New PROPERTY/CHECK lines → append to an already-wired dataset, or add
     a new dedicated file and list its name in the JOB's (and its WF_JOB
     twin's, if one exists) comma-separated `PROPERTY=`/`CHECK=` — both
     support multiple datasets. Prefer a new dedicated file when the
     addition is a self-contained feature worth naming and reviewing on
     its own.
3. **Write it**: EXPANSION → PROPERTY → QUERY sub-filter (only if you need
   one) → CHECK. Match an existing check's ID-naming/comment style in the
   same file rather than introducing a new convention.
4. **Match file mechanics exactly** before saving: `§` byte encoding
   (UTF-8 vs Latin-1 — varies per file, check first) and line endings
   (CRLF is near-universal in this ecosystem). Editing tools that silently
   normalize line endings (e.g. some `sed -i` builds) can rewrite an
   entire file's CRLF to LF — diff the result and restore with
   `unix2dos` if that happens.
5. **Verify.** Run a VFW linter/LSP if one is configured. Otherwise
   self-review for: `§`/`~` segment counts, unknown keywords, bad
   `scope=`/`CRITERIA=` values, a check ID reused with conflicting scopes,
   and `EXPANSION=`/`QUERY=` holding a comma. Compare against
   `reference/check.md` and precedent in the same project.

## Gotchas worth remembering

- `count eq`/`count gt`/`count lt` carry their operand **inside** the
  keyword segment (`§count lt 2§`), unlike every other keyword.
- `scope=` values are accepted case-insensitively in practice (`Object` and
  `object` both appear in deployed datasets) but a single check `ID`
  must not mix scopes.
- A failing check's severity is controlled by a **message prefix**, not a
  separate field: none = hard fail, `WARNING:` = non-blocking,
  `CRITICAL:` = blocking-but-dismissible, `AUTO_FILL:value` = not a
  failure, triggers AutoFill.
- For "is this value in a list built from other objects" (e.g. a
  precise-reference-is-leading dedup), prefer `allowed`/`not allowed` with
  a bracket-aggregated value (`[Type:Property]`) — `inlist`/`not inlist`
  do the same thing on paper but are rarely used and less proven.
- A dynamic PROPERTY alias (`Type§Alias§|formula|`) is *usually* referenced
  in CHECK as `Type:Alias`, but some datasets reference it as
  `Type§Alias` instead — don't assume the compare keyword is always the
  2nd `§`-segment when reading an unfamiliar line.
