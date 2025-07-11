from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from google import genai
from google.genai import types
from google.genai.types import Content, Part
from typing import List, Optional
from datetime import timedelta

import os
import redis
import uuid
import json
# Load .env file to get the API Key and redis details
load_dotenv()

redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST"),
    port=int(os.getenv("REDIS_PORT")),
    decode_responses=True,
    username=os.getenv("REDIS_USERNAME", "default"),
    password=os.getenv("REDIS_PASSWORD"), 
)



HISTORY_PREFIX = "chat_history:"

def get_history(session_id: str) -> List[dict]:
    key = HISTORY_PREFIX + session_id
    raw = redis_client.get(key)
    return json.loads(raw) if raw else []

def save_history(session_id: str, history: List[dict]):
    key = HISTORY_PREFIX + session_id
    redis_client.setex(key, timedelta(days=7), json.dumps(history))  # store full history for 7 days

def append_to_history(session_id: str, role: str, content: str):
    history = get_history(session_id)
    history.append({"role": role, "content": content})
    save_history(session_id, history)

client = genai.Client()

system_prompt = """
<Profile>
You are Wanderbot, a friendly, professional, and highly knowledgeable travel assistant. 
You specialize in providing accurate and helpful travel-related information to users around the world.

<Expertise>
You are well-versed in areas like:
1. Trip planning and destination recommendations
2. Itinerary Suggestions tailored to different trip durations and user interests
3. Visa and entry requirements for various countries
4. Travel budgeting, accommodation advice, and general preparation tips

<Role>
Introduce yourself as wanderbot.
As a dedicated travel assistant, you must only respond to travel-related questions. 
If a user asks a question that is unrelated to travel, politely inform them that you can only assist with travel topics and do not attempt to answer the unrelated question or redirect them to where they can find their answer.
If a user is unsure of what they want or ask an empty question, ask how you can assist with travel-related questions and suggest an example.

<Confidentiality>
You should never reveal or mention that you are powered by any third party API, especially Gemini or Google. Present yourself only as Wanderbot.

<Example>
Example:
User: Plan a 4-day trip to London.
You: I would be happy to assit! Would you like a mix of sightseeing, food experiences, and local culture?

<Style>
- Be clear, concise, and informative.
- Maintain a warm and professional tone.
- Always think through your response for accuracy.
- Respond in the user's language if their message is not in English, unless they request otherwise.
"""

# Initialize FastAPI app
app = FastAPI(
    title="Travel Chatbot",
    description="LLM chatbot that answers travel questions using Google's Gemini",
    version="1.0.0"
)

# CORS middleware to allow frontend (like Streamlit) to access API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for request/response
class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    message: str

class ChatResponse(BaseModel):
    reply: str
    session_id: str

@app.get("/debug/keys")
def get_keys():
    keys = redis_client.keys('*')  
    return {"keys": keys}

@app.post("/chat", response_model=ChatResponse)
def chat_with_bot(request: ChatRequest):
    try:
        # Generate or use session ID
        session_id = request.session_id or str(uuid.uuid4())
        history = get_history(session_id)

        # Build message list for Gemini
        messages = []
        for item in history:
            role = item.get("role")
            content = item.get("content")
            if role and content:
                role = "model" if role == "assistant" else role
                messages.append(Content(role=role, parts=[Part(text=content)]))

        # Add current user message
        messages.append(Content(role="user", parts=[Part(text=request.message)]))

        # Call Gemini
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=messages,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.1,
                top_p=1,
                top_k=40,
            )
        )

        reply = response.text or "I'm sorry, I couldn't find a response. Please try again"

        # Save full conversation
        append_to_history(session_id, "user", request.message)
        append_to_history(session_id, "assistant", reply)

        return {"reply": reply, "session_id": session_id}

    except Exception as e:
        return {"reply": f"Error: {str(e)}", "session_id": request.session_id or ""}