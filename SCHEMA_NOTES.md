# Schema friction log

This file collects cases where the current `IntentClassification` schema in `app/services/classify.py` made it awkward to express expected behavior while writing or maintaining tests. Entries accumulate over sessions; do not regenerate.

The runner does not write to this file. Add entries by hand as you encounter friction. A future session uses this list to scope a focused schema refactor.

## Entry format

Each entry is a small section with:

- date
- category (which test category surfaced it, or "general")
- offending utterance (when applicable)
- friction (what was awkward to express in the current schema)
- suggested direction (one line, optional)

---

## 2026-04-18: confidence threshold inconsistency

- category: general
- offending utterance: n/a
- friction: The system prompt in `app/services/classify.py` instructs the model that "Below 0.7 means the handler will ask for confirmation before acting," but `app/handlers/voice.py:137` actually gates on `confidence < 0.5` (and `app/handlers/voice.py:184` does the same in `handle_text_message`). Two different thresholds in two different places mean the model is being told one rule while the runtime applies another. Tests cannot meaningfully assert confidence behavior until this is reconciled.
- suggested direction: pick one threshold, lift it to `app/config.py` as a setting (e.g., `clarification_confidence_threshold`), reference it in both the prompt and the handler.

## 2026-04-18: BLOCKER — Pydantic schema rejected by Gemini response_schema

- category: general
- offending utterance: every utterance (failure is independent of input)
- error (verbatim): `ValueError: Unknown field for Schema: title`
- raised at: `app/services/classify.py:127-135`, specifically the `genai.GenerativeModel(...)` constructor call where `generation_config["response_schema"]` is set to `IntentClassification.model_json_schema()`. The exception originates client-side inside the `google-generativeai` SDK before any HTTP request is made, so the GEMINI_API_KEY is never exercised and quota is untouched. The exception sits outside `classify_intent`'s own try/except (which only wraps `model.generate_content(...)`), so it propagates to callers. Net effect: `classify_intent()` currently cannot return any real classification.
- friction: Pydantic's `model_json_schema()` emits standard JSON-Schema fields (`title` on the model and on every field, `default`, `$defs`, sometimes `additionalProperties`) that Gemini's stricter `Schema` dialect does not accept. The two schema vocabularies look identical at a glance but diverge on metadata fields.
- suggested direction: write a small `_to_gemini_schema(model_cls)` helper that calls `model_cls.model_json_schema()` then recursively strips disallowed keys (`title`, `default`, `$defs`, `additionalProperties`), inlines any `$ref`, and returns the cleaned dict. Wire it into `classify.py` line 132 in place of the bare `model_json_schema()` call. Add a small unit test that asserts the cleaned schema does not contain any of the disallowed keys. Either approach unblocks the test harness shipped today.
- SPEC.md scope: This fix is explicitly out of scope of `SPEC.md` ("Out of scope: Changes to `app/services/classify.py`"). It is the natural next session and gates real classifier behavior across all categories the new test harness covers.
- discovered: 2026-04-18 during the test_classify rewrite. Reproduced 32 times in a single run.

## 2026-04-18: delegate intent with a time

- category: scheduled_time_iso, role_only_references
- offending utterance: "Driver ko bolo 10 baje site par pahunche"
- friction: The intent is `delegate`, but the utterance carries a time the delegated party is expected to act by. The schema's `scheduled_time` field is documented as reminder-only ("For 'reminder': ISO 8601 time..."), so there is no clean place to put "10 baje" without overloading `content` or misusing `scheduled_time`. The test today only asserts the intent, but a downstream feature that wants to convert "delegate by X time" into a follow-up reminder cannot rely on a structured time field.
- suggested direction: either widen `scheduled_time` to apply to both reminder and delegate (with a separate `time_role` field indicating "due_by" vs "fire_at"), or add a dedicated `task_due_time` field on the schema for delegates.
- update 2026-04-18 (post-fix harness run): the harness empirically confirms this is a broader pattern, not just delegate. See "multi-intent utterances collapse..." entry below for message+reminder and call+reminder cases with the same shape.

