from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from google import genai
from google.genai import types
# from google import genai
# import google.generativeai as genai
# from google.generativeai import types

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

class ChatResponse(BaseModel):
    reply: str

system_prompt = "You are a helpful and knowledgeable travel assistant."

#Chat endpoint
@app.post("/chat", response_model=ChatResponse)
def chat_with_bot(request: ChatRequest):
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=request.message,
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

# import pprint

# @app.post("/chat", response_model=ChatResponse)
# def chat_with_bot(request: ChatRequest):
#     try:
#         response = client.models.generate_content(
#             model="gemini-2.5-flash",
#             contents=request.message,
#             config=types.GenerateContentConfig(
#                 system_instruction="You are a helpful travel assistant.",
#                 temperature=0.3,
#                 max_output_tokens=512
#             )
#         )

#         pprint.pprint(response)         # See the full object
#         pprint.pprint(response.text)    # Check if text is None
#         return {"reply": response.text or "No content returned."}

#     except Exception as e:
#         return {"reply": f"Error: {str(e)}"}
