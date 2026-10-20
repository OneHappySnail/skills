# <PROJECT_NAME> — Teamcenter customization

<!-- Template: replace every <PLACEHOLDER>. Delete the rows that do not apply. Keep only facts an agent cannot find by looking. -->

## C++ code

Load the `tc-cpp` skill before you write, review, or refactor any C/C++ in this repo. The rows below take precedence over it.

| Key | Value |
|---|---|
| Teamcenter version | `<e.g. 2312>` |
| `TC_ROOT` / `TC_DATA` | `<path>` / `<path>` |
| C headers / C++ headers | `$TC_ROOT/include` / `$TC_ROOT/include_cpp` |
| Project prefix | `<e.g. MY4>`, used for BMIDE types, handler names (`MY4-...`), and libraries |
| Custom error codes | `<header path>`, range `<from>-<to>`, generic fallback `<CODE_NAME>` |
| Logger root | `<Company.Project>` |
| Shared RAII and helper code | `<path>`. Reuse it before writing new wrappers. |

## Layout

<!-- Only what the directory tree does not explain itself. -->
- `<dir>`: <what lives here, if not obvious>

## Build and deploy

```sh
<build command>
<deploy / copy-to-TC_BIN command>
<how to run a utility or test against a dev server>
```

## Legacy code

<!-- Choose one policy and delete the others. -->
- Migrate on touch: replace legacy idioms (macros, `goto CLEANUP`, manual `MEM_free`) only inside functions you are already changing.
- Frozen: `<paths>` must not be refactored. Report problems there instead of fixing them.

## Project rules

<!-- Unwritten conventions, gotchas, and the reasons behind local choices. Examples:
- Handlers in `<dir>` run under `<user/group>`. Use `<API>` to bypass access checks only when <condition>.
- Preference `<NAME>` controls <behaviour>. Read it once per handler call.
-->
