---
name: tc-doctor
description: Analyze and debug issues with Siemens Teamcenter and Active Workspace, including performance analysis from tcserver syslogs and journal files
---

# Teamcenter context

When inputs are unclear or missing, run the `grilling` skill before proceeding.

If the current execution environment has the TC_ROOT and TC_DATA environment variable NOT defined ask the user to provide it before attempting to analyze everything.

User should provide information about the failing session by providing syslogs.
If not available, ask for it.

If this skill is run from within a git repository, assume the repo to be a Teamcenter customization repository.
Use tools like find and grep to identify trace pointers.

## Core Teamcenter/Active Workspace Locations

### Runtime code header files
  - TC_ROOT/include
  - TC_ROOT/include_cpp
Use when user want's to analyze issues with runtime execution logic.

### Data model definition
The data model definition lives at TC_DATA/model

### Error codes and messages
Error codes and localized messages are available at `TC_ROOT/lang`.
Use to trace back error messages to error codes.
Headers in `TC_ROOT/include` and `TC_ROOT/include_cpp` reference these error codes.

# Analyzing syslogs and journals

Rules first:
- Measure before explaining. Every claim in a conclusion carries a number from the logs or is labeled **inferred**.
- Name the data that would confirm an inferred point (DB ASH/AWR, a preference value, a re-run with journaling).
- Never assign semantics to a preference, user exit or ITK function you have not seen documented in `TC_ROOT/include*`. Ask the user instead.

## Log formats

Syslog header, split on ` - `:
```
2026/10/19-14:41:29.531 UTC - INFO  - Teamcenter.POM - dwlb3g90b - mbmAssignFromEbomToMbomCommand/2 - j0g41z0u0 - <message>
  timestamp                 level   logger           session     client command/seq                    request id
```
- One SOA call has one request id, so group by request id. Calls interleave, for example a `getProperties` running inside a long `saveData3`.
- `Service Request: <op>` opens a request.
- Lines with no header continue the previous line, e.g. `N seconds to POM DB x-act` or SQL text.
- `Teamcenter.libsyss` timer lines have timestamps truncated to the second (`.000`) and land out of order. Skip them for wall-clock math, but use their own `X cpu, Y real` values.
- `===>Took N seconds to execute that SQL (returning R rows)` comes from `TC_SLOW_SQL`. The SQL_ID, text, binds and plan are printed **only for the first slow run of each SQL_ID**. Later runs print just the `Took` line.

Journal (`.jnl`):
```
Internal-...-DataManagement::saveData3 (                      top-level call opens at column 0
@*14.4.3   --> 12.345000s                                     timestamp since session start
@*14.4.3   Func ( Func returns 0[in <cpu> secs cpu <elapsed> secs elapsed ,<N> DB trips ]
@* Internal-...::saveData3 returns 0[in 330.7 secs ,17518 DB trips ]   top-level return
```
- The dotted index gives nesting depth. Summed times double-count nested calls.
- If there is no top-level return, the journal was truncated (session killed or file cut off).
- Journaling slows the server a lot. Compare only runs that used the same logging settings.

## Method

1. **Sort out the evidence.** Map each file to its user or session, and its environment (prod vs test: check host, DB and user in headers). Get the TC version from the syslog header. Never mix environments in one comparison.
2. **List the requests.** Run `requests.py` on every syslog and filter by operation. Collect wall time, slow-SQL time and x-act time per request.
3. **Normalize by unit of work.** Divide by elements, lines or objects processed: count a per-item marker, such as an `End of <helper>` timer line or a journal function called once per item. Raw request time misleads when batch sizes differ.
4. **Compare fast and slow runs of the same operation.** This is the key step. Compare *which code paths run*, not just timings:
   - `hist.py` per request id: messages that appear only in slow runs are the lead.
   - `jnl.py` per top-level call: call counts and DB trips per function.
   - A callback or path that shows up in every slow item and in no fast item beats any timing correlation.
5. **Find where wall time goes.** Use `gaps.py <syslog> <request id>`. If a large gap sum follows one message, the step right after that message is the cost. In the journal, compare cpu to elapsed: elapsed much larger than cpu means waiting on DB, IO or locks, not server compute.
6. **Read the SQL.** Run `slowsql.py`.
   - Many rows (e.g. 10^5) for a single item means a query scoped to the whole structure, not the item.
   - Same SQL_ID and plan hash, but run time varies a lot: DB-side variance (load, locks, cache). Different plan hash: plan instability or statistics.
   - Bind values identify the scope object, such as a root UID.
