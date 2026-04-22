# Session Notes — 2026-04-22

Author: AV (via Claude Code)
Session length: one long working session
Goal at start: transcribe two long WhatsApp recordings from Garv

## Process deviation — explicit exception

This session did not follow the `CLAUDE_CODE_KICKOFF.md` four-step process
(interview → discuss Claude Code features → plan → implement → commit).
It started as an ad-hoc data-analysis task — transcribe some recordings
and see if they work — and grew into a broader evaluation of the whole
voice pipeline across many dimensions. No `SPEC.md` was written up front,
no interview was conducted, no plan was drafted in Plan Mode.

The discipline was resumed at the point an implementation change became
a real possibility: this file is the retroactive session record, and
`SPEC.md` (which this session is rewriting) scopes the code changes
that came out of the findings below. Future sessions should follow the
kickoff process; treat this one as a one-off because the work started
exploratory and only later implied production code changes.

---

## What was done

Six lines of investigation, in order:

1. **Transcribed the two long WhatsApp recordings** (approximately 108s
   and 129s) using Sarvam's batch API. Produced clean `.txt` transcripts
   and raw JSON with word-level timestamps under
   `recordings/_sarvam_out/`.
2. **Compared seven Sarvam variants** (`saarika:v2.5` in two language
   settings plus `saaras:v3` in five modes) on the same two files.
   Raw outputs under `recordings/_variants/`; summary in
   `recordings/variant_comparison.md`.
3. **Built a per-phrase capture matrix** mapping each of the 32 brief
   phrases to what each variant transcribed, with sentence-bounded
   extraction for readability
   (`recordings/phrase_matrix.md`, `recordings/expected_vs_actual.md`).
4. **Transcribed Yogesh's 6 clips and GS's 14 clips** (4 of which are
   byte-copies of Yogesh files) with `saaras:v3` translit and
   Devanagari. Outputs under `recordings/Yogesh/_sarvam_out/` and
   `recordings/GS/_sarvam_out/`.
5. **Ran the existing classifier** (`app.services.classify`) against
   every short-clip transcript, scoring intent accuracy per input
   script (Hinglish translit vs Devanagari). Report at
   `recordings/intent_classification.md`.
6. **Tested speaker verification** in three configurations:
   short-clip enrollment with Resemblyzer (failed), long enrollment
   with Resemblyzer (marginal), long enrollment with SpeechBrain
   ECAPA-TDNN (clean). Scripts under `scripts/test_biometric*.py`.

## Artifacts produced

### In `recordings/`
- `alignment.md` — Round-1 phrase alignment for the two long files.
- `variant_comparison.md` — seven-variant ASR comparison.
- `phrase_matrix.md` — per-phrase keyword-span capture for each variant.
- `expected_vs_actual.md` — clean side-by-side of brief phrase vs ASR output.
- `intent_classification.md` — classifier results on short clips.
- `DATA_COLLECTION_BRIEF_v2.md` — round-2 collection protocol (144 phrases
  across 12 sections, three time-tiers, consent text, file-naming scheme).

### In `scripts/`
- `transcribe_recordings.py` — batch transcription of all files in `recordings/`.
- `transcribe_folder.py` — parameterised folder transcription.
- `transcribe_variants.py` — sweep across all Sarvam model/mode variants.
- `build_phrase_matrix.py` — keyword-span matrix generator.
- `build_expected_vs_actual.py` — cleaner side-by-side view.
- `classify_transcripts.py` — intent classifier over short clips.
- `test_biometric.py` — short-clip biometric test.
- `test_biometric_long_enroll.py` — proper-length enrollment test (Resemblyzer).
- `test_biometric_ecapa.py` — same test with SpeechBrain ECAPA-TDNN.

### Dependency deltas discovered during the session
- `sarvamai==0.1.28` — added (Sarvam batch API).
- `httpx==0.28.1` — bumped from 0.27.2 (transitive).
- `librosa`, `soundfile`, `numpy`, `scipy`, `scikit-learn` — added for
  noise analysis.
- `imageio-ffmpeg` — added so MP4 audio decodes without a system ffmpeg.
- `resemblyzer`, `torch` (CPU), `webrtcvad-wheels` — added to test
  existing biometric before deciding to swap.
- `speechbrain==1.1.0`, `torchaudio` — added for ECAPA-TDNN.

Not all of these end up in production `requirements.txt`. The
handoff-relevant final set is in the next session's SPEC.

---

## Key findings

### ASR

