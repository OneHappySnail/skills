---
name: tc-solution-concept
description: >
  Generates the business and functional sections of a Solution Concept Document for Siemens
  Teamcenter PLM customizations. Use this skill whenever the user wants to write, draft, start,
  or create a solution concept document, concept doc, or functional spec for a Teamcenter
  feature, customization, or enhancement — You do not simply accept "write a concept for X",
  you guide through the document creation by asking questions until all details are clear. Covers
  everything from Document Information through Acceptance Criteria. For the technical design
  section, the tc-solution-spec skill picks up from here.
---

# Solution Concept Document

Business and functional part of a Solution Concept Document for a Teamcenter customization. The technical section is added by `tc-solution-spec` into the same JSON.

Never write the document by hand. Content goes into `concept.json`. `fill.py` renders it through `template.md`, which fixes layout, headings, table shapes and boilerplate text.

- `template.md`: static layout. Change only when the user asks.
- `fill.py`: refuses missing required fields, bad enum values, wrong table row widths and unknown technical subsections. Derives Version and Creation Date from `history`. Numbers use cases, assumptions (`A1`..) and acceptance criteria (`F1`/`T1`/`U1`/`D1`).
- `example.json`: full schema and the check. `python -I fill.py example.json <scratchpad>/concept.md` must succeed.

## Steps

1. **Gather.** Take what the user already shared (Jira tickets, feature description, stakeholders). Ask only for what is missing. Minimum for a first draft: topic, problem description, program/project, requirement owner, lead(s).
2. **Interview section by section** until every required field is clear. Accept dropping an optional section when the user gives a reason. Use `[TBD]` for unknowns, never invent.
3. **Write `concept.json`** in the scratchpad, following `example.json`.
4. **Render:** `python -I <skill-dir>/fill.py <scratchpad>/concept.json <scratchpad>/SCD_<short-name>.md`. Fix any refusal in the JSON, never in the output.
5. **Hand over:** the full `.md` path, a list of `[TBD]` values and open points, then: "Next step: `tc-solution-spec` for the Technical Solution Concept."

## Fields

Required: `topic`, `program`, `requirement_owner`, `leads`, `history`, `purpose`, `objectives`, `business_context`, `scope`, `use_cases`, `ui`, `acceptance`.

| Field | Content |
|---|---|
| `history` | `[version, date, author, change]` rows. First row gives Creation Date, last row gives Version. |
| `status` | `DRAFT` (default) / `IN REVIEW` / `APPROVED` |
| `purpose` | 2–4 paragraphs: current situation, gap, what the concept introduces. |
| `objectives` | 3–6 `{title, points[]}`. |
| `challenges` / `drivers` | `{title, text}`. |
| `scope.in` / `scope.out` | `{heading, items[]}` grouped by component or feature area. Out of scope says why. |
| `use_cases` | `{title, trigger, outcome, frequency, narrative, rules[]}`. `frequency`: Very high / High / Medium / Low / One-time / Periodically / On demand. |
| `ui.summary` | Required. If there is no UI change, say so here and leave the other `ui` keys out. |
| `ui.validation` | Only if the feature involves user input or save. |
| `risks` | `[risk, likelihood, impact, mitigation]`. Likelihood/impact: Low / Medium / High. |
| `acceptance` | Groups `functional`, `technical`, `user`, `data` (data only for migration or consistency), rows `[criterion, verification]`. Include relevant groups only. |
| `open_points` | `[topic, @responsible, OPEN / IN PROGRESS / DONE]`. Always rendered, empty is fine. |

Systems / Platforms is always "Siemens Teamcenter" (fixed in the template).

## Quality guidance

- Frame challenges, drivers and use cases in Teamcenter terms (item revisions, datasets, LOVs, workflows, BMIDE).
- Prefer concrete descriptions. Keep the same terminology throughout.
- No customer, vendor or person names unless the user provided them.
