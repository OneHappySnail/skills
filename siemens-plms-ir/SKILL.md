---
name: siemens-plms-ir
description: Create a Siemens PLMS Incident Report (IR, GTAC ticket) from tc-doctor findings, using a static template filled by script
---

# Siemens PLMS IR

Companion to `tc-doctor`. Turns its findings into an IR. Never write the IR by hand.

Output is always the `.md` file from `fill.py`, ready to copy and paste into the Siemens ticket. Never publish it as an artifact, doc, website or HTML page, and never convert it to another format.

The Siemens ticket form is a Quill rich-text editor, not a Markdown renderer. Pasted Markdown syntax shows up literally. So the output must be plain text:
- section titles on their own line, with no `#`
- lists only as `1.` and `-`
- no tables (rows become bullets), no code fences, no `**`/`_`

The submitter applies heading styles in the editor if wanted. Keep `template.md` and `fill.py` within these rules.

- `template.md` is the static IR layout. Change it only when the user asks.
- `fill.py` renders it from a findings JSON. It refuses missing required fields and analysis items whose status is not `verified` or `inferred`.
- `example.json` shows the full schema and is the check: `python -I fill.py example.json <scratchpad>/ir.md` must succeed.

## Steps

1. **Collect findings.** If no `tc-doctor` analysis exists in this conversation, run `tc-doctor` first. Don't file an IR without measurements.
2. **Write `findings.json`** in the scratchpad, following `example.json`:
   - `measurements`: numbers produced by tc-doctor scripts, not rounded estimates.
   - `analysis[]`: one item per claim, with an optional `excerpt` copied verbatim from the logs, and `status: verified|inferred`. Keep inferred claims marked as inferred.
   - `questions`: what Siemens must answer. Don't propose fixes the logs don't support.
   - `attachments`: the log files the analysis cites.
   - Leave `site_id`, `severity` and `contact` empty unless the user gave them. They render as `TBD by submitter`.
   - Additional information Siemens always asks for. Each renders as `TBD by submitter` when empty:
     - `environments_affected`: e.g. "Production; not reproduced on test".
     - `users_affected`: logs only give a lower bound, such as "at least 4 of 5 sampled users". Say that it is a sample.
     - `devices_affected`: client OS, browser or device. Not visible in server logs, so ask the user.
     - `other_versions`: whether it reproduces on another Teamcenter version. Fill in only if a run on that version was actually done.
   - Leave out hostnames, DB names, user names and customer data. Use pseudonyms like `u1`..`uN`.
3. **Render:** `python -I <skill-dir>/fill.py <scratchpad>/findings.json <scratchpad>/IR_<short-name>.md`
4. **Hand over:** give the full path of the `.md` file, plus a list of `TBD` fields and inferred claims for the user to check before filing.

Optional fields (`platform`, `database`, `impact`, `workarounds`) render as `None.` when empty. Ask for business impact if it's unknown, because Siemens uses it to prioritize.
