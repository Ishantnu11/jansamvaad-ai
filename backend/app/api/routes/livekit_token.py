from fastapi import APIRouter, Query
from app.services.livekit_service import generate_agent_token, generate_admin_token

router = APIRouter()


@router.get("/token")
async def get_livekit_token(
    room: str = Query(..., description="Room name"),
    participant: str = Query("citizen", description="Participant identity"),
):
    """Generate a LiveKit access token for a room participant."""
    token = await generate_agent_token(room_name=room, participant_name=participant)
    return {"token": token, "room": room, "participant": participant}
