"""
LiveKit SIP Telephony Dispatcher for JanSamvaad AI.
Enables real phone numbers (Twilio/Exotel) to connect directly to the Hindi Voice Agent.
"""
import os
import asyncio
import logging
from livekit import api
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("sip-telephony")

LIVEKIT_URL = os.getenv("LIVEKIT_URL")
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET")

async def create_sip_inbound_dispatch(
    trunk_id: str,
    call_prefix: str = "jansamvaad-sip-"
):
    """
    Creates a SIP Inbound Rule in LiveKit Cloud.
    Incoming telephone calls to your Twilio/Exotel SIP Trunk
    are routed automatically to a JanSamvaad AI room.
    """
    livekit_api = api.LiveKitAPI(LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
    
    try:
        # Define SIP dispatch rule
        dispatch_rule = api.SIPDispatchRule(
            rule=api.SIPDispatchRuleDirect(room_name=f"{call_prefix}room")
        )
        
        inbound_trunk = await livekit_api.sip.create_sip_inbound_trunk(
            api.CreateSIPInboundTrunkRequest(
                trunk=api.SIPInboundTrunkInfo(
                    name="JanSamvaad-Phone-Inbound",
                    numbers=["+17372508034"] # Your assigned phone number
                )
            )
        )
        logger.info(f"✅ SIP Inbound Trunk configured: {inbound_trunk.sip_trunk_id}")
        return inbound_trunk
    except Exception as e:
        logger.error(f"Error configuring SIP trunk: {e}")
    finally:
        await livekit_api.aclose()

async def dial_outbound_citizen(
    phone_number: str,
    room_name: str,
    sip_trunk_id: str
):
    """
    Triggers an outbound phone call to a citizen and connects them into the LiveKit Room.
    """
    livekit_api = api.LiveKitAPI(LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
    try:
        participant = await livekit_api.sip.create_sip_participant(
            api.CreateSIPParticipantRequest(
                sip_trunk_id=sip_trunk_id,
                sip_call_to=phone_number,
                room_name=room_name,
                participant_identity=f"phone-{phone_number}",
                participant_name="Citizen (Phone)"
            )
        )
        logger.info(f"📞 Dialing citizen at {phone_number} into room {room_name}")
        return participant
    except Exception as e:
        logger.error(f"Failed to place outbound SIP call: {e}")
        return None
    finally:
        await livekit_api.aclose()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("JanSamvaad AI Telephony Module loaded.")
