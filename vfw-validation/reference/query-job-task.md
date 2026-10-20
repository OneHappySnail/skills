# QUERY / JOB / TASK dataset reference

## QUERY

Finds the root objects (main query) and/or supplies sub-query filters used
from EXPANSION.

```
# main query: an existing Teamcenter Saved Query name, then its criteria
Item...
Item ID=Metric

# a variable, with an optional default after the comma
Item Revision...
Item ID=$ItemId,*

# multiple main queries: results are unioned (batch/ITK use only, not the
# interactive client)
Item...
Item ID=Metric
Item...
Item ID=Inch

# sub-query, referenced from EXPANSION as /FILTER_Rev
~FILTER_Rev
Item Revision...
Type=*
```
A sub-query name (`~Name`) can also point at a **custom/registered saved
query** rather than criteria for a generic one, e.g. `__CNO_BOM_FILTER`,
`__ACTIVE_group_members`, or a site-specific `__<Name>` query installed on
the Teamcenter server — these behave like opaque, pre-built filters and
their exact parameter set has to be discovered from how they're already
used elsewhere in the same project's QUERY dataset, not from this manual.

**A JOB can only reference a single QUERY dataset — no comma list** (see
JOB below).

## JOB

Combines EXPANSION/PROPERTY/CHECK/QUERY (+ optional TASK/SCRIPT) for one
operation, and is what an AW panel/RAC command/workflow handler actually
invokes.

```
QUERY=CNO_VFW_ITEM_QUERY
EXPANSION=CNO_VFW_ITEM_EXPANSION
PROPERTY=CNO_VFW_ITEM_PROPERTY
CHECK=CNO_VFW_ITEM_RELEASE_CHECK
TASK=CNO_VFW_ITEM_RELEASE_TASK
SCRIPT=CNO_VFW_SCRIPT
```

| Field | Multiple datasets (comma-separated)? |
|---|---|
| `QUERY=` | **No.** |
| `EXPANSION=` | **No.** |
| `PROPERTY=` | Yes: `PROPERTY=CNO_1_PROPERTY,CNO_2_PROPERTY`. |
| `CHECK=` | Yes: `CHECK=CNO_1_CHECK,CNO_2_CHECK`. |
| `TASK=` | Yes — observed deployments and one manual example both show it, despite an unrelated manual paragraph claiming otherwise; treat that paragraph as an error. |
| `SCRIPT=` | Yes — manual explicitly shows `SCRIPT=CNO_VFW_EXTERNAL_SCRIPT, CNO_VFW_SCRIPT`. |

Each `PROPERTY=`/`CHECK=` list must be declared on a single line, under
1025 characters.

`HELP=` is optional localized HTML help text, one line, `<br/>` for
newlines, `###` between locale blocks:
```
HELP=[en_US={CUSTOM_LOGO=MyLogo}<br><h4>{TC_USERNAME}, ...</h4>]###[de_DE=...]###
```
Placeholders: `{CNO_LOGO}` (vendor logo), `{CUSTOM_LOGO=DatasetName}` (a
custom Image dataset — PNG/JPEG recommended, watch client performance with
large images), `{TC_USERNAME}`, `{TC_GROUP}`, `{TC_ROLE}`.

**Input Variables** let the AW GUI prompt for a value before running the
validation, then use it in EXPANSION/CHECK/TASK as `[$VarName]`. Requires
`INPUT_FIELD=` entries in the JOB dataset (TC restart needed after editing —
cached). For `AUTO_FILL_BOMLINE` specifically, the properties involved must
not use an alias.

## TASK

Post-actions to run once validation completes, gated by object type and
(optionally) validation status.

```
[TASK_LIST]
ID=Item Release
TYPE_LIST=C:ItemRevision,C:Part
VALIDATION_STATUS=OK
ACTION_ID_LIST=ReleaseWorkflowAction
ACTION_OBJECT=ROOT
OPTION=SKIP_IN_WORKFLOW

[ACTION_LIST]
ID=ReleaseWorkflowAction
TYPE=WORKFLOW
TEMPLATE=TCM Release Process
OBJECT_COUNT=1
```

### `[TASK_LIST]` fields

| Field | Meaning |
|---|---|
| `ID` | Task's own ID (shown in the UI). |
| `TYPE_LIST` | Object type(s) the task applies to. |
| `VALIDATION_STATUS` | *(optional)* Gate on validation result: `OK`, `FAILED`, or `AUTO_FILL`. |
| `ACTION_OBJECT` | *(optional, default `ROOT`)* `ROOT` \| `CHILD` (BOM children) \| `ALL` (root+children) \| `RELATED` \| `WORKFLOW` (fires on the validation workflow itself). |
| `ACTION_OBJECT_FILTERS` | *(optional)* Name of an `[ACTION_OBJECT_FILTERS]` block — see [check.md](check.md#action_object_filters). |
| `OPTION` | *(optional)* `SKIP_IN_WORKFLOW` — don't trigger this action when validation runs inside a workflow handler. |
| `CHK_ID_LIST` | *(optional)* Restrict to specific CHECK-dataset IDs. |
| `AUTO_START` | *(optional)* Run automatically without showing the task in the UI, if the status fits. |
| `ACTION_ID_LIST` | The `[ACTION_LIST]` ID(s) this task triggers. |

### `[ACTION_LIST]` types

| `TYPE=` | Key fields |
|---|---|
| `WORKFLOW` | `TEMPLATE=` (workflow template name), `OBJECT_COUNT=` (batch size threshold), `SUCCESS_MSG=`, `FAILED_MSG=`. |
| `MAIL` | `SUBJECT=`, `RECEIVER=` (an address, or `OWNING USER`), `BODY=` (supports `TASK:TARGET` placeholder for the failing object list), `FORMAT=` (`TEXT`/`HTML`, external mail only). |
| `SCRIPT` | `SCRIPT=` — an external/embedded script call, e.g. `callErpTransfer([ItemRevision:item_id])`. |
| `SET_VALUE` | `PROPERTY=`, `VALUE=` — writes a property on success. |
| `AUTO_FILL` | No extra fields — runs the AutoFill extension for objects whose validation status is `AUTO_FILL`. |
| `SAVE_RESULT` | `SAVE_DATASET_NAME=`, `SAVE_DATASET_TYPE=`, `IS_BINARY_DATASET=`, `SAVE_NAMED_REFERENCE=`, `SAVE_RELATION_TYPE=`, optional `SAVE_DATASET_PROPERTIES=`, `SAVE_NAMED_REFERENCE_NAME=`. |
| `SAVE_REPORT` | Same shape as `SAVE_RESULT`, for the report dataset. |
| `REVISE` | No extra fields — revises the object. |
| `SAVEAS` | No extra fields — save-as's the object. |
| `AUTO_FILL_BOMLINE` | AutoFill on BOM-line attributes (`TYPE_LIST=C:PSOccurrenceThread`, `VALIDATION_STATUS=AUTO_FILL`). |
| `BOMLINE_ADD` / `BOMLINE_REMOVE` / `BOMLINE_REPLACE` | Add/remove/replace a BOM line by UID. |

`[TASK_LIST]` can list several `ID=` blocks (one per task) in the same
dataset, each pointing at its own `ACTION_ID_LIST`; `[ACTION_LIST]` likewise
lists several `ID=` action blocks below it.
