"""
LiveKit webhook handler: receives real-time room events.
"""
from fastapi import APIRouter, Request, HTTPException
from app.services.call_service import update_call_status, finalize_call
from app.models.call import CallStatus
import hmac, hashlib, json
from app.core.config import settings

router = APIRouter()


def verify_livekit_webhook(body: bytes, signature: str) -> bool:
    """Verify the webhook signature from LiveKit."""
    expected = hmac.new(
        settings.LIVEKIT_API_SECRET.encode(),
        body,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


@router.post("/livekit")
async def livekit_webhook(request: Request):
    body = await request.body()
    signature = request.headers.get("x-livekit-signature", "")

    # Validate signature in production
    if not settings.DEBUG:
        if not verify_livekit_webhook(body, signature):
            raise HTTPException(status_code=401, detail="Invalid signature")

    try:
        event = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    event_type = event.get("event")
    room = event.get("room", {})
    room_name = room.get("name", "")

    # Map room_name to call_id (convention: jansamvaad-{call_id_prefix})
    # In production, look this up from DB
    if event_type == "room_started":
        pass  # call is already created before room starts
    elif event_type == "participant_joined":
        # Update to in_progress when citizen joins
        pass
    elif event_type == "room_finished":
        # Finalize call
        pass

    return {"received": True, "event": event_type}
