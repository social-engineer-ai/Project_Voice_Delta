"""Build a clean 'expected vs actual' comparison so you can see, for each
of the 32 brief phrases, exactly what Sarvam transcribed.

Key difference from build_phrase_matrix.py: that one shows arbitrary
character windows around a keyword match, which starts mid-word and
drags in pieces of adjacent phrases. This one expands each hit to the
enclosing sentence (split on . ? ! ।) so the cell shows a proper phrase.

Output: recordings/expected_vs_actual.md

For readability we show two variants per file:
- saaras:v3 translit — Hinglish Latin output; lines up with the brief's format
- saarika:v2.5 hi — current bot default in Devanagari

"""
from __future__ import annotations

import re
import sys
import unicodedata
from itertools import product
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
RECORDINGS_DIR = REPO_ROOT / "recordings"
VARIANTS_DIR = RECORDINGS_DIR / "_variants"

AUDIO_FILE_1 = "WhatsApp Audio 2026-04-19 at 12.08.32 PM"
AUDIO_FILE_2 = "WhatsApp Audio 2026-04-19 at 12.08.33 PM"

# Variants we'll display. translit first (Hinglish, matches the brief's script),
# then saarika Devanagari so you can judge accuracy independent of transliteration.
DISPLAY_VARIANTS = [
    ("saaras_v3_translit", "Sarvam output (saaras:v3 translit — Hinglish)"),
    ("saarika_v2.5_hi",    "Sarvam output (saarika:v2.5 — Devanagari, current default)"),
]

MAX_SPAN = 180  # keyword span limit; same as matrix script


def norm(s: str) -> str:
    return unicodedata.normalize("NFC", s).lower()


# Phrase definitions: (num, expected_hinglish, keyword_sets_per_variant_type)
# keyword_sets_per_variant_type maps variant style → list of keyword sets.
# We want narrow keywords so the sentence that gets extracted is the right one.
PHRASES: list[tuple[int, str, dict[str, list[list[str]]]]] = [
    (1, "Rajesh ko WhatsApp karo, bolo kal subah 10 baje aa jaaye", {
        "devanagari": [["राजेश", "10", "सुबह"], ["राजेश", "दस", "सुबह"]],
        "latin":      [["Rajesh", "10", "subah"]],
    }),
    (2, "Supplier ko SMS bhejo, cement ka rate kya hai confirm karo", {
        "devanagari": [["सप्लायर", "सीमेंट", "रेट"]],
        "latin":      [["supplier", "cement", "rate"]],
    }),
    (3, "Sharma sahab ko WhatsApp karo, kal milte hain shop par", {
        "devanagari": [["शर्मा साहब", "शॉप"], ["शर्मा साहब", "मिलने"]],
        "latin":      [["Sharma sahab", "shop"]],
    }),
    (4, "Ramu bhaiya ko bolo yaad rakhe, kal delivery aayegi", {
        "devanagari": [["भैया", "याद", "डिलीवरी"], ["भैया", "याद", "delivery"]],
        "latin":      [["bhaiya", "yaad", "delivery"]],
    }),
    (5, "Send message to Sharma ji that payment will be done next week", {
        "devanagari": [["शर्मा जी", "पेमेंट", "हफ्ते"], ["शर्मा जी", "पेमेंट", "वीक"],
                       ["शर्मा", "पेमेंट", "next"], ["शर्मा", "पेमेंट", "week"]],
        "latin":      [["Sharma", "payment", "hafte"], ["Sharma", "payment", "week"]],
    }),
    (6, "3 baje yaad dilana Rajesh ko call karna hai", {
        "devanagari": [["3", "याद दिलाना", "राजेश"], ["तीन", "याद दिलाना", "राजेश"]],
        "latin":      [["3:00 baje", "Rajesh", "call"], ["3 baje", "Rajesh", "call"]],
    }),
    (7, "Kal subah reminder lagana bank jaana hai", {
        "devanagari": [["रिमाइंड", "बैंक", "सुबह"]],
        "latin":      [["reminder", "bank"], ["remind", "bank"]],
    }),
    (8, "30 minute baad yaad dilana godown check karna hai", {
        "devanagari": [["गोडाउन", "चेक", "मिनट"]],
        "latin":      [["godown", "check", "minute"]],
    }),
    (9, "Subah 8:30 baje yaad dilana", {
        "devanagari": [["8:30", "सुबह"], ["साढ़े आठ"]],
        "latin":      [["8:30", "subah"]],
    }),
    (10, "Thodi der mein yaad dilana", {
        "devanagari": [["थोड़ी", "देर", "याद"]],
        "latin":      [["thodi", "der", "yaad"]],
    }),
    (11, "Abhi yaad dilana", {
        "devanagari": [["अभी", "याद", "दिलाना"]],
        "latin":      [["abhi", "yaad", "dilana"]],
    }),
    (12, "In 30 minutes remind me", {
        "devanagari": [["30 मिनट में", "मुझे"], ["तीस मिनट में", "मुझे"]],
        "latin":      [["30 minute mein mujhe"]],
    }),
    (13, "In two hours remind me to call supplier", {
        "devanagari": [["2 घंटे", "सप्लायर"], ["दो घंटे", "सप्लायर"], ["टू आवर्स", "सप्लायर"]],
        "latin":      [["2 hours", "supplier"], ["two hours", "supplier"], ["2 ghante", "supplier"]],
    }),
    (14, "Kal shaam yaad dilana", {
        "devanagari": [["कल शाम", "याद"]],
        "latin":      [["kal shaam", "yaad"]],
    }),
    (15, "Shaam ko yaad dilana godown band karna", {
        "devanagari": [["शाम", "गोडाउन", "बंद"]],
        "latin":      [["shaam", "godown", "band"]],
    }),
    (16, "Raat ko 9 baje yaad dilana", {
        "devanagari": [["रात", "9", "याद"], ["रात", "नौ", "याद"]],
        "latin":      [["raat", "9", "yaad"]],
    }),
    (17, "Rajesh ko message bhejo ki kal aana hai aur 5 baje yaad bhi dilana", {
        "devanagari": [["राजेश", "मैसेज", "आना है", "याद"], ["राजेश", "मैसेज", "कल आना", "बजे"]],
        "latin":      [["Rajesh", "message", "kal aana", "baje"]],
    }),
    (18, "Ramu ko bolo Praveen ko call kare aur delivery confirm kare", {
        "devanagari": [
            ["रामू", "परमानेंट", "डिलीवरी"], ["रामू", "परमिट", "डिलीवरी"],
            ["रामू", "परमण", "डिलीवरी"],    ["रामू", "परमिण", "डिलीवरी"],
            ["रामू", "प्रवीण", "डिलीवरी"],  ["रामू", "प्रवीण", "delivery"],
        ],
        "latin":      [["Ramu", "permanent", "delivery"], ["Ramu", "Praveen", "delivery"]],
    }),
    (19, "Driver ko bolo 10 baje site par pahunche", {
        "devanagari": [["ड्राइवर", "साइट", "10"], ["ड्राइवर", "साइट", "दस"]],
        "latin":      [["driver", "site", "10"]],
    }),
    (20, "The driver ko call karo", {
        "devanagari": [["__never_matches__"]],
        "latin":      [["__never_matches__"]],
    }),
    (21, "Naukar ko bolo dukaan band kare", {
        "devanagari": [["नौकर", "दुकान"]],
        "latin":      [["naukar", "dukaan"]],
    }),
    (22, "Chhotu ko bolo ghar jaake khaana le aaye", {
        "devanagari": [["छोटू", "खाना"]],
        "latin":      [["chhotu", "khana"]],
    }),
    (23, "Driver ko call karo", {
        "devanagari": [["ड्राइवर", "को", "कॉल", "करो"], ["ड्राइवर", "को", "call", "करो"]],
        "latin":      [["Driver", "ko", "call", "karo"]],
    }),
    (24, "Rajesh ji ko phone lagao", {
        "devanagari": [["राजेश जी", "फ़ोन", "लगाओ"], ["राजेश जी", "फोन", "लगाओ"],
                       ["राजेश जी", "phone", "लगाओ"]],
        "latin":      [["Rajesh ji", "phone", "lagao"]],
    }),
    (25, "Call Ramu", {
        "devanagari": [["कॉल", "रामू"], ["call", "रामू"]],
        "latin":      [["Call", "Ramu"]],
    }),
    (26, "Accountant ji ko call karo abhi", {
        "devanagari": [["अकाउंटेंट", "अभी"], ["accountant", "अभी"]],
        "latin":      [["Accountant", "abhi"]],
    }),
    (27, "Chacha ko phone karo", {
        "devanagari": [["चाचा", "फ़ोन"], ["चाचा", "फोन"]],
        "latin":      [["Chacha", "phone"]],
    }),
    (28, "Rajesh ko 5 baje bolo", {
        "devanagari": [
            ["राजेश", "5:00 बजे बोलो"], ["राजेश", "5 बजे बोलो"],
            ["राजेश", "पाँच बजे बोलो"],
            ["राजेश", "5 बजे का बोलो"], ["राजेश", "5:00 बजे का बोलो"],
            ["राजेश", "पाँच बजे का बोलो"],
        ],
        "latin":      [
            ["Rajesh", "5:00 baje bolo"], ["Rajesh", "5 baje bolo"],
            ["Rajesh", "5 baje ka bolo"], ["Rajesh", "5:00 baje ka bolo"],
        ],
    }),
    (29, "Yaad dilana aaj", {
        "devanagari": [["याद", "दिलाना", "आज"]],
        "latin":      [["yaad", "dilana", "aaj"]],
    }),
    (30, "Kuch karo", {
        "devanagari": [["कुछ", "करो"]],
        "latin":      [["kuch", "karo"]],
    }),
    (31, "Haan theek hai", {
        "devanagari": [["हाँ", "ठीक", "है"], ["हां", "ठीक", "है"]],
        "latin":      [["Haan", "theek", "hai"]],
    }),
    (32, "Namaste, kya haal hai", {
        "devanagari": [["नमस्ते"]],
        "latin":      [["Namaste"]],
    }),
]


