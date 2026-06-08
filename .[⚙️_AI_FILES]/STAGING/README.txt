STAGING BUFFER

Purpose:
This folder is a buffer for large, multi-part, or reviewable archive requests/resources before they are ingested by Archive Admin or other workflow tools.

Use this area when:
- a request is too large or fragile for direct GitHub editing;
- a resource should be assembled in parts before being moved to a final location;
- a workflow request needs review before execution;
- multiple chunks should be collected before a single run.

Basic lifecycle:
1. INBOX/ — raw incoming material.
2. PARTS/ — chunked or partial files waiting to be assembled.
3. READY/ — reviewed staged requests/resources ready to run or move.
4. RUNNING/ — optional holding area for active staged work.
5. DONE/ — completed staged items or final receipts.
6. FAILED/ — staged items that failed and need diagnosis.

Current status:
Manual staging only. Future Archive Admin tasks may add ASSEMBLE_REQUEST or RUN_STAGED_REQUEST behavior.
