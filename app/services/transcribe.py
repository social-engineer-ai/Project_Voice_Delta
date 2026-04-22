"""Sarvam Saaras speech-to-text wrapper.

Uses saaras:v3 in codemix mode, language_code="hi-IN". Saaras v3 is Sarvam's
current recommended ASR (saarika v2.5 is on their deprecation path) and
fixes proper-noun errors that v2.5 makes on common Hindi names: v2.5 heard
"Ramu" as "Naamu" in our 2026-04-22 evaluation; saaras:v3 gets it right.

Codemix mode preserves English loanwords (phone, call, delivery, SMS,
WhatsApp, accountant) in Latin script alongside Devanagari, which matches
how Indian shopkeepers actually speak and gives the downstream intent
classifier a more faithful signal than forced-Devanagari output does.

Pricing (April 2026): ₹30 per hour of audio = ₹0.50 per minute. Mode and
model don't affect price per the public pricing page.
"""
import logging
from pathlib import Path
import httpx

from app.config import settings

logger = logging.getLogger(__name__)


async def transcribe_audio(audio_path: Path, language_code: str = "hi-IN") -> str:
    """Transcribe an audio file using Sarvam saaras:v3 codemix.

    Args:
        audio_path: local path to an audio file (OGG from Telegram works directly)
        language_code: default "hi-IN"; pass "unknown" for auto-detect if the
            shop later supports languages beyond Hindi.

    Returns:
        Transcribed text mixing Devanagari for Hindi words and Latin for
        English loanwords, as spoken.
    """
    headers = {"api-subscription-key": settings.sarvam_api_key}

    with open(audio_path, "rb") as f:
        files = {"file": (audio_path.name, f, "audio/ogg")}
        data = {
            "model": "saaras:v3",
            "mode": "codemix",
            "language_code": language_code,
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                settings.sarvam_stt_url,
                headers=headers,
                files=files,
                data=data,
            )

    if response.status_code != 200:
        logger.error(f"Sarvam error {response.status_code}: {response.text}")
        response.raise_for_status()

    result = response.json()
    transcript = result.get("transcript", "")
    detected_language = result.get("language_code", "")
    logger.info(f"Transcribed ({detected_language}): {transcript}")
    return transcript
