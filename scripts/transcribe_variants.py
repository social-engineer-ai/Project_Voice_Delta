"""Run Sarvam STT on recordings/*.mp4 across every available model+mode
variant, saving raw outputs and a clean transcript per variant.

Goal: find out whether any non-default configuration (saaras:v3 modes —
translit for Hinglish, codemix for code-mixed speech, verbatim, translate)
produces a cleaner or more useful transcript for ShopSaarthi's evaluation.

Outputs:
- recordings/_variants/<variant>/<audio_name>.mp4.json  (raw Sarvam output)
- recordings/_variants/<variant>/<audio_name>.txt       (extracted transcript)
"""
from __future__ import annotations

import json
import sys
import time
import traceback
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sarvamai import SarvamAI

from app.config import settings

RECORDINGS_DIR = REPO_ROOT / "recordings"
VARIANTS_DIR = RECORDINGS_DIR / "_variants"
AUDIO_EXTS = {".mp4", ".m4a", ".mp3", ".wav", ".ogg", ".opus"}

VARIANTS: list[dict] = [
    {"name": "saarika_v2.5_hi",       "model": "saarika:v2.5", "mode": None,         "lang": "hi-IN"},
    {"name": "saarika_v2.5_unknown",  "model": "saarika:v2.5", "mode": None,         "lang": "unknown"},
    {"name": "saaras_v3_transcribe",  "model": "saaras:v3",    "mode": "transcribe", "lang": "hi-IN"},
    {"name": "saaras_v3_verbatim",    "model": "saaras:v3",    "mode": "verbatim",   "lang": "hi-IN"},
    {"name": "saaras_v3_translit",    "model": "saaras:v3",    "mode": "translit",   "lang": "hi-IN"},
    {"name": "saaras_v3_codemix",     "model": "saaras:v3",    "mode": "codemix",    "lang": "hi-IN"},
    {"name": "saaras_v3_translate",   "model": "saaras:v3",    "mode": "translate",  "lang": "hi-IN"},
]


def find_audio_files() -> list[Path]:
    return sorted(
        p for p in RECORDINGS_DIR.iterdir()
        if p.is_file() and p.suffix.lower() in AUDIO_EXTS
    )


def run_variant(client: SarvamAI, variant: dict, audio_files: list[Path]) -> dict:
    out_dir = VARIANTS_DIR / variant["name"]
    out_dir.mkdir(parents=True, exist_ok=True)

    kwargs = {
        "model": variant["model"],
        "language_code": variant["lang"],
        "with_timestamps": True,
    }
    if variant["mode"]:
        kwargs["mode"] = variant["mode"]

    t0 = time.time()
    job = client.speech_to_text_job.create_job(**kwargs)
    job.upload_files(file_paths=[str(p) for p in audio_files], timeout=300.0)
    job.start()
    status = job.wait_until_complete(poll_interval=5, timeout=1800)
    elapsed = time.time() - t0

    result = {
        "variant": variant["name"],
        "elapsed_s": round(elapsed, 1),
        "successful": job.is_successful(),
        "job_id": getattr(status, "job_id", None),
        "files": {},
    }

    if not job.is_successful():
        result["error"] = f"status={status}"
        return result

    job.download_outputs(output_dir=str(out_dir))

    for audio in audio_files:
        raw_json_path = out_dir / f"{audio.name}.json"
        transcript = ""
        detected_lang = None
        if raw_json_path.exists():
            try:
                data = json.loads(raw_json_path.read_text(encoding="utf-8"))
                transcript = (data.get("transcript") or "").strip()
                detected_lang = data.get("language_code")
            except Exception as e:
                result["files"][audio.name] = {"error": f"parse fail: {e}"}
                continue
            txt_path = out_dir / (audio.stem + ".txt")
            txt_path.write_text(transcript, encoding="utf-8")
        result["files"][audio.name] = {
            "chars": len(transcript),
            "detected_language": detected_lang,
        }

    return result


def main() -> int:
    audio_files = find_audio_files()
    if not audio_files:
        print(f"No audio files under {RECORDINGS_DIR}")
        return 1
    print(f"Audio files: {[p.name for p in audio_files]}")
    print(f"Variants to run: {len(VARIANTS)}\n")

    client = SarvamAI(api_subscription_key=settings.sarvam_api_key)
    VARIANTS_DIR.mkdir(exist_ok=True)

    all_results = []
    for variant in VARIANTS:
        print(f"=== {variant['name']} (model={variant['model']} mode={variant['mode']} lang={variant['lang']}) ===")
        try:
            r = run_variant(client, variant, audio_files)
            all_results.append(r)
            if r["successful"]:
                print(f"  OK in {r['elapsed_s']}s")
                for fname, info in r["files"].items():
                    print(f"    {fname}: {info}")
            else:
                print(f"  FAILED: {r.get('error')}")
        except Exception as e:
            print(f"  EXCEPTION: {e}")
            traceback.print_exc()
            all_results.append({"variant": variant["name"], "error": str(e)})
        print()

    summary_path = VARIANTS_DIR / "_run_summary.json"
    summary_path.write_text(json.dumps(all_results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Summary written to {summary_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
