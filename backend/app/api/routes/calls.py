from fastapi import APIRouter, HTTPException, Query, Request, Response
from typing import Optional, List
import base64
import time
import os
import httpx

from app.core.config import settings

from app.models.call import (
    InitiateCallRequest,
    CallResponse,
    CallStatus,
    ConversationTurn,
    VoiceTurnRequest,
    VoiceTurnResponse,
)
from app.services import call_service
from app.services.livekit_service import generate_agent_token, dial_outbound_sip_phone
from app.services.twilio_service import place_outbound_call
from app.services.exotel_service import make_exotel_call, is_exotel_configured
from app.services.sarvam_service import synthesize_speech, transcribe_audio
from app.services.llm_service import generate_response

router = APIRouter()

GREETING_HINDI = "नमस्ते! मैं जनसंवाद AI असिस्टेंट बोल रहा हूँ। क्या आपके पास दो मिनट का समय है?"


@router.post("/initiate", response_model=CallResponse)
async def initiate_call(request: InitiateCallRequest):
    """Start a new outreach call session with voice greeting."""
    record = await call_service.create_call(
        phone_number=request.phone_number,
        citizen_name=request.citizen_name,
        survey_topic=request.survey_topic,
    )

    # Synthesize initial greeting speech using Sarvam TTS
    audio_b64 = None
    try:
        audio_bytes = await synthesize_speech(GREETING_HINDI)
        if audio_bytes:
            audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
    except Exception as e:
        print(f"Initial TTS error: {e}")

    # Add initial agent greeting turn to MongoDB
    agent_turn = ConversationTurn(speaker="agent", text=GREETING_HINDI, latency_ms=300)
    await call_service.add_conversation_turn(record.call_id, agent_turn)

    # Generate a LiveKit token for this room
    token = await generate_agent_token(room_name=record.room_name, participant_name="citizen")

    # If a phone number is provided, trigger outbound cellular call via LiveKit SIP / Exotel / Twilio
    phone_dialed = False
    dialer_used = None
    if request.phone_number:
        # 1. Primary: LiveKit SIP Outbound Trunk (direct connection into AI Voice Room)
        if settings.LIVEKIT_SIP_TRUNK_ID:
            phone_dialed = await dial_outbound_sip_phone(request.phone_number, record.room_name)
            if phone_dialed:
                dialer_used = f"LiveKit SIP Trunk ({settings.LIVEKIT_SIP_TRUNK_ID})"
                print(f"[SIP] Dialing {request.phone_number} directly into room {record.room_name}")

        # 2. Exotel Cloud Telephony fallback
        clean_num = "".join(c for c in request.phone_number if c.isdigit())
        is_indian = request.phone_number.startswith("+91") or (len(clean_num) == 10) or (clean_num.startswith("91") and len(clean_num) == 12)
        if not phone_dialed and is_indian and is_exotel_configured():
            exotel_res = make_exotel_call(request.phone_number)
            if exotel_res.get("success"):
                phone_dialed = True
                dialer_used = "Exotel (India Telephony)"
            else:
                print(f"Exotel call failed: {exotel_res.get('error')}")

        # 3. Twilio Voice fallback
        if not phone_dialed:
            call_sid = await place_outbound_call(request.phone_number, GREETING_HINDI)
            if call_sid:
                phone_dialed = True
                dialer_used = "Twilio Voice"

    message = "Call initiated."
    if phone_dialed:
        message = f"Outbound cellular call ringing {request.phone_number} via {dialer_used}!"

    return CallResponse(
        call_id=record.call_id,
        room_name=record.room_name,
        status=record.status,
        livekit_token=token,
        message=message,
        greeting_text=GREETING_HINDI,
        audio_base64=audio_b64,
        phone_dialed=phone_dialed,
    )


