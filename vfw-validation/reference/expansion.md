# EXPANSION dataset reference

Defines which objects get pulled into the validation structure, and how
(relation, direction, filters). One line per relation. **A JOB can only
reference a single EXPANSION dataset — no comma list** (confirmed by the
manual and observed JOB datasets; the field genuinely
behaves differently from `PROPERTY=`/`CHECK=`, see [query-job-task.md](query-job-task.md)).

## Direction and recursion

```
Item Revision>Iman_Relation>Item Revision      # L2R, recursive (default)
Item Revision>>Iman_Relation>Item Revision     # L2R, root object only (not recursive)
Item Revision<Iman_Specification<Item Revision # R2L, recursive
Item Revision<<Iman_Specification<Item Revision # R2L, root object only
```
`>`/`<` = direction (left-to-right / right-to-left, i.e. which side is the
new/target object). Doubling it (`>>`/`<<`) restricts expansion to the root
object only, and is also how you say "expand only from root" generally
(manual 17.2.15) and "non-recursive" (17.2.16) — same syntax, same effect.

A reference attribute also works as a relation: `ItemRevision>owning_group>Group`.

## Class prefix

`C:TypeName` expands to that class **and every subtype** — e.g.
`C:ItemRevision` matches Part Revision, Document Revision, etc.
`Part Revision>TC_Is_Represented_By>C:Document` expands to all Document
subtypes related to a Part Revision.

## Modifiers (append with `/`)

| Modifier | Effect |
|---|---|
| `/SKIP:Status1,Status2` | Skip expansion of objects with the given (comma-separated, **DB value**) status. `ALL` skips every release status. Works L2R and R2L. |
| `/SKIP_RELATION:RelName1,RelName2` | Skip expansion across the given relation(s). |
| `/ALIAS:Name` | Aliases the **relation** if placed right after the relation name (before the next `>`/`<`); aliases the **type** if placed after the type. Needed whenever the same relation or type is used more than once in EXPANSION with different semantics, so PROPERTY/CHECK can address them unambiguously. The alias is only reachable via the *same* relation chain that defined it — you cannot later reuse the alias name as a shorthand type in an unrelated relation path. |
| `/FILTERNAME` (matches a `~FILTERNAME` sub-query in QUERY) | Restricts the expanded set to what that sub-query's saved query returns. See "Sub-filtering" below. |
| `/FILTERNAME:sortAttr` | Same, but from the filtered candidates keep only the one with the highest `sortAttr` (typically `creation_date` or a date property) — the "give me the latest X matching this filter" pattern. |
| `^FakeRelationName` | Combined with a sub-filter, gives the expanded objects a pseudo-relation name of your choosing (a "fake relation"), so CHECK can address a path shape that doesn't exist as a real TC relation. |

## Special pseudo-relations

