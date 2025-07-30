import httpx
import logging
from app.core.llm import detect_task_type, get_ai_response  # assuming you have task detection

def perform_action(transcript: str, api_key: str) -> str:
    logging.info("🔍 Detecting intent and processing...")

    try:
        # (Optional) You can route logic here, or go straight to get_ai_response
        task_type = detect_task_type(transcript) if 'detect_task_type' in globals() else "general"
        logging.info(f"🧠 Detected Task Type: {task_type}")

        # Call LLM API (e.g. Groq)
        response = get_ai_response(transcript, api_key=api_key)
        return response

    except Exception as e:
        logging.error(f"❌ Action Handler Error: {e}")
        return "Sorry, I couldn't process your request right now."
