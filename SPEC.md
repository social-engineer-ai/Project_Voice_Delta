# SPEC: Prototype handoff changes from 2026-04-22 findings

Author: AV (via Claude Code)
Date: 2026-04-22
Scope: Migrate ASR and biometric encoders to better models, tighten the
classifier prompt to avoid slot hallucination and to always emit
confidence. Scoped to what's needed before Yogesh takes the prototype
for field testing.

## Context

This SPEC is being written **after** the investigation it acts on. The
2026-04-22 session started as exploratory transcription and grew into
broader evaluation. Findings and decisions are recorded in
`SESSION_NOTES_2026-04-22.md`. This SPEC limits itself to the
code-level work that operationalises those decisions.

The prior `SPEC.md` ("Expand classify.py test coverage", 2026-04-18)
was already implemented (commit `d967f96`) and is superseded by this file.

## Goal

Hand Yogesh a prototype with:
- An ASR pipeline that doesn't misrecognise common Hindi names
  ("Ramu" → "Naamu") where we already have evidence of a better
  variant.
- A speaker-verification layer that can actually distinguish unrelated
  speakers at the strict threshold.
- A classifier that is honest about what it doesn't know — no guessed
  times, confidence always populated so the handler's clarification
  logic works.

## Out of scope

- Contact-list context in the classifier prompt. Highest-value next
  step per `SESSION_NOTES_2026-04-22.md` but requires a decision on
  the three-layer schema (general / vertical / shop-specific) which
  `CLAUDE_CODE_KICKOFF.md` marks as a flag-don't-solve item.
- Telegram-side `/enroll` UX changes. The underlying `store_enrollment`
  keeps its shape; any conversational changes belong in a later spec.
- Migrating stored Resemblyzer embeddings. Existing enrollments become
  invalid with the encoder swap; re-enrollment on first command is
  acceptable for the prototype stage.
- Sarvam hotword / phrase-bias experiment. Saved for a later round of
  accuracy work.

## Changes by file

### `app/services/transcribe.py`

Switch the ASR call to `saaras:v3` with `mode="codemix"` and
`language_code="hi-IN"`. Reasons, from the variant comparison:

- `saaras:v3` recovers "Ramu" where `saarika:v2.5` mis-heard "Naamu".
- `codemix` mode preserves English tokens (`phone`, `call`, `accountant`)
  in Latin script alongside Devanagari, which matches how shopkeepers
  actually speak and gives the classifier a more faithful signal.
- `saarika:v2.5` is on Sarvam's deprecation path, so staying on it is
  technical debt.

Keep the existing function signature and the sync endpoint. Telegram
voice messages fit in the 30s sync window for almost all real commands.

### `app/services/verify_speaker.py`

Swap Resemblyzer for SpeechBrain ECAPA-TDNN
(`speechbrain/spkrec-ecapa-voxceleb`). Keep the module's public API —
`compute_embedding`, `verify_speaker`, `store_enrollment`, `THRESHOLDS`
— intact, because the handler and enrollment paths import them by name.

Rebase thresholds to match ECAPA's cosine-score distribution:

```python
THRESHOLDS = {
    "strict": 0.70,   # +0.28 margin over the worst imposter we measured
    "medium": 0.55,
    "loose":  0.40,
    "off":    0.0,
}
```

Default `security_threshold` on `User` remains `"medium"` for
unenrolled-but-marked-enrolled edge cases, but the recommended value
for the prototype is `"strict"` — set this in the first-enrollment flow
in a later spec if needed.

Lazy-load ECAPA the same way the Resemblyzer encoder is lazy-loaded.
First call downloads ~80 MB of weights to `.cache/spkrec-ecapa/`.
Cache directory is git-ignored (add to `.gitignore` if not already).

### `app/services/classify.py`

Two prompt tweaks, no schema change:

1. **Forbid guessing missing slots.** Add to the "Important rules"
   block: "If a number, time, or proper noun is not clearly present in
   the transcript, leave the corresponding field null. Do not infer a
   plausible value from context. Missing is missing."