| Relation | Meaning |
|---|---|
| `items_tag` | Revision → its Item (either direction). `Item<items_tag<ItemRevision` needs a revision rule or sub-query, otherwise it expands **every** revision of the item. `ItemRevision>items_tag>Item` (get the item) is always safe/unambiguous. |
| `previous_rev` / `next_rev` | Predecessor/successor revision. Optional sort attribute: `previous_rev(item_revision_id)`, `previous_rev(creation_date)`. |
| `latest_rev` | The latest revision of the item. |
| `revision_list` | Item → **all** its revisions (unfiltered) — the common idiom for "all revisions of this item", usually combined with a `/FILTERNAME` sub-query rather than a sort-attribute suffix (e.g. `Item>revision_list/FILTER_Rev_Released>ItemRevision`). Prefer this over `items_tag` R2L for item→revisions traversal. |
| `where_used` / `where_used_configured` | Find assemblies that use this object. The check itself can then run either on the component or the assembly — see [check.md](check.md#where-used). |
| `where_referenced` / `where_referenced_pom` | Like `where_used`, for GRM/POM references instead of BOM usage. |

## Sub-filtering (sub-queries)

A `~Name` block in QUERY, referenced from EXPANSION as `/Name`:

```
EXPANSION:
Item Revision>Iman_Relation/FILTER>Item Revision

QUERY:
~FILTER
Item Revision...
Rev ID=001
```

Add `:sortAttr` after the filter name to reduce a multi-match filtered set
down to a single "latest" object by that attribute (manual 17.2.9):

```
Item<items_tag/FILTER_IRev:date_released<ItemRevision
```

Sub-query criteria can reference the object's own property or its parent's,
using `[PARENT:property]`:

```
ItemRevision>IMAN_references/FilterByName:Name|[object_name]>ItemRevision
ItemRevision>TC_Attaches/FILTER_Rev:creation_date<ItemRevision
ItemRevision>IMAN_references/FilterByName:Name|[PARENT:object_name]>ItemRevision
```

## BOM view expansion

```
C:ItemRevision>view;p:Latest by Creation Date>C:ItemRevision
```
`view` is the BOM relation; the segment after `;` before `:` controls packing
and level, the segment after `:` is the revision rule name (or one of the
special values below).

| `;` segment | Meaning |
|---|---|
| `p` | Packed BOM. |
| `u` | Unpacked BOM. |
| `0` (as a level, or after the secondary type: `>C:ItemRevision;0`) | Extract BOM-line attributes only — no further recursive expansion via EXPANSION. |
| `N` (e.g. `10`) | Max recursion depth N. `0` or `ALL` = fully recursive. |
| `TOP` | Also extract the top BOM line's own data. |
| `ALL_CHILDREN` | Also extract non-ItemRevision/Item children (e.g. Forms). |
| `BOP` | Bill of Process view instead of the regular BOM view. |
| `:add_substitutes` (suffix on the revision-rule segment) | Also extract BOM substitutes. |

Revision-rule segment special values: `DEFAULT_REVISION_RULE` (from the
`TC_config_rule_name` preference), `ACTIVE_REVISION_RULE` (current client
session config), `ACTIVE_BOM_WINDOW` (current client's open BOM window,
packed setting included).

Root-only BOM expansion uses the same `>>` doubling as any other relation:
`C:ItemRevision>>view;p:...>C:ItemRevision;0`.

Multi-level BOM (checks run separately per sub-assembly) uses `|` before the
first `>`: `PartRevision|>EngineeringView:Any Status; Working>PartRevision`.

Further BOM-specific modifiers (all placed the same way as the general
`/ALIAS:`/`/SKIP:` modifiers above, appended to the revision-rule segment):

| Modifier | Effect |
|---|---|
| `/FILTERNAME` | Sub-query filter, same mechanism as general sub-filtering. |
| `/SKIP:Status1,Status2` | Skip BOM lines already at the given status (`ALL` = any status). |
| `/SKIP_EXPANSION:Status` | Still include the BOM line itself, but skip expanding *into* its ItemRevision when at the given status. |
| `/CLOSURE_RULE:Name` | Filter via a Teamcenter Closure Rule (must be registered in the `ClosureRulesForBomExpansion` preference). |
| `/PHANTOM:ItemType` | Only process the BOM under lines whose item type matches the given Phantom type. |
| `/VARIANT_RULE:Name` | Expand per a variant rule. |
| `/ALIAS:Name` | As above — needed whenever more than one BOM view is expanded in the same JOB. |

## Classification, folders, users/groups, tasks, projects, saved/user-exit queries

These all follow the same `Primary>relation>Secondary` shape as any other
relation; the ones seen in practice:

```
C:ItemRevision>>IMAN_classification>icm0                 # classification (see PROPERTY too)
C:ItemRevision>active_groupmember>GroupMember             # active session group/role
GroupMember>group>Group
C:ItemRevision>owning_group>Group
```
For folder content, active user/group/role, workflow task, project members,
saved-query-driven expansion, and user-exit-query expansion, search the
manual chapter 17.2.21–17.2.28 by name — these are used rarely enough that
copying a working example from an existing `*_EXPANSION.txt` in the target
project is more reliable than working from memory.
