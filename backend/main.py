from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from google.genai import types
from google.genai.types import Content, Part
from google.generativeai import GenerativeModel, configure
import google.ai.generativelanguage as glm
from typing import List, Optional, Callable
from datetime import timedelta
from backend.tools import get_weather_forecast

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

# client = genai.Client()
configure(api_key=os.getenv("GOOGLE_API_KEY"))


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
If a user asks to get the weather forecast for a city and date range, you must always call the get_weather_forecast tool instead of answering directly.
Do not generate weather-related replies yourself.


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
    session_id: Optional[str] = None



WEATHER_ITINERARY_TOOL = glm.Tool(
    function_declarations=[
        glm.FunctionDeclaration(
            name="get_weather_forecast",
            description="""
            Fetches hourly temperature and dominant weather condition forecasts for a given city in a country and within a date range.
            Use this tool to get weather information to help plan travel itineraries,
            suggest appropriate activities (indoor/outdoor), and advise on packing.
            The date range should be between 16 days.
            """,
            parameters=glm.Schema(
                type=glm.Type.OBJECT,
                properties={
                    "city": glm.Schema(
                        type=glm.Type.STRING,
                        description="The name of the city, e.g., 'London', 'Paris', 'New York', 'Lagos'. Provide the full city name for best results."
                    ),
                    "country": glm.Schema( 
                        type=glm.Type.STRING,
                        description="The country the city is in, e.g. 'France, 'Nigeria', 'England'"
                    ),
                    "start_date": glm.Schema(
                        type=glm.Type.STRING,
                        description="The start date of the forecast in 'YYYY-MM-DD' format. Must be today or in the future."
                    ),
                    "end_date": glm.Schema(
                        type=glm.Type.STRING,
                        description="The end date of the forecast in 'YYYY-MM-DD' format. Must be today or in the future, and not more than 16 days from the start date."
                    )
                },
                required=["city", "country", "start_date", "end_date"],
            ),
        )
    ]
)


model = GenerativeModel(
    model_name="gemini-2.5-flash",
    tools=[WEATHER_ITINERARY_TOOL], 
    system_instruction=system_prompt,
    # safety_settings={
    #     category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
    #     threshold=types.HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
    #     HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    #     HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    #     HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    #     HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    # }
)


AVAILABLE_TOOLS: dict[str, Callable] = {
    "get_weather_forecast": get_weather_forecast,
}

@app.post("/chat", response_model=ChatResponse)
def chat_with_bot(request: ChatRequest):
    try:
        session_id = request.session_id or str(uuid.uuid4())
        history = get_history(session_id)

        converted_history = []
        for item in history:
            if "role" in item and "content" in item:
                role = item["role"]  

            
                if role == "assistant":
                    role = "model"
                elif role == "tool":
                    continue  

            converted_history.append(
                glm.Content(role=role, parts=[glm.Part(text=item["content"])])
            )
        chat = model.start_chat(history=converted_history)

        response = chat.send_message(
            request.message,
            generation_config=glm.GenerationConfig(
                temperature=0.4,
                top_p=1,
                top_k=40,
            )
        )


        reply_content = ""
        # Check if the model wants to call a tool
        if response.candidates and response.candidates[0].content.parts[0].function_call:
            function_call = response.candidates[0].content.parts[0].function_call
            tool_name = function_call.name
            tool_args = {k: v for k, v in function_call.args.items()}

            

            if tool_name in AVAILABLE_TOOLS:
                print(f"Tool Call Detected: {tool_name} with args: {tool_args}")
                tool_output = AVAILABLE_TOOLS[tool_name](**tool_args)
                print(f"Tool Output: {tool_output}")

                follow_up_response = chat.send_message(
                    glm.Part(function_response=glm.FunctionResponse(name=tool_name, response=tool_output)),
                    generation_config=glm.GenerationConfig(
                        temperature=0.7,
                        top_p=1,
                        top_k=40,
                    )
                )
                reply_content = follow_up_response.text
            else:
                reply_content = f"Sorry, Wanderbot doesn't have a tool to perform '{tool_name}'."
        else:
            reply_content = response.text or "I'm sorry, I couldn't find a response. Please try again."


        new_history = []
        for content_item in chat.history:
            role = content_item.role
            text_content = ""
            for part in content_item.parts:
                if part.text:
                    text_content += part.text
                elif part.function_call:
                    args_for_history = {k: v for k, v in part.function_call.args.items()}
                    text_content += f"FunctionCall: {part.function_call.name}({json.dumps(args_for_history)})"
                elif part.function_response:
                    response_data = part.function_response.response

                    if not isinstance(response_data, dict):
                        try:
                            response_data = {k: v for k, v in response_data.items()}
                        except AttributeError:
                            print(f"DEBUG: Non-dict response_data type: {type(response_data)}. Converting to string.")
                            response_data = str(response_data)
                    
                    try:
                        text_content += f"FunctionResponse: {part.function_response.name}({json.dumps(response_data)})"
                    except TypeError as e:
                        print(f"CRITICAL ERROR IN HISTORY SAVE (FunctionResponse): {e}")
                        print(f"Offending type: {type(response_data)}, Value: {repr(response_data)}")
                        text_content += f"FunctionResponse: {part.function_response.name}(SerializationError: {e})"

            role_to_save = "assistant" if role == "model" else role
            new_history.append({"role": role_to_save, "content": text_content})
            
        save_history(session_id, new_history)


        return {"reply": reply_content, "session_id": session_id}

    except Exception as e:
        print(f"Error in chat_with_bot: {e}")
        return {"reply":  "An unexpected error occurred. Please try again"}