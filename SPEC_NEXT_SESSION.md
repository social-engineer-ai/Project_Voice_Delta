# SPEC: Split `content` into intent-scoped fields

Author: AV (via Claude Code)
Date: 2026-04-18
Scope: Address the highest-impact schema friction observed in the
2026-04-18 post-fix harness run. This spec owns one change only: retire
the overloaded `content` field in `IntentClassification` and replace it
with three intent-scoped fields.

## Problem statement

After the Gemini response_schema fix landed (commit 90c9e6c), the
evaluation harness produced its first real numbers: 31/32 overall
(96.9%), every core intent at 100%. The intent label is solid.

Field-level extraction is not. The single biggest gap is `content`:

- 0 of 15 message and delegate cases populated `content`.
- The only non-null `content` in the entire run was one reminder case.
- Downstream handlers (`message.py`, `delegate.py`, `reminder.py`) all
  read `intent.content` and bail out with a clarification prompt when
  it is None, so today's classifier returns would cause the bot to ask
  "kya message bhejna hai?" on every real utterance, even when the
  transcription clearly carries a body.

Root cause is in the schema, not the prompt. The field description at
`app/services/classify.py:44-47` tries to cover three distinct purposes
in one slot:

> "The message body, reminder text, or task description. For 'call', null."

The model has no clear mental model for when to fill it, and treats it
as optional metadata. The fix is to give each intent a named field with
a tight, single-purpose description.

This was logged as the first of six new entries in `SCHEMA_NOTES.md` on
2026-04-18. The other five entries remain out of scope for this session.

## Goal

After this session, `IntentClassification` exposes `message_body`,
`reminder_text`, and `task_description` instead of `content`. The
harness and all three consuming handlers are updated. Accuracy on the
intent label holds at or above the 96.9% baseline, and the three new
fields are populated on the cases where they should be.

## Out of scope

- The other five schema-friction entries from `SCHEMA_NOTES.md` dated
  2026-04-18 (scheduled_time format drift, followup_check being dead,
  the multi-intent collapse generalization, ambiguity having no
  structured representation, channel never being extracted). Each of
  those is its own future session.
- Voice verification, enrollment, or any handler change beyond the
  `content` rename.
- Retroactively re-processing stored intents in the database. No prior
  `UserCommand` records exist in the field test yet, so no migration
  is required today; if the db contains rows, flag and stop.
- Confidence-threshold reconciliation (the other 2026-04-18 entry in
  `SCHEMA_NOTES.md`). Still deferred.

## Changes in `app/services/classify.py`

### Pydantic model

Remove the single `content` field. Add three Optional fields in its
place:

```python
message_body: str | None = Field(
    default=None,
    description="For 'message' intent only: the text to send to the recipient, as spoken. Null for every other intent.",
)
reminder_text: str | None = Field(
    default=None,
    description="For 'reminder' intent only: what the shopkeeper wants to be reminded about. Null for every other intent.",
)
task_description: str | None = Field(
    default=None,
    description="For 'delegate' intent only: the task the recipient is being asked to do, as spoken. Null for every other intent.",
)
```

Tight per-intent descriptions matter; the empirical observation is that
the union-field description was the failure mode, so the replacement
descriptions must leave zero ambiguity about which intent fills which
field.

### System prompt

In the SYSTEM_PROMPT constant, update the per-intent output lines to
name the new fields:

- MESSAGE: `intent=message, recipient_name, channel, message_body`
- REMINDER: `intent=reminder, reminder_text, scheduled_time, recipient_name`
- DELEGATE: `intent=delegate, recipient_name, task_description, followup_check`
- CALL: unchanged (no body field applies)

Add one new rule under "Important rules":

> "Populate exactly one of message_body, reminder_text, task_description
> based on the intent. The other two must be null. For 'call' and
> 'unknown', all three must be null."

Keep the rest of the prompt untouched. In particular, leave
`followup_check`, `scheduled_time`, `channel`, and `clarification_needed`
alone; those are separate SCHEMA_NOTES entries.

### Fallback path

The `except` block in `classify_intent()` constructs a fallback
`IntentClassification`. It does not set `content` today, so the rename
needs no change there.

## Downstream handlers

Three handlers read `intent.content` and must switch to the new
intent-specific field:

