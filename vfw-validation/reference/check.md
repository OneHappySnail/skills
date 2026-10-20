# CHECK dataset reference

See [keywords.md](keywords.md) for the compare/value keyword tables and
bracket tokens — this file covers the surrounding line syntax: IDs, scope,
combination, reuse, and common recipes.

## Two line shapes

```
# simple: the whole line is the check expression
C:ItemRevision:LAST STATUS§allowed§Approved||Released~Invalid status~Status is valid

# structured: gives the check an ID, a scope, and a combination role
ID=REV_STATUS_CHECK;scope=object;CRITERIA=AND;CHECK=C:ItemRevision:LAST STATUS§allowed§Approved||Released~Invalid status~Status is valid
```
Structured fields, all optional except `CHECK=` (or `CHECK_ID=`/`CHECK_DATASET=`,
see "Reuse" below): `ID=`, `scope=`, `category=` (free-text, for UI
filtering only), `CRITERIA=`.

## `§` encoding — check before you edit an existing file

The separator is the single character `§` (U+00A7), but its **byte
encoding varies per project/file** — some datasets store it as UTF-8 (2
bytes, `C2 A7`), some as Latin-1/Windows-1252 (1 byte, `A7`). Before adding
a line to an existing CHECK file, check what the file already uses (`file`
on Linux/WSL, or inspect a hex dump) and match it — mixing encodings in one
file corrupts every `§` after the switch point when re-saved.

## Combined checks (AND / OR)

Group check lines under a shared `ID` with the same `CRITERIA`:
```
ID=cno1;CRITERIA=AND;CHECK=ItemRevision:Attribute1§allowed§1~Invalid Attribute value
ID=cno1;CRITERIA=AND;CHECK=ItemRevision:Attribute2§not eq§Review~Invalid Attribute value

ID=cno2;CRITERIA=OR;CHECK=ItemRevision:Source§allowed§2~BOM is required for this value
ID=cno2;CRITERIA=OR;CHECK=ItemRevision:ViewType§exist§View~BOM is required for this value
```

## Condition checks

A `CRITERIA=CONDITION` line under an ID must pass before any `AND`/`OR`
lines with the same ID are evaluated at all:
```
ID=cno4;CRITERIA=CONDITION;CHECK=ItemRevision Master:unit_of_measure§eq§kg||l~PreCondition
ID=cno4;CRITERIA=AND;CHECK=ItemRevision Master:hazard_class§not allowed§-~Test not successful
```
Use this to gate a check to a subtype/alias, or to skip a check for objects
already covered by a different path (the "precise reference is leading"
dedup pattern below).

## Check scope

One scope per `ID` — **mixing scopes under the same ID is not supported**.
Default is `structure`.

| Scope | Granularity |
|---|---|
| `complete` | One result for the entire validation XML (every structure). |
| `structure` (default) | One result per structure. |
| `object` | One result per object, independently — the only scope where `exist`/`count` answer "does at least one match exist for this specific object", rather than an all-must-pass roll-up. |
| `related` | Only the related objects of one object in one structure. |
| `bom` / `bom(level=N)` / `bom(level=N\|up\|down\|complete)` | Within a BOM; level controls how far the condition reaches (default: same BOM view only, `level=0`). `up`=parents only, `down`=children only, `complete`=siblings too. |
| `occurrence` (default for BOM lines) | Occurrence by occurrence, similar to `object` but for BOM. |

`exist` and `count` **only behave meaningfully in `structure` or `object`
scope** (manual 17.4.1 info box) — in other scopes they don't have a
sensible "at least one" answer to give.

## Reuse

**Reuse an ID as a condition** (`CHECK_ID=`, not `CHECK=`) — must be
declared earlier, in the same or an earlier CHECK dataset in the JOB's
`CHECK=` list:
```
ID=CNO-001;CRITERIA=AND;CHECK=C:ItemRevision:object_name§allowed§A*~...~...
ID=CNO-002;CRITERIA=CONDITION;CHECK_ID=CNO-001
ID=CNO-002;CRITERIA=AND;CHECK=C:ItemRevision:object_desc§allowed§B*~...~...
```

**Import an entire check dataset** into another (`CRITERIA=IMPORT`,
`CHECK_DATASET=`) — the importing JOB's EXPANSION/PROPERTY must still cover
everything the imported checks need:
```
ID=200;scope=Structure;CRITERIA=IMPORT;CHECK_DATASET=CNO_VFW_01_CHECK
```

## Root/main/related scoping keywords

`root:`, `noroot:`, `main:`, `related:` prefix a whole line (see
[keywords.md](keywords.md)) — combine with `scope=object` when you need a
per-object result rather than a structure-wide one.

## Uniqueness pattern

