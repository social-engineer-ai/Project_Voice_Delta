# SPEC: Expand classify.py test coverage

Author: AV (via Claude Code)
Date: 2026-04-18
Scope: Phase 1 hardening of the intent classifier's offline test suite.

## Goal

Grow `tests/test_classify.py` from 12 untagged cases into a structured evaluation harness that covers named edge categories, emits a machine-readable JSON report with per-intent and per-category breakdowns, and surfaces (but does not fix) schema limitations encountered along the way.

## Out of scope

- Changes to `app/services/classify.py`. The system prompt and the Pydantic schema are not touched. Friction is logged in `SCHEMA_NOTES.md`, not fixed.
- A pass-rate gate on test runs. Accuracy is reported, not enforced.
- Mocking Gemini. Tests continue to hit the live API. Cost per full run remains under a rupee at Flash-Lite pricing.
- CI integration. The harness produces a usable exit code and report; wiring it into a hook is a future scope.

## Edge categories to cover

Each category needs at least one test case. A case may carry more than one category tag.

1. `honorifics`. Names with "ji", "bhaiya", "sahab". Verifies the prompt's honorific stripping rule.
2. `role_only_references`. "the driver", "the supplier", "servant", with no proper name.
3. `multi_intent_compound`. Utterances that pack two intents into one sentence (delegate plus reminder, message plus reminder).
4. `scheduled_time_iso`. Reminder with an explicit clock time like "3 baje" or "10 AM tomorrow".
5. `scheduled_time_relative_hindi`. "30 minute baad", "thodi der mein", "abhi".
6. `scheduled_time_relative_english`. "in 30 minutes", "in two hours".
7. `scheduled_time_kal`. "kal subah", "kal shaam".
8. `scheduled_time_shaam_ko`. "shaam ko", "subah", "raat ko" (named-time-of-day shorthand).
9. `ambiguous_clarification`. Utterances that match multiple intents weakly or are missing required fields.
10. `off_topic_no_match`. Inputs that are plainly not commands. The existing "Haan theek hai" sits here.

## Assertions

For every case:

- `intent` equals the expected intent. This is the only hard assertion.

For categories where the expected intent is one of the four:

- `recipient_name` is reported and loosely compared against expected when expected is provided. Loose match means substring either way, matching the existing convention in `test_classify.py`.

For `ambiguous_clarification` and `multi_intent_compound`:

- `intent` must match the expected primary intent.
- `clarification_needed` and `confidence` are reported in the JSON output but not asserted.

For `scheduled_time_*` categories:

- `intent` must be `reminder`.
- `scheduled_time` is reported in the JSON output but not asserted on format. The goal today is to observe what the model returns across formats so we can decide how to normalize later.

## Output

`python -m tests.test_classify` produces:

1. Human-readable stdout: per-case status line with intent, recipient, and any failed assertions, plus per-intent and per-category summary blocks at the end.
2. `tests/last_run.json` containing:
   - `run_started_at` (ISO timestamp)
   - per-case records: input, categories, expected fields, full actual `IntentClassification`, `intent_passed` boolean, `recipient_passed` boolean (or null when not asserted), `latency_ms`
   - per-intent rollup: count, passed, accuracy
   - per-category rollup: count, passed, accuracy
   - overall: count, passed, accuracy
3. Exit code 0 if the harness ran to completion. Non-zero only on infrastructure failure (Gemini unreachable, schema parse error, etc.). Accuracy is observed today, not gated.

## Schema friction log

`SCHEMA_NOTES.md` lives at `shopsaarthi-bot/SCHEMA_NOTES.md`. It is appended to over time, not regenerated. Each entry has:

- date
- category
- offending utterance
- friction description (what was awkward about expressing the expected output in the current schema)
- suggested direction (one line, optional)

The test runner does not write to this file automatically. Entries are added by hand as test cases are written, whenever the schema makes the expected-output construction awkward.

## Test set composition

- Existing 12 cases: kept verbatim, retroactively tagged with applicable categories.
- New cases: roughly 2 to 4 per category, biased toward realistic utterances a building materials shopkeeper might produce.
- Total target: 35 to 50 cases.

## Files touched

- `tests/test_classify.py` (modified)
- `SCHEMA_NOTES.md` (new file at `shopsaarthi-bot/`)
- `SPEC.md` (this file, at `shopsaarthi-bot/`)

No changes to `app/services/classify.py` or anywhere else in `app/`.

## Verification

- `python -m tests.test_classify` runs to completion without error.
- `tests/last_run.json` exists, parses as JSON, contains all three rollup levels, and reports accuracy figures for every named category.
- Every named category has at least one case in the suite.
- `SCHEMA_NOTES.md` exists with a header and any entries surfaced during the work.
