# SPEC: Expand intent taxonomy from 4 to 12 with scope-aware routing

Author: AV (via Claude Code)
Date: 2026-04-22 (same calendar day as the handoff spec, separate
session started at 14:41 CDT)
Scope: Grow the classifier's intent taxonomy so it recognises shop-
domain commands beyond the four Phase 1 intents, without building the
backend for each. Future-phase intents are logged and acknowledged so
we learn real usage priorities before committing to module builds.

## Context

The earlier 2026-04-22 spec ("Prototype handoff changes") is now
shipped (commits `99c5bfe`, `0b6d847`, `f912386`). This is a follow-up
spec triggered by the brother-pilot scope review: the ShopSaathi PRD
(`../ShopSaarthi/ShopSaathi_PRD.md`) envisions 9 operational modules,
but Phase 1 of ShopSaarthi Voice Agent only covers four. Testing with
only four would systematically miss how a real shopkeeper speaks.

Two paths were weighed. Full-PRD build is out of Phase 1 scope
(~10-week React Native + Node.js + Postgres effort per the PRD's own
build sequence). Middle path — expand listening without expanding
acting — was chosen so the bot can recognise shop-domain commands
from day one while we learn which modules to build next from real
usage rather than PRD assumption.

The four interview answers from AV that frame this spec:

1. Taxonomy: compact (12 total), not granular splits.
2. Future-phase user feedback: specific echo — "Aapne {category}
   poocha, abhi ye feature build ho raha hai, note kar liya".
3. Multi-intent (in-scope + future-phase in one command): act on
   in-scope portion, acknowledge future portion separately.
4. Logging: new `FuturePhaseLog` SQLite table; aggregate for priority.

## Goal

At the end of this session:

- The classifier recognises 12 intent categories, not 4.
- Each classification carries an explicit `scope` field so the router
  does not have to match on intent strings.
- Future-phase commands are logged to a structured table with enough
  context (intent, transcript, confidence, extracted slots) that a
  two-week pilot produces a usage histogram — the input for the next
  module-build prioritisation.
- The existing four intents (`message, reminder, delegate, call`)
  behave exactly as before. No regression on the 31/32 baseline in
  `tests/test_classify.py`.
- `bhaiya` and Yogesh both get this build; the pilot is the same
  binary with different enrolled users.

## Out of scope

- Implementing any backend for `order`, `collection`, `supplier_payment`,
  `inventory`, `price_check`, `worker`, `summary` intents. Only
  recognition and logging.
- Contact-list context injection into the classifier prompt. Still
  deferred; will ship after bhaiya supplies his contact list (see
  `BROTHER_PILOT.md`).
- Telegram UX for viewing `FuturePhaseLog` aggregates. A later admin
  command once enough data accumulates.
- MESSAGE-prompt iteration from `SPEC_NEXT_SESSION.md`. Still
  deferred.
- WhatsApp API integration, call recording, Exotel — these are
  PRD-scope items, not this session.

## The 12-intent taxonomy

| Intent | Scope | What it covers | Example (Hinglish) |
|---|---|---|---|
| `message` | in_scope | send a WhatsApp/SMS to a person | "Rajesh ko WhatsApp karo, kal delivery aayegi" |
| `reminder` | in_scope | set a self-reminder at a time | "3 baje yaad dilana Rajesh ko call karna hai" |
| `delegate` | in_scope | tell someone to do a task | "Ramu ko bolo Praveen ko call kare" |
| `call` | in_scope | place a phone call | "Accountant ji ko call karo abhi" |
| `order` | future_phase | customer/supplier orders — inquiry, status, update | "Sharma ji ko 50 bori cement ka order karo" / "Rajesh ke order ka status kya hai" |
| `collection` | future_phase | customer payments owed to bhaiya | "Rajesh ka kitna pending hai", "Kisne paisa dena hai aaj" |
| `supplier_payment` | future_phase | what bhaiya owes suppliers | "Sharma ji ko kitna dena hai", "Aaj supplier payment kya hai" |
| `inventory` | future_phase | stock queries and updates | "Cement kitna bacha hai", "10 bori cement aayi hai" |
| `price_check` | future_phase | supplier/market rates | "Aaj gitti ka rate kya chal raha hai" |
| `worker` | future_phase | worker status beyond delegate | "Ramu kahan hai abhi", "Chhotu abhi tak nahi aaya" |
| `summary` | future_phase | daily/weekly business overview | "Aaj kitna business hua", "Haftey ka total kya hai" |
| `unknown` | unknown | doesn't match any category | "Namaste, kya haal hai" |

