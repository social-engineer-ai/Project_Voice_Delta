"""End-to-end sanity check of the Resemblyzer-based speaker verification.

Protocol:
1. Identify the 10 GS-original clips (some GS files are byte-copies of
   Yogesh clips — those would contaminate training).
2. Split GS-original into enrollment (N=5) and held-out same-speaker test.
3. Build a speaker profile from the enrollment clips (mean embedding).
4. Score every clip against the profile:
   - held-out GS-original        → expect HIGH similarity (same speaker)
   - Yogesh clips                → expect LOW (different speaker)
   - Long File 1 and File 2      → expect LOW (different speaker — Garv)
5. Report scores vs the three configured thresholds (0.55 / 0.65 / 0.75)
   and show false-accept / false-reject counts at each threshold.

mp3/mp4 decoding goes through librosa → audioread → the bundled ffmpeg
binary. We point subprocess callers at imageio_ffmpeg's executable via
the PATH for this process.
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

# Make the bundled ffmpeg findable by anything that calls `ffmpeg` directly.
import imageio_ffmpeg
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
os.environ["PATH"] = str(Path(FFMPEG).parent) + os.pathsep + os.environ.get("PATH", "")

import numpy as np
import soundfile as sf
from resemblyzer import VoiceEncoder, preprocess_wav


RECORDINGS = REPO_ROOT / "recordings"
YOGESH_DIR = RECORDINGS / "Yogesh"
GS_DIR = RECORDINGS / "GS"
LONG_FILES = [
    RECORDINGS / "WhatsApp Audio 2026-04-19 at 12.08.32 PM.mp4",
    RECORDINGS / "WhatsApp Audio 2026-04-19 at 12.08.33 PM.mp4",
]

# File sizes of GS clips that are byte-copies of Yogesh clips (identified
# from ls -la earlier: 50.7 KB, 92.1 KB, 191.6 KB, 240.5 KB).
# We exclude these from the GS enrollment / same-speaker set.
YOGESH_DUPLICATE_SIZES = {51953, 94272, 196222, 246248}

THRESHOLDS = {"strict": 0.75, "medium": 0.65, "loose": 0.55}


def decode_to_wav(src: Path, cache: dict[Path, Path]) -> Path:
    """Decode any audio format to 16 kHz mono WAV via bundled ffmpeg."""
    if src in cache:
        return cache[src]
    wav = Path(tempfile.gettempdir()) / (src.stem + ".biometric.wav")
    subprocess.run(
        [FFMPEG, "-y", "-i", str(src), "-ar", "16000", "-ac", "1", str(wav)],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True,
    )
    cache[src] = wav
    return wav


def embed(encoder: VoiceEncoder, src: Path, cache: dict[Path, Path]) -> np.ndarray:
    wav_path = decode_to_wav(src, cache)
    wav = preprocess_wav(wav_path)
    return encoder.embed_utterance(wav)


def cos(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def list_gs_originals_and_copies() -> tuple[list[Path], list[Path]]:
    originals, copies = [], []
    for p in sorted(GS_DIR.glob("*.mpeg")):
        if p.stat().st_size in YOGESH_DUPLICATE_SIZES:
            copies.append(p)
        else:
            originals.append(p)
    return originals, copies


def main() -> int:
    print("Loading Resemblyzer encoder...")
    encoder = VoiceEncoder()
    decode_cache: dict[Path, Path] = {}

    gs_originals, gs_copies = list_gs_originals_and_copies()
    yogesh = sorted(YOGESH_DIR.glob("*.mpeg"))

    print(f"\nDataset:")
    print(f"  GS originals (speaker=GS):           {len(gs_originals)} clips")
    print(f"  GS copies-of-Yogesh (actually=Yog):  {len(gs_copies)} clips")
    print(f"  Yogesh (speaker=Yogesh):             {len(yogesh)} clips")
    print(f"  Long files (speaker=other):          {len(LONG_FILES)} files")

    # Split GS-originals: first 5 for enrollment, rest for held-out same-speaker test.
    if len(gs_originals) < 7:
        print(f"! need at least 7 GS-original clips for a meaningful split")
        return 2
    enroll = gs_originals[:5]
    heldout_same = gs_originals[5:]

    print(f"\nEnrollment clips (building GS profile from {len(enroll)}):")
    for p in enroll:
        print(f"  {p.name}")

    # Build GS profile = mean of enrollment embeddings (L2-normalized)
    enroll_embs = []
    for p in enroll:
        try:
            enroll_embs.append(embed(encoder, p, decode_cache))
        except Exception as e:
            print(f"  ! failed {p.name}: {e}")
    if not enroll_embs:
        print("No enrollment embeddings produced; aborting.")
        return 3
    profile = np.mean(np.stack(enroll_embs), axis=0)
    profile = profile / np.linalg.norm(profile)

    def score_set(label: str, paths: list[Path]) -> list[tuple[str, float]]:
        print(f"\n--- {label} ({len(paths)} clips) ---")
        results = []
        for p in paths:
            try:
                emb = embed(encoder, p, decode_cache)
                s = cos(emb, profile)
                results.append((p.name, s))
                print(f"  {s:+.3f}  {p.name}")
            except Exception as e:
                print(f"  !!     {p.name}: {e}")
        return results

    heldout_scores = score_set("Held-out same-speaker (GS originals not used in enrollment)", heldout_same)
    yogesh_scores  = score_set("Different speaker (Yogesh clips)", yogesh)
    copies_scores  = score_set("GS files that are byte-copies of Yogesh (should score like Yogesh)", gs_copies)
    long_scores    = score_set("Different speaker (long files, Garv's recordings)", LONG_FILES)

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    def summarize(label: str, scores: list[tuple[str, float]], expect_high: bool):
        if not scores:
            print(f"  {label}: (no scores)"); return
        values = [s for _, s in scores]
        print(f"\n  {label}:")
        print(f"    min={min(values):+.3f}  mean={mean(values):+.3f}  max={max(values):+.3f}")
        for tname, tval in THRESHOLDS.items():
            accept = sum(1 for v in values if v >= tval)
            reject = len(values) - accept
            if expect_high:
                print(f"    threshold={tname}({tval}):  accept={accept}/{len(values)}  (false-reject={reject})")
            else:
                print(f"    threshold={tname}({tval}):  accept={accept}/{len(values)}  (false-accept={accept})")

    summarize("Same-speaker (held-out GS)",     heldout_scores, expect_high=True)
    summarize("Different (Yogesh clips)",        yogesh_scores,  expect_high=False)
    summarize("GS byte-copies of Yogesh",        copies_scores,  expect_high=False)
    summarize("Different (long files)",          long_scores,    expect_high=False)

    # Quick separation check
    if heldout_scores and yogesh_scores:
        min_same = min(s for _, s in heldout_scores)
        max_diff = max(s for _, s in yogesh_scores + copies_scores + long_scores)
        margin = min_same - max_diff
        print(f"\n  Separation: min(same)={min_same:+.3f}  max(diff)={max_diff:+.3f}  margin={margin:+.3f}")
        print("  -> A positive margin means same and different are cleanly separated.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
