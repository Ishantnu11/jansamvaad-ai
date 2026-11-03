from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import json

from app.core.config import settings
from app.core.database import connect_db, disconnect_db
from app.api.routes import calls, analytics, webhooks, livekit_token


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_db()
    yield
    await disconnect_db()


app = FastAPI(
    title="JanSamvaad AI – Hindi Voice Outreach API",
    version="1.0.0",
    description="Backend API for the JanSamvaad Hindi AI Voice Agent",
    lifespan=lifespan,
)

# CORS
origins = json.loads(settings.BACKEND_CORS_ORIGINS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(calls.router,        prefix="/api/calls",     tags=["Calls"])
app.include_router(analytics.router,    prefix="/api/analytics", tags=["Analytics"])
app.include_router(webhooks.router,     prefix="/api/webhooks",  tags=["Webhooks"])
app.include_router(livekit_token.router, prefix="/api/livekit",  tags=["LiveKit"])


@app.get("/")
async def root():
    return {"message": "JanSamvaad AI API is running 🇮🇳"}


@app.get("/health")
async def health():
    return {"status": "ok"}
