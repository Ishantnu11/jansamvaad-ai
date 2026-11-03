"""
Sarvam AI integration for Hindi STT (Speech-to-Text) and TTS (Text-to-Speech).
Docs: https://docs.sarvam.ai
"""
import httpx
import base64
from typing import Optional
from app.core.config import settings


SARVAM_STT_URL = f"{settings.SARVAM_API_URL}/speech-to-text"
SARVAM_TTS_URL = f"{settings.SARVAM_API_URL}/text-to-speech"
SARVAM_TRANSLATE_URL = f"{settings.SARVAM_API_URL}/translate"


async def transcribe_audio(audio_bytes: bytes, language_code: str = "hi-IN") -> dict:
    """
    Convert audio bytes to text using Sarvam AI STT.
    Returns dict with 'transcript' and 'language_code' keys.
    Supports: hi-IN (Hindi), en-IN (English), and auto-detection for Hinglish.
    """
    audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
    payload = {
        "model": "saarika:v2",
        "language_code": language_code,
        "with_timestamps": False,
        "with_disfluencies": False,
        "audio": audio_b64,
    }
    headers = {
        "api-subscription-key": settings.SARVAM_API_KEY,
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(SARVAM_STT_URL, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        return {
            "transcript": data.get("transcript", ""),
            "language_code": data.get("language_code", language_code),
        }


async def synthesize_speech(
    text: str,
    target_language_code: str = "hi-IN",
    speaker: str = "simran",
    pitch: float = 0,
    pace: float = 1.0,
    loudness: float = 1.5,
) -> bytes:
    """
    Convert text to Hindi speech using Sarvam AI TTS.
    Returns raw audio bytes (WAV format).
    Available speakers: simran, pooja, ritu, aditya, rahul, etc.
    """
    payload = {
        "inputs": [text],
        "target_language_code": target_language_code,
        "speaker": speaker,
        "pitch": pitch,
        "pace": pace,
        "loudness": loudness,
        "speech_sample_rate": 8000,
        "enable_preprocessing": True,
        "model": "bulbul:v3",
    }
    headers = {
        "api-subscription-key": settings.SARVAM_API_KEY,
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(SARVAM_TTS_URL, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        audio_b64 = data["audios"][0]
        return base64.b64decode(audio_b64)


async def translate_to_hindi(text: str, source_language: str = "en-IN") -> str:
    """Translate English or Hinglish text to Hindi for LLM processing."""
    payload = {
        "input": text,
        "source_language_code": source_language,
        "target_language_code": "hi-IN",
        "speaker_gender": "Male",
        "mode": "formal",
        "model": "mayura:v1",
        "enable_preprocessing": False,
    }
    headers = {
        "api-subscription-key": settings.SARVAM_API_KEY,
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(SARVAM_TRANSLATE_URL, json=payload, headers=headers)
        response.raise_for_status()
        return response.json().get("translated_text", text)
