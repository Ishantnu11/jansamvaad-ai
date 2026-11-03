"""
JanSamvaad AI Voice Agent — LiveKit Agents implementation.
Handles real-time Hindi voice conversations with:
  - Sarvam AI STT/TTS for Hindi/Hinglish support
  - Gemini/OpenAI LLM for conversation intelligence
  - Interruption handling via LiveKit's VAD
  - Latency monitoring
  - MongoDB persistence via FastAPI backend
"""

import asyncio
import logging
import time
import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

import httpx
from livekit import agents, rtc
from livekit.agents import (
    AgentSession,
    Agent,
    RoomInputOptions,
    function_tool,
)
from livekit.plugins import openai as lk_openai, silero

logger = logging.getLogger("jansamvaad-agent")

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
SARVAM_API_KEY = os.getenv("SARVAM_API_KEY", "")
SARVAM_API_URL = "https://api.sarvam.ai"

SYSTEM_PROMPT = """आप JanSamvaad AI हैं — एक सरकारी सर्वे AI असिस्टेंट जो नागरिकों से हिंदी में बात करता है।

आपके नियम:
1. हमेशा हिंदी में बात करें। अगर नागरिक Hinglish बोले तो उसे समझें पर जवाब हिंदी में दें।
2. आप एक AI हैं — यह हमेशा स्पष्ट रखें।
3. सर्वे का विषय: सार्वजनिक सुविधाएं (पानी, सड़क, बिजली, स्वास्थ्य, शिक्षा)।
4. एक बार में एक ही सवाल पूछें।
5. नागरिक की बात ध्यान से सुनें और संदर्भ के अनुसार अगला सवाल पूछें।
6. यदि नागरिक कोई समस्या बताए, उसकी गंभीरता और अवधि पूछें।
7. नागरिक अगर बात नहीं करना चाहे — तुरंत सम्मान के साथ विदाई दें।
8. कभी भी राजनीतिक राय न दें।
9. हर जवाब संक्षिप्त रखें (2-3 वाक्य)।

पहला संदेश हमेशा यह होना चाहिए:
"नमस्ते! मैं जनसंवाद AI असिस्टेंट बोल रहा हूँ। क्या आपके पास दो मिनट का समय है?"

सर्वे पूरा होने पर, JSON summary इस format में दें:
{"category": "...", "severity": "low|medium|high", "issue_description": "...", "location_mentioned": "...", "days_ongoing": null, "citizen_sentiment": "positive|neutral|negative|frustrated|satisfied", "resolved": false}"""


class SarvamSTT:
    """
    Custom Sarvam AI STT wrapper compatible with LiveKit Agents.
    Wraps the Sarvam /speech-to-text endpoint for Hindi/Hinglish.
    """

    def __init__(self, api_key: str, language_code: str = "hi-IN"):
        self.api_key = api_key
        self.language_code = language_code
        self._http = httpx.AsyncClient(timeout=30.0)

    async def transcribe(self, audio_bytes: bytes) -> str:
        import base64
        audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
        payload = {
            "model": "saarika:v2",
            "language_code": self.language_code,
            "with_timestamps": False,
            "with_disfluencies": False,
            "audio": audio_b64,
        }
        headers = {
            "api-subscription-key": self.api_key,
            "Content-Type": "application/json",
        }
        try:
            response = await self._http.post(
                f"{SARVAM_API_URL}/speech-to-text",
                json=payload,
                headers=headers,
            )
            response.raise_for_status()
            return response.json().get("transcript", "")
        except Exception as e:
            logger.error(f"Sarvam STT error: {e}")
            return ""

    async def close(self):
        await self._http.aclose()


class SarvamTTS:
    """
    Custom Sarvam AI TTS wrapper.
    Returns PCM audio bytes at 8kHz mono for telephony.
    """

    def __init__(self, api_key: str, speaker: str = "meera"):
        self.api_key = api_key
        self.speaker = speaker
        self._http = httpx.AsyncClient(timeout=30.0)

    async def synthesize(self, text: str) -> bytes:
        import base64
        payload = {
            "inputs": [text],
            "target_language_code": "hi-IN",
            "speaker": self.speaker,
            "pitch": 0,
            "pace": 1.0,
            "loudness": 1.5,
            "speech_sample_rate": 8000,
            "enable_preprocessing": True,
            "model": "bulbul:v1",
        }
        headers = {
            "api-subscription-key": self.api_key,
            "Content-Type": "application/json",
        }
        try:
            response = await self._http.post(
                f"{SARVAM_API_URL}/text-to-speech",
                json=payload,
                headers=headers,
            )
            response.raise_for_status()
            audio_b64 = response.json()["audios"][0]
            return base64.b64decode(audio_b64)
        except Exception as e:
            logger.error(f"Sarvam TTS error: {e}")
            return b""

    async def close(self):
        await self._http.aclose()


