---
name: tc-solution-spec
description: >
  Generates the Technical Solution Concept section of a Solution Concept Document for Siemens
  Teamcenter PLM customizations. Use this skill whenever the user wants to write or extend the
  technical design / technical specification part of a concept document — You do not accept
  "now do the technical part", but ask questions until all details are clear. Requires understanding
  of Teamcenter customization boundaries and patterns. Picks up where the tc-solution-concept skill leaves off.
---

# Technical Solution Concept (Teamcenter)

Writes the `technical` block of the `concept.json` that `tc-solution-concept` creates, and renders it with that skill's `fill.py`. Never write the section by hand. Implementers consume it, so ground it in what Teamcenter actually supports.

Renderer: `<skills-dir>/tc-solution-concept/fill.py`. Schema: the `technical` block in its `example.json`.

## Customization layers

Assign every design decision to one layer:

| Layer | What it is | Examples |
|---|---|---|
| **BMIDE / Data Model** | Data model configuration | Types, properties, LOVs, compound properties, display rules |
| **ITK / SOA** | Server-side custom code | Save handlers, property operations, extensions, custom SOA services |
| **AWC** | Active Workspace Client UI | Declarative configuration, commands, panels, stylesheets, column configs |
| **Workflow** | Workflow Designer + handlers | Templates, action/rule handlers, assignment rules |
| **Integration** | Gateways to other enterprise systems (e.g. T4S, T4EA) | Transfer config, mapping rules, payload generation, triggered syncs |
| **External** | External systems pushing to or pulling from TC | Import/export bridges, dispatcher jobs |
| **Preferences / Datasets** | Configuration stored in TC | Site preferences, dataset-stored config |

No custom code where BMIDE configuration suffices. No UI customization where a stylesheet does. If a requirement cannot be met within TC's customization model, say so and propose the closest viable alternative.

## Steps

1. **Load the concept.** Use the `concept.json` from this conversation. If the user brings a concept from elsewhere, ask for scope, use cases and UI concept, and write only the `technical` block.
2. **Extract:** functional behavior to implement, layers involved, constraints (TC version, integrations, existing customizations).
3. **Pick subsections** (table below). Not every feature needs every one.
4. **Interview** until every chosen subsection is clear. Accept dropping a subsection when the user gives a reason. Surface open points that block the design rather than guess. Ask the user when unsure about a Teamcenter mechanism.
5. **Write `technical`** into `concept.json`: `intro` (required: overall approach and layers involved) plus the chosen subsection keys.
6. **Render:**
   - Full document: `python -I <skills-dir>/tc-solution-concept/fill.py <scratchpad>/concept.json <scratchpad>/SCD_<short-name>.md`. The section lands before Open Points.
   - Concept from elsewhere: add `--technical-only` and give the user the section to paste after Acceptance Criteria.
7. **Hand over** the `.md` path and any new open points.

## Subsections

Rendered in this order. Bodies are Markdown strings, except `architecture` and `separation`: `{text, rows}` with fixed columns.

| Key | Include when | Content |
|---|---|---|
| `architecture` | Several interacting components or layers | Building blocks and interaction. Rows `[component, role, TC mechanism]`. |
| `data_model` | New or changed types, properties, LOVs, relations | Type + parent, property name/type/storage (local/compound/relation), LOV and how it is populated, BOM cardinalities, display rules. |
| `ui` | Stylesheets, tiles, columns, commands, panels, icons | Declarative config changes, command contributions, panel layouts. |
| `workflow` | Templates, handlers or assignment rules change | Template name. Per handler: type, trigger (task + event), logic, error behavior (block / warn / log). |
| `integration` | An enterprise integration is affected | Transfer config or payload changes, transferred properties, name/value mapping. |
| `external_sync` | An external system pushes data into TC | Source, trigger, mapping, conflict handling. |
| `processing` | Data processed by a custom algorithm | Inputs, steps, validation rule, output. Worked example if it helps. |
| `configuration` | Behavior driven by preferences or config datasets | What is configurable, storage, owner, load time (session / request), schema. |
| `validation` | Structured error contract | Where it runs (AWC / server / both), error codes + EN messages, failure behavior. |
| `persistence` | Caching or runtime behavior matters | What is persisted, cache scope (session / process), threading in batch or dispatcher. |
| `migration` | Existing data must change | Affected objects/properties, mapping, execution (ITK utility / dispatcher / manual), post-migration validation. |
| `separation` | Several layers interact | Rows `[layer, responsible for]`. |

## Quality guidance

- Name things concretely: real property types (`STRING`, `BOOLEAN`, `relation`), real handler names, real AWC config keys. Never invent a handler, preference or API; ask the user.
- Explain the why: which mechanism, and why over the alternative (e.g. save handler vs. property operation).
- An unsupported customization approach is a risk: flag it and propose the closest viable alternative.
