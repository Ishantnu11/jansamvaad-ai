"""
Exotel Voice Service for Indian Cloud Telephony.
Enables outbound calling to Indian mobile numbers via Exotel REST API.
"""

import logging
import requests
from typing import Optional, Dict, Any
from app.core.config import settings

logger = logging.getLogger(__name__)


def is_exotel_configured() -> bool:
    """Check if Exotel credentials are configured."""
    return bool(
        settings.EXOTEL_ACCOUNT_SID
        and settings.EXOTEL_API_KEY
        and settings.EXOTEL_API_TOKEN
        and settings.EXOTEL_CALLER_ID
    )


def format_indian_number(phone_number: str) -> str:
    """
    Format phone number for Exotel:
    Exotel works best with 10-digit mobile prefixed with 0 (e.g., 09991317827).
    """
    cleaned = "".join(c for c in phone_number if c.isdigit())
    if cleaned.startswith("91") and len(cleaned) == 12:
        return "0" + cleaned[2:]
    elif len(cleaned) == 10:
        return "0" + cleaned
    elif cleaned.startswith("0") and len(cleaned) == 11:
        return cleaned
    return phone_number.strip()


def make_exotel_call(
    to_number: str,
    app_url: Optional[str] = None,
    call_type: str = "trans",
    time_limit: int = 300,
    time_out: int = 30
) -> Dict[str, Any]:
    """
    Place an outbound call via Exotel.
    
    :param to_number: The recipient Indian phone number (e.g. +919991317827 or 09991317827)
    :param app_url: The ExoML Flow URL to execute once connected
    :param call_type: "trans" (transactional) or "promo" (promotional)
    :param time_limit: Max duration in seconds
    :param time_out: Ringing timeout in seconds
    :return: Dict with success status, call_sid, or error message
    """
    if not is_exotel_configured():
        return {
            "success": False,
            "error": "Exotel is not configured. Check EXOTEL_ACCOUNT_SID, EXOTEL_API_KEY, EXOTEL_API_TOKEN, EXOTEL_CALLER_ID in .env"
        }

    formatted_to = format_indian_number(to_number)
    endpoint = f"https://{settings.EXOTEL_SUBDOMAIN}/v1/Accounts/{settings.EXOTEL_ACCOUNT_SID}/Calls/connect.json"
    flow_url = app_url or settings.EXOTEL_APP_URL

    payload = {
        "From": formatted_to,
        "CallerId": settings.EXOTEL_CALLER_ID,
        "CallType": call_type,
        "TimeLimit": str(time_limit),
        "TimeOut": str(time_out),
    }

    if flow_url:
        payload["Url"] = flow_url

    try:
        logger.info(f"Placing Exotel call from virtual {settings.EXOTEL_CALLER_ID} to {formatted_to}...")
        resp = requests.post(
            endpoint,
            data=payload,
            auth=(settings.EXOTEL_API_KEY, settings.EXOTEL_API_TOKEN),
            timeout=15
        )

        if resp.status_code in (200, 201):
            data = resp.json().get("Call", {})
            call_sid = data.get("Sid")
            status = data.get("Status")
            logger.info(f"Exotel call placed successfully! SID={call_sid}, Status={status}")
            return {
                "success": True,
                "provider": "exotel",
                "call_sid": call_sid,
                "status": status,
                "from": settings.EXOTEL_CALLER_ID,
                "to": formatted_to
            }
        else:
            logger.error(f"Exotel API error ({resp.status_code}): {resp.text}")
            return {
                "success": False,
                "provider": "exotel",
                "error": f"Exotel error {resp.status_code}: {resp.text}"
            }
    except Exception as e:
        logger.error(f"Failed to place Exotel call: {e}")
        return {
            "success": False,
            "provider": "exotel",
            "error": str(e)
        }
