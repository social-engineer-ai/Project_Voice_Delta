"""Sarvam Saarika speech-to-text wrapper.

Sarvam's Saarika ASR handles Hindi, code-mixed Hindi-English, and 9 other
Indian languages. We use language_code="unknown" to auto-detect, which works
well for code-mixed speech.

Pricing (April 2026): ₹30 per hour of audio = ₹0.50 per minute.
"""
import logging
from pathlib import Path
import httpx

from app.config import settings

logger = logging.getLogger(__name__)


async def transcribe_audio(audio_path: Path, language_code: str = "unknown") -> str:
    """Transcribe an audio file using Sarvam Saarika.

    Args:
        audio_path: local path to an audio file (OGG from Telegram works directly)
        language_code: "hi-IN", "en-IN", "unknown" (auto-detect), etc.

    Returns:
        Transcribed text in the detected/specified language.
    """
    headers = {"api-subscription-key": settings.sarvam_api_key}

    with open(audio_path, "rb") as f:
        files = {"file": (audio_path.name, f, "audio/ogg")}
        data = {
            "model": "saarika:v2.5",
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
