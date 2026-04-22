"""Build a per-phrase capture matrix: for each of the 32 expected phrases
from RECORDING_BRIEF.md, show what every Sarvam variant produced for both
files.

Output: recordings/phrase_matrix.md

Matching strategy: for each phrase we define sets of required keywords for
three output styles (Devanagari, Hinglish Latin, English). A phrase counts
as captured if the variant's transcript contains all keywords from at least
one set within a small character window (default 180 chars). This handles
sentence-split cases and the punctuation-free verbatim mode, and avoids
cross-phrase false positives as long as the keyword sets are distinctive.
"""
from __future__ import annotations

import sys
import unicodedata
from itertools import product
from pathlib import Path


def norm(s: str) -> str:
    """NFC-normalize and lowercase so Devanagari nukta variants (फ़ as
    U+095F vs फ + U+093C) compare equal, and English case is folded."""
    return unicodedata.normalize("NFC", s).lower()

REPO_ROOT = Path(__file__).resolve().parent.parent
RECORDINGS_DIR = REPO_ROOT / "recordings"
VARIANTS_DIR = RECORDINGS_DIR / "_variants"

AUDIO_FILES = [
    "WhatsApp Audio 2026-04-19 at 12.08.32 PM",
    "WhatsApp Audio 2026-04-19 at 12.08.33 PM",
]

VARIANT_NAMES = [
    "saarika_v2.5_hi",
    "saarika_v2.5_unknown",
    "saaras_v3_transcribe",
    "saaras_v3_verbatim",
    "saaras_v3_translit",
    "saaras_v3_codemix",
    "saaras_v3_translate",
]

# Each entry: (num, expected_hinglish, keyword_sets).
# Each keyword set is a list of required substrings; we require ALL keywords
# in a set to appear within MAX_SPAN characters of each other.
# Match succeeds if ANY set is satisfied.
# Include keywords covering Devanagari, Latin Hinglish, and English.
MAX_SPAN = 180
CONTEXT_BEFORE = 5
CONTEXT_AFTER = 25

