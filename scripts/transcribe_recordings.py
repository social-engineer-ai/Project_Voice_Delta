"""One-off script to transcribe files in recordings/ using Sarvam batch STT.

Uses Sarvam's batch job API because the sync /speech-to-text endpoint is
capped at ~30s of audio and these files are several minutes long. The batch
API handles up to one hour per file.

Usage: python scripts/transcribe_recordings.py

Reads SARVAM_API_KEY from .env. Writes each transcript as a .txt file next
to the source audio, and the raw Sarvam JSON output under
recordings/_sarvam_out/ for later inspection.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sarvamai import SarvamAI

from app.config import settings

AUDIO_EXTS = {".mp4", ".m4a", ".mp3", ".wav", ".ogg", ".opus", ".aac", ".flac", ".webm"}

RECORDINGS_DIR = REPO_ROOT / "recordings"
RAW_OUTPUT_DIR = RECORDINGS_DIR / "_sarvam_out"


def find_audio_files() -> list[Path]:
    return sorted(
        p for p in RECORDINGS_DIR.iterdir()
        if p.is_file() and p.suffix.lower() in AUDIO_EXTS
    )


def read_transcript_from_raw(audio_path: Path) -> str | None:
    """Sarvam's batch SDK downloads each file's result as `<audio_name>.json`
    inside the output dir. Read the transcript directly from there — more
    reliable than get_file_results() whose dict keying has varied across
    SDK versions.
    """
    raw_json = RAW_OUTPUT_DIR / f"{audio_path.name}.json"
    if not raw_json.exists():
        return None
    data = json.loads(raw_json.read_text(encoding="utf-8"))
    transcript = data.get("transcript")
    if isinstance(transcript, str) and transcript.strip():
        return transcript.strip()
    return None


def main() -> int:
    audio_files = find_audio_files()
    if not audio_files:
        print(f"No audio files found under {RECORDINGS_DIR}")
        return 1

    print(f"Found {len(audio_files)} file(s):")
    for p in audio_files:
        print(f"  - {p.name}  ({p.stat().st_size / 1_048_576:.2f} MB)")

    client = SarvamAI(api_subscription_key=settings.sarvam_api_key)

    print("\nCreating batch job (saarika:v2.5, hi-IN, with timestamps)...")
    job = client.speech_to_text_job.create_job(
        model="saarika:v2.5",
        language_code="hi-IN",
        with_timestamps=True,
    )

    print(f"Uploading {len(audio_files)} file(s)...")
    job.upload_files(file_paths=[str(p) for p in audio_files], timeout=300.0)

    print("Starting job...")
    job.start()

    print("Waiting for completion (timeout 30 min, polling every 10s)...")
    status = job.wait_until_complete(poll_interval=10, timeout=1800)
    print(f"Job status: {status}")

    if not job.is_successful():
        print("Job did not succeed. See status above.")
        return 2

    RAW_OUTPUT_DIR.mkdir(exist_ok=True)
    print(f"Downloading raw outputs to {RAW_OUTPUT_DIR}...")
    job.download_outputs(output_dir=str(RAW_OUTPUT_DIR))

    print("Writing transcripts...")
    for audio_path in audio_files:
        transcript = read_transcript_from_raw(audio_path)
        out_path = audio_path.with_suffix(".txt")
        if transcript:
            out_path.write_text(transcript, encoding="utf-8")
            print(f"  -> {out_path.name}  ({len(transcript)} chars)")
        else:
            print(f"  ! No transcript found for {audio_path.name}. Check {RAW_OUTPUT_DIR}.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