| Finding | Evidence |
|---|---|
| `saaras:v3` fixes "Ramu → Naamu" that `saarika:v2.5` got wrong | File 1 phrase 4 in `variant_comparison.md` |
| No variant handles "Praveen" reliably in File 1; all get it in File 2 | `phrase_matrix.md` phrase 18 |
| `saaras:v3 mode=codemix` preserves English loanwords mixed with Devanagari — closest match to how shopkeepers actually speak | `variant_comparison.md` |
| `saaras:v3 mode=verbatim` and `translit` misheard "30 minute" as "20" on File 1 phrase 8; transcribe and codemix got 30 | `variant_comparison.md` |
| `saarika:v2.5` is on Sarvam's deprecation path; saaras:v3 is the current recommended ASR | Sarvam docs search |
| No cost difference between variants at the public price sheet; diarization adds ~50%, modes don't | `sarvam.ai/api-pricing` |
| Noise impact on accuracy at 14 dB SNR is near zero — all the errors we saw on File 1 recur on cleaner short clips | biometric script's noise measurements + per-phrase matrix |
| New proper-noun errors found: "Ramu → Aamu" (GS PM9), "shop par → subah sahab par" (GS PM6), "Accountant ji → Mountain G" (multiple) | `recordings/GS/_sarvam_out/` |

### Classifier

Intent accuracy on short clips: **15/18 translit, 14/18 Devanagari**
(83% / 78%), excluding ambiguous fragments. See
`recordings/intent_classification.md` for detail.

Issues surfaced:
- Classifier **hallucinates missing slot values**. On "Hours remind me
  to call supplier" (ASR dropped "2"), the classifier emitted
  `scheduled_time=in 1 hour` instead of leaving it null.
- `confidence` is almost always 0.0. Gemini is not populating it, and
  Pydantic defaults to 0.0. The handler's threshold logic is therefore
  effectively dead.
- **Misattribution when a prefix drops**: "Bolo ghar ja ke khana le
  aaye" (missing "Chhotu ko") produced `recipient_name=ghar` (home). A
  contact-list context in the prompt would have constrained this.
- Devanagari input is slightly more fragile than Hinglish translit for
  the classifier: "आमू को बोलो" failed where the translit equivalent
  "Aamu ko bolo" classified correctly as delegate.
- "Ramu ko bolo yaad rakhe, kal delivery aayegi" was classified as
  `delegate`, brief labels it as `message`. Genuine ambiguity; worth
  pinning the label one way or the other.

### Biometric

Two sequential experiments:

**Resemblyzer, proper enrollment (73s from File 2 chunks):**
- Same-speaker held-out: 0.897 - 0.978.
- Different speaker File 1 (confirmed different person, no relation):
  **0.771 - 0.876**.
- Separation margin: **+0.003** to **+0.088**. Not usable.

**SpeechBrain ECAPA-TDNN, same enrollment:**
- Same-speaker held-out: 0.897 - 0.931.
- Different File 1: **0.321 - 0.415**.
- Yogesh: 0.072 - 0.372.
- GS-original: 0.171 - 0.423.
- Separation margin: **+0.473**. Any threshold in [0.43, 0.89] works.

Decision: **swap Resemblyzer for ECAPA-TDNN** in production.

---

## Decisions taken this session

1. **ASR**: switch `app/services/transcribe.py` from `saarika:v2.5` to
   `saaras:v3` with `mode="codemix"`, `language_code="hi-IN"`.
2. **Biometric**: swap `app/services/verify_speaker.py` from Resemblyzer
   to SpeechBrain ECAPA-TDNN. Thresholds rebased to
   `strict=0.70, medium=0.55, loose=0.40`.
3. **Classifier**: prompt-level changes — forbid guessing missing slots;
   make `confidence` mandatory with a clear band.
4. **DB impact**: VoiceProfile embeddings change from 256-dim to 192-dim.
   Any users already enrolled need to re-enroll. For fresh prototype
   handoff this is acceptable; noted in HANDOVER.md.
5. **Not doing now**: contact-list context in the classifier prompt
   (needs its own schema decision per CLAUDE_CODE_KICKOFF's "things to
   flag, not solve" list for three-layer schema changes).

---

## Pointers

- Code changes: see updated `SPEC.md`.
- New friction items added: `SCHEMA_NOTES.md`.
- Handover instructions: `HANDOVER.md`.
- Round-2 data collection: `recordings/DATA_COLLECTION_BRIEF_v2.md`.
- Status ledger: `status_22_04_26.txt`.

---

## Cost of this session (Sarvam STT)

- Initial two-file transcription: ~4 min audio × ₹0.50 = ₹2
- Seven-variant sweep: 7 × ~4 min × ₹0.50 = ₹14
- Yogesh folder (6 clips): ~2 × 20s total × ₹0.50 ≈ ₹0.30
- GS folder (14 clips): ~2 × 60s total × ₹0.50 ≈ ₹1
- Total Sarvam spend: under ₹20.

Gemini classifier: ~40 calls at ~200 input tokens + ~150 output tokens
× Flash-Lite pricing = ~₹0.20.

Biometric: no API cost, all local inference.
