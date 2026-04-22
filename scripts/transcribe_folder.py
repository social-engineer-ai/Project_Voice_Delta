"""Transcribe every audio file in a given folder with Sarvam batch API.

Usage:
    python scripts/transcribe_folder.py <folder>

Runs two variants on all audio files:
    - saaras:v3 mode=translit (Hinglish Latin)
    - saaras:v3 mode=transcribe (Devanagari)

Outputs:
    <folder>/_sarvam_out/translit/<audio>.mp4.json + <audio>.txt
    <folder>/_sarvam_out/devanagari/<audio>.mp4.json + <audio>.txt
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sarvamai import SarvamAI

from app.config import settings

AUDIO_EXTS = {".mp4", ".m4a", ".mp3", ".wav", ".ogg", ".opus", ".mpeg", ".mpg", ".aac"}

VARIANTS = [
    {"name": "translit",   "mode": "translit"},
    {"name": "devanagari", "mode": "transcribe"},
]


def find_audio_files(folder: Path) -> list[Path]:
    return sorted(
        p for p in folder.iterdir()
        if p.is_file() and p.suffix.lower() in AUDIO_EXTS
    )


def run(folder: Path, audio_files: list[Path]) -> int:
    client = SarvamAI(api_subscription_key=settings.sarvam_api_key)

    for variant in VARIANTS:
        print(f"\n=== {variant['name']} (saaras:v3, mode={variant['mode']}) ===")
        out_dir = folder / "_sarvam_out" / variant["name"]
        out_dir.mkdir(parents=True, exist_ok=True)

        t0 = time.time()
        job = client.speech_to_text_job.create_job(
            model="saaras:v3",
            mode=variant["mode"],
            language_code="hi-IN",
            with_timestamps=True,
        )
        job.upload_files(file_paths=[str(p) for p in audio_files], timeout=300.0)
        job.start()
        job.wait_until_complete(poll_interval=5, timeout=1800)

        if not job.is_successful():
            print(f"  Job failed")
            continue

        job.download_outputs(output_dir=str(out_dir))
        elapsed = time.time() - t0
        print(f"  Completed in {elapsed:.1f}s")

        for audio in audio_files:
            raw = out_dir / f"{audio.name}.json"
            if not raw.exists():
                print(f"  ! {audio.name}: no raw output")
                continue
            data = json.loads(raw.read_text(encoding="utf-8"))
            transcript = (data.get("transcript") or "").strip()
            lang = data.get("language_code")
            txt = out_dir / (audio.stem + ".txt")
            txt.write_text(transcript, encoding="utf-8")
            print(f"  {audio.name}: {len(transcript)} chars  lang={lang}")

    return 0


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: python scripts/transcribe_folder.py <folder>")
        return 2
    folder = Path(sys.argv[1]).resolve()
    if not folder.is_dir():
        print(f"Not a directory: {folder}")
        return 2
    audio_files = find_audio_files(folder)
    if not audio_files:
        print(f"No audio files in {folder}")
        return 1
    print(f"Found {len(audio_files)} file(s) in {folder.name}:")
    for p in audio_files:
        print(f"  - {p.name}  ({p.stat().st_size / 1024:.1f} KB)")
    return run(folder, audio_files)


if __name__ == "__main__":
    sys.exit(main())