- `app/handlers/message.py` lines 47, 84, 87, 100, 113 → `intent.message_body`
- `app/handlers/delegate.py` lines 41, 71, 81, 93, 114 → `intent.task_description`
- `app/handlers/reminder.py` lines 105, 130, 144, 150 → `intent.reminder_text`

The diagnostic log line at `app/handlers/voice.py:133-134` also reads
`intent.content`. Replace with a line that reports whichever of the
three new fields is non-null (or all three if more than one is set, as
a diagnostic for detecting intent-field mismatches).

Each handler's "missing body" guard (e.g., `if not intent.content`)
switches to checking the field for that handler's intent. No behavior
change beyond the field rename.

## Test harness expectations (`tests/test_classify.py`)

Post-change, the harness should be aware of the three new fields.
Concretely:

1. Per-case stdout line: replace `content=...` (today the harness does
   not print content, it only prints intent/recipient/sched) with a
   compact indicator of which of the three body fields was populated,
   e.g. `body=message_body:"…"` or `body=none`.
2. Per-case JSON record in `tests/last_run.json`: already emits the
   full actual schema via `result.model_dump()`, so the new fields
   will appear automatically. No change needed to the rollup code.
3. Add a loose assertion per case, reported but not gated (consistent
   with the existing convention for recipient): for cases with
   `expected_intent` in `{"message", "delegate", "reminder"}`, verify
   that the corresponding intent-specific field is non-null and
   non-empty. Record the pass/fail on each case in the JSON under
   `body_passed` (mirroring `recipient_passed`).
4. New stdout block after the per-category rollup: `Body fields
   populated:` with rows for each of message/delegate/reminder showing
   `populated / total (%)`. Today's baseline is 0/5, 0/5, 1/12. After
   the fix the numbers should climb toward 5/5, 5/5, 12/12.

Do not add a hard gate. Accuracy and population rates are reported,
not enforced, matching the existing harness policy.

No new test cases are required for this SPEC. The existing 32 cover
the matrix well enough to detect regression.

## Verification

Run in order:

1. `python -m tests.test_schema_cleaner` passes. The cleaner change is
   trivial (field count shifts from 8 to 10) but the assertion should
   still hold.
2. `python -m tests.test_classify` runs to completion. Intent accuracy
   does not regress below 96.9% (31/32). If it does, do not close the
   session; investigate whether the new field descriptions are
   confusing the model. The earlier baseline (commit 90c9e6c) is the
   comparison point.
3. `tests/last_run.json` shows:
   - `message_body` non-null on at least 4 of 5 message cases
   - `task_description` non-null on at least 4 of 5 delegate cases
   - `reminder_text` non-null on at least 10 of 12 reminder cases
   - Exactly one of the three body fields non-null per case where the
     expected intent is message/delegate/reminder (no spillover).
4. Manual smoke test: run one `classify_intent()` call against each of
   three utterances (one message, one delegate, one reminder) and
   confirm the right field lights up and the other two are null. This
   is a belt-and-braces check on top of the harness.
5. Handlers import cleanly: `python -c "from app.handlers import message, delegate, reminder"` returns without error.

If steps 1-3 pass, commit with a message that names the renamed field,
reports the populated-count deltas (before/after), and cross-references
`SCHEMA_NOTES.md` entry dated 2026-04-18 "content field systematically
underfilled…" so future readers can trace the decision.

If step 3 shows spillover (e.g., `message_body` populated on a delegate
case), log it as a new `SCHEMA_NOTES.md` entry and leave the fix to a
later session. Do not expand scope mid-session.

## Files touched

- `app/services/classify.py` (modified: Pydantic model + SYSTEM_PROMPT)
- `app/handlers/message.py` (modified: `content` → `message_body`)
- `app/handlers/delegate.py` (modified: `content` → `task_description`)
- `app/handlers/reminder.py` (modified: `content` → `reminder_text`)
- `app/handlers/voice.py` (modified: diagnostic log line)
- `tests/test_classify.py` (modified: stdout body indicator, loose
  assertion, body-populated rollup)
- `SCHEMA_NOTES.md` (optional: close out the "content underfilled"
  entry with a `resolved 2026-XX-XX` note once verification passes)

No changes to `SPEC.md`, the database schema, voice verification, or
any other service.
