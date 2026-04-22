"""Speaker verification service using SpeechBrain ECAPA-TDNN.

Builds and compares voice embeddings for the trust layer. Each user enrolls
their voice by recording a few phrases. Each subsequent voice command is
checked against the enrolled embeddings before being processed.

This is a trust feature, not a security feature: the goal is to visibly
demonstrate to customers that the bot responds only to the shopkeeper.
False acceptance/rejection tradeoff is configurable per shop via
User.security_threshold.

Background — why ECAPA-TDNN:
2026-04-22 benchmarking found Resemblyzer (the previous encoder) could
not separate two confirmed-unrelated speakers reliably; different-speaker
scores reached 0.77-0.88 with enrolled-speaker scores at 0.82-0.97,
leaving no usable threshold. SpeechBrain's ECAPA-TDNN
(`speechbrain/spkrec-ecapa-voxceleb`) on the same audio produced a clean
separation: enrolled 0.897-0.931, different 0.072-0.423, margin 0.47.
Thresholds below are set for ECAPA-TDNN's score distribution, not
Resemblyzer's. If rolling back to Resemblyzer, rebase thresholds and
invalidate stored embeddings (the encoders produce different dimensions:
ECAPA 192-d, Resemblyzer 256-d).
"""
import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

import numpy as np
import soundfile as sf
import torch
from speechbrain.inference.speaker import EncoderClassifier
from sqlalchemy.orm import Session

from app.db.models import User, VoiceProfile

logger = logging.getLogger(__name__)


# Thresholds for speaker verification. Lower threshold = more permissive.
# ECAPA-TDNN cosine-similarity scores run in roughly [-0.1, +1.0]. The
# 2026-04-22 evaluation measured a minimum same-speaker score of 0.897
# and a maximum different-speaker score of 0.423, so strict=0.70 gives a
# ~0.28 safety buffer in both directions.
THRESHOLDS = {
    "strict": 0.70,   # very confident match required
    "medium": 0.55,   # default: balanced
    "loose": 0.40,    # permissive, for multi-user households
    "off": 0.0,       # effectively disabled
}


# Lazy-loaded encoder. First call downloads ~80 MB of weights to
# REPO_ROOT/.cache/spkrec-ecapa/ (configured below) and compiles the model,
# which takes several seconds. Subsequent calls reuse the loaded instance.
_encoder: Optional[EncoderClassifier] = None

_CACHE_DIR = Path(__file__).resolve().parent.parent.parent / ".cache" / "spkrec-ecapa"


def get_encoder() -> EncoderClassifier:
    global _encoder
    if _encoder is None:
        logger.info("Loading ECAPA-TDNN speaker encoder (first run downloads weights)...")
        _encoder = EncoderClassifier.from_hparams(
            source="speechbrain/spkrec-ecapa-voxceleb",
            savedir=str(_CACHE_DIR),
            run_opts={"device": "cpu"},
        )
        logger.info("ECAPA-TDNN encoder ready")
    return _encoder


def _decode_to_16k_mono(audio_path: Path) -> Path:
    """Sarvam/Telegram audio (OGG, M4A, MP3, MP4, MPEG) won't always load
    directly via soundfile. Route through bundled ffmpeg to a 16 kHz mono
    WAV that soundfile + ECAPA can both consume. Temporary file path is
    returned; caller is not responsible for cleanup (temp dir).
    """
    import imageio_ffmpeg
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    wav = Path(tempfile.gettempdir()) / f"{audio_path.stem}.{audio_path.suffix[1:]}.16k.wav"
    subprocess.run(
        [ffmpeg, "-y", "-i", str(audio_path), "-ar", "16000", "-ac", "1", str(wav)],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True,
    )
    return wav


def compute_embedding(audio_path: Path) -> np.ndarray:
    """Extract a 192-dimensional voice embedding from an audio file.

    Returns an L2-normalized float32 numpy array, ready for cosine
    similarity against another embedding computed the same way.
    """
    wav_path = _decode_to_16k_mono(audio_path)
    signal, sr = sf.read(str(wav_path), dtype="float32")
    assert sr == 16000, f"expected 16 kHz, got {sr}"
    if signal.ndim > 1:
        signal = signal.mean(axis=1)
    tensor = torch.from_numpy(signal).unsqueeze(0)  # [1, T]

    encoder = get_encoder()
    with torch.no_grad():
        emb = encoder.encode_batch(tensor)
    emb = emb.squeeze().cpu().numpy().astype(np.float32)
    # L2 normalize so cosine similarity is a simple dot product.
    return emb / (np.linalg.norm(emb) + 1e-12)


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Cosine similarity between two embedding vectors, in [-1, 1]."""
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-12))


def verify_speaker(
    db: Session, user: User, audio_path: Path
) -> tuple[bool, float]:
    """Check if an audio file matches any of the user's enrolled voice profiles.

    Returns (is_match, best_similarity_score).

    If the user is not enrolled, returns (True, 1.0) so the command is allowed
    through. Enrollment is mandatory only when the shopkeeper opts into
    verification by setting a non-off security threshold.

    If security_threshold is "off", always returns (True, 0.0).
    """
    if user.security_threshold == "off":
        return (True, 0.0)

    if not user.enrolled:
        # Not yet enrolled - allow through but log
        logger.info(f"User {user.id} not enrolled, allowing command through")
        return (True, 0.0)

    profiles = db.query(VoiceProfile).filter(VoiceProfile.user_id == user.id).all()
    if not profiles:
        logger.warning(f"User {user.id} marked enrolled but has no profiles")
        return (True, 0.0)

    try:
        new_embedding = compute_embedding(audio_path)
    except Exception as e:
        logger.exception(f"Failed to compute embedding: {e}")
        return (True, 0.0)  # Fail-open: don't block commands due to audio issues

    # Check against each enrolled embedding, take the best match.
    # Profiles persisted under the old Resemblyzer encoder are 256-d and
    # will produce nonsense scores against a 192-d ECAPA embedding; the
    # 2026-04-22 encoder swap assumes those profiles are re-captured
    # before meaningful verification. We still attempt scoring rather
    # than hard-failing so a stale profile doesn't brick the bot.
    best_score = -1.0
    for profile in profiles:
        stored = np.frombuffer(profile.embedding, dtype=np.float32)
        if stored.shape[0] != new_embedding.shape[0]:
            logger.warning(
                f"Profile {profile.id} has dim {stored.shape[0]}, "
                f"current encoder produces {new_embedding.shape[0]}. "
                f"User needs to re-enroll."
            )
            continue
        score = cosine_similarity(new_embedding, stored)
        if score > best_score:
            best_score = score

    threshold = THRESHOLDS.get(user.security_threshold, THRESHOLDS["medium"])
    is_match = best_score >= threshold

    logger.info(
        f"Speaker verification: user={user.id} score={best_score:.3f} "
        f"threshold={threshold:.3f} ({user.security_threshold}) match={is_match}"
    )
    return (is_match, best_score)


def store_enrollment(
    db: Session, user: User, audio_path: Path, label: str = "enrollment"
) -> VoiceProfile:
    """Compute embedding from an enrollment audio file and store it.

    Returns the created VoiceProfile row.
    """
    embedding = compute_embedding(audio_path)
    # Store as float32 bytes for compact storage (ECAPA-TDNN = 192 × 4 = 768 bytes).
    embedding_bytes = embedding.astype(np.float32).tobytes()

    profile = VoiceProfile(
        user_id=user.id,
        embedding=embedding_bytes,
        sample_label=label,
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile
