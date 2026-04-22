"""Run the intent classifier against our short-clip transcripts so we can
see, end-to-end, how well ASR + classify.py performs on real utterances.

Inputs: translit and Devanagari transcripts under
    recordings/Yogesh/_sarvam_out/{translit,devanagari}/*.txt
    recordings/GS/_sarvam_out/{translit,devanagari}/*.txt

Output: recordings/intent_classification.md
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.services.classify import classify_intent  # noqa: E402

RECORDINGS = REPO_ROOT / "recordings"

# (folder, clip_suffix, expected_intent, notes)
# Expected intent assigned by looking at the transcripts and the brief's
# intent groupings. "ambiguous" marks phrases the brief itself called ambiguous.
CLIPS: list[dict] = [
    # Yogesh folder
    {"folder": "Yogesh", "suffix": "PM1",  "expected": "unknown",  "brief": "~31 (off-topic 'haan theek hai' variant)"},
    {"folder": "Yogesh", "suffix": "PM2",  "expected": "delegate", "brief": "~19 (Driver ko bolo site pahunche) — prefix dropped"},
    {"folder": "Yogesh", "suffix": "PM3",  "expected": "reminder", "brief": "~9 variant (8 baje yaad dilana)"},
    {"folder": "Yogesh", "suffix": "PM4",  "expected": "ambiguous","brief": "fragment 'baje bolo'"},
    {"folder": "Yogesh", "suffix": "PM5",  "expected": "call",     "brief": "26 (Accountant ji ko call karo abhi) — 'Mountain G' error"},
    {"folder": "Yogesh", "suffix": "PM6",  "expected": "message",  "brief": "4 (Ramu bhaiya ko bolo yaad rakhe...)"},
    # GS folder
    {"folder": "GS", "suffix": "PM11",       "expected": "message",  "brief": "2 (Supplier ko SMS bhejo, cement rate)"},
    {"folder": "GS", "suffix": "PM13",       "expected": "message",  "brief": "1 (Rajesh ko WhatsApp karo)"},
    {"folder": "GS", "suffix": "PM10",       "expected": "reminder", "brief": "10 (Thodi der mein yaad dilana)"},
    {"folder": "GS", "suffix": "PM7",        "expected": "reminder", "brief": "6 (3 baje yaad dilana Rajesh ko call) — '3' dropped"},
    {"folder": "GS", "suffix": "PM8",        "expected": "message",  "brief": "5 (English: payment next week)"},
    {"folder": "GS", "suffix": "PM9",        "expected": "delegate", "brief": "18 (Ramu → Praveen ko call & delivery confirm) — 'Ramu→Aamu'"},
    {"folder": "GS", "suffix": "PM5",        "expected": "delegate", "brief": "22 fragment (Chhotu ko bolo ghar jaake khana)"},
    {"folder": "GS", "suffix": "PM6",        "expected": "message",  "brief": "3 (Sharma sahab ko WhatsApp) — 'shop par→subah sahab par' error"},
    {"folder": "GS", "suffix": "PM",         "expected": "message",  "brief": "17 compound (Rajesh ko message + 5 baje yaad) — Rajesh dropped"},
    {"folder": "GS", "suffix": "PM2-first",  "expected": "reminder", "brief": "13 (2 hours remind me to call supplier)"},
    {"folder": "GS", "suffix": "PM2-second", "expected": "call",     "brief": "26 (same as Yogesh PM5)"},
    {"folder": "GS", "suffix": "PM3",        "expected": "ambiguous","brief": "fragment 'baje bolo' (same as Yogesh PM4)"},
    {"folder": "GS", "suffix": "PM4",        "expected": "reminder", "brief": "9 variant (same as Yogesh PM3)"},
    {"folder": "GS", "suffix": "PM1",        "expected": "message",  "brief": "4 (same as Yogesh PM6)"},
]


def load_transcripts(folder: str) -> list[tuple[str, str, str]]:
    """Return [(stem, translit_text, devanagari_text), ...] sorted by stem."""
    tr_dir = RECORDINGS / folder / "_sarvam_out" / "translit"
    de_dir = RECORDINGS / folder / "_sarvam_out" / "devanagari"
    results = []
    for t in sorted(tr_dir.glob("*.txt")):
        stem = t.stem
        d = de_dir / t.name
        results.append((
            stem,
            t.read_text(encoding="utf-8").strip(),
            d.read_text(encoding="utf-8").strip() if d.exists() else "",
        ))
    return results


def suffix_from_stem(stem: str) -> str:
    """e.g. 'WhatsApp Audio 2026-04-21 at 9.53.07 PM1' -> 'PM1'; empty after PM -> 'PM'."""
    if "PM" not in stem:
        return stem
    after = stem.rsplit("PM", 1)[1]
    return f"PM{after}" if after else "PM"


def pick_transcript(folder: str, suffix: str) -> tuple[str, str, str] | None:
    """Resolve a clip reference like 'PM2-first' to (stem, translit, dev)."""
    all_t = load_transcripts(folder)
    # Normalize: two GS clips share the 'PM2' suffix (one at 9.56.39, one at 9.56.41).
    # Distinguish via -first / -second ordering.
    matches = [(s, t, d) for s, t, d in all_t if suffix_from_stem(s) == suffix]
    if matches:
        return matches[0]
    if suffix.endswith("-first") or suffix.endswith("-second"):
        base = suffix.rsplit("-", 1)[0]
        ordinal = suffix.rsplit("-", 1)[1]
        cand = [(s, t, d) for s, t, d in all_t if suffix_from_stem(s) == base]
        if len(cand) >= 2:
            return cand[0] if ordinal == "first" else cand[1]
    return None


def classify_with_retries(text: str, attempts: int = 3) -> dict:
    """Call classify_intent and normalize to a dict. Retry on transient errors."""
    last_err = None
    for _ in range(attempts):
        try:
            result = classify_intent(text)
            return result.model_dump()
        except Exception as e:
            last_err = e
            time.sleep(1.0)
    return {"intent": "error", "confidence": 0.0, "clarification_needed": str(last_err)}


def format_slots(d: dict) -> str:
    bits = []
    for key in ("recipient_name", "channel", "message_body", "reminder_text",
                "task_description", "scheduled_time", "followup_check"):
        v = d.get(key)
        if v:
            bits.append(f"{key}={v}")
    return "<br>".join(bits) if bits else "(none)"


def main() -> int:
    rows: list[dict] = []
    for clip in CLIPS:
        picked = pick_transcript(clip["folder"], clip["suffix"])
        if picked is None:
            print(f"! no transcript for {clip['folder']}/{clip['suffix']}")
            continue
        stem, translit, devanagari = picked
        print(f"[{clip['folder']}/{clip['suffix']}] translit={translit!r}")

        translit_result  = classify_with_retries(translit)  if translit  else {}
        devanagari_result = classify_with_retries(devanagari) if devanagari else {}
        time.sleep(0.3)  # gentle pacing to avoid rate limits

        rows.append({
            "clip": f"{clip['folder']}/{clip['suffix']}",
            "brief": clip["brief"],
            "expected": clip["expected"],
            "translit_text": translit,
            "devanagari_text": devanagari,
            "translit_result": translit_result,
            "devanagari_result": devanagari_result,
        })
        print(f"  translit → intent={translit_result.get('intent')} conf={translit_result.get('confidence')}")
        print(f"  dev      → intent={devanagari_result.get('intent')} conf={devanagari_result.get('confidence')}")

    # Render markdown
    lines: list[str] = [
        "# Intent classification results — short clips",
        "",
        "We ran each clip's transcript through `app.services.classify.classify_intent`",
        "(Gemini 2.5 Flash-Lite, `classify.py` SYSTEM_PROMPT). Two inputs per clip:",
        "the Hinglish translit output and the Devanagari output. If the classifier",
        "is robust to script, both should produce the same intent.",
        "",
        "`expected` is what a human would reasonably label the utterance — based on",
        "the brief's phrase groupings. 'ambiguous' and 'unknown' are legitimate",
        "outcomes for fragments and off-topic phrases.",
        "",
    ]

    # Summary counts
    intent_match = {"translit": 0, "devanagari": 0}
    total = 0
    for r in rows:
        expected = r["expected"]
        if expected == "ambiguous":
            continue  # don't count ambiguous against the classifier
        total += 1
        for script in ("translit", "devanagari"):
            key = f"{script}_result"
            if r[key].get("intent") == expected:
                intent_match[script] += 1

    lines.append("## Intent accuracy (excluding clips the brief itself labels ambiguous)")
    lines.append("")
    lines.append(f"- Translit input: **{intent_match['translit']}/{total}** intent matches")
    lines.append(f"- Devanagari input: **{intent_match['devanagari']}/{total}** intent matches")
    lines.append("")

    lines.append("## Per-clip detail")
    lines.append("")
    lines.append("| Clip | Expected | ASR translit → intent | conf | ASR dev → intent | conf | Slots (translit) |")
    lines.append("|---|---|---|---|---|---|---|")
    for r in rows:
        t = r["translit_result"]
        d = r["devanagari_result"]
        t_intent = t.get("intent", "?")
        d_intent = d.get("intent", "?")
        t_conf = t.get("confidence", "?")
        d_conf = d.get("confidence", "?")
        # mark mismatch
        expected = r["expected"]
        if expected != "ambiguous":
            t_mark = "✓" if t_intent == expected else "✗"
            d_mark = "✓" if d_intent == expected else "✗"
            t_cell = f"{t_mark} {t_intent}"
            d_cell = f"{d_mark} {d_intent}"
        else:
            t_cell = t_intent
            d_cell = d_intent
        slots = format_slots(t).replace("|", "\\|")
        translit_text_cell = r['translit_text'].replace("|", "\\|")
        lines.append(f"| `{r['clip']}`<br>_{translit_text_cell}_ | **{expected}**<br>{r['brief']} | {t_cell} | {t_conf} | {d_cell} | {d_conf} | {slots} |")

    out_path = RECORDINGS / "intent_classification.md"
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nWrote {out_path}")

    # Also print a concise summary to console
    print(f"\nIntent accuracy (translit): {intent_match['translit']}/{total}")
    print(f"Intent accuracy (Devanagari): {intent_match['devanagari']}/{total}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
