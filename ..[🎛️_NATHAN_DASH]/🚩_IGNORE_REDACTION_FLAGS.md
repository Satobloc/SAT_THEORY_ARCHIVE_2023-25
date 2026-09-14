# 🚩 Ignore / Redaction / Downgrade Flags

**Purpose:** audit queue for explicit Nathan instructions that override the standing additive-tagging rule.

Standing rule elsewhere: **if you read it, you tag it; tags/status are additive and are not downgraded.**

Use this file only when Nathan explicitly asks that something be ignored, redacted, suppressed, or downgraded for a reason. Do not infer such a request from obsolescence, contradiction, later correction, tone, or current theory status.

## Flag schema

### YYYY-MM-DD — <short flag heading>

- **Requested by:** Nathan
- **Request type:** `IGNORE` / `REDACT` / `SUPPRESS` / `DOWNGRADE` / other explicit instruction
- **Affected repository/source:** `<exact path>`
- **Affected message/item IDs:** `<IDs where available>`
- **Exact scope of requested action:** `<what Nathan explicitly asked to change>`
- **Reason:** `<Nathan's stated reason, if supplied>`
- **Audit handling:** `<what was changed; avoid reproducing content requested for redaction>`
- **Status:** `OPEN` / `APPLIED` / `RESOLVED`

---

## Open flags

### 2026-09-13 — Archive user-role authorship correction

- **Requested by:** Nathan
- **Request type:** `DOWNGRADE` / provenance correction
- **Affected repository/source:** `Satobloc/HsH/WORKSPACES/COMMON/tagging_ledgers/2026-09-13-Rotations-in-Higher-Dimensions-02.md` and corresponding verified batch
- **Affected message/item IDs:** `6f6bbfe0-6e84-4f08-b282-db40bebc7a85`
- **Exact scope of requested action:** Remove the speculative classification that a `role=user` archive message might not be Nathan-authored merely because it contains survey/template or pasted-looking material. For these archives, user is Nathan; other speakers are assistant or explicitly identified LLMs.
- **Reason:** Nathan explicitly clarified the archive speaker model.
- **Audit handling:** standing policy updated; affected ledger/batch to be corrected while preserving this audit note.
- **Status:** `APPLIED`

### 2026-09-13 — “Concrete sphere” analyst wording rejected

- **Requested by:** Nathan
- **Request type:** `DOWNGRADE`
- **Affected repository/source:** prior tagging-run report language; any future metadata if encountered
- **Affected message/item IDs:** none; phrase was analyst wording rather than a Nathan corpus term
- **Exact scope of requested action:** Do not treat “concrete sphere” as SAT/H(s)H terminology or a tag family.
- **Reason:** Nathan explicitly stated that it is not a thing.
- **Audit handling:** phrase excluded from terminology/tag vocabulary; no corpus tag bearing this name was found in the durable batch ledger.
- **Status:** `APPLIED`

### 2026-09-14 — Kerr / Kelvin / Whirligig current-status correction

- **Requested by:** Nathan
- **Request type:** `DOWNGRADE` / status correction
- **Affected repository/source:** analyst summaries, synthesis/status labels, tags, and future metadata wherever Kerr, Kelvin, Whirligig, or `donut` as a Whirligig synonym are classified as historical rather than current/live H(s)H hypotheses
- **Affected message/item IDs:** current live Nathan correction; exact raw message ID not yet backfilled
- **Exact scope of requested action:** Strip incorrect `historical` status from Kerr, Kelvin, and Whirligig/Donut-as-Whirligig. Treat them as live H(s)H hypotheses. Kerr construction work should be routed through the RAVEL conversation family.
- **Reason:** Nathan explicitly stated these are later conclusions and that the historical classification is reversed.
- **Audit handling:** current status recorded in `Satobloc/HsH/WORKSPACES/COMMON/CURRENT_HSH_HYPOTHESIS_STATUS_2026-09-14.md`; preserve prior misclassification only as audit history, not as current theory status.
- **Status:** `APPLIED`