---

The following entries were added after the first real end-to-end harness run (2026-04-19T04:09 UTC, 31/32 overall accuracy). They draw on concrete per-case output recorded in `tests/last_run.json` and were observed by reading the run, not by writing new test assertions.

## 2026-04-18: content field systematically underfilled on message and delegate intents

- category: general (spans honorifics, role_only_references, multi_intent_compound, simple_baseline)
- offending utterances (representative):
  - "Supplier ko SMS bhejo, cement ka rate kya hai confirm karo" → content=None (body is "cement ka rate kya hai confirm karo")
  - "Send message to Sharma ji that payment will be done next week" → content=None (body is "payment will be done next week")
  - "Ramu bhaiya ko bolo godown ki chaabi laao" → content=None (task is "godown ki chaabi laao")
  - "Naukar ko bolo dukaan band kare" → content=None (task is "dukaan band kare")
- friction: across 15 message/delegate cases in the run, `content` was populated on zero of them (the only non-null content in the whole run was one reminder). The field description at `app/services/classify.py:44-47` overloads one slot with three distinct purposes ("The message body, reminder text, or task description. For 'call', null.") so the model has no clear signal for when to use it. Downstream handlers will have literally nothing to send or act on.
- suggested direction: split `content` into intent-scoped fields: `message_body: str | None`, `reminder_text: str | None`, `task_description: str | None`. The union-field shape costs almost nothing and gives each intent a named home.
- partially resolved 2026-04-19: split landed in this session's content-field commit. Post-fix harness numbers: delegate 5/5 populated (up from 0/5), reminder 10/12 populated (up from 1/12). Message only climbed to 1/5, leaving the field description fix incomplete on that intent. Residual friction is now scoped below as its own entry ("MESSAGE block doesn't teach Hindi X-karo-Y construction").

## 2026-04-19: MESSAGE block doesn't teach Hindi X-karo-Y construction

- category: honorifics, role_only_references, scheduled_time_kal (all message cases that failed to populate `message_body` in the 2026-04-19 post-split run)
- offending utterances:
  - "Rajesh ko WhatsApp karo, bolo kal subah 10 baje aa jaaye" → `message_body=None` (body is "kal subah 10 baje aa jaaye")
  - "Supplier ko SMS bhejo, cement ka rate kya hai confirm karo" → `message_body=None` (body is "cement ka rate kya hai confirm karo")
  - "Sharma sahab ko WhatsApp karo, kal milte hain shop par" → `message_body=None` (body is "kal milte hain shop par")