## Schema changes

### `IntentClassification` (`app/services/classify.py`)

Change `intent` from free-text `str` to `Literal` over the 12 values
above. Gemini's Schema dialect accepts `enum`, which Pydantic emits
for `Literal` types, so the schema cleaner does not need changes.
Making it a Literal also nudges the model toward picking from the
known set rather than inventing.

Add a new field:

```python
scope: Literal["in_scope", "future_phase", "unknown"] = Field(
    default="in_scope",
    description="Whether the handler can fulfill this intent today..."
)
```

The prompt will map each intent to its scope, and the model is told
to emit the scope explicitly (redundant with the intent value, but
redundant signals are cheap and catch model drift).

Everything else on `IntentClassification` is kept as-is. `message_body`,
`reminder_text`, `task_description`, `scheduled_time`, `recipient_name`,
`channel`, `followup_check`, `confidence`, `clarification_needed` —
all preserved. Future-phase intents may populate `message_body` or
`task_description` loosely ("cement stock" as task_description on an
`inventory` command) — this is fine for v1; we will tighten if
aggregates are noisy.

### `SYSTEM_PROMPT` (`app/services/classify.py`)

Grow the prompt with seven new sections — one per future-phase intent
— each with the same shape:

```
INTENT_NAME: one-line what it is
Examples:
- "<Hindi/Hinglish example 1>"
- "<Hindi/Hinglish example 2>"
Output: intent=INTENT_NAME, scope=future_phase, recipient_name=<if named>, ...
```

Keep examples minimal (1-2 per category) so the prompt doesn't
balloon. Total new prompt addition estimated at ~40 lines.

Add a new rule in "Important rules":

> Always set `scope` to match the intent: `message`, `reminder`,
> `delegate`, `call` → `in_scope`. `order`, `collection`,
> `supplier_payment`, `inventory`, `price_check`, `worker`, `summary`
> → `future_phase`. `unknown` → `unknown`.

### `FuturePhaseLog` (`app/db/models.py`)

New table:

```python
class FuturePhaseLog(Base):
    __tablename__ = "future_phase_logs"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    transcript = Column(Text, nullable=False)
    intent = Column(String(32), nullable=False, index=True)
    scope = Column(String(16), nullable=False)
    confidence = Column(Float, nullable=True)
    recipient_name = Column(String(128), nullable=True)
    extracted_slots = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
```

Indexed on `user_id`, `intent`, and `created_at` so "top intents for
bhaiya in the last 7 days" is a cheap query. `extracted_slots` carries
the full IntentClassification dict for whatever slots the model filled,
so we can inspect retrospectively.

### `app/db/init_db.py`

No code change expected — `Base.metadata.create_all(engine)` picks up
new models. Verify this empirically after implementation.

## Router changes

### `app/handlers/voice.py`

Current behaviour: `handle_voice_message` calls `classify_intent`,
checks `confidence < 0.5 or intent == "unknown"` for clarification,
then routes to a handler dict:

```python
handlers = {
    "message": handle_message_intent,
    "reminder": handle_reminder_intent,
    "delegate": handle_delegate_intent,
    "call": handle_call_intent,
}
handler = handlers.get(intent.intent)
```

New behaviour:

