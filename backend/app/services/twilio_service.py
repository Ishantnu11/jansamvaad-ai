"""
Twilio Voice Outbound Calling Service for JanSamvaad AI.
Dials citizen phone numbers and streams conversational Hindi voice.
"""
import logging
import httpx
from typing import Optional
from app.core.config import settings

logger = logging.getLogger("twilio-voice")

TWILIO_CALLS_URL = f"https://api.twilio.com/2010-04-01/Accounts/{settings.TWILIO_ACCOUNT_SID}/Calls.json"


async def place_outbound_call(
    to_phone: str,
    greeting_text: str = "नमस्ते! मैं जनसंवाद AI असिस्टेंट बोल रहा हूँ। क्या आपके पास दो मिनट का समय है?",
) -> Optional[str]:
    """
    Places an outbound phone call using Twilio Programmable Voice.
    Speaks the greeting in Hindi to the citizen upon answering.
    """
    account_sid = settings.TWILIO_ACCOUNT_SID
    auth_token = settings.TWILIO_AUTH_TOKEN
    from_phone = (settings.TWILIO_PHONE_NUMBER or "").replace(" ", "").replace("-", "")
    clean_to = to_phone.replace(" ", "").replace("-", "")

    if not (account_sid and auth_token and from_phone):
        logger.warning("Twilio credentials not fully configured in settings.")
        return None

    # Ensure international format
    if not clean_to.startswith("+"):
        clean_to = "+91" + clean_to.lstrip("0")

    calls_url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Calls.json"

    # Twilio trial accounts require an XML URL parameter
    voice_url = getattr(settings, "TWILIO_VOICE_URL", "") or "https://demo.twilio.com/welcome/voice/"

    data = {
        "To": clean_to,
        "From": from_phone,
        "Url": voice_url,
    }

    async with httpx.AsyncClient(
        auth=(account_sid, auth_token),
        timeout=15.0,
    ) as client:
        try:
            res = await client.post(calls_url, data=data)
            if res.status_code in [200, 201]:
                call_sid = res.json().get("sid")
                logger.info(f"✅ Outbound phone call placed to {clean_to}! Call SID: {call_sid}")
                print(f"[TWILIO] Placed call to {clean_to}, SID: {call_sid}")
                return call_sid
            else:
                logger.error(f"❌ Twilio call failed: {res.status_code} - {res.text}")
                print(f"[TWILIO ERROR] {res.status_code}: {res.text}")
                return None
        except Exception as e:
            logger.error(f"❌ Twilio request error: {e}")
            print(f"[TWILIO EXCEPTION] {e}")
            return None

