import os
import requests
from dotenv import load_dotenv
from pathlib import Path
from openai import OpenAI

# Force load .env from project root
load_dotenv('.env')

OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
OPENROUTER_API_URL = os.getenv('OPENROUTER_API_URL')
OPENROUTER_API_MODEL = os.getenv('OPENROUTER_API_MODEL')

print(f"[DEBUG] OPENROUTER_API_URL loaded: {OPENROUTER_API_URL}")

# Set up OpenAI client for OpenRouter
client = OpenAI(
    base_url=OPENROUTER_API_URL,
    api_key=OPENROUTER_API_KEY,
)

def ask_llm(messages):
    try:
        completion = client.chat.completions.create(
            model=OPENROUTER_API_MODEL,
            messages=messages
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"Error calling LLM: {e}"
