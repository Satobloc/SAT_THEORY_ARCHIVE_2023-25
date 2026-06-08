# Archive Admin Task Schema Guide

Status: provisional / needs review

Primary request file:

```text
.[⚙️_AI_FILES]/REQUESTS/archive_admin_task.txt
```

Fallback request file:

```text
..[🎛️_NATHAN_DASH]/⚒️_ADMIN_TASK.txt
```

Workflow:

1. Put one or more TASK blocks in the AI-side request file.
2. Run Archive Admin or wait for the workflow.
3. Check `.[⚙️_AI_FILES]/LOGS/workflows/archive_admin_last_run.txt`.
4. Open the linked log in `.[⚙️_AI_FILES]/LOGS/archive_admin/`.
5. Confirm request source, task name, target, and output.
6. Reset the request file to idle after success.

Archive Admin is asynchronous. Always verify the current log before assuming a request has run.

## INDEX_FOLDER

```text
TASK: INDEX_FOLDER
TARGET: <folder path>
MAX_DEPTH: <integer, optional>
MAX_ENTRIES: <integer, optional>
INCLUDE_CONTROL_FOLDERS: YES   # optional
INCLUDE_GENERATED_INDEXES: YES # optional
```

Use `TARGET`, not `FOLDER`.

If `MAX_DEPTH` is omitted, the tool chooses a random depth from 2 to 5 and logs the value used. If `MAX_ENTRIES` is omitted, the tool chooses a random limit from 500 to 700 and logs the value used.

## WRITE_AI_FILE

```text
TASK: WRITE_AI_FILE
FILE: <path relative to .[⚙️_AI_FILES]>
TEXT:
<content>
ENDTEXT
```

Writes/replaces a file inside the AI control folder.

## APPEND_AI_FILE

```text
TASK: APPEND_AI_FILE
FILE: <path relative to .[⚙️_AI_FILES]>
TEXT:
<content>
ENDTEXT
```

Use for Watercooler notes, resource catalog notes, and other append-only AI-side documents.

## APPEND_DASH_FILE

```text
TASK: APPEND_DASH_FILE
FILE: ⚙️_LESSONS_LEARNED.txt
TEXT:
DATE:
PROBLEM:
CAUSE:
SOLUTION:
APPLIES TO:
NOTES:
ENDTEXT
```

Only approved dashboard files can be appended. Keep Nathan’s dashboard uncluttered.

## Recommended request identity

```text
# REQUEST_ID: 2026-06-08_short_description_001
# REQUEST_PURPOSE: One sentence.
```

Future tooling should echo request ID, request-source SHA, task status, targets, and output paths.

## PDF extraction note

The dry run found the live PDF extraction workflow watches:

```text
_AI_REQUESTS/pdf_extract_request.json
```

and writes to:

```text
_AUTO_EXTRACTED_TEXT/
```

This is currently a known migration mismatch with the newer AI-folder request architecture.
