# Sarvam STT variant comparison — Garv's recordings

All 7 variants run on both audio files. Each took ~16s (all 14 transcriptions
in ~113s total). Raw outputs under `recordings/_variants/<variant>/`.

Variants tested:

| Variant                 | Model         | Mode        | Lang   |
|-------------------------|---------------|-------------|--------|
| saarika_v2.5_hi         | saarika:v2.5  | (n/a)       | hi-IN  |
| saarika_v2.5_unknown    | saarika:v2.5  | (n/a)       | unknown|
| saaras_v3_transcribe    | saaras:v3     | transcribe  | hi-IN  |
| saaras_v3_verbatim      | saaras:v3     | verbatim    | hi-IN  |
| saaras_v3_translit      | saaras:v3     | translit    | hi-IN  |
| saaras_v3_codemix       | saaras:v3     | codemix     | hi-IN  |
| saaras_v3_translate     | saaras:v3     | translate   | hi-IN  |

---

## Where variants actually differ

Phrase coverage is near-identical across variants (same audio). The interesting
differences are on **proper nouns**, **script / language preservation**, and a
few **number / filler** interpretations.

### 1. Proper noun: "Ramu bhaiya" (File 1, phrase 4)

| Variant               | Output     | Correct? |
|-----------------------|------------|----------|
| saarika_v2.5_hi       | नामू       | ❌ (Naamu) |
| saarika_v2.5_unknown  | नामू       | ❌ (Naamu) |
| saaras_v3_transcribe  | रामू       | ✓        |
| saaras_v3_verbatim    | रामू       | ✓        |
| saaras_v3_translit    | Ramu       | ✓        |
| saaras_v3_codemix     | रामू       | ✓        |
| saaras_v3_translate   | Ramu       | ✓        |

**saaras:v3 fixes the "Ramu → Naamu" error that saarika:v2.5 makes on both language settings.** File 2 has everyone getting it right.

### 2. Proper noun: "Praveen" (File 1, phrase 18)

| Variant               | Output                | Correct? |
|-----------------------|-----------------------|----------|
| saarika_v2.5_hi       | परमानेंट (Permanent)  | ❌       |
| saarika_v2.5_unknown  | परमानेंट (Permanent)  | ❌       |
| saaras_v3_transcribe  | परमिट (Permit)        | ❌       |
| saaras_v3_verbatim    | परमिण (Parmin)        | ❌       |
| saaras_v3_translit    | permanent             | ❌       |
| saaras_v3_codemix     | परमण (Parman)         | ❌       |
| saaras_v3_translate   | Parman                | ❌       |

**No variant handles "Praveen" correctly in File 1.** All variants handle it correctly in File 2 → confirmed as pronunciation-dependent, not a systematic gap. Still useful as an adversarial test for the contact resolver.

### 3. English-in-Hindi handling (File 2, calls + reminders)

Illustrative segment from File 2 ("Rajesh ji ko phone lagao. Accountant ko call karo abhi. Call Ramu"):

| Variant               | Output |
|-----------------------|--------|
| saarika_v2.5_hi       | राजेश जी को फ़ोन लगाओ। अकाउंटेंट को कॉल करो अभी। कॉल रामू। |
| saaras_v3_transcribe  | राजेश जी को फ़ोन लगाओ, अकाउंटेंट को कॉल करो अभी, कॉल रामू। |
| saaras_v3_codemix     | राजेश जी को phone लगाओ accountant को call करो अभी call रामू |
| saaras_v3_translit    | Rajesh ji ko phone lagao. Accountant ko call karo abhi. Call Ramu. |
| saaras_v3_translate   | Call Rajesh ji. Call the accountant now. Call Ramu. |

- **codemix** preserves English tokens in Latin script mixed with Devanagari — the most faithful representation of how a shopkeeper actually speaks.
- **translit** produces pure Hinglish Latin — matches CLAUDE.md's preference for user-facing strings.
- **translate** loses the Hindi altogether — the speaker's "phone lagao" (WhatsApp call) and "call karo" (regular call) collapse to the same "Call …" — **a semantic loss for the intent classifier**.

### 4. Number interpretation: "30 minute" (File 1, phrase 8)

| Variant               | Output              |
|-----------------------|---------------------|
| saarika_v2.5_hi       | 30 मिनट ✓          |
| saarika_v2.5_unknown  | 30 मिनट ✓          |
| saaras_v3_transcribe  | 30 मिनट ✓          |
| saaras_v3_verbatim    | बीस मिनट (20) ❌   |
| saaras_v3_translit    | 20 minute ❌       |
| saaras_v3_codemix     | 30 मिनट ✓          |
| saaras_v3_translate   | 20 minutes ❌      |

**saaras:v3 verbatim/translit/translate heard "30" as "20" on this phrase.** Only an N=1 observation but worth watching — getting times wrong is worse than getting contact names wrong for a reminder bot.

### 5. Phrase 3 "kal milte hain shop par"

Captured by every variant in File 1 (slight wording variation: "मिलने शॉप पर" vs "मिलने"). Not captured by any variant in File 2 (speaker didn't say it).

### 6. Translate mode character

File 1 segment rendered by `saaras_v3_translate`:

> "Tell Rajesh to WhatsApp. Tell him to come tomorrow morning at 10:00 AM. Send an SMS to the supplier, confirm what the rate of cement is. WhatsApp Sharma Sahab to meet at the shop tomorrow. Ramu Bhaiya, remember, the delivery will come tomorrow. Send a message to Sharma Ji that the payment will be separate next week..."

Clean English. But note "payment will be **separate** next week" (should be "done") — same kind of content error as other variants, translated into English. Translate mode does not fix ASR errors, it just relocates them.

---

## Recommendation for ShopSaarthi

**Primary ASR pick: `saaras:v3` with `mode=codemix`, `language_code=hi-IN`.**

Reasons:
1. Fixes the "Ramu → Naamu" error that saarika:v2.5 makes.
2. Preserves English tokens (phone, call, accountant, WhatsApp, SMS, confirm) in their actual spoken form. The intent classifier can then route on English keywords without worrying about romanization inconsistencies.
3. Matches how Indian shopkeepers actually speak (code-mixed Hindi-English), which is exactly what ShopSaarthi targets.
4. Correctly heard "30 minute" where verbatim/translit/translate heard "20".

**Secondary option: `saaras:v3` with `mode=translit`** if AV wants consistent Hinglish Latin output to match the CLAUDE.md style rule for strings. Caveat: watch for time misrecognitions (saw one in this sample).

**Avoid for primary flow:** `saaras:v3 mode=translate` — it collapses "phone lagao" and "call karo" into the same English verb, which is useful semantic signal in the original Hindi. Useful only as a fallback for debugging / human review in English.

**No strong reason to keep saarika:v2.5 as primary** given saaras:v3 is same cost/latency and better on proper nouns. But keep it available as a fallback if saaras:v3 shows regressions in field testing.

---

## Next steps for the field-test harness (CLAUDE.md todo #1)

- Run classifier (`app/services/classify.py`) against each variant's transcript and measure intent + slot accuracy. The ASR output is an input, not the end metric — what matters is whether the classifier gets `intent`, `contact_name`, `time`, `message_body` right.
- Add "Praveen" and a handful of similarly-problematic Indic names to a proper-noun stress-test fixture.
- If saaras:v3 codemix becomes primary, update `app/services/transcribe.py` to use `model="saaras:v3"`, `mode="codemix"` — but verify the sync endpoint accepts the `mode` parameter (it's called out in docs as saaras:v3-only). Add a small test against a short wav to confirm before flipping.
