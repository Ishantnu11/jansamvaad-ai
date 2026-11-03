"""
Custom LiveKit-compatible Sarvam AI STT/TTS plugin.
Wraps Sarvam endpoints in the livekit-agents plugin interface
so they can be swapped in for OpenAI STT/TTS seamlessly.

Usage:
    from sarvam_livekit_plugin import SarvamSTTPlugin, SarvamTTSPlugin
    session = AgentSession(stt=SarvamSTTPlugin(), tts=SarvamTTSPlugin())
"""

import asyncio
import base64
import logging
import os
from typing import AsyncIterator

import httpx

logger = logging.getLogger("sarvam-plugin")

SARVAM_API_KEY = os.getenv("SARVAM_API_KEY", "")
SARVAM_API_URL = "https://api.sarvam.ai"


class SarvamSTTPlugin:
    """
    Sarvam AI Speech-to-Text plugin.
    Implements the minimal interface expected by livekit-agents AgentSession.
    """

    def __init__(
        self,
        language_code: str = "hi-IN",
        model: str = "saarika:v2",
        api_key: str = SARVAM_API_KEY,
    ):
        self.language_code = language_code
        self.model = model
        self.api_key = api_key

    async def recognize(self, audio_bytes: bytes) -> str:
        """Transcribe audio bytes to text."""
        audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
        payload = {
            "model": self.model,
            "language_code": self.language_code,
            "with_timestamps": False,
            "with_disfluencies": False,
            "audio": audio_b64,
        }
        headers = {
            "api-subscription-key": self.api_key,
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=20.0) as client:
            try:
                r = await client.post(
                    f"{SARVAM_API_URL}/speech-to-text",
                    json=payload,
                    headers=headers,
                )
                r.raise_for_status()
                transcript = r.json().get("transcript", "")
                logger.debug(f"STT transcript: {transcript}")
                return transcript
            except httpx.HTTPStatusError as e:
                logger.error(f"Sarvam STT HTTP error {e.response.status_code}: {e.response.text}")
                return ""
            except Exception as e:
                logger.error(f"Sarvam STT error: {e}")
                return ""


class SarvamTTSPlugin:
    """
    Sarvam AI Text-to-Speech plugin.
    Returns WAV audio bytes at 8kHz for telephony-grade audio.
    """

    SPEAKERS = ["meera", "pavithra", "maitreyi", "arvind", "amol", "amartya"]

    def __init__(
        self,
        speaker: str = "meera",
        language_code: str = "hi-IN",
        model: str = "bulbul:v1",
        pace: float = 1.0,
        pitch: float = 0.0,
        loudness: float = 1.5,
        sample_rate: int = 8000,
        api_key: str = SARVAM_API_KEY,
    ):
        self.speaker = speaker
        self.language_code = language_code
        self.model = model
        self.pace = pace
        self.pitch = pitch
        self.loudness = loudness
        self.sample_rate = sample_rate
        self.api_key = api_key

    async def synthesize(self, text: str) -> bytes:
        """Convert text to speech, return WAV bytes."""
        payload = {
            "inputs": [text],
            "target_language_code": self.language_code,
            "speaker": self.speaker,
            "pitch": self.pitch,
            "pace": self.pace,
            "loudness": self.loudness,
            "speech_sample_rate": self.sample_rate,
            "enable_preprocessing": True,
            "model": self.model,
        }
        headers = {
            "api-subscription-key": self.api_key,
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=20.0) as client:
            try:
                r = await client.post(
                    f"{SARVAM_API_URL}/text-to-speech",
                    json=payload,
                    headers=headers,
                )
                r.raise_for_status()
                audio_b64 = r.json()["audios"][0]
                return base64.b64decode(audio_b64)
            except httpx.HTTPStatusError as e:
                logger.error(f"Sarvam TTS HTTP error {e.response.status_code}: {e.response.text}")
                return b""
            except Exception as e:
                logger.error(f"Sarvam TTS error: {e}")
                return b""

    async def synthesize_streaming(self, text: str) -> AsyncIterator[bytes]:
        """
        Streaming TTS (chunk-by-chunk sentence synthesis for lower latency).
        Splits text at sentence boundaries and synthesizes each chunk.
        """
        import re
        sentences = re.split(r'(?<=[।.!?])\s+', text.strip())
        for sentence in sentences:
            if sentence.strip():
                audio = await self.synthesize(sentence.strip())
                if audio:
                    yield audio
                    # Small pause between sentences to avoid audio artifacts
                    await asyncio.sleep(0.05)
