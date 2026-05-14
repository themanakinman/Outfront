from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google import genai
from google.genai import types
import os
import json
from dotenv import load_dotenv
from parking_tool import query_parking, get_unique_streets, find_parking_near_address

env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(env_path)
api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    print("WARNING: GOOGLE_API_KEY not found in .env")

client = genai.Client(api_key=api_key)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

tools = [query_parking, get_unique_streets, find_parking_near_address]

system_instruction = """
You are a highly insightful, friendly LA parking assistant.
When a user asks for parking, use the available tools to find real vacant spots.
Provide an insightful response mentioning distances, street names, ease of parking, and any nearby landmarks if relevant.

You MUST respond in pure JSON format matching this schema:
{
  "insightful_response": "Your friendly, insightful chat response here.",
  "spots": [
    {
      "id": 1,
      "lat": 34.0522,
      "lng": -118.2437,
      "rate": "$2.00/hr",
      "address": "123 Main St"
    }
  ]
}

If you cannot find any spots, return an empty list for "spots".
Only return JSON.
"""

chat = client.chats.create(
    model="gemini-2.5-flash",
    config=types.GenerateContentConfig(
        system_instruction=system_instruction,
        tools=tools,
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=False)
    )
)

class ChatRequest(BaseModel):
    query: str

@app.post("/api/chat")
def chat_endpoint(req: ChatRequest):
    try:
        response = chat.send_message(req.query)
        text = response.text.strip()
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        data = json.loads(text.strip())
        return data
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app_ai:app", host="0.0.0.0", port=8000, reload=True)
