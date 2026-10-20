# PROPERTY dataset reference

Declares which properties get extracted from the objects EXPANSION brings
into the structure, with optional alias names. **Supports multiple
comma-separated datasets in a JOB's `PROPERTY=` field** (unlike EXPANSION/QUERY).

## Basic forms

```
Part:item_id                          # raw property name in output XML
Part:item_id~PART_ID                  # aliased: <property name="PART_ID">
Document/xyz4_DocumentClass           # Master Form property (note: "/" not ":")
```

## LOV, multilanguage, table, UID

```
Item Revision:!lov_DeliveryType       # LOV description
Item Revision:?lov_Restriction        # LOV database value
C:ItemRevision:object_desc,en_US~object_desc_en          # multilanguage
C:ItemRevision:object_desc[en_US]~object_desc_en         # equivalent, safer syntax
                                                          # (the "," form can break inside a dynamic
                                                          #  property or script parameter)
PartRevision§PART_UID§|UID|           # extract the object's own UID as a custom property
```
Table properties: expand `Type>tableProperty>RowType` in EXPANSION, then
declare each column as `RowType:columnProp~Alias` in PROPERTY — each row
becomes its own `<object>` node in the output XML linked back by relation.

## Dynamic properties

```
Type§AliasName§|formula|
```
The `§` (not `:`) form defines a computed property from a template of
literal text and `|:property|`/`|UID|`/`|js(...)|` placeholders, e.g.:
```
C:ItemRevision§BOM_REVISION_ID_COMBINATION§|bl_item_item_id|_|bl_rev_item_revision_id|
C:ItemRevision§ItemName§|C:ItemRevision>items_tag>C:Item:object_name|
C:Dataset§need_content§true
```
**Referencing a dynamic property alias in CHECK still uses the normal
`Type:Alias` colon form** in the common case — but some datasets
reference it as `Type§Alias` (matching the PROPERTY-side
separator) instead. If a CHECK line's compare keyword doesn't seem to parse
right, check whether the left-hand side is actually two `§`-joined segments
rather than a `Type:Property` pair — see [check.md](check.md#lhs-can-contain-a-%C2%A7) ("LHS can contain a §").

## Classification (icm0)

```
icm0>*:*                                          # all classes/attrs valid for the object
icm0>CLS_0001:Connectiontype~CONNECTION_TYPE       # specific class + attribute, aliased
icm0>CLS_0001:*                                    # specific class, all its attributes
```

## Relation properties

Extracted from the relation object itself, still declared with `Type` =
the relation name:
```
IMAN_specification:type_string~RelationType
IMAN_specification:primary_object~PrimaryObject
IMAN_specification:secondary_object~SecondaryObject
```
If more than one relation is used on the same object in the same
validation, prefix the alias with `REL_` (manual 17.4.28) so CHECK can tell
them apart.

## Additional / pseudo properties (no PROPERTY declaration needed beyond a class-level line)

These read TC-computed or session state rather than a stored attribute:

| Property | Meaning |
|---|---|
| `bom_children_count:viewtype` | Number of BOM children of a view type (ItemRevision only). |
| `checked_out` / `checked_out_by` | Checkout state / user. |
| `fnd0InProcess` | In an active workflow. |
| `ics_classified` / `ics_subclass_name` | Classification state / class name. |
| `Is_modifiable` | Modifiable by current user. |
| `last_release_status` | Current release status. **Runtime-computed — no DB column**, still needs a PROPERTY line to be extracted, but don't expect it to be usable as raw SQL/query criteria elsewhere. |
| `owning_user` / `owning_group` | Self-explanatory. |
| `where_used` / `where_referenced` / `where_referenced_pom` | Comma-separated `object_string` list of using assemblies/references (ItemRevision only). |
| `read_access` / `write_access` / `change_access` / `import_access` | `yes`/`no` for the current user. |
| `CNO_VFW_JOB_NAME` | Name of the current validation's JOB dataset — only usable via a dynamic property: `Type§JobName§|CNO_VFW_JOB_NAME|`. |

A single class-level line covers every subtype
and every alias reached from it, so you rarely need to redeclare a property
per-alias — `C:ItemRevision:last_release_status~last_release_status` once is
enough for every subtype alias in EXPANSION.

## BOM occurrence attributes

Declared the same way, on the `Type>view:...` path from EXPANSION, e.g.
`C:ItemRevision>view:bl_has_absocc`, `C:ItemRevision>view:bl_is_precise`,
`C:ItemRevision>view:bl_item_item_id`, `C:ItemRevision>view:bl_rev_item_revision_id`.
`bl_quantity` is empty when only 1 part exists; use `bl_real_quantity`
instead if you need it populated in that case too.

## Session / preference / user info

`SESSION_ACTIVE_ROLE`, `SESSION_ACTIVE_GROUP` and similar session tokens are
used as dynamic-property values: `Type§Current Role Name§|SESSION_ACTIVE_ROLE|`.
See manual 17.3.14–17.3.16 for the full session/preference token list if a
check needs one not listed here.