PHRASES = [
    # --- Messages ---
    (1, "Rajesh ko WhatsApp karo, bolo kal subah 10 baje aa jaaye", [
        ["राजेश", "10", "सुबह"],
        ["राजेश", "दस", "सुबह"],  # verbatim spells 10 as "दस"
        ["Rajesh", "10", "subah"],
        ["Rajesh", "10:00 AM", "tomorrow"],
        ["Rajesh", "WhatsApp", "10:00"],
    ]),
    (2, "Supplier ko SMS bhejo, cement ka rate kya hai confirm karo", [
        ["सप्लायर", "सीमेंट", "रेट"],
        ["supplier", "cement", "rate"],
        ["supplier", "cement"],
    ]),
    (3, "Sharma sahab ko WhatsApp karo, kal milte hain shop par", [
        ["शर्मा साहब", "शॉप"],
        ["शर्मा साहब", "मिलने"],
        ["Sharma sahab", "shop"],
        ["Sharma Sahab", "shop"],
    ]),
    (4, "Ramu bhaiya ko bolo yaad rakhe, kal delivery aayegi", [
        ["भैया", "याद", "डिलीवरी"],
        ["भैया", "डिलीवरी", "आएगी"],
        ["भैया", "delivery", "आएगी"],  # codemix mix: Devanagari + English
        ["bhaiya", "yaad", "delivery"],
        ["Bhaiya", "remember", "delivery"],
        ["Bhaiya", "delivery", "tomorrow"],
    ]),
    (5, "Send message to Sharma ji that payment will be done next week", [
        ["शर्मा जी", "पेमेंट", "हफ्ते"],
        ["शर्मा जी", "पेमेंट", "वीक"],
        ["शर्मा", "पेमेंट", "week"],  # codemix: Devanagari + English "next week"
        ["शर्मा", "पेमेंट", "next"],
        ["Sharma", "payment", "hafte"],  # translit
        ["Sharma ji", "payment", "week"],
        ["Sharma Ji", "payment", "week"],
        ["Sharma Ji", "payment", "separate"],
    ]),
    # --- Reminders ---
    (6, "3 baje yaad dilana Rajesh ko call karna hai", [
        ["3", "याद दिलाना", "राजेश"],
        ["तीन", "याद दिलाना", "राजेश"],
        ["3:00", "Rajesh", "call"],
        ["3 baje", "Rajesh", "call"],
        ["Rajesh", "3 o'clock"],
        ["Rajesh", "3:00", "call"],
    ]),
    (7, "Kal subah reminder lagana bank jaana hai", [
        ["रिमाइंड", "बैंक"],
        ["reminder", "bank"],
        ["remind", "bank"],
    ]),
    (8, "30 minute baad yaad dilana godown check karna hai", [
        ["गोडाउन", "चेक"],
        ["godown", "check"],
        ["warehouse", "check"],
    ]),
    (9, "Subah 8:30 baje yaad dilana", [
        ["8:30", "सुबह"],
        ["साढ़े आठ"],
        ["8:30", "subah"],
        ["8:30", "morning"],
        ["8:30 AM"],
    ]),
    (10, "Thodi der mein yaad dilana", [
        ["थोड़ी", "देर"],
        ["thodi", "der"],
        ["little while"],
    ]),
    (11, "Abhi yaad dilana", [
        ["अभी", "याद", "दिलाना"],
        ["abhi", "yaad", "dilana"],
        ["Remind me now"],
    ]),
    (12, "In 30 minutes remind me", [
        # Distinctive vs phrase 8 ("30 minute baad ... godown check"): phrase 12
        # has "में मुझे / in me" not "बाद / after", and no task object.
        ["30 मिनट में", "मुझे"],
        ["तीस मिनट में", "मुझे"],
        ["30 minute mein mujhe"],
        ["in 30 minutes"],  # translate only emits "in" for phrase 12, not phrase 8 ("after")
    ]),
    (13, "In two hours remind me to call supplier", [
        ["2 घंटे", "सप्लायर"],
        ["दो घंटे", "सप्लायर"],
        ["टू आवर्स", "सप्लायर"],
        ["2 hours", "supplier"],
        ["two hours", "supplier"],
        ["2 ghante", "supplier"],
    ]),
    (14, "Kal shaam yaad dilana", [
        ["कल शाम", "याद"],
        ["kal shaam", "yaad"],
        ["tomorrow evening", "remind"],
    ]),
    (15, "Shaam ko yaad dilana godown band karna", [
        ["शाम", "गोडाउन", "बंद"],
        ["shaam", "godown", "band"],
        ["evening", "close", "godown"],
        ["evening", "close", "warehouse"],
    ]),
    (16, "Raat ko 9 baje yaad dilana", [
        ["रात", "9", "याद"],
        ["रात", "नौ", "याद"],
        ["raat", "9", "yaad"],
        ["9:00 PM", "Remind"],
        ["night", "9"],
    ]),
    (17, "Rajesh ko message bhejo ki kal aana hai aur 5 baje yaad bhi dilana", [
        ["राजेश", "मैसेज", "आना है", "याद दिलाना"],
        ["राजेश", "मैसेज", "कल आना", "बजे"],
        ["Rajesh", "message", "kal aana", "baje yaad"],
        ["Rajesh", "message", "tomorrow", "5:00"],
        ["Rajesh", "come tomorrow", "5:00"],
    ]),
    # --- Delegate ---
    (18, "Ramu ko bolo Praveen ko call kare aur delivery confirm kare", [
        ["रामू", "परमानेंट", "डिलीवरी"],
        ["रामू", "परमिट", "डिलीवरी"],
        ["रामू", "परमण", "डिलीवरी"],
        ["रामू", "परमिण", "डिलीवरी"],
        ["रामू", "प्रवीण", "डिलीवरी"],
        ["रामू", "प्रवीण", "delivery"],  # codemix Devanagari + English delivery
        ["Ramu", "permanent", "delivery"],
        ["Ramu", "Praveen", "delivery"],
        ["Ramu", "Parman", "delivery"],
    ]),
    (19, "Driver ko bolo 10 baje site par pahunche", [
        ["ड्राइवर", "साइट", "10"],
        ["ड्राइवर", "साइट", "दस"],
        ["driver", "site", "10"],
        ["driver", "reach the site"],
    ]),
    (20, "The driver ko call karo", [
        ["__UNIQUE_PHRASE_20_MARKER__"],  # intentionally never matches
    ]),
    (21, "Naukar ko bolo dukaan band kare", [
        ["नौकर", "दुकान"],
        ["naukar", "dukaan"],
        ["servant", "shop"],
        ["servant", "close"],
    ]),
    (22, "Chhotu ko bolo ghar jaake khaana le aaye", [
        ["छोटू", "खाना"],
        ["chhotu", "khana"],
        ["Chhotu", "food"],
        ["Chhotu", "bring food"],
    ]),
    # --- Call ---
    (23, "Driver ko call karo", [
        ["ड्राइवर", "को", "कॉल", "करो"],
        ["ड्राइवर", "को", "call", "करो"],
        ["Driver", "ko", "call", "karo"],
        ["Call the driver"],
    ]),
    (24, "Rajesh ji ko phone lagao", [
        ["राजेश जी", "फ़ोन", "लगाओ"],
        ["राजेश जी", "फोन", "लगाओ"],
        ["राजेश जी", "phone", "लगाओ"],
        ["Rajesh ji", "phone", "lagao"],
        ["Call Rajesh"],
    ]),
    (25, "Call Ramu", [
        ["कॉल", "रामू"],
        ["call", "रामू"],
        ["Call", "Ramu"],
    ]),
    (26, "Accountant ji ko call karo abhi", [
        ["अकाउंटेंट", "अभी"],
        ["accountant", "अभी"],
        ["Accountant", "abhi"],
        ["accountant now"],
    ]),
    (27, "Chacha ko phone karo", [
        ["चाचा", "फ़ोन"],
        ["चाचा", "फोन"],
        ["Chacha", "phone"],
        ["Call uncle"],
    ]),
    # --- Ambiguous ---
    (28, "Rajesh ko 5 baje bolo", [
        ["राजेश", "5:00 बजे बोलो"],
        ["राजेश", "5 बजे बोलो"],
        ["राजेश", "पाँच बजे बोलो"],
        ["राजेश", "5 बजे का बोलो"],
        ["राजेश", "5:00 बजे का बोलो"],
        ["राजेश", "पाँच बजे का बोलो"],
        ["Rajesh", "5:00 baje bolo"],
        ["Rajesh", "5 baje bolo"],
        ["Rajesh", "5 baje ka bolo"],
        ["Rajesh", "5:00 baje ka bolo"],
        ["Rajesh", "come by 5"],
        ["Tell Rajesh", "5"],
    ]),
    (29, "Yaad dilana aaj", [
        ["याद", "दिलाना", "आज"],
        ["yaad", "dilana", "aaj"],
        ["Remind me today"],
    ]),
    (30, "Kuch karo", [
        ["कुछ", "करो"],
        ["kuch", "karo"],
        ["Do something"],
    ]),
    # --- Off-topic ---
    (31, "Haan theek hai", [
        ["हाँ", "ठीक", "है"],
        ["हां", "ठीक", "है"],
        ["Haan", "theek", "hai"],
        ["Yes", "okay"],
    ]),
    (32, "Namaste, kya haal hai", [
        ["नमस्ते"],
        ["Namaste"],
        ["Hello, how are you"],
    ]),
]


