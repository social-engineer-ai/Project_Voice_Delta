"""Same biometric protocol as test_biometric_long_enroll.py, but with
SpeechBrain's ECAPA-TDNN instead of Resemblyzer.

ECAPA-TDNN (spkrec-ecapa-voxceleb) reports ~0.8% EER on VoxCeleb — a
significant upgrade over Resemblyzer's older architecture, particularly
on short or noisy utterances. This script runs the identical enrollment
and test protocol so scores can be compared directly.
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
import soundfile as sf
import torch
from speechbrain.inference.speaker import EncoderClassifier

RECORDINGS = REPO_ROOT / "recordings"
FILE_1 = RECORDINGS / "WhatsApp Audio 2026-04-19 at 12.08.32 PM.mp4"
FILE_2 = RECORDINGS / "WhatsApp Audio 2026-04-19 at 12.08.33 PM.mp4"
YOGESH_DIR = RECORDINGS / "Yogesh"
GS_DIR = RECORDINGS / "GS"

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
FILE_2_ENROLL_CHUNKS = FILE_2_CHUNKS[:6]
FILE_2_TEST_CHUNKS   = FILE_2_CHUNKS[6:]

YOGESH_DUPLICATE_SIZES = {51953, 94272, 196222, 246248}

# ECAPA-TDNN cosine scores run higher than Resemblyzer's in general, but
# thresholds need to be recalibrated. VoxCeleb EER is usually around 0.25
# for this model; we'll start with the old bands and re-evaluate from data.
THRESHOLDS = {"strict": 0.70, "medium": 0.55, "loose": 0.40}


def ffmpeg_slice(src: Path, start: float, end: float) -> Path:
    wav = Path(tempfile.gettempdir()) / f"{src.stem}_{start:.2f}_{end:.2f}.16k.wav"
    subprocess.run(
        [FFMPEG, "-y", "-ss", f"{start}", "-to", f"{end}",
         "-i", str(src), "-ar", "16000", "-ac", "1", str(wav)],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True,
    )
    return wav


def ffmpeg_full(src: Path) -> Path:
    wav = Path(tempfile.gettempdir()) / f"{src.stem}.full.16k.wav"
    subprocess.run(
        [FFMPEG, "-y", "-i", str(src), "-ar", "16000", "-ac", "1", str(wav)],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True,
    )
    return wav


def embed(model: EncoderClassifier, wav_path: Path) -> np.ndarray:
    # ffmpeg already produced 16 kHz mono WAV, so soundfile is enough and
    # avoids torchaudio's new torchcodec dependency.
    signal, sr = sf.read(str(wav_path), dtype="float32")
    assert sr == 16000, f"expected 16 kHz, got {sr}"
    if signal.ndim > 1:
        signal = signal.mean(axis=1)
    tensor = torch.from_numpy(signal).unsqueeze(0)  # [1, T]
    with torch.no_grad():
        emb = model.encode_batch(tensor)
    emb = emb.squeeze().cpu().numpy()
    return emb / (np.linalg.norm(emb) + 1e-12)


def cos(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-12))


def build_profile(model: EncoderClassifier, src: Path,
                  chunks: list[tuple[float, float]]) -> np.ndarray:
    embs = []
    for s, e in chunks:
        wav = ffmpeg_slice(src, s, e)
        embs.append(embed(model, wav))
    profile = np.mean(np.stack(embs), axis=0)
    return profile / (np.linalg.norm(profile) + 1e-12)


def list_gs_originals() -> list[Path]:
    return [p for p in sorted(GS_DIR.glob("*.mpeg"))
            if p.stat().st_size not in YOGESH_DUPLICATE_SIZES]


def main() -> int:
    print("Loading ECAPA-TDNN (first run downloads ~80 MB of weights)...")
    model = EncoderClassifier.from_hparams(
        source="speechbrain/spkrec-ecapa-voxceleb",
        savedir=str(REPO_ROOT / ".cache" / "spkrec-ecapa"),
        run_opts={"device": "cpu"},
    )
    print("ECAPA-TDNN loaded")

    total_enroll = sum(e - s for s, e in FILE_2_ENROLL_CHUNKS)
    print(f"\nENROLLMENT: File 2 first {len(FILE_2_ENROLL_CHUNKS)} chunks, {total_enroll:.1f}s total")
    profile = build_profile(model, FILE_2, FILE_2_ENROLL_CHUNKS)

    def score_chunks(label: str, src: Path, chunks: list[tuple[float, float]]) -> list[float]:
        print(f"\n--- {label} ({len(chunks)} chunks from {src.name}) ---")
        out = []
        for s, e in chunks:
            wav = ffmpeg_slice(src, s, e)
            sc = cos(embed(model, wav), profile)
            out.append(sc)
            print(f"  {sc:+.3f}  [{s:6.2f}-{e:6.2f}] ({e-s:4.1f}s)")
        return out

    def score_files(label: str, paths: list[Path]) -> list[tuple[str, float]]:
        print(f"\n--- {label} ({len(paths)} files) ---")
        out = []
        for p in paths:
            wav = ffmpeg_full(p)
            sc = cos(embed(model, wav), profile)
            out.append((p.name, sc))
            print(f"  {sc:+.3f}  {p.name}")
        return out

    same_file2 = score_chunks("SAME speaker — File 2 held-out", FILE_2, FILE_2_TEST_CHUNKS)
    diff_file1 = score_chunks("DIFFERENT speaker (confirmed) — File 1", FILE_1, FILE_1_CHUNKS)

    yogesh = sorted(YOGESH_DIR.glob("*.mpeg"))
    gs     = list_gs_originals()
    diff_yogesh = score_files("DIFFERENT speaker — Yogesh", yogesh)
    diff_gs     = score_files("DIFFERENT speaker — GS-original", gs)

    print("\n" + "=" * 72)
    print("SUMMARY — ECAPA-TDNN")
    print("=" * 72)

    def summarize(label: str, values: list[float], expect_high: bool):
        if not values:
            return
        print(f"\n  {label}:  count={len(values)}  "
              f"min={min(values):+.3f}  mean={mean(values):+.3f}  max={max(values):+.3f}")
        for tname, tval in THRESHOLDS.items():
            accept = sum(1 for v in values if v >= tval)
            reject = len(values) - accept
            side = "false-reject" if expect_high else "false-accept"
            count = reject if expect_high else accept
            print(f"    th={tname}({tval}): accept={accept}/{len(values)}  {side}={count}")

    yogesh_vals = [s for _, s in diff_yogesh]
    gs_vals     = [s for _, s in diff_gs]

    summarize("SAME (File 2 held-out)",         same_file2,   expect_high=True)
    summarize("DIFFERENT (File 1, confirmed)",  diff_file1,   expect_high=False)
    summarize("DIFFERENT (Yogesh)",              yogesh_vals,  expect_high=False)
    summarize("DIFFERENT (GS-original)",         gs_vals,      expect_high=False)

    diff_all = diff_file1 + yogesh_vals + gs_vals
    if same_file2 and diff_all:
        margin = min(same_file2) - max(diff_all)
        print(f"\n  Separation:")
        print(f"    min(same) = {min(same_file2):+.3f}")
        print(f"    max(diff) = {max(diff_all):+.3f}")
        print(f"    margin    = {margin:+.3f}")
        if margin > 0:
            print(f"  -> A clean threshold exists between {max(diff_all):+.3f} and {min(same_file2):+.3f}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
