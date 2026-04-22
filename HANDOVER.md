# Prototype handover — 2026-04-22

Audience: Yogesh
Purpose: Pick up this branch and run the bot end-to-end for further
testing in real conversations and, when ready, in real shops.

## Two updates in one handover

This handover bundles two related pushes from 2026-04-22:

1. **Pipeline migrations** (commit `99c5bfe`): ASR swapped to
   saaras:v3 codemix, biometric swapped to SpeechBrain ECAPA-TDNN,
   classifier prompt hardened against slot hallucination.
2. **Intent taxonomy expansion** (later commit, same day): classifier
   grew from 4 intents to 12. The new 7 (`order, collection,
   supplier_payment, inventory, price_check, worker, summary`) are
   future-phase — the bot recognises and logs them but does not yet
   act. See `SESSION_NOTES_2026-04-22_intent_expansion.md` and the
   updated `SPEC.md` for details.

Both changes apply to your test sessions too — the binary you run is
the same one AV's brother will run in Indore.

## What changed since the last time you saw this code

Full context is in `SESSION_NOTES_2026-04-22.md` (pipeline) and
`SESSION_NOTES_2026-04-22_intent_expansion.md` (taxonomy). The short
list:

| Area | Before | After |
|---|---|---|
| ASR model | `saarika:v2.5` | `saaras:v3` mode=`codemix`, lang=`hi-IN` |
| Biometric encoder | Resemblyzer (256-d) | SpeechBrain ECAPA-TDNN (192-d) |
| Biometric thresholds | strict 0.75 / medium 0.65 / loose 0.55 | strict 0.70 / medium 0.55 / loose 0.40 |
| Classifier prompt | no explicit rule against guessing missing tokens | forbids guessing; mandates confidence |
| `confidence` default | 0.0 | 0.8 (Gemini omits the field; 0.8 keeps the handler gate working) |
| Intent taxonomy | 4 (`message, reminder, delegate, call`) | 12 — added `order, collection, supplier_payment, inventory, price_check, worker, summary` as `future_phase` scope |
| Scope field | none | `scope: in_scope / future_phase / unknown` — router uses this, not intent strings |
| Future-phase storage | n/a | new `FuturePhaseLog` table capturing transcript + intent + slots for aggregation |

All production changes are in `SPEC.md`. The retroactive session record
is in `SESSION_NOTES_2026-04-22.md`. Schema friction observed during
the session is logged in `SCHEMA_NOTES.md`. Status ledger in
`status_22_04_26.txt`.

## Environment setup

```bash
cd shopsaarthi-bot
python -m venv venv
venv/Scripts/activate    # Windows
# or: source venv/bin/activate   # Mac/Linux

pip install -r requirements.txt
```

First run downloads SpeechBrain's ECAPA-TDNN weights (~80 MB) to
`.cache/spkrec-ecapa/`. This directory is gitignored. Subsequent runs
skip the download.

`.env` requirements (copy from AV or the existing .env on this machine):

```
TELEGRAM_BOT_TOKEN=...
SARVAM_API_KEY=...
GEMINI_API_KEY=...
# optional overrides:
DATABASE_URL=sqlite:///./shopsaarthi.db
LOG_LEVEL=INFO
```

Start the bot:

```bash
python -m app.main
```

## Important — re-enrollment is required

The biometric encoder switched from Resemblyzer (256-d embeddings) to
ECAPA-TDNN (192-d). Any `VoiceProfile` rows in the SQLite database
from before 2026-04-22 are incompatible with the new encoder. The
code logs a warning and skips dimension-mismatched profiles rather
than failing, so the bot still runs — but verification against a
stale profile will always fail.

For a clean start, delete the existing DB:

```bash
rm shopsaarthi.db   # or whatever DATABASE_URL points at
python -m app.db.init_db
```

Then enroll yourself via Telegram:

```
/enroll        # walks through 5-7 phrases
/voicestatus   # confirms enrollment
/security strict   # sets verification threshold
```

The enrollment flow is `app/handlers/enrollment.py` — unchanged in this
update, only the backing encoder changed.

## Smoke test — day one

Run these in order. Each step should pass before moving to the next:

1. **Bot boots cleanly**
   ```
   python -m app.main
   ```
   Look for "Loading ECAPA-TDNN speaker encoder..." on the first voice
   message, then "ECAPA-TDNN encoder ready". If the download stalls,
   check network; the model is fetched from Hugging Face.

2. **Text command round-trip**
   Send a text message to the bot: "Rajesh ko WhatsApp karo, kal subah 10 baje aana hai"
   Expected: bot transcribes (for text it echoes), classifies as
   `message`, shows WhatsApp tap-to-send link.

3. **Voice command round-trip (not enrolled)**
   Send a voice message before enrolling. Bot should let it through with
   a log note "User X not enrolled, allowing command through". This
   confirms the default user path works.

4. **Enrollment flow**
   `/enroll`. Bot will ask for 5-7 phrases. Say each one as a separate
   voice message. Bot confirms enrollment.

5. **Voice command round-trip (enrolled, same speaker)**
   Send a voice command. Bot should verify (look for
   "Speaker verification: ... match=True" in logs), transcribe,
   classify, route.

6. **Voice command round-trip (enrolled, different speaker)**
   Have someone else speak into your phone. Bot should reject with
   "match=False" in logs and tell the user their voice doesn't match.