@router.post("/{call_id}/turn", response_model=VoiceTurnResponse)
async def process_turn(call_id: str, request: VoiceTurnRequest):
    """Process a voice or text turn from the citizen."""
    call = await call_service.get_call(call_id)
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")

    user_text = (request.text or "").strip()
    if not user_text and request.audio_base64:
        try:
            audio_bytes = base64.b64decode(request.audio_base64)
            stt_res = await transcribe_audio(audio_bytes)
            user_text = stt_res.get("transcript", "").strip()
        except Exception as e:
            print(f"STT error: {e}")

    if not user_text:
        raise HTTPException(status_code=400, detail="No speech or text provided")

    start_time = time.monotonic()

    # Append citizen turn
    citizen_turn = ConversationTurn(speaker="citizen", text=user_text)
    await call_service.add_conversation_turn(call_id, citizen_turn)

    # Fetch updated conversation turns for Gemini context
    updated_call = await call_service.get_call(call_id)
    turns = updated_call.get("conversation", [])
    history = []
    # All turns except the last citizen turn that was just added
    for turn in turns[:-1]:
        role = "assistant" if turn["speaker"] == "agent" else "user"
        history.append({"role": role, "content": turn["text"]})

    # Generate next Hindi response with Gemini
    agent_text, is_complete = await generate_response(history, user_text)

    # Synthesize audio response with Sarvam TTS
    audio_b64 = None
    try:
        clean_text = agent_text
        if "{" in clean_text:
            clean_text = clean_text.split("{")[0].strip() or "धन्यवाद, आपकी प्रतिक्रिया दर्ज कर ली गई है।"
        audio_bytes = await synthesize_speech(clean_text)
        if audio_bytes:
            audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
    except Exception as e:
        print(f"Turn TTS error: {e}")

    latency_ms = int((time.monotonic() - start_time) * 1000)

    # Append agent turn
    agent_turn = ConversationTurn(speaker="agent", text=agent_text, latency_ms=latency_ms)
    await call_service.add_conversation_turn(call_id, agent_turn)

    if is_complete:
        await call_service.finalize_call(call_id, agent_text)

    sentiment_val = citizen_turn.sentiment.value if citizen_turn.sentiment else "neutral"

    return VoiceTurnResponse(
        agent_text=agent_text,
        audio_base64=audio_b64,
        is_complete=is_complete,
        sentiment=sentiment_val,
    )


# =====================================================================
# Telephony Webhooks (Exotel & Twilio Integration)
# Connects cellular phone calls directly to Hindi Voice AI
# =====================================================================

GREETING_WAV_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "greeting.wav")
_turn_audio_cache: dict = {}


@router.get("/audio/greeting.wav")
async def get_greeting_audio():
    """Serves the Sarvam AI generated Hindi greeting audio."""
    if os.path.exists(GREETING_WAV_PATH):
        with open(GREETING_WAV_PATH, "rb") as f:
            audio_bytes = f.read()
        return Response(content=audio_bytes, media_type="audio/wav")
    
    audio_bytes = await synthesize_speech(GREETING_HINDI)
    if audio_bytes:
        return Response(content=audio_bytes, media_type="audio/wav")
    raise HTTPException(status_code=404, detail="Audio greeting not available")


@router.get("/audio/turn/{turn_id}.wav")
async def get_turn_audio(turn_id: str):
    """Serves dynamic turn audio for ongoing telephony conversation."""
    if turn_id in _turn_audio_cache:
        return Response(content=_turn_audio_cache[turn_id], media_type="audio/wav")
    raise HTTPException(status_code=404, detail="Audio turn not found")


@router.api_route("/exotel/voice", methods=["GET", "POST"])
async def exotel_voice_webhook(request: Request):
    """
    ExoML Webhook: Triggered when citizen answers the Exotel outbound phone call.
    Plays Hindi greeting (Sarvam TTS) and prompts the citizen to speak.
    """
    base_url = str(request.base_url).rstrip("/")
    if "trycloudflare.com" in base_url or "serveousercontent.com" in base_url:
        base_url = base_url.replace("http://", "https://")
    record_url = f"{base_url}/api/calls/exotel/record"
    play_url = f"{base_url}/api/calls/audio/greeting.wav"

    exoml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Play>{play_url}</Play>
    <Record action="{record_url}" method="POST" maxLength="20" finishOnKey="#" />