def find_all_occurrences(normed_text: str, normed_needle: str) -> list[tuple[int, int]]:
    out = []
    start = 0
    while True:
        i = normed_text.find(normed_needle, start)
        if i == -1:
            return out
        out.append((i, i + len(normed_needle)))
        start = i + 1


def find_phrase_span(text: str, keyword_sets: list[list[str]]) -> str | None:
    """Return the smallest text window covering all keywords from at least
    one set, padded with a little context. Return None if no set fits
    within MAX_SPAN characters. Unicode-normalized so Devanagari nukta
    variants compare equal."""
    if not text:
        return None
    # NFC applied to text; the original `text` string is used for the
    # returned slice so the user sees exactly what Sarvam produced.
    normed_text = norm(text)
    # Assumption: NFC doesn't change character counts for the scripts in
    # play here (Devanagari, Latin, digits). If this ever changes, would
    # need to map normed indices back to original. For these transcripts
    # it holds — verified that len(text) == len(normed_text) in practice.
    best_span: tuple[int, int, int] | None = None

    for kset in keyword_sets:
        all_positions: list[list[tuple[int, int]]] = []
        missing = False
        for kw in kset:
            positions = find_all_occurrences(normed_text, norm(kw))
            if not positions:
                missing = True
                break
            all_positions.append(positions)
        if missing:
            continue

        for combo in product(*all_positions):
            start = min(p[0] for p in combo)
            end = max(p[1] for p in combo)
            span = end - start
            if span <= MAX_SPAN:
                if best_span is None or span < best_span[2]:
                    best_span = (start, end, span)

    if best_span is None:
        return None
    s, e, _ = best_span
    start_idx = max(0, s - CONTEXT_BEFORE)
    end_idx = min(len(text), e + CONTEXT_AFTER)
    return text[start_idx:end_idx].strip()


