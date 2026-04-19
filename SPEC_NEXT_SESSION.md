# SPEC: Iterate MESSAGE prompt block to handle Hindi X-karo-Y

Author: AV (via Claude Code)
Date: 2026-04-19
Scope: Close the remaining gap from the 2026-04-19 content-split
session. The split fixed the schema side (10 fields, tight per-intent
descriptions) and lifted delegate body-population to 5/5 and reminder
to 10/12, but message only climbed to 1/5. Root cause is now in the
prompt, not the schema: the MESSAGE block in `SYSTEM_PROMPT`
underspecifies how `message_body` should be extracted from the Hindi
`<recipient> ko <channel> karo, <body>` construction.

## Problem statement

Post-split harness run (2026-04-19) observed:

- `delegate` body population: 5/5 (100%) ✅
- `reminder` body population: 10/12 (83.3%) ✅
- `message` body population: 1/5 (20%) ❌

Four of the five message cases fail. Three follow an identical Hindi
pattern:

- Case 1: "Rajesh ko WhatsApp karo, bolo kal subah 10 baje aa jaaye"
  → body should be "kal subah 10 baje aa jaaye"; got None.
- Case 2: "Supplier ko SMS bhejo, cement ka rate kya hai confirm karo"
  → body should be "cement ka rate kya hai confirm karo"; got None.
- Case 13: "Sharma sahab ko WhatsApp karo, kal milte hain shop par"
  → body should be "kal milte hain shop par"; got None.

The fourth failing case (17, "Rajesh ko message bhejo ki kal aana hai
aur 5 baje yaad bhi dilana") is a separate multi-intent spillover
issue already documented in SCHEMA_NOTES.md under the
"intent-scoped body field spillover on multi-intent message" and
"multi-intent utterances collapse to primary" entries. It is not a
target of this session.

The pattern in cases 1, 2, 13 is `<recipient> ko <channel-verb>,
<body>`. The comma separates the routing clause from the body clause,
but the classifier treats everything after the routing verb as
contextual qualifier and drops the body. The MESSAGE block example
"Rajesh ko WhatsApp karo, kal delivery aayegi" teaches this shape
implicitly, but the per-intent output line does not show the body
being routed into `message_body`.

## Goal

After this session, `message_body` is populated on at least 3 of the
4 failing cases (1, 2, 13, plus optionally 17 if the prompt change
also happens to fix the spillover). Overall harness accuracy holds
at or above 31/32. No regression on delegate (5/5) or reminder
(10/12) body population.

## Out of scope

- Any schema change (SCHEMA_NOTES.md has five open entries; all
  deferred).
- The case-17 multi-intent spillover as its own fix. If the MESSAGE
  block iteration happens to fix it, good; but it is tracked under
  the separate multi-intent-collapse entry and should be resolved
  structurally via a `followup_reminder` slot, not by more prompt
  examples.
- The case-28 ambiguity failure ("Rajesh ko 5 baje bolo"). Separate
  SCHEMA_NOTES entry.
- Any handler change. Handlers already read `intent.message_body` as
  of the content-split commit.

## Changes in `app/services/classify.py`

Edit the MESSAGE block in `SYSTEM_PROMPT` only. Leave DELEGATE,
REMINDER, CALL, and the "Important rules" section untouched.

Two concrete changes:

1. Add two or three additional Hindi X-karo-Y examples to the MESSAGE
   block that explicitly call out body extraction. Suggested:

   - "Rajesh ko WhatsApp karo, kal subah 10 baje aa jaaye"
     → recipient_name="Rajesh", channel="whatsapp",
       message_body="kal subah 10 baje aa jaaye"
   - "Supplier ko SMS bhejo, cement ka rate kya hai confirm karo"
     → recipient_name="supplier", channel="sms",
       message_body="cement ka rate kya hai confirm karo"

   Show the per-example extraction inline, in the same style the
   prompt already uses for its other examples, so the model sees
   "body text after the comma goes into message_body" as a concrete
   demonstration rather than an abstract rule.

2. Tighten the MESSAGE output line from

   `Output: intent=message, recipient_name, channel (if mentioned), message_body`

   to explicitly note where message_body comes from:

   `Output: intent=message, recipient_name, channel (if mentioned),
   message_body (the text the shopkeeper wants delivered, typically
   the clause after the routing verb like "karo" or "bhejo")`

   The parenthetical is the delta; it gives the model a pointer at
   the moment it decides what to put in the field.

Do not touch the field descriptions on `IntentClassification`; those
are already tight.

## Go / no-go criterion

Strict. After the prompt edit, rerun `python -m tests.test_classify`:

- PASS if `message_body` is non-null on at least 3 of 4 previously
  failing message cases (1, 2, 13 required; 17 optional), AND overall
  intent accuracy holds at 31/32, AND `delegate` body population is
  still 5/5, AND `reminder` body population is still at or above
  10/12.
- FAIL otherwise. On fail: `git checkout -- app/services/classify.py`
  to revert the prompt change, append a paragraph to the
  "MESSAGE block doesn't teach Hindi X-karo-Y construction" entry
  in SCHEMA_NOTES.md noting what was tried and what didn't work, and
  stop. Do not iterate further in the same session; the next
  attempt should be scoped as a fresh session with a different
  approach (for example, a few-shot variant or a smaller number of
  higher-salience examples).

## Verification

Run in order:

1. `python -m tests.test_schema_cleaner` (cheap; verifies the hook
   would pass on this edit). This also tests the hook itself fires if
   the schema cleaner is affected.
2. `python -m tests.test_classify` — full harness.
3. Read `tests/last_run.json`, confirm:
   - Case 1 `message_body` non-null and non-empty.
   - Case 2 `message_body` non-null and non-empty.
   - Case 13 `message_body` non-null and non-empty.
   - Case 17 either populated `message_body` (bonus) or still
     spillovers into `task_description` (acceptable; tracked
     elsewhere).
4. If go, commit with a message naming the prompt-block iteration
   and the before/after message body-population (1/5 → X/5).
5. If no-go, revert and document per the criterion above.

## Files touched (if go)

- `app/services/classify.py` (modified: MESSAGE block in SYSTEM_PROMPT)
- `SCHEMA_NOTES.md` (modified: mark the "MESSAGE block doesn't teach"
  entry resolved with the commit hash)

## Files touched (if no-go)

- `SCHEMA_NOTES.md` only (append a failure note to the existing entry;
  prompt change reverted via `git checkout --`)
