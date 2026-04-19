"""Speaker verification service using Resemblyzer.

Builds and compares voice embeddings for the trust layer. Each user enrolls
their voice by recording a few phrases. Each subsequent voice command is
checked against the enrolled embeddings before being processed.

This is a trust feature, not a security feature: the goal is to visibly
demonstrate to customers that the bot responds only to the shopkeeper.
False acceptance/rejection tradeoff is configurable per shop via
User.security_threshold.
"""
import logging
from pathlib import Path
from typing import Optional

import numpy as np
from resemblyzer import VoiceEncoder, preprocess_wav
from sqlalchemy.orm import Session

from app.db.models import User, VoiceProfile

logger = logging.getLogger(__name__)


# Thresholds for speaker verification. Lower threshold = more permissive.
# These are cosine-similarity values in Resemblyzer's embedding space.
# Calibrate these based on field testing with the 12th grader's recordings.
THRESHOLDS = {
    "strict": 0.75,   # very confident match required
    "medium": 0.65,   # default: balanced
    "loose": 0.55,    # permissive, for multi-user households
    "off": 0.0,       # effectively disabled
}


# Lazy-loaded encoder so import time is fast
_encoder: Optional[VoiceEncoder] = None


def get_encoder() -> VoiceEncoder:
    """Lazy-load the Resemblyzer encoder (first call takes a few seconds)."""
    global _encoder
    if _encoder is None:
        logger.info("Loading Resemblyzer encoder...")
        _encoder = VoiceEncoder()
        logger.info("Resemblyzer encoder ready")
    return _encoder


def compute_embedding(audio_path: Path) -> np.ndarray:
    """Extract a 256-dim voice embedding from an audio file.

    Resemblyzer handles resampling internally. Works with .wav, .ogg (via
    librosa), mp3, m4a, etc.
    """
    wav = preprocess_wav(audio_path)
    encoder = get_encoder()
    embedding = encoder.embed_utterance(wav)
    return embedding


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Cosine similarity between two embedding vectors, in [-1, 1]."""
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


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

    # Check against each enrolled embedding, take the best match
    best_score = -1.0
    for profile in profiles:
        stored = np.frombuffer(profile.embedding, dtype=np.float32)
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
    # Store as float32 bytes for compact storage
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