def is_latin_variant(variant_name: str) -> bool:
    return "translit" in variant_name or "translate" in variant_name


def find_all_occurrences(normed_text: str, needle: str) -> list[tuple[int, int]]:
    out = []
    start = 0
    while True:
        i = normed_text.find(needle, start)
        if i == -1:
            return out
        out.append((i, i + len(needle)))
        start = i + 1


def find_best_span(text: str, keyword_sets: list[list[str]]) -> tuple[int, int] | None:
    if not text:
        return None
    normed = norm(text)
    best: tuple[int, int, int] | None = None
    for kset in keyword_sets:
        positions: list[list[tuple[int, int]]] = []
        missing = False
        for kw in kset:
            pos = find_all_occurrences(normed, norm(kw))
            if not pos:
                missing = True
                break
            positions.append(pos)
        if missing:
            continue
        for combo in product(*positions):
            s = min(p[0] for p in combo)
            e = max(p[1] for p in combo)
            span = e - s
            if span <= MAX_SPAN and (best is None or span < best[2]):
                best = (s, e, span)
    return (best[0], best[1]) if best else None


# Sentence splitter: treat . ? ! and । as boundaries. Also treat a run of
# 3+ spaces as a soft boundary for verbatim mode (which lacks punctuation).
_SENT_BOUNDARIES = re.compile(r"[.?!।]")


def expand_to_sentence(text: str, start: int, end: int) -> str:
    """Expand [start, end) to the nearest sentence boundary on each side."""
    # Find boundary before start
    left = 0
    for m in _SENT_BOUNDARIES.finditer(text, 0, start):
        left = m.end()
    # Find boundary after end
    right = len(text)
    m = _SENT_BOUNDARIES.search(text, end)
    if m:
        right = m.end()
    return text[left:right].strip().strip(",;:")


def trim_around_span(sentence_text: str, kw_span_start: int, kw_span_end: int, max_len: int = 150) -> str:
    """If the enclosing sentence is longer than max_len, trim it to a window
    centered on the keyword span, with ellipses at the ends. Keeps the table
    readable when ASR output lacks punctuation for a long run."""
    if len(sentence_text) <= max_len:
        return sentence_text
    # Center the window on the middle of the keyword span
    center = (kw_span_start + kw_span_end) // 2
    half = max_len // 2
    start = max(0, center - half)
    end = min(len(sentence_text), start + max_len)
    start = max(0, end - max_len)
    prefix = "…" if start > 0 else ""
    suffix = "…" if end < len(sentence_text) else ""
    return f"{prefix}{sentence_text[start:end].strip()}{suffix}"


def extract(text: str, keyword_sets: list[list[str]]) -> str:
    span = find_best_span(text, keyword_sets)
    if not span:
        return "—"
    s, e = span
    sentence = expand_to_sentence(text, s, e)
    if not sentence:
        return "—"
    # Figure out the keyword span's position within the extracted sentence
    # so the trim stays centered on it.
    sentence_start_in_full = text.find(sentence)
    if sentence_start_in_full < 0:
        # fallback: sentence extraction may have normalized whitespace;
        # just use the middle of the sentence as the center point.
        return trim_around_span(sentence, len(sentence) // 2, len(sentence) // 2 + 1)
    kw_s_rel = s - sentence_start_in_full
    kw_e_rel = e - sentence_start_in_full
    return trim_around_span(sentence, kw_s_rel, kw_e_rel)


def load_variant(variant_name: str, audio_stem: str) -> str:
    p = VARIANTS_DIR / variant_name / (audio_stem + ".txt")
    return p.read_text(encoding="utf-8") if p.exists() else ""


def build() -> str:
    # Preload texts
    texts: dict[tuple[str, str], str] = {}
    for variant_name, _ in DISPLAY_VARIANTS:
        for audio in (AUDIO_FILE_1, AUDIO_FILE_2):
            texts[(variant_name, audio)] = load_variant(variant_name, audio)

    lines: list[str] = [
        "# Expected vs actual — what Sarvam transcribed",
        "",
        "Two columns per file:",
        "- **translit**: `saaras:v3` mode=translit — produces Hinglish Latin, lines up with the brief's format for easy visual comparison.",
        "- **saarika (Hindi)**: `saarika:v2.5` — the current bot default. Rendered in Devanagari.",
        "",
        "Each cell shows the extracted sentence containing the phrase keywords",
        "(expanded to the nearest sentence boundary). `—` = no matching span",
        "found, which means either the phrase wasn't spoken or the ASR output",
        "deviated too far from any of the keyword variants we tried. Cross-check",
        "against the full transcripts under `recordings/_variants/<variant>/` if",
        "any `—` looks suspicious.",
        "",
        "Phrase 20 (\"The driver ko call karo\") is excluded — transcribes",
        "identically to phrase 23 so it can't be distinguished.",
        "",
    ]

    for file_name, audio_stem in [("File 1 (12.08.32 PM)", AUDIO_FILE_1),
                                   ("File 2 (12.08.33 PM)", AUDIO_FILE_2)]:
        lines.append(f"## {file_name}")
        lines.append("")
        lines.append("| # | Expected (from brief) | saaras:v3 translit | saarika:v2.5 (Hindi) |")
        lines.append("|---|---|---|---|")

        for num, expected, kw_by_type in PHRASES:
            row_cells = []
            for variant_name, _ in DISPLAY_VARIANTS:
                is_latin = is_latin_variant(variant_name)
                kw_sets = kw_by_type["latin"] if is_latin else kw_by_type["devanagari"]
                out = extract(texts[(variant_name, audio_stem)], kw_sets)
                row_cells.append(out.replace("|", "\\|").replace("\n", " "))
            expected_cell = expected.replace("|", "\\|")
            lines.append(f"| {num} | {expected_cell} | {row_cells[0]} | {row_cells[1]} |")

        lines.append("")

    return "\n".join(lines)


def main() -> int:
    out_path = RECORDINGS_DIR / "expected_vs_actual.md"
    out_path.write_text(build(), encoding="utf-8")
    print(f"Wrote {out_path} ({out_path.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
