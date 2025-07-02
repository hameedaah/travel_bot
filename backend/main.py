from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from google import genai
from google.genai import types
from google.genai.types import Content, Part
from typing import List, Optional
# Load .env file to get the API key
load_dotenv()

client = genai.Client()

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
    message: str
    history: Optional[List[dict]] = []

class ChatResponse(BaseModel):
    reply: str


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

MAX_HISTORY_LENGTH = 10


#Chat endpoint
@app.post("/chat", response_model=ChatResponse)
def chat_with_bot(request: ChatRequest):
    try:
        messages = []

        # Add history if provided
        if request.history:
            trimmed_history = request.history[-MAX_HISTORY_LENGTH:]
            for item in trimmed_history:
                role = item["role"]
                if role == "assistant":
                    role = "model"
                messages.append(Content(role=role, parts=[Part(text=item["content"])]))

        # Add current user message
        messages.append(Content(role="user", parts=[Part(text=request.message)]))

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=messages,
            config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            # max_output_tokens= 512,
            temperature=0.1,
            top_p=1,
            top_k=40,
            )
        )
        return {"reply": response.text or "No content returned."}
    except Exception as e:
        return {"reply": f"Error: {str(e)}"}