The `count(...)` idiom for "no two objects share this combination" (manual
18.4.4, also the usual idiom for BOM position/ItemID uniqueness):
```
PROPERTY:
C:ItemRevision:item_id~ITEM_ID
C:ItemRevision§ItemIdRevIdCombination§|:item_id|_|:item_revision_id|

CHECK:
C:ItemRevision:ItemIdRevIdCombination§eq§count([C:ItemRevision:ITEM_ID]_*)~Relation of multiple Revisions with same Item found
```
Quirky and easy to misuse: per manual 18.4.3 note 2, the `count` result is
computed at the very end of validation against a synthetic non-object node,
so `[VAL_OBJECT:...]` / `[VAL_VALUE]` are **not** available in its message.

## LHS can contain a §

Normally `LHS§KEYWORD§VALUE`, LHS being `Type:Property` — but if LHS
references a *dynamic* property defined in PROPERTY as `Type§Alias§|formula|`,
it may itself be written as `Type§Alias` (using `§`, matching the PROPERTY
declaration) rather than `Type:Alias`. When scanning/parsing a CHECK line by
hand, don't assume the keyword is always the 2nd `§`-segment — find the
segment that's actually a recognised keyword.

## Where used

Expansion and property extraction happen on the `where_used`/`where_used_configured`
relation, but the check itself can run on either side:
```
EXPANSION: C:ItemRevision>where_used>C:ItemRevision
PROPERTY:  C:ItemRevision:last_release_status~LAST_STATUS
CHECK (on the component):
  C:ItemRevision>where_used>C:ItemRevision:LAST_STATUS§allowed§[root:C:ItemRevision:LAST_STATUS]~...
CHECK (on the assembly instead):
  noroot:C:ItemRevision:LAST_STATUS§eq§[VAL_OBJECT<where_used<C:ItemRevision:LAST_STATUS]~...
```

## Related-object / relation-property checks

```
# check based on the relation object's own property, applied to the primary object
EXPANSION: C:ItemRevision>IMAN_specification>C:Dataset
PROPERTY:  IMAN_specification:type_string~RelationType
CHECK:     C:ItemRevision:RelationType§not allowed§Specification

# check based on primary+relation+secondary together
EXPANSION: C:ItemRevision>IMAN_specification>DocumentRevision
PROPERTY:  DocumentRevision:object_desc~DESCRIPTION
CHECK:     C:ItemRevision>IMAN_specification>DocumentRevision:DESCRIPTION§eq§SpecificationText~...
# also works R2L: DocumentRevision<IMAN_specification<C:ItemRevision
```

## Existence / count of related objects

```
# existence, with a CONDITION guard to avoid false-positive object_type mismatch
ID=X;CRITERIA=CONDITION;CHECK=C:ItemRevision:?object_type§exist§PartRevision~Condition: no valid object
ID=X;CRITERIA=AND;CHECK=PartRevision:DesignRelation§exist§*~No Design exists for the Part

# count of related objects, scope=object required
C:ItemRevision>IMAN_specification>C:ItemRevision:IR_name§count lt 4§*~max. 3 objects related
```

## "Precise reference is leading" dedup pattern

When the same secondary object can be reached two ways from the same root
— a precise reference straight to a specific revision, and an imprecise
reference to the item (which then needs its own "does it have a qualifying
revision" resolution) — make the precise path the deciding one and skip the
imprecise path's check for anything the precise path already covered:
```
EXPANSION:
C:ItemRevision>>SomeRel>C:ItemRevision/ALIAS:PreciseRev
C:ItemRevision>>SomeRel>C:Item/ALIAS:RefItem
RefItem>revision_list>C:ItemRevision/ALIAS:RefItemRev

CHECK:
ID=PreciseChk;scope=object;CRITERIA=AND;CHECK=PreciseRev:last_release_status§not allowed§empty~...~...

ID=ItemChk;scope=object;CRITERIA=CONDITION;CHECK=RefItem:item_id§not allowed§[PreciseRev:item_id]~Skipped - precise reference is leading
ID=ItemChk;scope=object;CRITERIA=AND;CHECK=RefItemRev:last_release_status§exist§...~...~...
```
`not allowed§[PreciseRev:item_id]` works because a plain bracket reference
`[Type:Property]` (no `VAL_OBJECT`/`root` prefix) aggregates that property
across **every** matching object in the structure into a list — the same
mechanism the `count([Type:Property]_*)` uniqueness idiom relies on — and
`allowed`/`not allowed` already do list-membership testing natively.
Prefer this over `inlist`/`not inlist` (see [keywords.md](keywords.md)) —
rarely used, while `allowed`/`not allowed` are widely proven.

## ACTION_OBJECT_FILTERS

Gate a TASK's post-action by object properties, independent of the
validation result:
```
PROPERTY:
C:ItemRevision§Current Role Name§|SESSION_ACTIVE_ROLE|
C:ItemRevision:?fnd0InProcess~In Process

TASK:
[TASK_LIST]
ID=Start Workflow
ACTION_OBJECT_FILTERS=DesignReleasedFilter
VALIDATION_STATUS=OK
ACTION_ID_LIST=Start Workflow Action

[ACTION_OBJECT_FILTERS]
ID=DesignReleasedFilter
ACTION_OBJECT=RELATED,CHILD
Type=ItemRevision
|SESSION_ACTIVE_ROLE|=DBA
In Process=FALSE
```
