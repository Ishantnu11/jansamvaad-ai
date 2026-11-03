"""
Post-call notification service for WhatsApp & SMS.
Dispatches summary tickets to citizens after survey completion.
"""
import logging
import httpx
from typing import Optional

logger = logging.getLogger("notification-service")

async def send_whatsapp_summary(
    phone_number: str,
    citizen_name: Optional[str],
    ticket_id: str,
    category: str,
    summary: str,
    meta_token: Optional[str] = None,
    phone_number_id: Optional[str] = None
) -> bool:
    """
    Send WhatsApp message via WhatsApp Cloud API.
    """
    if not meta_token or not phone_number_id or not phone_number:
        logger.info(f"📱 [Simulated WhatsApp] To: {phone_number} | Ticket #{ticket_id}: आपकी {category} की समस्या दर्ज कर ली गई है।")
        return True

    url = f"https://graph.facebook.com/v19.0/{phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {meta_token}",
        "Content-Type": "application/json"
    }
    name = citizen_name or "नागरिक"
    body_text = (
        f"नमस्ते {name} जी,\n\n"
        f"जनसंवाद AI से बात करने के लिए धन्यवाद। आपकी समस्या दर्ज कर ली गई है:\n"
        f"📋 टिकट ID: #{ticket_id[:8].upper()}\n"
        f"📂 विषय: {category}\n"
        f"📝 विवरण: {summary}\n\n"
        f"संबंधित विभाग को आपकी प्रतिक्रिया भेज दी गई है।"
    )
    payload = {
        "messaging_product": "whatsapp",
        "to": phone_number,
        "type": "text",
        "text": {"body": body_text}
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            res = await client.post(url, json=payload, headers=headers)
            res.raise_for_status()
            logger.info(f"✅ WhatsApp alert sent to {phone_number}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to dispatch WhatsApp: {e}")
            return False

async def send_sms_summary(
    phone_number: str,
    ticket_id: str,
    category: str,
    twilio_sid: Optional[str] = None,
    twilio_token: Optional[str] = None,
    twilio_from: Optional[str] = None
) -> bool:
    """
    Send SMS alert via Twilio REST API.
    """
    if not (twilio_sid and twilio_token and twilio_from and phone_number):
        logger.info(f"📩 [Simulated SMS] To: {phone_number} | JanSamvaad: Ticket #{ticket_id[:8].upper()} registered for {category}.")
        return True

    url = f"https://api.twilio.com/2010-04-01/Accounts/{twilio_sid}/Messages.json"
    data = {
        "To": phone_number,
        "From": twilio_from,
        "Body": f"जनसंवाद AI: आपकी {category} की समस्या (टिकट #{ticket_id[:8].upper()}) दर्ज हो चुकी है। धन्यवाद।"
    }
    async with httpx.AsyncClient(auth=(twilio_sid, twilio_token), timeout=10.0) as client:
        try:
            res = await client.post(url, data=data)
            res.raise_for_status()
            logger.info(f"✅ SMS sent to {phone_number}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to dispatch SMS: {e}")
            return False
