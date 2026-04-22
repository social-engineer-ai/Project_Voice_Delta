"""Biometric verification test with a proper long enrollment window.

Previous test used short (1-7s) WhatsApp clips to build the speaker
profile and failed to separate same from different. Resemblyzer's
guidance is ~30+ seconds of enrollment; this test uses 70+.

Protocol:
1. ENROLLMENT: take File 2's first 6 phrase chunks (~73 seconds of continuous
   speech from one speaker). Build the profile by averaging sub-window
   embeddings across those 73 seconds.
2. SAME-SPEAKER TEST (held-out, same session): File 2's last 4 phrase chunks.
3. SAME-SPEAKER TEST (cross-session): all 9 phrase chunks of File 1.
   (We're unsure whether Files 1 and 2 are the same speaker — if they are,
   this validates cross-session. If they aren't, scores will be low and
   that itself is a data point.)
4. DIFFERENT-SPEAKER TEST: Yogesh clips + GS-original clips (excluding the
   4 that are byte-copies of Yogesh).
5. Report scores against the three configured thresholds.

Audio decoding: bundled ffmpeg (via imageio_ffmpeg).
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path
from statistics import mean

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import imageio_ffmpeg
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
os.environ["PATH"] = str(Path(FFMPEG).parent) + os.pathsep + os.environ.get("PATH", "")

import numpy as np
from resemblyzer import VoiceEncoder, preprocess_wav

RECORDINGS = REPO_ROOT / "recordings"
FILE_1 = RECORDINGS / "WhatsApp Audio 2026-04-19 at 12.08.32 PM.mp4"
FILE_2 = RECORDINGS / "WhatsApp Audio 2026-04-19 at 12.08.33 PM.mp4"
YOGESH_DIR = RECORDINGS / "Yogesh"
GS_DIR = RECORDINGS / "GS"

# Phrase chunks from Sarvam timestamps (File 1 and File 2).
FILE_1_CHUNKS = [
    (1.51, 15.71), (15.71, 26.24), (26.24, 38.79), (38.79, 49.22),
    (49.22, 60.51), (60.51, 72.42), (72.42, 86.21), (86.21, 102.63),
    (102.63, 108.22),
]
FILE_2_CHUNKS = [
    (0.32, 10.66), (10.66, 24.23), (24.23, 39.30), (39.30, 50.63),
    (50.63, 62.47), (62.47, 73.63), (73.63, 85.15), (85.15, 97.25),
    (97.25, 113.79), (113.79, 127.90),
]

# First 6 chunks of File 2 = enrollment (~73 seconds of continuous speech).
# Remaining 4 chunks of File 2 = held-out same-speaker test.
FILE_2_ENROLL_CHUNKS = FILE_2_CHUNKS[:6]
FILE_2_TEST_CHUNKS   = FILE_2_CHUNKS[6:]

# GS clips that are byte-copies of Yogesh (exclude from "different speaker")
YOGESH_DUPLICATE_SIZES = {51953, 94272, 196222, 246248}

THRESHOLDS = {"strict": 0.75, "medium": 0.65, "loose": 0.55}


def ffmpeg_slice(src: Path, start: float, end: float) -> Path:
    """Extract [start, end) seconds of src as 16 kHz mono WAV."""
    wav = Path(tempfile.gettempdir()) / f"{src.stem}_{start:.2f}_{end:.2f}.wav"
    subprocess.run(
        [FFMPEG, "-y", "-ss", f"{start}", "-to", f"{end}",
         "-i", str(src), "-ar", "16000", "-ac", "1", str(wav)],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True,
    )
    return wav


def ffmpeg_full(src: Path) -> Path:
    wav = Path(tempfile.gettempdir()) / f"{src.stem}.full.wav"
    subprocess.run(
        [FFMPEG, "-y", "-i", str(src), "-ar", "16000", "-ac", "1", str(wav)],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True,
    )
    return wav


def embed_file(encoder: VoiceEncoder, wav_path: Path) -> np.ndarray:
    wav = preprocess_wav(wav_path)
    return encoder.embed_utterance(wav)


def cos(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def build_enrollment_profile(encoder: VoiceEncoder, src: Path,
                              chunks: list[tuple[float, float]]) -> np.ndarray:
    """Build a speaker profile by averaging per-chunk embeddings. More
    robust than embedding one long concatenated sample because each
    chunk's embedding is produced with its own normalization."""
    embs = []
    for start, end in chunks:
        wav_path = ffmpeg_slice(src, start, end)
        try:
            embs.append(embed_file(encoder, wav_path))
        except Exception as e:
            print(f"  enrollment chunk {start}-{end} failed: {e}")
    profile = np.mean(np.stack(embs), axis=0)
    return profile / np.linalg.norm(profile)


