from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class CallStatus(str, Enum):
    INITIATED = "initiated"
    RINGING = "ringing"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    NO_ANSWER = "no_answer"


class SentimentLabel(str, Enum):
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    FRUSTRATED = "frustrated"
    SATISFIED = "satisfied"


class ConversationTurn(BaseModel):
    speaker: str  # "agent" or "citizen"
    text: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    language: str = "hi"  # hi, en, hi-en (hinglish)
    sentiment: Optional[SentimentLabel] = None
    latency_ms: Optional[int] = None  # only for agent turns


class CallFeedback(BaseModel):
    category: str          # e.g. "water_supply", "road_condition"
    severity: str          # "low", "medium", "high"
    issue_description: str
    location_mentioned: Optional[str] = None
    days_ongoing: Optional[int] = None
    citizen_sentiment: SentimentLabel = SentimentLabel.NEUTRAL
    resolved: bool = False


class CallRecord(BaseModel):
    call_id: str
    room_name: str
    phone_number: Optional[str] = None
    citizen_name: Optional[str] = None
    status: CallStatus = CallStatus.INITIATED
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    ended_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    conversation: List[ConversationTurn] = []
    summary: Optional[str] = None
    feedback: Optional[CallFeedback] = None
    avg_latency_ms: Optional[float] = None
    total_turns: int = 0
    interruptions: int = 0
    language_distribution: Dict[str, float] = {}  # {"hi": 0.7, "en": 0.3}
    metadata: Dict[str, Any] = {}


# Request / Response models
class InitiateCallRequest(BaseModel):
    phone_number: Optional[str] = None
    citizen_name: Optional[str] = None
    survey_topic: str = "public_services"
    language: str = "hi"


class CallResponse(BaseModel):
    call_id: str
    room_name: str
    status: CallStatus
    livekit_token: Optional[str] = None
    message: str
    greeting_text: Optional[str] = None
    audio_base64: Optional[str] = None
    phone_dialed: Optional[bool] = False


class VoiceTurnRequest(BaseModel):
    text: Optional[str] = None
    audio_base64: Optional[str] = None


class VoiceTurnResponse(BaseModel):
    agent_text: str
    audio_base64: Optional[str] = None
    is_complete: bool = False
    sentiment: Optional[str] = None
