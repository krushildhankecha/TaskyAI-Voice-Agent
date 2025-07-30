import httpx
from langdetect import detect


GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

def get_ai_response(prompt: str, api_key: str) -> str:
    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "llama3-8b-8192",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7
        }

        response = httpx.post(GROQ_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()

        return data["choices"][0]["message"]["content"].strip()

    except Exception as e:
        print("❌ LLM Error:", e)
        return "Sorry, something went wrong with the AI."
    

def detect_language(text: str) -> str:
    try:
        return detect(text)
    except Exception:
        return "en"  # fallback to English

# llm_util.py
def detect_task_type(text: str) -> str:
    """
    Dummy function to classify task type.
    You can expand with keywords, rules or LLM later.
    """
    if any(kw in text.lower() for kw in ["summary", "minutes", "meeting"]):
        return "meeting_summary"
    elif any(kw in text.lower() for kw in ["remind", "create", "schedule"]):
        return "action"
    else:
        return "query"

