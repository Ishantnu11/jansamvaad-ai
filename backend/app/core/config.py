from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # LiveKit
    LIVEKIT_URL: str = "wss://localhost:7880"
    LIVEKIT_API_KEY: str = "devkey"
    LIVEKIT_API_SECRET: str = "secret"
    LIVEKIT_SIP_TRUNK_ID: str = ""

    # Sarvam AI
    SARVAM_API_KEY: str = ""
    SARVAM_API_URL: str = "https://api.sarvam.ai"

    # LLM
    OPENAI_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    LLM_PROVIDER: str = "gemini"  # "openai" or "gemini"

    # MongoDB
    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "jansamvaad"

    # Twilio Voice
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_PHONE_NUMBER: str = ""
    TWILIO_VOICE_URL: str = ""

    # Exotel Voice (India Cloud Telephony)
    EXOTEL_ACCOUNT_SID: str = ""
    EXOTEL_API_KEY: str = ""
    EXOTEL_API_TOKEN: str = ""
    EXOTEL_CALLER_ID: str = ""
    EXOTEL_APP_URL: str = ""
    EXOTEL_SUBDOMAIN: str = "api.exotel.com"

    # Public URL for Telephony Webhooks (Exotel / Twilio)
    PUBLIC_BASE_URL: str = ""

    # App
    APP_SECRET_KEY: str = "change_me"
    BACKEND_CORS_ORIGINS: str = '["http://localhost:3000","http://localhost:5173"]'
    DEBUG: bool = True

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