- pattern: all three share the Hindi construction `<recipient> ko <channel> karo, <body>`. The comma separates the routing clause from the body, but the classifier treats the body as a modifier of the routing clause and drops it. Three of the four failing message cases in the run follow this exact shape; the fourth (case 17, "Rajesh ko message bhejo ki kal aana hai aur 5 baje yaad bhi dilana") is a separate multi-intent spillover and already covered by the earlier multi-intent-collapse entry.
- friction: the MESSAGE block examples in `SYSTEM_PROMPT` do teach `<recipient> ko WhatsApp karo, <body>` via "Rajesh ko WhatsApp karo, kal delivery aayegi", but the body-extraction demonstration is implicit. After the content-split landed, `message_body` only filled on 1 of 5 message cases (20%), while delegate hit 5/5 and reminder hit 10/12. The split fixed the schema side; the prompt side still underspecifies what "message_body" should contain when the body comes after a Hindi routing verb.
- suggested direction: iterate the MESSAGE block specifically. Add two or three Hindi X-karo-Y examples to the block that explicitly show the body being extracted into `message_body` (not into free-text or another field). Leave DELEGATE and REMINDER prompt lines alone since they're working. Verification on the four failing message cases (1, 2, 13, 17) with a go/no-go criterion of 3/4 populated on `message_body` (case 17 may still fail due to the separate multi-intent spillover). See SPEC_NEXT_SESSION.md.
- attempt 2026-04-19 (failed, reverted): tried the SPEC_NEXT_SESSION.md prescription literally. Added two inline demonstration examples to the MESSAGE block using `- "<utterance>"` followed by `→ recipient_name=..., channel=..., message_body=...` on the next line, and extended the MESSAGE output line with the parenthetical `message_body (the text the shopkeeper wants delivered, typically the clause after the routing verb like "karo" or "bhejo")`. Harness result (32 cases, Gemini Flash-Lite, temp=0.1): message body population went 1/5 → 0/5 (regression, not improvement). Cases 1, 2, 13 all still returned `message_body=None`; case 17 still spillovers into `task_description`. Overall accuracy held at 31/32 (case 28 still the single miss). Delegate body held at 5/5. Reminder body went 10/12 → 12/12, but both numbers are within Flash-Lite sampling noise at temp=0.1 and the move is not attributable to the prompt change. Prompt change reverted via `git checkout -- app/services/classify.py` per the spec's no-go path. Two hypotheses worth naming for the next attempt: (a) putting two of the verbatim failing utterances into the prompt as examples may have taught the model to treat them as templates of the routing-clause shape with no body, effectively reinforcing the drop behavior; (b) the inline `→ field=value` demonstration format is visually distinct enough from the rest of the prompt that the model parses it as decorative metadata rather than as a field-assignment demonstration, so the signal didn't land where intended. A fresh session should try a structurally different approach, not another example-count tweak. Candidates: move the body-extraction rule into the "Important rules" section as a single high-salience rule (e.g., "For message intent, everything after the comma or after 'karo'/'bhejo' is the message_body, not context."), or drop temperature to 0.0 first and re-baseline to separate prompt signal from sampling noise before iterating further.

## 2026-04-19: intent-scoped body field spillover on multi-intent message

- category: multi_intent_compound (one case in the 2026-04-19 run)
- offending utterance: "Rajesh ko message bhejo ki kal aana hai aur 5 baje yaad bhi dilana"
- observed: intent=message (correct primary), `task_description="kal aana hai"` (should be `message_body`), `message_body=None`. The prompt explicitly says "Populate exactly one of message_body, reminder_text, task_description based on the intent" and "The other two must be null"; this case violates both halves.
- friction: one case of field-mismatch spillover across all 32 cases (3% rate). The `voice.py` WARN-on-spillover diagnostic added in this session will catch this at runtime. Root cause is likely the same as the broader multi-intent-collapse entry: the model commits to `intent=message` but routes the secondary clause's body into whichever field feels closest.
- suggested direction: not a separate fix. Will likely resolve when the multi-intent-collapse entry ("multi-intent utterances collapse to primary, secondary misfiles into scheduled_time") is addressed via the proposed `followup_reminder` structured slot. Track here so the symptom is visible; do not expand scope to fix in isolation.

## 2026-04-18: scheduled_time format is unconstrained and drifts across 10+ variants

- category: scheduled_time_iso, scheduled_time_kal, scheduled_time_relative_hindi, scheduled_time_relative_english, scheduled_time_shaam_ko (all time categories)
- offending utterances: across 16 cases with non-null `scheduled_time`, the run produced at least these formats:
  - ISO time-only: "15:00:00", "17:00:00", "18:00:00"
  - ISO time+tz (no date): "08:30:00+05:30", "21:00:00+05:30"
  - Natural language: "tomorrow 10 AM", "tomorrow morning", "tomorrow at 6 PM", "in 30 minutes", "in 2 hours", "in a little while", "now"
  - Malformed: "tomorrow 09:00:00+05:30:00" (double-colon tz), "10:00:00 AM IST 2024-05-15T10:00:00Z" (two formats concatenated plus an invented 2024 date, run date is 2026)
