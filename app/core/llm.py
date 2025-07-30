import httpx
import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

HEADERS = {
    "Authorization": f"Bearer {GROQ_API_KEY}",
    "Content-Type": "application/json"
}

def get_ai_response(prompt: str, api_key: str) -> str:
    try:
        payload = {
            "model": "llama3-8b-8192",  # or llama3-70b-8192
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7
        }

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        response = httpx.post(GROQ_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()

        return data["choices"][0]["message"]["content"].strip()

    except Exception as e:
        print("LLM Error:", e)
        return "❌ Sorry, something went wrong with the AI."