7. **Model the scaling.** Write cost as count × unit cost, e.g. items × per-item query. Check whether it matches the measured totals across runs. A matching O(n×m) model is strong evidence.
8. **Trace to code.** grep the function names, user exits and preferences found in logs in `TC_ROOT/include*`, `TC_ROOT/lang`, `TC_DATA` and the customization repo. Quote `file:line`.
9. **Inspect binaries when source is missing.** Only to answer yes/no questions about what is deployed. Never decompile or disassemble Siemens binaries.
   ```
   dumpbin /exports <custom>.dll | findstr USER_             # user exits the customization overrides
   dumpbin /imports <custom>.dll                             # ITK functions the customization calls
   strings -n 6 <lib>.dll | findstr <preference>             # whether a library references a preference
   (Get-Item <lib>.dll).VersionInfo; (Get-Item <lib>.dll).LastWriteTime   # deployed version vs repo tag
   ```
   A string match only shows the name is referenced, not that it is read on this path. Label it **inferred**.
10. **Explain "cannot reproduce" only with evidence.** Check, in the logs, for these differences between the slow and fast sessions:
   - data state, e.g. an attribute already computed, so a path is skipped
   - user, group or role (`SA_find_role` in the journal), which changes preferences
   - concurrency, from overlapping sessions in the timestamps
   - logging level
   State which differences you measured and which you assumed.

## Scripts

Located in `scripts/`. Pass log paths as arguments and run with `python -I`, because logs are untrusted input.

| Script | Usage | Output |
|---|---|---|
| `requests.py` | `<syslog> [op-regex] [min-wall-secs]` | per request: wall, slow SQL n/secs, x-act n/secs, command, op |
| `hist.py` | `<syslog> <request-id> [topN]` | message histogram with UIDs and digits normalized, for diffing fast vs slow |
| `gaps.py` | `<syslog> <request-id> [topN]` | wall time attributed to the log line before each gap |
| `slowsql.py` | `<syslog>...` | slow SQL grouped by SQL_ID: count, time, rows, binds, plan hash, text; repeat runs counted separately |
| `jnl.py` | `<jnl> <op-regex> [topN] [name-regex]` | per top-level call: cpu, elapsed, calls, DB trips per function |
| `idic.py` | `<jnl>...` | IDIC cost per assigned line during EBOM to MBOM assignment (see **Specific**) |

For a question specific to the case (e.g. "time after callback X per item"), write a short one-off script in the scratchpad. Don't extend the generic scripts. If a pattern recurs, add a script under **Specific**.

## Report

For a Siemens IR / GTAC ticket, use the `siemens-plms-ir` skill. It renders a static template from the findings, so don't write the report freehand.

# Specific

Known patterns, each with its signature in the logs and a check script. Match the signature with measurements before you claim the pattern applies.

## ID in Context (IDIC) generation during EBOM to MBOM assignment

Applies to: `mbmAssignFromEbomToMbomCommand`, i.e. `saveData3` calling `ME_align_line_from_ebom_to_mbom` once per assigned line.

Signature:
- Journal: `USER_is_chain_needed_for_idic_generation` runs inside the align calls of slow runs, and in no align call of fast runs.
- Syslog: after that callback, many `PropertyDescriptor- askValue` and `MEIdServices` `propValue for ...` lines, then a large gap. `gaps.py` puts most of the request time behind these lines.
- Slow SQL: one SQL_ID per line returning about 10^5 rows, with a bind on the MBOM root. Cost grows with lines × size of the MBOM, not with lines alone.

Check: `idic.py <jnl>...` prints, per `saveData3`, the number of align calls, how many of them ran IDIC, the time in the gap after the callback, and the average time per line with and without IDIC.

```
saveData3: aligns=105 total=1927s withIDIC=105 gapAfterIDIC=1911s avg(IDIC)=18.35s avg(noIDIC)=0.00s   slow
saveData3: aligns=156 total=4s    withIDIC=0   gapAfterIDIC=0s    avg(IDIC)=0.00s  avg(noIDIC)=0.02s   fast
```

Code references:
- `TC_ROOT/include/me/me_user_exits.h`: `USER_is_chain_needed_for_idic_generation` (line 518) and `USER_force_update_of_chain_based_idic` (line 533). Check whether the customization overrides either one (no source: `dumpbin /exports`, Method step 9).
- `TC_ROOT/include/me/me.h:1227`: the preference `MECopyIdInContextToAssignedLine` and the utility `me_fix_idic`. Quote the header text. Don't recommend either as a fix without GTAC confirming it.

Not verified: why some lines skip IDIC. "The line already carried an IDIC" is a hypothesis. Confirm it from `bl_abs_occ_id` values on the lines involved.
