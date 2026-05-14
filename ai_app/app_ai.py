from google import genai
from google.genai import types
import os
from dotenv import load_dotenv
from parking_tool import query_parking, get_unique_streets, find_parking_near_address

env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(env_path)
api_key = os.getenv("GOOGLE_API_KEY")
client = genai.Client(api_key=api_key)

tools = [query_parking, get_unique_streets, find_parking_near_address]

chat = client.chats.create(
    model="gemini-2.5-flash-lite", 
    config=types.GenerateContentConfig(
        tools=tools,
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=False)
    )
)

def chat_with_parking_ai(user_input):
    response = chat.send_message(user_input)
    return response.text

if __name__ == "__main__":
    print("LA Parking AI (v2.0) is online!")
    print("Try asking: 'Where can I park on Main St?'")
    
    while True:
        user_q = input("\nYou: ")
        if user_q.lower() in ['exit', 'quit']:
            break
            
        print("AI: Thinking...")
        try:
            answer = chat_with_parking_ai(user_q)
            print(f"AI: {answer}")
        except Exception as e:
            print(f"Error: {e}")
            print("Check your GOOGLE_API_KEY and connection.")