- friction: the field description at `app/services/classify.py:48-51` offers two options in one sentence ("ISO 8601 time like '2026-04-18T15:00:00' or relative like 'in 30 minutes'") without forcing a pick. The model sometimes emits both at once; sometimes emits time-only with no date; sometimes hallucinates a date. Downstream code would need a dense natural-language date parser, and "10:00:00 AM IST 2024-05-15T10:00:00Z" is not machine-parseable at all.
- suggested direction: split into `scheduled_time_raw: str | None` (verbatim what the user said) and `scheduled_time_iso: str | None` (normalized ISO 8601, or null if the model can't normalize). Pass today's date into the prompt so "kal" resolves to a real date instead of one invented from pretraining.

## 2026-04-18: followup_check never populated, even on cases that literally say "follow up"

- category: multi_intent_compound, general
- offending utterances:
  - "Ramu ko bolo Praveen ko call kare aur delivery confirm kare" → followup_check=None (should be something like "delivery confirmed with Praveen")
  - "Driver ko bolo godown jaaye aur ek ghante baad yaad dilana follow up karna hai" → followup_check=None; follow-up semantics leaked into `scheduled_time="in 1 hour from now"` on a delegate intent
  - "Sharma ji ko call karo aur baad mein yaad dilana payment ka pucha tha" → followup_check=None; follow-up semantics leaked into `scheduled_time="in a little while"` on a call intent (call intents should have no time field at all)
- friction: 0 of 32 cases populated `followup_check`. The field is effectively invisible to the model even when the utterance contains "follow up" or "yaad dilana". Follow-up semantics instead misfile into `scheduled_time`, which is supposed to be reminder-only.
- suggested direction: either remove `followup_check` as dead weight, or replace with a structured `followup_reminder: {text: str, time: str} | None` that any intent can set. The structured shape also resolves the multi-intent-collapse friction below.

## 2026-04-18: multi-intent utterances collapse to primary, secondary misfiles into scheduled_time

- category: multi_intent_compound (generalizes the earlier "delegate intent with a time" entry)
- offending utterances:
  - "Rajesh ko message bhejo ki kal aana hai aur 5 baje yaad bhi dilana" → intent=message, scheduled_time="tomorrow 5 PM" (but this is a self-reminder, not a message send-time)
  - "Driver ko bolo godown jaaye aur ek ghante baad yaad dilana follow up karna hai" → intent=delegate, scheduled_time="in 1 hour from now" (delegate has no defined time slot)
  - "Sharma ji ko call karo aur baad mein yaad dilana payment ka pucha tha" → intent=call, scheduled_time="in a little while" (call has no time slot at all)
- friction: every compound-intent case in the run (4 of 4) produced intent=<primary> with the secondary intent's time leaking into `scheduled_time`, a field documented as reminder-only. For call intents, the leak lands in a field that shouldn't exist for that intent. Same underlying shape as the earlier delegate-with-time entry but the pattern spans message+reminder, delegate+reminder, call+reminder.
- suggested direction: add a structured secondary slot: `followup_reminder: {text: str, time_raw: str} | None` that any non-reminder intent can set. Supersedes both the per-intent `scheduled_time` misuse and the orphaned `followup_check` field. Would also let the classifier express "do the primary, plus remind me later" without needing two round trips.

## 2026-04-18: ambiguity has no structured representation, forces a guess

- category: ambiguous_clarification
- offending utterance: "Rajesh ko 5 baje bolo"
- friction: this utterance is genuinely ambiguous between `message` ("tell Rajesh something at 5"), `delegate` ("instruct Rajesh to do something at 5"), and `reminder` ("remind me at 5 about Rajesh"). The schema requires a single `intent` string; the only escape valve is `clarification_needed` (free text). The model picked `delegate` with no clarification set, and it was the only classifier failure in the run (31/32). The schema shape discourages deferring because the rest of the record assumes a committed intent, so the model commits.
- suggested direction: add `candidate_intents: list[str]` sorted by plausibility, and treat `intent` as the top candidate. Or add `is_ambiguous: bool` that explicitly opts into the clarification path. Either gives the model a first-class way to say "I'm not sure which of these three this is" without dropping to the `unknown` intent.

## 2026-04-18: channel is never extracted on messages, even when the user literally names it

- category: general (applies to every message case)
- offending utterances:
  - "Rajesh ko WhatsApp karo, bolo kal subah 10 baje aa jaaye" → channel=None
  - "Supplier ko SMS bhejo, cement ka rate kya hai confirm karo" → channel=None
  - "Sharma sahab ko WhatsApp karo, kal milte hain shop par" → channel=None
- friction: 4 of 5 message cases contained an explicit channel word ("WhatsApp karo", "SMS bhejo"); `channel` came back None on all 5. Closer to a prompt-shape miss than a schema-shape miss, but there is a schema-level fix: `channel` is currently `Optional[str]` with free-text description, which the model treats as opt-in. Downstream handlers can't route the message without this field.
- suggested direction: type `channel` as `Literal["whatsapp", "sms", "telegram"] | None`. Pydantic's JSON Schema emits `enum: [...]`, which Gemini's Schema dialect accepts, and enums make "pick one of these if you see a matching word" much more salient to the model than prose descriptions.

## 2026-04-22: classifier hallucinates slots when ASR drops a token

- category: general (surfaced on reminder and delegate; likely spans all intents)
- offending utterances (from `recordings/intent_classification.md`):
  - ASR output "Hours remind me to call supplier" (Sarvam dropped the leading "2") → classifier emitted `scheduled_time="in 1 hour"`, inventing a number that was never spoken.
  - ASR output "Baje yaad dilana Rajesh ko call karna hai" (Sarvam dropped the leading "3") → classifier emitted intent=reminder with recipient_name=Rajesh and a non-null reminder_text, but scheduled_time=null. Mixed behaviour: silent on time here, hallucinated on the previous case.
- friction: the prompt does not explicitly forbid guessing missing numbers/names/times. On cases where ASR has visibly dropped a leading token, the classifier sometimes fills in a plausible value rather than leaving the field null. This is worst on `scheduled_time` because the field accepts free-text and downstream handlers will happily schedule a fired-up "1 hour from now" reminder the user never asked for.
- suggested direction: add to "Important rules" in the system prompt: "If a number, time, or proper noun is not clearly present in the transcript, leave the corresponding field null. Missing is missing. Do not infer." Tighten further once the `scheduled_time_raw` vs `scheduled_time_iso` split (2026-04-18 entry) lands — the raw field can carry "unclear" as a token instead of null.

## 2026-04-22: confidence field is never populated on success paths

- category: general (observed on every classification in 2026-04-22 run)
- offending utterances: the entire `recordings/intent_classification.md` run. On 15/18 correct classifications, `confidence` came back 0.0. The only non-zero values were 0.5 (on `unknown` fallbacks) and two edge cases at 0.6 and 0.9.
- friction: Pydantic defaults `confidence` to 0.0, and Gemini is omitting the field in structured output even when the intent is obvious. The handler's clarification gate (`app/handlers/voice.py:137`) reads confidence to decide whether to ask for confirmation — if every correct intent returns 0.0, the handler should be asking for confirmation on every correct call, which is neither desired behaviour nor what actually happens (indicating the handler is also treating 0.0 as "allow through", a separate wrongness).
- suggested direction: make confidence mandatory in the prompt with an explicit band. "Always populate `confidence`: ≥0.9 when intent is unambiguous and all slots are filled; 0.6-0.8 when slot extraction is partial; <0.5 when intent is uncertain and the handler should ask for confirmation." Combined with reconciling the prompt/handler threshold mismatch (2026-04-18 entry) by standardising on 0.5 at both sites.
- scope: this is being addressed in SPEC.md (2026-04-22). Prompt-only change.

## 2026-04-22: Devanagari input slightly less robust than Hinglish translit for the classifier

- category: general (one clear case in 2026-04-22 run)
- offending utterance: "आमू को बोलो प्रवीण को कॉल करें और डिलीवरी कन्फर्म करें" (Devanagari output of GS PM9; ASR mis-heard "Ramu" as "Aamu" → "आमू").
- observed: translit variant ("Aamu ko bolo Praveen ko call karke delivery confirm kare") classified as `delegate` with recipient_name=Aamu, task_description populated. Same audio's Devanagari transcript classified as `unknown`. Same intent, same speaker, same content — only script differs.
- friction: for an ASR-error handling layer we haven't built yet (phonetic fuzzy-matching against the contact list), the classifier is seeing slightly different inputs depending on which output mode we pick. If we ship `saaras:v3 codemix` (mixed Devanagari + English) or `translit` (Latin Hinglish), the classifier should behave identically on either. The 18-clip sample shows one real divergence and suggests Latin-script inputs are marginally more robust for unusual tokens.
- suggested direction: not a schema fix; either (a) keep Devanagari as production output and include in the prompt "recipient names may be unusual or ASR-garbled; do not reject a plausible command just because the name is unfamiliar", or (b) switch production ASR output to `saaras:v3 translit` and re-baseline. Chose (a) implicitly by going with `codemix` in SPEC.md; the prompt hardening is the smaller lever.

## 2026-04-22: "Ramu ko bolo yaad rakhe" — genuine message/delegate ambiguity

- category: general / intent labelling
- offending utterance: "Ramu bhaiya ko bolo yaad rakhe, kal delivery aayegi" (RECORDING_BRIEF phrase 4)
- observed: classifier returns `delegate` with recipient=Ramu, task_description="yaad rakhein kal delivery aayegi". RECORDING_BRIEF labels this phrase as `message`. Brief-vs-classifier disagreement was 2 of 3 apparent "misses" on the 2026-04-22 run; the third was a correctly-rejected missing-recipient case.
- friction: "X ko bolo Y" is genuinely ambiguous between "send X a message saying Y" (message) and "ask X to do Y" (delegate). The brief's labelling picked `message`; the classifier picked `delegate`. Both are defensible. With intent as a single string, there is no way to express "probably delegate but could be message" — same shape as the 2026-04-18 `Rajesh ko 5 baje bolo` ambiguity entry, different utterance.
- suggested direction: not a new fix. Tracks with the existing `candidate_intents: list[str]` proposal in the 2026-04-18 "ambiguity has no structured representation" entry. In the meantime, update `RECORDING_BRIEF.md`'s labelling to treat "X ko bolo <content>" as `delegate` when the content describes an action, `message` only when the content is a statement to pass on. Non-binding.

---

## 2026-04-18: Task.payload keys should match intent-schema field names

- category: general (convention, not a specific friction case)
- offending utterance: n/a
- friction: before the `content` split landed, every handler wrote `{"content": intent.content, ...}` into `Task.payload` while the intent schema had a single overloaded `content` field. When splitting the intent schema into `message_body`, `task_description`, and `reminder_text`, the question arose whether the persisted payload key should also rename. The "keep the payload key as `content`" path is simpler short-term (no migration, no persisted-shape change) but guarantees ongoing drift between the intent schema and the persistence layer. That drift is expensive: every future schema change forces a "did the payload key change too?" decision, and readers of stored rows have to remember that `payload["content"]` could mean any of three things depending on `task_type`.
- resolution: as of the `content` split, `Task.payload` keys mirror the intent-schema field names exactly. `message` tasks write `{"message_body": ...}`, `delegate` tasks write `{"task_description": ...}`, `reminder` tasks write `{"reminder_text": ...}`. No data migration was required because no `Task` rows existed yet.
- convention going forward: when adding or renaming fields on `IntentClassification`, the corresponding `Task.payload` key should use the same name. If a good reason surfaces to diverge, document it in this file rather than letting it happen silently.
