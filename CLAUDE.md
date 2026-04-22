# ShopSaarthi Bot — Claude Code Guide

This file gives Claude Code session context when picking up this project for implementation or iteration.

## Project summary

Voice-native Telegram bot for Indian shopkeepers. Four core intents: send message, set reminder, delegate task, make call. Includes voice biometric verification as a trust feature. See `../shopsaarthi/ShopSaarthi_PRD_v0.2.md` for the full PRD.

## Before implementing anything new

**Pause and discuss with AV** (the author) which Claude Code capabilities would add value for the specific task before starting:

- **Skills** — worth creating for Telegram bot patterns, Sarvam API, Resemblyzer, or prompt engineering for the intent classifier
- **Hooks** — useful for running `tests/test_classify.py` automatically when `app/services/classify.py` changes
- **Subagents** — helpful when parallel work on backend handlers and testing makes sense
- **MCP servers** — Telegram, AWS, Postgres access could be useful if AV wants agentic deployment flows
- **Plan mode** — use for any multi-file feature like voice enrollment
- **CLAUDE.md updates** — add architecture conventions as they emerge

Don't assume any of these are needed; ask AV which ones fit the current task.

## Style conventions

- **No em-dashes in code comments or strings.** AV's explicit preference.
- **Plain professional language throughout.** No marketing voice, no hype.
- **Hindi strings for user-facing text** where it matches the user's experience. English for code, variable names, log messages.
- **Hinglish transliteration for Hindi strings** (not Devanagari). Shopkeepers read these on Telegram and Hinglish is more universally legible than Devanagari on a small screen.
- **Comments explain why, not what.** The code shows what; comments should add the reasoning.
- **Type hints throughout.** Python 3.11 style, `str | None` not `Optional[str]`.

## Current pipeline choices (2026-04-22)

These are the active model and mode selections on main after the 2026-04-22 evaluation session. When changing any of them, update this section and `SPEC.md` in the same commit.

- **ASR**: Sarvam `saaras:v3` with `mode="codemix"`, `language_code="hi-IN"`, sync `/speech-to-text` endpoint. Migrated from `saarika:v2.5` because v2.5 is on Sarvam's deprecation path and misrecognised common Hindi names ("Ramu" → "Naamu") that saaras:v3 got right. Codemix mode preserves English loanwords in Latin script alongside Devanagari, matching how shopkeepers actually speak.
- **Biometric**: SpeechBrain `spkrec-ecapa-voxceleb` (ECAPA-TDNN), 192-dim embeddings, cosine similarity. Migrated from Resemblyzer because Resemblyzer could not separate confirmed-unrelated speakers on our test audio (margin +0.003, unusable); ECAPA-TDNN gave a +0.473 margin on the same data. Thresholds: `strict=0.70, medium=0.55, loose=0.40, off=0.0`. Weights cache to `.cache/spkrec-ecapa/` (gitignored).
- **Classifier**: Gemini 2.5 Flash-Lite with the prompt in `app/services/classify.py`. Confidence default is 0.8 (not 0.0) because Gemini omits the field on successful classifications; fallback path in `classify_intent()` still emits 0.0 explicitly so the handler's `< 0.5` clarification gate behaves correctly.

### Intent taxonomy (expanded 2026-04-22)

The classifier recognises 12 intents split into two scopes. The router (`app/handlers/voice.py`) uses `IntentClassification.scope`, not the intent string, to decide whether to act.

| Scope | Intents | What the bot does |
|---|---|---|
| `in_scope` | `message, reminder, delegate, call` | Routes to the matching handler and acts on it. |
| `future_phase` | `order, collection, supplier_payment, inventory, price_check, worker, summary` | Recognises, logs to `FuturePhaseLog`, and replies with a specific Hindi acknowledgement. Does not act. |
| `unknown` | `unknown` | Falls back to the clarification path. |

Future-phase intents exist so the brother-shop pilot and Yogesh's testing produce a real usage histogram from day one. Priority order for building future-phase handlers comes from `FuturePhaseLog` aggregates after real usage, not from PRD guesses. Add new future-phase intents to `IntentValue`, `FUTURE_PHASE_INTENTS`, `INTENT_LABEL_HINDI`, the system prompt, and test cases.

## Known ASR failure modes worth defending against

These surfaced in the 2026-04-22 evaluation and recur across independent recordings. Context engineering (contact list + shop vocabulary in the classifier prompt) is the next leverage; the ASR-side levers are mostly exhausted.