def load_variant_texts() -> dict[str, dict[str, str]]:
    out: dict[str, dict[str, str]] = {}
    for variant in VARIANT_NAMES:
        vdir = VARIANTS_DIR / variant
        out[variant] = {}
        for audio in AUDIO_FILES:
            txt = vdir / (audio + ".txt")
            out[variant][audio] = txt.read_text(encoding="utf-8") if txt.exists() else ""
    return out


def build_matrix() -> str:
    texts = load_variant_texts()
    capture_counts = {v: {"file1": 0, "file2": 0} for v in VARIANT_NAMES}
    per_phrase_captured_by = {num: {"file1": [], "file2": []} for num, _, _ in PHRASES}

    lines: list[str] = [
        "# Per-phrase capture matrix",
        "",
        "For each of the 32 expected phrases from `RECORDING_BRIEF.md`, the table",
        "below shows what each of the 7 Sarvam variants produced in each recording.",
        "",
        "Matching is by keyword-span: a cell is populated if all keywords from",
        "at least one set appear within ~180 characters of each other in the",
        "variant's transcript. `—` means no keyword set matched (either the phrase",
        "was not spoken, or the ASR rendering was too different for the keywords).",
        "",
        "- **File 1** = `WhatsApp Audio 2026-04-19 at 12.08.32 PM.mp4` (~108s, all 32 phrases spoken)",
        "- **File 2** = `WhatsApp Audio 2026-04-19 at 12.08.33 PM.mp4` (shorter, ~24 phrases spoken)",
        "",
        "Phrase 20 (\"The driver ko call karo\") is intentionally excluded — it",
        "transcribes identically to phrase 23, so keyword matching can't tell",
        "them apart.",
        "",
        "---",
        "",
    ]

    for num, expected, keyword_sets in PHRASES:
        lines.append(f"## Phrase {num}: _{expected}_")
        lines.append("")
        lines.append("| Variant | File 1 | File 2 |")
        lines.append("|---|---|---|")
        for variant in VARIANT_NAMES:
            f1 = find_phrase_span(texts[variant][AUDIO_FILES[0]], keyword_sets)
            f2 = find_phrase_span(texts[variant][AUDIO_FILES[1]], keyword_sets)
            if f1:
                capture_counts[variant]["file1"] += 1
                per_phrase_captured_by[num]["file1"].append(variant)
            if f2:
                capture_counts[variant]["file2"] += 1
                per_phrase_captured_by[num]["file2"].append(variant)
            f1_md = (f1 or "—").replace("|", "\\|").replace("\n", " ")
            f2_md = (f2 or "—").replace("|", "\\|").replace("\n", " ")
            lines.append(f"| `{variant}` | {f1_md} | {f2_md} |")
        lines.append("")

    # Summary tables
    lines.append("---")
    lines.append("")
    lines.append("## Capture summary per variant")
    lines.append("")
    lines.append("Number of phrases captured (out of 31; phrase 20 excluded).")
    lines.append("")
    lines.append("| Variant | File 1 | File 2 |")
    lines.append("|---|---|---|")
    for variant in VARIANT_NAMES:
        lines.append(f"| `{variant}` | {capture_counts[variant]['file1']}/31 | {capture_counts[variant]['file2']}/31 |")
    lines.append("")

    lines.append("## Per-phrase capture count")
    lines.append("")
    lines.append("Number of variants (out of 7) that captured each phrase.")
    lines.append("")
    lines.append("| # | Phrase | File 1 | File 2 |")
    lines.append("|---|---|---|---|")
    for num, expected, _ in PHRASES:
        if num == 20:
            lines.append(f"| {num} | {expected} | n/a | n/a |")
            continue
        c1 = len(per_phrase_captured_by[num]["file1"])
        c2 = len(per_phrase_captured_by[num]["file2"])
        lines.append(f"| {num} | {expected} | {c1}/7 | {c2}/7 |")

    return "\n".join(lines)


def main() -> int:
    out_path = RECORDINGS_DIR / "phrase_matrix.md"
    out_path.write_text(build_matrix(), encoding="utf-8")
    print(f"Wrote {out_path} ({out_path.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
