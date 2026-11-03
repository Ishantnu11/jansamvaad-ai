"""
LiveKit token generation and room management.
"""
from livekit.api import AccessToken, VideoGrants
from app.core.config import settings


async def generate_agent_token(room_name: str, participant_name: str = "citizen") -> str:
    """
    Generate a short-lived LiveKit JWT for a participant to join a room.
    The agent itself uses a separate admin token.
    """
    token = (
        AccessToken(api_key=settings.LIVEKIT_API_KEY, api_secret=settings.LIVEKIT_API_SECRET)
        .with_identity(participant_name)
        .with_name(participant_name)
        .with_grants(
            VideoGrants(
                room_join=True,
                room=room_name,
                can_publish=True,
                can_subscribe=True,
            )
        )
    )
    return token.to_jwt()


async def generate_admin_token(room_name: str) -> str:
    """Generate an admin token for the AI agent to join and control the room."""
    token = (
        AccessToken(api_key=settings.LIVEKIT_API_KEY, api_secret=settings.LIVEKIT_API_SECRET)
        .with_identity("jansamvaad-agent")
        .with_name("JanSamvaad AI Agent")
        .with_grants(
            VideoGrants(
                room_join=True,
                room=room_name,
                can_publish=True,
                can_subscribe=True,
                room_admin=True,
            )
        )
    )
    return token.to_jwt()


async def dial_outbound_sip_phone(phone_number: str, room_name: str) -> bool:
    """Trigger an outbound cellular phone call via LiveKit SIP."""
    if not settings.LIVEKIT_SIP_TRUNK_ID or not phone_number:
        return False
    try:
        from livekit import api
        from livekit.protocol import sip as proto_sip
        lk = api.LiveKitAPI(settings.LIVEKIT_URL, settings.LIVEKIT_API_KEY, settings.LIVEKIT_API_SECRET)
        req = proto_sip.CreateSIPParticipantRequest(
            sip_trunk_id=settings.LIVEKIT_SIP_TRUNK_ID,
            sip_call_to=phone_number,
            room_name=room_name,
            participant_identity=f"phone-{phone_number}",
            participant_name="Citizen (Phone)"
        )
        await lk.sip.create_sip_participant(req)
        await lk.aclose()
        print(f"📞 Successfully placed outbound SIP call to {phone_number} in room {room_name}")
        return True
    except Exception as e:
        print(f"❌ Failed to place outbound SIP call: {e}")
        return False