class LatencyMonitor:
    """Track response latency: time from user speech end to agent speech start."""

    def __init__(self):
        self._user_stop_time: Optional[float] = None
        self.latencies: list[float] = []

    def record_user_stop(self):
        self._user_stop_time = time.monotonic()

    def record_agent_start(self) -> Optional[int]:
        if self._user_stop_time is None:
            return None
        latency_ms = int((time.monotonic() - self._user_stop_time) * 1000)
        self.latencies.append(latency_ms)
        self._user_stop_time = None
        logger.info(f"⚡ Response latency: {latency_ms}ms")
        return latency_ms

    @property
    def avg_latency_ms(self) -> Optional[float]:
        return sum(self.latencies) / len(self.latencies) if self.latencies else None


class JanSamvaadAgent(Agent):
    """
    The core JanSamvaad AI voice agent.
    Manages conversation state, latency monitoring, and backend persistence.
    """

    def __init__(self, call_id: str, sarvam_stt: SarvamSTT, sarvam_tts: SarvamTTS):
        super().__init__(instructions=SYSTEM_PROMPT)
        self.call_id = call_id
        self.sarvam_stt = sarvam_stt
        self.sarvam_tts = sarvam_tts
        self.latency_monitor = LatencyMonitor()
        self.turn_count = 0
        self.interruptions = 0
        self._http = httpx.AsyncClient(timeout=30.0)

    async def on_user_turn_completed(self, turn_ctx, new_message):
        """Called when the user finishes speaking — record latency start."""
        self.latency_monitor.record_user_stop()
        self.turn_count += 1

        # Persist turn to backend
        await self._persist_turn(
            speaker="citizen",
            text=new_message.content if hasattr(new_message, "content") else str(new_message),
        )

    async def on_agent_turn_start(self, turn_ctx):
        """Called when the agent starts responding — measure latency."""
        latency = self.latency_monitor.record_agent_start()
        if latency:
            logger.info(f"📊 Latency recorded: {latency}ms")

    async def on_speech_interrupted(self):
        """Handle mid-response interruptions gracefully."""
        self.interruptions += 1
        logger.info(f"🛑 Interruption #{self.interruptions} — stopping speech")

    async def _persist_turn(self, speaker: str, text: str, latency_ms: Optional[int] = None):
        """Send a conversation turn to the FastAPI backend."""
        try:
            payload = {
                "speaker": speaker,
                "text": text,
                "latency_ms": latency_ms,
            }
            await self._http.post(
                f"{BACKEND_URL}/api/calls/{self.call_id}/turn",
                json=payload,
            )
        except Exception as e:
            logger.warning(f"Could not persist turn: {e}")

    async def on_session_end(self):
        """Finalize the call when session ends."""
        try:
            await self._http.post(f"{BACKEND_URL}/api/calls/{self.call_id}/end")
        except Exception as e:
            logger.warning(f"Could not finalize call: {e}")
        finally:
            await self._http.aclose()
            await self.sarvam_stt.close()
            await self.sarvam_tts.close()


async def entrypoint(ctx: agents.JobContext):
    """LiveKit agent entrypoint — called for each new room."""
    logger.info(f"🎙️ JanSamvaad Agent joining room: {ctx.room.name}")

    # Extract call_id from room name (format: jansamvaad-{call_id_prefix})
    room_name = ctx.room.name
    call_id = room_name.replace("jansamvaad-", "")

    # Initialize Sarvam AI services
    sarvam_stt = SarvamSTT(api_key=SARVAM_API_KEY, language_code="hi-IN")
    sarvam_tts = SarvamTTS(api_key=SARVAM_API_KEY, speaker="meera")

    # Create the agent
    agent = JanSamvaadAgent(
        call_id=call_id,
        sarvam_stt=sarvam_stt,
        sarvam_tts=sarvam_tts,
    )

    # Use OpenAI-compatible LLM (works with Gemini via OpenAI-compat endpoint too)
    llm = lk_openai.LLM(
        model="gpt-4o-mini",
        api_key=os.getenv("OPENAI_API_KEY"),
    )

    # Use Silero VAD for Voice Activity Detection (interruption handling)
    vad = silero.VAD.load()

    session = AgentSession(
        vad=vad,
        llm=llm,
        # Note: When Sarvam LiveKit plugin is available, swap stt/tts below
        stt=lk_openai.STT(model="whisper-1"),  # fallback STT
        tts=lk_openai.TTS(model="tts-1", voice="alloy"),  # fallback TTS
    )

    await session.start(
        room=ctx.room,
        agent=agent,
        room_input_options=RoomInputOptions(),
    )

    # Greet the citizen
    await session.generate_reply(
        instructions="नागरिक को हिंदी में नमस्ते करें और पूछें कि क्या उनके पास दो मिनट का समय है।"
    )

    logger.info("✅ JanSamvaad Agent session started")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    agents.cli.run_app(
        agents.WorkerOptions(
            entrypoint_fnc=entrypoint,
            agent_name="jansamvaad-agent",
        )
    )
