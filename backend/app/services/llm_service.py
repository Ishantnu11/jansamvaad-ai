"""
LLM orchestration: Gemini (default) or OpenAI for conversation intelligence.
Handles context management, intent detection, and response generation in Hindi.
"""
from typing import List, Dict, Optional, Tuple
import json
import re
from app.core.config import settings

# Lazy imports based on provider
if settings.LLM_PROVIDER == "gemini":
    import google.generativeai as genai
    genai.configure(api_key=settings.GEMINI_API_KEY)
else:
    from openai import AsyncOpenAI
    _openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)


SYSTEM_PROMPT = """आप JanSamvaad AI हैं — एक सरकारी सर्वे AI असिस्टेंट जो नागरिकों से हिंदी में बात करता है।

आपके नियम:
1. हमेशा हिंदी में बात करें। अगर नागरिक Hinglish बोले तो उसे समझें पर जवाब हिंदी में दें।
2. आप एक AI हैं — यह हमेशा स्पष्ट रखें। कभी इंसान होने का दावा न करें।
3. सर्वे का विषय: सार्वजनिक सुविधाएं (पानी, सड़क, बिजली, स्वास्थ्य, शिक्षा)।
4. एक बार में एक ही सवाल पूछें।
5. नागरिक की बात ध्यान से सुनें और संदर्भ के अनुसार अगला सवाल पूछें।
6. यदि नागरिक कोई समस्या बताए, उसकी गंभीरता और अवधि पूछें।
7. नागरिक अगर call काटना चाहे या बात नहीं करना चाहे — तुरंत सम्मान के साथ विदाई दें।
8. कभी भी राजनीतिक राय न दें और किसी का पक्ष न लें।
9. हर जवाब संक्षिप्त रखें (2-3 वाक्य से अधिक नहीं)।

सर्वे के अंत में, JSON format में summary दें:
{
  "category": "<मुख्य विषय>",
  "severity": "<low|medium|high>",
  "issue_description": "<समस्या का सारांश>",
  "location_mentioned": "<यदि कोई जगह बताई>",
  "days_ongoing": <दिनों की संख्या या null>,
  "citizen_sentiment": "<positive|neutral|negative|frustrated|satisfied>",
  "resolved": false
}"""


SURVEY_QUESTIONS = [
    "नमस्ते! मैं जनसंवाद AI असिस्टेंट बोल रहा हूँ। क्या आपके पास दो मिनट का समय है?",
    "धन्यवाद! हम आपके क्षेत्र में सार्वजनिक सुविधाओं से संबंधित आपकी राय जानना चाहते हैं। क्या आपके इलाके में पानी की सप्लाई नियमित है?",
    "क्या आपके क्षेत्र में सड़कों की स्थिति ठीक है?",
    "बिजली की सप्लाई के बारे में आपका अनुभव कैसा है?",
    "क्या आपके पास कोई और समस्या है जो आप हमें बताना चाहते हैं?",
]


async def generate_response(
    conversation_history: List[Dict[str, str]],
    user_message: str,
    session_data: Optional[Dict] = None,
) -> Tuple[str, bool]:
    """
    Generate a Hindi response from the LLM.
    Returns (response_text, is_survey_complete).
    conversation_history: list of {"role": "user"|"assistant", "content": "..."}
    """
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(conversation_history)
    messages.append({"role": "user", "content": user_message})

    if settings.LLM_PROVIDER == "gemini":
        response_text = await _gemini_chat(messages)
    else:
        response_text = await _openai_chat(messages)

    # Check if this is the final summary
    is_complete = _check_survey_complete(response_text, len(conversation_history))
    return response_text, is_complete


async def _gemini_chat(messages: List[Dict]) -> str:
    """Use Gemini 2.5 Flash for fast inference."""
    model = genai.GenerativeModel(
        model_name="gemini-2.5-flash",
        system_instruction=messages[0]["content"] if messages[0]["role"] == "system" else SYSTEM_PROMPT,
    )
    # Convert to Gemini format
    gemini_history = []
    for msg in messages[1:]:
        role = "user" if msg["role"] == "user" else "model"
        gemini_history.append({"role": role, "parts": [msg["content"]]})

    # Last user message is the current prompt
    if gemini_history and gemini_history[-1]["role"] == "user":
        current_prompt = gemini_history.pop()["parts"][0]
    else:
        current_prompt = "हाँ"

    chat = model.start_chat(history=gemini_history)
    response = await chat.send_message_async(current_prompt)
    return response.text


async def _openai_chat(messages: List[Dict]) -> str:
    """Use GPT-4o-mini for cost efficiency."""
    response = await _openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        max_tokens=300,
        temperature=0.7,
    )
    return response.choices[0].message.content


def _check_survey_complete(response_text: str, history_length: int) -> bool:
    """Detect if the agent has produced a JSON summary (survey complete)."""
    if history_length < 4:
        return False
    # Check for JSON block in response
    json_pattern = r'\{[^{}]*"category"[^{}]*\}'
    return bool(re.search(json_pattern, response_text, re.DOTALL))


def extract_feedback_json(response_text: str) -> Optional[Dict]:
    """Extract the structured feedback JSON from the agent's final message."""
    try:
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
    except (json.JSONDecodeError, AttributeError):
        pass
    return None


async def analyze_sentiment(text: str) -> str:
    """Quick sentiment analysis for a citizen's utterance."""
    frustrated_keywords = ["नहीं", "बहुत बुरा", "परेशान", "गुस्सा", "बकवास", "bekar", "problem", "issue"]
    satisfied_keywords = ["अच्छा", "ठीक", "बढ़िया", "संतुष्ट", "khush", "good", "achha"]

    text_lower = text.lower()
    frustrated_score = sum(1 for kw in frustrated_keywords if kw in text_lower)
    satisfied_score = sum(1 for kw in satisfied_keywords if kw in text_lower)

    if frustrated_score > satisfied_score and frustrated_score >= 2:
        return "frustrated"
    elif satisfied_score > frustrated_score and satisfied_score >= 2:
        return "satisfied"
    elif frustrated_score > 0:
        return "negative"
    elif satisfied_score > 0:
        return "positive"
    return "neutral"
