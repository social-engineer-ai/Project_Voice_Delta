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