</Response>"""
    return Response(content=exoml, media_type="application/xml")


@router.api_route("/exotel/record", methods=["GET", "POST"])
async def exotel_record_webhook(request: Request):
    """
    ExoML Recording Handler: Receives recorded audio from citizen,
    transcribes it using Sarvam STT, generates next response via Gemini LLM,
    synthesizes speech using Sarvam TTS, and returns ExoML to speak the response.
    """
    base_url = str(request.base_url).rstrip("/")
    if "trycloudflare.com" in base_url or "serveousercontent.com" in base_url:
        base_url = base_url.replace("http://", "https://")
    record_url = f"{base_url}/api/calls/exotel/record"
    
    # Exotel can send params via form or query
    recording_url = None
    try:
        form_data = await request.form()
        recording_url = form_data.get("RecordingUrl")
    except Exception:
        pass
    if not recording_url:
        recording_url = request.query_params.get("RecordingUrl", "")

    citizen_text = ""
    if recording_url:
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                rec_resp = await client.get(recording_url)
                if rec_resp.status_code == 200:
                    stt_res = await transcribe_audio(rec_resp.content)
                    citizen_text = stt_res.get("transcript", "").strip()
        except Exception as e:
            print(f"Exotel STT error: {e}")

    if not citizen_text:
        citizen_text = "हाँ जी, मैं सुन रहा हूँ।"

    history = [{"role": "user", "content": citizen_text}]
    agent_text, is_complete = await generate_response(history, citizen_text)

    clean_text = agent_text
    if "{" in clean_text:
        clean_text = clean_text.split("{")[0].strip() or "धन्यवाद, आपकी प्रतिक्रिया दर्ज कर ली गई है।"

    # Generate Sarvam AI audio for this turn
    audio_tag = ""
    try:
        audio_bytes = await synthesize_speech(clean_text)
        if audio_bytes:
            turn_id = str(uuid.uuid4())[:8]
            _turn_audio_cache[turn_id] = audio_bytes
            turn_play_url = f"{base_url}/api/calls/audio/turn/{turn_id}.wav"
            audio_tag = f"<Play>{turn_play_url}</Play>"
    except Exception as e:
        print(f"Turn speech synthesis error: {e}")

    if not audio_tag:
        audio_tag = f'<Say voice="female" language="hi-IN">{clean_text}</Say>'

    if is_complete:
        exoml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    {audio_tag}
    <Hangup/>
</Response>"""
    else:
        exoml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    {audio_tag}
    <Record action="{record_url}" method="POST" maxLength="20" finishOnKey="#" />
</Response>"""

    return Response(content=exoml, media_type="application/xml")


@router.api_route("/twilio/voice", methods=["GET", "POST"])
async def twilio_voice_webhook(request: Request):
    """
    TwiML Webhook: Triggered when citizen answers the Twilio phone call.
    Greets in Hindi and listens for the citizen's speech.
    """
    base_url = settings.PUBLIC_BASE_URL.rstrip("/")
    turn_url = f"{base_url}/api/calls/twilio/turn"
    play_url = f"{base_url}/api/calls/audio/greeting.wav"

    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Play>{play_url}</Play>
    <Gather input="speech" language="hi-IN" action="{turn_url}" method="POST" speechTimeout="auto">
    </Gather>
</Response>"""
    return Response(content=twiml, media_type="application/xml")


@router.post("/twilio/turn")
async def twilio_turn_webhook(request: Request):
    """
    TwiML Turn Handler: Receives live speech recognition result from Twilio,
    processes with Gemini LLM, and speaks back in Hindi.
    """
    base_url = settings.PUBLIC_BASE_URL.rstrip("/")
    turn_url = f"{base_url}/api/calls/twilio/turn"

    form_data = await request.form()
    speech_result = form_data.get("SpeechResult", "").strip()

    if not speech_result:
        speech_result = "नमस्ते"

    history = [{"role": "user", "content": speech_result}]
    agent_text, is_complete = await generate_response(history, speech_result)

    clean_text = agent_text
    if "{" in clean_text:
        clean_text = clean_text.split("{")[0].strip() or "धन्यवाद, आपकी प्रतिक्रिया दर्ज कर ली गई है।"

    if is_complete:
        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Aditi" language="hi-IN">{clean_text}</Say>
    <Hangup/>
</Response>"""
    else:
        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Aditi" language="hi-IN">{clean_text}</Say>
    <Gather input="speech" language="hi-IN" action="{turn_url}" method="POST" speechTimeout="auto">
    </Gather>
</Response>"""

    return Response(content=twiml, media_type="application/xml")


@router.get("/{call_id}")
async def get_call(call_id: str):
    """Retrieve a specific call record."""
    call = await call_service.get_call(call_id)
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
    return call


@router.get("/")
async def list_calls(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
):
    """List all calls with optional status filter."""
    return await call_service.list_calls(skip=skip, limit=limit, status=status)


@router.post("/{call_id}/end")
async def end_call(call_id: str):
    """Manually end a call and trigger summarization."""
    call = await call_service.get_call(call_id)
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
    summary = await call_service.finalize_call(call_id, "")
    return {"call_id": call_id, "status": "completed", "summary": summary}