2. **Mandatory confidence band.** Replace the current single-line
   "confidence should reflect" rule with: "Always populate `confidence`.
   Use ≥0.9 when the intent is unambiguous and all slots are filled
   from the transcript. Use 0.6-0.8 when slot extraction is partial or
   the recipient is named but unfamiliar. Use <0.5 when the intent
   itself is uncertain — the handler will ask for confirmation."

Also: update the confidence handling. The handler's clarification path
(`app/handlers/voice.py:137` and `:184`) gates on `<0.5`; the previous
prompt said `<0.7`. Align the prompt to the handler (0.5) rather than
the other way round, because changing the handler touches more
downstream paths. `SCHEMA_NOTES.md` 2026-04-18 entry about this exact
inconsistency is being resolved by this change.

### `app/db/models.py`

Update the `VoiceProfile` docstring to reflect ECAPA-TDNN's
192-dimensional float32 embedding (768 bytes per sample vs 1024 with
Resemblyzer). No column schema change — `LargeBinary` accommodates
either.

### `requirements.txt`

Add:
- `speechbrain==1.1.0`
- `torch` (CPU wheels via PyTorch's CPU index)
- `soundfile==0.13.1`
- `imageio-ffmpeg==0.6.0`

Remove:
- `resemblyzer==0.1.4`
- `webrtcvad-wheels` (was a transitive of resemblyzer on Windows)

`librosa` stays — useful for future noise/quality tooling even though
it isn't in the production path.

### `CLAUDE.md`

Append a short "Current state (2026-04-22)" subsection under
architecture conventions listing: current ASR (`saaras:v3 codemix`),
current biometric (ECAPA-TDNN), the three known ASR failure modes that
context-engineering should address next
(proper-noun drift, English-loanword phonetic confusion, number drop on
short utterances).

### `recordings/DATA_COLLECTION_BRIEF_v2.md`

Remove the paragraph-length-enrollment recommendation in the earlier
version (it was written before we tested ECAPA). Replace with a note:
"Enrollment sessions can use the first 5-6 Section A phrases back to
back. ECAPA-TDNN gives a clean separation margin on 30s of speech;
dedicated paragraph recording is not required."

## Verification

Before handover:

1. `tests/test_schema_cleaner.py` — must pass (hook-enforced on any
   edit to `classify.py`).
2. `tests/test_classify.py` — run against the updated prompt. Report
   any intent-accuracy regression of >5 points to AV before shipping.
3. A single manual round-trip: a Telegram voice message in Hindi from
   AV's phone, through the updated `handle_voice_message`, should
   transcribe, classify, and produce the expected intent. (If AV can't
   do this pre-handover, Yogesh does it as first smoke test.)
4. Enrollment smoke test: `/enroll` five phrases, `/voicestatus` shows
   enrolled, a follow-up command from the same voice passes
   verification, a command from a different voice is rejected at
   `strict`.

## Rollback

If ECAPA-TDNN causes latency or deploy issues on Yogesh's environment,
fall back to Resemblyzer by reverting `verify_speaker.py` and restoring
`resemblyzer` in `requirements.txt`. The VoiceProfile column accepts
either encoder's output. Document any user who enrolled under ECAPA as
needing to re-enroll if the rollback happens — the 256-dim vs 192-dim
mismatch would produce garbage scores otherwise.

If `saaras:v3 codemix` produces worse results for Yogesh's test users
than `saarika:v2.5` did for AV, revert the one-line change in
`transcribe.py`. No migration needed — the two models are interchangeable
at the API level.

## Handover doc

A separate `HANDOVER.md` is produced alongside this spec with:
- How to run locally (env vars, first-time enrollment, cache directory).
- Known issues left unresolved (Praveen drift, Mountain G, Aamu).
- Suggested smoke-test flow for Yogesh on day one.
- What to do if something breaks.
