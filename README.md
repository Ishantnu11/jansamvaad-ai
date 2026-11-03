# 🇮🇳 JanSamvaad AI — Hindi Voice Outreach Agent

> An AI-powered Hindi voice agent for citizen outreach surveys, built with LiveKit, Sarvam AI, and Gemini/GPT.

[![Python](https://img.shields.io/badge/Python-3.11-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-green)](https://fastapi.tiangolo.com)
[![LiveKit](https://img.shields.io/badge/LiveKit-Agents-orange)](https://livekit.io)
[![Sarvam AI](https://img.shields.io/badge/Sarvam-Hindi%20STT%2FTTS-saffron)](https://sarvam.ai)

---

## ✨ Features

| Feature | Implementation |
|---|---|
| 🎙️ Hindi STT | Sarvam AI `saarika:v2` |
| 🔊 Hindi TTS | Sarvam AI `bulbul:v1` — voice: Meera |
| 🧠 Hinglish understanding | Sarvam multilingual + LLM prompt |
| 💬 Conversational memory | LLM message history |
| ⚡ Interruption handling | Silero VAD via LiveKit |
| 📊 Sentiment analysis | Keyword + LLM hybrid |
| 📝 Call summarization | LLM-generated JSON + narrative |
| 📈 Analytics dashboard | React + Recharts |
| ⏱️ Latency monitoring | Per-turn ms measurement |

---

## 🏗️ Architecture

```
Citizen Voice
     │
     ▼
LiveKit Room ◄──── Agent JWT Token
     │
     ├── STT: Sarvam AI (saarika:v2) ──► Hindi Transcript
     │
     ├── LLM: Gemini 1.5 Flash ──────► Hindi Response
     │         (System prompt in Hindi, conversational memory)
     │
     ├── TTS: Sarvam AI (bulbul:v1) ──► Hindi Speech → Citizen
     │
     └── FastAPI Backend ─────────────► MongoDB
               │                            │
               └── Analytics Dashboard ◄────┘
                   (React + Recharts)
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20+
- MongoDB (local or Atlas)
- [Sarvam AI API key](https://sarvam.ai)
- [LiveKit Cloud account](https://livekit.io)
- OpenAI or Gemini API key

### 1. Clone and setup

```bash
git clone <repo>
cd jansamvaad-ai
```

### 2. Backend

```bash
cd backend
cp .env.example .env
# Fill in your API keys in .env
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 3. LiveKit Agent

```bash
cd agent
cp .env.example .env
# Fill in your API keys in .env
pip install -r requirements.txt
python jansamvaad_agent.py start
```

### 4. Frontend Dashboard

```bash
cd frontend
npm install
npm run dev
# Open http://localhost:3000
```

### 5. Docker (all services)

```bash
cd docker
# Fill in backend/.env and agent/.env first
docker compose up --build
```

---

## 🔑 API Keys Required

| Service | Where to get | Used for |
|---|---|---|
| **Sarvam AI** | [console.sarvam.ai](https://console.sarvam.ai) | Hindi STT + TTS |
| **LiveKit** | [livekit.io](https://livekit.io) | Real-time voice rooms |
| **Gemini** | [Google AI Studio](https://aistudio.google.com) | LLM intelligence |
| **OpenAI** (optional) | [platform.openai.com](https://platform.openai.com) | Fallback LLM / STT / TTS |
| **MongoDB** | [MongoDB Atlas](https://mongodb.com/atlas) | Call history storage |

---

## 📡 API Endpoints

### Calls
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/calls/initiate` | Start a new call session |
| `GET` | `/api/calls/` | List all calls |
| `GET` | `/api/calls/{call_id}` | Get call details |
| `POST` | `/api/calls/{call_id}/end` | End a call |

### Analytics
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/analytics/summary` | KPI summary |
| `GET` | `/api/analytics/recent` | Recent completed calls |
| `GET` | `/api/analytics/issues` | Issue category breakdown |

### LiveKit
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/livekit/token` | Get room access token |

---

## 🎙️ Example Conversation

```
AI Agent: नमस्ते! मैं जनसंवाद AI असिस्टेंट बोल रहा हूँ।
          क्या आपके पास दो मिनट का समय है?

Citizen:  हाँ जी, बताइए।

AI Agent: धन्यवाद! क्या आपके इलाके में पानी की सप्लाई नियमित है?

Citizen:  Mere area mein water supply issue hai last 5 din se.
          [Hinglish — understood and responded in Hindi]

AI Agent: समझ गया। क्या आप बता सकते हैं कि यह समस्या कितने
          दिनों से चल रही है?

Citizen:  [interrupts mid-response]
          [Agent stops immediately — interruption handled]

AI Agent: जी, बताइए।
```

---

## 🛡️ Ethics & Consent

- The agent **always identifies itself as AI** — never claims to be human.
- Consent is obtained at the start of every call.
- Opt-outs are respected immediately and gracefully.
- Feedback collection is **neutral** — no political persuasion.
- All data is stored securely and can be deleted on request.

---

## 📁 Project Structure

```
jansamvaad-ai/
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── main.py             # FastAPI app entrypoint
│   │   ├── core/
│   │   │   ├── config.py       # Settings (pydantic-settings)
│   │   │   └── database.py     # MongoDB connection
│   │   ├── models/
│   │   │   └── call.py         # Pydantic data models
│   │   ├── services/
│   │   │   ├── sarvam_service.py   # Hindi STT/TTS
│   │   │   ├── llm_service.py      # Gemini/OpenAI LLM
│   │   │   ├── call_service.py     # Call lifecycle
│   │   │   └── livekit_service.py  # Token generation
│   │   └── api/routes/
│   │       ├── calls.py
│   │       ├── analytics.py
│   │       ├── webhooks.py
│   │       └── livekit_token.py
│   ├── requirements.txt
│   └── Dockerfile
├── agent/                      # LiveKit voice agent
│   ├── jansamvaad_agent.py     # Main agent entrypoint
│   ├── sarvam_livekit_plugin.py # Custom Sarvam plugin
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                   # React dashboard
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Dashboard.jsx
│   │   │   ├── CallsPage.jsx
│   │   │   ├── CallDetailPage.jsx
│   │   │   ├── LiveCallPage.jsx
│   │   │   └── AnalyticsPage.jsx
│   │   ├── components/
│   │   │   ├── StatCard.jsx
│   │   │   ├── CallStatusBadge.jsx
│   │   │   ├── SentimentBadge.jsx
│   │   │   ├── ConversationTimeline.jsx
│   │   │   └── LatencyChart.jsx
│   │   ├── hooks/useCallData.js
│   │   └── lib/api.js
│   ├── package.json
│   └── Dockerfile
└── docker/
    └── docker-compose.yml
```

---

## 🗓️ Development Plan

| Days | Tasks |
|---|---|
| 1–2 | Python env, Sarvam AI STT/TTS integration, API key validation |
| 3–4 | LLM integration (Gemini), Hindi system prompt, conversation flow |
| 5–6 | LiveKit agent setup, room management, real-time audio pipeline |
| 7–8 | Conversational memory, interruption handling (Silero VAD) |
| 9–10 | MongoDB persistence, FastAPI backend, webhook events |
| 11–12 | React dashboard, analytics charts, latency monitoring |
| 13–14 | End-to-end testing, latency optimization, Docker deployment |

---

## ⚡ Latency Targets

| Stage | Target |
|---|---|
| STT (Sarvam) | < 300ms |
| LLM (Gemini Flash) | < 800ms |
| TTS (Sarvam) | < 400ms |
| **Total E2E** | **< 1.5s** |

---

