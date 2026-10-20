# skills

Agent skills for Siemens Teamcenter work.

| Skill | Purpose |
|-------|---------|
| [tc-doctor](tc-doctor/) | Analyzes and debugs Teamcenter and Active Workspace issues, including performance analysis from tcserver syslogs and journal files. |
| [siemens-plms-ir](siemens-plms-ir/) | Creates a Siemens PLMS Incident Report (IR / GTAC ticket) from tc-doctor findings, using a static template filled by script. |
| [tc-solution-concept](tc-solution-concept/) | Generates the business and functional sections of a Solution Concept Document, guiding the user through questions until all details are clear. |
| [tc-solution-spec](tc-solution-spec/) | Generates the Technical Solution Concept section. Picks up where tc-solution-concept leaves off. |
| [vfw-validation](vfw-validation/) | Writes or edits Validation Framework (VFW) checks: the EXPANSION/PROPERTY/CHECK/QUERY/JOB/TASK plain-text datasets. |
| [grilling](grilling/) | Interviews the user until a plan is fully understood. Invoked by the other skills when inputs are unclear. Copy of [mattpocock/skills](https://github.com/mattpocock/skills/blob/main/skills/productivity/grilling/SKILL.md) by Matt Pocock (MIT). |
| [tc-cpp](tc-cpp/) | Writes, reviews, or refactors Teamcenter server-side C/C++ (ITK, handlers, extensions, user exits). Covers ITK memory ownership, extern "C" error handling, logging, and legacy idioms. |

## Templates

- [templates/AGENTS.md](templates/AGENTS.md): project `AGENTS.md` for a Teamcenter customization repo. Copy to the project root and fill in the placeholders.