- **Proper-noun drift on names**: "Ramu" → "Naamu" / "Aamu", "Praveen" → "Permanent" / "Parman" / "Permit". Different renderings each time the audio runs. Rely on the contact resolver to fuzzy-match on phonetic distance rather than exact string.
- **English loanword → Hindi phonetic neighbour**: "shop par" → "subah sahab par", "Accountant ji" → "Mountain G". Not noise-driven; happens in clean recordings. The classifier prompt or a post-ASR correction layer is where this gets fixed, not the ASR.
- **Leading-number drop on short utterances**: "3 baje" → "baje", "2 hours remind me" → "Hours remind me". Short fragments are more brittle than full sentences. Classifier prompt now forbids guessing missing numbers; pair with a "ask the user" flow when the reminder time is null.

## Architecture conventions

- **Services** (`app/services/`) are stateless wrappers around external APIs (Sarvam, Gemini, SpeechBrain) or pure-function utilities (contact_resolver). They don't know about Telegram.
- **Handlers** (`app/handlers/`) orchestrate services and interact with Telegram. They take `(update, context, user, intent)` for intent handlers or `(update, context)` for command handlers.
- **DB access** goes through `SessionLocal()` with a `try/finally db.close()` pattern. No global sessions.
- **Voice verification** happens in `handle_voice_message` before transcription — fail fast on bad voices.
- **Lazy-load heavy models** like Resemblyzer's VoiceEncoder. First inference pays the cost; subsequent calls are fast.

## Lab protocols (ethical requirements)

This project operates under documented lab protocols in place of IRB. When implementing features that touch user data:

- Voice recordings are temporary — delete from disk after embedding extraction
- Do not log full transcripts by default in production (truncate or hash)
- Any feature that stores new user data needs a retention and deletion path
- Commercial usage data is distinct from research data; the model training pipeline (when built) must only use data from shops that consented in their subscription terms

## Known todos / future work

In rough order of probable next steps:

1. **Field testing infrastructure** — a simple script to run Sarvam against a directory of labeled audio files and report accuracy. The 12th grader will produce the audio; we need the evaluation harness.
2. **Bill generation (Phase 1b)** — voice-triggered bill creation with PDF output and Tally XML export. Needs new `/handlers/bill.py` and `/services/tally_export.py`.
3. **Admin dashboard** — minimal FastAPI web UI for the accountant to download Tally XML exports. Starts as Phase 1b.
4. **Multi-user support** — extending VoiceProfile to handle multiple users per shop with permission tiers. Phase 4.
5. **Intelligence features** — weekly summaries, pattern detection. Phase 4.
6. **Offline / queued capture** — for poor connectivity. Conditional on field data from Phase 2.

## Testing approach

- **Offline classifier tests** (`tests/test_classify.py`) — hit Gemini with sample utterances, verify correct intent extraction. Run this before committing any change to `classify.py` or its system prompt.
- **End-to-end testing** — currently manual via AV's own Telegram account. No automated e2e tests yet.
- **Voice verification tests** — not built yet. Would need audio fixtures and a test harness that loads them through Resemblyzer.

## Deployment

Currently runs locally via `python -m app.main` with SQLite. For the India deployment:

- Move to Postgres on AWS RDS (ap-south-1, Mumbai region for latency)
- Deploy the bot as a systemd service or a containerized app on a small EC2 instance
- Use AWS Activate credits for infrastructure
- Add monitoring for API error rates, ASR accuracy samples, intent classification distributions

## Hooks

`.claude/settings.json` registers a `PostToolUse` hook on `Write|Edit`
that runs `tests/test_schema_cleaner.py` whenever `app/services/classify.py`
changes. The filename filter lives in the helper script at
`.claude/hooks/schema_cleaner_check.py`, not the matcher, so the hook
exits cheaply (~50ms) for unrelated edits. The invariant it protects:
the Pydantic-to-Gemini schema cleaner stays green. Without this, a
classifier edit can silently break response-schema generation and every
real classification call fails at runtime (see commit `90c9e6c` for the
original incident).

Behavior:
- Match: `app/services/classify.py` (path suffix; Windows backslashes normalized).
- Timeout: 10 seconds. On timeout the hook logs a warning and exits 0
  rather than blocking; the cleaner test should finish in under a
  second, so a timeout implies something larger is wrong.
- Success: silent exit 0. A success line on every edit would be noisy.
- Failure: exit 2 with stdout+stderr captured on stderr so Claude sees
  the test output as feedback.

Interpreter: the committed command uses `venv/Scripts/python.exe`,
which is AV's Windows venv layout. On macOS/Linux or a different venv
path, override the interpreter path via `.claude/settings.local.json`
(which is not checked in) rather than editing `settings.json`. The
hook script itself uses `sys.executable` for the subprocess, so only
the outer invocation needs environment tweaking.

## Who to ask

Product decisions: AV
Domain questions about shops: AV's brother (building materials), AV's jijaji (kirana), the friend's daughter (medical), Pravin (dalal), the accountant (bill/Tally integration)
Infrastructure: AV (self-managed on AWS)