7. **Known-good ASR cases** — send these voice commands in Hindi and
   check classification:
   - "3 baje yaad dilana Rajesh ko call karna hai" → intent=reminder, scope=in_scope
   - "Driver ko bolo 10 baje site par pahunche" → intent=delegate, scope=in_scope
   - "Accountant ji ko call karo abhi" → intent=call, scope=in_scope
   - "Supplier ko SMS bhejo, cement rate confirm karo" → intent=message, scope=in_scope

8. **Future-phase smoke cases** — send these and check the bot
   acknowledges with the extracted slots, does not route to a handler,
   and creates a `FuturePhaseLog` row:
   - "Cement kitna bacha hai" → intent=inventory, scope=future_phase
   - "Sharma ji ko kitna paisa dena hai" → intent=supplier_payment, scope=future_phase
   - "Rajesh ka kitna pending hai" → intent=collection, scope=future_phase, recipient_name=Rajesh
   - "Aaj kitna business hua" → intent=summary, scope=future_phase

   Quick DB check (from venv): `python -c "from app.db.session import SessionLocal; from app.db.models import FuturePhaseLog; db = SessionLocal(); [print(r.intent, r.transcript) for r in db.query(FuturePhaseLog).all()]"`

## Known issues you will likely hit

None of these are blocking for the prototype; they're documented so you
can recognise them as expected rather than regressions.

1. **"Praveen" often transcribes as "Permanent" or "Parman"** in some
   audio conditions. All `saaras:v3` modes have this issue in some
   clips; other clips get it right. The contact resolver can fuzzy-match
   this if Praveen is in the shop's contacts — but it's a weak signal.
   Context engineering (passing known contact names to the Gemini
   classifier prompt) is the next fix; intentionally not in this prototype.

2. **"Accountant ji" sometimes transcribes as "Mountain G" / "माउंटेन जी"**.
   Same class of issue. Contact resolver with role="accountant" in the
   shop's contact DB would recover this.

3. **"Ramu" sometimes transcribes as "Aamu" or "Naamu"**. Spelling-
   variant class of error.

4. **"Shop par" transcribed as "subah sahab par"** on one clip. The
   classifier still correctly classified the utterance as `message`.

5. **Classifier confidence is usually 0.8 (the default), not a value
   Gemini computed**. Gemini omits the confidence field on successful
   classifications. The handler's `confidence < 0.5` gate still works
   because the classify fallback path explicitly emits 0.0.

6. **`recordings/intent_classification.md`** has the 2026-04-22 run of
   the classifier on short clips — 15/18 translit, 14/18 Devanagari
   intent accuracy excluding ambiguous fragments. The 3 misses are all
   defensible (either genuine ambiguity or missing recipient).

## If something breaks

### ASR regresses for a specific speaker
Try swapping `mode="codemix"` → `mode="transcribe"` (forces Devanagari)
or `mode="translit"` (forces Hinglish) in `app/services/transcribe.py`.
One-line change; no other edits needed.

### Biometric latency is high
First call pays model-load cost (a few seconds). If subsequent calls
are also slow, check `.cache/spkrec-ecapa/` exists and isn't being
re-downloaded. Reduce load by moving to GPU: change
`run_opts={"device": "cpu"}` to `"device": "cuda"` in
`app/services/verify_speaker.py:get_encoder`.

### Biometric rejects the enrolled user
Likely threshold too tight or enrollment audio too short. Re-enroll
with longer phrases, or drop threshold from `strict` to `medium` via
`/security medium`.

### Rollback biometric to Resemblyzer
If ECAPA-TDNN causes install or runtime issues in your environment,
revert `app/services/verify_speaker.py` from git history and restore
`resemblyzer==0.1.4` + `webrtcvad-wheels` in `requirements.txt`. Then
invalidate existing profiles (they're ECAPA 192-d; Resemblyzer
generates 256-d) by resetting the DB as above.

### Rollback ASR to saarika
Change the `data` dict in `app/services/transcribe.py` back to
`{"model": "saarika:v2.5", "language_code": "hi-IN"}` and remove the
`mode` key. Nothing else changes.

## Where to put new recordings for testing

Drop any new audio under `recordings/<your_folder>/` (e.g.
`recordings/test_2026-04-25/`). The scripts in `scripts/` work against
any folder:

```bash
# Transcribe a folder with both Hinglish and Devanagari modes:
python scripts/transcribe_folder.py recordings/test_2026-04-25/

# Run biometric enrollment/verification against a folder:
# (uses File 2 as enrollment; change to your file)
python scripts/test_biometric_ecapa.py
```

The Round-2 data collection brief for market visits is at
`recordings/DATA_COLLECTION_BRIEF_v2.md` — 144 phrases across 12
categories, three time-tiers, consent script. Use this when going to
new shops.

## Contact for questions

- Product + scope: AV
- Sarvam API issues: AV first, Sarvam support if escalated
- Gemini API issues: Google AI Studio console
- SpeechBrain issues: project is on GitHub, or fall back to Resemblyzer
  per rollback section above.

## Commits to read before touching anything

```
git log --oneline -20
```

The last three commits before this handover tell most of the story.
This handover commit bundles the 2026-04-22 session's production
changes with retroactive SPEC and session notes. Treat this branch as
the baseline for your next round of testing.
