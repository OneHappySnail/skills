# CHECK keyword reference

Source: VFW admin manual, chapter 17.4.1 "Keywords". Field separator below is
written as `§` (the literal section-sign character, `U+00A7`) — see
[check.md](check.md) for why the byte encoding of this character matters.

## Compare keywords

Sit between the left-hand side (object/property) and the compare value:
`LHS§KEYWORD§VALUE~FailMessage~SuccessMessage`.

| Keyword | Meaning |
|---|---|
| `allowed` | Value must match one of a list of accepted values. `A§allowed§A,C` and `A§allowed§A\|\|B\|\|C` both pass if the left value is `A`. |
| `allowed ignorecase` | Like `allowed`, case-insensitive. |
| `not allowed` | Value must not match any of a list of forbidden values (`&&`-separated, e.g. `A§not allowed§A&&B&&C`). |
| `not allowed ignorecase` | Like `not allowed`, case-insensitive. |
| `eq` | Value1 = Value2. Also accepts a comma list (`A§eq§A,A,A` passes). |
| `eq ignorecase` / `not eq` / `not eq ignorecase` | As above, case-insensitive / negated variants. |
| `gt` / `lt` / `ge` / `le` | `>`, `<`, `>=`, `<=`. |
| `bt` | Between: `value§bt§value1;value2`. |
| `exist` | A matching related object/property exists. **Only valid in `scope=structure` or `scope=object`.** |
| `not exist` | No matching related object/property exists. |
| `count eq` / `count gt` / `count lt` | Quantity check of related objects, e.g. `Property§count lt 2§*`. **The operand is inline in the keyword segment itself** (`count lt 2`, not `count lt` with `2` as the compare value) — easy to get wrong when writing a parser/highlighter for this grammar. Only valid in scope structure/object; evaluated at the very end of validation, so `[VAL_OBJECT:...]`/`[VAL_VALUE]` are NOT available in its message (see manual 18.4.3 note 2). |
| `contains` / `contains ignorecase` | Property value contains a substring. |
| `not contains` / `not contains ignorecase` | Property value does not contain a substring. |
| `unique` | Property value is unique against a list of Teamcenter values. |
| `inlist` / `inlist ignorecase` | String exists in a list of check values. **Rarely used in deployments** — prefer `allowed`/`not allowed` (which do the same list-membership test and are used everywhere) unless you have a specific reason and can test live. |
| `not inlist` / `not inlist ignorecase` | Negation of `inlist`. Same caveat. |
| `isSubType` | object_type is the given type or a subtype of it. Needs a **DB-value** property (`?object_type`), e.g. `C:ItemRevision:?object_type~Type` then `Type§isSubType§ItemRevision`. |

## Value keywords / functions

Used on the right-hand (compare-value) side:

| Keyword | Meaning |
|---|---|
| `empty` | Matches an empty value. |
| `numeric` | Value is numeric, e.g. `Attr§allowed§numeric`. Also `eq§numeric(123)`. |
| `decimal` | Value is decimal. Also `eq§decimal(123.0)`. Uses the OS decimal separator of the **Teamcenter application server**, not the client. |
| `translate(VALUE)` | Translates VALUE via the current TC session locale/TextServer before compare. |
| `regex(EXPR)` | Regex compare. Regex engine differs between Linux/Windows TC servers. Use `&#xA;` for a literal newline in the XML dataset. |
| `[LOV:Name]` / `[LOV:?Name]` / `[LOV:!Name]` | Compare against a Teamcenter LOV — bare/`?` = DB value, `!` = description. |
| `count(VALUE)` | Counts matching property occurrences, almost always paired with `eq` for uniqueness checks (see [check.md](check.md#uniqueness-pattern)). Same end-of-validation timing caveat as `count eq/gt/lt`. |
| `sum(VALUE)` | Sums a related numeric property across matching objects. |
| `calc(EXPR)` | Date/number calculation, e.g. `calc([SYSTEM:DATETIME]+24h)`. Units: `Y M d h m s`. Uses the **server's** OS decimal separator for numeric math — a `,` instead of `.` silently miscalculates on most systems. |

## Bracket substitution tokens

`[KIND:Attribute]` or `[KIND>relation>Type:Attribute]`, used inside a compare
value or message:

| Token | Meaning |
|---|---|
| `[SYSTEM:DATETIME]` / `[SYSTEM:DATE]` | Teamcenter session date/time. |
| `[VAL_OBJECT:Attr]` | A property of the object currently being validated. Supports BOM/relation navigation: `[VAL_OBJECT-1:Attr]` / `[VAL_OBJECT+1:Attr]` (prev/next BOM line), `[VAL_OBJECT\|first:Attr]` / `[VAL_OBJECT\|last:Attr]`, `[VAL_OBJECT<view<TOP:Attr]` (parent line), `[VAL_OBJECT>relation>Type:Attr]`. |
| `[VAL_RELATED_OBJECT:Attr]` | A property of the related object found via the check's own relation. Supports `[VAL_RELATED_OBJECT>relation>Type:Attr]`. |
| `[root:Type:Attr]` | A property from the root object of the structure. Cannot combine with `VAL_OBJECT` or `QUERY`; only works within one structure. |
| `[noroot:Type:Attr]` | A property from a non-root object. Same restriction. |
| `[main:Type:Attr]` | A property from a main object (selected/BOM-expanded), ignoring related objects. |
| `[related:Type:Attr]` | A property from a related object, ignoring main objects. |
| `[PARENT:property]` | Inside a sub-query filter (QUERY dataset), a property of the parent object being expanded. |

## Line-leading modifiers

Prefix a whole CHECK line (before the object/property):

| Modifier | Meaning |
|---|---|
| `root:` | Run only on the selected root object(s). |
| `noroot:` | Run only on non-root objects. |
| `main:` | Run only on main objects (not relation-expanded). |
| `related:` | Run only on objects reached via a relation. |

## Message-prefix severities

The fail-message (2nd `~`-segment) controls how a failing check is reported —
this is NOT a separate keyword field, just a text prefix convention:

| Prefix | Effect |
|---|---|
| *(none)* | Hard failure — blocks Post Actions for the success case. |
| `WARNING:` | Non-blocking — Post Actions for success still run. |
| `CRITICAL:` | Blocking but dismissible — user gets a pop-up they can accept through. |
| `AUTO_FILL:value` | Not a failure at all — triggers the AutoFill extension to write `value` into the property (separately licensed feature; see manual 17.4.10 / 12). |