def list_gs_originals() -> list[Path]:
    return [p for p in sorted(GS_DIR.glob("*.mpeg"))
            if p.stat().st_size not in YOGESH_DUPLICATE_SIZES]


def main() -> int:
    print("Loading Resemblyzer encoder...")
    encoder = VoiceEncoder()

    print(f"\n=== ENROLLMENT ===")
    print(f"Source: {FILE_2.name}")
    print(f"Chunks: {len(FILE_2_ENROLL_CHUNKS)}")
    total_enroll_s = sum(e - s for s, e in FILE_2_ENROLL_CHUNKS)
    print(f"Total enrollment duration: {total_enroll_s:.1f}s")
    profile = build_enrollment_profile(encoder, FILE_2, FILE_2_ENROLL_CHUNKS)

    def score_chunks(label: str, src: Path, chunks: list[tuple[float, float]]) -> list[float]:
        print(f"\n--- {label} ({len(chunks)} chunks from {src.name}) ---")
        scores = []
        for s, e in chunks:
            wav = ffmpeg_slice(src, s, e)
            emb = embed_file(encoder, wav)
            sc = cos(emb, profile)
            scores.append(sc)
            print(f"  {sc:+.3f}  [{s:6.2f}-{e:6.2f}] ({e-s:4.1f}s)")
        return scores

    def score_files(label: str, paths: list[Path]) -> list[tuple[str, float]]:
        print(f"\n--- {label} ({len(paths)} files) ---")
        results = []
        for p in paths:
            wav = ffmpeg_full(p)
            emb = embed_file(encoder, wav)
            sc = cos(emb, profile)
            dur_s = subprocess.run(
                [FFMPEG, "-i", str(wav), "-hide_banner"],
                capture_output=True, text=True,
            ).stderr
            # Not parsing duration here; p.stat().st_size is enough signal
            results.append((p.name, sc))
            print(f"  {sc:+.3f}  {p.name}")
        return results

    same_file2  = score_chunks("SAME speaker, held-out File 2 chunks", FILE_2, FILE_2_TEST_CHUNKS)
    same_file1  = score_chunks("CROSS-session: File 1 chunks", FILE_1, FILE_1_CHUNKS)

    yogesh_clips = sorted(YOGESH_DIR.glob("*.mpeg"))
    gs_clips = list_gs_originals()
    diff_yogesh = score_files("DIFFERENT speaker: Yogesh clips", yogesh_clips)
    diff_gs     = score_files("DIFFERENT speaker: GS-original clips", gs_clips)

    # Summary
    print("\n" + "=" * 72)
    print("SUMMARY")
    print("=" * 72)

    def summarize(label: str, values: list[float], expect_high: bool):
        if not values:
            return
        print(f"\n  {label}:")
        print(f"    count={len(values)}  min={min(values):+.3f}  "
              f"mean={mean(values):+.3f}  max={max(values):+.3f}")
        for tname, tval in THRESHOLDS.items():
            accept = sum(1 for v in values if v >= tval)
            reject = len(values) - accept
            if expect_high:
                print(f"    th={tname}({tval}): accept={accept}/{len(values)} "
                      f"(false-reject={reject})")
            else:
                print(f"    th={tname}({tval}): accept={accept}/{len(values)} "
                      f"(false-accept={accept})")

    yogesh_vals = [s for _, s in diff_yogesh]
    gs_vals     = [s for _, s in diff_gs]

    summarize("SAME (File 2 held-out)",      same_file2,  expect_high=True)
    summarize("CROSS-session (File 1 all)",  same_file1,  expect_high=True)
    summarize("DIFFERENT (Yogesh)",           yogesh_vals, expect_high=False)
    summarize("DIFFERENT (GS-original)",      gs_vals,     expect_high=False)

    # Separation — assumes File 1 is the same speaker as File 2; if it
    # isn't, both File 1 chunks and Yogesh/GS would be "different".
    same_all = same_file2 + same_file1
    diff_all = yogesh_vals + gs_vals
    if same_all and diff_all:
        print(f"\n  If File 1 and File 2 are the SAME speaker:")
        print(f"    min(same)={min(same_all):+.3f}  max(diff)={max(diff_all):+.3f}  "
              f"margin={min(same_all) - max(diff_all):+.3f}")
    if same_file2 and (same_file1 + diff_all):
        print(f"\n  If File 1 is a DIFFERENT speaker from File 2:")
        print(f"    min(same)={min(same_file2):+.3f}  "
              f"max(diff)={max(same_file1 + diff_all):+.3f}  "
              f"margin={min(same_file2) - max(same_file1 + diff_all):+.3f}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