```python
if intent.scope == "unknown" or intent.confidence < 0.5:
    <existing clarification path>

elif intent.scope == "in_scope":
    <existing routing to handler dict>

elif intent.scope == "future_phase":
    <log to FuturePhaseLog>
    <reply with specific echo>
```

Multi-intent handling: not currently supported by the schema (intent
is a single value). The primary intent determines the path. If the
primary is `in_scope` and the model noticed a secondary future-phase
action, it should surface that in `clarification_needed` for now. A
future schema change could add a real `secondary_intent` field, but
this session keeps the intent cardinality as-is.

Future-phase echo template (Hinglish):

```
"Aapne {intent_label_hindi} poocha. Abhi ye feature build ho raha hai,
note kar liya. {specific_slot_echo_if_any}"
```

Where `intent_label_hindi` is a small mapping table in Python (e.g.
`inventory` → "stock check", `price_check` → "rate check",
`collection` → "customer payment", etc.) and
`specific_slot_echo_if_any` is populated if the model extracted a
recipient or product.

### `app/main.py`

The `IntentClassification(**pending)` reconstruction at `main.py:127`
in the contact-disambiguation callback needs to tolerate the new
`scope` field. Pydantic will accept the extra key and use the default
if missing. Verify in implementation.

## Test coverage

`tests/test_classify.py` gets 14 new cases — 2 per future-phase
intent category — following the existing test-case dict shape.
Assertions:

- Intent hard-assert (existing).
- `scope` hard-assert against expected (`future_phase` for all new
  cases).
- Body-field loose-assert stays as-is; new intents should mostly
  populate `task_description` with the essence of what was asked,
  not required.

Acceptance before merge:

- Existing 32 cases: ≥31/32 correct intent (current baseline).
- New 14 cases: ≥12/14 correct intent.
- All cases: `scope` matches expected.
- `tests/test_schema_cleaner.py` passes (hook-enforced).

If new-case accuracy is below the bar, iterate on prompt examples
once before merging. If existing regresses, the prompt expansion is
too aggressive and we trim examples.

## Documentation updates

- `CLAUDE.md`: update "Current pipeline choices" to list the 12
  intents and mention the future_phase routing pattern.
- `BROTHER_PILOT.md`: update the "What the bot does today" section
  to reflect expanded listening + logging.
- `HANDOVER.md`: brief note that Yogesh also gets the expanded
  scope (same binary).
- `SCHEMA_NOTES.md`: log any friction encountered during
  implementation (there will be some — Literal+Gemini, prompt size,
  accuracy tradeoffs).
- `SESSION_NOTES_2026-04-22_intent_expansion.md`: running timestamped
  log of this session.

## Commit plan

Two commits, same code/docs split as the earlier handoff work:

1. **Code**: classify.py, models.py, voice.py, main.py (if needed),
   tests/test_classify.py.
2. **Docs**: SPEC.md (this file), CLAUDE.md, BROTHER_PILOT.md,
   HANDOVER.md, SCHEMA_NOTES.md, SESSION_NOTES_2026-04-22_intent_expansion.md.

Push to `origin/main`.

## Rollback

If new-case accuracy is catastrophic (< 50%) or old-case regresses
below 28/32, revert the classify.py prompt changes only. Keep the
schema additions and FuturePhaseLog table — they are cheap and
inert. Iterate the prompt in a follow-up session using the same
infrastructure.

## Risks

- **Latency**: longer prompt → slightly slower classifier calls.
  Flash-Lite is fast (median ~1s); expect ~1.2s after expansion.
  Acceptable for voice UX.
- **Accuracy regression on the existing 4**: the model may confuse
  `message` with `order` (both involve talking to a supplier), or
  `reminder` with `summary`. Mitigation: prompt examples keep
  in-scope cases first and most prominent.
- **Over-logging**: if the model defaults to future-phase too
  readily on ambiguous inputs, `FuturePhaseLog` fills with noise.
  Mitigation: the `unknown` path is preserved; ambiguous inputs
  should still go to unknown, not future_phase.
